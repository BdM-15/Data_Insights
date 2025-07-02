"""
MCP Chat Server for Data_Insights

This FastAPI app serves as the backend for the "chat with the data" feature. It receives chat requests from the UI, orchestrates LLM calls (Ollama: Mistral/Llama-3 for Q&A, Code Llama for code/visualization), queries the capture_insights database as needed, logs all interactions, and returns answers/visualizations to the UI.

Author: Data_Insights Team
"""

from fastapi import FastAPI, HTTPException, Query, Path, Body
from fastapi.responses import JSONResponse
from src.backend.data.models.data_models import ChatRequest, ChatResponse, NoteRequest, NoteDeleteRequest, NoteUpdateRequest, ChatHistoryRequest, VisualizationRequest, VisualizationResponse, ProfileGenerateRequest, ProfileGenerateResponse, DataSummaryResponse
from src.mcp_server.llm_interface import query_llm
from src.mcp_server.notes import add_note, get_notes, delete_note, update_note, set_note_active
from src.mcp_server.logger import log_chat_interaction, get_chat_history, engine
from sqlalchemy import text as sa_text
from typing import List
from datetime import datetime

app = FastAPI(title="MCP Chat Server", description="Backend for chat with the data feature.")

# --- PATCH endpoint for soft delete/restore of a note ---
@app.patch("/note/{note_id}")
def patch_note_active(note_id: int = Path(..., description="Note ID to update"), data: dict = Body(...)):
    """
    Update the 'active' status of a note (soft delete/restore).
    Expects JSON: {"active": bool}
    """
    active = data.get("active")
    if active is None:
        return JSONResponse(status_code=400, content={"error": "Missing 'active' in request body."})
    success = set_note_active(note_id, active)
    if not success:
        return JSONResponse(status_code=404, content={"error": "Note not found or could not be updated."})
    return {"success": True, "id": note_id, "active": active}

@app.post("/chat", response_model=ChatResponse)
def chat_with_data(request: ChatRequest):
    """
    Main chat endpoint. Receives a user prompt, auto-includes all notes for the page/tab, orchestrates LLM/database, logs the interaction, and returns the answer.
    """

    # --- Step 1: Fetch all notes for this page/tab and include in context ---
    notes = get_notes(request.page, request.tab, session_id=request.session_id)
    notes_text = [note["note_text"] for note in notes] if notes else []


    # --- Step 2: Dynamically fetch relevant contract data for context based on user prompt, but skip for greetings/small talk ---
    import re
    greeting_patterns = [
        r"^\s*hi\s*$", r"^\s*hello\s*$", r"^\s*hey\s*$", r"^\s*good (morning|afternoon|evening)\s*$", r"^\s*how are you\s*\??$", r"^\s*what's up\s*\??$", r"^\s*yo\s*$", r"^\s*sup\s*$", r"^\s*thank you\s*\??$", r"^\s*thanks\s*\??$"
    ]
    is_greeting = any(re.match(pat, request.user_prompt.strip(), re.IGNORECASE) for pat in greeting_patterns)
    contract_data = []
    if not is_greeting:
        try:
            # Check for NAICS code in user prompt and for explicit LIMIT in the prompt
            naics_match = re.search(r"naics(?: code)?\s*([0-9]{4,6})", request.user_prompt, re.IGNORECASE)
            limit_match = re.search(r"(?:top|first|limit)\s*(\d+)", request.user_prompt, re.IGNORECASE)
            user_limit = int(limit_match.group(1)) if limit_match else None
            # Reason: Only apply a LIMIT if the user explicitly requests it
            # Check for 'potential total award' or similar in the prompt
            wants_potential_award = bool(re.search(r"potential( total)? award", request.user_prompt, re.IGNORECASE))
            if naics_match and wants_potential_award:
                naics_code = naics_match.group(1)
                sql_base = """
                    SELECT contract_award_unique_key, naics_code, potential_total_value_of_award
                    FROM capture_insights.s3_processed.usaspending_prime_awards
                    WHERE naics_code = :naics_code
                    ORDER BY potential_total_value_of_award DESC
                """
                if user_limit:
                    sql = sa_text(sql_base + f" LIMIT {user_limit}")
                else:
                    sql = sa_text(sql_base)
                with engine.begin() as conn:
                    result = conn.execute(sql, {"naics_code": naics_code})
                    contract_data = [dict(row) for row in result]
                # If all values are null, inform the user
                if contract_data and all(row.get("potential_total_value_of_award") is None for row in contract_data):
                    contract_data = [{"info": "No contracts with a non-null potential_total_value_of_award for this NAICS code."}]
            elif naics_match:
                naics_code = naics_match.group(1)
                sql_base = """
                    SELECT contract_award_unique_key, naics_code, federal_action_obligation
                    FROM capture_insights.s3_processed.usaspending_prime_awards
                    WHERE naics_code = :naics_code
                    ORDER BY federal_action_obligation DESC
                """
                if user_limit:
                    sql = sa_text(sql_base + f" LIMIT {user_limit}")
                else:
                    sql = sa_text(sql_base)
                with engine.begin() as conn:
                    result = conn.execute(sql, {"naics_code": naics_code})
                    contract_data = [dict(row) for row in result]
            else:
                # Use a simple keyword extraction from the user prompt for dynamic search
                keywords = re.findall(r"\b\w{4,}\b", request.user_prompt)
                keywords = [k for k in keywords if k.lower() not in {"about", "which", "where", "there", "their", "would", "could", "should", "these", "those", "with", "from", "this", "that", "have", "will", "more", "find", "help", "role", "your", "what", "when", "how", "many", "most", "some", "such", "into", "than", "then", "them", "they", "been", "also", "only", "each", "very", "just", "like", "over", "even", "both", "make", "used", "using", "data", "info", "info", "info", "info"}]
                contract_query = None
                params = {}
                if keywords:
                    # Build a dynamic WHERE clause for relevant fields
                    like_clauses = []
                    for idx, kw in enumerate(keywords[:5]):
                        param = f"kw{idx}"
                        like_clauses.append(f"(recipient_name ILIKE :{param} OR parent_award_agency_name ILIKE :{param} OR naics_code ILIKE :{param} OR transaction_description ILIKE :{param})")
                        params[param] = f"%{kw}%"
                    where_sql = " OR ".join(like_clauses)
                    sql_base = f"""
                        SELECT contract_award_unique_key, recipient_name, parent_award_agency_name, naics_code, transaction_description, federal_action_obligation, period_of_performance_current_end_date
                        FROM capture_insights.s3_processed.usaspending_prime_awards
                        WHERE {where_sql}
                        ORDER BY period_of_performance_current_end_date DESC
                    """
                    if user_limit:
                        contract_query = sa_text(sql_base + f" LIMIT {user_limit}")
                    else:
                        contract_query = sa_text(sql_base)
                else:
                    # Fallback: show all most recent contracts (no LIMIT unless user requests)
                    sql_base = """
                        SELECT contract_award_unique_key, recipient_name, parent_award_agency_name, naics_code, transaction_description, federal_action_obligation, period_of_performance_current_end_date
                        FROM capture_insights.s3_processed.usaspending_prime_awards
                        ORDER BY period_of_performance_current_end_date DESC
                    """
                    if user_limit:
                        contract_query = sa_text(sql_base + f" LIMIT {user_limit}")
                    else:
                        contract_query = sa_text(sql_base)
                with engine.begin() as conn:
                    result = conn.execute(contract_query, params)
                    contract_data = [dict(row) for row in result]
        except Exception as e:
            contract_data = [{"error": f"Failed to fetch contract data: {e}"}]

    # --- Step 3: Build prompt_structure with notes, contract data, and explicit system prompt ---
    prompt_structure = request.prompt_structure or {}
    if notes_text:
        prompt_structure["user_notes"] = notes_text

    # Only inject schema and tool list if this is a data question (not a greeting/small talk)
    if not is_greeting:
        # --- Fetch and include table schema for usaspending_prime_awards ---
        table_schema = []
        try:
            with engine.begin() as conn:
                schema_result = conn.execute(sa_text("""
                    SELECT column_name, data_type
                    FROM information_schema.columns
                    WHERE table_schema = 's3_processed' AND table_name = 'usaspending_prime_awards'
                    ORDER BY ordinal_position
                """))
                table_schema = [{"column": row[0], "type": row[1]} for row in schema_result]
        except Exception as e:
            table_schema = [{"error": f"Error fetching schema: {e}"}]
        prompt_structure["usaspending_prime_awards_schema"] = table_schema

        # --- Inject MCP tool list and tool usage instructions ---
        mcp_tools = [
            {
                "name": "Data Query Tool",
                "description": "Query the capture_insights.s3_processed.usaspending_prime_awards table for contract, agency, NAICS, and obligation data."
            },
            {
                "name": "Notes Tool",
                "description": "Retrieve, add, update, and delete user notes for any page/tab/session."
            },
            {
                "name": "Visualization Tool",
                "description": "Generate interactive charts and visualizations from contract data."
            },
            {
                "name": "Document Generator",
                "description": "Create capture profiles and milestone review documents."
            },
            {
                "name": "Analysis/Reasoning Tool",
                "description": "Provide strategic assessments and AI-augmented insights."
            }
        ]
        prompt_structure["mcp_tools"] = mcp_tools

    if contract_data:
        prompt_structure["contract_data"] = contract_data
        prompt_structure["contract_data_source"] = "capture_insights.s3_processed.usaspending_prime_awards"

    # --- Step 3b: Add explicit system prompt to instruct LLM to use MCP server, database, and tools ---
    if is_greeting:
        system_prompt = (
            "You are Roberto, an expert business intelligence assistant for defense contractors. "
            "You operate within the Data_Insights platform. Respond naturally to greetings and small talk. "
            "If the user asks a data-related question, use the provided context from the database."
        )
    else:
        system_prompt = (
            "You are Roberto, an expert business intelligence assistant for defense contractors. "
            "You operate within the Data_Insights platform, which uses the MCP server to orchestrate all AI and data operations. "
            "You have access to the following MCP tools for data analysis and business intelligence tasks: "
            "- Data Query Tool: Query the capture_insights.s3_processed.usaspending_prime_awards table for contract, agency, NAICS, and obligation data.\n"
            "- Notes Tool: Retrieve, add, update, and delete user notes for any page/tab/session.\n"
            "- Visualization Tool: Generate interactive charts and visualizations from contract data.\n"
            "- Document Generator: Create capture profiles and milestone review documents.\n"
            "- Analysis/Reasoning Tool: Provide strategic assessments and AI-augmented insights.\n"
            "If a user asks about your capabilities or available tools, list and describe these tools. "
            "If you need to use a tool, simply describe in plain language which tool you want to use and what you want to accomplish. The system will handle the rest. "
            "You are always provided with the actual results of your data queries in the 'contract_data' context. Use this data to answer the user's question directly. Do not generate SQL for the user to run unless explicitly asked. "
            "You must only use columns from the provided schema. Do not invent or assume column names. "
            "If the answer is not present in the data, say so or ask for clarification. "
            "Never make up contract details or reference data not explicitly provided. "
            "If you need more information, ask the user for clarification or for a more specific query."
        )
    prompt_structure["system_prompt"] = system_prompt

    # --- Step 4: Query LLM for answer/code/visualization ---
    llm_result = query_llm(
        user_prompt=request.user_prompt,
        context_data={"contract_data": contract_data},
        model="mistral",  # or "codellama" based on intent (to be improved)
        prompt_structure=prompt_structure
    )

    # --- Step 5: Log the interaction ---
    log_chat_interaction(
        user_prompt=request.user_prompt,
        llm_response=llm_result["answer"],
        llm_generated_code=llm_result.get("llm_generated_code"),
        response_type=llm_result["response_type"],
        page=request.page,
        tab=request.tab,
        prompt_structure=prompt_structure,
        session_id=request.session_id,
        user_id=request.user_id
    )

    # --- Step 6: Return the response to the UI ---
    return ChatResponse(
        answer=llm_result["answer"],
        plotly_json=llm_result["plotly_json"],
        llm_generated_code=llm_result["llm_generated_code"],
        response_type=llm_result["response_type"]
    )

@app.post("/note")
def add_user_note(request: NoteRequest):
    """
    Add a new user note for the given page/tab/user/session.
    Returns the new note's ID or error message.
    """
    note_id = add_note(request.note_text, request.page, request.tab, request.user_id, request.session_id)
    if note_id == -1:
        return JSONResponse(status_code=500, content={"error": "Failed to add note."})
    return {"note_id": note_id}

@app.get("/notes")
def fetch_notes(
    page: str = Query(..., description="Page where notes are used."),
    tab: str = Query(..., description="Tab where notes are used."),
    user_id: str = Query(None, description="User ID (optional)."),
    session_id: str = Query(None, description="Session ID (optional).")
):
    """
    Retrieve notes for a given page/tab (optionally filtered by user/session).
    Returns a list of notes.
    """
    notes = get_notes(page, tab, user_id, session_id)
    return {"notes": notes}

@app.delete("/notes/delete")
def delete_user_note(request: NoteDeleteRequest):
    """
    Delete a user note by its ID.
    Returns success status.
    """
    success = delete_note(request.id)
    if not success:
        return JSONResponse(status_code=404, content={"error": "Note not found or could not be deleted."})
    return {"success": True}

@app.put("/notes/update")
def update_user_note(request: NoteUpdateRequest):
    """
    Update a user note's text by its ID.
    Returns success status.
    """
    success = update_note(request.id, request.note_text)
    if not success:
        return JSONResponse(status_code=404, content={"error": "Note not found or could not be updated."})
    return {"success": True}

@app.post("/chat/history", response_model=List[ChatResponse])
def fetch_chat_history(request: ChatHistoryRequest):
    """
    Retrieve chat history for a given page/tab (optionally filtered by session/user).
    Returns a list of chat log entries (most recent first).
    """
    logs = get_chat_history(
        page=request.page,
        tab=request.tab,
        session_id=request.session_id,
        user_id=request.user_id
    )
    # Convert DB rows to ChatResponse objects (or dicts)
    responses = [
        ChatResponse(
            answer=log["llm_response"],
            plotly_json=None,  # Not stored in log; can be extended later
            llm_generated_code=log.get("llm_generated_code"),
            response_type=log["response_type"],
            timestamp=log["created_at"]
        )
        for log in logs
    ]
    return responses

@app.post("/visualization", response_model=VisualizationResponse)
def generate_visualization(request: VisualizationRequest):
    """
    Generate and return a custom chart or plot based on user parameters.
    Calls the LLM (via Ollama) to generate a visualization and returns Plotly JSON and code.
    """
    # --- Step 1: Prepare context for LLM (can be extended to fetch data, etc.) ---
    context_data = None  # Placeholder for future data fetch logic

    # --- Step 2: Call LLM for visualization (use codellama or similar model) ---
    llm_result = query_llm(
        user_prompt=request.user_prompt,
        context_data=context_data,
        model="codellama",  # Use code/visualization model
        prompt_structure={
            "data_filters": request.data_filters,
            "chart_type": request.chart_type,
            "page": request.page,
            "tab": request.tab
        }
    )

    # --- Step 3: Return the visualization response ---
    return VisualizationResponse(
        answer=llm_result["answer"],
        plotly_json=llm_result["plotly_json"],
        llm_generated_code=llm_result["llm_generated_code"],
        # response_type and timestamp are set by default
    )

@app.post("/profile/generate", response_model=ProfileGenerateResponse)
def generate_profile(request: ProfileGenerateRequest):
    """
    Generate an AI-assisted capture profile document or milestone review.
    If milestone is provided, generate a Shipley-style milestone review.
    """
    # --- Step 1: Build prompt for LLM ---
    prompt_structure = {
        "opportunity_id": request.opportunity_id,
        "milestone": request.milestone,
        "page": request.page,
        "tab": request.tab
    }
    # --- Step 2: Call LLM for document generation ---
    llm_result = query_llm(
        user_prompt=request.user_prompt or "Generate a capture profile document.",
        context_data=None,  # Extend to fetch opportunity data as needed
        model="mistral",  # Use general LLM for document/narrative
        prompt_structure=prompt_structure
    )
    # --- Step 3: Return the profile/milestone document ---
    return ProfileGenerateResponse(
        summary=llm_result.get("answer", "AI-generated summary unavailable."),
        document_text=llm_result.get("document_text", "[Full document text would be here.]"),
        ai_analysis=llm_result.get("ai_analysis"),
        milestone=request.milestone,
        # response_type and timestamp set by default
    )

@app.get("/data/summary", response_model=DataSummaryResponse)
def get_data_summary():
    """
    Provide quick stats or summaries for the dashboard (e.g., total contracts, total obligation, top agency, etc.).
    Queries the database for live values.
    """
    # Query from usaspending_prime_awards in capture_insights
    with engine.begin() as conn:
        total_contracts = conn.execute(sa_text("SELECT COUNT(*) FROM capture_insights.usaspending_prime_awards")).scalar() or 0
        total_obligation = conn.execute(sa_text("SELECT COALESCE(SUM(federal_action_obligation),0) FROM capture_insights.usaspending_prime_awards")).scalar() or 0.0
        top_agency = conn.execute(sa_text("SELECT parent_award_agency_name FROM capture_insights.usaspending_prime_awards GROUP BY parent_award_agency_name ORDER BY SUM(federal_action_obligation) DESC LIMIT 1")).scalar()
        top_contractor = conn.execute(sa_text("SELECT recipient_name FROM capture_insights.usaspending_prime_awards GROUP BY recipient_name ORDER BY SUM(federal_action_obligation) DESC LIMIT 1")).scalar()
        expiring_contracts = conn.execute(sa_text("SELECT COUNT(*) FROM capture_insights.usaspending_prime_awards WHERE period_of_performance_current_end_date >= CURRENT_DATE AND period_of_performance_current_end_date < CURRENT_DATE + INTERVAL '90 days' ")).scalar() or 0
    return DataSummaryResponse(
        total_contracts=total_contracts,
        total_obligation=total_obligation,
        top_agency=top_agency,
        top_contractor=top_contractor,
        expiring_contracts=expiring_contracts,
        last_updated=datetime.utcnow()
    )

@app.post("/search")
def search_data(request: dict):
    """
    Advanced semantic/keyword search across contracts, notes, or documents.
    Accepts a JSON payload with 'query', 'type' (contracts, notes, documents), and optional filters.
    Returns a list of matching results with relevant fields.
    """
    # Reason: This endpoint is extensible for future AI/semantic search integration.
    query = request.get("query", "")
    search_type = request.get("type", "contracts")
    filters = request.get("filters", {})
    results = []

    with engine.begin() as conn:
        if search_type == "contracts":
            # Simple keyword search on usaspending_prime_awards (can be extended for semantic search)
            sql = sa_text("""
                SELECT contract_award_unique_key, recipient_name, parent_award_agency_name, naics_code, transaction_description, federal_action_obligation, period_of_performance_current_end_date
                FROM capture_insights.usaspending_prime_awards
                WHERE (
                    recipient_name ILIKE :q OR
                    parent_award_agency_name ILIKE :q OR
                    naics_code ILIKE :q OR
                    transaction_description ILIKE :q
                )
                LIMIT 50
            """)
            db_results = conn.execute(sql, {"q": f"%{query}%"}).fetchall()
            for row in db_results:
                results.append(dict(row))
        elif search_type == "notes":
            # Search user notes (assuming notes table exists)
            sql = sa_text("""
                SELECT id, note_text, page, tab, user_id, session_id, created_at
                FROM capture_insights.user_notes
                WHERE note_text ILIKE :q
                LIMIT 50
            """)
            db_results = conn.execute(sql, {"q": f"%{query}%"}).fetchall()
            for row in db_results:
                results.append(dict(row))
        elif search_type == "documents":
            # Search documents (assuming documents table exists)
            sql = sa_text("""
                SELECT document_id, related_contract_id, text, document_type, created_at
                FROM capture_insights.documents
                WHERE text ILIKE :q
                LIMIT 50
            """)
            db_results = conn.execute(sql, {"q": f"%{query}%"}).fetchall()
            for row in db_results:
                results.append(dict(row))
        else:
            return JSONResponse(status_code=400, content={"error": "Invalid search type."})

    return {"results": results, "count": len(results)}

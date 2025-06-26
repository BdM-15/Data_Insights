"""
MCP Chat Server for Data_Insights

This FastAPI app serves as the backend for the "chat with the data" feature. It receives chat requests from the UI, orchestrates LLM calls (Ollama: Mistral/Llama-3 for Q&A, Code Llama for code/visualization), queries the capture_insights database as needed, logs all interactions, and returns answers/visualizations to the UI.

Author: Data_Insights Team
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from src.backend.data.models.data_models import ChatRequest, ChatResponse, NoteRequest, NoteDeleteRequest, NoteUpdateRequest, ChatHistoryRequest, VisualizationRequest, VisualizationResponse, ProfileGenerateRequest, ProfileGenerateResponse, DataSummaryResponse
from src.chat.llm_interface import query_llm
from src.chat.notes import add_note, get_notes, delete_note, update_note
from src.chat.logger import log_chat_interaction, get_chat_history, engine
from sqlalchemy import text as sa_text
from typing import List
from datetime import datetime

app = FastAPI(title="MCP Chat Server", description="Backend for chat with the data feature.")

@app.post("/chat", response_model=ChatResponse)
def chat_with_data(request: ChatRequest):
    """
    Main chat endpoint. Receives a user prompt, auto-includes all notes for the page/tab, orchestrates LLM/database, logs the interaction, and returns the answer.
    """
    # --- Step 1: Fetch all notes for this page/tab and include in context ---
    notes = get_notes(request.page, request.tab, session_id=request.session_id)
    notes_text = [note["note_text"] for note in notes] if notes else []

    # --- Step 2: (Placeholder) Fetch relevant data for context ---
    context_data = None  # Placeholder until db_access is implemented

    # --- Step 3: Build prompt_structure with notes ---
    prompt_structure = request.prompt_structure or {}
    if notes_text:
        prompt_structure["user_notes"] = notes_text

    # --- Step 4: Query LLM for answer/code/visualization ---
    llm_result = query_llm(
        user_prompt=request.user_prompt,
        context_data=context_data,
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

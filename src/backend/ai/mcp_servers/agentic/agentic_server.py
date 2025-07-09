"""
Agentic Orchestrator MCP Server

- Receives user prompts/intents from the frontend (e.g., chat UI)
- Calls the LLM to extract intent (using centralized intent schema)
- Routes the request to the correct specialized agent/tool (data, visualization, chat, notes, document, etc.)
- Aggregates and returns the result to the frontend

Rationale:
- This refactor separates the orchestrator logic from the chat agent, enabling clean, modular, and extensible agentic architecture.
- The orchestrator can call the chat agent as a sub-agent if the intent is 'chat' or 'qa'.
- This structure allows you to add more MCP servers (web intelligence, document generation, etc.) as siblings, each with their own folder and API.

This file is the main FastAPI entrypoint for the orchestrator.
"""
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from backend.data.models.data_models import AgenticIntent
# Import the chat MCP server as chat_server (renamed from mcp_server)
from backend.ai.mcp_servers.chat import chat_server
# Import other agents/tools as needed

app = FastAPI(title="Agentic Orchestrator MCP Server")

@app.post("/route")
async def route_intent(request: Request):
    """
    Receives a user prompt/context, calls the LLM for intent extraction, and routes to the correct agent/tool.
    """
    data = await request.json()
    # Step 1: Call LLM to extract intent (simulate for now)
    # In production, call llm_interface.extract_intent(data)
    llm_intent = data.get("llm_intent")  # For now, expect frontend to send intent directly
    try:
        intent_obj = AgenticIntent(**llm_intent)
    except ValidationError as e:
        return JSONResponse(status_code=400, content={"error": str(e)})

    # Step 2: Route to the correct agent/tool
    if intent_obj.intent == "chat":
        # Call the chat agent (as a submodule)
        return await chat_server.chat_endpoint(request)
    elif intent_obj.intent == "data_query":
        # TODO: Call data agent
        return JSONResponse({"result": "[Data agent response placeholder]"})
    elif intent_obj.intent == "visualization":
        # TODO: Call visualization agent
        return JSONResponse({"result": "[Visualization agent response placeholder]"})
    # ...add more intent/tool routing as needed
    else:
        return JSONResponse(status_code=400, content={"error": "Unknown intent"})

# Reason: This orchestrator enables flexible, modular, and extensible agentic workflows. The chat UI and all other user entry points should send prompts/intents to this orchestrator, which will handle LLM intent extraction and agent/tool dispatch.

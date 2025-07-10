"""
Orchestrator Router API for LLM intent parsing and tool dispatch.
"""
from fastapi import APIRouter, HTTPException, Request, Body
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Any, Dict, Optional
from backend.data.models.data_models import AgenticIntent
import requests
import json
from .orchestrator_prompt_template import ROSES_PROMPT_TEMPLATE, AGENTIC_TOOL_LIST
import logging
import os
import ast

router = APIRouter()

LLAMA3_MODEL = "llama3.1:8b"
OLLAMA_URL = "http://localhost:11434/api/chat"  # Switched to /api/chat for conversational context

logger = logging.getLogger("orchestrator_router")
logger.setLevel(logging.INFO)

try:
    LOG_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', 'logs'))
    LOG_PATH = os.path.join(LOG_DIR, 'orchestrator_router.log')
    os.makedirs(LOG_DIR, exist_ok=True)
    file_handler = logging.FileHandler(LOG_PATH)
    file_handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    file_handler.setFormatter(formatter)
    for h in logger.handlers[:]:
        logger.removeHandler(h)
    logger.addHandler(file_handler)
    print(f"[OrchestratorRouter] Logging to {LOG_PATH}")
    logger.info("[OrchestratorRouter] Logger initialized and ready.")
except Exception as log_setup_exc:
    print(f"[OrchestratorRouter] Logger setup failed: {log_setup_exc}")

@router.post("/route")
async def orchestrator_route(request: Request, body: Dict[str, Any] = Body(...)):
    """
    Main entrypoint for orchestrator LLM routing.
    Accepts POST requests from the frontend chat UI.
    Parses user prompt, calls LLM for intent, and dispatches to the correct tool/agent.
    """
    try:
        user_prompt = body.get("prompt") or body.get("user_prompt")
        user_id = body.get("user_id")
        session_id = body.get("session_id")
        page = body.get("page")
        tab = body.get("tab")
        # Reason: Compose LLM prompt for intent extraction
        tool_list = json.dumps(AGENTIC_TOOL_LIST, indent=2)
        llm_prompt = ROSES_PROMPT_TEMPLATE.format(tool_list=tool_list, user_prompt=user_prompt)
        # Call Ollama LLM for intent extraction
        ollama_payload = {
            "model": LLAMA3_MODEL,
            "messages": [
                {"role": "system", "content": llm_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "stream": False
        }
        llm_response = requests.post(OLLAMA_URL, json=ollama_payload, timeout=30)
        llm_response.raise_for_status()
        llm_content = llm_response.json().get("message", {}).get("content", "")
        # Try to parse LLM output as AgenticIntent (tool invocation)
        try:
            intent_json = json.loads(llm_content)
            agentic_intent = AgenticIntent(**intent_json)
        except Exception:
            # If not JSON, treat as conversational response (wrap in JSON for frontend compatibility)
            if isinstance(llm_content, str):
                return {"response": llm_content}
            return {"response": str(llm_content)}
        # Tool dispatch
        if agentic_intent.intent == "chat":
            # Forward to chat agent
            chat_payload = {
                "prompt": user_prompt,
                "user_id": user_id,
                "session_id": session_id,
                "page": page,
                "tab": tab
            }
            chat_response = requests.post("http://localhost:8002/chat/route", json=chat_payload, timeout=30)
            return JSONResponse(content=chat_response.json())
        elif agentic_intent.intent == "data_query":
            # Forward to database schema server for query execution
            query = agentic_intent.parameters.get("query")
            if not query:
                return JSONResponse(status_code=400, content={"error": "No query provided in parameters."})
            db_response = requests.post("http://localhost:8003/schema/run_query", json={"query": query}, timeout=30)
            return JSONResponse(content=db_response.json())
        elif agentic_intent.intent == "visualization":
            # Forward to chat server for visualization (or implement as needed)
            vis_payload = agentic_intent.parameters
            vis_payload.update({"user_id": user_id, "session_id": session_id, "page": page, "tab": tab})
            vis_response = requests.post("http://localhost:8002/visualization/route", json=vis_payload, timeout=30)
            return JSONResponse(content=vis_response.json())
        # Add more tool/agent dispatches as needed
        else:
            return JSONResponse(status_code=400, content={"error": f"Unknown or unsupported intent: {agentic_intent.intent}", "llm_output": llm_content})
    except Exception as exc:
        logger.error(f"Error in orchestrator_route: {exc}")
        return JSONResponse(status_code=500, content={"error": str(exc)})

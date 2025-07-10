"""
Orchestrator MCP Server

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
from backend.ai.mcp_servers.chat import chat_server
from .orchestrator_router import router as orchestrator_router

app = FastAPI(title="Orchestrator MCP Server")
app.include_router(orchestrator_router, prefix="/orchestrator")

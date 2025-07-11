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

# Use the main orchestrator router with dynamic tool discovery
app.include_router(orchestrator_router, prefix="/orchestrator")

@app.get("/health")
async def health_check():
    """Health check endpoint for service discovery."""
    return {
        "name": "orchestrator",
        "status": "healthy",
        "service_type": "orchestrator",
        "version": "1.0.0",
        "description": "Intelligent request routing and orchestration service"
    }

@app.get("/capabilities")
async def get_capabilities():
    """Return server capabilities for dynamic service discovery."""
    return {
        "capabilities": [
            {
                "name": "flexible_orchestration",
                "description": "Intelligent request routing with dynamic tool discovery and LLM reasoning",
                "endpoint": "http://localhost:8001/orchestrator/route",
                "method": "POST",
                "parameters": {
                    "prompt": "str",
                    "user_id": "str",
                    "session_id": "str",
                    "page": "str",
                    "tab": "str",
                    "context": "dict"
                },
                "examples": [
                    "Show me contract data for the last quarter",
                    "Generate a visualization of spending trends",
                    "Create a comprehensive analysis of defense contracting opportunities"
                ]
            },
            {
                "name": "tool_discovery",
                "description": "Dynamically discover available tools and capabilities from all MCP servers",
                "endpoint": "http://localhost:8001/orchestrator/discover_tools",
                "method": "POST",
                "parameters": {},
                "examples": [
                    "What tools are available?",
                    "Show me all system capabilities",
                    "Refresh the list of available services"
                ]
            },
            {
                "name": "system_status",
                "description": "Get comprehensive system status including server health and capabilities",
                "endpoint": "http://localhost:8001/orchestrator/system_status",
                "method": "GET",
                "parameters": {},
                "examples": [
                    "Check system health",
                    "Show server status",
                    "Display system overview"
                ]
            },
            {
                "name": "legacy_orchestration",
                "description": "Legacy routing for backward compatibility",
                "endpoint": "/legacy/route",
                "method": "POST",
                "parameters": {
                    "prompt": "str",
                    "user_id": "str",
                    "session_id": "str"
                },
                "examples": [
                    "Legacy routing support"
                ]
            }
        ]
    }

"""
MCP Chat Server for Data_Insights

This FastAPI app serves as the backend for the "chat with the data" feature. It receives chat requests from the UI, orchestrates LLM calls (Ollama: Mistral/Llama-3 for Q&A, Code Llama for code/visualization), queries the capture_insights database as needed, logs all interactions, and returns answers/visualizations to the UI.

Author: Data_Insights Team
"""

from fastapi import FastAPI, HTTPException, Query, Path, Body
from fastapi.responses import JSONResponse
from backend.data.models.data_models import ChatRequest, ChatResponse, NoteRequest, NoteDeleteRequest, NoteUpdateRequest, ChatHistoryRequest, VisualizationRequest, VisualizationResponse, ProfileGenerateRequest, ProfileGenerateResponse, DataSummaryResponse
# from backend.ai.llm_interface import query_llm  # Disabled: function not implemented yet
# from backend.core.notes import add_note, get_notes, delete_note, update_note, set_note_active  # Notes feature disabled
from backend.core.logger import log_chat_interaction, get_chat_history, engine
from sqlalchemy import text as sa_text
from typing import List
from datetime import datetime

app = FastAPI(title="MCP Chat Server", description="Backend for chat with the data feature.")

@app.get("/health")
async def health_check():
    """Health check endpoint for service discovery."""
    return {
        "name": "chat_server",
        "status": "healthy",
        "service_type": "chat",
        "version": "1.0.0",
        "description": "Conversational AI interface with domain expertise"
    }

@app.get("/capabilities")
async def get_capabilities():
    """Return server capabilities for dynamic service discovery."""
    return {
        "capabilities": [
            {
                "name": "chat",
                "description": "General Q&A and conversational responses with domain expertise in defense contracting",
                "endpoint": "http://localhost:8002/chat/route",
                "method": "POST",
                "parameters": {
                    "prompt": "str",
                    "user_id": "str",
                    "session_id": "str",
                    "page": "str",
                    "tab": "str"
                },
                "examples": [
                    "What are the key factors in defense contracting?",
                    "Explain the difference between prime and subcontract awards",
                    "How do I identify potential teaming partners?"
                ]
            },
            {
                "name": "visualization",
                "description": "Generate data visualizations and charts",
                "endpoint": "http://localhost:8002/visualization/route",
                "method": "POST",
                "parameters": {
                    "chart_type": "str",
                    "data_source": "str",
                    "filters": "dict"
                },
                "examples": [
                    "Create a bar chart of top agencies by spending",
                    "Generate a trend line for quarterly obligations",
                    "Show a pie chart of contract types"
                ]
            }
        ]
    }

# ...existing endpoints and logic from mcp_server.py...

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

# ...existing endpoints and logic from mcp_server.py...

"""
FastAPI-based chat endpoint for LLM/agent chat with Langfuse tracing.
UI-agnostic: can be called from Streamlit, React, Shiny, etc.
"""

from fastapi import FastAPI, Request
from pydantic import BaseModel
from typing import Optional, Dict, Any
import httpx
import os
from config import get_ollama_config, get_langfuse_config, get_prompt_repo_path
from .tracing import trace_llm_interaction

app = FastAPI()

# Pydantic model for chat requests
class ChatRequest(BaseModel):
    user_message: str
    context: Optional[str] = ""
    user_id: Optional[str] = None
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    trace_id: Optional[str] = None

# Helper to load prompt template
PROMPT_TEMPLATE_PATH = os.path.join(get_prompt_repo_path(), "default_chat_prompt.txt")
def load_prompt_template() -> str:
    with open(PROMPT_TEMPLATE_PATH, "r", encoding="utf-8") as f:
        return f.read()

# Helper to call Ollama LLM
async def call_ollama_llm(prompt: str, ollama_cfg: Dict[str, Any]) -> str:
    url = f"{ollama_cfg['OLLAMA_BASE_URL']}/api/generate"
    payload = {
        "model": ollama_cfg["OLLAMA_MODEL"],
        "prompt": prompt,
        "temperature": ollama_cfg["TEMPERATURE"],
        "max_tokens": ollama_cfg["MAX_TOKENS"],
    }
    async with httpx.AsyncClient() as client:
        resp = await client.post(url, json=payload, timeout=60)
        resp.raise_for_status()
        data = resp.json()
        return data.get("response") or data.get("text") or "[No response]"

@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    ollama_cfg = get_ollama_config()
    prompt_template = load_prompt_template()
    prompt = prompt_template.format(
        user_message=request.user_message,
        context=request.context or ""
    )
    # Call LLM
    llm_response = await call_ollama_llm(prompt, ollama_cfg)
    # Trace interaction
    trace = trace_llm_interaction(
        input_prompt=prompt,
        output=llm_response,
        metadata={
            "tool": "llm_chat",
            "user_id": request.user_id,
            "session_id": request.session_id,
        }
    )
    trace_id = getattr(trace, "id", None) if trace else None
    return ChatResponse(response=llm_response, trace_id=trace_id)

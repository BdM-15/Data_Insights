"""
Agentic Router API for orchestrator LLM intent parsing and tool dispatch.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Any, Dict, Optional
from backend.data.models.data_models import AgenticIntent
import requests
from .llm_prompt_template import ROSES_PROMPT_TEMPLATE, AGENTIC_TOOL_LIST
import logging
import os

router = APIRouter()

LLAMA3_MODEL = "llama3.1:8b"
OLLAMA_URL = "http://localhost:11434/api/chat"  # Switched to /api/chat for conversational context

logger = logging.getLogger("agentic_router")
logger.setLevel(logging.INFO)

try:
    LOG_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', 'logs'))
    LOG_PATH = os.path.join(LOG_DIR, 'agentic_router.log')
    os.makedirs(LOG_DIR, exist_ok=True)
    file_handler = logging.FileHandler(LOG_PATH)
    file_handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    file_handler.setFormatter(formatter)
    for h in logger.handlers[:]:
        logger.removeHandler(h)
    logger.addHandler(file_handler)
    print(f"[AgenticRouter] Logging to {LOG_PATH}")
    logger.info("[AgenticRouter] Logger initialized and ready.")
except Exception as log_setup_exc:
    print(f"[AgenticRouter] Logger setup failed: {log_setup_exc}")

def call_ollama_llm(prompt: str, model: str = LLAMA3_MODEL, chat_history=None) -> dict:
    """
    Calls the orchestrator LLM (llama3.1:8b) via Ollama /api/chat and returns the parsed intent dict.
    Maintains chat history for multi-turn conversations.
    """
    import json
    model_name = model if isinstance(model, str) else LLAMA3_MODEL
    if chat_history is None:
        # First message: system + user
        messages = [
            {"role": "system", "content": ROSES_PROMPT_TEMPLATE.format(
                tool_list=get_tool_list_text(),
                tool_names=get_tool_names(),
                user_prompt=""
            )},
            {"role": "user", "content": prompt}
        ]
    else:
        messages = chat_history + [{"role": "user", "content": prompt}]
    payload = {
        "model": model_name,
        "messages": messages
    }
    # Only log payload at DEBUG level to avoid log bloat
    logger.debug(f"[AgenticRouter] Sending payload to Ollama: {payload}")
    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=60, stream=True)
        response.raise_for_status()
        import json as _json
        content_fragments = []
        last_json = {}
        for line in response.iter_lines():
            if line:
                data = _json.loads(line.decode("utf-8"))
                # Ollama streaming: each chunk has 'content' under 'message' or at top level
                msg = data.get("message", data.get("response", ""))
                if isinstance(msg, dict):
                    frag = msg.get("content", "")
                elif isinstance(msg, str):
                    frag = msg
                else:
                    frag = str(msg)
                content_fragments.append(frag)
                last_json = data
        full_content = ''.join(content_fragments)
        try:
            parsed = _json.loads(full_content)
            return parsed
        except Exception as e:
            # If not valid JSON, return the raw string for chat fallback
            logger.warning(f"[AgenticRouter] LLM output is not valid JSON, returning raw string for chat: {e}")
            return full_content
    except Exception as e:
        logger.error(f"[AgenticRouter] Ollama call or JSON parse failed: {e}")
        raise HTTPException(status_code=500, detail=f"LLM call failed: {e}")

class AgenticRouteRequest(BaseModel):
    prompt: str
    context: Optional[Dict[str, Any]] = None

def get_tool_list_text():
    """
    Returns a formatted string of available tools/agents for the LLM prompt.
    """
    return '\n'.join([
        f"- {tool['name']}: {tool['description']}" for tool in AGENTIC_TOOL_LIST
    ])

def get_tool_names():
    """
    Returns a pipe-separated string of tool names for the prompt template.
    """
    return ' | '.join([tool['name'] for tool in AGENTIC_TOOL_LIST])

def build_llm_prompt(user_prompt: str) -> str:
    """
    Formats the ROSES prompt template with the tool list and user prompt.
    """
    return ROSES_PROMPT_TEMPLATE.format(
        tool_list=get_tool_list_text(),
        tool_names=get_tool_names(),
        user_prompt=user_prompt
    )

@router.post("/agentic/route")
def route_agentic_intent(request: AgenticRouteRequest):
    """
    Linear agentic workflow:
    1. Orchestrator LLM (llama3.1:8b) receives prompt/context and determines intent/tool/parameters.
    2. The orchestrator (this endpoint) dispatches to the correct specialized agent/tool, passing context/results down the chain.
    3. Each agent updates the context and returns its result up the chain.
    4. The orchestrator finalizes and returns the output to the user.
    """
    # 1. Build prompt for orchestrator LLM
    full_prompt = build_llm_prompt(request.prompt)
    logger.info(f"[AgenticRouter] User prompt: {request.prompt}")
    # Only log the full prompt at DEBUG level to avoid log bloat
    logger.debug(f"[AgenticRouter] Full LLM prompt: {full_prompt}")
    try:
        # 2. Call orchestrator LLM (llama3.1:8b) via Ollama
        llm_output = call_ollama_llm(full_prompt, request.context)
        # Only log a summary of the LLM output at INFO
        logger.info(f"[AgenticRouter] LLM output received.")
    except Exception as e:
        logger.error(f"[AgenticRouter] LLM call failed: {e} | User prompt: {request.prompt}")
        raise HTTPException(status_code=500, detail=f"LLM call failed: {e}")
    # 3. Parse LLM output as AgenticIntent
    # Flexible: if LLM output is a dict, treat as intent; if string, treat as chat reply
    if isinstance(llm_output, dict):
        try:
            intent = AgenticIntent(**llm_output)
            logger.info(f"[AgenticRouter] Routing intent: {intent.intent} | parameters: {intent.parameters}")
        except Exception as e:
            logger.error(f"[AgenticRouter] Invalid LLM output: {e} | Raw output: {llm_output} | User prompt: {request.prompt}")
            # If parsing fails, but output is a string, treat as chat reply
            if isinstance(llm_output.get('response'), str):
                result = {
                    "message": llm_output['response'],
                    "intent": None,
                    "llm_raw": llm_output
                }
                logger.info(f"[AgenticRouter] Final result dispatched (chat fallback on parse error).")
                return result
            raise HTTPException(status_code=400, detail=f"Invalid LLM output: {e}")
        # 4. Linear agent chain: pass context/results to specialized agent (stub)
        # If intent is 'chat', return the LLM's conversational reply (if present)
        if intent.intent == "chat":
            # Try to find a conversational reply in parameters or fallback to a generic message
            reply = None
            # Common keys the LLM might use for the reply
            for key in ("message", "reply", "response", "text", "answer", "content", "output"):
                if key in intent.parameters and isinstance(intent.parameters[key], str) and intent.parameters[key].strip():
                    reply = intent.parameters[key].strip()
                    break
            if not reply:
                # Fallback: echo the user prompt or a generic message
                reply = request.prompt
            result = {
                "message": reply,
                "intent": intent.dict(),
                "llm_raw": llm_output
            }
            logger.info(f"[AgenticRouter] Final result dispatched (chat reply).")
            return result
        # TODO: Implement actual agent/tool dispatch and context passing for other intents
        result = {
            "message": f"Dispatched to {intent.intent} with parameters {intent.parameters}",
            "intent": intent.dict(),
            "llm_raw": llm_output
        }
        logger.info(f"[AgenticRouter] Final result dispatched.")
        return result
    elif isinstance(llm_output, str):
        # If LLM output is a string, treat as a direct chat reply
        result = {
            "message": llm_output.strip(),
            "intent": None,
            "llm_raw": llm_output
        }
        logger.info(f"[AgenticRouter] Final result dispatched (chat direct string).")
        return result
    else:
        logger.error(f"[AgenticRouter] Unexpected LLM output type: {type(llm_output)} | Raw: {llm_output}")
        raise HTTPException(status_code=400, detail="Unexpected LLM output type.")

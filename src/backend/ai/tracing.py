"""
Centralized tracing utilities for LLM, agent, and MCP tool observability.
Loads all config from config.py (which reads from .env).
"""

import logging
from typing import Any, Dict, Optional
from config import get_app_config, get_ollama_config

# Import Langfuse and Pydantic AI tracing if available
try:
    from langfuse import Langfuse
    from pydantic_ai.tracing import Tracer as PydanticAITracer
except ImportError:
    Langfuse = None
    PydanticAITracer = None
    logging.warning("Langfuse or Pydantic AI not installed. Tracing will be disabled.")

# Load tracing config from environment via config.py
app_config = get_app_config()
ollama_config = get_ollama_config()

LANGFUSE_PUBLIC_KEY = app_config.get("LANGFUSE_PUBLIC_KEY") or None
LANGFUSE_SECRET_KEY = app_config.get("LANGFUSE_SECRET_KEY") or None
LANGFUSE_HOST = app_config.get("LANGFUSE_HOST", "http://localhost:3000")
LANGFUSE_PROJECT = app_config.get("LANGFUSE_PROJECT", "default")
LANGFUSE_ENVIRONMENT = app_config.get("LANGFUSE_ENVIRONMENT", "development")

# Initialize Langfuse client (singleton)
langfuse = None
if Langfuse and LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY:
    langfuse = Langfuse(
        public_key=LANGFUSE_PUBLIC_KEY,
        secret_key=LANGFUSE_SECRET_KEY,
        host=LANGFUSE_HOST,
        project=LANGFUSE_PROJECT,
        environment=LANGFUSE_ENVIRONMENT,
    )
else:
    logging.warning("Langfuse tracing is not fully configured or not installed.")

# Initialize Pydantic AI tracer (optional)
pydantic_ai_tracer = None
if PydanticAITracer and langfuse:
    pydantic_ai_tracer = PydanticAITracer(
        langfuse_client=langfuse,
        project=LANGFUSE_PROJECT,
        environment=LANGFUSE_ENVIRONMENT,
    )

def trace_llm_interaction(input_prompt: str, output: str, metadata: Optional[Dict[str, Any]] = None):
    """
    Trace a single LLM or agent interaction.
    Args:
        input_prompt: The prompt sent to the LLM/agent.
        output: The response from the LLM/agent.
        metadata: Optional dict of extra context (user, tool, etc.)
    """
    if langfuse:
        trace = langfuse.trace(
            name=metadata.get('tool', 'llm_interaction') if metadata else 'llm_interaction',
            input=input_prompt,
            output=output,
            metadata=metadata or {},
        )
        return trace
    else:
        logging.info(f"[Tracing Disabled] LLM interaction: {input_prompt[:80]} ... -> {output[:80]} ...")
        return None

def trace_pydantic_extraction(raw_output: str, parsed_result: Any, model_name: str, metadata: Optional[Dict[str, Any]] = None):
    """
    Trace a Pydantic AI extraction event.
    Args:
        raw_output: The raw LLM output.
        parsed_result: The validated/parsed result.
        model_name: Name of the Pydantic model used.
        metadata: Optional dict of extra context.
    """
    if pydantic_ai_tracer:
        trace = pydantic_ai_tracer.trace_extraction(
            raw_output=raw_output,
            parsed_result=parsed_result,
            model_name=model_name,
            metadata=metadata or {},
        )
        return trace
    else:
        logging.info(f"[Tracing Disabled] Pydantic extraction: {model_name} -> {parsed_result}")
        return None

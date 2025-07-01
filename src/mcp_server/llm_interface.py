"""
llm_interface.py

Handles all interactions with local LLMs via Ollama for the Data_Insights chat utility.
Supports:
- Mistral/Llama-3 for Q&A and general chat
- Code Llama for code/visualization generation

This module provides a single entry point (query_llm) for the MCP server to request LLM completions, keeping the main server logic clean and modular.

Author: Data_Insights Team
"""

from typing import Optional, Dict, Any
import plotly.io as pio
import traceback

# If you use an Ollama Python client, import it here (e.g., ollama or open-interpreter)
# import ollama


def query_llm(
    user_prompt: str,
    context_data: Optional[Dict[str, Any]] = None,
    model: str = "mistral",
    prompt_structure: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Query the local LLM (via Ollama) for an answer, code, or visualization.

    Args:
        user_prompt: The user's question or prompt.
        context_data: Optional dict of relevant data to provide context (e.g., dashboard data).
        model: Which LLM to use ("mistral", "llama3", "codellama").
        prompt_structure: Optional structured prompt for richer context.

    Returns:
        Dict with keys: answer (str), plotly_json (dict or None), llm_generated_code (str or None), response_type (str)
    """
    # --- Step 1: Build the prompt ---
    import requests
    import os
    import json
    # Combine user_prompt, context_data, and prompt_structure into a single prompt string for the LLM
    prompt = user_prompt
    if prompt_structure:
        prompt += f"\n\n[Prompt Structure]\n{json.dumps(prompt_structure, indent=2)}"
    if context_data:
        prompt += f"\n\n[Context Data]\n{json.dumps(context_data, indent=2)}"

    # --- Step 2: Call the LLM via Ollama REST API ---
    ollama_url = os.environ.get("OLLAMA_API_URL", "http://localhost:11434/api/generate")
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False
    }
    try:
        response = requests.post(ollama_url, json=payload, timeout=60)
        response.raise_for_status()
        data = response.json()
        answer = data.get("response") or data.get("message") or data.get("output") or "[No answer returned]"
    except Exception as e:
        answer = f"[Error calling Ollama: {e}]"

    # Visualization logic (codellama)
    if model == "codellama":
        # Optionally, parse code from LLM output and execute for plotly_json (advanced)
        return {
            "answer": answer,
            "plotly_json": None,
            "llm_generated_code": None,
            "response_type": "visualization"
        }
    return {
        "answer": answer,
        "plotly_json": None,
        "llm_generated_code": None,
        "response_type": "qa"
    }

# Reason: This module centralizes LLM logic, making it easy to maintain, extend, and test.

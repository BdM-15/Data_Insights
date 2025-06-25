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
    # Combine user_prompt, context_data, and prompt_structure into a single prompt string for the LLM
    # Reason: This allows the LLM to answer with full context and follow your prompt template
    # (Placeholder logic for now)
    prompt = user_prompt
    if prompt_structure:
        prompt += f"\n\n[Prompt Structure]\n{prompt_structure}"
    if context_data:
        prompt += f"\n\n[Context Data]\n{context_data}"

    # --- Step 2: Call the LLM via Ollama ---
    # TODO: Replace with actual Ollama API call
    # For now, return a dummy response
    if model == "codellama":
        # --- Step 1: Generate code using LLM (placeholder for Ollama call) ---
        # TODO: Replace with real Ollama call, e.g.:
        # response = ollama.generate(model="codellama", prompt=prompt)
        # llm_code = response['code']
        # For now, use a static code example:
        llm_code = (
            "import plotly.graph_objects as go\n"
            "fig = go.Figure([go.Bar(x=['A','B','C'], y=[10,20,15])])"
        )
        answer = f"[LLM-codellama] Here is a generated bar chart for: {user_prompt}"
        # --- Step 2: Safely execute the code to get a Plotly figure ---
        fig = None
        plotly_json = None
        exec_error = None
        local_vars = {}
        try:
            # Only allow plotly.graph_objects as go
            exec_globals = {"__builtins__": {}, "go": __import__("plotly.graph_objects", fromlist=["go"]).__dict__["go"]}
            exec(llm_code, exec_globals, local_vars)
            fig = local_vars.get("fig")
            if fig is not None:
                plotly_json = pio.to_json(fig, validate=False)
                plotly_json = pio.from_json(plotly_json)  # Return as dict
        except Exception as e:
            exec_error = traceback.format_exc()
            answer += f"\n[Error executing generated code: {e}]"
        return {
            "answer": answer,
            "plotly_json": plotly_json,
            "llm_generated_code": llm_code,
            "response_type": "visualization",
            "exec_error": exec_error
        }
    return {
        "answer": f"[LLM-{model}] This is a placeholder answer to: {user_prompt}",
        "plotly_json": None,
        "llm_generated_code": None,
        "response_type": "qa" if model != "codellama" else "code"
    }

# Reason: This module centralizes LLM logic, making it easy to maintain, extend, and test.

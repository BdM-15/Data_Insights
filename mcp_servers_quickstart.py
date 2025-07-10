"""
Quickstart script to start both MCP servers (agentic/orchestrator and chat) for Data_Insights.
Run this script with `python mcp_servers_quickstart.py` in your project root.
Then, in a separate terminal, run your Streamlit UI as before:
    streamlit run app.py
"""
import os
import sys
import threading
import uvicorn
import importlib
import subprocess

# Add the src directory to sys.path so 'backend' is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

def run_orchestrator_server():
    orchestrator_module = importlib.import_module("backend.ai.mcp_servers.orchestrator.orchestrator_server")
    uvicorn.run(orchestrator_module.app, host="0.0.0.0", port=8001, log_level="info")

def run_chat_server():
    chat_module = importlib.import_module("backend.ai.mcp_servers.chat.chat_server")
    uvicorn.run(chat_module.app, host="0.0.0.0", port=8002, log_level="info")

def run_database_schema_server():
    schema_module = importlib.import_module("backend.ai.mcp_servers.database_schema_server.database_schema_server")
    uvicorn.run(schema_module.app, host="0.0.0.0", port=8003, log_level="info")

def run_ollama_llm():
    # Start Ollama with llama3.1:8b model (if not already running)
    # This assumes 'ollama' is in PATH and model is pulled
    print("[INFO] Starting Ollama LLM server with llama3.1:8b...")
    subprocess.Popen(["ollama", "run", "llama3.1:8b"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

def start_mcp_servers():
    run_ollama_llm()
    t1 = threading.Thread(target=run_orchestrator_server, daemon=True)
    t2 = threading.Thread(target=run_chat_server, daemon=True)
    t3 = threading.Thread(target=run_database_schema_server, daemon=True)
    t1.start()
    t2.start()
    t3.start()
    print("[INFO] MCP servers started: Orchestrator (8001), Chat (8002), Database Schema (8003)")
    t1.join()
    t2.join()
    t3.join()

if __name__ == "__main__":
    start_mcp_servers()

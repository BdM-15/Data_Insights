"""
Temporary script to start both MCP servers (agentic/orchestrator and chat) for Data_Insights.
Run this script with `python temp_server_start.py` in your project root.
Then, in a separate terminal, run your Streamlit UI as before:
    streamlit run app.py
"""
import os
import sys
import threading
import uvicorn
import importlib

# Add the src directory to sys.path so 'backend' is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

def run_agentic_server():
    agentic_module = importlib.import_module("backend.ai.mcp_servers.agentic.agentic_server")
    uvicorn.run(agentic_module.app, host="0.0.0.0", port=8001, log_level="info")

def run_chat_server():
    chat_module = importlib.import_module("backend.ai.mcp_servers.chat.chat_server")
    uvicorn.run(chat_module.app, host="0.0.0.0", port=8002, log_level="info")

def start_mcp_servers():
    t1 = threading.Thread(target=run_agentic_server, daemon=True)
    t2 = threading.Thread(target=run_chat_server, daemon=True)
    t1.start()
    t2.start()
    print("[INFO] MCP servers started: Agentic (8001), Chat (8002)")
    t1.join()
    t2.join()

if __name__ == "__main__":
    start_mcp_servers()

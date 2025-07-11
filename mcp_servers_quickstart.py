"""
Simple MCP Servers Quickstart - Start all servers and test basic functionality

This script starts three MCP (Model Context Protocol) servers that work together:
1. Orchestrator Server - Routes requests to the right server
2. Chat Server - Handles conversational AI and visualizations  
3. Database Schema Server - Manages database queries and schema info

It also tests that all servers are healthy and can discover each other's capabilities.
"""
import os
import sys
import threading
import uvicorn
import importlib
import time
import requests
from colorama import Fore, Style, init

# Initialize colorama for colored terminal output (green checkmarks, red X's, etc.)
init(autoreset=True)

# Add the 'src' directory to Python's path so we can import our server modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

def start_orchestrator():
    """Start the Orchestrator server on port 8001 - this routes requests to other servers"""
    module = importlib.import_module("backend.ai.mcp_servers.orchestrator.orchestrator_server")
    uvicorn.run(module.app, host="0.0.0.0", port=8001, log_level="error")

def start_chat():
    """Start the Chat server on port 8002 - handles AI conversations and visualizations"""
    module = importlib.import_module("backend.ai.mcp_servers.chat.chat_server")
    uvicorn.run(module.app, host="0.0.0.0", port=8002, log_level="error")

def start_schema():
    """Start the Database Schema server on port 8003 - manages database queries and schema info"""
    module = importlib.import_module("backend.ai.mcp_servers.database_schema_server.database_schema_server")
    uvicorn.run(module.app, host="0.0.0.0", port=8003, log_level="error")

def start_ollama():
    """Check if Ollama (local AI model server) is running - required for AI functionality"""
    print(f"{Fore.CYAN}Starting Ollama...{Style.RESET_ALL}")
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            print(f"{Fore.GREEN}✓ Ollama already running{Style.RESET_ALL}")
        else:
            print(f"{Fore.RED}✗ Ollama not responding{Style.RESET_ALL}")
    except Exception as e:
        print(f"{Fore.RED}✗ Ollama failed: {e}{Style.RESET_ALL}")

def test_servers():
    """Test that all servers are healthy and can discover each other's capabilities"""
    time.sleep(5)  # Wait for servers to start up completely
    
    print(f"{Fore.CYAN}Testing servers...{Style.RESET_ALL}")
    servers = [(8001, "Orchestrator"), (8002, "Chat"), (8003, "Schema")]
    
    # Test each server's health endpoint
    for port, name in servers:
        try:
            r = requests.get(f"http://localhost:{port}/health", timeout=3)
            if r.status_code == 200:
                print(f"{Fore.GREEN}✓ {name} (port {port}): OK{Style.RESET_ALL}")
            else:
                print(f"{Fore.RED}✗ {name} (port {port}): HTTP {r.status_code}{Style.RESET_ALL}")
        except:
            print(f"{Fore.RED}✗ {name} (port {port}): Failed{Style.RESET_ALL}")
    
    # Test that the orchestrator can discover all available tools/capabilities
    print(f"\n{Fore.CYAN}Testing tool discovery...{Style.RESET_ALL}")
    try:
        r = requests.post("http://localhost:8001/orchestrator/discover_tools", timeout=10)
        if r.status_code == 200:
            data = r.json()
            total_tools = data['total_tools']
            server_count = data['server_count']
            if total_tools > 0:
                print(f"{Fore.GREEN}✓ Found {total_tools} tools from {server_count} servers{Style.RESET_ALL}")
            else:
                print(f"{Fore.YELLOW}⚠ Found {total_tools} tools from {server_count} servers (capabilities not being converted to tools){Style.RESET_ALL}")
        else:
            print(f"{Fore.RED}✗ Tool discovery failed: HTTP {r.status_code}{Style.RESET_ALL}")
    except Exception as e:
        print(f"{Fore.RED}✗ Tool discovery failed: {e}{Style.RESET_ALL}")
    
    # Test Phase 1 system status endpoint (required for AI Chat page)
    print(f"\n{Fore.CYAN}Testing Phase 1 system status...{Style.RESET_ALL}")
    try:
        r = requests.get("http://localhost:8001/orchestrator/system_status", timeout=5)
        if r.status_code == 200:
            status_data = r.json()
            print(f"{Fore.GREEN}✓ Phase 1 system status: {status_data['total_servers']} servers, {status_data['total_capabilities']} capabilities{Style.RESET_ALL}")
        else:
            print(f"{Fore.RED}✗ Phase 1 system status failed: HTTP {r.status_code}{Style.RESET_ALL}")
    except Exception as e:
        print(f"{Fore.RED}✗ Phase 1 system status failed: {e}{Style.RESET_ALL}")

if __name__ == "__main__":
    print("Starting MCP Servers...")
    
    # Step 1: Start Ollama first (required for AI functionality)
    start_ollama()
    
    print("\nStarting MCP servers...")
    # Step 2: Start all three servers in separate threads so they run simultaneously
    threading.Thread(target=start_orchestrator, daemon=True).start()
    threading.Thread(target=start_chat, daemon=True).start()
    threading.Thread(target=start_schema, daemon=True).start()
    
    # Step 3: Test that all servers are working and can communicate
    test_servers()
    
    print("\nServers running. Press Ctrl+C to stop.")
    try:
        # Keep the script running until user presses Ctrl+C
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping servers...")

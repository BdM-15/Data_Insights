#!/usr/bin/env python3
"""
Simple test script to check agent health
"""

import asyncio
import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.frontend.ai.llamaindex_mcp_communication import LangGraphOrchestratorAgent

async def test_agent_health():
    """Test the agent health check."""
    try:
        print("Creating agent...")
        agent = LangGraphOrchestratorAgent()
        
        print("Initializing agent...")
        await agent.initialize()
        
        print("Running health check...")
        health = await agent.health_check()
        
        print("\n=== Health Check Results ===")
        print(f"LLM Initialized: {health.get('llm_initialized')}")
        print(f"Agent Initialized: {health.get('agent_initialized')}")
        print(f"Total Tools: {health.get('total_tools')}")
        
        print("\nMCP Servers:")
        for name, info in health.get('mcp_servers', {}).items():
            status = info.get('status', 'unknown')
            print(f"  {name}: {status}")
            if status == 'error':
                print(f"    Error: {info.get('error', 'Unknown error')}")
        
        print("\nTesting simple chat...")
        response = await agent.chat_async("Hello!")
        print(f"Response: {response}")
        
        print("\n=== Test Completed Successfully ===")
        
    except Exception as e:
        print(f"Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_agent_health())

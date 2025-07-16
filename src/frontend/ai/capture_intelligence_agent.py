"""
Capture Intelligence Agent - Simplified

A streamlined business intelligence consultant for defense contracting.
Uses the centralized MCP Client Manager for tool access and focuses on
LLM orchestration and business logic.

Key simplifications:
- Uses MCPClientManager for all MCP interactions
- Eliminates manual JSON-RPC handling
- Cleaner LangGraph workflow
- Better error handling with graceful degradation
"""

import asyncio
import logging
import os
import sys
from typing import Dict, List, Any, Optional
from datetime import datetime

# Add backend path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../backend"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../.."))

# Import configuration
from config import (
    OLLAMA_MODEL, OLLAMA_TEMPERATURE, MAX_TOKENS, CONTEXT_WINDOW, 
    REQUEST_TIMEOUT, MAX_ITERATIONS
)

# LangChain imports
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_core.tools import tool

# LangGraph for agent orchestration
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from typing_extensions import TypedDict

# MCP Client Manager for centralized tool access
from src.backend.ai.mcp_client_manager import MCPClientManager

# Configure logging
logger = logging.getLogger(__name__)

# Agent state for LangGraph
class AgentState(TypedDict):
    """State for the agent workflow."""
    messages: List[HumanMessage | AIMessage | SystemMessage]
    current_query: Optional[str]
    context: Dict[str, Any]

class CaptureIntelligenceAgent:
    """
    Simplified Capture Intelligence Agent.
    
    Features:
    - Centralized MCP tool access
    - LangGraph workflow orchestration
    - Graceful error handling
    - Business intelligence specialization
    """
    
    def __init__(self):
        """Initialize the agent."""
        self.mcp_manager = MCPClientManager()
        self.llm = None
        self.tools = []
        self.workflow = None
        self._initialized = False
        
        # Strict, robust, and future-proof system prompt for LLM agent
        self.system_prompt = """
You are Roberto, a business intelligence agent for defense contracting. You have access to Model Context Protocol (MCP) tools for querying, analyzing, and reasoning over real-time data, including a connected database and other specialized sources.

**STRICT POLICY:**
For ANY factual, data-driven, or database question (such as database name, table schema, stats, or any information that could be retrieved from a tool), you MUST call the appropriate tool and use its output. You are NEVER allowed to answer from your own knowledge or memory for these questions, even if you think you know the answer. If you do not call a tool, you must respond: "I cannot answer this without calling a tool." If a question is ambiguous, ask clarifying questions before proceeding.

**For all other questions (not factual/database/tool-backed), use your full reasoning and expertise to provide the best possible answer.**
"""
        # Dynamic system prompt: always inject available tools and strict tool use policy
        # (Tool listing is handled dynamically in chat_async, not here)
        # The dynamic prompt is now fully strict and database-agnostic.
    
    async def initialize(self):
        """Initialize the agent with LLM and MCP connections."""
        if self._initialized:
            return
        
        logger.info("Initializing Capture Intelligence Agent...")
        
        # Initialize Ollama LLM
        self.llm = ChatOllama(
            model=OLLAMA_MODEL,
            temperature=OLLAMA_TEMPERATURE,
            timeout=REQUEST_TIMEOUT,
            # Performance optimizations
            num_ctx=CONTEXT_WINDOW,
            num_predict=MAX_TOKENS,
            top_k=40,
            top_p=0.9,
        )
        
        # Initialize MCP manager
        await self.mcp_manager.initialize()
        
        # Create LangChain tools from MCP tools
        await self._create_langchain_tools()
        
        # Build workflow
        self._build_workflow()
        
        self._initialized = True
        logger.info("Capture Intelligence Agent initialized successfully")
    
    async def _create_langchain_tools(self):
        """Create LangChain tools from MCP tools."""
        self.tools = []
        
        # Get available MCP tools
        available_tools = await self.mcp_manager.get_available_tools()
        
        for tool_info in available_tools:
            tool_name = tool_info["name"]
            tool_description = tool_info["description"]
            
            # Create a LangChain tool wrapper using correct syntax
            # LangChain @tool decorator doesn't support name parameter, so we use a different approach
            from langchain_core.tools import StructuredTool
            
            def create_mcp_tool_wrapper(name: str, description: str):
                """Factory function to create MCP tool wrapper."""
                async def mcp_tool_function(arguments: str):
                    """Wrapper for MCP tool calls."""
                    try:
                        # Parse arguments (assuming JSON string)
                        import json
                        args = json.loads(arguments) if arguments else {}
                        
                        # Call through MCP manager
                        result = await self.mcp_manager.call_tool(name, args)
                        return str(result)
                        
                    except Exception as e:
                        logger.error(f"Tool call failed: {e}")
                        return f"Error: {str(e)}"
                
                return StructuredTool.from_function(
                    func=mcp_tool_function,
                    name=name,
                    description=description
                )
            
            wrapped_tool = create_mcp_tool_wrapper(tool_name, tool_description)
            self.tools.append(wrapped_tool)
        
        logger.info(f"Created {len(self.tools)} LangChain tools")
    
    def _build_workflow(self):
        """Build the LangGraph workflow."""
        # Create tool node
        tool_node = ToolNode(self.tools)
        
        # Create workflow graph
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("agent", self._agent_node)
        workflow.add_node("tools", tool_node)
        
        # Add edges
        workflow.set_entry_point("agent")
        workflow.add_conditional_edges(
            "agent",
            self._should_continue,
            {
                "continue": "tools",
                "end": END
            }
        )
        workflow.add_edge("tools", "agent")
        
        # Compile workflow
        self.workflow = workflow.compile()
    
    async def _agent_node(self, state: AgentState):
        """Main agent reasoning node with dynamic tool awareness."""
        # Use dynamic system prompt from state context (if present)
        system_prompt = state["context"].get("system_prompt", self.system_prompt)
        messages = [SystemMessage(content=system_prompt)] + state["messages"]

        # Get LLM response
        response = await self.llm.ainvoke(messages)

        # Update state
        return {
            "messages": [response],
            "current_query": state.get("current_query"),
            "context": state.get("context", {})
        }
    
    def _should_continue(self, state: AgentState) -> str:
        """Determine if workflow should continue or end."""
        last_message = state["messages"][-1]
        
        # Check if LLM wants to use tools
        if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
            return "continue"
        else:
            return "end"
    
    async def chat_async(self, user_input: str, history: Optional[List[Dict[str, str]]] = None, debug: bool = False) -> Any:
        """
        Process user input and return response, supporting multi-turn conversation.
        Enforces a strict RAG loop: if the LLM calls a tool, execute it, append the tool output, and re-invoke the LLM for a final answer.
        For any factual/database/tool-backed question, always call the relevant tool and use its output. Never hallucinate.
        """
        if not self._initialized:
            await self.initialize()
        debug_info = {}
        try:
            # Check MCP health
            if not self.mcp_manager.is_healthy():
                logger.warning("MCP manager is unhealthy, working with limited capabilities")

            # Build conversation history
            messages = []
            if history:
                for msg in history:
                    if msg["role"] == "user":
                        messages.append(HumanMessage(content=msg["content"]))
                    elif msg["role"] == "assistant":
                        messages.append(AIMessage(content=msg["content"]))
                    elif msg["role"] == "system":
                        messages.append(SystemMessage(content=msg["content"]))
            # Add the new user message
            messages.append(HumanMessage(content=user_input))

            # --- Dynamic tool awareness ---
            available_tools = await self.mcp_manager.get_available_tools()
            if available_tools:
                tool_list = "\n".join([
                    f"- {tool['name']}: {tool['description']}" for tool in available_tools
                ])
                tool_prompt = f"\n\nYou currently have access to the following Model Context Protocol (MCP) tools:\n{tool_list}\n\nWhen asked about your tools or capabilities, always answer using this list."
            else:
                tool_prompt = "\n\nYou currently have no available MCP tools."

            dynamic_system_prompt = self.system_prompt.strip() + tool_prompt

            # Prepare initial state with dynamic system prompt in context
            initial_state = {
                "messages": messages,
                "current_query": user_input,
                "context": {"system_prompt": dynamic_system_prompt}
            }

            # --- Strict RAG loop ---
            # Always force a tool call for factual/database/tool-backed questions, regardless of LLM output
            def is_factual_query(user_input: str) -> bool:
                keywords = [
                    "database name", "what is the database", "current database", "which database",
                    "table schema", "list tables", "describe table", "database stats", "database statistics",
                    "show tables", "get table sample", "query database", "database info", "database information"
                ]
                lowered = user_input.lower()
                return any(kw in lowered for kw in keywords)

            if is_factual_query(user_input):
                # Always call the relevant tool for factual/database questions
                tool_name = "get_database_stats" if "database" in user_input.lower() else None
                # You can expand this logic to map other keywords to other tools as needed
                if tool_name:
                    tool_args = {}
                    tool_debug = {"tool_name": tool_name, "tool_args": tool_args, "forced": True}
                    try:
                        tool_result = await self.mcp_manager.call_tool(tool_name, tool_args)
                        if hasattr(tool_result, 'dict'):
                            tool_result_display = tool_result.dict()
                        else:
                            tool_result_display = tool_result
                        tool_debug["tool_result"] = tool_result_display
                        debug_info["tool_calls"].append(tool_debug)
                        # Format as JSON code block for LLM reliability
                        import json
                        tool_output_msg = f"Tool `{tool_name}` output:\n```json\n{json.dumps(tool_result_display, indent=2)}\n```\nPlease use this tool output to answer the user's question. Do not ignore or hallucinate."
                        messages.append(AIMessage(content=tool_output_msg))
                        # 2nd pass: re-invoke the LLM with tool output
                        initial_state2 = {
                            "messages": messages,
                            "current_query": user_input,
                            "context": {"system_prompt": dynamic_system_prompt}
                        }
                        result2 = await self.workflow.ainvoke(initial_state2)
                        final_message2 = result2["messages"][-1]
                        debug_info["llm_second_pass"] = str(final_message2)
                        if hasattr(final_message2, 'content'):
                            return final_message2.content, debug_info if debug else final_message2.content
                        else:
                            return str(final_message2), debug_info if debug else str(final_message2)
                    except Exception as e:
                        tool_debug["error"] = str(e)
                        debug_info["tool_calls"].append(tool_debug)
                        return f"I apologize, but I encountered an error while retrieving the database name: {e}", debug_info if debug else f"I apologize, but I encountered an error while retrieving the database name: {e}"
                else:
                    return "I cannot answer this without calling a tool.", debug_info if debug else "I cannot answer this without calling a tool."
            # For non-factual questions, let the LLM respond as usual
            result = await self.workflow.ainvoke(initial_state)
            final_message = result["messages"][-1]
            debug_info["llm_first_pass"] = str(final_message)
            debug_info["tool_calls"] = []
            if hasattr(final_message, 'content'):
                return final_message.content, debug_info if debug else final_message.content
            else:
                return str(final_message), debug_info if debug else str(final_message)
        except Exception as e:
            logger.error(f"Error in chat_async: {e}")
            debug_info["error"] = str(e)
            return f"I apologize, but I encountered an error: {str(e)}. Please try again or rephrase your question.", debug_info if debug else f"I apologize, but I encountered an error: {str(e)}. Please try again or rephrase your question."
    
    async def get_tool_status(self) -> Dict[str, Any]:
        """
        Get status of available tools.
        
        Returns:
            Dictionary with tool status information
        """
        if not self._initialized:
            return {"status": "not_initialized", "tools": []}
        
        # Get health status
        health_status = await self.mcp_manager.health_check()
        
        # Get available tools
        available_tools = await self.mcp_manager.get_available_tools()
        
        return {
            "status": "healthy" if self.mcp_manager.is_healthy() else "degraded",
            "server_health": health_status,
            "available_tools": available_tools,
            "total_tools": len(available_tools)
        }
    
    async def cleanup(self):
        """Clean shutdown of the agent."""
        logger.info("Cleaning up Capture Intelligence Agent...")
        
        if self.mcp_manager:
            await self.mcp_manager.cleanup()
        
        self._initialized = False
        logger.info("Agent cleanup completed")

# Create global agent instance for session persistence
_agent_instance = None

async def get_agent() -> CaptureIntelligenceAgent:
    """Get or create the global agent instance."""
    global _agent_instance
    
    if _agent_instance is None:
        _agent_instance = CaptureIntelligenceAgent()
        await _agent_instance.initialize()
    
    return _agent_instance

"""
Capture Intelligence Agent

A business intelligence consultant for defense contracting that specializes in:
- Contract data analysis and insights
- Competitive intelligence 
- Capture management support
- Strategic opportunity assessment

Uses LangGraph for modern tool orchestration and MCP servers for modular data access.
"""

import asyncio
import logging
import os
import sys
from typing import Dict, List, Any, Optional, Annotated
from datetime import datetime

# Add backend path for config
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../backend"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../.."))

# Import configuration
from config import (
    OLLAMA_MODEL, OLLAMA_TEMPERATURE, MAX_TOKENS, CONTEXT_WINDOW, 
    REQUEST_TIMEOUT, MAX_ITERATIONS
)

# Modern LangChain and LangGraph imports
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate

# LangGraph for modern agent orchestration
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from typing_extensions import TypedDict

# MCP Integration using official LangChain MCP adapters
try:
    from langchain_mcp_adapters import MCPToolkit
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    logging.warning("LangChain MCP adapters not available. Install with: pip install langchain-mcp-adapters")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AgentState(TypedDict):
    """State for the capture intelligence agent."""
    messages: Annotated[list, add_messages]
    tool_results: Optional[Dict[str, Any]]
    reasoning_steps: Optional[List[str]]

class CaptureIntelligenceAgent:
    """
    A specialized business intelligence consultant for defense contracting.
    
    This agent helps with:
    - Contract database analysis
    - Competitive intelligence
    - Opportunity assessment
    - Strategic recommendations
    
    Uses modern LangGraph for tool orchestration and MCP servers for data access.
    """
    
    def __init__(self, model_name: str = None, temperature: float = None):
        self.model_name = model_name or OLLAMA_MODEL
        self.temperature = temperature or OLLAMA_TEMPERATURE
        self.llm = None
        self.mcp_toolkit = None
        self.tools = []
        self.graph = None
        self._initialized = False
        
        logger.info(f"CaptureIntelligenceAgent initializing with model: {self.model_name}")
    
    async def initialize(self):
        """Initialize the agent with LLM, MCP tools, and LangGraph workflow."""
        if self._initialized:
            return
        
        logger.info("Starting Capture Intelligence Agent initialization...")
        
        # Initialize Ollama chat model
        self.llm = ChatOllama(
            model=self.model_name,
            temperature=self.temperature,
            num_predict=MAX_TOKENS,
            num_ctx=CONTEXT_WINDOW,
            request_timeout=REQUEST_TIMEOUT,
        )
        
        logger.info(f"Ollama LLM initialized: {self.model_name}")
        
        # Initialize MCP tools
        await self._initialize_mcp_tools()
        
        # Build LangGraph workflow
        self._build_langgraph_workflow()
        
        self._initialized = True
        logger.info("Capture Intelligence Agent initialization completed successfully")
    
    async def _initialize_mcp_tools(self):
        """Initialize MCP tools using official LangChain MCP adapters."""
        if not MCP_AVAILABLE:
            logger.warning("MCP adapters not available - agent will work without database tools")
            self.tools = []
            return
        
        try:
            # Initialize MCP toolkit pointing to our FastMCP database server
            self.mcp_toolkit = MCPToolkit()
            
            # Connect to our FastMCP database server on port 8003
            await self.mcp_toolkit.connect_to_server(
                "http://localhost:8003",
                server_name="database_schema_service"
            )
            
            # Get available tools from the MCP server
            self.tools = await self.mcp_toolkit.get_tools()
            
            logger.info(f"Successfully connected to MCP server with {len(self.tools)} tools:")
            for tool in self.tools:
                logger.info(f"  - {tool.name}: {tool.description}")
                
        except Exception as e:
            logger.error(f"Failed to connect to MCP server: {e}")
            logger.info("Agent will operate without database tools")
            self.tools = []
    
    def _build_langgraph_workflow(self):
        """Build the LangGraph workflow for tool orchestration."""
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("agent", self._agent_node)
        if self.tools:
            workflow.add_node("tools", ToolNode(self.tools))
        
        # Define workflow edges
        workflow.set_entry_point("agent")
        
        if self.tools:
            # If tools are available, agent can decide to use them
            workflow.add_conditional_edges(
                "agent",
                self._should_continue,
                {
                    "continue": "tools",
                    "end": END,
                }
            )
            workflow.add_edge("tools", "agent")
        else:
            # No tools available, just end after agent response
            workflow.add_edge("agent", END)
        
        # Compile the graph
        self.graph = workflow.compile()
        logger.info("LangGraph workflow compiled successfully")
    
    async def _agent_node(self, state: AgentState):
        """Main agent reasoning node."""
        system_prompt = self._create_system_prompt()
        
        # Build messages with system prompt
        messages = [SystemMessage(content=system_prompt)] + state["messages"]
        
        # If we have tools, bind them to the LLM
        if self.tools:
            llm_with_tools = self.llm.bind_tools(self.tools)
            response = await llm_with_tools.ainvoke(messages)
        else:
            response = await self.llm.ainvoke(messages)
        
        return {"messages": [response]}
    
    def _should_continue(self, state: AgentState):
        """Determine if the agent should continue with tool use or end."""
        last_message = state["messages"][-1]
        
        # If the last message has tool calls, continue to tools
        if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
            return "continue"
        else:
            return "end"
    
    def _create_system_prompt(self) -> str:
        """Create system prompt for the capture intelligence consultant."""
        tools_info = ""
        if self.tools:
            tool_names = [tool.name for tool in self.tools]
            tools_info = f"\n\nYou have access to these database tools: {', '.join(tool_names)}. Use them when users ask for specific data analysis, contract information, or database queries."
        
        return f"""You are Roberto, a senior business intelligence consultant specializing in defense contracting and capture management. Today is {datetime.now().strftime("%B %d, %Y")}.

Your expertise includes:
- Federal contract analysis and market intelligence
- Competitive landscape assessment
- Capture strategy development
- Opportunity qualification and prioritization
- Win probability analysis
- Defense industry trends and insights

Communication style:
- Be concise and professional
- Provide actionable insights
- Use data to support recommendations
- Explain complex concepts clearly
- Focus on business value and strategic implications

For simple greetings, respond briefly and offer to help with contract analysis or business intelligence questions.{tools_info}

Always aim to provide expert-level insights that help with strategic decision making in defense contracting."""
    
    async def chat_async(self, user_input: str, context: Dict[str, Any] = None) -> str:
        """
        Process user input using the LangGraph workflow.
        """
        if not self._initialized:
            await self.initialize()
        
        logger.info(f"Processing user input: {user_input[:100]}...")
        
        try:
            # Create initial state
            initial_state = {
                "messages": [HumanMessage(content=user_input)],
                "tool_results": None,
                "reasoning_steps": []
            }
            
            # Run the LangGraph workflow
            final_state = await self.graph.ainvoke(initial_state)
            
            # Extract the final response
            last_message = final_state["messages"][-1]
            response = last_message.content if hasattr(last_message, 'content') else str(last_message)
            
            logger.info(f"Generated response: {len(response)} characters")
            return response
                
        except Exception as e:
            logger.error(f"Error in chat_async: {e}")
            return f"I encountered an error processing your request: {e}"
    
    def chat(self, user_input: str, context: Dict[str, Any] = None) -> str:
        """Synchronous wrapper for chat functionality."""
        try:
            return asyncio.run(self.chat_async(user_input, context))
        except Exception as e:
            logger.error(f"Error in synchronous chat: {e}")
            return f"I encountered an error: {e}"
    
    async def health_check(self) -> Dict[str, Any]:
        """Comprehensive health check for the agent."""
        return {
            "agent_initialized": self._initialized,
            "llm_available": self.llm is not None,
            "mcp_available": MCP_AVAILABLE,
            "mcp_connected": self.mcp_toolkit is not None,
            "tools_count": len(self.tools),
            "available_tools": [tool.name for tool in self.tools] if self.tools else [],
            "model_name": self.model_name,
            "langgraph_ready": self.graph is not None
        }

# Alias for backward compatibility
class ModernAgent(CaptureIntelligenceAgent):
    """Backward compatibility alias."""
    pass

# Additional alias for current usage
class LangGraphOrchestratorAgent(CaptureIntelligenceAgent):
    """Backward compatibility alias."""
    pass

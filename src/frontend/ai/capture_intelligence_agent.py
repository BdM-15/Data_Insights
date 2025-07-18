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
from src.frontend.ai.agent_logger import AgentLogger
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
    REQUEST_TIMEOUT, MAX_ITERATIONS, BUSINESS_TERM_TO_COLUMN
)

# LangChain imports
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_core.tools import tool

# LangGraph for agent orchestration
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode

# MCP Client Manager for centralized tool access
from src.backend.ai.mcp_client_manager import MCPClientManager

# Configure logging
logger = logging.getLogger(__name__)

class CaptureIntelligenceAgent:
    def __init__(self):
        """Initialize the agent."""
        self.mcp_manager = MCPClientManager()
        self.llm = None
        self.tools = []
        self.workflow = None
        self._initialized = False
        # Set up robust file logging (overwrite all handlers to ensure only file logging)
        log_dir = os.path.join(os.path.dirname(__file__), '../../../logs')
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        log_file = os.path.join(log_dir, 'agent_test.log')
        self.logger = logging.getLogger('agent_test_logger')
        self.logger.setLevel(logging.INFO)
        # Remove all handlers first to avoid duplicate/console logging
        for handler in list(self.logger.handlers):
            self.logger.removeHandler(handler)
        file_handler = logging.FileHandler(log_file)
        formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
        # Reason: All debug and error info will be written to agent_test.log, not printed to terminal.
        # Enhanced system prompt for tool-calling reliability
        self.system_prompt = (
            "You are Roberto, a capture intelligence agent for federal government contracting. "
            "You interact with a PostgreSQL database using Model Context Protocol (MCP) tools.\n\n"
            "**CRITICAL INSTRUCTIONS:**\n"
            "- Always use the most recent tool output as your factual basis. Never answer from memory or fallback logic.\n"
            "- After every tool call, you will receive the tool output as a message. Use this output to reason, plan next steps, and answer the user’s question.\n"
            "- If the user asks about the database, always use the output of `list_tables` or `get_database_stats` to answer, never speculate.\n"
            "- Never reference a database or table name unless it was actually discovered by a tool or provided in configuration.\n"
            "- Never suggest calling a tool as a SQL function (e.g., never write `SELECT * FROM list_tables()`).\n\n"
            "**CHAIN-OF-THOUGHT REASONING:**\n"
            "- Think step by step.\n"
            "- Explain your reasoning and which tools you need to call before answering.\n"
            "- After each tool output, update your reasoning and decide if more information is needed.\n"
            "- When you have enough information, summarize the answer for the user, referencing only the real, discovered data.\n\n"
            "**DATA CONTEXT:**\n"
            "- The main database is typically `capture_insights` with schema `s3_processed`.\n"
            "- The main contract data is in the `usaspending_prime_awards` table.\n"
            "- For contract counts, use only records where `modification_number = '0'`.\n\n"
            "**TOOL CALLING FORMAT:**\n"
            "If you need to use a tool, respond in JSON with a 'tool_calls' key as per the OpenAI tool calling spec. Do not answer from memory. Always call a tool for any factual query."
        )
        # Dynamic system prompt: always inject available tools and strict tool use policy
        # (Tool listing is handled dynamically in chat_async, not here)
        # The dynamic prompt is now fully strict and database-agnostic.
    
    async def initialize(self):
        """Initialize the agent with LLM and MCP connections."""
        if self._initialized:
            return

        self.logger.info("Initializing Capture Intelligence Agent...")

        # Use a tool-calling-capable model (no experimental fallback)
        model_name = "llama3.1:8b"  # Use the user's specific model
        try:
            self.llm = ChatOllama(
                model=model_name,
                temperature=OLLAMA_TEMPERATURE,
                timeout=REQUEST_TIMEOUT,
                num_ctx=CONTEXT_WINDOW,
                num_predict=MAX_TOKENS,
                top_k=40,
                top_p=0.9,
            )
            self.logger.info(f"Using standard ChatOllama with model '{model_name}'; ensure model supports tool calling.")
        except Exception as e:
            self.logger.error(f"Failed to initialize LLM: {e}")
            raise

        # Initialize MCP manager
        await self.mcp_manager.initialize()

        # Create LangChain tools from MCP tools
        await self._create_langchain_tools()

        # Build workflow
        self._build_workflow()

        self._initialized = True
        self.logger.info("Capture Intelligence Agent initialized successfully")
    
    async def _create_langchain_tools(self):
        """Create LangChain tools from MCP tools."""
        self.tools = []
        
        # Get available MCP tools
        available_tools = await self.mcp_manager.get_available_tools()
        
        for tool_info in available_tools:
            tool_name = tool_info["name"]
            tool_description = tool_info["description"]
            
            # Create a LangChain tool wrapper using correct syntax
            from langchain_core.tools import StructuredTool
            from pydantic import BaseModel, Field
            from typing import Optional
            
            def create_mcp_tool_wrapper(name: str, description: str):
                """Factory function to create MCP tool wrapper."""
                
                # Define input schema for the tool based on tool type
                if name == "query_database":
                    class ToolInput(BaseModel):
                        sql_query: str = Field(description="SQL query to execute")
                elif name == "describe_table":
                    class ToolInput(BaseModel):
                        table_name: str = Field(description="Name of the table")
                        schema_name: str = Field(description="Schema name", default="public")
                elif name == "get_table_sample":
                    class ToolInput(BaseModel):
                        table_name: str = Field(description="Name of the table")
                        schema_name: str = Field(description="Schema name", default="public")
                        limit: Optional[int] = Field(description="Sample row limit", default=10)
                else:
                    class ToolInput(BaseModel):
                        table_name: Optional[str] = Field(description="Name of the table", default="")
                        schema_name: Optional[str] = Field(description="Schema name", default="public")

                from langchain_core.callbacks import CallbackManagerForToolRun

                def create_sync_wrapper(async_func, tool_args_map, name):
                    """Create a synchronous wrapper for async function."""
                    def sync_wrapper(**kwargs):
                        import asyncio

                        mapped_args = {}
                        if name == "query_database":
                            sql_query = kwargs.get("sql_query")
                            if sql_query:
                                mapped_args = {"sql_query": sql_query}
                        elif name == "describe_table":
                            table_name = kwargs.get("table_name")
                            schema_name = kwargs.get("schema_name", "public")
                            if table_name:
                                mapped_args = {"table_name": table_name, "schema_name": schema_name}
                        elif name == "get_table_sample":
                            table_name = kwargs.get("table_name")
                            schema_name = kwargs.get("schema_name", "public")
                            limit = kwargs.get("limit", 10)
                            if table_name:
                                mapped_args = {"table_name": table_name, "schema_name": schema_name, "limit": limit}
                        elif name in ["list_tables", "get_database_stats"]:
                            mapped_args = {}
                        else:
                            # Generic args for any other tool, filter out None/empty values
                            mapped_args = {k: v for k, v in kwargs.items() if v is not None and v != ""}

                        # Run the async function
                        try:
                            loop = asyncio.get_event_loop()
                        except RuntimeError:
                            # No event loop in current thread, create one
                            return asyncio.run(async_func(**mapped_args))

                        if loop.is_running():
                            # We're in an async context, need to handle carefully
                            import concurrent.futures
                            import threading

                            def run_in_thread():
                                new_loop = asyncio.new_event_loop()
                                asyncio.set_event_loop(new_loop)
                                try:
                                    return new_loop.run_until_complete(async_func(**mapped_args))
                                finally:
                                    new_loop.close()

                            with concurrent.futures.ThreadPoolExecutor() as executor:
                                future = executor.submit(run_in_thread)
                                return future.result()
                        else:
                            return loop.run_until_complete(async_func(**mapped_args))

                    return sync_wrapper
                
                async def mcp_tool_function(**kwargs):
                    """Async wrapper for MCP tool calls."""
                    try:
                        # Build arguments based on tool name
                        if name == "query_database":
                            args = {"sql_query": kwargs.get("sql_query", "")}
                        elif name == "describe_table":
                            args = {"table_name": kwargs.get("table_name", ""), "schema_name": kwargs.get("schema_name", "public")}
                        elif name == "get_table_sample":
                            args = {"table_name": kwargs.get("table_name", ""), "schema_name": kwargs.get("schema_name", "public"), "limit": kwargs.get("limit", 10)}
                        elif name in ["list_tables", "get_database_stats"]:
                            args = {}
                        else:
                            # Generic args for any other tool
                            args = {k: v for k, v in kwargs.items() if v}  # Remove empty values

                        # Call through MCP manager
                        result = await self.mcp_manager.call_tool(name, args)

                        # Patch: For query_database, ensure results is always a list
                        if name == "query_database" and hasattr(result, 'results'):
                            data = result.results
                            # If data is a dict, wrap in a list
                            if isinstance(data, dict):
                                self.logger.warning("query_database returned dict, wrapping in list for Pydantic validation.")
                                data = [data]
                                result.results = data
                            sql_query = args.get("sql_query", "").lower()
                            if len(data) == 1 and 'count' in str(data[0]).lower():
                                count_value = list(data[0].values())[0] if data[0] else 0
                                if "modification_number = '0'" in sql_query:
                                    return f"Contract count (base awards only): {count_value}"
                                elif "usaspending_prime_awards" in sql_query and "count" in sql_query:
                                    if "modification_number" not in sql_query:
                                        return f"Total records count (includes all modifications): {count_value}. Note: For actual contract count, filter by modification_number = '0'"
                                    else:
                                        return f"Query result: {count_value} contracts"
                                else:
                                    return f"Query result: {count_value} (count of records)"
                            else:
                                return f"Query results: {data}"
                        elif name == "list_tables" and hasattr(result, 'tables'):
                            return (
                                "Here are the real tables discovered in the database using the list_tables tool: "
                                f"{result.tables}\n"
                                "(Note: 'list_tables' is a tool, not a SQL function. Never call it as SQL; always use the tool interface.)"
                            )
                        elif name == "get_database_stats" and hasattr(result, 'stats'):
                            return f"Database statistics: {result.stats}"
                        else:
                            return str(result)

                    except Exception as e:
                        self.logger.error(f"Tool call failed: {e}")
                        return f"Error: {str(e)}"
                
                # Create sync wrapper
                sync_func = create_sync_wrapper(mcp_tool_function, {}, name)
                
                return StructuredTool.from_function(
                    func=sync_func,
                    name=name,
                    description=description,
                    args_schema=ToolInput
                )
            
            wrapped_tool = create_mcp_tool_wrapper(tool_name, tool_description)
            self.tools.append(wrapped_tool)
        
        self.logger.info(f"Created {len(self.tools)} LangChain tools")
    
    def _build_workflow(self):
        """Build the LangGraph workflow."""
        from langgraph.graph import StateGraph, END
        
        # Create custom tool node that captures debug info
        def custom_tool_node(state: Dict[str, Any]) -> Dict[str, Any]:
            """Custom tool node that captures tool calls in debug info."""
            debug_info = state.get("debug_info", {"tool_calls": [], "logs": []})
            messages = state["messages"]

            # Check if there are tool calls to process
            if messages and hasattr(messages[-1], 'tool_calls') and messages[-1].tool_calls:
                # Use the built-in ToolNode to execute tools
                tool_node = ToolNode(self.tools)
                result_state = tool_node.invoke(state)

                # Capture tool call info in debug_info
                for tool_call in messages[-1].tool_calls:
                    debug_info["tool_calls"].append({
                        "tool_name": tool_call["name"],
                        "tool_args": tool_call["args"],
                        "tool_id": tool_call["id"]
                    })

                # Inject tool output as a SystemMessage for LLM chain-of-thought
                # Find the tool output in the new messages (after tool_node.invoke)
                new_messages = result_state["messages"]
                if len(new_messages) > len(messages):
                    # Assume the new message is the tool output (from the tool call)
                    tool_output_msg = new_messages[-1]
                    # Format a human-readable summary for the LLM
                    tool_name = debug_info["tool_calls"][-1]["tool_name"] if debug_info["tool_calls"] else "tool"
                    tool_args = debug_info["tool_calls"][-1]["tool_args"] if debug_info["tool_calls"] else {}
                    tool_output_str = getattr(tool_output_msg, "content", str(tool_output_msg))
                    summary = f"TOOL OUTPUT ({tool_name}):\nArguments: {tool_args}\nResult: {tool_output_str}"
                    # Insert as a SystemMessage for the LLM to reason over
                    new_messages.append(SystemMessage(content=summary))
                    result_state["messages"] = new_messages

                # Update debug_info in the result state
                result_state["debug_info"] = debug_info
                return result_state
            else:
                return state
        
        # Create workflow graph with simple dictionary state
        workflow = StateGraph(dict)
        
        # Add nodes
        workflow.add_node("agent", self._agent_node)
        workflow.add_node("tools", custom_tool_node)
        
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
        self.graph = workflow.compile()
    
    async def _agent_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Main agent reasoning node with dynamic tool awareness."""
        try:
            messages = state["messages"]
            debug_info = state.get("debug_info", {"tool_calls": [], "logs": []})

            # Log the full message list sent to the LLM for debugging
            self.logger.info("Messages sent to LLM:")
            for idx, msg in enumerate(messages):
                self.logger.info(f"Message {idx}: role={getattr(msg, 'type', getattr(msg, 'role', 'unknown'))}, content={getattr(msg, 'content', str(msg))}")

            # Bind tools to LLM for tool calling
            llm_with_tools = self.llm.bind_tools(self.tools) if self.tools else self.llm

            # Get LLM response
            response = await llm_with_tools.ainvoke(messages)

            # Log raw LLM response for debugging
            self.logger.info(f"RAW LLM RESPONSE: {repr(response)}")
            debug_info["logs"].append({"llm_response": str(response)})

            # Capture tool calls in debug info
            if hasattr(response, 'tool_calls') and response.tool_calls:
                for tool_call in response.tool_calls:
                    debug_info["tool_calls"].append({
                        "tool_name": tool_call["name"],
                        "tool_args": tool_call["args"],
                        "tool_id": tool_call["id"]
                    })
            else:
                self.logger.warning("No tool_calls found in LLM response. Check model/tool compatibility and prompt.")

            # Add response to messages
            messages.append(response)

            # Update state
            state["messages"] = messages
            state["debug_info"] = debug_info

            return state

        except Exception as e:
            self.logger.error(f"Error in agent node: {e}")
            # Add error message to state
            error_msg = f"Error occurred: {str(e)}"
            state["messages"].append(AIMessage(content=error_msg))
            return state
    
    def _should_continue(self, state: Dict[str, Any]) -> str:
        """Determine if workflow should continue or end."""
        messages = state["messages"]
        if not messages:
            return "end"
            
        last_message = messages[-1]
        
        # Check if LLM wants to use tools
        if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
            return "continue"
        else:
            return "end"
    
    async def chat_async(self, user_input: str, history: Optional[List[Dict[str, str]]] = None, debug: bool = False) -> Any:
        """
        Conversational loop: always discover real tables and columns before answering. Never assume table/column names. Uses LangGraph workflow.
        """
        debug_info = {"tool_calls": [], "logs": []}
        
        if not self.mcp_manager.is_healthy():
            self.logger.warning("MCP manager is unhealthy, working with limited capabilities")

        # Always discover real tables at the start
        available_tables = []
        try:
            available_tables = await self.mcp_manager.call_tool("list_tables", {})
        except Exception as e:
            self.logger.error(f"Failed to call list_tables: {e}")
            if debug:
                return f"Error: Could not list tables: {e}", debug_info
            else:
                return f"Error: Could not list tables: {e}"

        # Debug: Log the actual structure of available_tables
        self.logger.info(f"list_tables returned: type={type(available_tables)}, value={available_tables}")

        # Handle both Pydantic model and raw list formats
        if hasattr(available_tables, 'tables'):
            # Pydantic ListTablesOutput model
            tables_list = available_tables.tables
        elif isinstance(available_tables, list):
            # Raw list format
            tables_list = available_tables
        else:
            self.logger.error(f"Expected list or ListTablesOutput from list_tables, got: {type(available_tables)}")
            raise ValueError(f"Expected list or ListTablesOutput from list_tables, got: {type(available_tables)}")

        # Enforce strict format: list of dicts with 'table_name' key
        table_names = []
        if tables_list:
            for t in tables_list:
                if not (isinstance(t, dict) and 'table_name' in t):
                    self.logger.error(f"Invalid format from list_tables: expected dict with 'table_name', got: {t}")
                    raise ValueError(f"Invalid format from list_tables: expected dict with 'table_name', got: {t}")
                table_names.append(t['table_name'])
        table_list_str = ", ".join(table_names) if table_names else "(none)"


        # Build conversation history, always inject dynamic system prompt as the first message
        available_tools = await self.mcp_manager.get_available_tools()
        if available_tools:
            tool_list = "\n".join([
                f"- {tool['name']}: {tool['description']}" for tool in available_tools
            ])
            tool_prompt = f"\n\nYou currently have access to the following Model Context Protocol (MCP) tools:\n{tool_list}\n\nWhen asked about your tools or capabilities, always answer using this list."
        else:
            tool_prompt = "\n\nYou currently have no available MCP tools."

        # Inject real table list into the system prompt
        dynamic_system_prompt = self.system_prompt.strip() + f"\n\n**REAL TABLES IN s3_processed:** {table_list_str}" + tool_prompt

        messages = [SystemMessage(content=dynamic_system_prompt)]
        if history:
            for msg in history:
                if msg["role"] == "user":
                    messages.append(HumanMessage(content=msg["content"]))
                elif msg["role"] == "assistant":
                    messages.append(AIMessage(content=msg["content"]))
                elif msg["role"] == "system":
                    # Never allow a second system message, skip
                    continue
        messages.append(HumanMessage(content=user_input))

        # Initial state
        state = {
            "messages": messages,
            "debug_info": debug_info,
            "table_names": table_names
        }

        # Run the LangGraph workflow
        try:
            final_state = await self.graph.ainvoke(state)
            
            # Extract the final response
            final_messages = final_state.get("messages", [])
            if final_messages:
                final_response = final_messages[-1].content if hasattr(final_messages[-1], 'content') else str(final_messages[-1])
            else:
                final_response = "I apologize, but I could not process your request."
            
            # Post-processing: Remove or correct hallucinated database/table names
            if final_response:
                # Remove or correct any hallucinated database names
                # Only allow discovered database name(s) and tables
                allowed_db_names = ["capture_insights"]  # Add more if discovered dynamically
                for db_name in ["usaspending_subawards", "other_fake_db", "test_db"]:
                    if db_name in final_response:
                        final_response = final_response.replace(db_name, allowed_db_names[0])
                # Remove any suggestion of calling tools as SQL functions
                if "select * from list_tables()" in final_response.lower():
                    final_response = final_response.replace("SELECT * FROM list_tables() WHERE table_name LIKE '%usaspending_prime_awards%';", "(Use the list_tables tool and filter results in Python/LLM, not SQL)")
            
            if debug:
                return final_response, final_state.get("debug_info", debug_info)
            else:
                return final_response
                
        except Exception as e:
            self.logger.error(f"Error in LangGraph workflow: {e}")
            error_msg = f"Error occurred during conversation: {str(e)}"
            if debug:
                return error_msg, debug_info
            else:
                return error_msg
    
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
        self.logger.info("Cleaning up Capture Intelligence Agent...")
        
        if self.mcp_manager:
            await self.mcp_manager.cleanup()
        
        self._initialized = False
        self.logger.info("Agent cleanup completed")

# Create global agent instance for session persistence
_agent_instance = None

async def get_agent() -> CaptureIntelligenceAgent:
    """Get or create the global agent instance."""
    global _agent_instance
    
    if _agent_instance is None:
        _agent_instance = CaptureIntelligenceAgent()
        await _agent_instance.initialize()
    
    return _agent_instance

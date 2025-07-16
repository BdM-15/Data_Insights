"""
MCP Client Manager

Centralized MCP client management using the official MCP Python SDK.
Handles connection lifecycle, tool discovery, and error recovery for all MCP servers.

This replaces the manual JSON-RPC handling with proper SDK usage and provides
a clean interface for the Capture Intelligence Agent.
"""

import asyncio
import logging
import sys
import os
from typing import Dict, List, Any, Optional
from pathlib import Path

# Official MCP SDK imports
from mcp.client.stdio import StdioServerParameters, stdio_client
from mcp.client.session import ClientSession
from mcp import types

# Configure logging
logger = logging.getLogger(__name__)

class MCPClientManager:
    """
    Centralized MCP client management using official SDK.
    
    Features:
    - Connection lifecycle management
    - Tool discovery and routing
    - Health monitoring and recovery
    - Graceful error handling
    """
    
    def __init__(self):
        """Initialize the MCP client manager."""
        self.sessions: Dict[str, ClientSession] = {}  # server_name -> session
        self.tools: Dict[str, str] = {}  # tool_name -> server_name
        self.health_status: Dict[str, bool] = {}  # server_name -> is_healthy
        self.server_params: Dict[str, StdioServerParameters] = {}  # server_name -> params
        self._initialized = False
    
    async def initialize(self):
        """Initialize all MCP server connections."""
        if self._initialized:
            return
        
        logger.info("Initializing MCP Client Manager...")
        
        # Initialize database server
        await self._initialize_database_server()
        
        self._initialized = True
        logger.info("MCP Client Manager initialized successfully")
    
    async def _initialize_database_server(self):
        """Initialize the database MCP server connection."""
        server_name = "database"
        
        try:
            # Path to the database server
            server_path = Path(__file__).parent.parent / "mcp_servers" / "data_insights_database" / "fastmcp_database_server.py"
            
            # Create server parameters
            server_params = StdioServerParameters(
                command=sys.executable,
                args=[str(server_path)],
                env=dict(os.environ)
            )
            
            self.server_params[server_name] = server_params
            
            # Establish connection using official SDK
            async with stdio_client(server_params) as (read, write):
                # Create client session
                session = ClientSession(read, write)
                
                # Initialize the session (critical for protocol compliance)
                await session.initialize()
                
                # Store the session
                self.sessions[server_name] = session
                
                # Discover available tools
                tools_result = await session.list_tools()
                
                # Register tools
                for tool in tools_result.tools:
                    self.tools[tool.name] = server_name
                    logger.info(f"Registered tool: {tool.name}")
                
                # Mark as healthy
                self.health_status[server_name] = True
                
                logger.info(f"Database server initialized with {len(tools_result.tools)} tools")
                
        except Exception as e:
            logger.error(f"Failed to initialize database server: {e}")
            self.health_status[server_name] = False
            # Don't raise - allow graceful degradation
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """
        Call a tool through the appropriate MCP server.
        
        Args:
            tool_name: Name of the tool to call
            arguments: Arguments to pass to the tool
            
        Returns:
            Tool execution result
            
        Raises:
            ValueError: If tool is not found or server is unhealthy
        """
        # Check if tool exists
        if tool_name not in self.tools:
            raise ValueError(f"Tool '{tool_name}' not found. Available tools: {list(self.tools.keys())}")
        
        # Get server for this tool
        server_name = self.tools[tool_name]
        
        # Check server health
        if not self.health_status.get(server_name, False):
            raise ValueError(f"Server '{server_name}' is unhealthy")
        
        # Get session
        session = self.sessions.get(server_name)
        if not session:
            raise ValueError(f"No active session for server '{server_name}'")
        
        try:
            # Call the tool using official SDK
            result = await session.call_tool(tool_name, arguments)
            
            # Extract text content from result
            if result.content:
                # Return the text content from the first item
                return result.content[0].text if hasattr(result.content[0], 'text') else str(result.content[0])
            else:
                return "No content returned from tool"
                
        except Exception as e:
            logger.error(f"Tool call failed for '{tool_name}': {e}")
            # Mark server as unhealthy
            self.health_status[server_name] = False
            raise ValueError(f"Tool call failed: {e}")
    
    async def get_available_tools(self) -> List[Dict[str, Any]]:
        """
        Get list of all available tools across all servers.
        
        Returns:
            List of tool information dictionaries
        """
        available_tools = []
        
        for server_name, session in self.sessions.items():
            if self.health_status.get(server_name, False):
                try:
                    tools_result = await session.list_tools()
                    for tool in tools_result.tools:
                        available_tools.append({
                            "name": tool.name,
                            "description": tool.description,
                            "server": server_name
                        })
                except Exception as e:
                    logger.warning(f"Failed to get tools from server '{server_name}': {e}")
                    self.health_status[server_name] = False
        
        return available_tools
    
    async def health_check(self) -> Dict[str, bool]:
        """
        Check health of all MCP servers.
        
        Returns:
            Dictionary mapping server names to health status
        """
        health_results = {}
        
        for server_name, session in self.sessions.items():
            try:
                # Try to list tools as a health check
                await session.list_tools()
                health_results[server_name] = True
                self.health_status[server_name] = True
            except Exception as e:
                logger.warning(f"Health check failed for server '{server_name}': {e}")
                health_results[server_name] = False
                self.health_status[server_name] = False
        
        return health_results
    
    async def cleanup(self):
        """Clean shutdown of all MCP connections."""
        logger.info("Cleaning up MCP Client Manager...")
        
        # Close all sessions
        for server_name, session in self.sessions.items():
            try:
                # Note: ClientSession cleanup is handled by context manager
                logger.info(f"Cleaned up session for server '{server_name}'")
            except Exception as e:
                logger.warning(f"Error cleaning up session for '{server_name}': {e}")
        
        # Clear state
        self.sessions.clear()
        self.tools.clear()
        self.health_status.clear()
        self._initialized = False
        
        logger.info("MCP Client Manager cleanup completed")
    
    def is_healthy(self, server_name: str = None) -> bool:
        """
        Check if a specific server or all servers are healthy.
        
        Args:
            server_name: Optional specific server to check
            
        Returns:
            True if healthy, False otherwise
        """
        if server_name:
            return self.health_status.get(server_name, False)
        else:
            # Return True if at least one server is healthy
            return any(self.health_status.values())

"""
Data Insights MCP Servers Package

This package contains all FastMCP servers for the Data Insights platform.
Each server is organized in its own subdirectory for clean separation.

Architecture:
- FastMCP (official high-level MCP implementation)
- SSE transport for persistent client-server communication
- Automatic server discovery and health monitoring
- Future-proof tool registration system

Available Servers:
- data_insights_database: Database schema introspection and query execution
"""

# FastMCP servers are executable, not importable
# Use server files directly for server operations

__all__ = []

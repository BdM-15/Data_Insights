"""
Data Insights Database MCP Server Package

This package contains the FastMCP server for database schema introspection
and query execution capabilities.
"""

from .fastmcp_database_server import mcp as database_server

__all__ = ["database_server"]

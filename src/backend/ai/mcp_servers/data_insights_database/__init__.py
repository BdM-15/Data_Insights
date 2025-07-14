"""
Data Insights Database MCP Server Package

This package contains the Python MCP SDK server for database schema introspection
and query execution capabilities.

Architecture:
- Python MCP SDK (official implementation)
- Stdio transport for reliable communication
- Centralized configuration via config.py
- Production-ready error handling and logging
"""

from .python_mcp_database_server import server as database_server

__all__ = ["database_server"]

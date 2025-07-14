"""
Data Insights MCP Servers Package

This package contains all Python MCP SDK servers for the Data Insights platform.
Each server is organized in its own subdirectory for clean separation.

Architecture:
- Python MCP SDK (official implementation)
- Stdio transport for reliable client-server communication
- Automatic server discovery and health monitoring
- Future-proof tool registration system

Available Servers:
- data_insights_database: Database schema introspection and query execution
"""

# Import available servers
from .data_insights_database import database_server

__all__ = ["database_server"]

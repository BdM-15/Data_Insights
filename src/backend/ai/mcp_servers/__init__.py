"""
Data Insights MCP Servers Package

This package contains all FastMCP servers for the Data Insights platform.
Each server is organized in its own subdirectory for clean separation.

Available Servers:
- data_insights_database: Database schema introspection and query execution
"""

# Import available servers
from .data_insights_database import database_server

__all__ = ["database_server"]

#!/usr/bin/env python3
"""
Python MCP Database Server using Official MCP SDK

This is the official Python MCP SDK replacement for the FastMCP Database Server.
It provides the same 4 database tools but with a pure Python implementation
that should resolve the "Event loop is closed" issues.

Based on official Python MCP SDK examples from:
https://github.com/modelcontextprotocol/python-sdk
"""

import asyncio
import logging
import sys
from typing import Any, Dict, List

import asyncpg
import click
import mcp.types as types
from mcp.server.lowlevel import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database configuration (will be loaded from config.py)
DATABASE_CONFIG = {
    "host": "localhost",
    "port": 5433,
    "database": "usaspending",
    "user": "postgres",
    "password": "your_password"  # Will be loaded from config.py
}

# Create server instance
server = Server("data-insights-database")


@server.list_tools()
async def list_tools() -> List[types.Tool]:
    """
    List available database tools.
    
    Returns:
        List of available tools for database operations
    """
    return [
        types.Tool(
            name="get_database_schema",
            description="Get comprehensive database schema information including all schemas, tables, and basic statistics",
            inputSchema={
                "type": "object",
                "properties": {
                    "schema_name": {
                        "type": "string",
                        "description": "Optional schema name to filter results (e.g., 's3_processed', 's2_interim', 's1_raw')"
                    }
                },
                "additionalProperties": False
            }
        ),
        types.Tool(
            name="get_table_info",
            description="Get detailed information about a specific table including column details, row count, and sample data",
            inputSchema={
                "type": "object",
                "properties": {
                    "table_name": {
                        "type": "string",
                        "description": "Name of the table to analyze"
                    },
                    "schema_name": {
                        "type": "string",
                        "description": "Schema name (default: s3_processed)",
                        "default": "s3_processed"
                    }
                },
                "required": ["table_name"],
                "additionalProperties": False
            }
        ),
        types.Tool(
            name="execute_sql_query",
            description="Execute SQL queries with safety checks. Use for data analysis and business intelligence queries",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "SQL query to execute (SELECT statements only for safety)"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of rows to return (default: 100, max: 1000)",
                        "default": 100,
                        "minimum": 1,
                        "maximum": 1000
                    }
                },
                "required": ["query"],
                "additionalProperties": False
            }
        ),
        types.Tool(
            name="get_server_status",
            description="Get database server status and connection information",
            inputSchema={
                "type": "object",
                "properties": {},
                "additionalProperties": False
            }
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[types.ContentBlock]:
    """
    Handle tool execution.
    
    Args:
        name: Name of the tool to execute
        arguments: Tool arguments
        
    Returns:
        List of content blocks with tool results
    """
    try:
        if name == "get_database_schema":
            return await handle_get_database_schema(arguments)
        elif name == "get_table_info":
            return await handle_get_table_info(arguments)
        elif name == "execute_sql_query":
            return await handle_execute_sql_query(arguments)
        elif name == "get_server_status":
            return await handle_get_server_status(arguments)
        else:
            raise ValueError(f"Unknown tool: {name}")
            
    except Exception as e:
        logger.error(f"Error executing tool {name}: {e}")
        return [types.TextContent(
            type="text",
            text=f"Error executing {name}: {str(e)}"
        )]


async def handle_get_database_schema(arguments: Dict[str, Any]) -> List[types.ContentBlock]:
    """Handle get_database_schema tool execution."""
    schema_filter = arguments.get("schema_name")
    
    try:
        conn = await asyncpg.connect(**DATABASE_CONFIG)
        
        # Query to get schema information
        if schema_filter:
            query = """
                SELECT schemaname, tablename, 
                       pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
                FROM pg_tables 
                WHERE schemaname = $1
                ORDER BY schemaname, tablename;
            """
            rows = await conn.fetch(query, schema_filter)
        else:
            query = """
                SELECT schemaname, tablename,
                       pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
                FROM pg_tables 
                WHERE schemaname IN ('public', 'app_logs', 's3_processed', 's2_interim', 's1_raw')
                ORDER BY schemaname, tablename;
            """
            rows = await conn.fetch(query)
        
        await conn.close()
        
        # Format results
        schema_info = {}
        for row in rows:
            schema = row['schemaname']
            if schema not in schema_info:
                schema_info[schema] = []
            schema_info[schema].append({
                'table': row['tablename'],
                'size': row['size']
            })
        
        # Create formatted response
        result_text = "Database Schema Information:\n\n"
        for schema, tables in schema_info.items():
            result_text += f"Schema: {schema}\n"
            for table in tables:
                result_text += f"  - {table['table']} (Size: {table['size']})\n"
            result_text += "\n"
        
        return [types.TextContent(type="text", text=result_text)]
        
    except Exception as e:
        logger.error(f"Error in get_database_schema: {e}")
        raise


async def handle_get_table_info(arguments: Dict[str, Any]) -> List[types.ContentBlock]:
    """Handle get_table_info tool execution."""
    table_name = arguments["table_name"]
    schema_name = arguments.get("schema_name", "s3_processed")
    
    try:
        conn = await asyncpg.connect(**DATABASE_CONFIG)
        
        # Get table information
        info_query = """
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns
            WHERE table_schema = $1 AND table_name = $2
            ORDER BY ordinal_position;
        """
        columns = await conn.fetch(info_query, schema_name, table_name)
        
        # Get row count
        count_query = f"SELECT COUNT(*) as row_count FROM {schema_name}.{table_name};"
        count_result = await conn.fetchrow(count_query)
        row_count = count_result['row_count'] if count_result else 0
        
        await conn.close()
        
        # Format response
        result_text = f"Table Information: {schema_name}.{table_name}\n"
        result_text += f"Row Count: {row_count:,}\n\n"
        result_text += "Columns:\n"
        
        for col in columns:
            nullable = "NULL" if col['is_nullable'] == 'YES' else "NOT NULL"
            default = f" DEFAULT {col['column_default']}" if col['column_default'] else ""
            result_text += f"  - {col['column_name']}: {col['data_type']} {nullable}{default}\n"
        
        return [types.TextContent(type="text", text=result_text)]
        
    except Exception as e:
        logger.error(f"Error in get_table_info: {e}")
        raise


async def handle_execute_sql_query(arguments: Dict[str, Any]) -> List[types.ContentBlock]:
    """Handle execute_sql_query tool execution."""
    query = arguments["query"].strip()
    limit = arguments.get("limit", 100)
    
    # Safety checks
    query_upper = query.upper()
    if not query_upper.startswith("SELECT"):
        raise ValueError("Only SELECT queries are allowed for safety")
    
    dangerous_keywords = ["DELETE", "DROP", "INSERT", "UPDATE", "ALTER", "CREATE", "TRUNCATE"]
    if any(keyword in query_upper for keyword in dangerous_keywords):
        raise ValueError("Query contains potentially dangerous keywords")
    
    try:
        conn = await asyncpg.connect(**DATABASE_CONFIG)
        
        # Add LIMIT if not present
        if "LIMIT" not in query_upper:
            query += f" LIMIT {limit}"
        
        rows = await conn.fetch(query)
        await conn.close()
        
        if not rows:
            return [types.TextContent(type="text", text="Query executed successfully. No results returned.")]
        
        # Format results
        result_text = f"Query Results ({len(rows)} rows):\n\n"
        
        # Get column names
        columns = list(rows[0].keys())
        
        # Create header
        header = " | ".join(columns)
        result_text += header + "\n"
        result_text += "-" * len(header) + "\n"
        
        # Add data rows
        for row in rows:
            row_data = " | ".join(str(row[col]) for col in columns)
            result_text += row_data + "\n"
        
        return [types.TextContent(type="text", text=result_text)]
        
    except Exception as e:
        logger.error(f"Error in execute_sql_query: {e}")
        raise


async def handle_get_server_status(arguments: Dict[str, Any]) -> List[types.ContentBlock]:
    """Handle get_server_status tool execution."""
    try:
        conn = await asyncpg.connect(**DATABASE_CONFIG)
        
        # Get server version and status
        version_result = await conn.fetchrow("SELECT version();")
        version = version_result['version'] if version_result else "Unknown"
        
        # Get database size
        size_result = await conn.fetchrow(
            "SELECT pg_size_pretty(pg_database_size(current_database())) as db_size;"
        )
        db_size = size_result['db_size'] if size_result else "Unknown"
        
        await conn.close()
        
        result_text = "Database Server Status:\n\n"
        result_text += f"Version: {version}\n"
        result_text += f"Database: {DATABASE_CONFIG['database']}\n"
        result_text += f"Host: {DATABASE_CONFIG['host']}:{DATABASE_CONFIG['port']}\n"
        result_text += f"Database Size: {db_size}\n"
        result_text += "Status: Connected and operational\n"
        
        return [types.TextContent(type="text", text=result_text)]
        
    except Exception as e:
        logger.error(f"Error in get_server_status: {e}")
        raise


@click.command()
@click.option("--log-level", default="INFO", help="Logging level")
def main(log_level: str):
    """
    Main entry point for the Python MCP Database Server.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
    """
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    logger.info("Starting Python MCP Database Server...")
    
    # Run the server
    asyncio.run(run_server())


async def run_server():
    """Run the MCP server using stdio transport."""
    try:
        # Test database connection
        logger.info("Testing database connection...")
        conn = await asyncpg.connect(**DATABASE_CONFIG)
        await conn.close()
        logger.info("Database connection successful")
        
        # Start MCP server
        async with stdio_server() as (read_stream, write_stream):
            logger.info("MCP Server started with stdio transport")
            await server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="data-insights-database",
                    server_version="1.0.0",
                    capabilities=server.get_capabilities(
                        notification_options={},
                        experimental_capabilities={}
                    )
                )
            )
    except Exception as e:
        logger.error(f"Server error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

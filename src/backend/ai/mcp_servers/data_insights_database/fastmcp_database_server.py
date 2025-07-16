#!/usr/bin/env python3
"""
FastMCP Database Server - Data Insights

A simplified MCP database server using FastMCP from the official MCP Python SDK.
Provides PostgreSQL database access through MCP tools with automatic SSE transport handling.

This replaces the complex low-level implementation with FastMCP's high-level API.
"""

import os
import sys
import logging
import asyncio
import asyncpg
from typing import Any, Dict, List, Optional
import click

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', '..'))

from mcp.server.fastmcp import FastMCP
import mcp.types as types

# Configure logging to write to file
log_file = os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', '..', 'logs', 'mcp_server_activity.log')
os.makedirs(os.path.dirname(log_file), exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()  # Also log to console for debugging
    ]
)
logger = logging.getLogger(__name__)

# Log server startup
logger.info("FastMCP Database Server starting up...")
logger.info(f"Logging to: {log_file}")

def get_database_config() -> Dict[str, Any]:
    """Get database configuration from environment variables."""
    try:
        from config import get_db_config
        db_config = get_db_config()
        # Convert PG_ prefixed keys to standard keys
        return {
            "host": db_config["PG_HOST"],
            "port": int(db_config["PG_PORT"]),
            "database": db_config["PG_DBNAME"],
            "user": db_config["PG_USER"],
            "password": db_config["PG_PASSWORD"]
        }
    except ImportError:
        # Fallback to environment variables
        return {
            "host": os.getenv("PG_HOST", "localhost"),
            "port": int(os.getenv("PG_PORT", "5432")),
            "database": os.getenv("PG_DBNAME", "data_insights"),
            "user": os.getenv("PG_USER", "postgres"),
            "password": os.getenv("PG_PASSWORD", "")
        }

# Create FastMCP instance
mcp = FastMCP("Data Insights Database Server")

# Log server creation
logger.info("FastMCP server instance created")

@mcp.tool()
async def query_database(sql_query: str) -> List[Dict[str, Any]]:
    """
    Execute a SQL query on the PostgreSQL database and return results.
    
    Args:
        sql_query: The SQL query to execute
        
    Returns:
        List of dictionaries containing query results
    """
    logger.info(f"Tool called: query_database with query: {sql_query[:100]}...")
    
    try:
        # Get database configuration
        db_config = get_database_config()
        
        # Connect to database
        conn = await asyncpg.connect(**db_config)
        
        try:
            # Execute query
            if sql_query.strip().upper().startswith(('SELECT', 'SHOW', 'DESCRIBE', 'EXPLAIN')):
                # Read-only queries
                rows = await conn.fetch(sql_query)
                results = [dict(row) for row in rows]
                logger.info(f"Query returned {len(results)} rows")
                return results
            else:
                # Write operations
                result = await conn.execute(sql_query)
                logger.info(f"Query executed successfully: {result}")
                return [{"status": "success", "result": result}]
                
        finally:
            await conn.close()
            
    except Exception as e:
        error_msg = f"Database query error: {str(e)}"
        logger.error(error_msg)
        return [{"error": error_msg}]

@mcp.tool()
async def list_tables() -> List[Dict[str, Any]]:
    """
    List all tables in the database with their schemas.
    
    Returns:
        List of dictionaries containing table information
    """
    logger.info("Listing database tables...")
    
    query = """
    SELECT 
        table_schema,
        table_name,
        table_type
    FROM information_schema.tables 
    WHERE table_schema NOT IN ('information_schema', 'pg_catalog')
    ORDER BY table_schema, table_name;
    """
    
    return await query_database(query)

@mcp.tool()
async def describe_table(table_name: str, schema_name: str = "public") -> List[Dict[str, Any]]:
    """
    Describe the structure of a specific table.
    
    Args:
        table_name: Name of the table to describe
        schema_name: Schema name (default: public)
        
    Returns:
        List of dictionaries containing column information
    """
    logger.info(f"Describing table: {schema_name}.{table_name}")
    
    query = """
    SELECT 
        column_name,
        data_type,
        is_nullable,
        column_default,
        character_maximum_length,
        numeric_precision,
        numeric_scale
    FROM information_schema.columns 
    WHERE table_schema = $1 AND table_name = $2
    ORDER BY ordinal_position;
    """
    
    try:
        db_config = get_database_config()
        conn = await asyncpg.connect(**db_config)
        
        try:
            rows = await conn.fetch(query, schema_name, table_name)
            results = [dict(row) for row in rows]
            logger.info(f"Table {schema_name}.{table_name} has {len(results)} columns")
            return results
        finally:
            await conn.close()
            
    except Exception as e:
        error_msg = f"Error describing table {schema_name}.{table_name}: {str(e)}"
        logger.error(error_msg)
        return [{"error": error_msg}]

@mcp.tool()
async def get_table_sample(table_name: str, schema_name: str = "public", limit: int = 10) -> List[Dict[str, Any]]:
    """
    Get a sample of data from a table.
    
    Args:
        table_name: Name of the table
        schema_name: Schema name (default: public)
        limit: Number of rows to return (default: 10)
        
    Returns:
        List of dictionaries containing sample data
    """
    logger.info(f"Getting sample data from: {schema_name}.{table_name} (limit: {limit})")
    
    # Sanitize inputs to prevent SQL injection
    if not table_name.replace('_', '').replace('-', '').isalnum():
        return [{"error": "Invalid table name"}]
    if not schema_name.replace('_', '').replace('-', '').isalnum():
        return [{"error": "Invalid schema name"}]
    
    query = f'SELECT * FROM "{schema_name}"."{table_name}" LIMIT {min(limit, 100)};'
    
    return await query_database(query)

@mcp.tool()
async def get_database_stats() -> List[Dict[str, Any]]:
    """
    Get database statistics and information.
    
    Returns:
        List of dictionaries containing database statistics
    """
    logger.info("Getting database statistics...")
    
    query = """
    SELECT 
        'database_size' as metric,
        pg_size_pretty(pg_database_size(current_database())) as value
    UNION ALL
    SELECT 
        'table_count' as metric,
        COUNT(*)::text as value
    FROM information_schema.tables 
    WHERE table_schema NOT IN ('information_schema', 'pg_catalog')
    UNION ALL
    SELECT 
        'version' as metric,
        version() as value;
    """
    
    return await query_database(query)

@mcp.resource("schema://database_schema")
async def get_database_schema() -> str:
    """
    Get a comprehensive database schema description.
    
    Returns:
        String containing database schema information
    """
    logger.info("Resource called: get_database_schema")
    
    try:
        tables = await list_tables()
        
        schema_info = "Database Schema:\n\n"
        
        current_schema = None
        for table in tables:
            if table.get('table_schema') != current_schema:
                current_schema = table.get('table_schema')
                schema_info += f"\nSchema: {current_schema}\n"
                schema_info += "=" * (len(current_schema) + 8) + "\n"
            
            table_name = table.get('table_name')
            table_type = table.get('table_type', 'TABLE')
            schema_info += f"\n{table_type}: {table_name}\n"
            
            # Get column information
            columns = await describe_table(table_name, current_schema)
            if columns and not columns[0].get('error'):
                for col in columns:
                    col_name = col.get('column_name')
                    data_type = col.get('data_type')
                    is_nullable = col.get('is_nullable', 'YES')
                    nullable_str = "NULL" if is_nullable == "YES" else "NOT NULL"
                    schema_info += f"  - {col_name}: {data_type} {nullable_str}\n"
            
        return schema_info
        
    except Exception as e:
        error_msg = f"Error getting database schema: {str(e)}"
        logger.error(error_msg)
        return error_msg

@click.command()
@click.option('--transport', default='stdio', help='Transport type (stdio or sse)')
@click.option('--port', default=8765, help='Port for SSE transport')
def main(transport: str, port: int):
    """
    Main entry point for the FastMCP Database Server.
    
    Args:
        transport: Transport type (stdio or sse)
        port: Port for SSE transport
    """
    logger.info("=== FastMCP Database Server Starting ===")
    logger.info(f"Transport: {transport}, Port: {port}")
    
    # Test database connection
    try:
        db_config = get_database_config()
        safe_config = db_config.copy()
        safe_config['password'] = '***' if safe_config['password'] else 'EMPTY'
        logger.info(f"Database config: {safe_config}")
        
        # Test connection
        async def test_connection():
            logger.info("Testing database connection...")
            conn = await asyncpg.connect(**db_config)
            await conn.close()
            logger.info("Database connection test successful")
        
        asyncio.run(test_connection())
        
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        sys.exit(1)
    
    # Run the server
    if transport == "sse":
        logger.info("Starting FastMCP server with SSE transport")
        logger.info("Server will accept connections at http://127.0.0.1:8000/sse/")
        logger.info("Note: MCP SDK's FastMCP uses /sse/ endpoint (with trailing slash)")
        try:
            mcp.run(transport="sse")
        except Exception as e:
            logger.error(f"Failed to start FastMCP server with SSE transport: {e}")
            raise
    else:
        logger.info("Starting FastMCP server with stdio transport")
        try:
            mcp.run(transport="stdio")
        except Exception as e:
            logger.error(f"Failed to start FastMCP server with stdio transport: {e}")
            raise

def main_stdio():
    """
    Entry point for stdio mode without Click (used by MCP clients).
    """
    logger.info("Starting FastMCP Database Server in stdio mode...")
    mcp.run(transport="stdio")

if __name__ == "__main__":
    # If no arguments are provided (typically when run by MCP client),
    # use stdio mode without Click
    if len(sys.argv) == 1:
        main_stdio()
    else:
        # Use Click for command-line interface
        main()

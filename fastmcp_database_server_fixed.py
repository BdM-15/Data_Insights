#!/usr/bin/env python3
"""
FastMCP Database Server - Data Insights (Fixed Version)

Based on Oracle's official FastMCP example, ensuring we use only current, non-deprecated features.
"""

import os
import sys
import logging
import asyncio
import asyncpg
from typing import Any, Dict, List
import json

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', '..'))

from mcp.server.fastmcp import FastMCP

# Configure logging
log_file = os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', '..', 'logs', 'mcp_server_activity.log')
os.makedirs(os.path.dirname(log_file), exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def get_database_config() -> Dict[str, Any]:
    """Get database configuration from environment variables."""
    try:
        from config import get_db_config
        db_config = get_db_config()
        return {
            "host": db_config["PG_HOST"],
            "port": int(db_config["PG_PORT"]),
            "database": db_config["PG_DBNAME"],
            "user": db_config["PG_USER"],
            "password": db_config["PG_PASSWORD"]
        }
    except ImportError:
        return {
            "host": os.getenv("PG_HOST", "localhost"),
            "port": int(os.getenv("PG_PORT", "5432")),
            "database": os.getenv("PG_DBNAME", "data_insights"),
            "user": os.getenv("PG_USER", "postgres"),
            "password": os.getenv("PG_PASSWORD", "")
        }

# Create FastMCP instance - following Oracle example exactly
mcp = FastMCP("Data Insights Database Server")

@mcp.tool()
async def query_database(sql_query: str) -> str:
    """Execute a SQL query on the PostgreSQL database and return results as JSON string.
    
    Args:
        sql_query: The SQL query to execute
        
    Returns:
        JSON string containing query results
    """
    logger.info(f"Tool called: query_database with query: {sql_query[:100]}...")
    
    try:
        db_config = get_database_config()
        conn = await asyncpg.connect(**db_config)
        
        try:
            if sql_query.strip().upper().startswith(('SELECT', 'SHOW', 'DESCRIBE', 'EXPLAIN')):
                rows = await conn.fetch(sql_query)
                results = [dict(row) for row in rows]
                logger.info(f"Query returned {len(results)} rows")
                return json.dumps(results, default=str)
            else:
                result = await conn.execute(sql_query)
                logger.info(f"Query executed successfully: {result}")
                return json.dumps({"status": "success", "result": result})
                
        finally:
            await conn.close()
            
    except Exception as e:
        error_msg = f"Database query error: {str(e)}"
        logger.error(error_msg)
        return json.dumps({"error": error_msg})

@mcp.tool()
async def list_tables() -> str:
    """List all tables in the database with their schemas.
    
    Returns:
        JSON string containing table information
    """
    logger.info("Tool called: list_tables")
    
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
async def describe_table(table_name: str) -> str:
    """Describe the structure of a specific table.
    
    Args:
        table_name: Name of the table to describe
        
    Returns:
        JSON string containing column information
    """
    logger.info(f"Tool called: describe_table for table: {table_name}")
    
    query = f"""
    SELECT 
        column_name,
        data_type,
        is_nullable,
        column_default
    FROM information_schema.columns 
    WHERE table_schema = 'public' AND table_name = '{table_name}'
    ORDER BY ordinal_position;
    """
    
    return await query_database(query)

@mcp.tool()
async def get_database_stats() -> str:
    """Get database statistics and information.
    
    Returns:
        JSON string containing database statistics
    """
    logger.info("Tool called: get_database_stats")
    
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

if __name__ == "__main__":
    # Following Oracle example exactly - no statements after mcp.run()
    logger.info("Starting FastMCP Database Server in stdio mode...")
    mcp.run(transport='stdio')

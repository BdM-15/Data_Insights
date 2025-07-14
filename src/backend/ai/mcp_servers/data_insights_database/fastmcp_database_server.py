"""
FastMCP Database Schema Server

This server provides database schema introspection and query execution capabilities
using the FastMCP framework and @mcp.tool() decorator pattern.

Based on best practices from the MCP community and focused on lean, maintainable code.
"""

import asyncio
import logging
import warnings
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field
from fastmcp import FastMCP
import psycopg2
from psycopg2.extras import RealDictCursor
import json
import os
from datetime import datetime
from fastapi import FastAPI

# Suppress known deprecation warnings from uvicorn/websockets compatibility issues
warnings.filterwarnings("ignore", category=DeprecationWarning, module="websockets.legacy")
warnings.filterwarnings("ignore", message="websockets.server.WebSocketServerProtocol is deprecated")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastMCP server
mcp = FastMCP("DatabaseSchemaService")

# Database connection configuration
DB_CONFIG = {
    'host': os.getenv('PG_HOST', 'localhost'),
    'port': int(os.getenv('PG_PORT', '5432')),
    'database': os.getenv('PG_DBNAME', 'capture_insights'),
    'user': os.getenv('PG_USER', 'postgres'),
    'password': os.getenv('PG_PASSWORD', 'postgres')
}

# Pydantic Models for structured inputs/outputs
class DatabaseSchemaResponse(BaseModel):
    """Response model for database schema information."""
    schemas: List[Dict[str, Any]] = Field(description="List of database schemas with their tables and columns")
    total_schemas: int = Field(description="Total number of schemas")
    total_tables: int = Field(description="Total number of tables across all schemas")
    timestamp: str = Field(description="Timestamp when schema was retrieved")

class TableInfo(BaseModel):
    """Response model for specific table information."""
    table_name: str = Field(description="Name of the table")
    schema_name: str = Field(description="Schema containing the table")
    columns: List[Dict[str, Any]] = Field(description="List of columns with their properties")
    row_count: Optional[int] = Field(description="Approximate number of rows in the table", default=None)
    table_size: Optional[str] = Field(description="Size of the table", default=None)

class QueryResult(BaseModel):
    """Response model for query execution results."""
    success: bool = Field(description="Whether the query executed successfully")
    data: Optional[List[Dict[str, Any]]] = Field(description="Query result data", default=None)
    columns: Optional[List[str]] = Field(description="Column names in the result", default=None)
    row_count: Optional[int] = Field(description="Number of rows returned", default=None)
    execution_time: Optional[float] = Field(description="Query execution time in seconds", default=None)
    error_message: Optional[str] = Field(description="Error message if query failed", default=None)

class QueryRequest(BaseModel):
    """Request model for query execution."""
    query: str = Field(description="SQL query to execute")
    limit: Optional[int] = Field(description="Maximum number of rows to return", default=1000)

# Database connection utilities
def get_db_connection():
    """Get a database connection."""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        raise

def execute_query(query: str, fetch_results: bool = True) -> Dict[str, Any]:
    """Execute a SQL query and return results."""
    start_time = datetime.now()
    
    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query)
                
                if fetch_results:
                    results = cur.fetchall()
                    columns = [desc[0] for desc in cur.description] if cur.description else []
                    data = [dict(row) for row in results]
                    row_count = len(results)
                else:
                    data = None
                    columns = []
                    row_count = cur.rowcount
                
                execution_time = (datetime.now() - start_time).total_seconds()
                
                return {
                    "success": True,
                    "data": data,
                    "columns": columns,
                    "row_count": row_count,
                    "execution_time": execution_time
                }
                
    except Exception as e:
        execution_time = (datetime.now() - start_time).total_seconds()
        logger.error(f"Query execution failed: {e}")
        return {
            "success": False,
            "error_message": str(e),
            "execution_time": execution_time
        }

# MCP Tools using @mcp.tool() decorator
@mcp.tool()
async def get_database_schema(schema_filter: Optional[str] = None) -> DatabaseSchemaResponse:
    """
    Get comprehensive database schema information including tables, columns, and metadata.
    
    Args:
        schema_filter: Optional schema name to filter results (e.g., 's3_processed')
    
    Returns:
        DatabaseSchemaResponse with complete schema information
    """
    try:
        # Query to get schema information
        schema_query = """
        SELECT 
            schemaname,
            tablename,
            ARRAY_AGG(
                jsonb_build_object(
                    'column_name', column_name,
                    'data_type', data_type,
                    'is_nullable', is_nullable,
                    'column_default', column_default,
                    'character_maximum_length', character_maximum_length
                ) ORDER BY ordinal_position
            ) as columns
        FROM (
            SELECT 
                t.schemaname,
                t.tablename,
                c.column_name,
                c.data_type,
                c.is_nullable,
                c.column_default,
                c.character_maximum_length,
                c.ordinal_position
            FROM pg_tables t
            JOIN information_schema.columns c ON (
                t.schemaname = c.table_schema 
                AND t.tablename = c.table_name
            )
            WHERE t.schemaname NOT IN ('information_schema', 'pg_catalog')
        ) schema_info
        """
        
        if schema_filter:
            schema_query += f" AND schemaname = '{schema_filter}'"
        
        schema_query += """
        GROUP BY schemaname, tablename
        ORDER BY schemaname, tablename
        """
        
        result = execute_query(schema_query)
        
        if not result["success"]:
            raise Exception(result["error_message"])
        
        # Organize data by schema
        schemas = {}
        total_tables = 0
        
        for row in result["data"]:
            schema_name = row["schemaname"]
            if schema_name not in schemas:
                schemas[schema_name] = {
                    "schema_name": schema_name,
                    "tables": []
                }
            
            schemas[schema_name]["tables"].append({
                "table_name": row["tablename"],
                "columns": row["columns"]
            })
            total_tables += 1
        
        return DatabaseSchemaResponse(
            schemas=list(schemas.values()),
            total_schemas=len(schemas),
            total_tables=total_tables,
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Schema retrieval failed: {e}")
        raise Exception(f"Failed to retrieve database schema: {e}")

@mcp.tool()
async def get_table_info(table_name: str, schema_name: str = "s3_processed") -> TableInfo:
    """
    Get detailed information about a specific table.
    
    Args:
        table_name: Name of the table to inspect
        schema_name: Schema containing the table (default: s3_processed)
    
    Returns:
        TableInfo with detailed table information
    """
    try:
        # Get column information
        columns_query = """
        SELECT 
            column_name,
            data_type,
            is_nullable,
            column_default,
            character_maximum_length,
            ordinal_position
        FROM information_schema.columns 
        WHERE table_schema = %s AND table_name = %s
        ORDER BY ordinal_position
        """
        
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(columns_query, (schema_name, table_name))
                columns = [dict(row) for row in cur.fetchall()]
                
                # Get table statistics
                stats_query = f"""
                SELECT 
                    reltuples::bigint as row_count,
                    pg_size_pretty(pg_total_relation_size('{schema_name}.{table_name}')) as table_size
                FROM pg_class 
                WHERE relname = %s
                """
                cur.execute(stats_query, (table_name,))
                stats = cur.fetchone()
                
                return TableInfo(
                    table_name=table_name,
                    schema_name=schema_name,
                    columns=columns,
                    row_count=int(stats["row_count"]) if stats and stats["row_count"] else None,
                    table_size=stats["table_size"] if stats else None
                )
                
    except Exception as e:
        logger.error(f"Table info retrieval failed: {e}")
        raise Exception(f"Failed to retrieve table info for {schema_name}.{table_name}: {e}")

@mcp.tool()
async def execute_sql_query(query_request: QueryRequest) -> QueryResult:
    """
    Execute a SQL query with safety checks and return results.
    
    Args:
        query_request: QueryRequest containing the SQL query and optional limit
    
    Returns:
        QueryResult with query execution results
    """
    try:
        query = query_request.query.strip()
        limit = query_request.limit or 1000
        
        # Basic safety checks
        if not query.upper().startswith(('SELECT', 'WITH')):
            raise Exception("Only SELECT and WITH queries are allowed")
        
        # Add limit if not present
        if 'LIMIT' not in query.upper():
            query += f" LIMIT {limit}"
        
        result = execute_query(query)
        
        return QueryResult(
            success=result["success"],
            data=result.get("data"),
            columns=result.get("columns"),
            row_count=result.get("row_count"),
            execution_time=result.get("execution_time"),
            error_message=result.get("error_message")
        )
        
    except Exception as e:
        logger.error(f"Query execution failed: {e}")
        return QueryResult(
            success=False,
            error_message=str(e)
        )

@mcp.tool()
async def get_server_status() -> Dict[str, Any]:
    """
    Get database server status and connection information.
    
    Returns:
        Dictionary with server status information
    """
    try:
        status_query = """
        SELECT 
            version() as postgres_version,
            current_database() as current_database,
            current_user as current_user,
            inet_server_addr() as server_address,
            inet_server_port() as server_port,
            pg_postmaster_start_time() as server_start_time,
            pg_database_size(current_database()) as database_size
        """
        
        result = execute_query(status_query)
        
        if result["success"] and result["data"]:
            status_data = result["data"][0]
            status_data["database_size_pretty"] = f"{status_data['database_size'] / (1024**3):.2f} GB"
            status_data["connection_config"] = {
                "host": DB_CONFIG["host"],
                "port": DB_CONFIG["port"],
                "database": DB_CONFIG["database"]
            }
            status_data["timestamp"] = datetime.now().isoformat()
            return status_data
        else:
            raise Exception(result.get("error_message", "Unknown error"))
            
    except Exception as e:
        logger.error(f"Server status check failed: {e}")
        return {
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="FastMCP Database Schema Service")
    parser.add_argument("--connection_type", type=str, default="http", 
                       choices=["http", "stdio"], help="Connection type")
    args = parser.parse_args()
    
    # Comprehensive startup health checks for DATABASE MCP Server
    print(f"\n🔍 Running DATABASE MCP Server startup health checks...")
    print(f"📡 This is the DATABASE MCP Server - one of multiple MCP servers in the Data Insights platform")
    
    # Test database connection
    try:
        test_result = execute_query("SELECT 1 as test")
        if test_result["success"]:
            print(f"✅ PostgreSQL database connection successful")
            logger.info("Database connection successful")
        else:
            print(f"❌ PostgreSQL database connection failed: {test_result['error_message']}")
            logger.error(f"Database connection failed: {test_result['error_message']}")
    except Exception as e:
        print(f"❌ PostgreSQL database connection test failed: {e}")
        logger.error(f"Database connection test failed: {e}")
    
    # Test database content
    try:
        count_result = execute_query("SELECT COUNT(*) as count FROM s3_processed.usaspending_prime_awards LIMIT 1")
        if count_result["success"] and count_result["data"]:
            record_count = count_result["data"][0]["count"]
            print(f"✅ Database content verified: {record_count:,} prime contract records")
        else:
            print(f"⚠️  Could not verify database content")
    except Exception as e:
        print(f"⚠️  Database content check failed: {e}")
    
    # List available MCP tools for THIS server
    print(f"\n🔧 Available DATABASE MCP Tools (this server only):")
    tool_info = [
        ("get_database_schema", "Get comprehensive database schema information"),
        ("get_table_info", "Get detailed information about specific tables"),
        ("execute_sql_query", "Execute SQL queries with safety checks"),
        ("get_server_status", "Get database server status and connection info")
    ]
    
    for tool_name, description in tool_info:
        print(f"  📋 {tool_name}: {description}")
    
    print(f"\n🚀 DATABASE MCP Server Configuration:")
    print(f"  🏷️  Server Name: DatabaseSchemaService")
    print(f"  🏠 Database Host: {DB_CONFIG['host']}:{DB_CONFIG['port']}")
    print(f"  🗄️  Database: {DB_CONFIG['database']}")
    print(f"  👤 User: {DB_CONFIG['user']}")
    print(f"  🔗 Connection Type: {args.connection_type}")
    print(f"  📡 MCP Server URL: http://127.0.0.1:8003/sse/")
    
    print(f"\n📝 Future MCP Servers (planned):")
    print(f"  🌐 Web Intelligence Scraper MCP Server")
    print(f"  📄 Document Creator/Editor MCP Server") 
    print(f"  📊 Visualization Generator MCP Server")
    print(f"  🧠 Strategic Analysis MCP Server")
    
    # Start the server
    server_type = "sse" if args.connection_type == "http" else "stdio"
    print(f"\n🎯 Starting DATABASE MCP Server on port 8003 with {args.connection_type} connection")
    print(f"🔗 LangChain agents will connect to this server via MCP protocol")
    
    mcp.run(server_type, port=8003)

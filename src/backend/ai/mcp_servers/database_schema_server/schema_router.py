"""
API router for database schema and query endpoints.

Endpoints:
- /get_table_names: Returns just the list of table names
- /get_schema: Returns s3_processed schema (tables/columns)
- /run_query: Executes read-only SQL queries against s3_processed
"""

from fastapi import APIRouter, FastAPI, HTTPException
from pydantic import BaseModel
from typing import Any, Dict
import sqlalchemy
from sqlalchemy import create_engine, inspect, text
import config

app = FastAPI(title="Database Schema MCP Server")

@app.get("/health")
async def health_check():
    """Health check endpoint for service discovery."""
    return {
        "name": "database_schema_server",
        "status": "healthy",
        "service_type": "database",
        "version": "1.0.0",
        "description": "Database schema introspection and intelligent query execution"
    }

@app.get("/capabilities")
async def get_capabilities():
    """Return server capabilities for dynamic service discovery."""
    return {
        "capabilities": [
            {
                "name": "schema_introspection",
                "description": "Get comprehensive database schema information for all tables, columns, and relationships",
                "endpoint": "http://localhost:8003/schema/get_schema",
                "method": "GET",
                "parameters": {},
                "examples": [
                    "Show me all available tables",
                    "What columns are in the awards table?",
                    "Get the complete database schema"
                ]
            },
            {
                "name": "data_query",
                "description": "Execute intelligent, LLM-validated SQL queries against the database",
                "endpoint": "http://localhost:8003/schema/run_query",
                "method": "POST",
                "parameters": {
                    "query": "str"
                },
                "examples": [
                    "SELECT * FROM s3_processed.usaspending_prime_awards LIMIT 10",
                    "Show top 10 agencies by total obligations",
                    "Find all contracts expiring in the next 6 months"
                ]
            }
        ]
    }

router = APIRouter()

class QueryRequest(BaseModel):
    query: str

@router.get("/get_schema", response_model=Dict[str, Any])
def get_schema() -> Dict[str, Any]:
    """
    Return the s3_processed schema (tables and columns) from the database.
    """
    try:
        engine = create_engine(config.DATABASE_URL)
        inspector = inspect(engine)
        tables = inspector.get_table_names(schema="s3_processed")
        schema = {}
        for table in tables:
            columns = inspector.get_columns(table, schema="s3_processed")
            schema[table] = [col["name"] for col in columns]
        return schema
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Schema introspection failed: {e}")

@router.post("/run_query")
def run_query(request: QueryRequest) -> Dict[str, Any]:
    """
    Execute a read-only SQL query against s3_processed and return results.
    """
    # Reason: Only allow SELECT queries for safety
    if not request.query.strip().lower().startswith("select"):
        raise HTTPException(status_code=400, detail="Only SELECT queries are allowed.")
    try:
        engine = create_engine(config.DATABASE_URL)
        with engine.connect() as conn:
            result = conn.execute(text(request.query))
            rows = [dict(row) for row in result]
        return {"results": rows}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query execution failed: {e}")

app.include_router(router, prefix="/schema")

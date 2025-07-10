"""
API router for database schema and query endpoints.

Endpoints:
- /get_schema: Returns s3_processed schema (tables/columns)
- /run_query: Executes read-only SQL queries against s3_processed
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Any, Dict
import sqlalchemy
from sqlalchemy import create_engine, inspect, text
import config

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

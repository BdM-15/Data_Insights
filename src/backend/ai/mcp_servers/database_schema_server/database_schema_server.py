"""
Database Schema MCP Server for Capture Insights

Exposes the s3_processed schema and enables read-only query execution for LLM agents.
"""

from fastapi import FastAPI
from .schema_router import router as schema_router

app = FastAPI(title="Database Schema MCP Server", description="Expose s3_processed schema and run read-only queries for LLM access.")

app.include_router(schema_router, prefix="/schema", tags=["schema"])

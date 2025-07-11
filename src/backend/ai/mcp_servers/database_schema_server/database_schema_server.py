"""
Database Schema MCP Server for Capture Insights

Exposes the s3_processed schema and enables read-only query execution for LLM agents.
"""

from fastapi import FastAPI
from .schema_router import router as schema_router, app as schema_app

# Use the app from schema_router which has the health and capabilities endpoints
app = schema_app

app.include_router(schema_router, prefix="/schema", tags=["schema"])

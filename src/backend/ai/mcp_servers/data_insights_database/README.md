# Data Insights Database MCP Server

**FastMCP Implementation** - High-level MCP database server providing comprehensive PostgreSQL integration for the Data Insights platform using FastMCP from the official MCP Python SDK.

## Architecture

- **FastMCP**: Official Model Context Protocol high-level implementation from MCP Python SDK
- **SSE Transport**: Persistent server connections for multi-client access
- **Centralized Config**: Uses `config.py` for database settings
- **Production Ready**: Comprehensive error handling and logging

## Features

- **Database Schema Discovery**: Complete schema introspection with tables, columns, and metadata
- **Table Analysis**: Detailed table information including row counts, sizes, and column definitions
- **Safe Query Execution**: SELECT-only queries with safety checks and result limits
- **Server Status Monitoring**: Database server health and connection information

## Available Tools

### `query_database`

Execute SQL queries on the PostgreSQL database with comprehensive safety checks.

**Parameters:**

- `sql_query` (required): SQL statement to execute

**Returns:**

- Query results as list of dictionaries with execution metadata

### `list_tables`

List all tables in the database with their schemas.

**Returns:**

- List of table information with schema, name, and type

### `describe_table`

Get detailed information about a specific table including structure and statistics.

**Parameters:**

- `table_name` (required): Name of the table to analyze
- `schema_name` (optional): Schema name (default: 'public')

**Returns:**

- Column definitions, data types, constraints, and metadata

### `get_table_sample`

Get a sample of data from a table.

**Parameters:**

- `table_name` (required): Name of the table
- `schema_name` (optional): Schema name (default: 'public')
- `limit` (optional): Number of rows to return (default: 10)

**Returns:**

- Sample data rows as list of dictionaries

### `get_database_stats`

Get database statistics and information.

**Returns:**

- Database size, table count, and version information

## Resources

### `schema://database_schema`

Get comprehensive database schema description.

**Returns:**

- Complete schema information with tables, columns, and organization

## Usage

### Direct Server Execution

```bash
# Start the server (SSE transport, default port 8000)
python fastmcp_database_server.py --transport sse

# Start with stdio transport
python fastmcp_database_server.py --transport stdio

# With command line options
python fastmcp_database_server.py --transport sse
```

### Via MCP Launcher

```bash
# Start all MCP servers with health checks
python mcp_servers_launcher.py

# Health checks only
python mcp_servers_launcher.py --health-check

# Server discovery
python mcp_servers_launcher.py --discover
```

## Configuration

The server uses centralized configuration from `config.py`:

```python
# Database settings automatically loaded from config.py
from config import get_db_config

# Fallback configuration if config.py unavailable:
DATABASE_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "data_insights",
    "user": "postgres",
    "password": ""
}
```

**Environment Variables** (set in `.env`):

- `PG_HOST`: PostgreSQL host
- `PG_PORT`: PostgreSQL port
- `PG_DBNAME`: Database name
- `PG_USER`: Database user
- `PG_PASSWORD`: Database password

## Safety & Security Features

- **Query Restrictions**: Separates read-only and write operations
- **Connection Management**: Proper async connection handling with cleanup
- **Error Handling**: Comprehensive exception handling and logging
- **Input Validation**: Parameter validation and sanitization
- **Rate Limiting**: Built-in protection against excessive queries

## Integration Benefits

- **FastMCP**: High-level, simplified MCP server development
- **SSE Transport**: Persistent server connections for multi-client access
- **Official MCP SDK**: Future-proof and well-documented
- **Centralized Config**: Consistent with platform configuration management
- **Production Ready**: Comprehensive logging, error handling, and monitoring

## Client Connection Examples

The server uses SSE transport by default and can be connected to by any MCP-compatible client:

```bash
# Direct connection via SSE (default port 8000)
python fastmcp_database_server.py --transport sse

# Via launcher (recommended)
python mcp_servers_launcher.py
```

## Logging

Server activity is logged to:

- **Console**: Real-time status and errors
- **File**: `logs/mcp_server_activity.log` for persistent logging

## Migration Notes

This server uses FastMCP from the official MCP Python SDK with:

- ✅ High-level, simplified server development
- ✅ Built-in SSE transport for persistent connections
- ✅ Automatic tool registration and validation
- ✅ Production-ready error handling and logging
- ✅ Centralized configuration management

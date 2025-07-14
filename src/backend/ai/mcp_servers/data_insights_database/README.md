# Data Insights Database MCP Server

**Python MCP SDK Implementation** - Pure Python database server providing comprehensive PostgreSQL integration for the Data Insights platform.

## Architecture

- **Python MCP SDK**: Official Model Context Protocol implementation (pure Python)
- **Stdio Transport**: Reliable process-based client-server communication
- **Centralized Config**: Uses `config.py` for database settings
- **Production Ready**: Comprehensive error handling and logging

## Features

- **Database Schema Discovery**: Complete schema introspection with tables, columns, and metadata
- **Table Analysis**: Detailed table information including row counts, sizes, and column definitions
- **Safe Query Execution**: SELECT-only queries with safety checks and result limits
- **Server Status Monitoring**: Database server health and connection information

## Available Tools

### `get_database_schema`

Get comprehensive database schema information across all schemas.

**Parameters:**

- `schema_name` (optional): Filter by specific schema (e.g., 's3_processed', 's2_interim', 's1_raw')

**Returns:**

- Complete schema information with tables, sizes, and organization

### `get_table_info`

Get detailed information about a specific table including structure and statistics.

**Parameters:**

- `table_name` (required): Name of the table to analyze
- `schema_name` (optional): Schema name (default: 's3_processed')

**Returns:**

- Column definitions, data types, constraints, row count, and table metadata

### `execute_sql_query`

Execute SELECT queries with comprehensive safety checks.

**Parameters:**

- `query` (required): SQL SELECT statement to execute
- `limit` (optional): Maximum rows to return (default: 100, max: 1000)

**Returns:**

- Query results in formatted table with execution metadata

### `get_server_status`

Get database server status and connection information.

**Returns:**

- PostgreSQL version, database size, connection details, and operational status

## Usage

### Direct Server Execution

```bash
# Start the server (stdio transport)
python -m backend.ai.mcp_servers.data_insights_database.python_mcp_database_server

# With command line options
python -m backend.ai.mcp_servers.data_insights_database.python_mcp_database_server --log-level DEBUG
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
    "port": 5433,
    "database": "usaspending",
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

- **Query Restrictions**: Only SELECT queries allowed (no DDL/DML)
- **Keyword Filtering**: Blocks dangerous operations (DELETE, DROP, INSERT, etc.)
- **Automatic Limits**: Adds LIMIT clause if not specified
- **Connection Management**: Proper async connection handling with cleanup
- **Error Handling**: Comprehensive exception handling and logging
- **Input Validation**: Parameter validation and sanitization

## Integration Benefits

- **Pure Python**: No TypeScript hybrid complexity
- **Async/Await Stability**: Resolves "Event loop is closed" errors
- **Official MCP SDK**: Future-proof and well-documented
- **Centralized Config**: Consistent with platform configuration management
- **Production Ready**: Comprehensive logging, error handling, and monitoring

## Client Connection Examples

The server uses stdio transport and can be connected to by any MCP-compatible client:

```bash
# Direct connection
python -m backend.ai.mcp_servers.data_insights_database.python_mcp_database_server

# Via launcher (recommended)
python mcp_servers_launcher.py
```

## Logging

Server activity is logged to:

- **Console**: Real-time status and errors
- **File**: `logs/mcp_server_activity.log` for persistent logging

## Migration Notes

This server replaces the previous FastMCP implementation with:

- ✅ Improved async/await stability
- ✅ Better error handling and recovery
- ✅ Pure Python architecture (no TypeScript dependencies)
- ✅ Official MCP SDK support and documentation
- ✅ Centralized configuration management

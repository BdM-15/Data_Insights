# Data Insights Database MCP Server

This FastMCP server provides database schema introspection and query execution capabilities for the Data Insights platform.

## Features

- **Database Schema Discovery**: Get comprehensive schema information including tables, columns, and metadata
- **Table Information**: Detailed information about specific tables including row counts and sizes
- **Safe Query Execution**: Execute SELECT queries with safety checks and result limits
- **Server Status**: Get database server status and connection information

## Available Tools

### `get_database_schema`

Get comprehensive database schema information including tables, columns, and metadata.

**Parameters:**

- `schema_filter` (optional): Filter results by schema name (e.g., 's3_processed')

**Returns:**

- Complete schema information with tables and columns

### `get_table_info`

Get detailed information about a specific table.

**Parameters:**

- `table_name`: Name of the table to inspect
- `schema_name`: Schema containing the table (default: 's3_processed')

**Returns:**

- Table information including columns, row count, and size

### `execute_sql_query`

Execute a SQL query with safety checks and return results.

**Parameters:**

- `query_request`: QueryRequest containing SQL query and optional limit

**Returns:**

- Query results with execution metadata

### `get_server_status`

Get database server status and connection information.

**Returns:**

- Server status including version, connection info, and database size

## Usage

### Standalone Server

```bash
python fastmcp_database_server.py
```

### HTTP Connection

```bash
python fastmcp_database_server.py --connection_type http
```

### STDIO Connection

```bash
python fastmcp_database_server.py --connection_type stdio
```

## Configuration

The server uses environment variables for database configuration:

- `DB_HOST`: Database host (default: 'localhost')
- `DB_PORT`: Database port (default: 5433)
- `DB_NAME`: Database name (default: 'capture_insights')
- `DB_USER`: Database user (default: 'postgres')
- `DB_PASSWORD`: Database password (default: 'postgres')

## Safety Features

- Only SELECT and WITH queries are allowed
- Automatic LIMIT clause addition if not present
- Connection pooling and error handling
- Comprehensive logging

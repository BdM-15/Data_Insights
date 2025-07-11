# Phase 1: Dynamic Tool Discovery & Self-Awareness

## Overview

This implementation represents the first phase of transforming the Data_Insights MCP server architecture from a rigid, hard-coded system into an intelligent, LLM-first architecture. The system now dynamically discovers available tools and capabilities instead of relying on static tool lists.

## Key Features Implemented

### 1. Dynamic Service Discovery

- **Automatic Server Detection**: Polls known ports to discover active MCP servers
- **Health Monitoring**: Continuous health checks for all discovered servers
- **Capability Introspection**: Automatically discovers what each server can do
- **Real-time Updates**: Refreshes available tools and capabilities dynamically

### 2. Enhanced MCP Server Architecture

- **Health Endpoints**: All servers now expose `/health` endpoints for service discovery
- **Capabilities Endpoints**: All servers expose `/capabilities` endpoints describing their functions
- **Standardized Metadata**: Consistent server identification and capability description

### 3. Flexible Orchestrator Router

- **LLM-Driven Routing**: Uses LLM reasoning to choose appropriate tools
- **Multi-Modal Execution**: Supports conversational, single-tool, multi-step, and workflow approaches
- **Context-Aware Prompts**: Generates dynamic prompts with real-time system state
- **Backward Compatibility**: Maintains legacy routing for existing integrations

### 4. Enhanced Data Models

- **FlexibleIntent**: Advanced intent schema capturing LLM reasoning and confidence
- **ServiceDiscoveryResponse**: Structured response for system status
- **DynamicToolResponse**: Response format for discovered tools

## Architecture Changes

### Before (Hard-coded)

```python
AGENTIC_TOOL_LIST = [
    {"name": "chat", "description": "..."},
    {"name": "data_query", "description": "..."},
    # ... fixed list
]
```

### After (Dynamic)

```python
service_discovery = get_service_discovery()
available_tools = await service_discovery.get_available_tools()
# Tools discovered at runtime from actual running servers
```

## File Structure

```
src/backend/ai/mcp_servers/
├── service_discovery/
│   ├── __init__.py
│   └── service_discovery.py          # Core service discovery logic
├── orchestrator/
│   ├── orchestrator_server.py        # Enhanced with health/capabilities
│   ├── flexible_orchestrator_router.py # New flexible routing
│   └── orchestrator_router.py        # Legacy routing (maintained)
├── chat/
│   └── chat_server.py                # Enhanced with health/capabilities
└── database_schema_server/
    ├── database_schema_server.py     # Enhanced with health/capabilities
    └── schema_router.py              # Enhanced with health/capabilities
```

## Testing

### 1. Start MCP Servers

```bash
python mcp_servers_quickstart.py
```

### 2. Test Health Endpoints

```bash
python test_health_endpoints.py
```

### 3. Test Service Discovery

```bash
python test_service_discovery.py
```

## API Endpoints

### Orchestrator (Port 8001)

- `GET /health` - Health check
- `GET /capabilities` - Available capabilities
- `POST /orchestrator/flexible_route` - New flexible routing
- `POST /orchestrator/discover_tools` - Discover available tools
- `GET /orchestrator/system_status` - System status
- `POST /legacy/route` - Legacy routing (backward compatibility)

### Chat Server (Port 8002)

- `GET /health` - Health check
- `GET /capabilities` - Available capabilities
- `POST /chat/route` - Chat functionality
- `POST /visualization/route` - Visualization functionality

### Database Schema Server (Port 8003)

- `GET /health` - Health check
- `GET /capabilities` - Available capabilities
- `GET /schema/get_schema` - Database schema
- `POST /schema/run_query` - Execute queries

## Key Benefits

1. **Scalability**: Adding new MCP servers automatically extends capabilities
2. **Resilience**: System adapts to server failures and recoveries
3. **Intelligence**: LLM makes informed decisions about tool usage
4. **Flexibility**: Supports complex multi-step workflows
5. **Self-Awareness**: System knows its own capabilities and limitations

## LLM Integration

The system now uses dynamic prompts that include:

- Real-time system status
- Available tools and capabilities
- Server health information
- Contextual examples
- Adaptive instruction based on system state

### Example Dynamic Prompt

```
You are an advanced AI orchestrator...

**SYSTEM STATUS**
- Total Servers: 3
- Healthy Servers: 3
- Total Capabilities: 7
- Last Discovery: 2025-07-10T14:30:00

**AVAILABLE TOOLS & CAPABILITIES**
- chat: General Q&A and conversational responses
- data_query: Execute intelligent SQL queries
- schema_introspection: Get database schema information
- ...

**INSTRUCTIONS**
[Context-aware instructions based on available tools]
```

## Next Steps (Phase 2)

1. **Enhanced SQL Validation**: Replace string matching with LLM-based query validation
2. **Multi-Server Query Coordination**: Enable queries across multiple data sources
3. **Workflow Orchestration**: Implement complex multi-step workflows
4. **Learning and Adaptation**: Add feedback loops for continuous improvement
5. **External Integration**: Connect to SAM.gov, SBA SubNet, and other external APIs

## Monitoring and Logging

All service discovery activities are logged to:

- `logs/service_discovery.log`
- `logs/flexible_orchestrator.log`

## Configuration

The system automatically discovers servers on ports 8001-8010. To add new servers:

1. Start them on an available port in this range
2. Implement `/health` and `/capabilities` endpoints
3. The system will automatically discover them

## Backward Compatibility

The legacy routing system remains available at `/legacy/route` to ensure existing integrations continue to work while the system transitions to the new flexible architecture.

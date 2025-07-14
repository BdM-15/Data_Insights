# Python MCP SDK Migration Plan

## Executive Summary

Based on the "Event loop is closed" error and complexity issues with the FastMCP (Python/TypeScript hybrid) implementation, we are migrating to the official Python MCP SDK (https://github.com/modelcontextprotocol/python-sdk) for a more robust, maintainable, and Python-native MCP integration.

## Background: Current State vs Target State

### Current Architecture (FastMCP - Hybrid Stack)

- **Server**: FastMCP Database Server (Python/TypeScript hybrid)
- **Transport**: SSE (Server-Sent Events) on port 8003
- **Client**: MultiServerMCPClient with SSE transport
- **Issue**: "Event loop is closed" errors on complex/second queries
- **Complexity**: Hybrid Python/TypeScript stack increases maintenance burden

### Target Architecture (Python MCP SDK - Pure Python)

- **Server**: Pure Python MCP Server using official SDK
- **Transport**: stdio or SSE using official transport implementations
- **Client**: Official Python MCP Client with LangGraph integration
- **Benefits**: Simplified stack, better async handling, official support

## Migration Strategy

### Phase 1: Server Migration (Priority 1)

#### 1.1 Update Requirements

**Current**: Added Python MCP SDK dependencies to existing `requirements.txt` with clear comments

- ✅ `mcp>=1.0.0` - Official Python MCP SDK
- ✅ `asyncpg>=0.29.0` - Database connectivity for MCP tools
- ✅ Marked FastMCP and LlamaIndex dependencies for removal

#### 1.2 Create New Python MCP Database Server

**Target**: Replace FastMCP Database Server with official Python MCP SDK
**File**: `src/backend/ai/mcp_servers/python_mcp_database_server.py` ✅ (Created)

#### 1.3 Update Existing Launcher

**Target**: Modify `fastmcp_servers_launcher.py` to support both FastMCP and Python MCP during transition
**Later**: Remove FastMCP support and rename to `mcp_servers_launcher.py`

### Phase 2: Client Migration (Priority 2)

#### 2.1 Update CaptureIntelligenceAgent

**Current**: `src/frontend/ai/capture_intelligence_agent.py`
**Target**: Replace MultiServerMCPClient with official Python MCP Client

#### 2.2 Test Integration

**Target**: Update existing integration tests instead of creating new ones
**File**: Modify existing test files in place

### Phase 3: Integration & Testing (Priority 3)

#### 3.1 End-to-End Testing

**Target**: Test Streamlit AI Chat interface with new MCP stack
**Approach**: Use existing test framework, not create new test files

### Phase 4: Cleanup & Documentation (Priority 4)

#### 4.1 Remove Legacy Code & Files

**Files to Remove After Migration**:

- `fastmcp_servers_launcher.py` (replace with renamed `mcp_servers_launcher.py`)
- `test_python_mcp_migration.py` (temporary test file)
- `python_mcp_servers_launcher.py` (consolidate into main launcher)
- FastMCP dependencies from `requirements.txt`
- Legacy LlamaIndex dependencies from `requirements.txt`

#### 4.2 Update Documentation

**Files to Update**:

- `TASKS.md` - Remove migration task, update architecture
- `FRESH_CONVERSATION_CONTEXT.md` - Update current state
- `README.md` - Update setup instructions
- Remove `PYTHON_MCP_SDK_MIGRATION_PLAN.md` (this file) after completion

#### 4.3 Final File Structure

**Goal**: Clean, minimal structure with no redundant files

## Implementation Timeline

### Week 1: Server Migration

- [ ] Implement Python MCP Database Server using official SDK
- [ ] Test server functionality with official MCP clients
- [ ] Create launcher script for new server

### Week 2: Client Migration

- [ ] Integrate official Python MCP Client with LangGraph
- [ ] Update CaptureIntelligenceAgent for new client
- [ ] Test basic tool execution and async handling

### Week 3: Integration & Testing

- [ ] Update Streamlit AI Chat interface
- [ ] Run comprehensive integration tests
- [ ] Validate "Event loop is closed" issue resolution

### Week 4: Polish & Documentation

- [ ] Update all documentation
- [ ] Remove legacy FastMCP code
- [ ] Performance optimization and final testing

## Risk Mitigation

### Technical Risks

- **Async Event Loop Issues**: Official SDK should handle this better
- **Transport Compatibility**: Start with stdio, migrate to SSE if needed
- **Performance Changes**: Monitor and optimize as needed

### Migration Risks

- **Breaking Changes**: Maintain parallel development branches
- **Integration Complexity**: Incremental migration approach
- **Testing Coverage**: Comprehensive test suite before cutover

## Expected Benefits

### Technical Benefits

- **Simplified Architecture**: Pure Python stack, easier maintenance
- **Better Async Handling**: Official SDK should resolve event loop issues
- **Official Support**: Backed by ModelContextProtocol organization
- **Future Compatibility**: Aligned with MCP standard evolution

### Development Benefits

- **Reduced Complexity**: No more Python/TypeScript hybrid stack
- **Better Documentation**: Official examples and patterns
- **Community Support**: Access to official MCP community
- **Easier Debugging**: Standard Python debugging tools

## Success Criteria

### Technical Success

- [ ] "Event loop is closed" error eliminated
- [ ] All 4 database tools functional with new architecture
- [ ] Streamlit AI Chat interface working seamlessly
- [ ] Performance equal to or better than FastMCP implementation

### Functional Success

- [ ] All integration tests passing
- [ ] Complex multi-step queries working
- [ ] Domain expertise scenarios functioning
- [ ] Roberto's expert persona maintained

### Code Quality Success

- [ ] Clean, maintainable Python codebase
- [ ] Comprehensive test coverage
- [ ] Updated documentation
- [ ] Simplified deployment process

## Next Actions

1. **Immediate**: Begin implementing Python MCP Database Server using official SDK
2. **Week 1**: Complete server migration and basic testing
3. **Week 2**: Integrate official client with existing LangGraph architecture
4. **Week 3**: End-to-end testing and validation
5. **Week 4**: Documentation updates and legacy code cleanup

This migration will establish a robust, maintainable foundation for the Data Insights AI Agent while resolving current technical issues and positioning the project for future enhancements.

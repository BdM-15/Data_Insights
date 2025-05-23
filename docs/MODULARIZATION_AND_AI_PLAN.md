# Data Insights Project: Modularization and AI Integration Roadmap

## Modularization & AI Integration Status Table

| Task/Phase                                       | Status      |
| ------------------------------------------------ | ----------- |
| 1. Centralize Theme Configuration                | Complete    |
| 2. Extract Database and Data Processing Logic    | Complete    |
| 3. Create Reusable Visualization Components      | Complete    |
| 4. Implement Tabbed Interface Components         | Complete    |
| 5. Create a Layout Component Library             | Complete    |
| 6. Integrate with Streamlit's Config System      | Complete    |
| 7. Pydantic Model Integration (Backend/Frontend) | Complete    |
| 8. Specialized MCP/AI Agent Integration          | In Progress |
| 9. AI-Assisted Capture Profile Generator         | Not Started |
| 10. External Data Connectors & Market Intel      | Not Started |

---

## MCP Server Capabilities Table (Prioritized Implementation Order, May 2025)

| #   | Functionality                   | Open Source | Local | Free | Recommended Server(s)                                                                     |
| --- | ------------------------------- | ----------- | ----- | ---- | ----------------------------------------------------------------------------------------- |
| 1   | Observability/Tracing           | Yes         | Yes   | Yes  | langfuse, pydanticai (Completed)                                                          |
| 2   | LLM/Chat                        | Yes         | Yes   | Yes  | ollama-mcp-server, pydanticai-mcp-server (In Progress)                                    |
| 3   | Agent Orchestration             | Yes         | Yes   | Yes  | python-sdk-mcp, pydanticai-mcp-server (Not Started)                                       |
| 4   | GitHub Automation               | Yes         | Yes   | Yes  | github-mcp-server (Not Started)                                                           |
| 5   | Web Search                      | Yes         | Yes   | Yes  | Brave Search MCP (Not Started)                                                            |
| 6   | Web Scraping                    | Yes         | Yes   | Yes  | Firecrawl MCP, Crawl4AI MCP (Not Started)                                                 |
| 7   | Database (Postgres)             | Yes         | Yes   | Yes  | postgres-mcp-server (Not Started)                                                         |
| 8   | Visualization                   | Yes         | Yes   | Yes  | vega-lite-mcp-server (Not Started)                                                        |
| 9   | Document Generation             | Yes         | Yes   | Yes  | python-sdk-mcp + python-docx (Not Started)                                                |
| 10  | Reasoning/Analysis              | Yes         | Yes   | Yes  | Sequential Thinking MCP (Not Started)                                                     |
| 11  | SAM.gov Solicitation Enrichment | Yes         | Yes   | Yes  | See `/src/backend/data_acquisition/sam_gov_enrichment_example.py` and `/docs/PLANNING.md` |

---

## Updated MCP/AI Agent Integration Roadmap (May 2025)

### May 2025 Progress Update

#### ETL/Analytics Pipeline Refactor (May 2025)

- The ETL/data pipeline is modular, schema-aware, and fully automated using a three-stage schema (`s1_raw`, `s2_interim`, `s3_processed`).
- Deduplication is robust for both prime awards and subawards, and all index creation and precomputed tables (filter values, dependencies, quarterly_data, etc.) are handled in the transformation stage and created only in `s3_processed`.
- The transformation script creates all recommended indexes and precomputes filter/aggregation tables for analytics and AI, using only `s3_processed.usaspending_prime_awards` and `s3_processed.usaspending_subawards` as sources.
- No analytics or reporting is performed on `s1_raw` or `s2_interim` tables.
- The pipeline is idempotent, future-proofed for AI/LLM/RAG, and ready for downstream agent and RAG integration.

---

---

## AI Chat Integration & Agentic Sidebar Plan (May 2025)

### Overview

We are beginning the integration of AI/LLM capabilities into the Data Insights platform, focusing on a modular, agentic, and context-aware chat experience. The following plan outlines the incremental steps for integrating a sidebar AI chat agent that is:

- **UI-agnostic** (works across all pages)
- **Context-aware** (knows what the user is viewing)
- **Agentic** (can adjust filters, suggest actions, and orchestrate MCP tools)
- **Efficient** (does not trigger full Streamlit reruns on every chat interaction)
- **Observable** (all LLM/MCP/agent actions traced via Langfuse)

### Stepwise Integration Plan

#### Step 1: Sidebar AI Chat UI & FastAPI Integration

- Build an "AI Tools" page in Streamlit.
- Move navigation to the top of the main page (horizontal menu/tabs).
- Sidebar is reserved for the AI chat/agent panel.
- Integrate the sidebar chat UI with the FastAPI chat endpoint (UI-agnostic, no page rerun on chat).
- Display prompt examples and allow user input.

#### Step 2: Contextual Awareness

- Pass current page/tab and filter state to the chat endpoint with each message.
- Backend uses this context for more relevant responses.

#### Step 3: Agentic Actions (Filter Adjustment)

- Extend chat backend to return both a text response and an optional "action" payload (e.g., {"set_filter": {"agency": "Army", "date_range": "2023"}}).
- Streamlit checks for action payloads and updates session state accordingly.
- **No full rerun:** Use Streamlit's session state and component callbacks to update only affected UI parts.

#### Step 4: Database Querying via LLM/MCP

- Integrate a PostgreSQL MCP server or direct LLM-to-SQL translation for contract data queries.
- Allow the agent to answer questions using live data, not just static context.

#### Step 5: Web Intelligence Tools

- Integrate Brave Search, Crawl4AI, and Firecrawl MCPs for web search and scraping.
- Expose these as agent tools, so the prime agent can choose the right tool for the user’s query.

#### Step 6: Enhanced Agentic Capabilities

- Allow the agent to suggest filters, visualizations, or even switch pages based on user intent.
- Add brainstorming and intent clarification features.

---

### Prime Agent Structure (Planning)

- **Prime Agent**: Orchestrates all tool calls (LLM, database, web search, document generation, etc.)
- **Tool Plugins**: Each MCP server/tool is a plugin (Postgres, Brave, Crawl4AI, etc.)
- **Context Manager**: Tracks current page, filters, and user history
- **Action Dispatcher**: Returns both text and UI actions (filter changes, navigation, etc.)
- **Observability**: All actions and tool calls are traced via Langfuse

---

### AI Tools for Capture Managers (Feature Ideas)

- Natural language contract data queries ("Show top 5 expiring contracts in Q4")
- Market research via web scraping (SAM.gov, competitor sites)
- Similar NAICS/PSC code discovery
- Opportunity qualification checklists
- Win theme and discriminator brainstorming
- Competitive landscape summaries
- Document/proposal outline generation
- Price-to-win and risk analysis (future phase)

---

### Navigation Refactor

- Move page navigation to the top of the main page (horizontal menu or tabs)
- Sidebar is reserved for the AI chat/agent panel

---

### Summary Table

| Step | Feature/Action                          | Outcome                        |
| ---- | --------------------------------------- | ------------------------------ |
| 1    | Sidebar AI chat UI, FastAPI integration | Chatbot available on all pages |
| 2    | Pass page/filter context to chat        | Context-aware responses        |
| 3    | Agentic filter adjustment               | AI can set filters for user    |
| 4    | LLM/MCP database queries                | Data-driven insights           |
| 5    | Web intelligence tools                  | Market research via AI         |
| 6    | Prime agent orchestration               | Flexible, multi-tool agent     |

---

### Notes

- **No Streamlit rerun on chat:** The chat component will use Streamlit's session state and component callbacks to update only the chat UI, not the whole page, for a smooth user experience.
- **Incremental approach:** Each step is modular and can be validated independently.
- **All LLM/MCP/agent actions are observable via Langfuse.**

---

- **WSL2 Ubuntu 22.04 LTS with NVIDIA Container Toolkit**: Complete. Confirmed GPU access in Docker containers for RTX 4060.
- **Ollama and FastAPI Chat API Docker Compose Integration**: Complete. Both services run as containers, with Ollama using GPU.
- **Langfuse and Pydantic AI Tracing**: Complete. Centralized tracing module implemented, all config in `.env`/`.env.example`.
- **Prompt Template System**: Complete. Markdown-based prompt templates in place, loaded by chat API.
- **Configuration Refactor**: Complete. All config now accessed via function-based accessors in `config.py`.
- **Documentation and Planning**: In Progress. Modularization and AI integration plans updated, but ongoing as features are added.
- **AI Chat Endpoint**: In Progress. FastAPI endpoint scaffolded, ready for further development in a new branch.

### Next Steps

1. **Observability Foundation**

   - **Langfuse integration is complete.**
   - All LLM, MCP, and agent interactions will be traced using Langfuse and Pydantic AI.
   - All chatbots, agents, and MCP tool calls are now observable from the start.

2. **AI Chat Agent Integration**

   - Deploy ollama-mcp-server as the first general-purpose LLM/chat MCP tool (local, GPU-accelerated).
   - Expose chat and completion endpoints for Streamlit and agent workflows.
   - Document configuration and usage in README and planning docs.

3. **Prime Agent & Structured Orchestration**

   - Integrate pydanticai-mcp-server for type-safe, orchestrated agent workflows.
   - Develop a prime agent to coordinate all MCP tools, LLMs, and specialized agents.
   - Ensure all agent interactions are observable via Langfuse/Logfire.

4. **Incremental Tool Expansion**
   - Add web intelligence (crawl4ai-mcp-server), document creation, and vector search tools as needed.
   - Maintain modular, observable architecture for all new tools.

### AI Agent Architecture Note

- All agent and LLM interactions (including chatbots) will be traced and evaluated using Langfuse and Logfire.
- The prime agent will coordinate tool selection, prompt routing, and result aggregation, with full observability.

> **Legend:** Complete | In Progress | Not Started

---

## Overview

This document outlines a comprehensive plan for:

1. **Code Modularization** - Restructuring the codebase for better maintainability and scalability
2. **AI Integration** - Incrementally adding AI capabilities including Model Context Protocol (MCP), chatbot functionality, and LLM integration

---

## MCP/AI Agent Integration Roadmap (Updated May 2025)

### Phase 1: MCP Server Setup

- [x] Dockerize and configure the GitHub MCP server for local agent workflows
- [x] Add VS Code MCP tool configuration for secure, local launch
- [x] Validate local-only processing and privacy compliance

### Phase 2: Tool Integration

- [x] Integrate first MCP tool (GitHub MCP server) into the Data_Insights project
- [x] Document configuration and usage in README and planning docs
- [x] Test agent workflow end-to-end with local LLM inference

### Phase 3: Expand Agent Suite

- [ ] Add additional MCP tools (web intelligence, document creation, visualization, analysis)
- [ ] Modularize agent orchestration and workflow management
- [ ] Document best practices for agent integration

_Last updated: May 8, 2025_

## Code Modularization Plan

**Performance Principle:**

- Each modularization step will be validated for performance to ensure no degradation in speed or responsiveness. Optimization for efficient data access, caching, and minimal overhead is a priority throughout the process.

The current codebase has grown significantly, with large files handling multiple responsibilities. This plan outlines how to restructure the code to improve maintainability, reusability, and testing.

### 1. Centralize Theme Configuration

**Status:** Complete (May 15, 2025)

- Theme colors and chart settings are now defined in `src/frontend/styles/theme.py`.
- Reusable CSS generation is in `src/frontend/styles/custom_css.py`.
- The dashboard imports and injects theme/CSS from these modules, with all logic and visuals unchanged.
- The dashboard was tested after this step and confirmed to work with no visual or functional changes.
- **Performance was validated and no slowdown was observed.**

**Rationale:**

- This approach ensures a single source of truth for all theme-related values, making future updates and maintenance easier.
- By using a function to generate CSS, we avoid code duplication and make it easier to apply consistent styles across all pages.
- Modularizing theme and CSS logic is a low-risk, high-impact first step that does not affect business logic or data processing, so it is ideal for validating the modularization process incrementally.
- Performance is monitored after each step to ensure the user experience remains optimal.

```
src/
└── frontend/
    └── styles/
        ├── theme.py          # Theme configuration (colors, styling)
        └── custom_css.py     # Reusable custom CSS functions
```

**Implementation Steps:**

1. Extract theme colors and constants from the dashboard file
2. Create theme.py with color definitions and style constants
3. Create custom_css.py with functions that generate appropriate CSS
4. Update .streamlit/config.toml with base theme settings
5. Replace hardcoded styles with imports from theme module

**Benefits:**

- Consistent theme across all pages
- Easier theme updates and customization
- Reduced code duplication

### 2. Extract Database and Data Processing Logic

**Goal:** Create dedicated modules for database operations and data processing.

```
src/
└── backend/
    ├── core/
    │   ├── database.py       # Already exists, expand functionality
    │   └── queries.py        # SQL queries and database functions
    └── data/
        ├── processors/
        │   ├── awards.py     # Award data processing functions
        │   ├── agencies.py   # Agency data processing functions
        │   └── competition.py # Competition analysis functions
        └── models/
            └── data_models.py # Pydantic models for data validation
```

**Implementation Steps:**

1. Identify database operations in dashboard files
2. Move SQL queries to queries.py, organized by domain
3. Create processor modules for different data types
4. Define data models with Pydantic for validation
5. Update dashboard to use these modules

**Benefits:**

- Separation of database logic from UI code
- Reusable data transformations across different pages
- Better testability of data processing logic
- Clearer code organization by domain

### 3. Create Reusable Visualization Components

**Goal:** Extract visualization code into modular, reusable components.

```
src/
└── frontend/
    └── visualizations/
        ├── charts/
        │   ├── trend_charts.py    # Time-series visualizations
        │   ├── comparison_charts.py # Comparison visualizations
        │   ├── distribution_charts.py # Distribution visualizations
        │   └── geo_charts.py      # Geographic visualizations
        ├── components/
        │   ├── metric_cards.py    # KPI metric display utilities
        │   └── tooltips.py        # Custom tooltip components
        └── utils/
            └── plotly_helpers.py  # Common Plotly configuration
```

**Implementation Steps:**

1. Identify common visualization patterns
2. Extract each chart type to its own function
3. Standardize function signatures (data, config, theme)
4. Add caching decorators to visualization functions
5. Replace inline chart code with component calls

**Benefits:**

- Standardized visualization components
- Easier maintenance when updating chart styles
- Component-level caching for performance
- Reusable visualizations across multiple pages

### 4. Implement Tabbed Interface Components as Modules

**Goal:** Break down tabs into their own modules.

```
src/
└── frontend/
    └── pages/
        ├── strategic_dashboard.py  # Main page with tabs
        └── tabs/
            ├── market_overview.py  # Tab 1 content
            ├── future_opportunities.py # Tab 2 content
            ├── agency_intelligence.py # Tab 3 content
            └── competitive_analysis.py # Tab 4 content
```

**Implementation Steps:**

1. Create a module for each tab
2. Extract tab-specific functionality to these modules
3. Create standardized function signatures for tab rendering
4. Update main dashboard to import and display tab content
5. Implement state management between tabs

**Benefits:**

- Reduced file size of main dashboard
- Independent development of different tabs
- Better code organization and maintainability
- Simplified testing of tab components

### 5. Create a Layout Component Library

**Goal:** Standardize common UI patterns.

```
src/
└── frontend/
    └── components/
        ├── layouts/
        │   ├── grid.py        # Standardized grid layouts
        │   └── containers.py  # Custom container components
        ├── filters/
        │   ├── filter_bar.py  # Common filter components
        │   └── date_range.py  # Date range selector
        └── navigation/
            └── sidebar.py     # Sidebar navigation component
```

**Implementation Steps:**

1. Identify repeating layout patterns
2. Create standardized functions for common layouts
3. Extract filter components to reusable modules
4. Create a standardized sidebar navigation component
5. Update pages to use these components

**Benefits:**

- Consistent UI patterns across the application
- Reduced code duplication
- Easier maintenance when updating UI components
- Faster development of new pages

### 6. Integrate with Streamlit's Config System

**Goal:** Leverage Streamlit's built-in configuration system.

**Implementation Steps:**

1. Update .streamlit/config.toml:
   ```toml
   [theme]
   base = "dark"
   primaryColor = "#00C3FF"
   backgroundColor = "#051B30"
   secondaryBackgroundColor = "#203040"
   textColor = "#FFFFFF"
   font = "sans-serif"
   ```
2. Modify CSS to use theme variables
3. Create a config loader utility to merge custom and Streamlit config

**Benefits:**

- Better integration with Streamlit's theming
- More consistent UI appearance
- Simplified CSS management

## Recent Progress: Dashboard Modularization & AI Integration

- **Theme modularization is complete:** All theme colors and CSS are now centralized in `src/frontend/styles/theme.py` and `custom_css.py`. The dashboard imports these modules for consistent styling.
- **Backend data processing is fully modularized:** All data processing and database logic have been moved out of the Streamlit frontend and into backend modules (`src/backend/data/processors/awards.py`, `agencies.py`, `competition.py`).
- **Frontend is UI-only:** The Streamlit dashboard now only handles UI and calls backend functions for all data and processing. No business/data logic remains in the frontend.
- **Sidebar diagnostics restored and improved:** Diagnostics for DB connection, table existence, and row count for `usaprime_cleaned` are now robust and match the original backup dashboard style.
- **File-based logging implemented:** All major operations and errors are logged to `logs/dashboard.log` for traceability and debugging.
- **Tested and validated:** The dashboard runs successfully, diagnostics and logging work, and all data is sourced exclusively from `usaprime_cleaned`.
- **Database connection logic is backend-only:** All database connection and diagnostics logic is now in `src/backend/core/database.py` (see `get_db_connection_with_status`). The frontend only handles UI feedback.
- **Tab logic is fully modularized:** All tab content and logic are in `src/frontend/pages/tabs/`, with each tab importing backend processors as needed.
- **Pydantic model integration is complete:** All backend processor functions now return lists of Pydantic models for major data flows (awards, agencies, competition, etc.), and the frontend/tab code has been refactored to consume these models. Type safety and validation are enforced throughout the data pipeline. All metric cards and KPI visualizations now use a unified MetricCard Pydantic model for type safety and maintainability across the frontend.
- **Frontend and backend are fully type-safe:** All major data flows between backend and frontend are validated and documented using Pydantic models. All visualizations and metrics are now based on validated, structured data. The MetricCard Pydantic model is now used for all KPI/metric cards in the dashboard, ensuring a single, consistent approach for UI metrics.
- **Visualization components are fully modularized:** All chart and metric logic has been moved into reusable, well-documented components under `src/frontend/visualizations/charts/` and `components/`. All visuals match the original dashboard’s style, and all original dashboard features are preserved.
- **All original dashboard functionality is preserved:** No charts or features were removed during modularization or refactor. All original analytics, including custom DataFrame-based visualizations, remain intact and tested.
- **Layout component library created and in use:** Standardized grid, card, and sidebar layouts are now implemented in `src/frontend/components/layouts/grid.py` and used throughout the dashboard for consistent UI structure.
- **Centralized filter logic:** All filter UI and logic are now in `src/frontend/components/filters.py`, supporting robust filter state management and a reliable Clear Filters button.
- **Theme and formatting persistence:** Theme CSS and formatting utilities are injected on every rerun, ensuring consistent appearance and accessibility.
- **Chart/visualization improvements:** All charts use THEME colors, improved axis label readability, and correct contract type/legend labeling. Heatmap rendering is now consistent and human-readable.
- **Planned features and code scaffolding:** Scaffolding for MCP/AI agent integration, capture profile generation, and external data connectors is in place, with modular code structure ready for incremental feature addition.

## Roadmap: Next Steps

- **Add Pydantic models for any new or advanced analytics:** As new backend features or analytics are added, define and use Pydantic models for any reusable or API-exposed data structures.
- **Develop and integrate specialized MCP agents** for web intelligence, document creation, visualization, and advanced analytics.
- **Implement the AI-assisted capture profile generator,** leveraging local LLMs for narrative and strategic analysis.
- **Continue to modularize and document new features** as they are added, ensuring maintainability and scalability.
- **Begin MCP/AI agent integration:** Start with local LLM (Ollama) and MCP server setup, then incrementally add AI-driven features as outlined in the AI Integration Roadmap.
- **Expand test coverage:** Add/expand Pytest unit tests for new backend processors, visualization components, and filter logic.
- **Document new layout and filter components:** Supplement documentation in `PLANNING.md` and `strategic_dashboard_implementation.md` to reflect new UI scaffolding and filter management patterns.

## Market Overview Tab: Planned Advanced Features

- **Projected Awards and Suitability Overlay Chart**: Implement a projection chart that takes all active contracts and projects their next award date and obligations. Overlay a second line based on the suitability of our company, showing both total projected spending and the potential amount our company could win.

  - _Reason/Benefit_: Enables users to visually compare the overall market opportunity with the realistic, suitability-filtered opportunity for their company, supporting strategic targeting and resource allocation.

- **Similar NAICS Table via LLM Semantic Search**: Add a table that identifies NAICS codes similar to the one being filtered, using LLM-based semantic search on NAICS codes and descriptions. This will help users discover adjacent or unexplored market areas.

  - _Reason/Benefit_: By surfacing related NAICS codes, users can expand their market research, identify diversification opportunities, and avoid missing relevant opportunities due to narrow filtering.

- **Interactive Sankey Diagram (Agency → Office → Contract)**: Add an interactive Sankey diagram as the last visual, tracing the flow from parent agency to office level and further into contract levels.
  - _Reason/Benefit_: Provides a clear, intuitive visualization of how obligations and actions flow through the federal hierarchy, helping users identify bottlenecks, key offices, and contract concentrations for more effective targeting.

---

## AI Integration Roadmap

This section outlines a step-by-step approach to integrating AI capabilities into the application, following an incremental implementation strategy.

### Phase 1: Local LLM Setup (Weeks 1-2)

**Goal:** Establish the foundation for AI capabilities with local LLM integration.

**Implementation Steps:**

1. **Set up Ollama for local LLM inference**

   - Install Ollama server locally
   - Configure for optimized performance on NVIDIA GTX 4060
   - Add langchain/llama-index integration utilities

2. **Create base LLM interaction module**

   ```
   src/
   └── backend/
       └── ai/
           ├── llm_config.py       # LLM configuration management
           ├── ollama_client.py    # Ollama API wrapper
           └── prompt_templates.py # Base prompt templates
   ```

3. **Implement basic context management**

   - Create utilities for handling context windows
   - Add memory management for conversation history
   - Implement simple prompt template system

4. **Add observability with Langfuse**
   - Set up Langfuse locally for LLM monitoring
   - Create instrumentation wrappers
   - Implement basic logging of LLM interactions

### Phase 2: PydanticAI Integration (Weeks 3-4)

**Goal:** Add structured data extraction from text using PydanticAI.

**Implementation Steps:**

1. **Create structured data models**

   ```
   src/
   └── backend/
       └── ai/
           └── models/
               ├── contract_models.py      # Contract data structures
               ├── opportunity_models.py   # Opportunity extraction models
               └── competitor_models.py    # Competitor analysis models
   ```

2. **Implement extraction patterns**

   - Create parsers for contract descriptions
   - Add extractors for competitive intelligence
   - Implement validators for extracted data

3. **Connect to existing data pipeline**

   - Create transformation utilities between Pydantic and Pandas
   - Add data enrichment functions with AI-extracted fields
   - Implement cache management for LLM extraction results

4. **Add basic analytics dashboard**
   - Create diagnostics view for extraction quality
   - Add confidence scoring for extracted fields
   - Implement manual correction mechanisms

### Phase 3: Basic Chatbot Integration (Weeks 5-6)

**Goal:** Add a simple chatbot interface for querying contract data.

**Implementation Steps:**

1. **Create chatbot backend**

   ```
   src/
   └── backend/
       └── ai/
           └── chatbot/
               ├── conversation.py    # Conversation state management
               ├── query_parser.py    # Intent recognition and query extraction
               ├── data_retriever.py  # Database retrieval functions
               └── response_gen.py    # Response generation system
   ```

2. **Implement chat UI component**

   ```
   src/
   └── frontend/
       └── components/
           └── chat/
               ├── chat_interface.py  # Chat UI component
               ├── message_types.py   # Message visualization components
               └── chat_state.py      # Streamlit state management for chat
   ```

3. **Connect to contract database**

   - Create natural language to SQL translation
   - Add parameterized query templates
   - Implement result formatting for chat interface

4. **Add basic analytical capabilities**
   - Create predefined analytical questions
   - Implement simple visualization generation
   - Add follow-up suggestion functionality

### Phase 4: Model Context Protocol (MCP) Integration (Weeks 7-9)

**Goal:** Implement the Model Context Protocol for advanced AI agent capabilities.

**Implementation Steps:**

1. **Set up MCP server infrastructure**

   ```
   src/
   └── backend/
       └── ai/
           └── mcp/
               ├── server.py          # MCP server implementation
               ├── tools/             # Tool definitions directory
               │   ├── web_search.py      # Web intelligence tool
               │   ├── doc_creator.py     # Document creation tool
               │   ├── viz_generator.py   # Visualization creation tool
               │   └── analyzer.py        # Analysis/reasoning tool
               └── mcp_types.py       # MCP message type definitions
   ```

2. **Integrate existing MCP servers**

   - **Crawl4AI MCP Server**: Implement for web intelligence gathering and RAG
   - **Vectorize**: Add for advanced retrieval and document analysis
   - **Data Exploration**: Integrate for autonomous data analysis
   - **Vega-Lite**: Implement for dynamic visualization generation
   - **MongoDB/PostgreSQL Connectors**: Adapt for database integration

3. **Create AI agent definitions**

   - Implement specialized agents for different tasks
   - Define tool permissions and capabilities
   - Create agent orchestration systems

4. **Add web intelligence capabilities**

   - Implement web scraping tools for market research
   - Add content extraction and summarization
   - Create knowledge base integration for web data

5. **Implement document creation tools**

   - Add report generation capabilities
   - Create proposal outline generators
   - Implement capture document templates

6. **Utilize python-sdk-mcp**
   - Implement Python bindings for MCP servers and clients
   - Create unified interface for all MCP tools
   - Design custom MCP server extensions

### Phase 5: Advanced Analytics and Full Integration (Weeks 10-12)

**Goal:** Integrate AI capabilities throughout the application for advanced analytics.

**Implementation Steps:**

1. **Implement AI-powered dashboard insights**

   - Add automated analysis of trends
   - Create AI-generated opportunity recommendations
   - Implement competitive intelligence briefings

2. **Create advanced visualization tools**

   - Add natural language to visualization conversion
   - Implement predictive analytics visualizations
   - Create interactive what-if analysis tools

3. **Full capture profile generation**

   - Implement comprehensive capture document generation
   - Create win strategy recommendation engine
   - Add competitive positioning analysis

4. **System optimization and refinement**
   - Performance tuning of LLM interactions
   - Implement caching strategies for frequent queries
   - Create automated training data generation from user interactions

### Phase 6: Shipley Process Integration & Advanced Capabilities (Weeks 13-16)

**Goal:** Align AI capabilities with the Shipley capture process and implement advanced features.

**Implementation Steps:**

1. **Create Shipley milestone framework integration**

   ```
   src/
   └── backend/
       └── ai/
           └── shipley/
               ├── milestone_tracker.py   # Milestone progress tracking
               ├── milestone_0.py         # Opportunity identification
               ├── milestone_1.py         # Opportunity assessment
               ├── milestone_2.py         # Bid/no-bid decision
               └── milestone_3.py         # Proposal strategy
   ```

2. **Implement MCP-based competitive analysis**

   - Create competitor database ingestion tools
   - Design capability gap analysis system
   - Implement competitive position mapping

3. **Advanced price-to-win modeling**

   - Integrate BLS wage data analysis
   - Create statistical pricing models
   - Implement scenario-based pricing analysis

4. **Implement capture profile enhancement with AI agents**
   - Create executive summary generators
   - Design win theme extractors
   - Implement discriminator analysis

### Phase 7: External Data Integration & Market Intelligence (Weeks 17-20)

**Goal:** Integrate external data sources and enhance market intelligence capabilities.

**Implementation Steps:**

1. **Create advanced external data connectors**

   ```
   src/
   └── backend/
       └── data_acquisition/
           └── connectors/
               ├── sam_gov.py         # SAM.gov integration
               ├── sba_subnet.py      # SBA SubNet integration
               ├── bls_oews.py        # BLS wage data
               ├── nato_nspa.py       # NATO procurement data
               └── sba_mentorship.py  # SBA Mentor-Protégé data
   ```

2. **Implement MCP data fusion capabilities**

   - Create cross-source data connectors
   - Design entity resolution system
   - Implement relationship mapping tools

3. **Advanced market intelligence dashboard**

   - Create agency spending predictors
   - Implement contract expiration timelines
   - Design recompete opportunity trackers

4. **Enhance data quality with AI validation**
   - Implement data quality monitoring
   - Create anomaly detection systems
   - Design data correction recommendations

## Implementation Priority and Timeline

To ensure steady progress while managing complexity, here's a suggested implementation order:

### Modularization (First Month)

1. **Week 1:** Extract theme configuration and visualization components
2. **Week 2:** Create layout component library and integrate with Streamlit config
3. **Week 3:** Extract database and data processing logic
4. **Week 4:** Implement tabbed interface components as modules

### AI Integration (Following Five Months)

1. **Weeks 1-2:** Local LLM setup with Ollama and Langfuse
2. **Weeks 3-4:** PydanticAI integration
3. **Weeks 5-6:** Basic chatbot implementation
4. **Weeks 7-9:** Model Context Protocol integration with existing servers
5. **Weeks 10-12:** Advanced analytics and full integration
6. **Weeks 13-16:** Shipley process integration & advanced capabilities
7. **Weeks 17-20:** External data integration & market intelligence

## Recommended MCP Server Integrations

Based on the project requirements and available MCP servers, here are the specific integrations recommended for implementation:

### 1. Web Intelligence & Data Collection

- **[Crawl4AI MCP Server](https://github.com/crawl4ai/mcp-server)**

  - **Purpose:** Web scraping for market research and competitive intelligence
  - **Key Features:**
    - Clean markdown generation for RAG pipelines
    - Structured data extraction from web pages
    - Advanced browser control for complex government websites
  - **Integration Timeline:** Phase 4 (Weeks 7-9)
  - **Implementation Approach:** Adapt for scraping SAM.gov, USAspending.gov, and contractor websites

- **Brave Search MCP (websearch)**

  - **Purpose:** Privacy-focused, real-time web search and retrieval using the Brave Search engine
  - **Key Features:**
    - Up-to-date, privacy-respecting web search results
    - Structured output for downstream AI analysis and RAG pipelines
    - Complements static scraping (Crawl4AI) and document retrieval (Vectorize)
    - No persistent logs or external data sharing; all queries/results handled locally
  - **Integration Timeline:** Phase 4 (Weeks 7-9)
  - **Implementation Approach:** Integrate as a core web intelligence tool, expose in AI Tools tab and web intelligence dashboard, and document best practices for combined use with other MCP agents

- **[Vectorize](https://github.com/ContextualAI/vectorize/tree/main/mcp)**
  - **Purpose:** Enhanced document retrieval and analysis
  - **Key Features:**
    - Semantic chunking for contract documents
    - Recursive summarization for long proposal documents
    - Deep research integration for competitive intelligence
  - **Integration Timeline:** Phase 4 (Weeks 7-9)
  - **Implementation Approach:** Use for enhanced RAG on contract data and external sources

### 2. Database & Data Analysis

- **[PostgreSQL MCP Connector](https://github.com/dencold/mcp-postgres)** (adapt from MySQL or MongoDB patterns)

  - **Purpose:** Native MCP integration with the project's PostgreSQL databases
  - **Key Features:**
    - Direct SQL query capabilities from LLM agents
    - Schema understanding for improved query generation
    - Data analytics integration
  - **Integration Timeline:** Phase 4 (Weeks 7-9)
  - **Implementation Approach:** Adapt from existing SQL MCP server patterns

- **[Data Exploration MCP Server](https://github.com/fcas/data-explorer)**
  - **Purpose:** Autonomous data exploration for capture insights
  - **Key Features:**
    - Pattern discovery in contract data
    - Anomaly detection in spending patterns
    - Trend analysis and visualization generation
  - **Integration Timeline:** Phase 5 (Weeks 10-12)
  - **Implementation Approach:** Connect to both PostgreSQL databases

### 3. Visualization & Analytics

- **[Vega-Lite MCP Server](https://github.com/Iapetus-11/vega-lite-mcp)**
  - **Purpose:** Dynamic visualization generation
  - **Key Features:**
    - AI-driven chart creation
    - Multi-dimensional data visualization
    - Interactive dashboard element generation
  - **Integration Timeline:** Phase 5 (Weeks 10-12)
  - **Implementation Approach:** Integrate with Streamlit for dynamic visualizations

### 4. Document Creation & Management

- **Custom Document Creation MCP Server** (based on python-sdk-mcp)
  - **Purpose:** Capture profile and proposal document generation
  - **Key Features:**
    - Multi-format document creation (Word, PDF, PowerPoint)
    - Template-based generation with dynamic content
    - Structured content organization with Shipley methodology alignment
  - **Integration Timeline:** Phase 5-6 (Weeks 10-16)
  - **Implementation Approach:** Build custom server using python-sdk-mcp

### 5. Integration Framework

- **[python-sdk-mcp](https://github.com/BdM-15/python-sdk-mcp)**
  - **Purpose:** Framework for MCP tool development and integration
  - **Key Features:**
    - Python bindings for MCP servers and clients
    - Streamlined tool development
    - Standard interfaces for MCP communication
  - **Integration Timeline:** Throughout Phase 4 (Weeks 7-9)
  - **Implementation Approach:** Use as foundation for all custom MCP server development

## Conclusion

This modularization and AI integration plan provides a structured approach to evolving the Data Insights platform. By breaking down the work into manageable steps, we can incrementally improve both the codebase structure and AI capabilities without disrupting the existing functionality.

The MCP integration strategy leverages existing servers where appropriate while building custom capabilities where needed, ensuring an optimal balance between rapid implementation and tailored functionality for capture management. Each phase builds on the previous one, ensuring that we maintain a working application throughout the process while steadily enhancing its capabilities and maintainability.

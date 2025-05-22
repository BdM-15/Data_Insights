# TASKS.md

## Active Tasks

- ~~**Fix type mismatch error in "Contracts Expiring in the Next 24 Months" section**~~:
  - Status: ✅ Fixed, tested, and working correctly.
  - ~~Sub-task: Test the updated code to ensure the section renders correctly.~~
- ~~**Render remaining visualizations**~~:
  - ✅ "Top Recipients by Total Awards Made"
  - ✅ "Top Recipients by Total Obligation Amount"
  - ✅ "Top NAICS by Award Actions"
  - ✅ "Top NAICS by Total Obligation Amount"
  - ✅ Agency/Sub-Agency/Office visuals
  - Status: ✅ Implemented and rendering correctly in expandable sections.
- **Apply expandable sections to visualizations**:
  - ✅ Implemented expandable sections for all visualizations
  - ✅ Removed diagnostic data tables for cleaner interface
  - ✅ Made "Contract Actions by Quarter & Contract Expiring Table" section expanded by default
- **Fix fiscal quarter calculation for government fiscal year**:
  - ✅ Updated fiscal year and quarter calculation to correctly align with government fiscal year (Oct 1 - Sep 30)
  - ✅ Fixed NaN handling in quarterly data visualization
    **SAM.gov Solicitation Enrichment Pipeline**:
  - ✅ Foundation: API integration, robust rate limiting, deduplication, and full-text solicitation ingestion
  - ✅ Sample enrichment function and Document model usage in `/src/backend/data_acquisition/sam_gov_enrichment_example.py`
  - ✅ Documentation in `/docs/PLANNING.md` and `/docs/CAPTUREINTEL.md`
  - Next: Implement embedding generation, semantic search, and RAG workflows
  - Status: ✅ Foundation complete, ready for implementation
- **Implement Automated Schema Migration for Data Sources**:
  - ✅ Created dynamic schema detection and adaptation system for external data sources
  - ✅ Implemented automatic column addition when source data formats change
  - ✅ Added case-insensitive column matching to prevent duplication
  - ✅ Fixed NATO NSPA data import to preserve original XML field names and formats
  - ✅ Eliminated need for manual table recreation when data sources evolve
  - ✅ Added detailed logging for schema changes to track format evolution
  - Status: ✅ Completed. NATO NSPA importer now handles schema changes gracefully.
- **Reorganize Codebase Structure**:
  - ✅ Implemented a clean, modular folder structure for better organization
  - ✅ Created proper Python package hierarchy with **init**.py files
  - ✅ Restructured backend functionality into logical modules:
    - ✅ core: Database utilities and common functions
    - ✅ data_processing: Data transformation and cleansing
    - ✅ data_acquisition: Data fetching from external sources
    - ✅ ai: AI integration components
  - ✅ Organized frontend code into specialized directories:
    - ✅ pages: Streamlit multipage components
    - ✅ components: Reusable UI elements
    - ✅ visualizations: Data visualization components
    - ✅ capture: Capture management features
  - ✅ Moved config.py to the root directory for easier access
  - ✅ Updated documentation to reflect the new structure
  - Status: ✅ Completed. Codebase now follows a clean, modular architecture.
- ~~**Database Migration to PostgreSQL**~~:
  - ✅ Successfully migrated data from SQLite to PostgreSQL for improved performance with large datasets
  - ✅ Updated connection strings and database queries in application code
  - ✅ Optimized PostgreSQL configuration for high-performance operation
  - ✅ Verified all functionality works correctly with the new database
  - Status: ✅ Completed, with significant performance improvements observed
- ~~**Full USAspending Database Restoration**~~:

  - ✅ Successfully restored complete USAspending.gov database (1.1TB) on May 1, 2025
  - ✅ Completed all restoration phases (schema creation, data loading, index creation)
  - ✅ Optimized PostgreSQL instance on port 5433 with performance settings
  - ✅ Created all database schemas, tables, and relationships
  - ✅ Established primary key constraints and specialized indexes
  - ✅ Updated documentation with database connection details
  - Status: ✅ Completed, database now fully operational

- ~~**Optimize Data Cleansing Process**~~:
  - ✅ Completely redesigned data_cleansing.py using direct SQL transformations
  - ✅ Reduced processing time from 3.5+ hours to under 12 minutes for 22 million records
  - ✅ Achieved processing speeds of ~29,000 rows per second
  - ✅ Removed 3.6 million duplicate records (16.58% of the original data)
  - ✅ Fixed data type handling issues for proper data normalization
  - Status: ✅ Completed with dramatic performance improvements
- ~~**Fix filter dependencies JSON handling**~~:
  - ✅ Fixed JSON handling in the `get_unique_values` function to properly handle both string JSON and parsed list types
  - ✅ Resolved error: "the JSON object must be str, bytes or bytearray, not list" when selecting parent filter values
  - ✅ Added robust error handling for JSON parse failures
  - ✅ Improved sorting and deduplication of filter values
  - Status: ✅ Completed, dependent filters now working correctly
- **Implement Streamlit Multipage Application Structure**:
  - ✅ Redesigned application architecture with modular structure
  - ✅ Created app.py as main entry point with dashboard functionality
  - ✅ Implemented proper import structure for modules
  - ✅ Set up navigation in sidebar with page references
  - ✅ Established component organization (filters, charts, export)
  - Status: **COMPLETE**
- **Implement Tabbed Interface Components**:
  - ✅ Added tabbed layouts to Strategic Dashboard (Overview, Trends, Opportunities)
  - ✅ Created consistent styling across all tabs
  - ✅ Implemented placeholders for content within tabs
  - Status: **COMPLETE**
- **Enhanced Strategic Dashboard UI**:
  - ✅ Centered metric card titles for improved readability
  - ✅ Redesigned sidebar layout based on project documentation structure
  - ✅ Created proper navigation structure in sidebar with logical page organization
  - ✅ Removed diagnostic sidebars for a cleaner interface
  - ✅ Added About section in sidebar footer with version information
  - ✅ Applied consistent electric theme styling throughout the dashboard
  - ✅ Created placeholders for secondary tabs (Agency Intelligence, Competitive Analysis, etc.)
  - Status: **COMPLETE**
- **Implement Competitive Analysis Tab**:
  - ✅ Created Market Share Analysis visualization with horizontal bar chart
  - ✅ Implemented Win Rate Analysis with competitors visualization
  - ✅ Developed quadrant-based Market Position Analysis scatter plot
  - ✅ Added Competitor-Agency Relationships heatmap visualization (now consistently readable)
  - ✅ Created Contract Type competition intensity analysis (with correct contract type labeling)
  - ✅ Implemented dual-axis Contract Type Value Analysis chart
  - ✅ Added actionable Competitive Strategy Insights section
  - ✅ Incorporated "number_of_offers_received" data for competition intensity
  - ✅ Added PWin modeling based on competitive analysis
  - Status: **COMPLETE** (May 2025)
- **Implement Future Opportunities Tab**:
  - ✅ Added "Future Opportunities" tab between "Market Overview" and "Agency Intelligence"
  - ✅ Created placeholder with informational text explaining the tab's purpose
  - ✅ Outlined planned visualizations with bullet points
  - [ ] Implement the following planned visualizations:
    - [ ] Expiring Contracts Timeline for next 6-24 months
    - [ ] Strategic Alignment Analysis (Suitability vs. Synergy quadrant chart)
    - [ ] Active SAM.gov Opportunities with capability match scoring
    - [ ] NATO NSPA Opportunities integration with capability match scoring
    - [ ] Strategic Connections showing links between historical performance and future opportunities
  - [ ] Integrate data from both SAM.gov and NATO NSPA APIs
  - [ ] Implement capability match scoring algorithm based on historical performance
  - [ ] Add clickable links to opportunity details on SAM.gov and NATO NSPA portals
  - Status: **PARTIAL - Basic tab created, full implementation pending** (April 2025)
- **Contract Vehicle Analysis Tab**:
  - ✅ All planned visualizations (pie, stacked bar, line, bar) and export features implemented and error-free
  - ✅ Fixed KeyError by aggregating vehicle preference by agency directly from the original DataFrame using the correct columns
  - ✅ Fixed KeyError for 'vehicle_type' and 'obligation' by using 'contract_vehicle' and aggregating from the original DataFrame as needed
  - ✅ Replaced all references to THEME['category_colors'] with a local CATEGORY_COLORS list for Plotly charts
- **Geographic Analysis Tab**:
  - ✅ All planned visualizations (choropleth, bar, scatter geo) and export features implemented and error-free
  - ✅ Added export functionality for each visualization
  - ✅ Added CATEGORY_COLORS for future categorical charts
  - ✅ All error handling and missing data cases are covered

## Strategic Dashboard Implementation Tasks

### Phase 1: Core Dashboard Development (Completed)

- [x] Create new `strategic_dashboard.py` file in the frontend/pages directory
- [x] Set up dashboard layout with tabs and placeholder components
- [x] Implement base query for NAICS 561210 data
- [x] Add global filters for date range, agency, and other dimensions
- [x] Calculate and display executive summary metrics
  - [x] Total obligations in NAICS 561210
  - [x] Total award actions (Modification No = '0' only)
  - [x] Average award value
  - [x] Active contracts count
  - [x] Expiring contracts (24mo) count
  - [x] Suitability percentage for expiring contracts
  - [x] Synergy percentage across business units
  - [ ] Average bidders (competition intensity) metric
  - [ ] Estimated pWin percentage based on competition
- [x] Optimize logo display in sidebar
- [x] Modernize navigation links for sleek appearance
- [x] Add Clear Filters button to filter controls
- [x] Fetch all NAICS codes from PostgreSQL database
- [x] Develop combined obligations and award actions trend chart
  - [x] Dual-axis visualization with bar and line
  - [x] Quarterly breakdown with fiscal year markers
  - [x] Interactive tooltips with detailed metrics
- [x] Implement agency-to-obligation ratio analysis
  - [x] Scatter plot with quadrant analysis
  - [x] Size bubbles by average award value
  - [x] Add interactive elements for agency details
- [x] Create contract vehicle distribution visualization
  - [x] Donut chart of vehicle types
  - [x] Tooltips with vehicle details and counts
  - [x] Link to detailed vehicle analysis
- [x] Build competitive landscape visualization
  - [x] Treemap of top competitors
  - [x] Color coding by win rate
  - [x] Interactive elements for competitor details

### Phase 2: Secondary Analysis Tabs (In Progress)

- [x] Create Market Share Analysis visualization with horizontal bar chart
- [x] Implement Win Rate Analysis with competitors visualization
- [x] Develop quadrant-based Market Position Analysis scatter plot
- [x] Add Competitor-Agency Relationships heatmap visualization
- [x] Create Contract Type competition intensity analysis
- [x] Implement dual-axis Contract Type Value Analysis chart
- [x] Add actionable Competitive Strategy Insights section
- [ ] Incorporate "number_of_offers_received" data when available
- [ ] Add PWin modeling based on competitive analysis
- [ ] Create agency hierarchy visualization
- [ ] Implement agency year-over-year growth chart
- [ ] Develop set-aside utilization patterns visualization
- [ ] Build single vs. multiple award analysis component
- [ ] Implement Expiring Contracts Timeline for next 6-24 months
- [ ] Develop Strategic Alignment Analysis (Suitability vs. Synergy quadrant chart)
- [ ] Integrate SAM.gov Opportunities with capability match scoring
- [ ] Integrate NATO NSPA Opportunities with capability match scoring
- [ ] Create Strategic Connections visualization
- [ ] Create vehicle preference by agency visualization
- [ ] Implement award type distributions chart
- [ ] Develop single vs. multiple award trends analysis
- [ ] Build vehicle success rate visualization
- [ ] Create performance by location map
- [ ] Implement regional spending patterns visualization
- [ ] Develop geographic concentration of awards chart

### Phase 3: Enhancements and Optimization (Planned)

- [ ] Add expandable cards for drill-down analysis
- [ ] Implement dashboard state saving
- [ ] Create export functionality for visualizations
- [ ] Add user preference settings
- [ ] Optimize database queries for performance
- [ ] Implement caching for frequently accessed data
- [ ] Add progress indicators for long-running queries
- [x] Replace Unicode characters with ASCII-compatible alternatives for improved compatibility
- [ ] Optimize visualization rendering
- [ ] Create user documentation for dashboard features
- [ ] Develop testing plan for dashboard components
- [ ] Perform cross-browser compatibility testing
- [ ] Solicit user feedback and make refinements

## Backlog

- **Develop Model Context Protocol (MCP) Integration**:

  - ✅ First MCP tool (GitHub MCP server) is now fully integrated and running locally via Docker and VS Code configuration (`.vscode/mcp.json`).
  - ✅ All MCP tool processing is local, with no external API calls for AI/LLM inference, in line with project privacy requirements.
  - ✅ See `github-mcp-server/Dockerfile` and `.vscode/mcp.json` for implementation details.

  - Sub-tasks:
    - **Visualization Tool Integration**:
      - Design and develop a dedicated Python-based UI for interactive visualizations of USASpending.gov data
      - Create specialized visualization templates for contract awards, spending trends, and competitor analysis
      - Implement drill-down capabilities for detailed exploration of data points
      - Integrate visualization exports for presentations and proposals
      - Connect visualization tool with the main USAspending.gov Data Explorer app
    - **Chatbot for Award Data Analysis**:
      - Develop an AI-powered conversational interface integrated directly into VS Code
      - Train the model on USASpending.gov data structures and business development concepts
      - Implement query understanding for natural language questions about contract data
      - Create context-aware response generation with data visualization capabilities
      - Build a conversation history feature for continuing analysis sessions
    - **Capability Identifier Tool**:
      - Create data processing workflows to digest prime and sub-award data
      - Develop algorithms to identify company and competitor core capabilities
      - Build gap analysis functionality to highlight competitive opportunities
      - Implement competitiveness assessment metrics and win probability estimation
      - Design solution brainstorming features powered by AI
      - Create report generation for capability assessments
    - **Web Intelligence Scraper**:
      - Develop a web scraping engine to gather market intelligence from public sources
      - Implement targeted searches for news articles, X (Twitter) posts, LinkedIn updates, and public filings
      - Create entity detection to monitor specific agencies, competitors, and technology trends
      - Build search functionality for Google, news sites, social media, and government portals
      - Develop data cleaning and preprocessing of scraped content
      - Integrate Crawl4AI for high-performance, LLM-friendly web crawling and data extraction:
        - Utilize its markdown generation capability for direct LLM ingestion
        - Implement structured extraction for consistent data formatting
        - Leverage advanced browser control for navigating complex government websites
        - Use parallel crawling for faster intelligence gathering
        - Benefit from its open-source approach with no API key requirements
      - Integrate LLM-based summarization to convert raw web content into actionable intelligence
      - Create custom intelligence digests by topic (customer priorities, competitive moves, market trends)
      - Add document storage for historical analysis and trend identification
      - Implement privacy-preserving measures to ensure compliance with terms of service
      - Build integration with VS Code to enable quick reference during document creation
    - **Document Creator/Editor Agent**:
      - Build AI agent to create and update multiple document types (Word, Excel, CSV, PowerPoint)
      - Implement template library for different document types (capture profiles, briefings, proposals)
      - Develop context-aware document generation based on analyzed data
      - Create export capabilities for different formats and styling options
      - Build integration with other AI agents for seamless workflow
  - Status: Planned, high priority as these tools will provide the foundation for the Capture Profile feature

- **Enhance User Interface**:

  - Sub-tasks:
    - Implement filter state persistence between sessions
    - Add custom CSS for improved branding
    - Create dynamic help tooltips for filters and charts
  - Status: Planned, medium priority

- **Complete Data Explorer Page**:

  - Sub-tasks:
    - Implement advanced filtering functionality
    - Create detailed data table view with sorting/filtering
    - Add export functionality for filtered data
  - Status: Planned, high priority

- **Implement Visualizations Page**:

  - Sub-tasks:
    - Create comprehensive visualization library
    - Implement user customization options for charts
    - Add interactive features (drill-down, tooltips)
  - Status: Planned, medium priority

- **Add AI Tools Integration**:
  - Sub-tasks:
    - Connect to Ollama API for local LLM inference
    - Implement contract analysis features
    - Create capture profile generation capability
  - Status: Planned, medium priority

## User Interface Enhancement Tasks

- **Implement Streamlit Multipage Application Structure**:

  - Sub-tasks:
    - **Redesign Application Architecture**:
      - Convert existing monolithic app.py into modular multipage structure
      - Create a `pages/` directory with individual page scripts
      - Implement homepage (app.py) as the strategic dashboard
      - Create consistent navigation and state management across pages
    - **Develop Page Components**:
      - Create `data_explorer.py` for advanced filtering and query functionality
      - Develop `visualizations.py` for comprehensive visualization library
      - Implement `capture_profiles.py` for profile generation interface
      - Build `ai_tools.py` for AI-powered features access
      - Create `admin.py` for administrative functions (restricted access)
    - **Create Shared Component Library**:
      - Develop reusable filter components for consistent filtering across pages
      - Create standardized visualization components
      - Implement shared state management utilities
      - Build consistent header/footer components
    - **Ensure Cross-Page State Persistence**:
      - Implement session state management for filter selections
      - Create data caching strategy for query results
      - Ensure visualization settings persist between page navigations
  - Status: Planned, high priority to improve application organization and user experience

- **Implement Tabbed Interface Components**:

  - Sub-tasks:
    - **Add Tabbed Layouts to Strategic Dashboard**:
      - Create "Overview", "Trends", "Opportunities", and "Competitive Analysis" tabs
      - Implement consistent styling across all tabs
      - Ensure efficient data loading to minimize tab switching delays
    - **Implement Tabbed Results View**:
      - Create "Table View", "Summary View", and "Visual View" tabs for query results
      - Ensure data is shared efficiently between tabs
      - Implement consistent interaction patterns across tabs
    - **Add Tabbed Visualization Library**:
      - Organize visualizations by category (timeline, geographic, comparative, etc.)
      - Create consistent control patterns across visualization tabs
      - Implement cross-tab data sharing for consistent filtering
    - **Develop Tabbed Configuration Interfaces**:
      - Create logical groupings for configuration options
      - Implement "Basic", "Advanced", and "Expert" settings tabs
      - Add help content and guidance in each settings tab
  - Status: Planned, medium priority to organize content within pages

- **Implement Advanced Streamlit Features**:
  - Sub-tasks:
    - **Enhance Performance with Caching**:
      - Implement `@st.cache_data` for database query results
      - Add `@st.cache_resource` for database connections and model loading
      - Create invalidation strategy for cached data
    - **Add Interactive Callbacks**:
      - Replace full-page refreshes with targeted component updates
      - Implement progressive disclosure for complex forms
      - Create dynamic filtering with instant feedback
    - **Improve User Experience**:
      - Add loading animations for long-running operations
      - Implement tooltips and contextual help throughout the application
      - Create guided workflows for complex tasks
    - **Customize Visual Design**:
      - Implement custom CSS for consistent branding
      - Create dark/light mode toggle
      - Add responsive design elements for different screen sizes
    - **Implement Session State Management**:
      - Create utilities for managing complex state across the application
      - Implement state persistence between sessions
      - Add user preference storage
  - Status: Planned, medium priority to enhance overall application experience

## Model Context Protocol (MCP) Tools Integration for Streamlit App

- **Add MCP Integration to Streamlit Interface**:

  - Sub-tasks:
    - **Create MCP Tools Tab in Streamlit**:
      - Implement a multi-tab interface in the Streamlit app
      - Create a dedicated "AI Tools" tab for MCP integration
      - Design a clean UI for tool selection and interaction
      - Implement authentication/security for AI tool access
    - **Chatbot Interface Integration**:
      - Embed a conversational interface in the Streamlit sidebar
      - Connect the interface to local Ollama runtime
      - Implement context-aware prompting with active filters and selected data
      - Add conversation history management
      - Create specialized prompts for contract analysis questions
    - **Capture Profile Generator UI**:
      - Add "Generate Capture Profile" button to query results
      - Create a form for capture profile customization options
      - Implement progress indicator for document generation
      - Add preview capability for generated profiles
      - Include download options for different formats (DOCX, PDF)
    - **Web Intelligence Integration**:
      - Create a search interface for market intelligence gathering
      - Implement entity selection (agencies, companies, technologies)
      - Add visualization for intelligence mapping
      - Create a digest generator for web intelligence findings
    - **Visualization Tool Enhancement**:
      - Add AI-assisted visualization recommendation engine
      - Implement natural language query-to-visualization converter
      - Create custom visualization templates for federal contracting
      - Add annotation and sharing capabilities
  - Status: Planned, to be implemented after core MCP tools are developed

- **Implement Shipley Capture Milestone Mapping**:

  - Sub-tasks:
    - Create data model for Shipley milestone framework (0-3) in the database
    - Develop milestone tracking dashboard with milestone-specific KPIs
    - Implement automated data collection for milestone decision requirements
    - Build milestone progression tracking and notification system
    - Create milestone decision documentation tools
    - Integrate advanced pricing analysis components:
      - Historical price range analysis
      - Pricing strategy percentile analysis
      - Agency-specific pricing patterns analysis
      - Competitor pricing analysis
      - Price-to-win predictive modeling
      - Cost structure analysis
      - Best Value vs. LPTA prediction
    - Design comparison views for competitive assessment at each milestone
  - Status: Planned, high priority to enhance capture management capabilities

- **Create Robust Data Dictionary**:

  - Sub-tasks:
    - Document all database tables, views, and their relationships
    - Define each data field with descriptions, data types, and business context
    - Map data fields to their source systems and transformation logic
    - Create metadata documentation for calculated fields and KPIs
    - Document data refresh cycles and update processes
    - Build searchable data dictionary interface within the application
    - Implement data lineage tracking for complex derived fields
    - Create user-friendly documentation for business users
    - Establish data governance procedures for maintaining the dictionary
  - Status: Planned, important foundational task for system documentation and user adoption

- **Implement "Enhanced Capture Profile Generator"**:

  - Sub-tasks:
    - Design an integrated framework that leverages outputs from all MCP tools
    - Create templated sections for different capture profile components (opportunity overview, customer analysis, competitive analysis, win strategy)
    - Implement row selection in the "Query Results" DataFrame to initiate profile generation
    - Add functionality to incorporate visualizations, chatbot insights, and capability assessments directly into the document
    - Integrate Ollama for local LLM inference on GTX 4060 with CUDA to generate narrative sections
    - Use `python-docx` to assemble the complete document with proper formatting and branding
    - Add export capabilities for different formats (DOCX, PDF)
    - Ensure all processing remains local for privacy
    - Create executive summary section that synthesizes key findings from all AI tools
    - Implement competitive positioning analysis based on Web Intelligence tool outputs
    - Build probability of win calculation using multi-factor scoring from all sources
    - Add strategic recommendation section generated from Analysis and Reasoning tool
    - Include automated generation of visual aids and supporting materials for proposal teams
  - Status: Planned, to be developed after MCP tools are functional, as it represents the end-state deliverable that consolidates all AI capabilities

- **External Data Source Integration**:

  - Sub-tasks:
    - **SAM.gov Integration**:
      - Develop API connector for SAM.gov to access future opportunity data
      - Create data pipeline for combining historical with future opportunity data
      - Implement filtering and search capabilities for SAM.gov opportunities
    - **SBA SubNet Integration**:
      - Build connector for SBA's SubNet to access subcontracting opportunities
      - Implement data processing for potential teaming partner identification
      - Create visualization of subcontracting opportunities by industry and agency
    - **GovWin IQ API Integration**:
      - Develop secure API key management for GovWin IQ access
      - Create data pipeline for pre-RFP intelligence and teaming partners
      - Build integration with opportunity qualification workflows
      - Implement agency insights visualization from GovWin data
    - **Bloomberg Government API Integration**:
      - Develop secure API key management for BGov access
      - Create data pipeline for financial insights and legislative tracking
      - Build subcontractor data integration for teaming opportunities
      - Implement visualization of agency spending trends from BGov data
    - **ILOSTAT Database API Integration**:
      - Implement secure API key management for ILOSTAT access
      - Create data connector for accessing international labor statistics
      - Develop data processing for global wage rate analysis
      - Implement filtering to use global data only when appropriate for international opportunities
      - Build visualization components for comparative wage analysis across regions
      - Create integration with pricing models for international opportunities
    - **Data.gov Contract-Awarded Labor Category API Integration**:
      - Develop secure API key management for Data.gov CALC API
      - Create data pipeline for labor category rates and qualifications
      - Build integration with pricing strategy components
      - Implement visualization of market rates for common labor categories
      - Create capability to benchmark proposed rates against historical awarded rates
      - Develop integration with price-to-win modeling
    - **Bureau of Labor Statistics OEWS API Integration**:
      - Implement secure API key management for BLS API access
      - Create data connector for accessing Occupational Employment and Wage Statistics
      - Develop data processing pipeline for 800+ occupations across industries and geographic areas
      - Build integration with pricing strategy and labor rate analysis components
      - Create visualization tools for wage percentiles (10th, 25th, median, 75th, 90th)
      - Implement cross-industry wage comparison by region
      - Add capability to benchmark proposed rates against standard occupation wages
      - Develop geographic wage variation analysis for distributed contract work
    - **Salesforce REST API Integration**:
      - Create bidirectional sync between data platform and Salesforce CRM
      - Develop automated opportunity feeds into Salesforce
      - Build contact intelligence integration for relationship management
      - Implement capture management workflow automation
  - Status: Planned, to be developed in parallel with MCP tools for comprehensive data solution

- **Add Admin-Only Data Fetch Interface**:

  - Sub-tasks:
    - **Create Admin Authentication System**:
      - Implement user identification via environment variable (ADMIN_USER_IDS)
      - Add session-based authentication mechanism to Streamlit interface
      - Create secure admin verification function
    - **Build Admin Data Fetch Interface**:
      - Add admin-only data fetch button to sidebar for authenticated users
      - Create modal dialog with source selection options (SAM.gov, NATO, USAspending)
      - Implement progress indicators for ongoing fetches
      - Display fetch status and results summary
    - **Add Logging and Monitoring**:
      - Create detailed logs of data fetch operations
      - Implement notification system for completed fetches
      - Add error reporting with diagnostics
  - Status: Planned, medium priority to provide convenient data refresh without exposing to all users

- **Implement Strategic Default Dashboard**:

  - Sub-tasks:
    - **Create Multi-Tab Interface**:
      - Develop a default "Strategic Overview" tab that loads automatically
      - Implement dynamic visualization updates based on sidebar filters
      - Create a professional, clean UI with expandable sections and tooltips
    - **Develop Historical Contract Summary**:
      - Visualize contract spending trends by fiscal quarter and year
      - Create agency/sub-agency/office hierarchical drill-down visualizations
      - Add top NAICS code analysis with descriptions and spending patterns
    - **Build Contract Vehicle Analysis**:
      - Implement pie charts for contract vehicle types (IDV, single/multiple award)
      - Create distribution visualizations by agency and NAICS code
      - Add timeline view of IDV expiration dates and remaining ceiling values
    - **Create Geographic Visualization**:
      - Implement interactive heat map of contract place of performance
      - Show award density by state with drill-down capabilities
      - Include filtering by NAICS, PSC, and agency
    - **Add Competitive Landscape Analysis**:
      - Create market share visualization for top contractors
      - Show small business participation metrics
      - Visualize competitor performance by NAICS code and agency
    - **Implement Projected Spend Forecast**:
      - Develop ML-based projection model for future spending
      - Create 24-36 month forecast visualization with confidence intervals
      - Show projected obligations by agency and NAICS code
    - **Expiring Contracts Timeline**:
      - Build interactive timeline of contracts expiring in next 6-24 months
      - Include filtering by value threshold, NAICS, and agency
      - Provide strategic opportunity assessment for each expiring contract
  - Status: Planned, high priority to enhance business intelligence capabilities and provide immediate value on application launch

- **Add advanced filtering**:
  - Implement keyword search for contract descriptions.
  - Add multi-select filters for NAICS/PSC codes.
  - Status: Planned.
- **Enhance visualizations**:
  - Add interactive features (e.g., tooltips, drill-downs).
  - Add new visuals for contract type, extent competed, or set-aside type trends.
  - Status: Planned.
- **Optimize performance**:
  - Explore lazy loading or pagination for large datasets.
  - Review database indexes for further optimization.
  - Status: Planned.

## GitHub Copilot Integration

- **Implement GitHub Copilot Custom Tools**:
  - ✅ Created a `.copilot` directory structure for custom tool definitions
  - ✅ Developed eight specialized tool configurations for project-specific assistance:
    - Contract Analysis Tool: For analyzing federal contracts from USAspending.gov data
    - Capture Management Tool: For capture management and business development code
    - PostgreSQL Query Generator: For optimized database queries
    - Streamlit Visualization Helper: For advanced Streamlit/Plotly visualizations
    - MCP Integration Tool: For Model Context Protocol integration templates
    - Shipley Milestone Framework Helper: For implementing capture milestone tracking
    - Data Pipeline Integration Tool: For external data source integration
    - Capture Profile Generator Tool: For AI-assisted capture profile creation
  - Sub-tasks:
    - Implement supporting Python functions referenced by the Copilot tools
    - Create test cases to validate tool functionality
    - Document usage patterns for each tool
    - Refine tool definitions based on usage feedback
  - Status: ✅ Tool framework created, supporting functions pending implementation

## Milestones

- **Milestone 1: Core Functionality Complete**:
  - ✅ Query and filter data.
  - ✅ Display results in a DataFrame with CSV export.
  - ✅ Render all visualizations correctly in expandable sections.
  - Status: ✅ Completed
- **Milestone 2: MCP Integration and Advanced AI Tools**:
  - ✅ Integrate and deploy the first MCP tool (GitHub MCP server) as a local agent service
  - ✅ Document configuration and usage in planning and modularization docs
  - ✅ Test agent workflow end-to-end with local LLM inference
  - Develop and integrate Visualization Tool with the main application
  - Create VS Code integrated Chatbot for award data analysis
  - Build Capability Identifier for competitive analysis
  - Implement Web Intelligence Scraper for market research
  - Develop Document Creator/Editor Agent for multi-format outputs
  - Status: Planned, first priority to establish the foundation for advanced features.
- **Milestone 3: External Data Source Integration**:
  - Integrate SAM.gov API for future opportunity data
  - Connect SBA SubNet for subcontracting opportunities
  - Implement GovWin IQ and Bloomberg Government API integrations
  - Create Salesforce REST API connector for CRM integration
  - Status: Planned, to be developed in parallel with MCP tools.
- **Milestone 4: Enhanced Capture Management**:
  - Implement pipeline building with automated opportunity feeds
  - Develop opportunity qualification with PWin scoring models
  - Create teaming partner identification and management
  - Build competitive analysis with visualization dashboards
  - Implement proposal development automation
  - Status: Planned, to be developed after data source integration.
- **Milestone 5: Enhanced Capture Profile Generator**:

  - Implement a comprehensive profile generator that leverages all MCP tools
  - Create document generation with AI-assisted narratives and integrated visualizations
  - Build export capabilities for proposal and business development teams
  - Develop executive summary with synthesized intelligence from all sources
  - Implement PWin calculation using multi-factor analysis from all tools
  - Create strategic recommendation sections from Analysis and Reasoning tool
  - Build automated visual aids generation for proposal support
  - Generate ghosting strategies based on competitor intelligence
  - Status: Planned, to be developed after MCP tools are functional, as it represents the end-state deliverable that consolidates all AI capabilities

- **Milestone 6: Advanced Features and Optimization**:
  - Add advanced filtering and enhanced visualizations.
  - Optimize performance for large datasets.
  - Status: Planned.
- **Milestone 7: UI/UX Enhancement**:
  - Implement multipage application structure
  - Add tabbed interfaces for content organization
  - Integrate advanced Streamlit features for improved user experience
  - Status: Planned, to be implemented after core functionality is stable.

## Future Development Tasks

### Competition Analysis Enhancement

- [ ] Integrate "number_of_offers_received" data from USAspending.gov for competition intensity analysis
- [ ] Develop visualization for competitive density by agency, NAICS, and contract type
- [ ] Create mathematical pWin model using number of bidders as a key factor
- [ ] Add competition level filter to strategic dashboard sidebar (Low: 1-2, Medium: 3-5, High: 6+)
- [ ] Generate "sweet spot" analysis identifying optimal value-to-competition ratio opportunities
- [ ] Add competition intensity metrics to executive summary dashboard
- [ ] Incorporate competition level insights into Shipley milestone process

### Automated Data Fetch Scheduler

- [ ] Implement scheduled data fetching system to replace manual refresh process
- [ ] Create configurable schedule for different data sources (USAspending, SAM.gov, NATO NSPA)
- [ ] Add logging and notification system for scheduled fetch results
- [ ] Implement retry mechanism for failed fetches with exponential backoff
- [ ] Create admin dashboard for schedule configuration and monitoring
- [ ] Add health check reporting for data source connectivity
- [ ] Implement differential update to only fetch new/changed records
- [ ] Develop email/notification alerts for fetch failures or anomalies

### Langfuse Observability Integration

- [ ] **Set up Langfuse for LLM observability**:

  - [ ] Install Langfuse SDK in the Data_Insights environment
  - [ ] Configure Langfuse connection (API keys, endpoints)
  - [ ] Implement core tracing functionality in AI component framework
  - [ ] Create initial prompt templates in Langfuse for version control
  - [ ] Set up evaluation metrics specific to federal contracting domain

- [ ] **Integrate Langfuse with MCP Tools**:
  - [ ] Add tracing to the VS Code integrated Chatbot for award data analysis
  - [ ] Implement prompt versioning in the Document Creator/Editor Agent
  - [ ] Add observability to Capability Identifier Tool LLM calls
  - [ ] Integrate Web Intelligence Scraper with Langfuse tracing
  - [ ] Set up trace session management for user interactions
- [ ] **Create Custom Evaluation Framework**:

  - [ ] Define domain-specific evaluation criteria for federal contract analysis
  - [ ] Implement LLM-as-a-judge evaluators for capture profile quality
  - [ ] Create evaluation dashboards for AI component performance
  - [ ] Set up feedback collection from business development users
  - [ ] Develop benchmarks using historical successful capture profiles

- [ ] **Establish Test Datasets in Langfuse**:

  - [ ] Create datasets of example contracts from different agencies
  - [ ] Build prompt testing frameworks for each contracting scenario
  - [ ] Set up automated testing using contract datasets
  - [ ] Implement A/B testing for prompt variations

- [ ] **Implement Prompt Management System**:
  - [ ] Create centralized prompt library in Langfuse
  - [ ] Establish versioning workflow for prompt improvements
  - [ ] Document prompt strategies and parameters
  - [ ] Implement prompt templates for different contract types and agencies

### PydanticAI Framework Integration

- [ ] **Set up PydanticAI for MCP agent development**:

  - [ ] Install PydanticAI in the Data_Insights environment
  - [ ] Create core agent architecture for structured LLM interactions
  - [ ] Develop domain-specific Pydantic models for federal contract data
  - [ ] Implement base dependency injection system for database access
  - [ ] Set up agent configuration with Ollama models for local inference

- [ ] **Structured Agent Implementation for MCP Tools**:

  - [ ] Create contract analysis agent with structured output validation
  - [ ] Implement capture profile generator with document structure validation
  - [ ] Build competitor analysis agent with defined output schema
  - [ ] Develop agency intelligence agent with structured agency insights
  - [ ] Create pricing analysis agent with structured pricing recommendations

- [ ] **Type-Safe Agent Composition**:

  - [ ] Implement modular agent design with composition patterns
  - [ ] Create agent pipelines with validated intermediate outputs
  - [ ] Develop typed communication between agent components
  - [ ] Build testing framework for agent interactions
  - [ ] Create error handling and recovery strategies for agent failures

- [ ] **Integrate with Database and External Data**:

  - [ ] Implement dependency injection for PostgreSQL database context
  - [ ] Create structured data types for USAspending database entities
  - [ ] Build Pydantic models for external API responses (SAM.gov, NATO NSPA)
  - [ ] Develop context providers for real-time data access
  - [ ] Create caching mechanisms for expensive data operations

- [ ] **Develop Federal Contract Domain-Specific Models**:
  - [ ] Create structured models for opportunity qualification
  - [ ] Implement capture planning document schema
  - [ ] Build competitive analysis report structure
  - [ ] Develop price-to-win model with structured components
  - [ ] Create proposal strategy recommendation schema
  - [ ] Implement win themes generator with structured outputs

Future Development Tasks

### Competition Analysis Enhancement

- [ ] Integrate "number_of_offers_received" data from USAspending.gov for competition intensity analysis
- [ ] Develop visualization for competitive density by agency, NAICS, and contract type
- [ ] Create mathematical pWin model using number of bidders as a key factor
- [ ] Add competition level filter to strategic dashboard sidebar (Low: 1-2, Medium: 3-5, High: 6+)
- [ ] Generate "sweet spot" analysis identifying optimal value-to-competition ratio opportunities
- [ ] Add competition intensity metrics to executive summary dashboard
- [ ] Incorporate competition level insights into Shipley milestone process

### Automated Data Fetch Scheduler

- [ ] Implement scheduled data fetching system to replace manual refresh process
- [ ] Create configurable schedule for different data sources (USAspending, SAM.gov, NATO NSPA)
- [ ] Add logging and notification system for scheduled fetch results
- [ ] Implement retry mechanism for failed fetches with exponential backoff
- [ ] Create admin dashboard for schedule configuration and monitoring
- [ ] Add health check reporting for data source connectivity
- [ ] Implement differential update to only fetch new/changed records
- [ ] Develop email/notification alerts for fetch failures or anomalies

Future Development Tasks

### Competition Analysis Enhancement

- [ ] Integrate "number_of_offers_received" data from USAspending.gov for competition intensity analysis
- [ ] Develop visualization for competitive density by agency, NAICS, and contract type
- [ ] Create mathematical pWin model using number of bidders as a key factor
- [ ] Add competition level filter to strategic dashboard sidebar (Low: 1-2, Medium: 3-5, High: 6+)
- [ ] Generate "sweet spot" analysis identifying optimal value-to-competition ratio opportunities
- [ ] Add competition intensity metrics to executive summary dashboard
- [ ] Incorporate competition level insights into Shipley milestone process

### Automated Data Fetch Scheduler

- [ ] Implement scheduled data fetching system to replace manual refresh process
- [ ] Create configurable schedule for different data sources (USAspending, SAM.gov, NATO NSPA)
- [ ] Add logging and notification system for scheduled fetch results
- [ ] Implement retry mechanism for failed fetches with exponential backoff
- [ ] Create admin dashboard for schedule configuration and monitoring
- [ ] Add health check reporting for data source connectivity
- [ ] Implement differential update to only fetch new/changed records
- [ ] Develop email/notification alerts for fetch failures or anomalies

Future Development Tasks

### Competition Analysis Enhancement

- [ ] Integrate "number_of_offers_received" data from USAspending.gov for competition intensity analysis
- [ ] Develop visualization for competitive density by agency, NAICS, and contract type
- [ ] Create mathematical pWin model using number of bidders as a key factor
- [ ] Add competition level filter to strategic dashboard sidebar (Low: 1-2, Medium: 3-5, High: 6+)
- [ ] Generate "sweet spot" analysis identifying optimal value-to-competition ratio opportunities
- [ ] Add competition intensity metrics to executive summary dashboard
- [ ] Incorporate competition level insights into Shipley milestone process

### Automated Data Fetch Scheduler

- [ ] Implement scheduled data fetching system to replace manual refresh process
- [ ] Create configurable schedule for different data sources (USAspending, SAM.gov, NATO NSPA)
- [ ] Add logging and notification system for scheduled fetch results
- [ ] Implement retry mechanism for failed fetches with exponential backoff
- [ ] Create admin dashboard for schedule configuration and monitoring
- [ ] Add health check reporting for data source connectivity
- [ ] Implement differential update to only fetch new/changed records
- [ ] Develop email/notification alerts for fetch failures or anomalies

Future Development Tasks

### Competition Analysis Enhancement

- [ ] Integrate "number_of_offers_received" data from USAspending.gov for competition intensity analysis
- [ ] Develop visualization for competitive density by agency, NAICS, and contract type
- [ ] Create mathematical pWin model using number of bidders as a key factor
- [ ] Add competition level filter to strategic dashboard sidebar (Low: 1-2, Medium: 3-5, High: 6+)
- [ ] Generate "sweet spot" analysis identifying optimal value-to-competition ratio opportunities
- [ ] Add competition intensity metrics to executive summary dashboard
- [ ] Incorporate competition level insights into Shipley milestone process

### Automated Data Fetch Scheduler

- [ ] Implement scheduled data fetching system to replace manual refresh process
- [ ] Create configurable schedule for different data sources (USAspending, SAM.gov, NATO NSPA)
- [ ] Add logging and notification system for scheduled fetch results
- [ ] Implement retry mechanism for failed fetches with exponential backoff
- [ ] Create admin dashboard for schedule configuration and monitoring
- [ ] Add health check reporting for data source connectivity
- [ ] Implement differential update to only fetch new/changed records
- [ ] Develop email/notification alerts for fetch failures or anomalies

Future Development Tasks

### Competition Analysis Enhancement

- [ ] Integrate "number_of_offers_received" data from USAspending.gov for competition intensity analysis
- [ ] Develop visualization for competitive density by agency, NAICS, and contract type
- [ ] Create mathematical pWin model using number of bidders as a key factor
- [ ] Add competition level filter to strategic dashboard sidebar (Low: 1-2, Medium: 3-5, High: 6+)
- [ ] Generate "sweet spot" analysis identifying optimal value-to-competition ratio opportunities
- [ ] Add competition intensity metrics to executive summary dashboard
- [ ] Incorporate competition level insights into Shipley milestone process

### Automated Data Fetch Scheduler

- [ ] Implement scheduled data fetching system to replace manual refresh process
- [ ] Create configurable schedule for different data sources (USAspending, SAM.gov, NATO NSPA)
- [ ] Add logging and notification system for scheduled fetch results
- [ ] Implement retry mechanism for failed fetches with exponential backoff
- [ ] Create admin dashboard for schedule configuration and monitoring
- [ ] Add health check reporting for data source connectivity
- [ ] Implement differential update to only fetch new/changed records
- [ ] Develop email/notification alerts for fetch failures or anomalies

Future Development Tasks

### Competition Analysis Enhancement

- [ ] Integrate "number_of_offers_received" data from USAspending.gov for competition intensity analysis
- [ ] Develop visualization for competitive density by agency, NAICS, and contract type
- [ ] Create mathematical pWin model using number of bidders as a key factor
- [ ] Add competition level filter to strategic dashboard sidebar (Low: 1-2, Medium: 3-5, High: 6+)
- [ ] Generate "sweet spot" analysis identifying optimal value-to-competition ratio opportunities
- [ ] Add competition intensity metrics to executive summary dashboard
- [ ] Incorporate competition level insights into Shipley milestone process

### Automated Data Fetch Scheduler

- [ ] Implement scheduled data fetching system to replace manual refresh process
- [ ] Create configurable schedule for different data sources (USAspending, SAM.gov, NATO NSPA)
- [ ] Add logging and notification system for scheduled fetch results
- [ ] Implement retry mechanism for failed fetches with exponential backoff
- [ ] Create admin dashboard for schedule configuration and monitoring
- [ ] Add health check reporting for data source connectivity
- [ ] Implement differential update to only fetch new/changed records
- [ ] Develop email/notification alerts for fetch failures or anomalies

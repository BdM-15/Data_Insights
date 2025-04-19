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

## Backlog

- **Develop Model Context Protocol (MCP) Integration**:

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
      - Integrate LLM-based summarization to convert raw web content into actionable intelligence
      - Create custom intelligence digests by topic (customer priorities, competitive moves, market trends)
      - Add document storage for historical analysis and trend identification
      - Implement privacy-preserving measures to ensure compliance with terms of service
      - Build integration with VS Code to enable quick reference during document creation
  - Status: Planned, high priority as these tools will provide the foundation for the Capture Profile feature

- **Implement SAM.gov and SBA SUBNet Integration**:
  - Sub-tasks:
    - **SAM.gov API Integration**:
      - Implement authentication system for SAM.gov API using existing API key
      - Create ETL pipeline to fetch and process current contract opportunities
      - Develop data model to link historical awards with future opportunities
      - Create matching algorithms to identify relevant opportunities based on historical success patterns
      - Implement daily/weekly update system to keep opportunities current
      - Build custom filters for targeted opportunity searches
    - **SBA SUBNet Integration**:
      - Develop crawler for SBA's SUBNet to extract subcontracting opportunities
      - Create data processing pipeline to standardize SUBNet data with our existing schema
      - Implement capability matching to flag relevant subcontracting opportunities
      - Build competitor analysis tools to identify potential teaming partners or competitors from subcontracting data
      - Design visualization components for subcontracting patterns and relationships
    - **Extended Data Source Integration**:
      - Create connectors for commercial data platforms (when available):
        - Develop GovWin IQ API integration for enhanced opportunity tracking
        - Implement Bloomberg Government data integration for market insights
      - Set up pipeline for SBA's Directory of Federal Government Prime Contractors with Subcontracting Plans
      - Develop USASpending.gov API integration focused on subaward data extraction
      - Create unified schema to standardize data across multiple sources
      - Implement data quality checks and deduplication processes
    - **Unified Opportunity Dashboard**:
      - Create integrated view of historical data, SAM.gov opportunities, and SUBNet subcontracting options
      - Develop opportunity scoring system based on historical win data
      - Implement timeline views for upcoming solicitations and proposal deadlines
      - Build notification system for new relevant opportunities
      - Create data visualizations for subcontracting networks and relationships
  - Status: Planned, high priority to enhance business development capabilities with forward-looking opportunity data

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
  - Status: Planned, to be developed after MCP tools are functional, as it represents the end-state deliverable

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

## Milestones

- **Milestone 1: Core Functionality Complete**:
  - ✅ Query and filter data.
  - ✅ Display results in a DataFrame with CSV export.
  - ✅ Render all visualizations correctly in expandable sections.
  - Status: ✅ Completed
- **Milestone 2: MCP Integration and Advanced AI Tools**:
  - Develop and integrate Visualization Tool with the main application
  - Create VS Code integrated Chatbot for award data analysis
  - Build Capability Identifier for competitive analysis
  - Status: Planned, first priority to establish the foundation for advanced features.
- **Milestone 3: Enhanced Capture Profile Generator**:
  - Implement a comprehensive profile generator that leverages all MCP tools
  - Create document generation with AI-assisted narratives and integrated visualizations
  - Build export capabilities for proposal and business development teams
  - Status: Planned, to be developed after MCP tools as the end-state deliverable.
- **Milestone 4: Advanced Features and Optimization**:
  - Add advanced filtering and enhanced visualizations.
  - Optimize performance for large datasets.
  - Status: Planned.

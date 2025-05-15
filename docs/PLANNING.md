# PLANNING.md

## Purpose

The **USAspending.gov Data Explorer** is a Streamlit-based web application designed to help users explore, filter, and visualize government spending data from the USAspending.gov dataset. The app aims to provide actionable insights for business development, competitive analysis, and opportunity identification by allowing users to query contract data, view spending trends, and identify expiring contracts.

## High-Level Vision

- **Data Exploration**: Enable users to filter contract data by dimensions such as date range, agency, contractor, NAICS/PSC codes, contract type, extent competed, and set-aside type.
- **Visual Insights**: Provide visualizations to understand spending trends, identify top recipients/NAICS codes/agencies, and highlight expiring contracts.
- **Capture Profile Generation**: Allow users to select a contract and generate a capture profile (Word document) with details, analysis, visuals, and AI-generated narratives for proposal support.
- **Performance and Usability**: Ensure fast query performance and a clean, intuitive UI with proper formatting and interactivity.
- **No cost and open source**: Ensure we are keeping this effort to a no cost framework.
- **Integrated Data Sources**: Combine historical data (USAspending.gov) with future opportunity data (SAM.gov) and additional sources to support enhanced capture management, providing a comprehensive view of past performance and upcoming opportunities.
- **Comprehensive Capture Management**: Utilize outputs from all AI tools and data sources to create complete, polished Capture Profiles representing the true end state of the system, enabling strategic decision-making and proposal development.

## Architecture

### Updated Modular Architecture

The codebase has been restructured to follow a clean, modular approach with improved organization:

```
Data_Insights/
├── config.py                     # Configuration settings (root level)
├── app.py                        # Main Streamlit application entry point
├── requirements.txt              # Dependencies
├── .env                          # Environment variables (not in git)
├── .env.example                  # Example environment variables
├── data/                         # Data files
├── docs/                         # Documentation
├── logs/                         # Log files
├── tests/                        # Unit tests
└── src/                          # Source code
    ├── backend/                  # Backend functionality
    │   ├── core/                 # Core backend functionality
    │   │   ├── database.py       # Database connection and utilities
    │   │   ├── maintenance.py    # Database maintenance utilities
    │   │   └── utils.py          # Common utilities
    │   ├── data_processing/      # Data processing modules
    │   │   ├── cleansing.py      # Data cleaning functions
    │   │   ├── transformation.py # Data transformation
    │   │   ├── import.py         # Data import utilities
    │   │   └── migration.py      # Database migration utilities
    │   ├── data_acquisition/     # Data acquisition modules
    │   │   ├── sam_gov.py        # SAM.gov API integration
    │   │   ├── nato_nspa.py      # NATO NSPA data acquisition
    │   │   ├── usaspending.py    # USAspending.gov current data
    │   │   └── usaspending_historical.py # USAspending.gov historical data
    │   └── ai/                   # AI integration
    │       └── mcp/              # Model Context Protocol integration
    └── frontend/                 # Frontend UI functionality
        ├── pages/                # Streamlit multipage components
        ├── components/           # Reusable UI components
        ├── visualizations/       # Visualization components
        └── capture/              # Capture management features
```

### Component Architecture

- **Frontend**: Streamlit for the web interface, providing a sidebar for filters, DataFrame displays, and Plotly visualizations. However, open to other suggestions for better performance and user experience.
- **Backend**:
  - PostgreSQL database migrated from the original SQLite (`usaspending_historical.db`) for enhanced performance with large datasets
  - Precomputed tables (`filter_values_*`, `filter_dependencies`) for filter values and dependencies.
  - Pre-aggregated `quarterly_data` table for visualizations.
- **Data Processing**: Pandas for data manipulation, SQLAlchemy for database queries.
- **Visualizations**: Plotly for interactive charts (e.g., line charts, bar charts).
- **AI Integration**: Ollama for local LLM inference to generate capture profile narratives, leveraging the user's GTX 4060 with CUDA.
- **External Data Sources**: API integrations with SAM.gov, SBA's SubNet, GovWin IQ, Bloomberg Government, and potential Salesforce REST API for CRM integration.
- **AI Agent Platform**: Microsoft VSCode Toolkit for Model Context Protocol (MCP) integration to build and deploy local AI tools.

## Constraints

- **Privacy**: All processing must be local to handle private information securely. No external API calls for AI or data processing.
- **Hardware**: The app must run on the user’s system with 64GB RAM, a NVIDIA GTX 4060 GPU, and CUDA installed for local LLM inference.
- **Performance**: Optimize database queries and data loading to handle large datasets and create visuals efficiently. Please feel free to recommend other libraries, UIs, databases, that can be used to increase performance.

## Tech Stack

- **Python Libraries** (as per `requirements.txt`):
  - `streamlit`: For the web interface.
  - `pandas`: For data manipulation.
  - `sqlalchemy`: For database queries.
  - `plotly`: For visualizations.
  - `ollama`: For local LLM inference.
  - `psycopg2-binary`: For PostgreSQL database connectivity.
  - Additional dependencies: `numpy`, `pyarrow`, `python-dateutil`, etc.
- **Database**: PostgreSQL (migrated from SQLite) for improved performance with large datasets.
- **Hardware**: GTX 4060 with CUDA for GPU-accelerated LLM inference.

## Tools

- **Development**: Python 3.x, Visual Studio Code (or similar IDE).
- **Version Control**: Git (repository at `C:\GitHub\Opp_Sem_Search`).
- **AI**: Ollama for local LLM inference, with models like `llama2` or `mistral` for narrative generation.
- **Claude Desktop**: Claude Desktop can be used to assist with natural language processing tasks, such as summarizing large datasets, generating insights, or drafting narratives for the capture profile generation. It complements the local LLM inference by providing an additional layer of AI-driven analysis and content creation.
- **Model Context Protocol**: Plan to incorporate Model Context Protocol (MCP) into the project to enhance advanced data analysis and predictive insights using the Microsoft VSCode Toolkit for local deployment.
- **PydanticAI**: Agent framework for building production-grade AI applications with structured outputs, type safety, and a dependency injection system. Will provide the foundation for all LLM interactions across MCP tools, ensuring consistent, reliable agent behavior.
- **Langfuse**: Open-source LLM engineering platform for observability, prompt management, evals, and analytics for all AI components in the application. Will track performance of all LLM interactions, store version history of prompts, and provide evaluation frameworks.
- **Crawl4AI**: Open-source LLM-friendly web crawler and scraper for the Web Intelligence Scraper tool. Will provide clean markdown generation for RAG pipelines, structured data extraction, and advanced browser control for navigating complex government websites.
- **AI Agent Suite**: Custom-built local AI tools using MCP integration:
  - Web Scraping/Intelligence Gatherer: AI-powered scraping tool to collect relevant contract and agency information
  - Document Creation Agent: AI assistant to create and update multiple document types (Word, Excel, CSV, PowerPoint) based on analyzed data
  - Visualization Tool: AI-enhanced tool for generating insightful visualizations of contract data
  - Analysis and Reasoning Tool: AI agent to perform complex analysis on multi-source government contract data

## Planned Features

- **Strategic Default Dashboard**:

  - Provide automatic strategic-level insights dashboard on app startup
  - Display historical contract data summary and projected spend for next 24-36 months
  - Include interactive visualizations including heatmaps, bar charts, and pie charts for:
    - Top agencies, sub-agencies, and offices by award actions and obligations
    - Top NAICS codes by award actions and obligations
    - Contract vehicles distribution (IDV, single/multiple award) by agency
    - Geographic distribution of contract awards (heatmap)
    - Expiring contracts in the next 6-24 months (timeline view)
    - Projected spend forecast based on historical trends
    - Competitive landscape analysis
    - Small business participation metrics
  - Implement dynamic filtering with real-time visualization updates
  - Add market share analysis for contractors within selected NAICS codes
  - Include opportunity timeline showing contract expirations and projected solicitations

- **Generate Capture Profile**:

  - Allow users to select a row in the DataFrame and generate a Word document ("Capture Profile") with contract details, analysis, and AI-generated narratives (e.g., win strategies for proposals).
  - Use `python-docx` for document generation.
  - Integrate Ollama for local LLM inference, leveraging the user's GTX 4060 with CUDA for performance.
  - Ensure all processing remains local to protect private information.

- **Incorporate Model Context Protocol (MCP)**:

  - Integrate MCP with Microsoft VSCode Toolkit to create and deploy local AI agents
  - Develop intelligence gathering tool for web scraping and data collection
  - Build document creation and updating agent for multiple formats (Word, Excel, CSV, PowerPoint)
  - Create visualization and analytics tools for data-driven insights
  - Implement reasoning tool for strategic analysis of government contract data

- **MCP Tools Integration for Streamlit App**:

  - Create dedicated "AI Tools" tab with multi-tab interface in Streamlit
  - Add conversational AI assistant embedded in the Streamlit sidebar
  - Implement capture profile generation UI with customization options
  - Create web intelligence dashboard for market intelligence gathering
  - Add AI-assisted visualization recommendation engine
  - Implement natural language query-to-visualization converter

- **Implement Shipley Capture Milestone Mapping**:

  - Create data model for Shipley milestone framework (0-3) in the database
  - Develop milestone tracking dashboard with milestone-specific KPIs
  - Implement automated data collection for milestone decision requirements
  - Integrate advanced pricing analysis components:
    - Historical price range analysis
    - Pricing strategy percentile analysis
    - Agency-specific pricing patterns analysis
    - Competitor pricing analysis
    - Price-to-win predictive modeling
  - Design comparison views for competitive assessment at each milestone

- **Create Robust Data Dictionary**:

  - Document all database tables, views, and their relationships
  - Define each data field with descriptions, data types, and business context
  - Map data fields to their source systems and transformation logic
  - Build searchable data dictionary interface within the application
  - Implement data lineage tracking for complex derived fields

- **External Data Source Integration**:

  - **USAspending.gov**: Primary source for historical contract data
  - **SAM.gov API**: Integration for future opportunity data
  - **SBA Mentor-Protégé Agreements**: Partnership data from SBA.gov providing insights on mentor-protégé relationships (https://www.sba.gov/document/support-active-mentor-protege-agreements)
  - **SBA's SubNet**: Integration for subcontracting opportunities
  - **Bureau of Labor Statistics (BLS) API**: Economic data including employment, wages, and price indices to provide market context and economic trends
  - **GovWin IQ API**: Pre-RFP intelligence and teaming partners (requires API key)
  - **Bloomberg Government API**: Financial insights and subcontractor data (requires API key)
  - **Salesforce REST API**: Capture management and CRM functionality integration

- **Admin-Only Data Fetch Interface**:

  - Create admin authentication system using environment variables
  - Build data fetch interface with source selection options
  - Implement progress indicators and status monitoring
  - Add detailed logging and notification system

- **Capture Management Enhancement**:

  - Pipeline building with automatic opportunity feeds into CRM systems
  - Opportunity qualification with scoring models for probability of win
  - Teaming and relationship building through subcontractor identification
  - Competitive analysis with visualization of competitor trends
  - Proposal development with automated extraction of key RFP terms

- **Competition Intensity Analysis**:

  - Create a dedicated "Competition Intensity" dashboard component showing:
    - Average number of bidders by agency, NAICS code, and contract type
    - Visual classification of high, medium, and low competition markets
    - Trend analysis showing changes in competitive density over time
    - "Sweet spot" identification for optimal value-to-competition ratio
    - Correlation between competition levels and contract values
  - Implement competition-based filtering options in the sidebar
  - Develop a mathematical pWin model incorporating number of bidders as a key factor
  - Integrate competition intensity metrics into opportunity qualification scoring
  - Create specialized visualizations showing competitive density across federal market segments

## Potential Improvements

- Add pagination or lazy loading to the DataFrame to handle large datasets more efficiently.
- Enhance visualizations with interactive features (e.g., tooltips, drill-downs).
- Implement additional filters or search capabilities (e.g., keyword search in contract descriptions).
- Optimize database queries further if performance issues arise with larger datasets.

## User Interface Enhancements

### Multipage Application Structure

- **Implement Streamlit Multipage Framework**:

  - Leverage Streamlit's built-in multipage functionality by organizing content into distinct pages
  - Create a dedicated `pages/` directory to house separate Python scripts for each section
  - Support automatic sidebar navigation between application sections
  - Ensure consistent styling and navigation experience across pages

- **Logical Page Organization**:
  - **Home/Dashboard**: Strategic overview dashboard with key metrics and insights
  - **Data Explorer**: Advanced filtering and detailed contract data exploration
  - **Visualizations**: Comprehensive visualization library with interactive elements
  - **Capture Profiles**: Interface for generating and customizing capture profiles
  - **AI Tools**: Access to AI-powered features via Model Context Protocol integration
  - **Admin**: Administrative tools for data refresh and system maintenance (restricted access)

### Tabbed Interface Components

- **Implement Tabbed Content Organization**:

  - Use `st.tabs` to organize related content within each page
  - Apply consistent tab naming and organization patterns across the application
  - Maintain optimal number of tabs per page (3-5) to prevent overwhelming users

- **Strategic Tab Implementation**:
  - **Visualization Tabs**: Separate different visualization types (timelines, charts, maps)
  - **Analysis Tabs**: Group different analytical perspectives (financial, competitive, historical)
  - **Configuration Tabs**: Organize advanced settings and customization options
  - **Results Tabs**: Present query results in different formats (table, summary, dashboard)

### Advanced Streamlit Features

- **Session State Management**:

  - Implement `st.session_state` to persist user selections between interactions
  - Create memory-efficient caching for expensive data operations
  - Enable cross-page data sharing while maintaining clean code separation

- **Interactive Elements**:

  - Add interactive callbacks for dynamic content updates without full page refreshes
  - Implement progressive disclosure patterns for complex functionality
  - Use tooltips and contextual help elements to improve usability

- **Performance Optimizations**:

  - Apply `@st.cache_data` and `@st.cache_resource` decorators for efficient data loading
  - Implement lazy loading patterns for computationally expensive visualizations
  - Optimize layout to minimize recomputation during user interaction

- **Visual Enhancements**:
  - Create custom header and footer components for consistent branding
  - Implement animations for state changes and transitions
  - Use consistent color schemes and visual hierarchy to improve information processing

## Database Optimization

- **Database Migration**:
  - Migrated from SQLite to PostgreSQL for improved performance with large datasets
  - Optimized PostgreSQL configuration for high-performance queries
- **Data Cleansing Optimizations**:
  - Dramatically improved data cleansing performance using direct SQL transformations
  - Reduced processing time from 3.5+ hours to under 12 minutes for 22 million records
  - Achieved processing speeds of ~29,000 rows per second
  - Eliminated Python overhead by performing transformations directly in PostgreSQL
  - Removed 3.6 million duplicate records (16.58% of the original data)
  - Implemented proper type handling and data normalization in a single SQL operation
- **SAM.gov Integration Improvements**:
  - Implemented robust rate limiting with exponential backoff for API requests
  - Added automatic retry mechanism with configurable maximum retries
  - Enhanced error handling for rate limit, connection, and general errors
  - Created detailed logging system with timestamps for troubleshooting
  - Implemented daily request quota tracking to manage API usage limits
  - Added cache invalidation and session refresh mechanisms
  - Successfully enabled fetching of future opportunity data from SAM.gov, a critical step toward our vision of combining historical contract data with upcoming opportunities
  - Established a foundation for the integrated data environment that will power capture management workflows
  - Resolved HTTP 429 "Too Many Requests" errors with intelligent backoff strategy
- **External Data Source Schema Handling Improvements**:
  - Implemented automated schema migration system for external data sources
  - Created dynamic schema detection that identifies new fields in data sources
  - Added ability to automatically evolve database tables when source data formats change
  - Preserved exact field names and formats from original data sources (XML, CSV, JSON)
  - Implemented case-insensitive column matching to prevent field duplication
  - Eliminated need for manual table deletion when data formats change
  - Added automated logging of schema changes for tracking source data evolution
  - Applied to NATO NSPA data source with immediate reliability improvements
  - Prepared foundation for seamless integration of future data sources
- **PostgreSQL Tables**:
  - `usaprime_cleaned`: Main table with contract data
  - `filter_values_*`: Precomputed filter values for each column
  - `filter_dependencies`: Precomputed dependencies between filters (e.g., agency to sub-agency)
  - `quarterly_data`: Pre-aggregated data for visualizations
- **Indexes**:
  - Columns: `action_date`, `period_of_performance_current_end_date`, `modification_number`, `parent_award_agency_name`, `funding_sub_agency_name`, `funding_office_name`, `recipient_name`, `naics_code`, `product_or_service_code`, `type_of_contract_pricing`, `extent_competed`, `type_of_set_aside`
  - Composite index: `idx_filter_composite` on frequently filtered columns
  - PostgreSQL-specific index optimizations (B-tree, GIN) for improved query performance

## Implementation Status

### Completed Features

- ✅ **Application Architecture**: Modular structure with clear separation of concerns
- ✅ **PostgreSQL Integration**: Connection, queries, and data management
- ✅ **Basic UI**: Streamlit interface with filtering and visualization
- ✅ **Dashboard**: Strategic overview with metrics and charts
- ✅ **Tabbed Interface**: Content organization with tabs for different views
- ✅ **Multipage Structure**: Navigation between dedicated application pages

### In Progress

- 🔄 **Advanced Filtering**: Enhanced data filtering capabilities
- 🔄 **Export Functionality**: CSV and Excel export for data tables

### Pending

- ⏱️ **AI Integration**: Local LLM inference with Ollama
- ⏱️ **Capture Profile Generation**: AI-assisted document creation
- ⏱️ **External Data Integration**: SAM.gov and other data sources

## Architecture Updates

### Streamlit Multipage Implementation

The application now follows a modular structure with:

- **Root Level**:

  - `app.py`: Main entry point and home dashboard
  - `config.py`: Centralized configuration management
  - `.env`: Environment-specific configuration

- **Source Code Structure**:
  - `src/backend/core`: Core utilities for database and processing
  - `src/frontend/pages`: Individual page implementations
  - `src/frontend/components`: Reusable UI components
  - `src/frontend/visualizations`: Chart generation functions

### Component Organization

- **Database Layer**: Abstracted through utility functions in `database.py`
- **Configuration**: Environment variables centralized in `config.py`
- **UI Components**: Modular components for filters, charts, and data display
- **Visualization**: Dedicated functions for creating different chart types

## Data Architecture

### Data Sources

- **Primary Data Sources**:

  - **USAspending.gov API**: Historical contract award data
  - **USAspending.gov Bulk Download**: Large-scale historical data

- Complete PostgreSQL database (1.1TB) hosted on port 5433

  - Direct access to all USAspending.gov tables and views
  - Optimized for performance with custom PostgreSQL configuration
  - **SAM.gov API**: Active and future opportunities
  - **NATO NSPA XML Feed**: European procurement opportunities
  - **Small Business Administration (SBA) SubNet**: Subcontracting opportunities
  - **Federal Procurement Data System (FPDS)**: Additional contract data
  - **GovWin IQ API**: Pre-RFP intelligence and teaming opportunities
  - **Bloomberg Government API**: Agency spending trends and legislative tracking
  - **ILOSTAT Database API**: International Labour Organization's central repository of labor statistics for global wage rate analysis
  - **Data.gov Contract-Awarded Labor Category API**: General Services Administration's data on contract-awarded labor categories, rates and qualifications
  - **Bureau of Labor Statistics OEWS API**: Occupational Employment and Wage Statistics providing comprehensive wage data for 800+ occupations across various industries and geographic areas

- **Data Acquisition Mechanisms**:
  - **Manual Fetch Button**: Admin-only interface for on-demand data updates
  - **Automated Fetch Scheduler**: Configurable scheduled data retrieval system
    - Time-based scheduling (daily, weekly, monthly)
    - Differential updates to minimize processing requirements
    - Automated retry with exponential backoff for failed fetches
    - Health check reporting and notification system
    - Source-specific configuration (frequency, scope, credentials)
    - Logging and monitoring dashboard
  - **REST API Connectors**: For real-time data access
  - **Bulk Download Processors**: For large dataset ingestion
  - **Web Scrapers**: For non-API data sources

### Data Storage

- **PostgreSQL Database**: Primary data storage
  - Optimized table structure for federal contracting data
  - Materialized views for common query patterns
  - Indexed search fields for performance
  - Partitioning for large historical datasets
  - Connection pooling for concurrent access

### Database Configuration

The application now uses a dual-database approach:

1. **Main application database** (PostgreSQL, port 5432):

   - Contains cleansed and transformed data
   - Optimized for application performance
   - Stores filter values, dependencies, and materialized views
   - Used for direct application operations

2. **USAspending full database** (PostgreSQL, port 5433):
   - Contains the complete USAspending.gov database
   - Approximately 1.1TB in size
   - Provides access to all original tables and relationships
   - Configured with optimized performance settings:
     - `shared_buffers = 4GB`
     - `work_mem = 512MB`
     - `maintenance_work_mem = 2000MB`
     - `max_parallel_workers_per_gather = 8`
     - `max_parallel_workers = 16`
     - And other performance settings

Both databases can be accessed separately through their respective connection details. The USAspending database provides comprehensive access to the complete federal spending dataset, while the main application database provides optimized performance for the application's specific needs.

Connection details for both databases are stored in the `.env` file. See `docs/DATABASE_SETUP.md` for comprehensive database configuration information.

## Recent Progress: Modularization & AI Integration

- The Streamlit dashboard (`src/frontend/pages/strategic_dashboard.py`) now imports all key data processing functions (`get_quarterly_trends`, `get_award_summary`, `get_top_agencies`) from backend modules only. No local definitions remain, ensuring a single source of truth and improved maintainability.
- Backend data processing is fully modularized, with canonical implementations in `src/backend/data/processors/awards.py` and related modules.
- Modular architecture is enforced across frontend and backend, with clear separation of UI, data processing, and database logic.
- AI integration is underway: local LLM inference via Ollama is functional, and the codebase is structured for future MCP agent integration (web intelligence, document creation, visualization, analysis).

## Next Steps

- Expand MCP agent development for specialized tasks (web scraping, document generation, advanced analytics).
- Begin implementation of the AI-assisted capture profile generator, leveraging local LLMs for narrative and analysis.
- Continue to modularize and document new features as they are added.

## Next Steps

### Short Term

1. Complete the filter implementation in the sidebar
2. Implement the Data Explorer page with advanced filtering
3. Create the Visualizations page with interactive charts

### Medium Term

1. Implement state persistence between pages
2. Add export functionality for all data views
3. Enhance visualizations with interactive features

### Long Term

1. Integrate local LLM inference with Ollama
2. Implement capture profile generation
3. Add external data integration (SAM.gov, etc.)
4. Create AI agents using Model Context Protocol

## AI Integration Strategies

### PydanticAI Implementation Strategy

PydanticAI provides a type-safe agent framework for building production-grade AI applications. The following implementation strategy will ensure successful integration with our Data_Insights project:

#### Phase 1: Core Foundation

1. **Core Domain Models**:

   - Define Pydantic models for key federal contract entities
   - Implement models for awards, agencies, opportunities, and contracts
   - Create validation rules specific to federal contracting data
   - Design specialized validators for monetary values, NAICS codes, and agency identifiers

2. **Simple Analysis Agent**:

   - Build a basic contract analysis agent as proof of concept
   - Connect to Ollama for local LLM inference
   - Implement structured response validation
   - Test with sample contract data queries
   - Measure performance and accuracy metrics

3. **Database Integration**:
   - Implement dependency injection for PostgreSQL database context
   - Create data providers for USAspending database
   - Design caching mechanisms for expensive database operations
   - Build type-safe query result mappers to Pydantic models
   - Implement transaction management for agent operations

#### Phase 2: MCP Tool Integration

4. **Capability Identifier Tool**:

   - Define structured output models for capability identification
   - Implement competitor capability modeling
   - Create gap analysis schema with validated outputs
   - Design structured competitiveness assessment metrics
   - Build win probability estimation models

5. **Document Creator Agent**:

   - Develop document schema models for different output types
   - Implement structured section generators
   - Create validation for narrative sections
   - Design templating system with typed parameters
   - Build export validation for different formats

6. **Web Intelligence Scraper**:

   - Design models for intelligence sources and findings
   - Implement entity detection with validation
   - Create structured intelligence digest schema
   - Build search result validation models
   - Develop models for competitive intelligence analysis

7. **Visualization Tool Enhancement**:
   - Implement chart configuration models
   - Create visualization recommendation schemas
   - Design data validation for visualization inputs
   - Build query-to-visualization converter models
   - Implement annotation and metadata schemas

#### Phase 3: Advanced Features

8. **Agent Composition**:

   - Implement modular agent design with composition patterns
   - Create agent pipelines with validated intermediate outputs
   - Design typed communication protocols between agent components
   - Build testing framework for agent interactions
   - Implement error handling and recovery strategies

9. **Domain-Specific Models**:

   - Create structured models for opportunity qualification
   - Implement capture planning document schemas
   - Design competitive analysis report structures
   - Build price-to-win models with structured components
   - Develop proposal strategy recommendation schemas

10. **Integration with Langfuse**:
    - Implement tracing for structured outputs
    - Create evaluation metrics based on model validation
    - Design test datasets for agent validation
    - Build performance dashboards using structure definitions
    - Implement A/B testing framework for model variants

#### Implementation Guidelines

1. **Start Small**: Begin with core models and a simple agent to test the integration framework
2. **Incremental Adoption**: Gradually incorporate PydanticAI into each MCP tool
3. **Type Safety First**: Leverage Python type hints throughout the implementation
4. **Test-Driven Development**: Create comprehensive tests for all models and agents
5. **Consistent Patterns**: Establish standard patterns for dependency injection and error handling
6. **Documentation**: Document all models and their validation rules for future reference

This implementation strategy aligns with the project's focus on local processing, strong validation, and domain-specific AI capabilities for federal contract analysis.

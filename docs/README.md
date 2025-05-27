# README.md

## USAspending.gov Data Explorer

### Overview

The **USAspending.gov Data Explorer** is a Streamlit-based web application designed to analyze and visualize federal spending data from PostgreSQL (migrated from SQLite for improved performance). The app provides users with the ability to filter, query, and visualize federal contract data, enabling actionable insights for business development and capture management. The ultimate goal is to create comprehensive Capture Profiles that synthesize data from multiple sources and leverage AI tools to support strategic decision-making in federal contracting.

### Features

- **Dynamic Filtering**: Filter contract data by date range, agency, contractor, NAICS/PSC codes, contract type, extent competed, and set-aside type. All filter logic is now centralized in `src/frontend/components/filters.py` for maintainability and robust state management. The Clear Filters button now fully resets the dashboard to its default state.
- **Interactive DataFrame**: Display query results (top 100 rows) with formatted monetary columns and a CSV download option.
- **Visualizations**:
  - Expandable sections for all visualizations, providing a cleaner interface
  - Cumulative spending and award actions by fiscal quarter (correctly aligned with government fiscal year)
  - Contracts expiring between 6 and 24 months
  - Top recipients by total awards made and obligation amount
  - Top NAICS codes by award actions and obligation amount
  - Top funding offices, sub-agencies, and awarding agencies statistics
  - **Consistent, human-readable heatmaps and improved axis labeling**
  - **All charts use THEME colors and formatting from `src/frontend/styles/theme.py`**
- **Projected Awards and Suitability Overlay Chart**: Visualize projected award dates and obligations for all active contracts, with a second line overlay showing the portion realistically winnable by your company based on suitability.
  - _Benefit_: Compare total market opportunity to your company's addressable market, supporting strategic targeting and resource allocation.
- **Similar NAICS Table via LLM Semantic Search**: Table of NAICS codes similar to the one being filtered, powered by LLM-based semantic search on NAICS codes and descriptions.
  - _Benefit_: Discover adjacent or unexplored market areas, expand research, and avoid missing relevant opportunities due to narrow filtering.
- **Interactive Sankey Diagram (Agency → Office → Contract)**: Interactive Sankey diagram tracing the flow from parent agency to office and contract levels.
  - _Benefit_: Intuitive visualization of how obligations and actions flow through the federal hierarchy, helping identify bottlenecks, key offices, and contract concentrations for more effective targeting.
- **Performance Optimizations**: Precomputed filter dependencies, indexed database, and optimized fiscal quarter calculations for faster queries and visualizations. Layout and chart rendering are optimized for large datasets and fast UI response.
- **Integrated Data Sources**: Combine data from USAspending.gov with SAM.gov (including full-text solicitation enrichment as `Document` objects), SBA SubNet, GovWin IQ, and Bloomberg Government for comprehensive insights. Scaffolding for additional connectors is in place.
- **AI-Powered Capture Profiles**: Generate comprehensive capture profiles that synthesize intelligence from multiple sources and AI tools—including enriched SAM.gov solicitations—for strategic decision-making. Scaffolding for local LLM and MCP agent integration is in place.

**May 2025 Update:**

- The GitHub MCP server is now fully integrated as the first MCP tool in the Data_Insights project.
- The integration is managed via Docker and VS Code configuration (`.vscode/mcp.json`), enabling secure, local agent workflows for GitHub data and future AI tools.
- All MCP tool processing is local, with no external API calls for AI/LLM inference, in line with project privacy requirements.
- See `github-mcp-server/Dockerfile` and `.vscode/mcp.json` for implementation details.
- **Full USAspending.gov Database**: Direct access to the complete USAspending.gov database (1.1TB) through a dedicated PostgreSQL instance on port 5433.
- **Modularized UI and Backend**: All business/data logic is in backend modules, and the frontend is UI-only. Layout, filter, and visualization components are fully modular and reusable.
- **Logging and Diagnostics**: File-based logging and robust sidebar diagnostics are implemented for traceability and debugging.

### Project Structure (May 2025)

The project is fully modularized for maintainability, performance, and AI extensibility. All analytics, reporting, and precomputed tables are in the `s3_processed` schema. Below is the current folder structure with key modules and their purposes:

```
Data_Insights/
├── config.py                     # Centralized configuration access for all environment variables and settings
├── app.py                        # Main Streamlit application entry point
├── requirements.txt              # Python dependencies
├── .env                          # Environment variables (not in git)
├── .env.example                  # Example environment variables for setup
├── data/                         # Data files (external, intermediate, or for import)
├── docs/                         # Project documentation (see below for key docs)
├── logs/                         # Log files for diagnostics and traceability
├── tests/                        # Unit tests (mirrors app structure)
└── src/
    ├── backend/
    │   ├── core/
    │   │   ├── database.py           # Database connection management and utilities
    │   │   ├── maintenance.py        # Database maintenance and optimization utilities
    │   │   └── utils.py              # Common backend utility functions
    │   ├── data_processing/
    │   │   ├── cleansing.py          # Data cleaning and normalization logic
    │   │   ├── deduplication.py      # Deduplication of prime and subawards (s2_interim → s3_processed)
    │   │   ├── transformation.py     # Transformation, index creation, and precompute tables (all in s3_processed)
    │   │   ├── import.py             # CSV to database import utilities
    │   │   └── migration.py          # Database migration (SQLite → PostgreSQL)
    │   ├── data_acquisition/
    │   │   ├── sam_gov.py            # SAM.gov API integration for opportunity data
    │   │   ├── nato_nspa.py          # NATO NSPA data acquisition
    │   │   ├── usaspending.py        # USAspending.gov current data acquisition
    │   │   └── usaspending_historical.py # USAspending.gov historical data acquisition
    │   └── ai/
    │       └── mcp/                  # Model Context Protocol (MCP) agent integration and AI tools
    └── frontend/
        ├── pages/                    # Streamlit multipage components (main dashboard, tabs, etc.)
        ├── components/               # Reusable UI components (filters, layout, cards, etc.)
        ├── visualizations/           # Visualization/chart modules (heatmaps, comparison charts, etc.)
        ├── styles/                   # Theme and CSS logic (THEME colors, formatting)
        └── capture/                  # Capture management and profile generation (AI-powered scaffolding)
```

**Key Documentation:**

- `MODULARIZATION_AND_AI_PLAN.md`: Modularization and AI integration roadmap
- `PLANNING.md`: Project vision, architecture, and feature planning
- `DATABASE_SCHEMA.md`: Database schema, table definitions, and best practices
- `CAPTUREINTEL.md`: Capture intelligence workflows and strategies
- `TASKS.md`: Task tracking and milestones
- `strategic_dashboard_implementation.md`: Dashboard design and implementation details

All new features, modularization, and AI scaffolding are documented in the relevant docs (see `MODULARIZATION_AND_AI_PLAN.md`, `PLANNING.md`, `TASKS.md`, and `strategic_dashboard_implementation.md`).

### Module Descriptions

#### Core Application

- **`app.py`**: The main Streamlit application that provides the user interface for filtering, querying, and visualizing federal spending data.
- **`config.py`**: Central configuration file that manages all application settings, API keys, and environment variables.

#### Backend Modules

- **Core Utilities**:

  - **`src/backend/core/database.py`**: Database connection management and common database operations.
  - **`src/backend/core/maintenance.py`**: Database maintenance utilities for optimization and cleanup.
  - **`src/backend/core/utils.py`**: Common utility functions used throughout the application.

- **Data Processing**:

  - **`src/backend/data_processing/cleansing.py`**: Data cleaning and normalization functions.
  - **`src/backend/data_processing/deduplication.py`**: Deduplication of prime awards and subawards, reading from `s2_interim` and writing to `s3_processed`.
  - **`src/backend/data_processing/transformation.py`**: Automated transformation, index creation, and filter/aggregation table generation for analytics and AI, using only `s3_processed` as the source.
  - **`src/backend/data_processing/import.py`**: CSV to database transfer utilities.
  - **`src/backend/data_processing/migration.py`**: Database migration utilities (SQLite to PostgreSQL).

- **Data Acquisition**:

  - **`src/backend/data_acquisition/sam_gov.py`**: SAM.gov API integration for opportunity data.
  - **`src/backend/data_acquisition/nato_nspa.py`**: NATO NSPA data acquisition.
  - **`src/backend/data_acquisition/usaspending.py`**: Current USAspending.gov data acquisition.
  - **`src/backend/data_acquisition/usaspending_historical.py`**: Historical USAspending.gov data acquisition.

- **AI Integration**:
  - **`src/backend/ai/mcp/`**: Model Context Protocol integration for advanced AI capabilities.

#### Frontend Modules

- **`src/frontend/pages/`**: Streamlit multipage components for different application views.
- **`src/frontend/components/`**: Reusable UI components such as filters and tables.
- **`src/frontend/visualizations/`**: Data visualization components and chart generation.
- **`src/frontend/capture/`**: Capture management features including profile generation.

### Supporting Documents

- **`PLANNING.md`**: Outlines the project's purpose, high-level vision, architecture, constraints, and tools.
- **`TASKS.md`**: Lists specific tasks and milestones for the project.
- **`CAPTUREINTEL.md`**: Provides detailed insights and strategies for leveraging federal spending data for business development and capture management.

### Requirements

- **Python Version**: 3.12 or higher
- **Dependencies**: Listed in `requirements.txt`. Install using:
  ```bash
  pip install -r requirements.txt
  ```
- **Databases**:
  - Main Application Database: PostgreSQL database on port 5432 with transformed data
  - USAspending Database: Complete USAspending.gov database on port 5433 (approximately 1.1TB)
- **PostgreSQL**: PostgreSQL 14 or higher must be installed and configured.
- **Hardware**:
  - Minimum 64GB RAM recommended for optimal performance
  - At least 2TB of free disk space for the USAspending database (1.1TB) and working files

### How to Run

1. **Set Up the Environment**:

   - Create a virtual environment:
     ```bash
     python -m venv insight_venv
     ```
   - Activate the virtual environment:
     ```bash
     source insight_venv/bin/activate  # On Windows: insight_venv\Scripts\activate
     ```
   - Install dependencies:
     ```bash
     pip install -r requirements.txt
     ```

2. **Prepare the Databases**:

   - Ensure PostgreSQL is installed and running
   - Configure your database connections in `.env` file (see `.env.example`)
   - For the main application database:
     1. Run the data preparation scripts in the following order:
        - `src/backend/data_processing/migration.py` (if migrating from an existing SQLite database)
        - `src/backend/data_processing/cleansing.py`
        - `src/backend/data_processing/deduplication.py`
        - `src/backend/data_processing/transformation.py`
        - `src/backend/data_processing/import.py` (if importing from CSV files)
   - For the USAspending database:
     1. Download the USAspending bulk data from USAspending.gov
     2. Extract the data to a local directory
     3. Run the restoration script:
        ```bash
        python usaspening_restore_improved.py
        ```
     4. See `docs/DATABASE_SETUP.md` for detailed database setup instructions

3. **Start the Application**:

   - Run the Streamlit app:
     ```bash
     streamlit run app.py
     ```

4. **Access the Application**:
   - Open the provided local URL in your web browser.

### Recent Pipeline & Schema Updates (May 2025)

- **All analytics, reporting, indexes, and precomputed tables (filter values, dependencies, quarterly_data, etc.) are now created exclusively in the `s3_processed` schema.**
  - This ensures a single, high-performance, analytics-ready layer for all downstream use.
- **Source Tables:**
  - `s3_processed.usaspending_prime_awards`: Main deduplicated, analytics-ready contract data table. **All analytics, reporting, and dashboard queries now use this as the sole source for prime award data.**
  - `s3_processed.usaspending_subawards`: Deduplicated subaward data. **All subaward analytics use this table as the source.**
- **Precomputed & Aggregation Tables (all in `s3_processed`):**
  - `filter_values_*`: Precomputed filter values for each column (for fast UI filtering)
  - `filter_dependencies`: Precomputed dependencies between filters
  - `quarterly_data`: Pre-aggregated data for visualizations
  - **All new analytics, reporting, and dashboard tables are created in `s3_processed` only. No analytics or reporting tables are created outside this schema.**
- **Direct SQL Analytics:** All dashboard metrics, aggregations, and calculations are now performed via direct, filter-aware SQL queries (no Pandas-based aggregation in the backend). This ensures maximum performance and leverages database indexes.
- **Materialized Views:** For high-traffic or default dashboard queries (e.g., "Top Competitors by Market Share"), materialized views in `s3_processed` are recommended to provide instant load times. These should be refreshed after each ETL/transform run. For highly dynamic, ad-hoc filters, the index-optimized base tables are sufficient.
- **Indexing:** All recommended indexes are now created in `s3_processed` during the transformation stage, including:
  - Composite indexes for high-frequency filter and grouping columns (e.g., `recipient_parent_name, recipient_name, funding_sub_agency_name` for competitive landscape/treemap)
  - Indexes on `federal_action_obligation`, `modification_number`, `funding_sub_agency_name`, and all major filter columns
  - PostgreSQL-specific index optimizations (B-tree, GIN) for improved query performance

**Summary:** All analytics, reporting, and dashboard queries are now filter-aware, SQL-backed, and index-optimized, using only the `s3_processed` schema as the source. Materialized views are recommended for the most common, high-traffic queries to ensure instant dashboard performance.

**See also:** `docs/DATABASE_SCHEMA.md` for table and field definitions, and `src/backend/data/data_processing/transformation.py` for index/materialized view creation logic.

---

- Consistent error handling and recovery patterns
- Model-agnostic support for Ollama, OpenAI, Anthropic, and other providers
- **LLM Observability**: Langfuse integration for tracking, evaluating, and improving AI component performance:
  - Tracing of all LLM interactions across the application
  - Prompt management system with versioning and templates
  - Custom evaluation metrics for federal contracting domain
  - Test datasets for continuous improvement of AI components
- **Advanced Web Intelligence**: Crawl4AI integration for high-performance web scraping:
  - Clean markdown generation for direct LLM consumption
  - Structured extraction of data from complex websites
  - Advanced browser control for federal procurement sites
  - Parallel crawling for efficient intelligence gathering

### GitHub Copilot Integration

The project includes custom GitHub Copilot tools to enhance development productivity through AI-assisted coding. These tools are designed specifically for the USAspending.gov Data Explorer project and provide domain-specific assistance.

#### Available Custom Tools

1. **Contract Analysis Tool**

   - Purpose: Generate code for analyzing federal contracts from USAspending.gov data
   - Usage: Ask Copilot questions like "How do I analyze contracts by NAICS code?" or "Show me a query to find expiring contracts"
   - Benefit: Provides contract analysis code tailored to the project's data structure

2. **Capture Management Tool**

   - Purpose: Generate code for capture management functionalities (PWin calculations, teaming partner identification)
   - Usage: Ask Copilot questions like "Generate code to calculate probability of win scores" or "How to identify teaming partners from contract data"
   - Benefit: Accelerates development of specialized business development features

3. **PostgreSQL Query Generator**

   - Purpose: Create optimized PostgreSQL queries specific to the USAspending data model
   - Usage: Ask Copilot for "SQL to find top contractors by award amount" or "Query to analyze spending trends by quarter"
   - Benefit: Provides efficient queries tailored to the database structure

4. **Streamlit Visualization Helper**

   - Purpose: Generate Streamlit code for creating interactive visualizations
   - Usage: Ask Copilot to "Create a visualization for contract awards by fiscal quarter" or "Generate code for expandable visualizations"
   - Benefit: Accelerates development of data visualizations with Streamlit and Plotly

5. **MCP Integration Tool**

   - Purpose: Create template code for Model Context Protocol integration
   - Usage: Ask Copilot for "How to integrate MCP with Data Explorer" or "Create a web intelligence scraper template"
   - Benefit: Provides starting points for implementing advanced AI functionalities

6. **Shipley Milestone Framework Helper**

   - Purpose: Generate code for implementing Shipley capture milestone tracking
   - Usage: Ask Copilot to "Create a Shipley milestone tracking dashboard" or "Generate SQL schema for milestone tracking"
   - Benefit: Provides ready-to-use code templates for capture management

7. **Data Pipeline Integration Tool**

   - Purpose: Create ETL pipelines for external data sources
   - Usage: Ask Copilot to "Generate a SAM.gov API integration pipeline" or "Create code to integrate SBA SubNet data"
   - Benefit: Accelerates development of data integration features

8. **Capture Profile Generator Tool**
   - Purpose: Generate code for creating AI-powered capture profiles
   - Usage: Ask Copilot for "How to generate a capture profile with python-docx" or "Create code for AI-generated executive summaries"
   - Benefit: Provides templates for document generation with AI-assisted narratives

#### How to Use the Custom Tools

1. **Setup**: The tools are already configured in the `.copilot` directory at the project root.

2. **Using with GitHub Copilot Chat**:

   - Open VS Code with GitHub Copilot extension installed
   - Open the Copilot Chat panel (Ctrl+Shift+I or via the Copilot icon)
   - Frame your question related to one of the tool domains
   - Copilot will automatically use the appropriate specialized tool to generate more relevant responses

3. **Example Workflow**:

   ```
   User: "How do I create a visualization for top NAICS codes by award amount?"
   Copilot: [Uses streamlit_viz_helper tool to generate specialized Streamlit/Plotly code]
   ```

4. **Implementation Notes**:
   - The tool configurations reference function implementations that need to be created
   - As functions are implemented, the tools will provide increasingly accurate and useful code
   - Until then, the tools will return template code that can be adapted to specific needs

#### Next Steps for Tool Enhancement

- Implement the supporting Python functions referenced by each tool
- Create documentation examples for each tool showing typical usage patterns
- Develop test cases to validate tool functionality with real project data
- Refine tool definitions based on usage feedback and evolving project needs

### Contact

For questions or support, please contact the project maintainer.

#### Data Model Update (May 2025)

**All analytics, reporting, indexes, and precomputed tables are now created exclusively in the `s3_processed` schema.**

- All analytics and reporting use only `s3_processed.usaspending_prime_awards` and `s3_processed.usaspending_subawards` as sources. No legacy or interim tables are referenced.
- All precomputed filter tables, dependencies, and quarterly aggregations are created in `s3_processed` (e.g., `s3_processed.filter_values_*`, `s3_processed.filter_dependencies`, `s3_processed.quarterly_data`).
- No analytics or reporting is performed on `s1_raw` or `s2_interim` tables.
- All dashboard metrics, aggregations, and calculations are now performed via direct, filter-aware SQL queries (no Pandas-based aggregation in the backend). This ensures maximum performance and leverages database indexes.
- Materialized views in `s3_processed` are recommended for the most common, high-traffic queries (e.g., Top Competitors by Market Share) to provide instant dashboard performance. These should be refreshed after each ETL/transform run.
- The architecture is designed for future integration with Model Context Protocol (MCP) agents and local LLMs (Ollama, etc.), enabling advanced analytics, reasoning, and document generation.

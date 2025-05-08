# README.md

## USAspending.gov Data Explorer

### Overview

The **USAspending.gov Data Explorer** is a Streamlit-based web application designed to analyze and visualize federal spending data from PostgreSQL (migrated from SQLite for improved performance). The app provides users with the ability to filter, query, and visualize federal contract data, enabling actionable insights for business development and capture management. The ultimate goal is to create comprehensive Capture Profiles that synthesize data from multiple sources and leverage AI tools to support strategic decision-making in federal contracting.

### Features

- **Dynamic Filtering**: Filter contract data by date range, agency, contractor, NAICS/PSC codes, contract type, extent competed, and set-aside type.
- **Interactive DataFrame**: Display query results (top 100 rows) with formatted monetary columns and a CSV download option.
- **Visualizations**:
  - Expandable sections for all visualizations, providing a cleaner interface
  - Cumulative spending and award actions by fiscal quarter (correctly aligned with government fiscal year)
  - Contracts expiring between 6 and 24 months
  - Top recipients by total awards made and obligation amount
  - Top NAICS codes by award actions and obligation amount
  - Top funding offices, sub-agencies, and awarding agencies statistics
- **Performance Optimizations**: Precomputed filter dependencies, indexed database, and optimized fiscal quarter calculations for faster queries and visualizations.
- **Integrated Data Sources**: Combine data from USAspending.gov with SAM.gov, SBA SubNet, GovWin IQ, and Bloomberg Government for comprehensive insights.
- **AI-Powered Capture Profiles**: Generate comprehensive capture profiles that synthesize intelligence from multiple sources and AI tools to support strategic decision-making.
- **Full USAspending.gov Database**: Direct access to the complete USAspending.gov database (1.1TB) through a dedicated PostgreSQL instance on port 5433.

### Project Structure

The project has been reorganized to follow a modular approach for better code organization and maintainability:

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
  - **`src/backend/data_processing/transformation.py`**: Data transformation and preprocessing for app performance.
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

### Future Enhancements

- **Comprehensive Capture Profile Generation**:
  - Create polished, strategic Capture Profiles that synthesize all AI tool outputs
  - Include executive summaries, competitive positioning, PWin calculations, and strategic recommendations
  - Generate visual aids and proposal support materials automatically
  - Implement ghosting strategies based on competitor intelligence
- **Model Context Protocol (MCP) Integration**:
  - Build AI tools for web intelligence gathering, document creation, visualization, and strategic analysis
  - Integrate all AI capabilities through Microsoft VSCode Toolkit for local deployment
- **Langfuse Observability Integration**:
  - Implement LLM observability framework for all AI components
  - Track and version control prompts for all LLM interactions
  - Create custom evaluation metrics for federal contracting domain
  - Build performance dashboards for AI component quality assessment
  - Develop test datasets and benchmarks for continuous improvement
- **Advanced Web Intelligence with Crawl4AI**:
  - Integrate open-source Crawl4AI for high-performance, LLM-friendly web crawling
  - Generate clean markdown from government websites for direct LLM consumption
  - Implement structured extraction for consistent data formatting across sources
  - Leverage advanced browser control for navigating complex federal websites
  - Enable parallel crawling for faster intelligence collection at scale
  - Create a unified intelligence repository from multiple sources
- **External Data Source Integration**:
  - Connect SAM.gov for future opportunity data
  - Integrate SBA SubNet for subcontracting opportunities
  - Implement GovWin IQ and Bloomberg Government APIs for market intelligence
  - Create Salesforce REST API integration for CRM and capture management
- **Enhanced Capture Management Workflows**:
  - Automate opportunity feeds for pipeline building
  - Develop sophisticated PWin scoring models
  - Create teaming partner identification tools
  - Build automated proposal development support
- **UI/UX Improvements**:
  - Add interactive visualization features
  - Implement advanced filtering options
  - Optimize for large datasets with pagination

### Recent Updates (May 2025)

- **USAspending Database Restoration Complete**:

  - Full 1.1TB USAspending.gov database successfully restored on May 1, 2025
  - All schemas, indexes, and constraints properly created and optimized
  - Database accessible on dedicated PostgreSQL instance on port 5433
  - Performance-optimized configuration enables efficient querying of complex federal spending data
  - See `docs/DATABASE_SETUP.md` for detailed connection information

- **Cross-Environment Compatibility Improvements**:
  - Replaced all Unicode special characters with ASCII-compatible alternatives
  - Standardized symbol usage across dashboards and reports
  - Enhanced compatibility across Windows, Linux, and cloud environments
  - Fixed encoding issues in exported files and visualizations
  - Improved readability and consistent appearance across different platforms

### Model Context Protocol (MCP) Integration in Streamlit

The USAspending.gov Data Explorer will be enhanced with direct integration of Model Context Protocol (MCP) AI tools within the Streamlit interface, providing users with AI-powered analysis capabilities directly in the web application.

#### Planned MCP Features in Streamlit

1. **AI Tools Tab**

   - A dedicated multi-tab interface for AI-powered features
   - Clean, intuitive UI for tool selection and interaction
   - Secure access management for AI capabilities

2. **Integrated Chatbot**

   - Conversational AI assistant embedded in the Streamlit sidebar
   - Context-aware interaction with active filters and selected contract data
   - Specialized prompts for contract analysis and capture intelligence
   - Persistent conversation history for continuing analysis sessions

3. **In-App Capture Profile Generation**

   - One-click capture profile generation from selected contracts
   - Customization options for different capture profile types
   - Real-time progress indicators during document generation
   - Preview capability before download
   - Multiple export formats (DOCX, PDF)

4. **Web Intelligence Dashboard**

   - Integrated search and analysis of market intelligence
   - Entity tracking for agencies, competitors, and technologies
   - Visual mapping of relationships and intelligence findings
   - Automatic digest generation of key intelligence points

5. **AI-Enhanced Visualizations**
   - Natural language queries to generate custom visualizations
   - AI-driven visualization recommendations based on selected data
   - Federal contracting-specific visualization templates
   - Annotation and sharing capabilities for collaborative analysis

#### Implementation Approach

The MCP integration will leverage local AI models through Ollama, ensuring all data processing remains on the user's system with no external API calls. The implementation will utilize the GTX 4060 GPU with CUDA for efficient inference, making sophisticated AI capabilities accessible without compromising data privacy.

### AI Components and Framework

The Data_Insights project incorporates several advanced AI components:

- **Local LLM Integration**: Using Ollama for local LLM inference to generate capture profile narratives, leveraging the user's GTX 4060 with CUDA.
- **AI Agent Framework**: Model Context Protocol (MCP) integration to build local AI tools including web intelligence gathering, document creation, and analysis.
- **PydanticAI Integration**: Structured agent framework for type-safe AI components with validated outputs:
  - Structured response validation using Pydantic models
  - Type-safe dependency injection for AI agent components
  - Domain-specific models for federal contracting
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

# PLANNING.md

## Purpose
The **USAspending.gov Data Explorer** is a Streamlit-based web application designed to help users explore, filter, and visualize government spending data from the USAspending.gov dataset. The app aims to provide actionable insights for business development, competitive analysis, and opportunity identification by allowing users to query contract data, view spending trends, and identify expiring contracts.

## High-Level Vision
- **Data Exploration**: Enable users to filter contract data by dimensions such as date range, agency, contractor, NAICS/PSC codes, contract type, extent competed, and set-aside type.
- **Visual Insights**: Provide visualizations to understand spending trends, identify top recipients/NAICS codes/agencies, and highlight expiring contracts.
- **Capture Profile Generation**: Allow users to select a contract and generate a capture profile (Word document) with details, analysis, and AI-generated narratives for proposal support.
- **Performance and Usability**: Ensure fast query performance and a clean, intuitive UI with proper formatting and interactivity.
- **No cost and open source**: Ensure we are keeping this effort to a no cost framework.

## Architecture
- **Frontend**: Streamlit for the web interface, providing a sidebar for filters, DataFrame displays, and Plotly visualizations.  However, open to other suggestions for better performance and user experience.
- **Backend**:
  - SQLite database (`usaspending_historical.db`) storing the `awards_slim_cleaned` table with contract data.
  - Precomputed tables (`filter_values_*`, `filter_dependencies`) for filter values and dependencies.
  - Pre-aggregated `quarterly_data` table for visualizations.
  - Open to other database
- **Data Processing**: Pandas for data manipulation, SQLAlchemy for database queries.
- **Visualizations**: Plotly for interactive charts (e.g., line charts, bar charts).
- **AI Integration**: Ollama for local LLM inference to generate capture profile narratives, leveraging the user’s GTX 4060 with CUDA.

## Constraints
- **Privacy**: All processing must be local to handle private information securely. No external API calls for AI or data processing.
- **Hardware**: The app must run on the user’s system with 64GB RAM, a NVIDIA GTX 4060 GPU, and CUDA installed for local LLM inference.
- **Performance**: Optimize database queries and data loading to handle large datasets and create visuals efficiently.  Please feel free to recommend other libraries, UIs, databases, that can be used to increase performance.

## Tech Stack
- **Python Libraries** (as per `requirements.txt`):
  - `streamlit`: For the web interface.
  - `pandas`: For data manipulation.
  - `sqlalchemy`: For database queries.
  - `plotly`: For visualizations.
  - `ollama`: For local LLM inference.
  - Additional dependencies: `numpy`, `pyarrow`, `python-dateutil`, etc.
- **Database**: SQLite (`usaspending_historical.db`).
- **Hardware**: GTX 4060 with CUDA for GPU-accelerated LLM inference.

## Tools
- **Development**: Python 3.x, Visual Studio Code (or similar IDE).
- **Version Control**: Git (repository at `C:\GitHub\Opp_Sem_Search`).
- **AI**: Ollama for local LLM inference, with models like `llama2` or `mistral` for narrative generation.
- **Claude Desktop**: Claude Desktop can be used to assist with natural language processing tasks, such as summarizing large datasets, generating insights, or drafting narratives for the capture profile generation. It complements the local LLM inference by providing an additional layer of AI-driven analysis and content creation.
- **Model Context Protocol**: Plan to incorporate Model Context Protocol (MCP) into the project to enhance advanced data analysis and predictive insights. Details of MCP integration are pending user clarification.

## Planned Features
- **Generate Capture Profile**:
  - Allow users to select a row in the DataFrame and generate a Word document ("Capture Profile") with contract details, analysis, and AI-generated narratives (e.g., win strategies for proposals).
  - Use `python-docx` for document generation.
  - Integrate Ollama for local LLM inference, leveraging the user’s GTX 4060 with CUDA for performance.
  - Ensure all processing remains local to protect private information.

- **Incorporate Model Context Protocol (MCP)**:
  - Integrate MCP and AI tools (as discussed previously) to enhance the app’s capabilities, potentially for advanced data analysis or predictive insights.
  - Details of MCP integration are pending user clarification.

## Potential Improvements
- Add pagination or lazy loading to the DataFrame to handle large datasets more efficiently.
- Enhance visualizations with interactive features (e.g., tooltips, drill-downs).
- Implement additional filters or search capabilities (e.g., keyword search in contract descriptions).
- Optimize database queries further if performance issues arise with larger datasets.

## Database Optimization
- **Tables**:
  - `awards_slim_cleaned`: Main table with contract data.
  - `filter_values_*`: Precomputed filter values for each column.
  - `filter_dependencies`: Precomputed dependencies between filters (e.g., agency to sub-agency).
  - `quarterly_data`: Pre-aggregated data for visualizations.
- **Indexes**:
  - Columns: `action_date`, `period_of_performance_current_end_date`, `modification_number`, `parent_award_agency_name`, `funding_sub_agency_name`, `funding_office_name`, `recipient_name`, `naics_code`, `product_or_service_code`, `type_of_contract_pricing`, `extent_competed`, `type_of_set_aside`.
  - Composite index: `idx_filter_composite` on frequently filtered columns.
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

### Scripts and Their Purpose

#### **Core Application**

- **`app.py`**: The main Streamlit application that provides the user interface for filtering, querying, and visualizing federal spending data.

#### **Data Preparation and Transformation**

- **`create_awards_slim_table.py`**: Creates the `awards_slim` table by extracting and transforming relevant data from the source database.
- **`data_transformation.py`**: Cleans and transforms the data in the `awards_slim` table, creating the `awards_slim_cleaned` table. Includes precomputing filter values and aggregating quarterly data for visualizations.
- **`data_cleansing_in_db.py`**: Cleans specific columns in the database, such as replacing blanks with default values and applying title case transformations.
- **`remove_duplicates_db.py`**: Removes duplicate rows from the `awards_slim` table and recreates indexes for optimized performance.

#### **Database Management**

- **`create_sql_indexes.py`**: Creates indexes on frequently filtered columns and a composite index for improved query performance.
- **`db_check.py`**: Provides utilities to inspect the database schema and verify the presence of specific tables or columns.
- **`sqlite_to_postgresql_migration.py`**: Migrates data from SQLite to PostgreSQL for improved performance with large datasets.

#### **Data Loading**

- **`csv_to_db_transfer.py`**: Automates the process of uploading CSV files into the database, handling large datasets in chunks.

#### **Error Handling and Debugging**

- **`review_project_files.py`**: Reads and extracts rules, tasks, and insights from `PLANNING.md`, `TASKS.md`, and `CAPTUREINTEL.md` to ensure alignment with project goals.

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
- **Database**: PostgreSQL database (migrated from SQLite) with preloaded data.
- **PostgreSQL**: PostgreSQL 14 or higher must be installed and configured.

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

2. **Prepare the Database**:

   - Ensure PostgreSQL is installed and running
   - Run the data preparation scripts in the following order:
     1. `sqlite_to_postgresql_migration.py` (if migrating from an existing SQLite database)
     2. `create_awards_slim_table.py`
     3. `data_cleansing_in_db.py`
     4. `remove_duplicates_db.py`
     5. `data_transformation.py`
     6. `create_sql_indexes.py`

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

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

### Contact

For questions or support, please contact the project maintainer.

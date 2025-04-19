# README.md

## USAspending.gov Data Explorer

### Overview

The **USAspending.gov Data Explorer** is a Streamlit-based web application designed to analyze and visualize federal spending data from the `awards_slim_cleaned` table in a PostgreSQL database (migrated from SQLite). The app provides users with the ability to filter, query, and visualize federal contract data, enabling actionable insights for business development and capture management. The ultimate goal is to combine historical contract data with current opportunity data from sources like SAM.gov and SBA's SUBNet to provide a comprehensive view for strategic business development.

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
- **Planned Opportunity Data Integration**: Future integration with SAM.gov API and SBA's SUBNet to combine historical contract data with current opportunities for comprehensive business intelligence.

### Scripts and Their Purpose

#### **Core Application**

- **`app.py`**: The main Streamlit application that provides the user interface for filtering, querying, and visualizing federal spending data.

#### **Data Preparation and Transformation**

- **`data_cleansing.py`**: Cleans and transforms the raw data, creating the `awards_slim_cleaned` table with proper data types and formatting.
- **`data_preprocessing_for_app_performance.py`**: Prepares data for optimal app performance by creating filter values tables, precomputing dependencies, and aggregating data for visualizations.

#### **Database Management**

- **`db_config.py`**: Centralized database configuration that manages connections to PostgreSQL with SQLite fallback.
- **`db_check.py`**: Provides utilities to inspect the database schema and verify the presence of specific tables or columns.

#### **Data Migration**

- **`migrate_to_postgres.py`**: Migrates data from SQLite to PostgreSQL database with proper schema conversion.
- **`simplified_migrate_to_postgres.py`**: Simplified version focusing on migrating just the raw awards table.
- **`reset_postgres_database.py`**: Utility to reset the PostgreSQL database for a clean migration.

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
- **Databases**: 
  - PostgreSQL database for primary storage and query performance
  - SQLite database (`usaspending_historical.db`) as fallback if PostgreSQL is unavailable

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

   - Set up PostgreSQL database (recommended for performance):
     1. Create a PostgreSQL database named 'usaspending'
     2. Run `simplified_migrate_to_postgres.py` to transfer raw data
     3. Run `data_cleansing.py` to clean data in PostgreSQL
     4. Run `data_preprocessing_for_app_performance.py` to create optimized tables
   
   - Alternatively, use the existing SQLite database:
     1. Ensure `usaspending_historical.db` is in the correct location
     2. The application will fall back to SQLite if PostgreSQL is unavailable

3. **Start the Application**:

   - Run the Streamlit app:
     ```bash
     streamlit run app.py
     ```

4. **Access the Application**:
   - Open the provided local URL in your web browser.

### Future Enhancements

- **Opportunity Data Integration**: 
  - Connect to SAM.gov API for live contract opportunities
  - Integrate SBA's SUBNet data for subcontracting opportunities
  - Create unified view of historical and future opportunities
  
- **Capture Profile Generation**: Generate Word documents with contract details and AI-generated narratives.
- **Model Context Protocol (MCP) Integration**: Enhance the app with advanced data analysis and predictive insights.
- **Improved Visualizations**: Add interactive features like tooltips and drill-downs.
- **Pagination**: Implement lazy loading for large datasets.

### Contact

For questions or support, please contact the project maintainer.

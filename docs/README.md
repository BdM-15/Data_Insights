# README.md

## USAspending.gov Data Explorer

### Overview
The **USAspending.gov Data Explorer** is a Streamlit-based web application designed to analyze and visualize federal spending data from the `awards_slim_cleaned` table in a SQLite database. The app provides users with the ability to filter, query, and visualize federal contract data, enabling actionable insights for business development and capture management.

### Features
- **Dynamic Filtering**: Filter contract data by date range, agency, contractor, NAICS/PSC codes, contract type, extent competed, and set-aside type.
- **Interactive DataFrame**: Display query results (top 100 rows) with formatted monetary columns and a CSV download option.
- **Visualizations**:
  - Cumulative spending and award actions by fiscal quarter.
  - Contracts expiring in the next 24 months.
  - Top recipients, NAICS codes, and agencies by award actions and total contract award amount.
- **Performance Optimizations**: Precomputed filter dependencies, indexed database, and pre-aggregated quarterly data for faster queries and visualizations.

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
- **Database**: SQLite database (`usaspending_historical.db`) with preloaded data.

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
   - Run the data preparation scripts in the following order:
     1. `create_awards_slim_table.py`
     2. `data_cleansing_in_db.py`
     3. `remove_duplicates_db.py`
     4. `data_transformation.py`
     5. `create_sql_indexes.py`

3. **Start the Application**:
   - Run the Streamlit app:
     ```bash
     streamlit run app.py
     ```

4. **Access the Application**:
   - Open the provided local URL in your web browser.

### Future Enhancements
- **Capture Profile Generation**: Generate Word documents with contract details and AI-generated narratives.
- **Model Context Protocol (MCP) Integration**: Enhance the app with advanced data analysis and predictive insights.
- **Improved Visualizations**: Add interactive features like tooltips and drill-downs.
- **Pagination**: Implement lazy loading for large datasets.

### Contact
For questions or support, please contact the project maintainer.
# Data Preprocessing for App Performance
# This script handles preprocessing steps to optimize application performance:
# - Creating filter values tables
# - Precomputing dependent filter relationships
# - Pre-aggregating data for visualizations
# - Creating database indexes for query performance

import pandas as pd
from sqlalchemy import create_engine, text
import json
import time
from data_cleansing import cleanse_data

# Connect to the SQLite database
db_path = r'sqlite:///C:\GitHub\Data_Insights\data\usaspending_historical.db?timeout=30'
engine = create_engine(db_path, connect_args={'timeout': 30})

def preprocess_data(df=None):
    """
    Main function to preprocess data for app performance:
    1. Load cleansed data if not provided
    2. Precompute filter values for dropdowns
    3. Precompute dependent filter relationships for cascading filters
    4. Pre-aggregate quarterly data for visualizations
    5. Create database indexes for performance
    """
    start_time = time.time()
    print("Starting data preprocessing for app performance...")
    
    # Step 1: Load cleansed data if not provided
    if df is None:
        print("Loading cleansed data from awards_slim_cleaned table...")
        with engine.connect() as connection:
            df = pd.read_sql_table('awards_slim_cleaned', connection)
    
    # Step 2: Precompute filter values for dropdown menus
    print("Precomputing filter values for dropdowns...")
    
    filter_columns = [
        "parent_award_agency_name", "funding_sub_agency_name", "funding_office_name",
        "recipient_name", "naics_code", "product_or_service_code", "type_of_contract_pricing",
        "extent_competed", "type_of_set_aside"
    ]
    
    with engine.connect() as connection:
        for column in filter_columns:
            if column in df.columns:
                print(f"  - Processing filter values for {column}...")
                unique_values = df[column].dropna().drop_duplicates().sort_values().tolist()
                filter_df = pd.DataFrame(unique_values, columns=["value"])
                table_name = f"filter_values_{column}"
                connection.execute(text(f"DROP TABLE IF EXISTS {table_name}"))
                filter_df.to_sql(table_name, engine, if_exists='replace', index=False)
    
    # Step 3: Precompute dependent filter relationships for cascading filters
    print("Precomputing dependent filter relationships...")
    
    # Parent agency to sub-agency
    parent_to_sub = df[['parent_award_agency_name', 'funding_sub_agency_name']].drop_duplicates().dropna()
    parent_to_sub = parent_to_sub.groupby('parent_award_agency_name')['funding_sub_agency_name'].apply(list).reset_index()
    parent_to_sub.columns = ['parent_value', 'child_values']
    parent_to_sub['child_column'] = 'funding_sub_agency_name'
    
    # Sub-agency to funding office
    sub_to_office = df[['funding_sub_agency_name', 'funding_office_name']].drop_duplicates().dropna()
    sub_to_office = sub_to_office.groupby('funding_sub_agency_name')['funding_office_name'].apply(list).reset_index()
    sub_to_office.columns = ['parent_value', 'child_values']
    sub_to_office['child_column'] = 'funding_office_name'
    
    # Combine into a single table
    filter_dependencies = pd.concat([parent_to_sub, sub_to_office], ignore_index=True)
    
    # Serialize child_values as JSON strings
    filter_dependencies['child_values'] = filter_dependencies['child_values'].apply(json.dumps)
    
    # Save to database
    with engine.connect() as connection:
        connection.execute(text("DROP TABLE IF EXISTS filter_dependencies"))
        filter_dependencies.to_sql('filter_dependencies', engine, if_exists='replace', index=False)
    
    # Step 4: Pre-aggregate data for visualizations
    print("Pre-aggregating data for visualizations...")
    
    # Need to convert action_date to datetime for fiscal calculations
    action_date_dt = pd.to_datetime(df['action_date'], errors='coerce')
    
    # Calculate fiscal year and quarter
    months = action_date_dt.dt.month
    years = action_date_dt.dt.year
    fiscal_years = years + (months >= 10).astype(int)
    fiscal_quarters = pd.cut(
        months,
        bins=[0, 3, 6, 9, 12],
        labels=[2, 3, 4, 1],
        include_lowest=True,
        right=True
    ).astype(int)
    fiscal_quarters = fiscal_quarters.where(months < 10, 1)
    
    df['fiscal_year'] = fiscal_years
    df['fiscal_quarter'] = fiscal_quarters
    df['year_quarter'] = 'FY' + df['fiscal_year'].astype(str) + ' Q' + df['fiscal_quarter'].astype(str)
    
    # Print diagnostic info about the modification number filtering
    print(f"Unique modification_number values: {df['modification_number'].unique().tolist()[:10]} (showing first 10)")
    print(f"Total records: {len(df)}, Records with modification_number='0': {len(df[df['modification_number'] == '0'])}")
    
    # Aggregate quarterly spending and award counts
    quarterly_spending = df.groupby('year_quarter')['federal_action_obligation'].sum().reset_index()
    quarterly_awards = df[df['modification_number'] == '0'].groupby('year_quarter').size().reset_index(name='award_count')
    
    # Merge into a single table
    quarterly_data = quarterly_spending.merge(quarterly_awards, on='year_quarter', how='outer').fillna(0)
    quarterly_data['fiscal_year'] = quarterly_data['year_quarter'].str.extract(r'FY(\d{4})')[0]
    quarterly_data['cumulative_spending'] = quarterly_data.groupby('fiscal_year')['federal_action_obligation'].cumsum()
    quarterly_data['cumulative_awards'] = quarterly_data.groupby('fiscal_year')['award_count'].cumsum()
    
    # Verify correct filtering
    print(f"Total quarterly records: {len(quarterly_data)}")
    print(f"Sum of all award counts: {quarterly_data['award_count'].sum()}")
    print(f"Sum should match records with modification_number='0': {len(df[df['modification_number'] == '0'])}")
    
    # Save to database
    with engine.connect() as connection:
        connection.execute(text("DROP TABLE IF EXISTS quarterly_data"))
        quarterly_data.to_sql('quarterly_data', engine, if_exists='replace', index=False)
    
    # Step 5: Create indexes for better query performance
    print("Creating indexes for better performance...")
    with engine.connect() as connection:
        # Create single-column indexes for commonly filtered columns
        index_columns = [
            "action_date", "period_of_performance_current_end_date", "modification_number",
            "parent_award_agency_name", "funding_sub_agency_name", "funding_office_name",
            "recipient_name", "naics_code", "product_or_service_code", "type_of_contract_pricing",
            "extent_competed", "type_of_set_aside"
        ]
        
        for column in index_columns:
            connection.execute(text(f"CREATE INDEX IF NOT EXISTS idx_{column} ON awards_slim_cleaned ({column})"))
        
        # Create a composite index for frequently combined filters
        connection.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_filter_composite 
            ON awards_slim_cleaned (
                action_date, period_of_performance_current_end_date, 
                parent_award_agency_name, funding_sub_agency_name
            )
        """))
    
    elapsed_time = time.time() - start_time
    print(f"Data preprocessing complete. Elapsed time: {elapsed_time:.2f} seconds.")
    print("Created tables: filter value tables, filter_dependencies, quarterly_data.")
    print("Created indexes on commonly filtered columns for improved query performance.")

if __name__ == "__main__":
    # Option 1: Run the entire pipeline
    # df = cleanse_data()
    # preprocess_data(df)
    
    # Option 2: Only run preprocessing (assumes cleansed data already exists)
    preprocess_data()
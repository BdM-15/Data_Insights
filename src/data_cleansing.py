# Data Cleansing Script
# This script handles data cleansing operations like removing blank columns, 
# removing duplicates, changing datatypes, and modifying column names.

import pandas as pd
from sqlalchemy import create_engine, text
import time
import numpy as np
import sys
import os

# Add parent directory to path to import db_config
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.db_config import get_db_engine

def cleanse_data():
    """
    Main function to cleanse the raw awards data:
    1. Extract data from the awards table
    2. Remove columns that are entirely blank
    3. Remove duplicate rows
    4. Change datatypes (string, numeric, dates)
    5. Clean specific fields like NAICS codes
    6. Output to awards_slim_cleaned table
    """
    start_time = time.time()
    print("Starting data cleansing process...")
    
    # Get database engine from centralized config
    engine = get_db_engine()

    # Step 1: Get all required columns from the raw awards table
    print("Extracting data from awards table...")
    
    # All columns needed from the raw awards table (based on app.py column mapping)
    columns = [
        "action_date_fiscal_year", "action_date", "parent_award_id_piid", "award_id_piid", 
        "modification_number", "federal_action_obligation", "total_dollars_obligated",
        "potential_total_value_of_award", "total_outlayed_amount_for_overall_award",
        "period_of_performance_start_date", "period_of_performance_current_end_date",
        "period_of_performance_potential_end_date", "ordering_period_end_date", 
        "primary_place_of_performance_city_name", "primary_place_of_performance_state_code",
        "prime_award_base_transaction_description", "transaction_description", 
        "naics_code", "naics_description", "product_or_service_code",
        "product_or_service_code_description", "dod_acquisition_program_description",
        "parent_award_agency_name", "awarding_sub_agency_name", "awarding_office_name",
        "funding_agency_name", "funding_sub_agency_name", "funding_office_name",
        "recipient_name", "recipient_uei", "recipient_parent_name", "recipient_parent_uei",
        "solicitation_date", "solicitation_procedures", "extent_competed", "type_of_set_aside",
        "fair_opportunity_limited_sources", "other_than_full_and_open_competition",
        "number_of_offers_received", "subcontracting_plan", "government_furnished_property",
        "type_of_contract_pricing", "action_type", "award_type", "type_of_idc", "idv_type",
        "undefinitized_action", "program_acronym", "multi_year_contract", "multiple_or_single_award_idv",
        "usaspending_permalink"
    ]
    
    # Load data directly from the awards table
    with engine.connect() as connection:
        df = pd.read_sql(text(f"SELECT {', '.join(columns)} FROM awards"), connection)
    
    # Step 2: Remove columns that are entirely blank or null
    print("Removing columns that are entirely blank...")
    before_columns = len(df.columns)
    
    # Calculate the percentage of non-null values in each column
    null_percentages = df.isnull().mean() * 100
    
    # List columns with more than 99% nulls (these will be removed)
    nearly_empty_columns = null_percentages[null_percentages > 99].index.tolist()
    if nearly_empty_columns:
        print(f"Removing the following columns (>99% null): {', '.join(nearly_empty_columns)}")
        df = df.drop(columns=nearly_empty_columns)
    
    print(f"Removed {before_columns - len(df.columns)} entirely blank columns")
    
    # Step 3: Fill missing values for critical columns
    print("Filling missing values for critical columns...")
    
    # Fill missing parent_award_agency_name
    df['parent_award_agency_name'] = df['parent_award_agency_name'].fillna('DEPT OF DEFENSE')
    df.loc[df['parent_award_agency_name'].str.strip() == '', 'parent_award_agency_name'] = 'DEPT OF DEFENSE'
    
    # Step 4: Remove duplicate rows
    print("Removing duplicate rows...")
    before_rows = len(df)
    df = df.drop_duplicates(subset=['award_id_piid', 'modification_number', 'action_date', 
                                     'federal_action_obligation', 'recipient_name'])
    print(f"Removed {before_rows - len(df)} duplicate rows")
    
    # Step 5: Change datatypes
    print("Converting data types...")
    
    # 1. Clean and convert NAICS codes
    df['naics_code'] = df['naics_code'].astype(str).str.replace(r'\.0$', '', regex=True).str.slice(0, 6)
    
    # 2. Convert date columns to datetime and remove timestamps
    date_columns = ['action_date', 'period_of_performance_start_date', 
                   'period_of_performance_current_end_date', 
                   'period_of_performance_potential_end_date',
                   'ordering_period_end_date', 'solicitation_date']
    
    for col in date_columns:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce').dt.date
    
    # 3. Convert monetary columns to numeric
    monetary_columns = ['federal_action_obligation', 'total_dollars_obligated', 
                       'potential_total_value_of_award', 'total_outlayed_amount_for_overall_award']
    
    for col in monetary_columns:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # 4. Convert string columns to uppercase for filtering
    string_columns = [
        "parent_award_agency_name", "funding_sub_agency_name", "funding_office_name",
        "recipient_name", "naics_code", "product_or_service_code", "type_of_contract_pricing",
        "extent_competed", "type_of_set_aside", "awarding_sub_agency_name", "funding_agency_name"
    ]
    
    for col in string_columns:
        if col in df.columns and df[col].dtype == 'object':
            df[col] = df[col].str.upper()
    
    # 5. Convert modification_number to string and strip whitespace (critical for accurate filtering)
    df['modification_number'] = df['modification_number'].astype(str).str.strip()
    
    # Step 6: Output cleansed data to database
    print("Creating awards_slim_cleaned table...")
    with engine.connect() as connection:
        connection.execute(text("DROP TABLE IF EXISTS awards_slim_cleaned"))
        df.to_sql('awards_slim_cleaned', engine, if_exists='replace', index=False)
    
    elapsed_time = time.time() - start_time
    print(f"Data cleansing complete. Elapsed time: {elapsed_time:.2f} seconds.")
    print(f"Cleansed data saved to awards_slim_cleaned table with {len(df)} rows and {len(df.columns)} columns")
    
    return df  # Return the dataframe for use in the preprocessing script if needed

if __name__ == "__main__":
    cleanse_data()
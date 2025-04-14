# clean_data.py
import pandas as pd
from sqlalchemy import create_engine, text
import re

# Connect to the SQLite database
db_path = r'sqlite:///C:\GitHub\Opp_Sem_Search\backend\data\usaspending_historical.db?timeout=30'
engine = create_engine(db_path, connect_args={'timeout': 30})

# Define the columns to select
required_columns = [
    "action_date", "modification_number", "federal_action_obligation", "total_dollars_obligated",
    "period_of_performance_current_end_date", "recipient_name", "naics_code",
    "parent_award_agency_name", "funding_sub_agency_name", "funding_office_name",
    "product_or_service_code", "type_of_contract_pricing", "extent_competed", "type_of_set_aside",
    "parent_award_id_piid", "award_id_piid", "potential_total_value_of_award",
    "primary_place_of_performance_city_name", "primary_place_of_performance_state_code",
    "prime_award_base_transaction_description", "transaction_description", "naics_description",
    "product_or_service_code_description", "awarding_office_name", "recipient_uei",
    "recipient_parent_name", "recipient_parent_uei", "solicitation_date", "solicitation_procedures",
    "fair_opportunity_limited_sources", "other_than_full_and_open_competition",
    "number_of_offers_received", "subcontracting_plan", "government_furnished_property",
    "usaspending_permalink"
]

# Load the data
print("Loading data from awards_slim...")
with engine.connect() as connection:
    df = pd.read_sql(text(f"SELECT {', '.join(required_columns)} FROM awards_slim"), connection)

# Perform cleaning and transformations
print("Cleaning data...")

# 1. Clean NAICS codes
df['naics_code'] = df['naics_code'].astype(str).str.replace(r'\.0$', '', regex=True).str.slice(0, 6)

# 2. Convert date columns to datetime
df['action_date'] = pd.to_datetime(df['action_date'], errors='coerce')
df['period_of_performance_current_end_date'] = pd.to_datetime(df['period_of_performance_current_end_date'], errors='coerce')

# 3. Convert monetary columns to numeric
monetary_columns = ['federal_action_obligation', 'total_dollars_obligated', 'potential_total_value_of_award']
for col in monetary_columns:
    df[col] = pd.to_numeric(df[col], errors='coerce')

# 4. Convert string columns to uppercase for filtering
string_columns = [
    "parent_award_agency_name", "funding_sub_agency_name", "funding_office_name",
    "recipient_name", "naics_code", "product_or_service_code", "type_of_contract_pricing",
    "extent_competed", "type_of_set_aside"
]
for col in string_columns:
    df[col] = df[col].str.upper()

# 5. Drop rows with missing critical columns
# df = df.dropna(subset=['action_date', 'period_of_performance_current_end_date'])

# Create a new table for the cleaned data
print("Creating new table awards_slim_cleaned...")
with engine.connect() as connection:
    # Drop the table if it exists
    connection.execute(text("DROP TABLE IF EXISTS awards_slim_cleaned"))
    # Write the cleaned DataFrame to the new table
    df.to_sql('awards_slim_cleaned', engine, if_exists='replace', index=False)

print("Data cleaning complete. New table awards_slim_cleaned created.")
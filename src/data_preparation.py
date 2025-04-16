# Consolidated Data Preparation Script

from sqlalchemy import create_engine, text
import pandas as pd
import json
import time

# Connect to the SQLite database
db_path = r'sqlite:///C:\GitHub\Opp_Sem_Search\backend\data\usaspending_historical.db?timeout=30'
engine = create_engine(db_path, connect_args={'timeout': 30})

# Step 1: Create or Update awards_slim Table
def create_or_update_awards_slim():
    print("Creating or updating awards_slim table...")
    with engine.connect() as connection:
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS awards_slim AS
            SELECT action_date_fiscal_year, action_date, parent_award_id_piid, award_id_piid, modification_number,
                   federal_action_obligation, total_dollars_obligated, potential_total_value_of_award,
                   total_outlayed_amount_for_overall_award, period_of_performance_start_date,
                   period_of_performance_current_end_date, period_of_performance_potential_end_date,
                   ordering_period_end_date, primary_place_of_performance_city_name,
                   primary_place_of_performance_state_code, prime_award_base_transaction_description,
                   transaction_description, naics_code, naics_description, product_or_service_code,
                   product_or_service_code_description, dod_acquisition_program_description,
                   parent_award_agency_name, awarding_sub_agency_name, awarding_office_name,
                   funding_agency_name, funding_sub_agency_name, funding_office_name,
                   recipient_name, recipient_uei, recipient_parent_name, recipient_parent_uei,
                   solicitation_date, solicitation_procedures, extent_competed, type_of_set_aside,
                   fair_opportunity_limited_sources, other_than_full_and_open_competition,
                   number_of_offers_received, subcontracting_plan, government_furnished_property,
                   type_of_contract_pricing, action_type, award_type, type_of_idc, idv_type,
                   undefinitized_action, program_acronym, multi_year_contract, multiple_or_single_award_idv,
                   usaspending_permalink
            FROM awards;
        """))
    print("awards_slim table created or updated.")

# Step 2: Data Cleansing
def cleanse_data():
    print("Cleansing data in awards_slim table...")
    with engine.connect() as connection:
        connection.execute(text("""
            UPDATE awards_slim
            SET parent_award_agency_name = 'DEPT OF DEFENSE'
            WHERE parent_award_agency_name IS NULL OR TRIM(parent_award_agency_name) = '';
        """))
    print("Data cleansing completed.")

# Step 3: Data Transformation
def transform_data():
    print("Transforming data in awards_slim table...")
    with engine.connect() as connection:
        df = pd.read_sql(text("SELECT * FROM awards_slim"), connection)
        df['naics_code'] = df['naics_code'].astype(str).str.replace(r'\.0$', '', regex=True).str.slice(0, 6)
        df['action_date'] = pd.to_datetime(df['action_date'], errors='coerce').dt.date
        df.to_sql('awards_slim_cleaned', engine, if_exists='replace', index=False)
    print("Data transformation completed.")

# Execute all steps
if __name__ == "__main__":
    create_or_update_awards_slim()
    cleanse_data()
    transform_data()

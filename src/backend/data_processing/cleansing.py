# Data Cleansing Script - High Performance Edition
# Optimized for fast PostgreSQL data transfer on powerful systems

import pandas as pd
from sqlalchemy import create_engine, text
import time
import numpy as np
import os
import psycopg2
from dotenv import load_dotenv
import multiprocessing
import sys

# Load environment variables from .env file
load_dotenv()

# Get PostgreSQL connection details from environment variables
pg_user = os.getenv('PG_USER')
pg_password = os.getenv('PG_PASSWORD')
pg_host = os.getenv('PG_HOST')
pg_port = os.getenv('PG_PORT')
pg_dbname = os.getenv('PG_DBNAME')

# Basic engine for setup and queries
db_url = f"postgresql://{pg_user}:{pg_password}@{pg_host}:{pg_port}/{pg_dbname}"
engine = create_engine(db_url, echo=False)

def cleanse_data(force_rebuild=True):
    """
    Main function to cleanse the raw awards data with significantly improved performance.
    Optimized for 64GB RAM and NVIDIA GTX 4060 GPU hardware on Windows platform.
    
    Parameters:
    -----------
    force_rebuild : bool, default=True
        If True, drops and recreates the usaprime_cleaned table if it exists.
    """
    start_time = time.time()
    print("Starting high-performance data cleansing process...")
    
    # Display system info
    cpu_count = multiprocessing.cpu_count()
    print(f"System has {cpu_count} CPU cores available")
    print(f"Using optimized PostgreSQL direct SQL transformation")
    
    # Check if destination table already exists and handle accordingly
    with engine.connect() as connection:
        table_exists_query = text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'usaprime_cleaned'
            )
        """)
        destination_exists = connection.execute(table_exists_query).scalar()
        
        if destination_exists:
            if force_rebuild:
                print("\nWARNING: usaprime_cleaned table already exists and will be dropped and recreated.")
                print("All existing data in usaprime_cleaned will be lost.")
                print("Processing will continue in 5 seconds...\n")
                time.sleep(5)
                # Explicitly drop the table with CASCADE to ensure it's removed
                try:
                    connection.execute(text("DROP TABLE IF EXISTS usaprime_cleaned CASCADE"))
                    connection.commit()
                    print("Successfully dropped usaprime_cleaned table.")
                except Exception as e:
                    print(f"Error dropping table: {e}")
                    raise
            else:
                print("usaprime_cleaned table already exists. Exiting to prevent data loss.")
                return False
    
    try:
        # Create destination table with optimized structure
        print("Creating optimized usaprime_cleaned table structure...")
        with engine.connect() as connection:
            # Verify source table exists
            table_check_query = text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'usaspending_prime_awards'
                )
            """)
            source_exists = connection.execute(table_check_query).scalar()
            
            if not source_exists:
                raise Exception("Error: usaspending_prime_awards table does not exist")
            
            # Get exact row count from source table
            count_query = text("SELECT COUNT(*) FROM usaspending_prime_awards")
            source_row_count = connection.execute(count_query).scalar()
            print(f"Source table contains {source_row_count:,} rows")
            
            # Create optimized destination table with SQL
            create_table_query = text("""
                CREATE TABLE usaprime_cleaned (
                    action_date_fiscal_year TEXT,
                    action_date DATE,
                    parent_award_id_piid TEXT,
                    award_id_piid TEXT,
                    modification_number TEXT,
                    federal_action_obligation NUMERIC,
                    total_dollars_obligated NUMERIC,
                    potential_total_value_of_award NUMERIC,
                    total_outlayed_amount_for_overall_award NUMERIC,
                    period_of_performance_start_date DATE,
                    period_of_performance_current_end_date DATE,
                    period_of_performance_potential_end_date DATE,
                    ordering_period_end_date DATE,
                    primary_place_of_performance_city_name TEXT,
                    primary_place_of_performance_state_code TEXT,
                    prime_award_base_transaction_description TEXT,
                    transaction_description TEXT,
                    naics_code TEXT,
                    naics_description TEXT,
                    product_or_service_code TEXT,
                    product_or_service_code_description TEXT,
                    dod_acquisition_program_description TEXT,
                    parent_award_agency_name TEXT,
                    awarding_sub_agency_name TEXT,
                    awarding_office_name TEXT,
                    funding_agency_name TEXT,
                    funding_sub_agency_name TEXT,
                    funding_office_name TEXT,
                    recipient_name TEXT,
                    recipient_uei TEXT,
                    recipient_parent_name TEXT,
                    recipient_parent_uei TEXT,
                    solicitation_date DATE,
                    solicitation_procedures TEXT,
                    extent_competed TEXT,
                    type_of_set_aside TEXT,
                    fair_opportunity_limited_sources TEXT,
                    other_than_full_and_open_competition TEXT,
                    number_of_offers_received INTEGER,
                    subcontracting_plan TEXT,
                    government_furnished_property TEXT,
                    type_of_contract_pricing TEXT,
                    action_type TEXT,
                    award_type TEXT,
                    type_of_idc TEXT,
                    idv_type TEXT,
                    undefinitized_action TEXT,
                    multi_year_contract TEXT,
                    multiple_or_single_award_idv TEXT,
                    usaspending_permalink TEXT
                );
            """)
            connection.execute(create_table_query)
            connection.commit()
        
        # Use direct SQL transformation for optimal performance
        print("\nPerforming direct SQL transformation and data cleansing...")
        
        # Execute the single, optimized SQL statement that does all the work
        with engine.connect() as connection:
            # Set performance optimization parameters for Windows platform with 64GB RAM
            # Reason: Only use parameters that can be changed during runtime in PostgreSQL on Windows
            connection.execute(text("SET synchronous_commit = OFF"))
            connection.execute(text("SET work_mem = '2047MB'"))  # Max allowed ~2GB (2097151 KB)
            connection.execute(text("SET maintenance_work_mem = '2047MB'"))  # Max allowed ~2GB
            connection.execute(text("SET max_parallel_workers_per_gather = 4"))  # Use multiple cores
            connection.execute(text("SET max_parallel_workers = 8"))  # Set max workers based on CPU cores
            connection.execute(text("SET random_page_cost = 1.1"))  # Assume fast SSD storage
            connection.execute(text("SET cpu_tuple_cost = 0.03"))  # Lower for modern CPUs
            
            print("Starting data transformation (this may take some time)...")
            transform_start = time.time()
            
            # Modified SQL transformation - REMOVED deduplication logic to preserve all raw data
            # Reason: Preserving all raw data until deduplication strategy is confirmed
            transform_sql = text("""
                INSERT INTO usaprime_cleaned
                SELECT 
                    action_date_fiscal_year::text,
                    action_date::date,
                    parent_award_id_piid,
                    award_id_piid,
                    -- Standardize modification_number for consistent award counting
                    -- Only basic standardization to ensure empty values become '0'
                    CASE 
                        WHEN modification_number IS NULL THEN '0'
                        WHEN TRIM(modification_number::text) = '' THEN '0'
                        ELSE TRIM(modification_number::text)
                    END,
                    federal_action_obligation::numeric,
                    total_dollars_obligated::numeric,
                    potential_total_value_of_award::numeric,
                    total_outlayed_amount_for_overall_award::numeric,
                    period_of_performance_start_date::date,
                    period_of_performance_current_end_date::date,
                    period_of_performance_potential_end_date::date,
                    ordering_period_end_date::date,
                    primary_place_of_performance_city_name,
                    primary_place_of_performance_state_code,
                    prime_award_base_transaction_description,
                    transaction_description,
                    SUBSTRING(REGEXP_REPLACE(naics_code::text, '\\.0$', ''), 1, 6),
                    naics_description,
                    product_or_service_code,
                    product_or_service_code_description,
                    dod_acquisition_program_description,
                    COALESCE(UPPER(NULLIF(TRIM(parent_award_agency_name), '')), 'DEPT OF DEFENSE'),
                    UPPER(awarding_sub_agency_name),
                    UPPER(awarding_office_name),
                    UPPER(funding_agency_name),
                    UPPER(funding_sub_agency_name),
                    UPPER(funding_office_name),
                    UPPER(recipient_name),
                    recipient_uei,
                    UPPER(recipient_parent_name),
                    recipient_parent_uei,
                    solicitation_date::date,
                    solicitation_procedures,
                    UPPER(extent_competed),
                    UPPER(type_of_set_aside),
                    fair_opportunity_limited_sources,
                    other_than_full_and_open_competition,
                    CASE 
                        WHEN number_of_offers_received ~ '^[0-9]+(\\.0+)?$' THEN CAST(REGEXP_REPLACE(number_of_offers_received, '\\.0+$', '') AS INTEGER)
                        ELSE NULL
                    END,
                    subcontracting_plan,
                    government_furnished_property,
                    UPPER(type_of_contract_pricing),
                    action_type,
                    award_type,
                    type_of_idc,
                    idv_type,
                    undefinitized_action,
                    multi_year_contract,
                    multiple_or_single_award_idv,
                    usaspending_permalink
                FROM usaspending_prime_awards
            """)
            
            try:
                # Execute transformation
                result = connection.execute(transform_sql)
                connection.commit()
                transform_end = time.time()
                transform_duration = transform_end - transform_start
                
                # Get count of processed rows
                count_query = text("SELECT COUNT(*) FROM usaprime_cleaned")
                processed_rows = connection.execute(count_query).scalar()
                
                # Calculate time stats
                minutes = int(transform_duration // 60)
                seconds = int(transform_duration % 60)
                rows_per_second = processed_rows / transform_duration if transform_duration > 0 else 0
                
                print(f"Transformation complete in {minutes}m {seconds}s")
                print(f"Processed {processed_rows:,} rows")
                print(f"Processing speed: {rows_per_second:.2f} rows/second")
                
                # Note about preserved rows
                print(f"All {source_row_count:,} source rows preserved in the transformation")
                
                # Optimize indexing for query performance
                print("\nCreating optimized indexes for query performance...")
                
                # Create index on modification_number for efficient base award filtering
                connection.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_modification_number 
                    ON usaprime_cleaned(modification_number);
                """))
                print("✓ Created index on modification_number")
                
                # Create index on award_id_piid for efficient joins
                connection.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_award_id_piid 
                    ON usaprime_cleaned(award_id_piid);
                """))
                print("✓ Created index on award_id_piid")
                
                # Create index on action_date for time-based queries
                connection.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_action_date 
                    ON usaprime_cleaned(action_date);
                """))
                print("✓ Created index on action_date")
                
                # Create index on recipient_name for competitor analysis
                connection.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_recipient_name 
                    ON usaprime_cleaned(recipient_name);
                """))
                print("✓ Created index on recipient_name")
                
                # Create index on naics_code for filtering
                connection.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_naics_code 
                    ON usaprime_cleaned(naics_code);
                """))
                print("✓ Created index on naics_code")
                
                # Create composite index for common query patterns
                connection.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_agency_fiscal_year 
                    ON usaprime_cleaned(parent_award_agency_name, action_date_fiscal_year);
                """))
                print("✓ Created composite index on parent_award_agency_name and action_date_fiscal_year")
                
                # Analyze table for query optimization
                print("\nAnalyzing table for query optimization...")
                connection.execute(text("ANALYZE usaprime_cleaned"))
                connection.commit()
                
            except Exception as e:
                print(f"Error during transformation: {str(e)}")
                raise
        
    except Exception as e:
        print(f"\nERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    elapsed_time = time.time() - start_time
    hours = int(elapsed_time // 3600)
    minutes = int((elapsed_time % 3600) // 60)
    seconds = int(elapsed_time % 60)
    
    print(f"\nData cleansing complete!")
    print(f"Total elapsed time: {hours}h {minutes}m {seconds}s")
    print(f"Processed {processed_rows:,} records")
    print(f"Average processing speed: {processed_rows/elapsed_time:.2f} rows/second")
    print(f"\nIMPORTANT: Run data_preprocessing_for_app_performance.py next to create filter tables")
    
    return True

if __name__ == "__main__":
    print(f"Python version: {sys.version}")
    print(f"Pandas version: {pd.__version__}")
    print(f"Starting data cleansing process with direct SQL transformation...")
    
    cleanse_data()
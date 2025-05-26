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
import logging

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

# Set up logging
logger = logging.getLogger(__name__)

def cleanse_data(force_rebuild=True):
    """
    Main function to cleanse the raw awards data with significantly improved performance.
    Creates a clean dataset while preserving all raw data records.
    Uses contract_transaction_unique_key as the PRIMARY KEY.
    Optimized for 64GB RAM and NVIDIA GTX 4060 GPU hardware on Windows platform.
    
    Parameters:
    -----------
    force_rebuild : bool, default=True
        If True, drops and recreates the usaprime_cleaned table if it exists.
        
    Returns:
    --------
    bool
        True if cleansing was successful, False otherwise.
    """
    start_time = time.time()
    logger.info("Starting high-performance data cleansing process...")
    
    # Display system info
    cpu_count = multiprocessing.cpu_count()
    logger.info(f"System has {cpu_count} CPU cores available")
    logger.info(f"Using optimized PostgreSQL direct SQL transformation")
    
    # Check if destination table already exists and handle accordingly
    with engine.connect() as connection:
        table_exists_query = text(f"""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 's2_interim' AND table_name = 'usaspending_prime_awards'
            )
        """)
        destination_exists = connection.execute(table_exists_query).scalar()
        if destination_exists:
            if force_rebuild:
                logger.warning(f"\nWARNING: s2_interim.usaspending_prime_awards table already exists and will be dropped and recreated.")
                logger.warning("All existing data in s2_interim.usaspending_prime_awards will be lost.")
                logger.warning("Processing will continue in 5 seconds...\n")
                time.sleep(5)
                try:
                    connection.execute(text("DROP TABLE IF EXISTS s2_interim.usaspending_prime_awards CASCADE"))
                    connection.commit()
                    logger.info("Successfully dropped s2_interim.usaspending_prime_awards table.")
                except Exception as e:
                    logger.error(f"Error dropping table: {e}")
                    raise
            else:
                logger.info("s2_interim.usaspending_prime_awards table already exists. Exiting to prevent data loss.")
                return False
    
    try:
        # --- PRIME AWARDS CLEANSING ---
        PRIME_SRC = "s1_raw.usaspending_prime_awards_slim"
        PRIME_DEST = "s2_interim.usaspending_prime_awards"

        logger.info(f"Creating optimized {PRIME_DEST} table structure...")
        with engine.connect() as connection:
            # Verify source table exists
            table_check_query = text(
                f"SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_schema = 's1_raw' AND table_name = 'usaspending_prime_awards_slim');"
            )
            source_exists = connection.execute(table_check_query).scalar()
            if not source_exists:
                raise Exception(f"Error: {PRIME_SRC} table does not exist")

            # Check if the unique keys exist in the source table
            # Reason: Check for contract_transaction_unique_key in s1_raw.usaspending_prime_awards_slim
            column_check_query = text(
                "SELECT COUNT(*) FROM information_schema.columns WHERE table_schema = 's1_raw' AND table_name = 'usaspending_prime_awards_slim' AND column_name = 'contract_transaction_unique_key';"
            )
            has_unique_key = connection.execute(column_check_query).scalar() > 0
            if not has_unique_key:
                logger.warning("WARNING: contract_transaction_unique_key not found in source table!")
                logger.warning("This column is required as it will be used as the PRIMARY KEY.")
                logger.warning("Please ensure your raw data includes this column.")
                raise Exception("Missing required contract_transaction_unique_key column in source table")

            # Get exact row count and key stats from source table
            count_query = text(f"SELECT COUNT(*) FROM {PRIME_SRC};")
            source_row_count = connection.execute(count_query).scalar()
            logger.info(f"Source table contains {source_row_count:,} rows")

            # Check for duplicates on contract_transaction_unique_key and NULL values
            key_check_query = text(
                "SELECT COUNT(*) - COUNT(DISTINCT contract_transaction_unique_key) AS duplicate_count, "
                "COUNT(DISTINCT contract_transaction_unique_key) AS unique_keys, "
                "COUNT(*) FILTER (WHERE contract_transaction_unique_key IS NULL) AS null_keys "
                f"FROM {PRIME_SRC};"
            )
            result = connection.execute(key_check_query).fetchone()
            duplicate_count, unique_key_count, null_key_count = result[0], result[1], result[2]
            if duplicate_count > 0:
                logger.warning(f"Found {duplicate_count:,} duplicate transaction keys in source data")
                logger.warning(f"Source contains {unique_key_count:,} unique transaction keys out of {source_row_count:,} total rows")
            if null_key_count > 0:
                logger.warning(f"Found {null_key_count:,} rows with NULL transaction keys")
                logger.warning("These rows will be preserved but may cause issues with PRIMARY KEY constraint")

            # Create optimized destination table with SQL - using contract_transaction_unique_key as PRIMARY KEY
            create_table_query = text(f"""                
                CREATE TABLE {PRIME_DEST} (
                    contract_transaction_unique_key TEXT PRIMARY KEY,
                    contract_award_unique_key TEXT,
                    action_date_fiscal_year TEXT,
                    action_date_fiscal_quarter INTEGER,
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
        logger.info(f"\nPerforming direct SQL transformation and data cleansing for {PRIME_SRC}...")

        # --- MAIN CLEANSING SQL ---
        with engine.connect() as connection:
            # Set performance optimization parameters for Windows platform with 64GB RAM
            connection.execute(text("SET synchronous_commit = OFF;"))
            connection.execute(text("SET work_mem = '2047MB';"))
            connection.execute(text("SET maintenance_work_mem = '2047MB';"))
            connection.execute(text("SET max_parallel_workers_per_gather = 4;"))
            connection.execute(text("SET max_parallel_workers = 8;"))
            connection.execute(text("SET random_page_cost = 1.1;"))
            connection.execute(text("SET cpu_tuple_cost = 0.03;"))

            logger.info("Starting data transformation (this may take some time)...")
            transform_start = time.time()

            # --- CLEANSING LOGIC ---
            # Reason: Standardize type_of_set_aside, apply rules for extent_competed/type_of_set_aside
            transform_sql = text(rf"""
                INSERT INTO {PRIME_DEST}                SELECT DISTINCT ON (contract_transaction_unique_key)
                    contract_transaction_unique_key,
                    contract_award_unique_key,
                    action_date_fiscal_year::text,
                    -- Calculate fiscal quarter from action_date (supports quarterly trend analysis and strategic dashboard performance)
                    -- US Federal fiscal year quarters: Q1 (Oct-Dec), Q2 (Jan-Mar), Q3 (Apr-Jun), Q4 (Jul-Sep)
                    CASE 
                        WHEN EXTRACT(MONTH FROM action_date) IN (10, 11, 12) THEN 1
                        WHEN EXTRACT(MONTH FROM action_date) IN (1, 2, 3) THEN 2
                        WHEN EXTRACT(MONTH FROM action_date) IN (4, 5, 6) THEN 3
                        WHEN EXTRACT(MONTH FROM action_date) IN (7, 8, 9) THEN 4
                        ELSE NULL
                    END AS action_date_fiscal_quarter,
                    action_date::date,
                    parent_award_id_piid,
                    award_id_piid,
                    CASE WHEN modification_number IS NULL THEN '0'
                         WHEN TRIM(modification_number::text) = '' THEN '0'
                         ELSE TRIM(modification_number::text) END AS modification_number,
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
                    SUBSTRING(REGEXP_REPLACE(naics_code::text, '\.0$', ''), 1, 6) AS naics_code,
                    naics_description,
                    product_or_service_code,
                    product_or_service_code_description,
                    dod_acquisition_program_description,
                    COALESCE(NULLIF(TRIM(parent_award_agency_name), ''), 'DEPT OF DEFENSE') AS parent_award_agency_name,
                    UPPER(awarding_sub_agency_name) AS awarding_sub_agency_name,
                    UPPER(awarding_office_name) AS awarding_office_name,
                    UPPER(funding_agency_name) AS funding_agency_name,
                    UPPER(funding_sub_agency_name) AS funding_sub_agency_name,
                    UPPER(funding_office_name) AS funding_office_name,
                    UPPER(recipient_name) AS recipient_name,
                    recipient_uei,
                    UPPER(recipient_parent_name) AS recipient_parent_name,
                    recipient_parent_uei,
                    solicitation_date::date,
                    solicitation_procedures,
                    UPPER(extent_competed) AS extent_competed,
                    CASE
                        WHEN type_of_set_aside ILIKE 'NO SET ASIDE USED.' THEN 'NO SET ASIDE USED'
                        WHEN UPPER(extent_competed) = 'FULL AND OPEN COMPETITION' THEN 'NO SET ASIDE USED'
                        WHEN UPPER(extent_competed) = 'FULL AND OPEN COMPETITION AFTER EXCLUSION OF SOURCES' AND (UPPER(type_of_set_aside) = 'NO SET ASIDE USED' OR UPPER(type_of_set_aside) = 'NO SET ASIDE USED.') THEN NULL
                        ELSE UPPER(type_of_set_aside)
                    END AS type_of_set_aside,
                    fair_opportunity_limited_sources,
                    other_than_full_and_open_competition,
                    CASE WHEN number_of_offers_received ~ '^[0-9]+(\.0+)?$' THEN CAST(REGEXP_REPLACE(number_of_offers_received, '\.0+$', '') AS INTEGER) ELSE NULL END AS number_of_offers_received,
                    subcontracting_plan,
                    government_furnished_property,
                    UPPER(type_of_contract_pricing) AS type_of_contract_pricing,
                    action_type,
                    award_type,
                    type_of_idc,
                    idv_type,
                    undefinitized_action,
                    multi_year_contract,
                    multiple_or_single_award_idv,
                    usaspending_permalink
                FROM {PRIME_SRC}
                WHERE contract_transaction_unique_key IS NOT NULL
                ORDER BY contract_transaction_unique_key, action_date DESC;
            """)
            connection.execute(transform_sql)
            connection.commit()

            # Handle NULL transaction keys (if any)
            if null_key_count > 0:
                logger.warning(f"Handling {null_key_count} rows with NULL transaction keys...")
                connection.execute(text(f"""
                    CREATE TEMP TABLE null_key_records AS SELECT * FROM {PRIME_SRC} WHERE contract_transaction_unique_key IS NULL;
                """))
                connection.execute(text("ALTER TABLE null_key_records ADD COLUMN temp_id SERIAL;"))
                null_records_sql = text(rf"""
                    INSERT INTO {PRIME_DEST}
                    SELECT 
                        'GENERATED_KEY_' || temp_id::text AS contract_transaction_unique_key,
                        contract_award_unique_key,
                        action_date_fiscal_year::text,
                        action_date::date,
                        parent_award_id_piid,
                        award_id_piid,
                        CASE 
                            WHEN modification_number IS NULL THEN '0'
                            WHEN TRIM(modification_number::text) = '' THEN '0'
                            ELSE TRIM(modification_number::text)
                        END AS modification_number,
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
                        SUBSTRING(REGEXP_REPLACE(naics_code::text, '\.0$', ''), 1, 6) AS naics_code,
                        naics_description,
                        product_or_service_code,
                        product_or_service_code_description,
                        dod_acquisition_program_description,
                        COALESCE(NULLIF(TRIM(parent_award_agency_name), ''), 'DEPT OF DEFENSE') AS parent_award_agency_name,
                        UPPER(awarding_sub_agency_name) AS awarding_sub_agency_name,
                        UPPER(awarding_office_name) AS awarding_office_name,
                        UPPER(funding_agency_name) AS funding_agency_name,
                        UPPER(funding_sub_agency_name) AS funding_sub_agency_name,
                        UPPER(funding_office_name) AS funding_office_name,
                        UPPER(recipient_name) AS recipient_name,
                        recipient_uei,
                        UPPER(recipient_parent_name) AS recipient_parent_name,
                        recipient_parent_uei,
                        solicitation_date::date,
                        solicitation_procedures,
                        UPPER(extent_competed) AS extent_competed,
                        CASE
                            WHEN type_of_set_aside ILIKE 'NO SET ASIDE USED.' THEN 'NO SET ASIDE USED'
                            WHEN UPPER(extent_competed) = 'FULL AND OPEN COMPETITION' THEN 'NO SET ASIDE USED'
                            WHEN UPPER(extent_competed) = 'FULL AND OPEN COMPETITION AFTER EXCLUSION OF SOURCES' AND (UPPER(type_of_set_aside) = 'NO SET ASIDE USED' OR UPPER(type_of_set_aside) = 'NO SET ASIDE USED.') THEN NULL
                            ELSE UPPER(type_of_set_aside)
                        END AS type_of_set_aside,
                        fair_opportunity_limited_sources,
                        other_than_full_and_open_competition,
                        CASE 
                            WHEN number_of_offers_received ~ '^[0-9]+(\.0+)?$' THEN 
                                CAST(REGEXP_REPLACE(number_of_offers_received, '\.0+$', '') AS INTEGER)
                            ELSE NULL
                        END AS number_of_offers_received,
                        subcontracting_plan,
                        government_furnished_property,
                        UPPER(type_of_contract_pricing) AS type_of_contract_pricing,
                        action_type,
                        award_type,
                        type_of_idc,
                        idv_type,
                        undefinitized_action,
                        multi_year_contract,
                        multiple_or_single_award_idv,
                        usaspending_permalink
                    FROM null_key_records;
                """)
                connection.execute(null_records_sql)
                connection.commit()
                connection.execute(text("DROP TABLE null_key_records;"))
                connection.commit()
                logger.info(f"Successfully added {null_key_count} records with generated transaction keys")
            
            # (Removed legacy error handling for PRIMARY KEY constraint and old table names)
                
            # Calculate statistics for the transformation
            transform_end = time.time()
            transform_duration = transform_end - transform_start
            
            # Get count of processed rows
            count_query = text(f"SELECT COUNT(*) FROM {PRIME_DEST}")
            processed_rows = connection.execute(count_query).scalar()
            
            # Calculate time stats
            minutes = int(transform_duration // 60)
            seconds = int(transform_duration % 60)
            rows_per_second = processed_rows / transform_duration if transform_duration > 0 else 0
            
            logger.info(f"Transformation complete in {minutes}m {seconds}s")
            logger.info(f"Processed {processed_rows:,} rows")
            logger.info(f"Processing speed: {rows_per_second:.2f} rows/second")
            
            # Verify data preservation
            if processed_rows != source_row_count:
                logger.warning(f"WARNING: Processed rows ({processed_rows:,}) doesn't match source count ({source_row_count:,})")
                logger.warning("This could indicate a problem with data preservation or duplicate keys!")

                # Get specific counts to diagnose the issue
                unique_count_query = text(f"""
                    SELECT COUNT(DISTINCT contract_transaction_unique_key) 
                    FROM {PRIME_DEST}
                    WHERE contract_transaction_unique_key IS NOT NULL
                """)
                unique_cleaned_count = connection.execute(unique_count_query).scalar()
                null_count_query = text(f"SELECT COUNT(*) FROM {PRIME_DEST} WHERE contract_transaction_unique_key IS NULL")
                null_cleaned_count = connection.execute(null_count_query).scalar()

                logger.info(f"Cleaned data has {unique_cleaned_count:,} unique transaction keys")
                logger.info(f"Cleaned data has {null_cleaned_count:,} records with NULL transaction keys")

                if unique_cleaned_count + null_cleaned_count == processed_rows:
                    logger.info("All processed records are accounted for (unique keys + NULL keys)")

                # Report on duplicates that may have been eliminated
                if unique_key_count != unique_cleaned_count:
                    logger.warning(f"Lost {unique_key_count - unique_cleaned_count:,} unique transaction keys during cleaning")
            else:
                logger.info(f"[OK] All {source_row_count:,} source rows successfully preserved in the transformation")   
        
    except Exception as e:
        logger.error(f"\nERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    elapsed_time = time.time() - start_time
    hours = int(elapsed_time // 3600)
    minutes = int((elapsed_time % 3600) // 60)
    seconds = int(elapsed_time % 60)
    
    logger.info(f"\nData cleansing complete!")
    logger.info(f"Total elapsed time: {hours}h {minutes}m {seconds}s")
    logger.info(f"Processed {processed_rows:,} records")
    logger.info(f"Average processing speed: {processed_rows/elapsed_time:.2f} rows/second")
    
    return True
def cleanse_subawards_data(force_rebuild=True):
    """
    Cleanse the usaspending_subawards_slim table and output to usaspending_subawards_cleaned.
    Standardizes text fields, handles NULLs, and optimizes for analytics. Deduplication is handled elsewhere.

    Args:
        force_rebuild: If True, drops and recreates the cleaned table if it exists.
    Returns:
        True if successful, False otherwise.
    """
    start_time = time.time()
    logger.info("Starting subawards data cleansing process...")

    SUB_SRC = "s1_raw.usaspending_subawards"
    SUB_DEST = "s2_interim.usaspending_subawards"

    with engine.connect() as connection:
        table_exists_query = text(f"""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 's2_interim' AND table_name = 'usaspending_subawards'
            )
        """)
        destination_exists = connection.execute(table_exists_query).scalar()
        if destination_exists:
            if force_rebuild:
                logger.warning(f"\nWARNING: s2_interim.usaspending_subawards table already exists and will be dropped and recreated.")
                logger.warning(f"All existing data in s2_interim.usaspending_subawards will be lost.")
                logger.warning("Processing will continue in 5 seconds...\n")
                time.sleep(5)
                try:
                    connection.execute(text(f"DROP TABLE IF EXISTS s2_interim.usaspending_subawards CASCADE"))
                    connection.commit()
                    logger.info(f"Successfully dropped s2_interim.usaspending_subawards table.")
                except Exception as e:
                    logger.error(f"Error dropping table: {e}")
                    raise
            else:
                logger.info(f"s2_interim.usaspending_subawards table already exists. Exiting to prevent data loss.")
                return False

    try:
        with engine.connect() as connection:
            # Verify source table exists
            table_check_query = text(
                f"SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_schema = 's1_raw' AND table_name = 'usaspending_subawards');"
            )
            source_exists = connection.execute(table_check_query).scalar()
            if not source_exists:
                raise Exception(f"Error: {SUB_SRC} table does not exist")

            # Get row count
            count_query = text(f"SELECT COUNT(*) FROM {SUB_SRC};")
            source_row_count = connection.execute(count_query).scalar()
            logger.info(f"Subawards source table contains {source_row_count:,} rows")

            # Create destination table
            create_table_query = text(f"""
                CREATE TABLE {SUB_DEST} (
                    id BIGSERIAL PRIMARY KEY,
                    prime_award_unique_key TEXT,
                    subaward_number TEXT,
                    subaward_amount NUMERIC,
                    subaward_action_date DATE,
                    subaward_description TEXT,
                    subawardee_name TEXT,
                    subawardee_uei TEXT,
                    subawardee_parent_name TEXT,
                    subawardee_parent_uei TEXT,
                    subawardee_city_name TEXT,
                    subawardee_state_code TEXT,
                    subawardee_country_code TEXT,
                    subawardee_country_name TEXT,
                    subawardee_business_types TEXT,
                    subaward_primary_place_of_performance_city_name TEXT,
                    subaward_primary_place_of_performance_state_code TEXT,
                    subaward_type TEXT,
                    created_at TIMESTAMP,
                    updated_at TIMESTAMP,
                    fetch_date DATE
                );
            """)
            connection.execute(create_table_query)
            connection.commit()

        # Cleansing and transformation
        logger.info(f"\nPerforming SQL cleansing and transformation for {SUB_SRC}...")
        with engine.connect() as connection:
            connection.execute(text("SET synchronous_commit = OFF;"))
            connection.execute(text("SET work_mem = '1024MB';"))
            connection.execute(text("SET maintenance_work_mem = '1024MB';"))
            connection.execute(text("SET max_parallel_workers_per_gather = 4;"))
            connection.execute(text("SET max_parallel_workers = 8;"))
            connection.execute(text("SET random_page_cost = 1.1;"))
            connection.execute(text("SET cpu_tuple_cost = 0.03;"))

            logger.info("Starting subawards data transformation...")
            transform_start = time.time()

            transform_sql = text(rf"""
                INSERT INTO {SUB_DEST} (
                    prime_award_unique_key,
                    subaward_number,
                    subaward_amount,
                    subaward_action_date,
                    subaward_description,
                    subawardee_name,
                    subawardee_uei,
                    subawardee_parent_name,
                    subawardee_parent_uei,
                    subawardee_city_name,
                    subawardee_state_code,
                    subawardee_country_code,
                    subawardee_country_name,
                    subawardee_business_types,
                    subaward_primary_place_of_performance_city_name,
                    subaward_primary_place_of_performance_state_code,
                    subaward_type,
                    created_at,
                    updated_at,
                    fetch_date
                )
                SELECT
                    prime_award_unique_key,
                    subaward_number,
                    subaward_amount::numeric,
                    subaward_action_date::date,
                    TRIM(subaward_description),
                    UPPER(TRIM(subawardee_name)),
                    subawardee_uei,
                    UPPER(TRIM(subawardee_parent_name)),
                    subawardee_parent_uei,
                    UPPER(TRIM(subawardee_city_name)),
                    UPPER(TRIM(subawardee_state_code)),
                    UPPER(TRIM(subawardee_country_code)),
                    UPPER(TRIM(subawardee_country_name)),
                    subawardee_business_types,
                    UPPER(TRIM(subaward_primary_place_of_performance_city_name)),
                    UPPER(TRIM(subaward_primary_place_of_performance_state_code)),
                    UPPER(TRIM(subaward_type)),
                    created_at,
                    updated_at,
                    fetch_date
                FROM {SUB_SRC};
            """)
            connection.execute(transform_sql)
            connection.commit()

            transform_end = time.time()
            transform_duration = transform_end - transform_start
            minutes = int(transform_duration // 60)
            seconds = int(transform_duration % 60)
            count_query = text(f"SELECT COUNT(*) FROM {SUB_DEST}")
            processed_rows = connection.execute(count_query).scalar()
            logger.info(f"Subawards transformation complete in {minutes}m {seconds}s")
            logger.info(f"Processed {processed_rows:,} subaward rows")
            logger.info(f"Processing speed: {processed_rows/transform_duration:.2f} rows/second")

    except Exception as e:
        logger.error(f"\nERROR in subawards cleansing: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

    elapsed_time = time.time() - start_time
    hours = int(elapsed_time // 3600)
    minutes = int((elapsed_time % 3600) // 60)
    seconds = int(elapsed_time % 60)
    logger.info(f"\nSubawards data cleansing complete!")
    logger.info(f"Total elapsed time: {hours}h {minutes}m {seconds}s")
    logger.info(f"Processed {processed_rows:,} subaward records")
    logger.info(f"Average processing speed: {processed_rows/elapsed_time:.2f} rows/second")
    return True

if __name__ == "__main__":
    # Configure logging when run as a standalone script
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )

    logger.info(f"Python version: {sys.version}")
    logger.info(f"Pandas version: {pd.__version__}")
    logger.info(f"Starting data cleansing process with direct SQL transformation...")

    # Run both cleansing functions
    cleanse_data()
    cleanse_subawards_data()
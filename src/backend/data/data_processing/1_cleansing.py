"""
Step 1: Consolidated Data Cleansing, Empty Column Removal, and Deduplication for USASpending ETL Pipeline

This script consolidates all ETL preprocessing steps for both prime awards and subawards:
- Cleansing and standardization (type fixes, agency name normalization, text cleaning)
- Removal of empty columns (columns with all NULLs or blanks)
- Business-level deduplication (using robust compound keys)
- All logging, validation, and reporting from legacy scripts is preserved

Outputs:
- s2_interim.usaspending_prime_awards_dedup (fully cleaned and deduplicated prime awards)
- s2_interim.usaspending_subawards_dedup (fully cleaned and deduplicated subawards)

This reduces disk usage, improves performance, and simplifies orchestration. Downstream scripts (enrichment, analytics) should use the *_dedup tables as before.

Run as standalone or as part of the ETL pipeline.
"""
import os
import sys
import time
import logging
 
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

pg_user = os.getenv('PG_USER')
pg_password = os.getenv('PG_PASSWORD')
pg_host = os.getenv('PG_HOST')
pg_port = os.getenv('PG_PORT')
pg_dbname = os.getenv('PG_DBNAME')

db_url = f"postgresql://{pg_user}:{pg_password}@{pg_host}:{pg_port}/{pg_dbname}"
engine = create_engine(db_url, echo=False)

logger = logging.getLogger(__name__)

# --- Utility: Remove empty columns from a table ---
def remove_empty_columns(table_name, schema='s2_interim'):
    """
    Drops columns from the table where all values are NULL or blank.
    """
    with engine.connect() as connection:
        cols_query = text(f"""
            SELECT column_name FROM information_schema.columns
            WHERE table_schema = '{schema}' AND table_name = '{table_name}'
        """)
        cols = [row[0] for row in connection.execute(cols_query)]
        empty_cols = []
        for col in cols:
            null_count = connection.execute(text(f"SELECT COUNT(*) FROM {schema}.{table_name} WHERE {col} IS NOT NULL AND TRIM(COALESCE({col}::text,'')) <> ''")).scalar()
            if null_count == 0:
                empty_cols.append(col)
        for col in empty_cols:
            logger.info(f"Dropping empty column: {col}")
            connection.execute(text(f"ALTER TABLE {schema}.{table_name} DROP COLUMN IF EXISTS {col}"))
        connection.commit()
    return empty_cols

# --- Prime Awards: Cleansing + Empty Column Removal + Deduplication ---
def process_prime_awards(force_rebuild=True):
    start_time = time.time()
    logger.info("Starting consolidated cleansing for prime awards...")
    PRIME_SRC = "s1_raw.usaspending_prime_awards_slim"
    PRIME_DEST = "s2_interim.usaspending_prime_awards_dedup"
    # Compound key for deduplication
    compound_keys = [
        "award_id_piid",
        "modification_number",
        "action_date",
        "federal_action_obligation",
        "recipient_name"
    ]
    compound_key_expr = ", ".join(compound_keys)
    with engine.connect() as connection:
        # Drop destination if exists
        connection.execute(text(f"DROP TABLE IF EXISTS {PRIME_DEST} CASCADE"))
        connection.commit()
        # Cleansing, transformation, and deduplication in one step
        logger.info("Transforming, cleaning, and deduplicating prime awards...")
        create_query = text(f"""
CREATE TABLE {PRIME_DEST} AS
SELECT DISTINCT ON ({compound_key_expr})
    contract_transaction_unique_key,
    contract_award_unique_key,
    action_date_fiscal_year::text,
    CASE 
        WHEN EXTRACT(MONTH FROM action_date::date) IN (10, 11, 12) THEN 1
        WHEN EXTRACT(MONTH FROM action_date::date) IN (1, 2, 3) THEN 2
        WHEN EXTRACT(MONTH FROM action_date::date) IN (4, 5, 6) THEN 3
        WHEN EXTRACT(MONTH FROM action_date::date) IN (7, 8, 9) THEN 4
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
    SUBSTRING(REGEXP_REPLACE(naics_code::text, '\\.0$', ''), 1, 6) AS naics_code,
    naics_description,
    product_or_service_code,
    product_or_service_code_description,
    dod_acquisition_program_description,
    CASE
        WHEN TRIM(parent_award_agency_name) ILIKE 'DEPT OF DEFENSE' THEN 'DEPARTMENT OF DEFENSE'
        ELSE TRIM(parent_award_agency_name)
    END AS parent_award_agency_name,
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
    number_of_offers_received::NUMERIC::INTEGER AS number_of_offers_received,
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
ORDER BY {compound_key_expr}, action_date DESC;
        """)
        connection.execute(create_query)
        connection.commit()
        logger.info("Prime awards: removing empty columns...")
        remove_empty_columns('usaspending_prime_awards_dedup')
        count_query = text(f"SELECT COUNT(*) FROM {PRIME_DEST}")
        row_count = connection.execute(count_query).scalar()
        logger.info(f"Prime awards deduplication complete: {row_count:,} rows in final table.")
    elapsed = time.time() - start_time
    minutes = int(elapsed // 60)
    seconds = int(elapsed % 60)
    logger.info(f"Prime awards processing completed in {minutes}m {seconds}s ({elapsed:.2f} seconds).")
    return row_count

# --- Subawards: Cleansing + Empty Column Removal + Deduplication ---
def process_subawards(force_rebuild=True):
    start_time = time.time()
    logger.info("Starting consolidated cleansing for subawards...")
    SUB_SRC = "s1_raw.usaspending_subawards"
    SUB_DEST = "s2_interim.usaspending_subawards_dedup"
    # Compound key for deduplication
    sub_keys = [
        "prime_award_unique_key",
        "subaward_number",
        "subaward_action_date",
        "subaward_amount",
        "subawardee_uei",
        "subawardee_name"
    ]
    sub_key_expr = ", ".join(sub_keys)
    with engine.connect() as connection:
        connection.execute(text(f"DROP TABLE IF EXISTS {SUB_DEST} CASCADE"))
        connection.commit()
        logger.info("Transforming, cleaning, and deduplicating subawards...")
        create_query = text(f"""
CREATE TABLE {SUB_DEST} AS
SELECT DISTINCT ON ({sub_key_expr})
    subaward_unique_key, -- Carry over surrogate key for traceability and batching
    prime_award_unique_key,
    subaward_number,
    subaward_amount::numeric,
    subaward_action_date::date,
    TRIM(subaward_description) AS subaward_description,
    UPPER(TRIM(subawardee_name)) AS subawardee_name,
    subawardee_uei,
    UPPER(TRIM(subawardee_parent_name)) AS subawardee_parent_name,
    subawardee_parent_uei,
    UPPER(TRIM(subawardee_city_name)) AS subawardee_city_name,
    UPPER(TRIM(subawardee_state_code)) AS subawardee_state_code,
    UPPER(TRIM(subawardee_country_code)) AS subawardee_country_code,
    UPPER(TRIM(subawardee_country_name)) AS subawardee_country_name,
    subawardee_business_types,
    UPPER(TRIM(subaward_primary_place_of_performance_city_name)) AS subaward_primary_place_of_performance_city_name,
    UPPER(TRIM(subaward_primary_place_of_performance_state_code)) AS subaward_primary_place_of_performance_state_code,
    UPPER(TRIM(subaward_type)) AS subaward_type,
    created_at,
    updated_at,
    fetch_date
FROM s2_interim.usaspending_subawards
WHERE prime_award_unique_key IS NOT NULL
ORDER BY {sub_key_expr};
        """)
        connection.execute(create_query)
        connection.commit()
        logger.info("Subawards: removing empty columns...")
        remove_empty_columns('usaspending_subawards_dedup')
        count_query = text(f"SELECT COUNT(*) FROM {SUB_DEST}")
        row_count = connection.execute(count_query).scalar()
        logger.info(f"Subawards deduplication complete: {row_count:,} rows in final table.")
    elapsed = time.time() - start_time
    minutes = int(elapsed // 60)
    seconds = int(elapsed % 60)
    logger.info(f"Subawards processing completed in {minutes}m {seconds}s ({elapsed:.2f} seconds).")
    return row_count

def cleanse_data(force_rebuild=True):
    """
    Cleanses s1_raw.usaspending_prime_awards_slim into s2_interim.usaspending_prime_awards.
    Preserves all previous cleaning logic, type fixes, and agency name standardization.
    """
    start_time = time.time()
    logger.info("Starting high-performance data cleansing process for prime awards...")
    # Multiprocessing not used; all processing is SQL-based.
    logger.info(f"Using optimized PostgreSQL direct SQL transformation")

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
                    logger.info(f"Successfully dropped s2_interim.usaspending_prime_awards table.")
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

            # Check for contract_transaction_unique_key in source table
            column_check_query = text(
                "SELECT COUNT(*) FROM information_schema.columns WHERE table_schema = 's1_raw' AND table_name = 'usaspending_prime_awards_slim' AND column_name = 'contract_transaction_unique_key';"
            )
            has_unique_key = connection.execute(column_check_query).scalar() > 0
            if not has_unique_key:
                logger.warning("WARNING: contract_transaction_unique_key not found in source table!")
                logger.warning("This column is required as it will be used as the PRIMARY KEY.")
                raise Exception("Missing required contract_transaction_unique_key column in source table")

            # Get row count and key stats
            count_query = text(f"SELECT COUNT(*) FROM {PRIME_SRC};")
            source_row_count = connection.execute(count_query).scalar()
            logger.info(f"Source table contains {source_row_count:,} rows")

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
            if null_key_count > 0:
                logger.warning(f"Found {null_key_count:,} rows with NULL transaction keys")

            # Create destination table
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

        # --- MAIN CLEANSING SQL ---
        with engine.connect() as connection:
            connection.execute(text("SET synchronous_commit = OFF;"))
            connection.execute(text("SET work_mem = '2047MB';"))
            connection.execute(text("SET maintenance_work_mem = '2047MB';"))
            connection.execute(text("SET max_parallel_workers_per_gather = 4;"))
            connection.execute(text("SET max_parallel_workers = 8;"))
            connection.execute(text("SET random_page_cost = 1.1;"))
            connection.execute(text("SET cpu_tuple_cost = 0.03;"))

            logger.info("Starting data transformation (this may take some time)...")
            transform_start = time.time()

            transform_sql = text(rf"""
                INSERT INTO {PRIME_DEST}
                SELECT DISTINCT ON (contract_transaction_unique_key)
                    contract_transaction_unique_key,
                    contract_award_unique_key,
                    action_date_fiscal_year::text,
                    CASE 
                        WHEN EXTRACT(MONTH FROM action_date::date) IN (10, 11, 12) THEN 1
                        WHEN EXTRACT(MONTH FROM action_date::date) IN (1, 2, 3) THEN 2
                        WHEN EXTRACT(MONTH FROM action_date::date) IN (4, 5, 6) THEN 3
                        WHEN EXTRACT(MONTH FROM action_date::date) IN (7, 8, 9) THEN 4
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
                    SUBSTRING(REGEXP_REPLACE(naics_code::text, '\\.0$', ''), 1, 6) AS naics_code,
                    naics_description,
                    product_or_service_code,
                    product_or_service_code_description,
                    dod_acquisition_program_description,
                    -- Standardize DEPT OF DEFENSE to DEPARTMENT OF DEFENSE, do not fill nulls/blanks
                    CASE
                        WHEN TRIM(parent_award_agency_name) ILIKE 'DEPT OF DEFENSE' THEN 'DEPARTMENT OF DEFENSE'
                        ELSE TRIM(parent_award_agency_name)
                    END AS parent_award_agency_name,
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
                    number_of_offers_received::NUMERIC::INTEGER AS number_of_offers_received,
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
                        CASE 
                            WHEN EXTRACT(MONTH FROM action_date::date) IN (10, 11, 12) THEN 1
                            WHEN EXTRACT(MONTH FROM action_date::date) IN (1, 2, 3) THEN 2
                            WHEN EXTRACT(MONTH FROM action_date::date) IN (4, 5, 6) THEN 3
                            WHEN EXTRACT(MONTH FROM action_date::date) IN (7, 8, 9) THEN 4
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
                        SUBSTRING(REGEXP_REPLACE(naics_code::text, '\\.0$', ''), 1, 6) AS naics_code,
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
                        CASE WHEN number_of_offers_received ~ '^[0-9]+(\\.0+)?$' THEN CAST(REGEXP_REPLACE(number_of_offers_received, '\\.0+$', '') AS INTEGER) ELSE NULL END AS number_of_offers_received,
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

            # Calculate statistics
            transform_end = time.time()
            transform_duration = transform_end - transform_start
            count_query = text(f"SELECT COUNT(*) FROM {PRIME_DEST}")
            processed_rows = connection.execute(count_query).scalar()
            minutes = int(transform_duration // 60)
            seconds = int(transform_duration % 60)
            logger.info(f"Transformation complete in {minutes}m {seconds}s")
            logger.info(f"Processed {processed_rows:,} rows")
            logger.info(f"Processing speed: {processed_rows/transform_duration:.2f} rows/second")

            # Data preservation check
            if processed_rows != source_row_count:
                logger.warning(f"WARNING: Processed rows ({processed_rows:,}) doesn't match source count ({source_row_count:,})")
                unique_count_query = text(f"SELECT COUNT(DISTINCT contract_transaction_unique_key) FROM {PRIME_DEST} WHERE contract_transaction_unique_key IS NOT NULL")
                unique_cleaned_count = connection.execute(unique_count_query).scalar()
                null_count_query = text(f"SELECT COUNT(*) FROM {PRIME_DEST} WHERE contract_transaction_unique_key IS NULL")
                null_cleaned_count = connection.execute(null_count_query).scalar()
                logger.info(f"Cleaned data has {unique_cleaned_count:,} unique transaction keys")
                logger.info(f"Cleaned data has {null_cleaned_count:,} records with NULL transaction keys")
                if unique_cleaned_count + null_cleaned_count == processed_rows:
                    logger.info("All processed records are accounted for (unique keys + NULL keys)")
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
    Cleanses s1_raw.usaspending_subawards into s2_interim.usaspending_subawards.
    Standardizes text fields, handles NULLs, and optimizes for analytics. Deduplication is handled elsewhere.
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
            table_check_query = text(
                f"SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_schema = 's1_raw' AND table_name = 'usaspending_subawards');"
            )
            source_exists = connection.execute(table_check_query).scalar()
            if not source_exists:
                raise Exception(f"Error: {SUB_SRC} table does not exist")
            count_query = text(f"SELECT COUNT(*) FROM {SUB_SRC};")
            source_row_count = connection.execute(count_query).scalar()
            logger.info(f"Subawards source table contains {source_row_count:,} rows")
            # Reason: Preserve a unique surrogate key for batching and downstream processing
            create_table_query = text(f"""
                CREATE TABLE {SUB_DEST} (
                    subaward_unique_key BIGSERIAL PRIMARY KEY, -- Surrogate key for batching and uniqueness
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
            # Reason: subaward_unique_key is auto-generated, so do not insert it explicitly
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
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)]
    )
    logger.info(f"Python version: {sys.version}")
    logger.info("Step 1: Cleansing raw prime awards (s1_raw.usaspending_prime_awards_slim) -> s2_interim.usaspending_prime_awards ...")
    cleanse_data()
    logger.info("Step 2: Deduplicating prime awards (s2_interim.usaspending_prime_awards_dedup) ...")
    process_prime_awards()
    logger.info("Step 3: Cleansing raw subawards (s1_raw.usaspending_subawards) -> s2_interim.usaspending_subawards ...")
    cleanse_subawards_data()
    logger.info("Step 4: Deduplicating subawards (s2_interim.usaspending_subawards_dedup) ...")
    process_subawards()

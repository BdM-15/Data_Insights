"""
Data Transformation Script for USASpending Contract Data.

This script handles the post-deduplicated data transformation and optimization
to improve application query performance. It creates aggregated views and filtered
subsets of data that will power the application's visualizations.
"""

import pandas as pd
import numpy as np
import time
import os
import sys
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import logging
from datetime import datetime

# Set up logging
logger = logging.getLogger(__name__)

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

"""
Note on Key Relationships:
    - In s3_processed.usaspending_prime_awards, contract_transaction_unique_key is the unique row/transaction key.
    - contract_award_unique_key identifies the overall contract/award (across all transactions).
    - In s3_processed.usaspending_subawards, prime_award_unique_key is a foreign key that links each subaward to its parent contract/award (not to a transaction).
    - This design allows you to join all subawards for a given contract/award using prime_award_unique_key <-> contract_award_unique_key.
    - There is no issue with deduplication on contract_transaction_unique_key for primes and using prime_award_unique_key for subaward-to-prime joins.
"""

# Function to create indexes for deduplicated tables in s3_processed
def create_performance_indexes():
    """
    Create recommended indexes on s3_processed.usaspending_prime_awards and s3_processed.usaspending_subawards
    to optimize analytics, AI, and RAG workloads. Index creation is idempotent and safe to rerun.
    """
    with engine.connect() as connection:
        # Begin a transaction to ensure DDL is committed
        with connection.begin():
            # Helper to drop index if it exists on the table in s3_processed
            def drop_index_if_exists(index_name: str):
                sql = f"""
                    DO $$
                    BEGIN
                        IF EXISTS (
                            SELECT 1 FROM pg_indexes 
                            WHERE schemaname = 's3_processed' AND indexname = '{index_name}'
                        ) THEN
                            EXECUTE 'DROP INDEX IF EXISTS s3_processed.{index_name}';
                        END IF;
                    END$$;
                """
                connection.execute(text(sql))

            prime_table = 's3_processed.usaspending_prime_awards'
            prime_indexes = [
                {"name": "s3p_idx_prime_contract_transaction_unique_key", "columns": "contract_transaction_unique_key"},
                {"name": "s3p_idx_prime_award_id_piid", "columns": "award_id_piid"},
                {"name": "s3p_idx_prime_action_date", "columns": "action_date"},
                {"name": "s3p_idx_prime_recipient_name", "columns": "recipient_name"},
                {"name": "s3p_idx_prime_naics_code", "columns": "naics_code"},
                {"name": "s3p_idx_prime_agency_fiscal_year", "columns": "parent_award_agency_name, action_date_fiscal_year"},
                # Treemap-specific indexes for competitive landscape visualization
                {"name": "s3p_idx_treemap_grouping", "columns": "recipient_parent_name, recipient_name, funding_sub_agency_name"},
                {"name": "s3p_idx_treemap_obligation", "columns": "federal_action_obligation"},
                {"name": "s3p_idx_treemap_modification", "columns": "modification_number"},
                {"name": "s3p_idx_funding_sub_agency", "columns": "funding_sub_agency_name"}
            ]
            for idx in prime_indexes:
                logger.info(f"Ensuring index {idx['name']} on {prime_table}({idx['columns']})...")
                drop_index_if_exists(idx["name"])
                try:
                    connection.execute(text(f'CREATE INDEX {idx["name"]} ON s3_processed.usaspending_prime_awards ({idx["columns"]})'))
                    logger.info(f"  [OK] Created index {idx['name']} on {prime_table}")
                except Exception as e:
                    logger.error(f"  [ERROR] Failed to create index {idx['name']} on {prime_table}: {e}")

            sub_table = 's3_processed.usaspending_subawards'
            sub_indexes = [
                {"name": "s3p_idx_sub_prime_award_unique_key", "columns": "prime_award_unique_key"},
                {"name": "s3p_idx_sub_subawardee_uei", "columns": "subawardee_uei"},
                {"name": "s3p_idx_sub_subaward_action_date", "columns": "subaward_action_date"},
                {"name": "s3p_idx_sub_composite_key", "columns": "prime_award_unique_key, subaward_number, subaward_action_date, subaward_amount"}
            ]
            for idx in sub_indexes:
                logger.info(f"Ensuring index {idx['name']} on {sub_table}({idx['columns']})...")
                drop_index_if_exists(idx["name"])
                try:
                    connection.execute(text(f'CREATE INDEX {idx["name"]} ON s3_processed.usaspending_subawards ({idx["columns"]})'))
                    logger.info(f"  [OK] Created index {idx['name']} on {sub_table}")
                except Exception as e:
                    logger.error(f"  [ERROR] Failed to create index {idx['name']} on {sub_table}: {e}")

            logger.info("[OK] All recommended indexes created for s3_processed tables.")

            # Verification step: log all indexes found for the two tables
            logger.info("Verifying created indexes...")
            result = connection.execute(text("""
                SELECT indexname 
                FROM pg_indexes 
                WHERE schemaname = 's3_processed' 
                AND tablename IN ('usaspending_prime_awards', 'usaspending_subawards')
            """)).fetchall()
            for row in result:
                logger.info(f"Found index: {row[0]}")
            if not result:
                logger.warning("No indexes found for usaspending_prime_awards or usaspending_subawards!")

def preprocess_data_optimized():
    """
    Optimized preprocessing of deduplicated data using direct SQL.
    Creates various lookup tables and filter value lists to improve
    query performance in the application.
    
    Returns:
    --------
    dict
        A dictionary containing the preprocessing results.
    """
    start_time = time.time()
    results = {}
    # Automatically create performance indexes before preprocessing
    logger.info("\n[Auto] Creating performance indexes for s3_processed tables before preprocessing...")
    create_performance_indexes()
    
    # Use s3_processed.usaspending_prime_awards as the source table
    source_schema = "s3_processed"
    source_table = f"{source_schema}.usaspending_prime_awards"
    logger.info(f"Using {source_table} as source for transformation")
    logger.info("Starting optimized data preprocessing for app performance...")
    # Check if primary table exists and has data
    with engine.connect() as connection:
        table_exists = connection.execute(text(
            """
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables 
                WHERE table_schema = 's3_processed' AND table_name = 'usaspending_prime_awards'
            )
            """
        )).scalar()
        if not table_exists:
            logger.error(f"Error: {source_table} table does not exist. Run data cleansing and deduplication first.")
            return {"error": f"{source_table} table not found"}
        # Get row count
        row_count = connection.execute(text(f"SELECT COUNT(*) FROM {source_table}")).scalar()
        if row_count == 0:
            logger.error(f"Error: {source_table} table is empty. Check data cleansing process.")
            return {"error": f"{source_table} table is empty"}
        logger.info(f"Found {source_table} table with {row_count:,} rows.")
    
    with engine.connect() as connection:
        # Create distinct filter value tables for the UI in s3_processed
        logger.info("\nPrecomputing filter values tables using direct SQL...")

        filter_columns = [
            "parent_award_agency_name",
            "funding_sub_agency_name",
            "funding_office_name",
            "recipient_name",
            "naics_code",
            "product_or_service_code",
            "type_of_contract_pricing",
            "extent_competed",
            "type_of_set_aside"
        ]

        filter_tables = []

        for column in filter_columns:
            logger.info(f"  - Creating filter values for {column}...")
            table_name = f"{source_schema}.filter_values_{column}"

            # Drop existing table if it exists
            connection.execute(text(f"DROP TABLE IF EXISTS {table_name}"))

            # Create the filter values table with counts
            create_filter_query = text(f"""
                CREATE TABLE {table_name} AS
                SELECT 
                    {column} as value,
                    COUNT(*) as record_count,
                    SUM(federal_action_obligation) as total_obligation
                FROM 
                    {source_table}
                WHERE 
                    {column} IS NOT NULL AND {column} != ''
                GROUP BY 
                    {column}
                ORDER BY 
                    COUNT(*) DESC
            """)

            connection.execute(create_filter_query)
            connection.commit()

            # Get row count
            filter_count = connection.execute(text(f"SELECT COUNT(*) FROM {table_name}")).scalar()
            filter_tables.append({"name": table_name, "count": filter_count})

            logger.info(f"    [OK] Created filter values table for {column}")

        # Precompute dependent filter relationships (e.g., agency → sub-agency → office) in s3_processed
        logger.info("\nPrecomputing dependent filter relationships using direct SQL...")

        dependencies_table = f"{source_schema}.filter_dependencies"
        # Drop existing table if it exists
        connection.execute(text(f"DROP TABLE IF EXISTS {dependencies_table}"))

        # Create the filter dependencies table for hierarchical filters
        logger.info("  - Creating agency to sub-agency dependencies...")
        create_dependencies_query = text(f"""
            CREATE TABLE {dependencies_table} AS
            SELECT 
                'parent_agency_to_sub_agency' as relationship_type,
                parent_award_agency_name as parent_value,
                funding_sub_agency_name as child_value,
                COUNT(*) as record_count
            FROM 
                {source_table}
            WHERE 
                parent_award_agency_name IS NOT NULL AND parent_award_agency_name != '' AND
                funding_sub_agency_name IS NOT NULL AND funding_sub_agency_name != ''
            GROUP BY 
                parent_award_agency_name, funding_sub_agency_name
            ORDER BY 
                parent_award_agency_name, COUNT(*) DESC
        """)

        connection.execute(create_dependencies_query)
        connection.commit()

        # Add sub-agency to funding office relationships
        logger.info("  - Creating sub-agency to funding office dependencies...")
        append_dependencies_query = text(f"""
            INSERT INTO {dependencies_table}
            SELECT 
                'sub_agency_to_funding_office' as relationship_type,
                funding_sub_agency_name as parent_value,
                funding_office_name as child_value,
                COUNT(*) as record_count
            FROM 
                {source_table}
            WHERE 
                funding_sub_agency_name IS NOT NULL AND funding_sub_agency_name != '' AND
                funding_office_name IS NOT NULL AND funding_office_name != ''
            GROUP BY 
                funding_sub_agency_name, funding_office_name
            ORDER BY 
                funding_sub_agency_name, COUNT(*) DESC
        """)

        connection.execute(append_dependencies_query)
        connection.commit()

        # Get dependency count
        dependency_count = connection.execute(text(f"SELECT COUNT(*) FROM {dependencies_table}")).scalar()

        logger.info(f"  [OK] Created filter_dependencies table with {dependency_count} relationships.")

        # Confirm it exists
        filter_dependencies_exists = connection.execute(text(
            f"SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_schema = '{source_schema}' AND table_name = 'filter_dependencies')"
        )).scalar()

        if filter_dependencies_exists:
            logger.info(f"    [OK] Confirmed filter_dependencies table exists in database")
        else:
            logger.error("Error: filter_dependencies table was not created successfully")

        # Create quarterly aggregated data for timeline charts in s3_processed
        logger.info("\nPre-aggregating data for visualizations using direct SQL...")

        quarterly_table = f"{source_schema}.quarterly_data"
        # Drop existing table if it exists
        connection.execute(text(f"DROP TABLE IF EXISTS {quarterly_table}"))

        # Create the quarterly data table with fiscal year and quarter calculations (computed on the fly)
        # US Federal Fiscal Year starts in October, so add 3 months to action_date
        create_quarterly_query = text(f"""
            CREATE TABLE {quarterly_table} AS
            SELECT 
                EXTRACT(YEAR FROM action_date + INTERVAL '3 months') AS fiscal_year,
                EXTRACT(QUARTER FROM action_date + INTERVAL '3 months') AS fiscal_quarter,
                CONCAT(EXTRACT(YEAR FROM action_date + INTERVAL '3 months'), ' Q', EXTRACT(QUARTER FROM action_date + INTERVAL '3 months')) AS fiscal_period,
                COUNT(*) as award_count,
                SUM(federal_action_obligation) as total_obligation,
                COUNT(DISTINCT recipient_name) as vendor_count,
                COUNT(DISTINCT contract_award_unique_key) as unique_award_count,
                COUNT(DISTINCT naics_code) as unique_naics_count
            FROM 
                {source_table}
            WHERE 
                action_date IS NOT NULL
            GROUP BY 
                fiscal_year, fiscal_quarter
            ORDER BY 
                fiscal_year, fiscal_quarter
        """)

        connection.execute(create_quarterly_query)
        connection.commit()

        # Get quarterly count
        quarterly_count = connection.execute(text(f"SELECT COUNT(*) FROM {quarterly_table}")).scalar()

        logger.info(f"  [OK] Created quarterly_data table with {quarterly_count} rows.")

        # Confirm it exists
        quarterly_data_exists = connection.execute(text(
            f"SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_schema = '{source_schema}' AND table_name = 'quarterly_data')"
        )).scalar()

        if quarterly_data_exists:
            logger.info(f"    [OK] Confirmed quarterly_data table exists in database")
        else:
            logger.error("Error: quarterly_data table was not created successfully")

        # Final optimization: ANALYZE tables for query planning
        logger.info("\nPerforming final optimization and cleanup...")

        # List of tables to analyze
        tables_to_analyze = [
            source_table,
            quarterly_table,
            dependencies_table
        ] + [table["name"] for table in filter_tables]

        for table in tables_to_analyze:
            connection.execute(text(f"ANALYZE {table}"))
            logger.info(f"  [OK] Analyzed {table} table for optimal query performance")

        # Clean up any temporary tables in s3_processed (if any)
        temp_tables_query = text(f"""
            SELECT tablename FROM pg_tables 
            WHERE tablename LIKE 'temp_%' 
            AND schemaname = '{source_schema}'
        """)

        temp_tables = [row[0] for row in connection.execute(temp_tables_query).fetchall()]

        if temp_tables:
            logger.info(f"Found {len(temp_tables)} temporary tables to clean up:")

            for table_name in temp_tables:
                logger.info(f"  - Dropping temporary table: {table_name}")
                connection.execute(text(f"DROP TABLE IF EXISTS {source_schema}.{table_name}"))
                logger.info(f"    [OK] Removed temporary table {table_name}")

        # Get final table stats for the report (only s3_processed tables)
        all_tables_query = text(f"""
            SELECT 
                tablename, 
                (SELECT COUNT(*) FROM information_schema.columns WHERE table_schema = '{source_schema}' AND table_name = tablename) as column_count,
                pg_relation_size(quote_ident(tablename)) as table_size
            FROM 
                pg_tables 
            WHERE 
                schemaname = '{source_schema}' AND
                tablename NOT LIKE 'pg_%' AND
                tablename NOT LIKE 'sql_%'
            ORDER BY 
                tablename
        """)

        all_tables = connection.execute(all_tables_query).fetchall()

        tables_with_counts = []

        for table_name, column_count, table_size in all_tables:
            # Skip tables that are not part of our application
            if ("_" in table_name and not table_name.startswith("filter_") and 
                not table_name == "quarterly_data" and
                not table_name.startswith("usaspending_")):
                continue

            row_count = connection.execute(text(f"SELECT COUNT(*) FROM {source_schema}.{table_name}")).scalar()
            tables_with_counts.append({
                "name": table_name,
                "row_count": row_count,
                "column_count": column_count,
                "size_bytes": table_size
            })

        # Store results for application tables
        app_tables = []
        for table in tables_with_counts:
            logger.info(f"  - {table['name']}: {table['row_count']:,} rows")
            app_tables.append({
                "name": table["name"],
                "row_count": table["row_count"]
            })
    
    # Calculate elapsed time
    elapsed_time = time.time() - start_time
    minutes = int(elapsed_time // 60)
    seconds = int(elapsed_time % 60)
    
    # Store results
    results["preprocessing_time_seconds"] = round(elapsed_time, 2)
    results["filter_tables"] = filter_tables
    results["app_tables"] = app_tables
    results["dependencies_count"] = dependency_count
    results["quarterly_periods"] = quarterly_count
    
    logger.info(f"\nData preprocessing complete! Total time: {minutes}m {seconds}s")
    logger.info("The application is now ready to run with optimal performance!")
    
    return results

# If run as a script, run preprocessing (and thus indexing) automatically
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)]
    )
    logger.info("Starting full transformation pipeline (indexing + preprocessing)...")
    preprocess_data_optimized()
    logger.info("Transformation pipeline complete.")
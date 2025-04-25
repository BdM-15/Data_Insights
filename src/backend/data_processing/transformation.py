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

# Function to preprocess the data using direct SQL for better performance
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
    
    # Determine which table to use as the source
    with engine.connect() as connection:
        deduplicated_exists = connection.execute(text(
            "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'usaprime_deduplicated')"
        )).scalar()
        
        if deduplicated_exists:
            source_table = "usaprime_deduplicated"
            logger.info(f"Using {source_table} as source for transformation")
        else:
            source_table = "usaprime_cleaned"
            logger.info(f"Using {source_table} as source for transformation")
    
    logger.info("Starting optimized data preprocessing for app performance...")
    
    # Check if primary table exists and has data
    with engine.connect() as connection:
        table_exists = connection.execute(text(
            f"SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = '{source_table}')"
        )).scalar()
        
        if not table_exists:
            logger.error(f"Error: {source_table} table does not exist. Run data cleansing first.")
            return {"error": f"{source_table} table not found"}
        
        # Get row count
        row_count = connection.execute(text(f"SELECT COUNT(*) FROM {source_table}")).scalar()
        
        if row_count == 0:
            logger.error(f"Error: {source_table} table is empty. Check data cleansing process.")
            return {"error": f"{source_table} table is empty"}
        
        logger.info(f"Found {source_table} table with {row_count:,} rows.")
    
    with engine.connect() as connection:
        # Create distinct filter value tables for the UI
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
            table_name = f"filter_values_{column}"
            
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
        
        # Precompute dependent filter relationships (e.g., agency → sub-agency → office)
        logger.info("\nPrecomputing dependent filter relationships using direct SQL...")
        
        # Drop existing table if it exists
        connection.execute(text("DROP TABLE IF EXISTS filter_dependencies"))
        
        # Create the filter dependencies table for hierarchical filters
        logger.info("  - Creating agency to sub-agency dependencies...")
        create_dependencies_query = text(f"""
            CREATE TABLE filter_dependencies AS
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
            INSERT INTO filter_dependencies
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
        dependency_count = connection.execute(text("SELECT COUNT(*) FROM filter_dependencies")).scalar()
        
        logger.info(f"  [OK] Created filter_dependencies table with {dependency_count} relationships.")
        
        # Confirm it exists
        filter_dependencies_exists = connection.execute(text(
            "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'filter_dependencies')"
        )).scalar()
        
        if filter_dependencies_exists:
            logger.info(f"    [OK] Confirmed filter_dependencies table exists in database")
        else:
            logger.error("Error: filter_dependencies table was not created successfully")
        
        # Create quarterly aggregated data for timeline charts
        logger.info("\nPre-aggregating data for visualizations using direct SQL...")
        
        # Create quarterly data table
        logger.info("  - Creating quarterly_data table with fiscal calculations...")
        
        # Drop existing table if it exists
        connection.execute(text("DROP TABLE IF EXISTS quarterly_data"))
        
        # Create the quarterly data table with fiscal year and quarter calculations
        create_quarterly_query = text(f"""
            CREATE TABLE quarterly_data AS
            SELECT 
                action_date_fiscal_year as fiscal_year,
                action_date_fiscal_quarter as fiscal_quarter,
                CONCAT(action_date_fiscal_year, ' Q', action_date_fiscal_quarter) as fiscal_period,
                COUNT(*) as award_count,
                SUM(federal_action_obligation) as total_obligation,
                COUNT(DISTINCT recipient_name) as vendor_count,
                COUNT(DISTINCT contract_award_unique_key) as unique_award_count,
                COUNT(DISTINCT naics_code) as unique_naics_count
            FROM 
                {source_table}
            WHERE 
                action_date_fiscal_year IS NOT NULL AND
                action_date_fiscal_quarter IS NOT NULL
            GROUP BY 
                action_date_fiscal_year, action_date_fiscal_quarter
            ORDER BY 
                action_date_fiscal_year, action_date_fiscal_quarter
        """)
        
        connection.execute(create_quarterly_query)
        connection.commit()
        
        # Get quarterly count
        quarterly_count = connection.execute(text("SELECT COUNT(*) FROM quarterly_data")).scalar()
        
        logger.info(f"  [OK] Created quarterly_data table with {quarterly_count} rows.")
        
        # Confirm it exists
        quarterly_data_exists = connection.execute(text(
            "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'quarterly_data')"
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
            "quarterly_data",
            "filter_dependencies"
        ] + [table["name"] for table in filter_tables]
        
        for table in tables_to_analyze:
            connection.execute(text(f"ANALYZE {table}"))
            logger.info(f"  [OK] Analyzed {table} table for optimal query performance")
        
        # Clean up any temporary tables
        temp_tables_query = text("""
            SELECT tablename FROM pg_tables 
            WHERE tablename LIKE 'temp_%' 
            AND schemaname = 'public'
        """)
        
        temp_tables = [row[0] for row in connection.execute(temp_tables_query).fetchall()]
        
        if temp_tables:
            logger.info(f"Found {len(temp_tables)} temporary tables to clean up:")
            
            for table_name in temp_tables:
                logger.info(f"  - Dropping temporary table: {table_name}")
                connection.execute(text(f"DROP TABLE IF EXISTS {table_name}"))
                logger.info(f"    [OK] Removed temporary table {table_name}")
        
        # Get final table stats for the report
        all_tables_query = text("""
            SELECT 
                tablename, 
                (SELECT COUNT(*) FROM information_schema.columns WHERE table_name = tablename) as column_count,
                pg_relation_size(quote_ident(tablename)) as table_size
            FROM 
                pg_tables 
            WHERE 
                schemaname = 'public' AND
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
                not table_name.startswith("usaprime_")):
                continue
                
            row_count = connection.execute(text(f"SELECT COUNT(*) FROM {table_name}")).scalar()
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
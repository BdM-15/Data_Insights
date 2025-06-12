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
from logging.handlers import RotatingFileHandler
from datetime import datetime

# Robust logging setup for transformation.log
def setup_transformation_logging():
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, "transformation.log")
    logger = logging.getLogger("transformation")
    logger.setLevel(logging.INFO)
    # Remove existing handlers
    logger.handlers.clear()
    # File handler
    fh = RotatingFileHandler(log_file, maxBytes=10*1024*1024, backupCount=5)
    fh.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    # Console handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    logger.addHandler(fh)
    logger.addHandler(ch)
    logger.propagate = False
    return logger

logger = setup_transformation_logging()
# Function to create indexes for deduplicated tables in s3_processed
def clean_s3_processed_schema():
    """
    Drop all tables, indexes, and materialized views in s3_processed except usaspending_* tables.
    """
    with engine.connect() as connection:
        logger.info("Starting schema cleanup for s3_processed (preserving usaspending_* tables)...")
        # Drop materialized views
        mviews = connection.execute(text("""
            SELECT matviewname FROM pg_matviews WHERE schemaname = 's3_processed'
        """)).fetchall()
        for (mv,) in mviews:
            if not mv.startswith("usaspending_"):
                try:
                    connection.execute(text(f'DROP MATERIALIZED VIEW IF EXISTS s3_processed.{mv} CASCADE'))
                    logger.info(f"Dropped materialized view: {mv}")
                except Exception as e:
                    logger.error(f"Failed to drop materialized view {mv}: {e}")

        # Drop tables
        tables = connection.execute(text("""
            SELECT tablename FROM pg_tables WHERE schemaname = 's3_processed'
        """)).fetchall()
        for (tbl,) in tables:
            if not tbl.startswith("usaspending_"):
                try:
                    connection.execute(text(f'DROP TABLE IF EXISTS s3_processed.{tbl} CASCADE'))
                    logger.info(f"Dropped table: {tbl}")
                except Exception as e:
                    logger.error(f"Failed to drop table {tbl}: {e}")

        # Drop indexes (indexes on usaspending_* will be recreated by transformation)
        indexes = connection.execute(text("""
            SELECT indexname FROM pg_indexes WHERE schemaname = 's3_processed'
        """)).fetchall()
        for (idx,) in indexes:
            if not (idx.startswith("usaspending_") or idx.startswith("s3p_idx_")):
                try:
                    connection.execute(text(f'DROP INDEX IF EXISTS s3_processed.{idx} CASCADE'))
                    logger.info(f"Dropped index: {idx}")
                except Exception as e:
                    logger.error(f"Failed to drop index {idx}: {e}")

        logger.info("Schema cleanup complete. Only usaspending_* tables remain.")

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
    logger.info("[PERF] Ensuring performance indexes exist on s3_processed.usaspending_prime_awards...")
    with engine.connect() as connection:
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

        # --- Enterprise filter performance: ensure B-tree indexes for filter tables ---
        with connection.begin():
            connection.execute(text(
                "CREATE INDEX IF NOT EXISTS s3p_idx_prime_naics_code ON s3_processed.usaspending_prime_awards (naics_code)"))
            logger.info("  [OK] Index on naics_code")
            connection.execute(text(
                "CREATE INDEX IF NOT EXISTS s3p_idx_prime_parent_agency ON s3_processed.usaspending_prime_awards (parent_award_agency_name)"))
            logger.info("  [OK] Index on parent_award_agency_name")

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
                {"name": "s3p_idx_funding_sub_agency", "columns": "funding_sub_agency_name"},                # Additional performance indexes for app processors
                {"name": "s3p_idx_quarterly_trends", "columns": "action_date_fiscal_year, action_date"},
                {"name": "s3p_idx_agency_analysis", "columns": "parent_award_agency_name, funding_sub_agency_name"},
                {"name": "s3p_idx_contract_vehicle", "columns": "type_of_contract_pricing, extent_competed"},
                {"name": "s3p_idx_set_aside", "columns": "type_of_set_aside"},
                {"name": "s3p_idx_psc_naics", "columns": "product_or_service_code, naics_code"},
                {"name": "s3p_idx_recipient_parent", "columns": "recipient_parent_name"},
                {"name": "s3p_idx_action_date_year", "columns": "action_date_fiscal_year"},
                # Composite indexes for competitive analysis
                {"name": "s3p_idx_competitive_position", "columns": "recipient_name, federal_action_obligation"},
                {"name": "s3p_idx_agency_contractor", "columns": "parent_award_agency_name, recipient_name"},
                
                # NEW: Additional specialized indexes for app_processor optimization
                  # Date range filtering optimization
                {"name": "s3p_idx_date_range_filter", "columns": "action_date, modification_number"},
                {"name": "s3p_idx_fiscal_period_filter", "columns": "action_date_fiscal_year, modification_number"},
                
                # Award summary query optimization
                {"name": "s3p_idx_award_summary", "columns": "modification_number, federal_action_obligation, contract_award_unique_key"},
                {"name": "s3p_idx_award_summary_naics", "columns": "naics_code, modification_number, federal_action_obligation"},
                {"name": "s3p_idx_award_summary_agency", "columns": "parent_award_agency_name, modification_number, federal_action_obligation"},
                {"name": "s3p_idx_award_summary_psc", "columns": "product_or_service_code, modification_number, federal_action_obligation"},
                
                # Top agencies query optimization
                {"name": "s3p_idx_top_agencies_count", "columns": "parent_award_agency_name, modification_number"},
                {"name": "s3p_idx_top_agencies_obligation", "columns": "parent_award_agency_name, federal_action_obligation"},
                {"name": "s3p_idx_top_agencies_filtered", "columns": "parent_award_agency_name, naics_code, modification_number"},
                  # Quarterly trends optimization
                {"name": "s3p_idx_quarterly_fiscal_calc", "columns": "action_date, federal_action_obligation, modification_number"},
                {"name": "s3p_idx_quarterly_grouping", "columns": "action_date_fiscal_year, federal_action_obligation"},
                
                # Agency obligation ratio optimization
                {"name": "s3p_idx_agency_ratio_calc", "columns": "parent_award_agency_name, modification_number, federal_action_obligation"},
                {"name": "s3p_idx_agency_ratio_filtered", "columns": "parent_award_agency_name, naics_code, federal_action_obligation"},
                
                # Competition analysis optimization
                {"name": "s3p_idx_competition_treemap", "columns": "recipient_parent_name, funding_sub_agency_name, federal_action_obligation"},
                {"name": "s3p_idx_competition_landscape", "columns": "recipient_name, modification_number, federal_action_obligation"},
                
                # Expiring contracts optimization
                {"name": "s3p_idx_expiring_contracts", "columns": "modification_number, period_of_performance_current_end_date"},
                {"name": "s3p_idx_expiring_alt_dates", "columns": "modification_number, action_date"},  # Fallback for estimated dates
                
                # Filter combination optimization for complex queries
                {"name": "s3p_idx_multi_filter_naics_agency", "columns": "naics_code, parent_award_agency_name, action_date"},
                {"name": "s3p_idx_multi_filter_psc_agency", "columns": "product_or_service_code, parent_award_agency_name, action_date"},
                {"name": "s3p_idx_multi_filter_contractor_agency", "columns": "recipient_name, parent_award_agency_name, action_date"},
                
                # Contract vehicle analysis optimization
                {"name": "s3p_idx_contract_vehicle_combo", "columns": "type_of_contract_pricing, extent_competed, type_of_set_aside"},
                {"name": "s3p_idx_contract_competition", "columns": "extent_competed, federal_action_obligation"},
                  # Performance end date alternatives (for contracts without proper end dates)
                {"name": "s3p_idx_performance_dates", "columns": "period_of_performance_current_end_date, modification_number"},
                {"name": "s3p_idx_alt_end_dates", "columns": "period_of_performance_current_end_date, modification_number"},
                  # Note: transaction_description removed due to PostgreSQL btree size limit (field too large for indexing)
                
                # Small business and set-aside analysis
                {"name": "s3p_idx_set_aside_analysis", "columns": "type_of_set_aside, federal_action_obligation, modification_number"},
                  # NAICS and PSC code performance
                {"name": "s3p_idx_naics_performance", "columns": "naics_code, federal_action_obligation, modification_number"},
                {"name": "s3p_idx_psc_performance", "columns": "product_or_service_code, federal_action_obligation, modification_number"}
        ]
        
        # Create prime table indexes individually with error handling
        successful_indexes = 0
        failed_indexes = 0
        for idx in prime_indexes:
            logger.info(f"Ensuring index {idx['name']} on {prime_table}({idx['columns']})...")
            try:
                # Use individual transactions for each index to prevent one failure from rolling back all
                with connection.begin():
                    drop_index_if_exists(idx["name"])
                    connection.execute(text(f'CREATE INDEX {idx["name"]} ON s3_processed.usaspending_prime_awards ({idx["columns"]})'))
                logger.info(f"  [OK] Created index {idx['name']} on {prime_table}")
                successful_indexes += 1
            except Exception as e:
                logger.error(f"  [ERROR] Failed to create index {idx['name']} on {prime_table}: {e}")
                failed_indexes += 1
                # Continue with next index instead of failing entire process
                continue

        logger.info(f"Prime table index creation complete: {successful_indexes} successful, {failed_indexes} failed")

        sub_table = 's3_processed.usaspending_subawards'
        sub_indexes = [
            {"name": "s3p_idx_sub_prime_award_unique_key", "columns": "prime_award_unique_key"},
            {"name": "s3p_idx_sub_subawardee_uei", "columns": "subawardee_uei"},
            {"name": "s3p_idx_sub_subaward_action_date", "columns": "subaward_action_date"},
            {"name": "s3p_idx_sub_composite_key", "columns": "prime_award_unique_key, subaward_number, subaward_action_date, subaward_amount"}
        ]
        
        # Create subaward indexes individually with error handling  
        for idx in sub_indexes:
            logger.info(f"Ensuring index {idx['name']} on {sub_table}({idx['columns']})...")
            try:
                # Use individual transactions for each index to prevent one failure from rolling back all
                with connection.begin():
                    drop_index_if_exists(idx["name"])
                    connection.execute(text(f'CREATE INDEX {idx["name"]} ON s3_processed.usaspending_subawards ({idx["columns"]})'))
                logger.info(f"  [OK] Created index {idx['name']} on {sub_table}")
                successful_indexes += 1
            except Exception as e:
                logger.error(f"  [ERROR] Failed to create index {idx['name']} on {sub_table}: {e}")
                failed_indexes += 1
                continue

        logger.info(f"[OK] Index creation complete: {successful_indexes} successful, {failed_indexes} failed total.")

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


def create_materialized_views():
    """
    Create materialized views for high-traffic dashboard queries to provide instant load times.
    These views should be refreshed after each ETL/transform run to keep analytics up to date.
    """
    with engine.connect() as connection:
        with connection.begin():
            logger.info("\nCreating materialized views for high-traffic queries...")
            
            # 1. Top Competitors by Market Share - Most accessed query in competitive analysis
            logger.info("  - Creating mv_top_competitors_market_share...")
            connection.execute(text("DROP MATERIALIZED VIEW IF EXISTS s3_processed.mv_top_competitors_market_share"))
            
            mv_competitors_query = text("""
                CREATE MATERIALIZED VIEW s3_processed.mv_top_competitors_market_share AS
                WITH recipient_totals AS (
                    SELECT
                        recipient_parent_name,
                        recipient_name,
                        SUM(federal_action_obligation) AS total_obligation,
                        COUNT(*) FILTER (WHERE modification_number = '0') AS award_count,
                        COUNT(*) AS total_transactions
                    FROM s3_processed.usaspending_prime_awards
                    WHERE federal_action_obligation > 0
                    GROUP BY recipient_parent_name, recipient_name
                ),
                market_totals AS (
                    SELECT SUM(total_obligation) AS market_total_obligation,
                           SUM(award_count) AS market_total_awards
                    FROM recipient_totals
                )
                SELECT 
                    rt.recipient_parent_name,
                    rt.recipient_name,
                    rt.total_obligation,
                    rt.award_count,
                    rt.total_transactions,
                    ROUND((rt.total_obligation / mt.market_total_obligation * 100)::numeric, 2) AS market_share,
                    ROUND((rt.award_count::numeric / mt.market_total_awards * 100)::numeric, 2) AS win_rate,
                    RANK() OVER (ORDER BY rt.total_obligation DESC) AS market_rank
                FROM recipient_totals rt
                CROSS JOIN market_totals mt
                WHERE rt.total_obligation > 0
                ORDER BY rt.total_obligation DESC;
            """)
            
            connection.execute(mv_competitors_query)
            connection.execute(text("CREATE INDEX ON s3_processed.mv_top_competitors_market_share (market_rank)"))
            connection.execute(text("CREATE INDEX ON s3_processed.mv_top_competitors_market_share (recipient_name)"))
            logger.info("    [OK] Created mv_top_competitors_market_share with indexes")
            
            # 2. Treemap Competitive Landscape - Second most accessed query
            logger.info("  - Creating mv_treemap_competitive_landscape...")
            connection.execute(text("DROP MATERIALIZED VIEW IF EXISTS s3_processed.mv_treemap_competitive_landscape"))
            
            mv_treemap_query = text("""
                CREATE MATERIALIZED VIEW s3_processed.mv_treemap_competitive_landscape AS
                WITH grouped_data AS (
                    SELECT
                        recipient_parent_name,
                        recipient_name,
                        funding_sub_agency_name,
                        -- Use MAX for better performance than MODE()
                        MAX(CASE WHEN transaction_description IS NOT NULL AND transaction_description != '' 
                                 THEN transaction_description 
                                 ELSE 'All Contracts' END) AS transaction_description,
                        SUM(federal_action_obligation) AS federal_action_obligation,
                        COUNT(*) FILTER (WHERE modification_number = '0') AS award_count,
                        COUNT(*) AS total_transactions
                    FROM s3_processed.usaspending_prime_awards
                    WHERE federal_action_obligation > 0
                    GROUP BY recipient_parent_name, recipient_name, funding_sub_agency_name
                ),
                totals AS (
                    SELECT SUM(federal_action_obligation) AS total_obligations,
                           SUM(award_count) AS total_awards
                    FROM grouped_data
                )
                SELECT 
                    gd.recipient_parent_name,
                    gd.recipient_name,
                    gd.funding_sub_agency_name,
                    gd.transaction_description,
                    gd.federal_action_obligation,
                    gd.award_count,
                    gd.total_transactions,
                    ROUND((gd.federal_action_obligation / t.total_obligations * 100)::numeric, 2) AS market_share,
                    ROUND((gd.award_count::numeric / t.total_awards * 100)::numeric, 2) AS win_rate,
                    ROW_NUMBER() OVER (ORDER BY gd.federal_action_obligation DESC) AS obligation_rank
                FROM grouped_data gd
                CROSS JOIN totals t
                WHERE gd.federal_action_obligation > 0                ORDER BY gd.federal_action_obligation DESC;
            """)
            connection.execute(mv_treemap_query)
            connection.execute(text("CREATE INDEX ON s3_processed.mv_treemap_competitive_landscape (obligation_rank)"))
            connection.execute(text("CREATE INDEX ON s3_processed.mv_treemap_competitive_landscape (recipient_parent_name, recipient_name, funding_sub_agency_name)"))
            logger.info("    [OK] Created mv_treemap_competitive_landscape with indexes")
            
            # 3. Quarterly Trends Analysis - For timeline visualizations
            logger.info("  - Creating mv_quarterly_trends_analysis...")
            connection.execute(text("DROP MATERIALIZED VIEW IF EXISTS s3_processed.mv_quarterly_trends_analysis"))
            mv_quarterly_query = text("""
                CREATE MATERIALIZED VIEW s3_processed.mv_quarterly_trends_analysis AS
                WITH quarterly_data AS (
                    SELECT 
                        -- Calculate fiscal year from action_date (Oct 1 - Sep 30)
                        CASE 
                            WHEN EXTRACT(MONTH FROM action_date) >= 10 THEN EXTRACT(YEAR FROM action_date) + 1
                            ELSE EXTRACT(YEAR FROM action_date)
                        END as calculated_fiscal_year,
                        -- Calculate fiscal quarter from action_date
                        CASE 
                            WHEN EXTRACT(MONTH FROM action_date) IN (1, 2, 3) THEN 2
                            WHEN EXTRACT(MONTH FROM action_date) IN (4, 5, 6) THEN 3
                            WHEN EXTRACT(MONTH FROM action_date) IN (7, 8, 9) THEN 4
                            WHEN EXTRACT(MONTH FROM action_date) IN (10, 11, 12) THEN 1
                        END as fiscal_quarter,
                        modification_number,
                        federal_action_obligation,
                        recipient_name,
                        parent_award_agency_name,
                        naics_code,
                        contract_award_unique_key,
                        type_of_set_aside,
                        extent_competed
                    FROM s3_processed.usaspending_prime_awards
                    WHERE action_date IS NOT NULL
                )
                SELECT 
                    calculated_fiscal_year as action_date_fiscal_year,
                    fiscal_quarter,
                    CONCAT(calculated_fiscal_year, ' Q', fiscal_quarter) AS fiscal_period,
                    COUNT(*) as transaction_count,
                    COUNT(*) FILTER (WHERE modification_number = '0') as award_count,
                    SUM(federal_action_obligation) as total_obligation,
                    AVG(federal_action_obligation) as avg_obligation,
                    COUNT(DISTINCT recipient_name) as unique_contractors,
                    COUNT(DISTINCT parent_award_agency_name) as unique_agencies,
                    COUNT(DISTINCT naics_code) as unique_naics_codes,                    
                    COUNT(DISTINCT contract_award_unique_key) as unique_awards,
                    -- Small business metrics (fixed set aside value)
                    COUNT(*) FILTER (WHERE type_of_set_aside IS NOT NULL AND type_of_set_aside != 'NO SET ASIDE USED') as set_aside_count,
                    SUM(federal_action_obligation) FILTER (WHERE type_of_set_aside IS NOT NULL AND type_of_set_aside != 'NO SET ASIDE USED') as set_aside_obligation,
                    -- Competition metrics
                    COUNT(*) FILTER (WHERE extent_competed = 'FULL AND OPEN COMPETITION') as full_competition_count,
                    SUM(federal_action_obligation) FILTER (WHERE extent_competed = 'FULL AND OPEN COMPETITION') as full_competition_obligation                FROM quarterly_data
                GROUP BY calculated_fiscal_year, fiscal_quarter
                ORDER BY calculated_fiscal_year, fiscal_quarter;
            """)
            connection.execute(mv_quarterly_query)
            connection.execute(text("CREATE INDEX ON s3_processed.mv_quarterly_trends_analysis (action_date_fiscal_year, fiscal_quarter)"))
            connection.execute(text("CREATE INDEX ON s3_processed.mv_quarterly_trends_analysis (fiscal_period)"))
            logger.info("    [OK] Created mv_quarterly_trends_analysis with indexes")
            
            # 4. Agency Analysis Summary - For agency intelligence tab
            logger.info("  - Creating mv_agency_analysis_summary...")
            connection.execute(text("DROP MATERIALIZED VIEW IF EXISTS s3_processed.mv_agency_analysis_summary"))
            
            mv_agency_query = text("""
                CREATE MATERIALIZED VIEW s3_processed.mv_agency_analysis_summary AS
                WITH agency_stats AS (
                    SELECT 
                        parent_award_agency_name,
                        funding_sub_agency_name,
                        COUNT(*) as transaction_count,
                        COUNT(*) FILTER (WHERE modification_number = '0') as award_count,
                        SUM(federal_action_obligation) as total_obligation,
                        AVG(federal_action_obligation) as avg_obligation,
                        COUNT(DISTINCT recipient_name) as unique_contractors,
                        COUNT(DISTINCT naics_code) as unique_naics_codes,
                        COUNT(DISTINCT product_or_service_code) as unique_psc_codes,
                        -- Top NAICS by obligation
                        MODE() WITHIN GROUP (ORDER BY naics_code) FILTER (WHERE naics_code IS NOT NULL) as top_naics_code,                        -- Competition metrics
                        COUNT(*) FILTER (WHERE extent_competed = 'FULL AND OPEN COMPETITION') as full_competition_count,
                        SUM(federal_action_obligation) FILTER (WHERE extent_competed = 'FULL AND OPEN COMPETITION') as full_competition_obligation,
                        -- Set aside metrics (fixed set aside value)
                        COUNT(*) FILTER (WHERE type_of_set_aside IS NOT NULL AND type_of_set_aside != 'NO SET ASIDE USED') as set_aside_count,
                        SUM(federal_action_obligation) FILTER (WHERE type_of_set_aside IS NOT NULL AND type_of_set_aside != 'NO SET ASIDE USED') as set_aside_obligation,
                        -- Contract vehicle metrics
                        MODE() WITHIN GROUP (ORDER BY type_of_contract_pricing) FILTER (WHERE type_of_contract_pricing IS NOT NULL) as primary_contract_type
                    FROM s3_processed.usaspending_prime_awards
                    WHERE parent_award_agency_name IS NOT NULL 
                        AND funding_sub_agency_name IS NOT NULL
                        AND federal_action_obligation > 0
                    GROUP BY parent_award_agency_name, funding_sub_agency_name
                )
                SELECT 
                    parent_award_agency_name,
                    funding_sub_agency_name,
                    transaction_count,
                    award_count,
                    total_obligation,
                    ROUND(avg_obligation::numeric, 2) as avg_obligation,
                    unique_contractors,
                    unique_naics_codes,
                    unique_psc_codes,
                    top_naics_code,
                    full_competition_count,
                    ROUND((full_competition_obligation / total_obligation * 100)::numeric, 2) as competition_percentage,
                    set_aside_count,
                    ROUND((set_aside_obligation / total_obligation * 100)::numeric, 2) as set_aside_percentage,
                    primary_contract_type,
                    RANK() OVER (PARTITION BY parent_award_agency_name ORDER BY total_obligation DESC) as sub_agency_rank,
                    RANK() OVER (ORDER BY total_obligation DESC) as overall_rank
                FROM agency_stats
                ORDER BY total_obligation DESC;
            """)
            
            connection.execute(mv_agency_query)
            connection.execute(text("CREATE INDEX ON s3_processed.mv_agency_analysis_summary (parent_award_agency_name)"))
            connection.execute(text("CREATE INDEX ON s3_processed.mv_agency_analysis_summary (funding_sub_agency_name)"))
            connection.execute(text("CREATE INDEX ON s3_processed.mv_agency_analysis_summary (overall_rank)"))
            logger.info("    [OK] Created mv_agency_analysis_summary with indexes")
            
            # 5. Contract Vehicle Analysis - For contract vehicle tab performance
            logger.info("  - Creating mv_contract_vehicle_analysis...")
            connection.execute(text("DROP MATERIALIZED VIEW IF EXISTS s3_processed.mv_contract_vehicle_analysis"))
            
            mv_vehicle_query = text("""
                CREATE MATERIALIZED VIEW s3_processed.mv_contract_vehicle_analysis AS
                SELECT 
                    type_of_contract_pricing,
                    extent_competed,
                    type_of_set_aside,
                    COUNT(*) as transaction_count,
                    COUNT(*) FILTER (WHERE modification_number = '0') as award_count,
                    SUM(federal_action_obligation) as total_obligation,
                    AVG(federal_action_obligation) as avg_obligation,
                    COUNT(DISTINCT recipient_name) as unique_contractors,
                    COUNT(DISTINCT parent_award_agency_name) as unique_agencies,                    -- Success rate calculation (base awards vs total transactions)
                    ROUND((COUNT(*) FILTER (WHERE modification_number = '0')::numeric / COUNT(*) * 100)::numeric, 2) as success_rate,
                    -- Competition intensity
                    CASE 
                        WHEN extent_competed = 'FULL AND OPEN COMPETITION' THEN 'High'
                        WHEN extent_competed LIKE '%LIMITED%' THEN 'Medium'
                        WHEN extent_competed = 'NOT COMPETED' THEN 'Low'
                        ELSE 'Unknown'
                    END as competition_level
                FROM s3_processed.usaspending_prime_awards
                WHERE type_of_contract_pricing IS NOT NULL 
                    AND extent_competed IS NOT NULL
                    AND federal_action_obligation > 0
                GROUP BY type_of_contract_pricing, extent_competed, type_of_set_aside
                ORDER BY total_obligation DESC;
            """)
            
            connection.execute(mv_vehicle_query)
            connection.execute(text("CREATE INDEX ON s3_processed.mv_contract_vehicle_analysis (type_of_contract_pricing)"))
            connection.execute(text("CREATE INDEX ON s3_processed.mv_contract_vehicle_analysis (extent_competed)"))
            connection.execute(text("CREATE INDEX ON s3_processed.mv_contract_vehicle_analysis (competition_level)"))
            logger.info("    [OK] Created mv_contract_vehicle_analysis with indexes")

            # 6. NEW: App Processor Specific Optimizations
            
            # 6a. Award Summary Metrics - For get_award_summary() performance
            logger.info("  - Creating mv_award_summary_metrics...")
            connection.execute(text("DROP MATERIALIZED VIEW IF EXISTS s3_processed.mv_award_summary_metrics"))
            
            mv_summary_query = text("""
                CREATE MATERIALIZED VIEW s3_processed.mv_award_summary_metrics AS
                SELECT 
                    -- Global metrics (no filters)
                    'ALL' as filter_category,
                    'ALL' as filter_value,
                    SUM(federal_action_obligation) AS total_obligations,
                    COUNT(*) FILTER (WHERE modification_number = '0') AS total_award_actions,
                    CASE WHEN COUNT(*) FILTER (WHERE modification_number = '0') > 0
                         THEN SUM(federal_action_obligation) / COUNT(*) FILTER (WHERE modification_number = '0')
                         ELSE 0 END AS avg_award_value,
                    COUNT(DISTINCT contract_award_unique_key) FILTER (WHERE modification_number = '0') AS active_contracts
                FROM s3_processed.usaspending_prime_awards
                
                UNION ALL
                
                -- By NAICS code
                SELECT 
                    'NAICS' as filter_category,
                    naics_code as filter_value,
                    SUM(federal_action_obligation) AS total_obligations,
                    COUNT(*) FILTER (WHERE modification_number = '0') AS total_award_actions,
                    CASE WHEN COUNT(*) FILTER (WHERE modification_number = '0') > 0
                         THEN SUM(federal_action_obligation) / COUNT(*) FILTER (WHERE modification_number = '0')
                         ELSE 0 END AS avg_award_value,
                    COUNT(DISTINCT contract_award_unique_key) FILTER (WHERE modification_number = '0') AS active_contracts
                FROM s3_processed.usaspending_prime_awards
                WHERE naics_code IS NOT NULL
                GROUP BY naics_code
                
                UNION ALL
                
                -- By Agency
                SELECT 
                    'AGENCY' as filter_category,
                    parent_award_agency_name as filter_value,
                    SUM(federal_action_obligation) AS total_obligations,
                    COUNT(*) FILTER (WHERE modification_number = '0') AS total_award_actions,
                    CASE WHEN COUNT(*) FILTER (WHERE modification_number = '0') > 0
                         THEN SUM(federal_action_obligation) / COUNT(*) FILTER (WHERE modification_number = '0')
                         ELSE 0 END AS avg_award_value,
                    COUNT(DISTINCT contract_award_unique_key) FILTER (WHERE modification_number = '0') AS active_contracts
                FROM s3_processed.usaspending_prime_awards
                WHERE parent_award_agency_name IS NOT NULL
                GROUP BY parent_award_agency_name
                
                UNION ALL
                
                -- By PSC
                SELECT 
                    'PSC' as filter_category,
                    product_or_service_code as filter_value,
                    SUM(federal_action_obligation) AS total_obligations,
                    COUNT(*) FILTER (WHERE modification_number = '0') AS total_award_actions,
                    CASE WHEN COUNT(*) FILTER (WHERE modification_number = '0') > 0
                         THEN SUM(federal_action_obligation) / COUNT(*) FILTER (WHERE modification_number = '0')
                         ELSE 0 END AS avg_award_value,
                    COUNT(DISTINCT contract_award_unique_key) FILTER (WHERE modification_number = '0') AS active_contracts
                FROM s3_processed.usaspending_prime_awards
                WHERE product_or_service_code IS NOT NULL
                GROUP BY product_or_service_code;
            """)
            
            connection.execute(mv_summary_query)
            connection.execute(text("CREATE INDEX ON s3_processed.mv_award_summary_metrics (filter_category, filter_value)"))
            logger.info("    [OK] Created mv_award_summary_metrics with indexes")

            # 6b. Top Agencies Materialized View - For get_top_agencies() performance
            logger.info("  - Creating mv_top_agencies...")
            connection.execute(text("DROP MATERIALIZED VIEW IF EXISTS s3_processed.mv_top_agencies"))
            
            mv_agencies_query = text("""
                CREATE MATERIALIZED VIEW s3_processed.mv_top_agencies AS
                WITH agency_metrics AS (
                    SELECT
                        parent_award_agency_name,
                        COUNT(*) FILTER (WHERE modification_number = '0') AS award_count,
                        SUM(federal_action_obligation) AS federal_action_obligation,
                        COUNT(*) AS total_transactions,
                        COUNT(DISTINCT recipient_name) AS unique_contractors,
                        COUNT(DISTINCT naics_code) AS unique_naics_codes,
                        AVG(federal_action_obligation) AS avg_obligation,
                        -- NAICS filtering support
                        STRING_AGG(DISTINCT naics_code, ',' ORDER BY naics_code) AS all_naics_codes,
                        -- PSC filtering support  
                        STRING_AGG(DISTINCT product_or_service_code, ',' ORDER BY product_or_service_code) AS all_psc_codes
                    FROM s3_processed.usaspending_prime_awards
                    WHERE parent_award_agency_name IS NOT NULL
                    GROUP BY parent_award_agency_name
                )
                SELECT 
                    parent_award_agency_name,
                    award_count,
                    federal_action_obligation,
                    total_transactions,
                    unique_contractors,
                    unique_naics_codes,
                    ROUND(avg_obligation::numeric, 2) as avg_obligation,
                    all_naics_codes,
                    all_psc_codes,
                    -- Rankings
                    RANK() OVER (ORDER BY award_count DESC) AS rank_by_count,
                    RANK() OVER (ORDER BY federal_action_obligation DESC) AS rank_by_obligation,
                    -- Percentile rankings for better insights
                    PERCENT_RANK() OVER (ORDER BY award_count DESC) AS percentile_by_count,
                    PERCENT_RANK() OVER (ORDER BY federal_action_obligation DESC) AS percentile_by_obligation
                FROM agency_metrics
                ORDER BY federal_action_obligation DESC;
            """)
            
            connection.execute(mv_agencies_query)
            connection.execute(text("CREATE INDEX ON s3_processed.mv_top_agencies (rank_by_count)"))
            connection.execute(text("CREATE INDEX ON s3_processed.mv_top_agencies (rank_by_obligation)"))
            connection.execute(text("CREATE INDEX ON s3_processed.mv_top_agencies (parent_award_agency_name)"))
            logger.info("    [OK] Created mv_top_agencies with indexes")

            # 6c. Quarterly Trends Optimized - For get_quarterly_trends() performance
            logger.info("  - Creating mv_quarterly_trends_optimized...")
            connection.execute(text("DROP MATERIALIZED VIEW IF EXISTS s3_processed.mv_quarterly_trends_optimized"))
            
            mv_quarterly_opt_query = text("""
                CREATE MATERIALIZED VIEW s3_processed.mv_quarterly_trends_optimized AS
                WITH fiscal_calculations AS (
                    SELECT 
                        action_date,
                        federal_action_obligation,
                        modification_number,
                        parent_award_agency_name,
                        recipient_name,
                        naics_code,
                        product_or_service_code,
                        -- Pre-calculate fiscal year and quarter for performance
                        EXTRACT(YEAR FROM action_date + INTERVAL '3 months') AS fiscal_year,
                        EXTRACT(QUARTER FROM action_date + INTERVAL '3 months') AS fiscal_quarter
                    FROM s3_processed.usaspending_prime_awards
                    WHERE action_date IS NOT NULL
                ),
                quarterly_aggregates AS (
                    SELECT
                        fiscal_year,
                        fiscal_quarter,
                        CONCAT(fiscal_year, '-Q', fiscal_quarter) AS fiscal_period,
                        -- Overall metrics
                        COUNT(*) FILTER (WHERE modification_number = '0') AS award_count,
                        SUM(federal_action_obligation) AS total_obligation,
                        -- By agency breakdowns
                        parent_award_agency_name,
                        COUNT(*) FILTER (WHERE modification_number = '0' AND parent_award_agency_name IS NOT NULL) AS agency_award_count,
                        SUM(CASE WHEN parent_award_agency_name IS NOT NULL THEN federal_action_obligation ELSE 0 END) AS agency_obligation,
                        -- By NAICS breakdowns
                        naics_code,
                        COUNT(*) FILTER (WHERE modification_number = '0' AND naics_code IS NOT NULL) AS naics_award_count,
                        SUM(CASE WHEN naics_code IS NOT NULL THEN federal_action_obligation ELSE 0 END) AS naics_obligation
                    FROM fiscal_calculations
                    GROUP BY GROUPING SETS (
                        (fiscal_year, fiscal_quarter, fiscal_period),
                        (fiscal_year, fiscal_quarter, fiscal_period, parent_award_agency_name),
                        (fiscal_year, fiscal_quarter, fiscal_period, naics_code)
                    )
                )
                SELECT
                    fiscal_year,
                    fiscal_quarter,
                    fiscal_period,
                    parent_award_agency_name,
                    naics_code,
                    COALESCE(award_count, agency_award_count, naics_award_count, 0) AS award_count,
                    COALESCE(total_obligation, agency_obligation, naics_obligation, 0) AS total_obligation,
                    -- Calculate running totals by fiscal year
                    SUM(COALESCE(award_count, agency_award_count, naics_award_count, 0)) 
                        OVER (PARTITION BY fiscal_year, parent_award_agency_name, naics_code 
                              ORDER BY fiscal_quarter 
                              ROWS UNBOUNDED PRECEDING) AS cumulative_award_count,
                    SUM(COALESCE(total_obligation, agency_obligation, naics_obligation, 0)) 
                        OVER (PARTITION BY fiscal_year, parent_award_agency_name, naics_code 
                              ORDER BY fiscal_quarter 
                              ROWS UNBOUNDED PRECEDING) AS cumulative_obligation
                FROM quarterly_aggregates
                ORDER BY fiscal_year, fiscal_quarter, parent_award_agency_name, naics_code;
            """)
            
            connection.execute(mv_quarterly_opt_query)
            connection.execute(text("CREATE INDEX ON s3_processed.mv_quarterly_trends_optimized (fiscal_year, fiscal_quarter)"))
            connection.execute(text("CREATE INDEX ON s3_processed.mv_quarterly_trends_optimized (parent_award_agency_name, fiscal_year, fiscal_quarter)"))
            connection.execute(text("CREATE INDEX ON s3_processed.mv_quarterly_trends_optimized (naics_code, fiscal_year, fiscal_quarter)"))
            logger.info("    [OK] Created mv_quarterly_trends_optimized with indexes")

            # 6d. Agency Obligation Ratio Optimized - For get_agency_obligation_ratio() performance
            logger.info("  - Creating mv_agency_obligation_ratio...")
            connection.execute(text("DROP MATERIALIZED VIEW IF EXISTS s3_processed.mv_agency_obligation_ratio"))
            
            mv_ratio_query = text("""
                CREATE MATERIALIZED VIEW s3_processed.mv_agency_obligation_ratio AS
                WITH agency_metrics AS (
                    SELECT
                        parent_award_agency_name,
                        COUNT(*) FILTER (WHERE modification_number = '0') AS award_count,
                        SUM(federal_action_obligation) AS federal_action_obligation,
                        -- Calculate avg award value directly in SQL
                        CASE WHEN COUNT(*) FILTER (WHERE modification_number = '0') > 0
                             THEN SUM(federal_action_obligation) / COUNT(*) FILTER (WHERE modification_number = '0')
                             ELSE 0 END AS avg_award_value,
                        -- Additional metrics for insights
                        COUNT(DISTINCT recipient_name) AS unique_contractors,
                        COUNT(DISTINCT naics_code) AS unique_naics_codes,
                        COUNT(DISTINCT product_or_service_code) AS unique_psc_codes,                        -- Competition metrics
                        COUNT(*) FILTER (WHERE modification_number = '0' AND extent_competed = 'FULL AND OPEN COMPETITION') AS competitive_awards,
                        SUM(federal_action_obligation) FILTER (WHERE extent_competed = 'FULL AND OPEN COMPETITION') AS competitive_obligation
                    FROM s3_processed.usaspending_prime_awards
                    WHERE parent_award_agency_name IS NOT NULL
                    GROUP BY parent_award_agency_name
                )
                SELECT
                    parent_award_agency_name,
                    award_count,
                    federal_action_obligation,
                    avg_award_value,
                    unique_contractors,
                    unique_naics_codes,
                    unique_psc_codes,
                    competitive_awards,
                    competitive_obligation,                    -- Pre-calculate scatter plot sizing and normalization
                    GREATEST(ABS(avg_award_value), 5) AS scatter_size_raw,
                    LN(award_count + 1) AS award_count_normalized,
                    LN(GREATEST(ABS(federal_action_obligation), 1)) AS obligation_normalized,
                    -- Percentile rankings for scatter plot positioning
                    PERCENT_RANK() OVER (ORDER BY award_count) AS award_count_percentile,
                    PERCENT_RANK() OVER (ORDER BY ABS(federal_action_obligation)) AS obligation_percentile,
                    PERCENT_RANK() OVER (ORDER BY avg_award_value) AS avg_value_percentile
                FROM agency_metrics
                WHERE award_count > 0  -- Filter out agencies with no base awards
                    AND federal_action_obligation IS NOT NULL  -- Filter out null obligations
                ORDER BY federal_action_obligation DESC;            """)
            
            connection.execute(mv_ratio_query)
            connection.execute(text("CREATE INDEX ON s3_processed.mv_agency_obligation_ratio (parent_award_agency_name)"))
            connection.execute(text("CREATE INDEX ON s3_processed.mv_agency_obligation_ratio (award_count_percentile)"))
            connection.execute(text("CREATE INDEX ON s3_processed.mv_agency_obligation_ratio (obligation_percentile)"))
            logger.info("    [OK] Created mv_agency_obligation_ratio with indexes")            # 6e. Contract Net Obligations - For proper deobligation handling
            logger.info("  - Creating mv_contract_net_obligations...")
            # Drop dependent views first to avoid dependency errors - use CASCADE to handle all dependencies
            connection.execute(text("DROP MATERIALIZED VIEW IF EXISTS s3_processed.mv_agency_net_obligations CASCADE"))
            connection.execute(text("DROP MATERIALIZED VIEW IF EXISTS s3_processed.mv_contract_net_obligations CASCADE"))
            
            mv_contract_net_query = text("""
                CREATE MATERIALIZED VIEW s3_processed.mv_contract_net_obligations AS
                WITH contract_aggregates AS (
                    SELECT
                        contract_award_unique_key,
                        MAX(recipient_name) as recipient_name,
                        MAX(parent_award_agency_name) as parent_award_agency_name,
                        MAX(funding_sub_agency_name) as funding_sub_agency_name,
                        MAX(awarding_sub_agency_name) as awarding_sub_agency_name,
                        MAX(naics_code) as naics_code,
                        MAX(naics_description) as naics_description,
                        MAX(product_or_service_code) as product_or_service_code,
                        MAX(product_or_service_code_description) as product_or_service_code_description,
                        -- Financial aggregations - NET OBLIGATIONS PER CONTRACT
                        SUM(federal_action_obligation) as net_contract_obligation,
                        SUM(CASE WHEN federal_action_obligation > 0 THEN federal_action_obligation ELSE 0 END) as gross_positive_obligation,
                        SUM(CASE WHEN federal_action_obligation < 0 THEN federal_action_obligation ELSE 0 END) as total_deobligations,
                        MAX(total_dollars_obligated) as latest_total_obligated,
                        MAX(potential_total_value_of_award) as potential_total_value,
                        -- Transaction patterns
                        COUNT(*) as total_transactions,
                        COUNT(*) FILTER (WHERE modification_number = '0') as has_base_award,
                        COUNT(*) FILTER (WHERE federal_action_obligation > 0) as positive_transactions,
                        COUNT(*) FILTER (WHERE federal_action_obligation < 0) as deobligation_transactions,
                        COUNT(*) FILTER (WHERE federal_action_obligation = 0) as zero_transactions,
                        -- Dates
                        MIN(action_date) as first_action_date,
                        MAX(action_date) as last_action_date,
                        MAX(period_of_performance_current_end_date) as period_of_performance_end_date,
                        -- Competition info
                        MAX(extent_competed) as extent_competed,
                        MAX(type_of_set_aside) as type_of_set_aside,
                        MAX(type_of_contract_pricing) as contract_pricing_type
                    FROM s3_processed.usaspending_prime_awards
                    WHERE contract_award_unique_key IS NOT NULL
                    GROUP BY contract_award_unique_key
                ),
                classified_contracts AS (
                    SELECT *,
                        -- Contract classification based on net obligations
                        CASE 
                            WHEN net_contract_obligation > 0 THEN 'ACTIVE_POSITIVE'
                            WHEN net_contract_obligation = 0 THEN 'FULLY_DEOBLIGATED'
                            WHEN net_contract_obligation < 0 THEN 'NET_NEGATIVE'
                            ELSE 'UNKNOWN'
                        END as contract_status,
                        -- Deobligation analysis
                        CASE 
                            WHEN deobligation_transactions = 0 THEN 'NO_DEOBLIGATIONS'
                            WHEN ABS(total_deobligations) < (gross_positive_obligation * 0.1) THEN 'MINOR_DEOBLIGATIONS'
                            WHEN ABS(total_deobligations) < (gross_positive_obligation * 0.5) THEN 'MODERATE_DEOBLIGATIONS'
                            WHEN ABS(total_deobligations) >= (gross_positive_obligation * 0.5) THEN 'MAJOR_DEOBLIGATIONS'
                            ELSE 'UNKNOWN_DEOBLIGATION_PATTERN'
                        END as deobligation_category,
                        -- Calculate deobligation percentage
                        CASE 
                            WHEN gross_positive_obligation > 0 
                            THEN (ABS(total_deobligations) / gross_positive_obligation * 100)
                            ELSE 0 
                        END as deobligation_percentage
                    FROM contract_aggregates
                )
                SELECT * FROM classified_contracts
                ORDER BY net_contract_obligation DESC;
            """)
            
            connection.execute(mv_contract_net_query)
            connection.execute(text("CREATE INDEX ON s3_processed.mv_contract_net_obligations (contract_award_unique_key)"))
            connection.execute(text("CREATE INDEX ON s3_processed.mv_contract_net_obligations (parent_award_agency_name)"))
            connection.execute(text("CREATE INDEX ON s3_processed.mv_contract_net_obligations (recipient_name)"))
            connection.execute(text("CREATE INDEX ON s3_processed.mv_contract_net_obligations (contract_status)"))
            connection.execute(text("CREATE INDEX ON s3_processed.mv_contract_net_obligations (deobligation_category)"))
            connection.execute(text("CREATE INDEX ON s3_processed.mv_contract_net_obligations (naics_code)"))
            connection.execute(text("CREATE INDEX ON s3_processed.mv_contract_net_obligations (net_contract_obligation)"))
            logger.info("    [OK] Created mv_contract_net_obligations with indexes")

            # 6f. Agency Net Obligations Summary - For proper agency reporting with deobligation awareness
            logger.info("  - Creating mv_agency_net_obligations...")
            connection.execute(text("DROP MATERIALIZED VIEW IF EXISTS s3_processed.mv_agency_net_obligations"))
            
            mv_agency_net_query = text("""
                CREATE MATERIALIZED VIEW s3_processed.mv_agency_net_obligations AS
                SELECT
                    parent_award_agency_name,
                    -- Traditional metrics (transaction-level aggregation)
                    COUNT(*) as total_contracts,
                    COUNT(*) FILTER (WHERE has_base_award > 0) as contracts_with_base_awards,
                    SUM(net_contract_obligation) as net_total_obligations,
                    AVG(net_contract_obligation) FILTER (WHERE net_contract_obligation > 0) as avg_positive_contract_value,
                    -- Active portfolio (only positive net obligations)
                    COUNT(*) FILTER (WHERE contract_status = 'ACTIVE_POSITIVE') as active_positive_contracts,
                    SUM(net_contract_obligation) FILTER (WHERE contract_status = 'ACTIVE_POSITIVE') as active_portfolio_value,
                    AVG(net_contract_obligation) FILTER (WHERE contract_status = 'ACTIVE_POSITIVE') as avg_active_contract_value,
                    -- Deobligation patterns
                    COUNT(*) FILTER (WHERE contract_status = 'FULLY_DEOBLIGATED') as fully_deobligated_contracts,
                    COUNT(*) FILTER (WHERE contract_status = 'NET_NEGATIVE') as net_negative_contracts,
                    COUNT(*) FILTER (WHERE deobligation_transactions > 0) as contracts_with_deobligations,
                    SUM(total_deobligations) as total_deobligations,
                    SUM(gross_positive_obligation) as gross_positive_obligations,
                    -- Deobligation rates
                    AVG(deobligation_percentage) FILTER (WHERE deobligation_transactions > 0) as avg_deobligation_rate,
                    COUNT(*) FILTER (WHERE deobligation_category = 'MAJOR_DEOBLIGATIONS') as major_deobligation_contracts,
                    -- Competition and diversity metrics for active portfolio
                    COUNT(DISTINCT recipient_name) FILTER (WHERE contract_status = 'ACTIVE_POSITIVE') as active_unique_contractors,
                    COUNT(DISTINCT naics_code) FILTER (WHERE contract_status = 'ACTIVE_POSITIVE') as active_unique_naics,
                    COUNT(*) FILTER (WHERE contract_status = 'ACTIVE_POSITIVE' AND extent_competed = 'FULL AND OPEN COMPETITION') as active_competitive_contracts,
                    SUM(net_contract_obligation) FILTER (WHERE contract_status = 'ACTIVE_POSITIVE' AND extent_competed = 'FULL AND OPEN COMPETITION') as active_competitive_value
                FROM s3_processed.mv_contract_net_obligations
                WHERE parent_award_agency_name IS NOT NULL
                GROUP BY parent_award_agency_name
                ORDER BY active_portfolio_value DESC;
            """)
            
            connection.execute(mv_agency_net_query)
            connection.execute(text("CREATE INDEX ON s3_processed.mv_agency_net_obligations (parent_award_agency_name)"))
            connection.execute(text("CREATE INDEX ON s3_processed.mv_agency_net_obligations (active_portfolio_value)"))
            connection.execute(text("CREATE INDEX ON s3_processed.mv_agency_net_obligations (net_total_obligations)"))
            logger.info("    [OK] Created mv_agency_net_obligations with indexes")

            # 6g. Expiring Contracts Optimized - For get_expiring_contracts() performance
            logger.info("  - Creating mv_expiring_contracts...")
            connection.execute(text("DROP MATERIALIZED VIEW IF EXISTS s3_processed.mv_expiring_contracts"))
            
            mv_expiring_query = text("""
                CREATE MATERIALIZED VIEW s3_processed.mv_expiring_contracts AS
                WITH base_awards AS (
                    SELECT
                        contract_transaction_unique_key,
                        contract_award_unique_key,
                        award_id_piid,
                        recipient_name,
                        parent_award_agency_name,
                        funding_sub_agency_name,
                        action_date,
                        federal_action_obligation,
                        potential_total_value_of_award,                        naics_code,
                        product_or_service_code,
                        -- Contract end dates based on contract type
                        -- Standard contracts: Use current performance end date (or potential if current is null)
                        -- IDV contracts: Use ordering period end date
                        CASE 
                            WHEN ordering_period_end_date IS NOT NULL THEN ordering_period_end_date
                            ELSE COALESCE(period_of_performance_current_end_date, period_of_performance_potential_end_date)
                        END AS contract_end_date,
                        -- Contract type classification for analysis
                        CASE 
                            WHEN ordering_period_end_date IS NOT NULL THEN 'IDV'
                            WHEN period_of_performance_current_end_date IS NOT NULL OR period_of_performance_potential_end_date IS NOT NULL THEN 'STANDARD'
                            ELSE 'UNKNOWN'
                        END AS contract_type
                    FROM s3_processed.usaspending_prime_awards
                    WHERE modification_number = '0'  -- Base awards only
                        AND recipient_name IS NOT NULL
                        AND parent_award_agency_name IS NOT NULL
                ),                expiring_analysis AS (
                    SELECT
                        *,
                        -- Calculate days to expiration from current date
                        contract_end_date - CURRENT_DATE AS days_to_expiration,
                        -- Categorize expiration timeframes
                        CASE 
                            WHEN contract_end_date - CURRENT_DATE <= 180 THEN '0-6 months'
                            WHEN contract_end_date - CURRENT_DATE <= 365 THEN '6-12 months'
                            WHEN contract_end_date - CURRENT_DATE <= 730 THEN '12-24 months'
                            ELSE '24+ months'
                        END AS expiration_timeframe
                    FROM base_awards
                    WHERE contract_end_date IS NOT NULL  -- Only contracts with valid end dates
                )                SELECT
                    contract_transaction_unique_key,
                    contract_award_unique_key,
                    award_id_piid,
                    recipient_name,
                    parent_award_agency_name,
                    funding_sub_agency_name,
                    action_date,
                    federal_action_obligation,
                    potential_total_value_of_award,
                    naics_code,
                    product_or_service_code,
                    contract_end_date,
                    contract_type,
                    days_to_expiration,
                    expiration_timeframe,
                    -- Ranking by obligation within each timeframe and contract type
                    RANK() OVER (PARTITION BY expiration_timeframe, contract_type ORDER BY federal_action_obligation DESC) AS rank_in_timeframe,
                    -- Overall ranking
                    RANK() OVER (ORDER BY federal_action_obligation DESC) AS overall_rank
                FROM expiring_analysis
                WHERE contract_end_date > CURRENT_DATE  -- Only future-expiring contracts
                    AND contract_end_date <= CURRENT_DATE + INTERVAL '24 months'  -- Within 24 months
                ORDER BY days_to_expiration, federal_action_obligation DESC;
            """)
            connection.execute(mv_expiring_query)
            connection.execute(text("CREATE INDEX ON s3_processed.mv_expiring_contracts (expiration_timeframe, contract_type, rank_in_timeframe)"))
            connection.execute(text("CREATE INDEX ON s3_processed.mv_expiring_contracts (contract_end_date)"))
            connection.execute(text("CREATE INDEX ON s3_processed.mv_expiring_contracts (days_to_expiration)"))
            connection.execute(text("CREATE INDEX ON s3_processed.mv_expiring_contracts (contract_type)"))
            connection.execute(text("CREATE INDEX ON s3_processed.mv_expiring_contracts (recipient_name)"))
            connection.execute(text("CREATE INDEX ON s3_processed.mv_expiring_contracts (parent_award_agency_name)"))
            logger.info("    [OK] Created mv_expiring_contracts with indexes")
            
            logger.info("[OK] All materialized views created successfully!")


def refresh_materialized_views():
    """
    Refresh all materialized views to update with latest data.
    This should be called after each ETL/transform run.
    """    
    materialized_views = [
        "s3_processed.mv_top_competitors_market_share",
        "s3_processed.mv_treemap_competitive_landscape", 
        "s3_processed.mv_quarterly_trends_analysis",
        "s3_processed.mv_agency_analysis_summary",
        "s3_processed.mv_contract_vehicle_analysis",
        "s3_processed.mv_award_summary_metrics",
        "s3_processed.mv_top_agencies",
        "s3_processed.mv_quarterly_trends_optimized",
        "s3_processed.mv_agency_obligation_ratio",
        "s3_processed.mv_contract_net_obligations",
        "s3_processed.mv_agency_net_obligations",
        "s3_processed.mv_expiring_contracts"
    ]
    
    with engine.connect() as connection:
        with connection.begin():
            logger.info("\nRefreshing materialized views with latest data...")
            
            for view in materialized_views:
                try:
                    start_time = time.time()
                    connection.execute(text(f"REFRESH MATERIALIZED VIEW {view}"))
                    end_time = time.time()
                    logger.info(f"  [OK] Refreshed {view} in {end_time - start_time:.2f} seconds")
                except Exception as e:
                    logger.error(f"  [ERROR] Failed to refresh {view}: {e}")
            
            logger.info("[OK] All materialized views refreshed!")


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
    
    # Create materialized views for high-traffic queries
    logger.info("\n[Auto] Creating materialized views for instant dashboard performance...")
    create_materialized_views()
    
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
            "funding_agency_name",           # Added missing column
            "recipient_name",
            "recipient_parent_name",         # Added missing column
            "award_id_piid",                 # Added missing column
            "parent_award_id_piid",          # Added missing column
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

        # List of tables to analyze (including materialized views)
        tables_to_analyze = [
            source_table,
            quarterly_table,
            dependencies_table,
            "s3_processed.mv_top_competitors_market_share",
            "s3_processed.mv_treemap_competitive_landscape", 
            "s3_processed.mv_quarterly_trends_analysis",
            "s3_processed.mv_agency_analysis_summary",
            "s3_processed.mv_contract_vehicle_analysis"
        ] + [table["name"] for table in filter_tables]

        for table in tables_to_analyze:
            try:
                connection.execute(text(f"ANALYZE {table}"))
                logger.info(f"  [OK] Analyzed {table} table for optimal query performance")
            except Exception as e:
                logger.warning(f"  [WARN] Could not analyze {table}: {e}")

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
            # Include: filter_*, quarterly_data, usaspending_*, mv_*
            # Exclude: lookup_*, temp_*, and other utility tables
            if (table_name.startswith("lookup_") or 
                table_name.startswith("temp_") or
                ("_" in table_name and not table_name.startswith("filter_") and 
                 not table_name == "quarterly_data" and
                 not table_name.startswith("usaspending_") and
                 not table_name.startswith("mv_"))):
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
    results["materialized_views_created"] = 5
    
    logger.info(f"\nData preprocessing complete! Total time: {minutes}m {seconds}s")
    logger.info("✨ Enhanced with materialized views for instant dashboard performance!")
    logger.info("The application is now ready to run with optimal performance!")
    
    return results

# If run as a script, run preprocessing (and thus indexing) automatically
def clean_s3_processed_schema():
    """
    Remove all tables, materialized views, and indexes in s3_processed except for usaspending_* tables.
    For usaspending_* tables, drop all indexes except PK/unique constraints.
    Logs all actions to transformation.log.
    """
    from sqlalchemy import inspect
    import re
    logger.info("[CLEANUP] Starting cleanup of s3_processed schema...")
    with engine.connect() as connection:
        # Use an explicit transaction block to ensure DDL is committed
        with connection.begin():
            # 1. Drop all materialized views except usaspending_*
            mv_query = text("""
                SELECT matviewname FROM pg_matviews
                WHERE schemaname = 's3_processed' AND matviewname NOT LIKE 'usaspending_%'
            """)
            mvs = [row[0] for row in connection.execute(mv_query).fetchall()]
            for mv in mvs:
                logger.info(f"[CLEANUP] Dropping materialized view: {mv}")
                connection.execute(text(f"DROP MATERIALIZED VIEW IF EXISTS s3_processed.{mv} CASCADE"))
            # 2. Drop all tables except usaspending_*
            table_query = text("""
                SELECT tablename FROM pg_tables
                WHERE schemaname = 's3_processed' AND tablename NOT LIKE 'usaspending_%'
            """)
            tables = [row[0] for row in connection.execute(table_query).fetchall()]
            for table in tables:
                logger.info(f"[CLEANUP] Dropping table: {table}")
                connection.execute(text(f"DROP TABLE IF EXISTS s3_processed.{table} CASCADE"))
            # 3. For each usaspending_* table, drop all non-PK/unique indexes
            usaspending_table_query = text("""
                SELECT tablename FROM pg_tables
                WHERE schemaname = 's3_processed' AND tablename LIKE 'usaspending_%'
            """)
            usaspending_tables = [row[0] for row in connection.execute(usaspending_table_query).fetchall()]
            for table in usaspending_tables:
                # Get all indexes for this table
                idx_query = text(f"""
                    SELECT i.relname as index_name, ix.indisprimary, ix.indisunique
                    FROM pg_class t
                    JOIN pg_index ix ON t.oid = ix.indrelid
                    JOIN pg_class i ON i.oid = ix.indexrelid
                    JOIN pg_namespace n ON n.oid = t.relnamespace
                    WHERE n.nspname = 's3_processed' AND t.relname = :table
                """)
                indexes = connection.execute(idx_query, {"table": table}).fetchall()
                for index_name, is_pk, is_unique in indexes:
                    # Only keep PK or unique indexes
                    if not is_pk and not is_unique:
                        logger.info(f"[CLEANUP] Dropping index {index_name} on {table}")
                        connection.execute(text(f"DROP INDEX IF EXISTS s3_processed.{index_name} CASCADE"))
            logger.info("[CLEANUP] s3_processed schema cleanup complete.")

if __name__ == "__main__":
    logger.info("=== Data_Insights Transformation Pipeline Started ===")
    logger.info("Step 1: Cleaning s3_processed schema (preserving usaspending_* tables and only PK/unique indexes)...")
    clean_s3_processed_schema()
    logger.info("Step 2: Running full transformation pipeline (indexing + materialized views + preprocessing)...")
    preprocess_data_optimized()
    logger.info("=== Transformation pipeline complete. See logs/transformation.log for details. ===")
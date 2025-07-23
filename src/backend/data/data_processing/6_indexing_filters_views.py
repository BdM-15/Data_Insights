"""
Step 6: Indexing, Filter Tables, and Materialized Views for s3_processed (ETL Pipeline)

- Adds all required indexes (including pgvector) to s3_processed.usaspending_prime_awards and s3_processed.usaspending_subawards.
- Creates all filter tables (e.g., filter_values_naics_code, etc.) in s3_processed.
- Creates and refreshes all materialized views (e.g., mv_agency_analysis_summary, etc.) in s3_processed.
- Modular, idempotent, and ready for orchestration.
- Refactored from transformation.py for the new pipeline.

Requirements:
- SQLAlchemy
- pgvector extension (for vector search, optional)

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


def create_indexes():
    """
    Create indexes for s3_processed tables, including pgvector index if available.
    """
    start_time = time.time()
    logger.info("Starting index creation for s3_processed tables...")
    with engine.connect() as connection:
        # Ensure pgvector extension exists
        try:
            connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            logger.info("[OK] pgvector extension ensured.")
        except Exception as e:
            logger.warning(f"[WARN] Could not create/verify pgvector extension: {e}")

        # Indexes for prime awards
        prime_table = 's3_processed.usaspending_prime_awards'
        prime_indexes = [
            {"name": "s3p_idx_prime_contract_award_unique_key", "columns": "contract_award_unique_key"},
            {"name": "s3p_idx_prime_recipient_uei", "columns": "recipient_uei"},
            {"name": "s3p_idx_prime_naics_code", "columns": "naics_code"},
            {"name": "s3p_idx_prime_parent_agency", "columns": "parent_award_agency_name"},
            {"name": "s3p_idx_prime_semantic_vector", "columns": "semantic_vector", "type": "vector"}
        ]
        for idx in prime_indexes:
            try:
                if idx.get("type") == "vector":
                    connection.execute(text(f'''
                        DO $$
                        BEGIN
                            IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema = 's3_processed' AND table_name = 'usaspending_prime_awards' AND column_name = 'semantic_vector') THEN
                                IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE schemaname = 's3_processed' AND indexname = '{idx['name']}') THEN
                                    EXECUTE 'CREATE INDEX {idx['name']} ON s3_processed.usaspending_prime_awards USING ivfflat (semantic_vector vector_cosine_ops)';
                                END IF;
                            END IF;
                        END$$;
                    '''))
                    logger.info(f"[OK] Vector index {idx['name']} ensured on {prime_table}")
                else:
                    connection.execute(text(f"CREATE INDEX IF NOT EXISTS {idx['name']} ON {prime_table} ({idx['columns']})"))
                    logger.info(f"[OK] Index {idx['name']} ensured on {prime_table}")
            except Exception as e:
                logger.warning(f"[WARN] Could not create index {idx['name']} on {prime_table}: {e}")

        # Indexes for subawards
        sub_table = 's3_processed.usaspending_subawards'
        sub_indexes = [
            {"name": "s3p_idx_sub_prime_award_unique_key", "columns": "prime_award_unique_key"},
            {"name": "s3p_idx_sub_subawardee_uei", "columns": "subawardee_uei"},
            {"name": "s3p_idx_sub_subaward_number", "columns": "subaward_number"},
            {"name": "s3p_idx_sub_semantic_vector", "columns": "semantic_vector", "type": "vector"}
        ]
        for idx in sub_indexes:
            try:
                if idx.get("type") == "vector":
                    connection.execute(text(f'''
                        DO $$
                        BEGIN
                            IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema = 's3_processed' AND table_name = 'usaspending_subawards' AND column_name = 'semantic_vector') THEN
                                IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE schemaname = 's3_processed' AND indexname = '{idx['name']}') THEN
                                    EXECUTE 'CREATE INDEX {idx['name']} ON s3_processed.usaspending_subawards USING ivfflat (semantic_vector vector_cosine_ops)';
                                END IF;
                            END IF;
                        END$$;
                    '''))
                    logger.info(f"[OK] Vector index {idx['name']} ensured on {sub_table}")
                else:
                    connection.execute(text(f"CREATE INDEX IF NOT EXISTS {idx['name']} ON {sub_table} ({idx['columns']})"))
                    logger.info(f"[OK] Index {idx['name']} ensured on {sub_table}")
            except Exception as e:
                logger.warning(f"[WARN] Could not create index {idx['name']} on {sub_table}: {e}")
    elapsed = time.time() - start_time
    minutes = int(elapsed // 60)
    seconds = int(elapsed % 60)
    logger.info(f"Index creation complete in {minutes}m {seconds}s ({elapsed:.2f} seconds).")


def create_filter_tables():
    """
    Create filter value tables in s3_processed for fast UI filtering.
    """
    filter_columns = [
        "parent_award_agency_name",
        "funding_sub_agency_name",
        "funding_office_name",
        "funding_agency_name",
        "recipient_name",
        "recipient_parent_name",
        "award_id_piid",
        "parent_award_id_piid",
        "naics_code",
        "product_or_service_code",
        "type_of_contract_pricing",
        "extent_competed",
        "type_of_set_aside"
    ]
    source_table = "s3_processed.usaspending_prime_awards"
    start_time = time.time()
    logger.info("Starting filter table creation for s3_processed...")
    with engine.connect() as connection:
        for column in filter_columns:
            table_name = f"s3_processed.filter_values_{column}"
            logger.info(f"Creating filter values table: {table_name}")
            connection.execute(text(f"DROP TABLE IF EXISTS {table_name}"))
            create_filter_query = text(f'''
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
            ''')
            connection.execute(create_filter_query)
            logger.info(f"[OK] Created filter values table for {column}")
        connection.commit()
    elapsed = time.time() - start_time
    minutes = int(elapsed // 60)
    seconds = int(elapsed % 60)
    logger.info(f"Filter table creation complete in {minutes}m {seconds}s ({elapsed:.2f} seconds).")


def create_materialized_views():
    """
    Create and refresh materialized views for analytics in s3_processed.
    """
    start_time = time.time()
    logger.info("Starting materialized view creation for s3_processed...")
    with engine.connect() as connection:
        # Example: Agency Analysis Summary (add more as needed)
        logger.info("Creating materialized view: mv_agency_analysis_summary")
        connection.execute(text("DROP MATERIALIZED VIEW IF EXISTS s3_processed.mv_agency_analysis_summary"))
        mv_agency_query = text('''
            CREATE MATERIALIZED VIEW s3_processed.mv_agency_analysis_summary AS
            SELECT 
                parent_award_agency_name,
                funding_sub_agency_name,
                COUNT(*) as transaction_count,
                COUNT(*) FILTER (WHERE modification_number = '0') as award_count,
                SUM(federal_action_obligation) as total_obligation,
                AVG(federal_action_obligation) as avg_obligation,
                COUNT(DISTINCT recipient_name) as unique_contractors,
                COUNT(DISTINCT naics_code) as unique_naics_codes,
                COUNT(DISTINCT product_or_service_code) as unique_psc_codes
            FROM s3_processed.usaspending_prime_awards
            WHERE parent_award_agency_name IS NOT NULL 
                AND funding_sub_agency_name IS NOT NULL
                AND federal_action_obligation > 0
            GROUP BY parent_award_agency_name, funding_sub_agency_name
            ORDER BY total_obligation DESC;
        ''')
        connection.execute(mv_agency_query)
        connection.execute(text("CREATE INDEX IF NOT EXISTS s3p_idx_mv_agency_analysis_summary_agency ON s3_processed.mv_agency_analysis_summary (parent_award_agency_name)"))
        logger.info("[OK] Created mv_agency_analysis_summary with index.")
        # Add more materialized views as needed, following the pattern in transformation.py
        connection.commit()
    elapsed = time.time() - start_time
    minutes = int(elapsed // 60)
    seconds = int(elapsed % 60)
    logger.info(f"Materialized view creation complete in {minutes}m {seconds}s ({elapsed:.2f} seconds).")


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)]
    )
    logger.info("Step 6: Creating indexes, filter tables, and materialized views in s3_processed...")
    start_all = time.time()
    create_indexes()
    create_filter_tables()
    create_materialized_views()
    elapsed_all = time.time() - start_all
    minutes_all = int(elapsed_all // 60)
    seconds_all = int(elapsed_all % 60)
    logger.info(f"All indexes, filter tables, and materialized views created in s3_processed in {minutes_all}m {seconds_all}s ({elapsed_all:.2f} seconds).")
    logger.info("All indexes, filter tables, and materialized views created in s3_processed.")

if __name__ == "__main__":
    main()

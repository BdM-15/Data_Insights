"""
Step 3: Semantic Description Column Creation for Semantic Search (ETL Pipeline)

- Adds a 'semantic_description' column to each enriched table for LLM/AI embedding generation.
- Populates the column by concatenating key descriptive fields for each record.
- No vector generation is performed here; this is for downstream embedding/vectorization.

Prime Awards Table (s2_interim.usaspending_prime_awards_enriched):
    semantic_description = prime_award_base_transaction_description || ' ' || transaction_description || ' ' || naics_description || ' ' || product_or_service_code_description

Subawards Table (s2_interim.usaspending_subawards_enriched):
    semantic_description = subaward_description || ' ' || prime_award_base_transaction_description || ' ' || transaction_description || ' ' || naics_description || ' ' || product_or_service_code_description
    (prime fields are joined from the prime table, already present from enrichment step)

This script is modular and ready for orchestration in the ETL pipeline.
"""

import time
import logging
from sqlalchemy import create_engine, text
import os
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



def add_semantic_description_prime():
    """
    Add and populate semantic_description column for prime awards dedup table.
    """
    start_time = time.time()
    logger.info("Starting semantic_description column creation for prime awards (dedup table)...")
    table_name = "s2_interim.usaspending_prime_awards_dedup"
    try:
        with engine.begin() as connection:
            # Safety timeout
            try:
                connection.execute(text("SET LOCAL statement_timeout = '30min'"))
            except Exception:
                pass
            # Ensure column exists
            connection.execute(text(f"""
                ALTER TABLE {table_name}
                ADD COLUMN IF NOT EXISTS semantic_description TEXT;
            """))
            # Populate only when NULL to avoid rewriting unchanged rows
            result = connection.execute(text(f"""
                UPDATE {table_name}
                SET semantic_description =
                    COALESCE(prime_award_base_transaction_description, '') || ' ' ||
                    COALESCE(transaction_description, '') || ' ' ||
                    COALESCE(naics_description, '') || ' ' ||
                    COALESCE(product_or_service_code_description, '')
                WHERE semantic_description IS NULL
            """))
            updated = getattr(result, 'rowcount', None)
            logger.info(f"semantic_description populated for prime dedup; rows updated: {updated if updated is not None else '?'}.")
    except Exception as e:
        logger.error(f"Failed to update {table_name}: {e}")
        return
    elapsed = time.time() - start_time
    minutes = int(elapsed // 60)
    seconds = int(elapsed % 60)
    logger.info(f"Prime semantic_description completed in {minutes}m {seconds}s ({elapsed:.2f} seconds).")



def add_semantic_description_subawards():
    """
    Add and populate semantic_description column for subawards enriched table.
    """
    start_time = time.time()
    logger.info("Starting semantic_description column creation for subawards...")
    with engine.begin() as connection:
        # Safety timeout
        try:
            connection.execute(text("SET LOCAL statement_timeout = '30min'"))
        except Exception:
            pass
        connection.execute(text("""
            ALTER TABLE s2_interim.usaspending_subawards_enriched
            ADD COLUMN IF NOT EXISTS semantic_description TEXT;
        """))
        result = connection.execute(text("""
            UPDATE s2_interim.usaspending_subawards_enriched
            SET semantic_description =
                COALESCE(subaward_description, '') || ' ' ||
                COALESCE(prime_prime_award_base_transaction_description, '') || ' ' ||
                COALESCE(prime_transaction_description, '') || ' ' ||
                COALESCE(prime_naics_description, '') || ' ' ||
                COALESCE(prime_product_or_service_code_description, '')
            WHERE semantic_description IS NULL
        """))
        updated = getattr(result, 'rowcount', None)
        logger.info(f"semantic_description populated for subawards_enriched; rows updated: {updated if updated is not None else '?' }.")
    elapsed = time.time() - start_time
    minutes = int(elapsed // 60)
    seconds = int(elapsed % 60)
    logger.info(f"Subawards semantic_description completed in {minutes}m {seconds}s ({elapsed:.2f} seconds).")



def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[logging.StreamHandler()]
    )
    logger.info("Step 3: Creating semantic_description columns for semantic search...")
    start_all = time.time()
    add_semantic_description_prime()
    add_semantic_description_subawards()
    elapsed_all = time.time() - start_all
    minutes_all = int(elapsed_all // 60)
    seconds_all = int(elapsed_all % 60)
    logger.info(f"Semantic description columns created and populated for all tables in {minutes_all}m {seconds_all}s ({elapsed_all:.2f} seconds).")

if __name__ == "__main__":
    main()

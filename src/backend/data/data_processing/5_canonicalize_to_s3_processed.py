"""
Step 5: Canonicalization - Move Final Tables to s3_processed (ETL Pipeline)

- Copies (or renames) the fully processed tables from s2_interim to s3_processed schema.
- Ensures all columns, including semantic_description and semantic_vector, are preserved.
- Overwrites any existing tables in s3_processed with the same name.
- This step is required before indexing, filter table, and materialized view creation.

Requirements:
- SQLAlchemy

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


def canonicalize_tables():
    """
    Move/copy final tables from s2_interim to s3_processed, overwriting if exists.
    """
    start_time = time.time()
    logger.info("Starting canonicalization (move/copy to s3_processed)...")
    tables = [
        ("usaspending_prime_awards_enriched", "usaspending_prime_awards"),
        ("usaspending_subawards_enriched", "usaspending_subawards")
    ]
    with engine.connect() as connection:
        for src, dest in tables:
            src_table = f"s2_interim.{src}"
            dest_table = f"s3_processed.{dest}"
            logger.info(f"Copying {src_table} to {dest_table} (overwriting if exists)...")
            # Drop destination table if exists
            connection.execute(text(f"DROP TABLE IF EXISTS {dest_table} CASCADE"))
            # Copy table structure and data
            connection.execute(text(f"CREATE TABLE {dest_table} AS TABLE {src_table}"))
            logger.info(f"[OK] {dest_table} created.")
        connection.commit()
    elapsed = time.time() - start_time
    minutes = int(elapsed // 60)
    seconds = int(elapsed % 60)
    logger.info(f"Canonicalization completed in {minutes}m {seconds}s ({elapsed:.2f} seconds).")

def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)]
    )
    logger.info("Step 5: Moving final tables to s3_processed schema...")
    start_all = time.time()
    canonicalize_tables()
    elapsed_all = time.time() - start_all
    minutes_all = int(elapsed_all // 60)
    seconds_all = int(elapsed_all % 60)
    logger.info(f"All canonical tables are now in s3_processed in {minutes_all}m {seconds_all}s ({elapsed_all:.2f} seconds).")

if __name__ == "__main__":
    main()

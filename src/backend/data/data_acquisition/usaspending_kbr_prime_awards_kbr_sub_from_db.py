# usaspending_kbr_prime_awards_kbr_sub_from_db.py
"""
Extracts all prime awards from s3_processed.usaspending_prime_awards where KBR UEIs are performing as a subawardee (from s3_processed.usaspending_subawards_kbr),
and writes them to s3_processed.usaspending_prime_awards_kbr_sub, preserving all columns.

- Joins subawards table to prime awards on prime_award_unique_key
- Keeps all columns from the prime awards table
- Drops and recreates the destination table on each run
- Deduplicates using award_id or prime_award_unique_key if available
- Follows Data_Insights project standards
"""
import os
import sys
import logging
import psycopg2
from tqdm import tqdm

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))
import config

# --- Logging Setup ---
def setup_logging(log_file: str = 'logs/usaspending_kbr_prime_awards_kbr_sub_db.log'):
    log_dir = os.path.dirname(log_file)
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    logger = logging.getLogger("usaspending_kbr_prime_awards_kbr_sub_db")
    logger.setLevel(logging.INFO)
    if logger.handlers:
        logger.handlers.clear()
    file_handler = logging.FileHandler(log_file)
    file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_formatter)
    console_handler = logging.StreamHandler()
    console_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(console_formatter)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    logger.propagate = False
    return logger

logger = setup_logging()

# --- DB Extraction and Table Creation ---
def main():
    logger.info("Connecting to PostgreSQL database...")
    try:
        conn = psycopg2.connect(
            host=config.PG_HOST,
            port=config.PG_PORT,
            dbname=config.PG_DATABASE,
            user=config.PG_USER,
            password=config.PG_PASSWORD
        )
        cursor = conn.cursor()
        # Drop destination table if it exists
        logger.info("Dropping destination table if it exists...")
        cursor.execute("DROP TABLE IF EXISTS s3_processed.usaspending_prime_awards_kbr_sub;")
        conn.commit()
        # Get all columns from source table
        cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_schema = 's3_processed' AND table_name = 'usaspending_prime_awards' ORDER BY ordinal_position;")
        columns = [row[0] for row in cursor.fetchall()]
        col_str = ', '.join([f'\"{col}\"' for col in columns])
        # Create destination table with same structure
        cursor.execute(f"""
            CREATE TABLE s3_processed.usaspending_prime_awards_kbr_sub AS SELECT * FROM s3_processed.usaspending_prime_awards WHERE false;
        """)
        conn.commit()
        # Build join and deduplication logic
        logger.info("Joining subawards and prime awards tables on prime_award_unique_key and deduplicating...")
        # Check for deduplication key
        dedup_key = None
        if 'award_id' in columns:
            dedup_key = 'award_id'
        elif 'prime_award_unique_key' in columns:
            dedup_key = 'prime_award_unique_key'
        # Reason: Use DISTINCT ON for deduplication if possible
        if dedup_key:
            distinct_select = f"DISTINCT ON ({dedup_key}) {col_str}"
        else:
            distinct_select = f"DISTINCT {col_str}"
        query = f"""
            SELECT {distinct_select}
            FROM s3_processed.usaspending_prime_awards pa
            INNER JOIN s3_processed.usaspending_subawards_kbr sub
                ON pa.contract_award_unique_key = sub.prime_award_unique_key
            WHERE pa.modification_number = '0'
        """
        cursor.execute(query)
        rows = cursor.fetchall()
        logger.info(f"Fetched {len(rows)} unique prime award records where KBR is subawardee.")
        # Insert into destination table
        if rows:
            insert_query = f"INSERT INTO s3_processed.usaspending_prime_awards_kbr_sub ({col_str}) VALUES ({','.join(['%s']*len(columns))})"
            for row in tqdm(rows, desc="Inserting records"):
                cursor.execute(insert_query, row)
            conn.commit()
            logger.info(f"Inserted {len(rows)} records into s3_processed.usaspending_prime_awards_kbr_sub.")
        else:
            logger.info("No records to insert.")
        cursor.close()
        conn.close()
        logger.info("Done.")
    except Exception as e:
        logger.error(f"Error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

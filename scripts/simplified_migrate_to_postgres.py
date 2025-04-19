"""
Simplified SQLite to PostgreSQL Migration Script

This script handles the migration of only the raw awards table from SQLite to PostgreSQL.
After migration, you can run the data_cleansing.py and data_preprocessing_for_app_performance.py
scripts to process the data in PostgreSQL.
"""

import os
import pandas as pd
import time
import logging
import sys
from sqlalchemy import create_engine, inspect, text, MetaData, Table, Column
from tqdm import tqdm

# Add parent directory to path to import db_config
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.db_config import get_postgres_connection_url, DEFAULT_SQLITE_PATH

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("migration.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Connection parameters
sqlite_path = DEFAULT_SQLITE_PATH
postgres_url = get_postgres_connection_url()

# Connect to both databases
sqlite_engine = create_engine(sqlite_path, connect_args={'timeout': 60})
postgres_engine = create_engine(postgres_url)

def get_sqlite_table_schema(table_name):
    """Get the schema of a table in the SQLite database"""
    with sqlite_engine.connect() as conn:
        result = conn.execute(text(f"PRAGMA table_info({table_name})"))
        columns = []
        for row in result:
            columns.append({
                'name': row[1],
                'type': row[2],
                'notnull': row[3],
                'default': row[4],
                'pk': row[5]
            })
    return columns

def transfer_data(batch_size=10000):
    """Transfer data from SQLite to PostgreSQL in batches"""
    table_name = 'awards'
    start_time = time.time()
    logger.info(f"Starting data transfer for table {table_name}")
    
    # Get row count from SQLite
    with sqlite_engine.connect() as conn:
        result = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
        total_rows = result.scalar()
    
    logger.info(f"Table {table_name} has {total_rows} rows")
    
    # Transfer data in batches
    offset = 0
    with tqdm(total=total_rows, desc=f"Transferring {table_name}") as pbar:
        while True:
            # Read batch from SQLite
            query = f"SELECT * FROM {table_name} LIMIT {batch_size} OFFSET {offset}"
            try:
                df = pd.read_sql(query, sqlite_engine)
            except Exception as e:
                logger.error(f"Error reading from SQLite: {str(e)}")
                break
            
            if df.empty:
                break
            
            # Write batch to PostgreSQL
            try:
                # Write to PostgreSQL with "append" for all batches
                if_exists = 'replace' if offset == 0 else 'append'
                df.to_sql(table_name, postgres_engine, if_exists=if_exists, index=False)
            except Exception as e:
                logger.error(f"Error writing to PostgreSQL: {str(e)}")
                raise
            
            # Update progress
            offset += batch_size
            pbar.update(len(df))
            
            if len(df) < batch_size:
                break
    
    elapsed_time = time.time() - start_time
    logger.info(f"Data transfer for table {table_name} completed in {elapsed_time:.2f} seconds")

def create_fetch_progress_table():
    """Create the fetch_progress table in PostgreSQL"""
    try:
        with postgres_engine.connect() as conn:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS fetch_progress (
                    id SERIAL PRIMARY KEY,
                    last_fetched_date DATE
                )
            """))
            conn.commit()
            
            # Check if the table has any records
            result = conn.execute(text("SELECT COUNT(*) FROM fetch_progress"))
            count = result.scalar()
            
            # Insert initial record if the table is empty
            if count == 0:
                conn.execute(
                    text("INSERT INTO fetch_progress (id, last_fetched_date) VALUES (1, '2022-02-01')")
                )
                conn.commit()
                logger.info("Created and initialized fetch_progress table")
            else:
                logger.info("fetch_progress table already has data, skipping initialization")
    except Exception as e:
        logger.error(f"Error creating fetch_progress table: {str(e)}")

if __name__ == "__main__":
    logger.info("Starting simplified SQLite to PostgreSQL migration (awards table only)")
    
    try:
        # Test PostgreSQL connection
        with postgres_engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.scalar()
            logger.info(f"Connected to PostgreSQL: {version}")
        
        # Create fetch_progress table (required by other scripts)
        create_fetch_progress_table()
        
        # Transfer awards table data
        transfer_data()
        
        logger.info("Awards table migration completed successfully")
        logger.info("You can now run data_cleansing.py and data_preprocessing_for_app_performance.py to process the data")
    except Exception as e:
        logger.error(f"Migration failed: {str(e)}", exc_info=True)
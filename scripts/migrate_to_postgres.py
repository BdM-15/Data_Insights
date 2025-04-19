"""
SQLite to PostgreSQL Migration Script

This script handles the migration of data from the SQLite database to PostgreSQL.
It creates the necessary tables, transfers data, and sets up indexes.
"""

import os
import pandas as pd
import time
import logging
from sqlalchemy import create_engine, inspect, text, MetaData, Table, Column
from sqlalchemy.exc import OperationalError, ProgrammingError
from sqlalchemy.types import Integer, Float, String, Date, DateTime, Boolean
from tqdm import tqdm
import sys

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

def get_sqlite_tables():
    """Get a list of all tables in the SQLite database"""
    with sqlite_engine.connect() as conn:
        result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
        tables = [row[0] for row in result]
    return tables

def get_sqlite_table_schema(table_name):
    """Get the schema of a table in the SQLite database"""
    with sqlite_engine.connect() as conn:
        result = conn.execute(text(f"PRAGMA table_info({table_name})"))
        columns = []
        for row in result:
            column = {
                'name': row[1],
                'type': row[2],
                'notnull': row[3],
                'default': row[4],
                'pk': row[5]
            }
            columns.append(column)
    return columns

def map_sqlite_type_to_postgres(sqlite_type):
    """Map SQLite data types to PostgreSQL data types"""
    sqlite_type = sqlite_type.upper()
    
    if 'INT' in sqlite_type:
        return Integer
    elif 'REAL' in sqlite_type or 'FLOAT' in sqlite_type or 'DOUBLE' in sqlite_type or 'NUMERIC' in sqlite_type:
        return Float
    elif 'TEXT' in sqlite_type or 'CHAR' in sqlite_type or 'CLOB' in sqlite_type or 'VARCHAR' in sqlite_type:
        return String(1000)  # Adjust length as needed
    elif 'DATE' in sqlite_type:
        return Date
    elif 'DATETIME' in sqlite_type or 'TIMESTAMP' in sqlite_type:
        return DateTime
    elif 'BOOLEAN' in sqlite_type or 'BOOL' in sqlite_type:
        return Boolean
    else:
        # Default to text for unknown types
        logger.warning(f"Unknown SQLite type: {sqlite_type}, defaulting to String")
        return String(1000)

def create_postgres_table(table_name, columns):
    """Create a table in PostgreSQL with the same structure as in SQLite"""
    metadata = MetaData()
    
    # Create columns
    table_columns = []
    for col in columns:
        # Map SQLite types to PostgreSQL types
        col_type = map_sqlite_type_to_postgres(col['type'])
        
        # Add column
        column = Column(
            col['name'],
            col_type,
            primary_key=(col['pk'] == 1),
            nullable=(col['notnull'] == 0)
        )
        table_columns.append(column)
    
    # Create table
    table = Table(table_name, metadata, *table_columns)
    
    # Create table in PostgreSQL
    metadata.create_all(postgres_engine)
    logger.info(f"Created table {table_name} in PostgreSQL")

def check_postgres_table_exists(table_name):
    """Check if a table exists in PostgreSQL"""
    inspector = inspect(postgres_engine)
    return table_name in inspector.get_table_names()

def transfer_data(table_name, batch_size=10000):
    """Transfer data from SQLite to PostgreSQL in batches"""
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
            except OperationalError as e:
                logger.error(f"Error reading from SQLite: {str(e)}")
                break
            
            if df.empty:
                break
            
            # Write batch to PostgreSQL
            try:
                df.to_sql(table_name, postgres_engine, if_exists='append', index=False)
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

def create_indexes(table_name):
    """Create the same indexes in PostgreSQL as in SQLite"""
    logger.info(f"Creating indexes for table {table_name}")
    
    # Get indexes from SQLite
    with sqlite_engine.connect() as conn:
        result = conn.execute(text(f"SELECT name, sql FROM sqlite_master WHERE type='index' AND tbl_name='{table_name}'"))
        indexes = [(row[0], row[1]) for row in result if row[1] is not None]
    
    # Create indexes in PostgreSQL
    for index_name, sql in indexes:
        # Skip SQLite internal indexes
        if index_name.startswith('sqlite_'):
            continue
        
        # Convert SQLite index to PostgreSQL format
        # This is a simplified approach - complex indexes might need manual conversion
        try:
            # Extract the column list from the SQLite CREATE INDEX statement
            # Expected format: CREATE INDEX idx_name ON table_name (column1, column2, ...)
            parts = sql.split('(')
            if len(parts) != 2:
                logger.warning(f"Could not parse index SQL: {sql}")
                continue
                
            columns_part = parts[1].rstrip(');').strip()
            
            # Create the PostgreSQL index
            postgres_sql = f"CREATE INDEX IF NOT EXISTS {index_name} ON {table_name} ({columns_part})"
            with postgres_engine.connect() as conn:
                conn.execute(text(postgres_sql))
                conn.commit()
                
            logger.info(f"Created index {index_name} on {table_name}")
        except Exception as e:
            logger.error(f"Error creating index {index_name}: {str(e)}")

def migrate_table(table_name):
    """Migrate a single table from SQLite to PostgreSQL"""
    logger.info(f"Migrating table {table_name}")
    
    # Check if table already exists in PostgreSQL
    if check_postgres_table_exists(table_name):
        logger.warning(f"Table {table_name} already exists in PostgreSQL. Skipping table creation.")
    else:
        # Get table schema from SQLite
        columns = get_sqlite_table_schema(table_name)
        
        # Create table in PostgreSQL
        create_postgres_table(table_name, columns)
    
    # Transfer data
    transfer_data(table_name)
    
    # Create indexes
    create_indexes(table_name)
    
    logger.info(f"Table {table_name} migrated successfully")

def migrate_all_tables():
    """Migrate all tables from SQLite to PostgreSQL"""
    # Get all tables from SQLite
    tables = get_sqlite_tables()
    logger.info(f"Found {len(tables)} tables in SQLite database: {', '.join(tables)}")
    
    # Migrate each table
    for table_name in tables:
        try:
            migrate_table(table_name)
        except Exception as e:
            logger.error(f"Error migrating table {table_name}: {str(e)}")

if __name__ == "__main__":
    logger.info("Starting SQLite to PostgreSQL migration")
    
    try:
        # Test PostgreSQL connection
        with postgres_engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.scalar()
            logger.info(f"Connected to PostgreSQL: {version}")
        
        # Run migration
        migrate_all_tables()
        
        logger.info("Migration completed successfully")
    except Exception as e:
        logger.error(f"Migration failed: {str(e)}", exc_info=True)
"""
Reset PostgreSQL Database Script

This script drops all tables in the PostgreSQL database to provide a clean slate for migration.
"""

import sys
import os
import logging
from sqlalchemy import create_engine, text

# Add parent directory to path to import db_config
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.db_config import get_postgres_connection_url

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def reset_postgres_database():
    """Drop all tables in the PostgreSQL database"""
    try:
        # Connect to PostgreSQL
        postgres_url = get_postgres_connection_url()
        postgres_engine = create_engine(postgres_url)
        
        logger.info("Connected to PostgreSQL database")
        
        # List all tables
        with postgres_engine.connect() as conn:
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
            """))
            tables = [row[0] for row in result]
        
        if not tables:
            logger.info("No tables found in the PostgreSQL database")
            return
        
        logger.info(f"Found {len(tables)} tables: {', '.join(tables)}")
        
        # Drop each table
        with postgres_engine.connect() as conn:
            # Disable foreign key checks temporarily
            conn.execute(text("SET CONSTRAINTS ALL DEFERRED"))
            
            for table in tables:
                try:
                    conn.execute(text(f'DROP TABLE IF EXISTS "{table}" CASCADE'))
                    logger.info(f"Dropped table: {table}")
                except Exception as e:
                    logger.error(f"Error dropping table {table}: {str(e)}")
            
            conn.commit()
        
        logger.info("All tables have been dropped")
        
    except Exception as e:
        logger.error(f"Error resetting PostgreSQL database: {str(e)}", exc_info=True)

if __name__ == "__main__":
    logger.info("Starting PostgreSQL database reset")
    reset_postgres_database()
    logger.info("PostgreSQL database reset completed")
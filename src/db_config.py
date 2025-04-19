# Database configuration file for centralized connection management

import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
import logging

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Default SQLite path (used as fallback if PostgreSQL connection fails)
DEFAULT_SQLITE_PATH = r'sqlite:///C:\GitHub\Data_Insights\data\usaspending_historical.db?timeout=30'

# PostgreSQL connection parameters
PG_HOST = os.getenv('PG_HOST', 'localhost')
PG_PORT = os.getenv('PG_PORT', '5432')
PG_DATABASE = os.getenv('PG_DATABASE', 'usaspending')
PG_USER = os.getenv('PG_USER', 'postgres')
PG_PASSWORD = os.getenv('PG_PASSWORD', 'postgres')

def get_postgres_connection_url():
    """
    Build the PostgreSQL connection URL from environment variables.
    """
    return f"postgresql://{PG_USER}:{PG_PASSWORD}@{PG_HOST}:{PG_PORT}/{PG_DATABASE}"

def get_db_engine(use_sqlite_fallback=True):
    """
    Create and return a SQLAlchemy engine for database operations.
    
    Args:
        use_sqlite_fallback (bool): If True, falls back to SQLite if PostgreSQL connection fails
        
    Returns:
        SQLAlchemy engine instance
    """
    try:
        # Try to create PostgreSQL engine
        pg_url = get_postgres_connection_url()
        engine = create_engine(pg_url)
        
        # Test the connection
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            logger.info("Successfully connected to PostgreSQL database")
        
        return engine
    except Exception as e:
        logger.error(f"Error connecting to PostgreSQL: {str(e)}")
        
        if use_sqlite_fallback:
            logger.warning("Falling back to SQLite database")
            return create_engine(DEFAULT_SQLITE_PATH, connect_args={'timeout': 30})
        else:
            raise

def is_postgres_available():
    """
    Check if PostgreSQL connection is available.
    
    Returns:
        bool: True if PostgreSQL is available, False otherwise
    """
    try:
        engine = create_engine(get_postgres_connection_url())
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
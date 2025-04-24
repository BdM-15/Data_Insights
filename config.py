"""
Central configuration module for Data_Insights application.

This module handles all configuration settings, database connections, and environment variables.
It serves as the single source of truth for application configuration.
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from typing import Dict, Any, Optional
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/app.log"),
        logging.StreamHandler()
    ]
)

# Load environment variables from .env file
load_dotenv()

# Base Paths
PROJECT_ROOT = Path(__file__).parent.parent.absolute()
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
ARCHIVE_DIR = os.path.join(DATA_DIR, "archive")
LOGS_DIR = os.path.join(PROJECT_ROOT, "logs")

# Ensure directories exist
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(ARCHIVE_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)

# API Settings
# SAM.gov API
SAM_API_URL = "https://api.sam.gov/opportunities/v2/search"
SAM_API_KEY = os.getenv("SAM_API_KEY")
# Optional SAM.gov API parameters - loaded from .env if provided
SAM_PTYPE = os.getenv("SAM_PTYPE", "o")  # Default to "o" (opportunities)
SAM_TYPE_OF_SET_ASIDE = os.getenv("SAM_TYPE_OF_SET_ASIDE")  # Optional set-aside code
SAM_NAICS_CODE = os.getenv("SAM_NAICS_CODE")  # Optional NAICS code filter
SAM_STATE = os.getenv("SAM_STATE")  # Optional state filter
SAM_ZIP = os.getenv("SAM_ZIP")  # Optional ZIP code filter

# Rate limiting management for SAM.gov
SAM_API_RATE_LIMIT = int(os.getenv("SAM_API_RATE_LIMIT", "5").split('#')[0].strip())  # Requests per minute allowed
SAM_API_MAX_ATTEMPTS = int(os.getenv("SAM_API_MAX_ATTEMPTS", "8").split('#')[0].strip())  # Maximum retries on failure
SAM_API_BATCH_DELAY = int(os.getenv("SAM_API_BATCH_DELAY", "30").split('#')[0].strip())  # Seconds between batches
SAM_API_MIN_WAIT = int(os.getenv("SAM_API_MIN_WAIT", "30").split('#')[0].strip())  # Minimum wait for exponential backoff
SAM_API_MAX_WAIT = int(os.getenv("SAM_API_MAX_WAIT", "600").split('#')[0].strip())  # Maximum wait time (10 minutes)
SAM_API_BACKOFF_MULTIPLIER = int(os.getenv("SAM_API_BACKOFF_MULTIPLIER", "3").split('#')[0].strip())  # Multiplier for backoff
SAM_API_DEFAULT_RETRY_AFTER = int(os.getenv("SAM_API_DEFAULT_RETRY_AFTER", "120").split('#')[0].strip())  # Default retry wait
SAM_API_RETRY_BUFFER = int(os.getenv("SAM_API_RETRY_BUFFER", "30").split('#')[0].strip())  # Additional buffer to retry time
SAM_API_CHUNK_SIZE = int(os.getenv("SAM_API_CHUNK_SIZE", "7").split('#')[0].strip())  # Days per chunk for historical fetch
SAM_API_MAX_CONSECUTIVE_FAILURES = int(os.getenv("SAM_API_MAX_CONSECUTIVE_FAILURES", "3").split('#')[0].strip())  # Max failures

# NATO API
NATO_BASE_XML = "https://eportal.nspa.nato.int/eProcurement/XML/eprocurementdata.xml"

# USAspending.gov API
USASPENDING_API_URL = "https://api.usaspending.gov/api/v2/bulk_download/awards/"

# Database Settings
# PostgreSQL connection
PG_USER = os.getenv("PG_USER")
PG_PASSWORD = os.getenv("PG_PASSWORD")
PG_HOST = os.getenv("PG_HOST")
PG_PORT = os.getenv("PG_PORT")
PG_DATABASE = os.getenv("PG_DBNAME")  # Note: Using PG_DBNAME from .env file

# Database table names
TABLE_SAM_GOV = "fetched_opp_sam_gov"
TABLE_NATO_NSPA = "fetched_opp_nato_nspa"
TABLE_CURRENT_USASPENDING = "fetched_current_usaspending"
TABLE_HISTORICAL_USASPENDING = "fetched_historical_usaspending" 

# Database URL
DATABASE_URL = f"postgresql://{PG_USER}:{PG_PASSWORD}@{PG_HOST}:{PG_PORT}/{PG_DATABASE}"

# Request Settings
REQUEST_TIMEOUT = 30
MAX_WAIT_SECONDS = 900  # 15 minutes maximum wait time
DOWNLOAD_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

# Data Fetch Settings
# USAspending historical fetch settings
HISTORICAL_START_DATE = os.getenv("HISTORICAL_START_DATE")
HISTORICAL_END_DATE = os.getenv("HISTORICAL_END_DATE")
HISTORICAL_CHUNK_DAYS = int(os.getenv("HISTORICAL_CHUNK_DAYS", "2").split('#')[0].strip())

# Current data fetch settings
CURRENT_DAYS_LOOKBACK = int(os.getenv("CURRENT_DAYS_LOOKBACK", "7").split('#')[0].strip())

# Feature flags
ADMIN_USER_IDS = os.getenv("ADMIN_USER_IDS", "").split(",")

def get_db_config() -> Dict[str, str]:
    """
    Get database configuration from environment variables.
    
    Returns:
        Dictionary containing PostgreSQL connection parameters
    """
    return {
        "PG_USER": os.getenv("PG_USER", "postgres"),
        "PG_PASSWORD": os.getenv("PG_PASSWORD", ""),
        "PG_HOST": os.getenv("PG_HOST", "localhost"),
        "PG_PORT": os.getenv("PG_PORT", "5432"),
        "PG_DBNAME": os.getenv("PG_DBNAME", "usaspending"),
        "PG_SCHEMA": os.getenv("PG_SCHEMA", "public")
    }

def get_api_config() -> Dict[str, Any]:
    """
    Get API configuration from environment variables.
    
    Returns:
        Dictionary containing API configuration parameters
    """
    # Map SAM_API_KEY to SAM_GOV_API_KEY for backwards compatibility
    sam_api_key = os.getenv("SAM_GOV_API_KEY", os.getenv("SAM_API_KEY", ""))
    
    return {
        "SAM_GOV_API_KEY": sam_api_key,
        "SAM_PTYPE": os.getenv("SAM_PTYPE", "o"),
        "SAM_API_RATE_LIMIT": int(os.getenv("SAM_API_RATE_LIMIT", "5")),
        "SAM_API_MAX_ATTEMPTS": int(os.getenv("SAM_API_MAX_ATTEMPTS", "8")),
        "SAM_API_BATCH_DELAY": int(os.getenv("SAM_API_BATCH_DELAY", "30")),
        "SAM_API_MIN_WAIT": int(os.getenv("SAM_API_MIN_WAIT", "30")),
        "SAM_API_MAX_WAIT": int(os.getenv("SAM_API_MAX_WAIT", "600")),
        "SAM_API_BACKOFF_MULTIPLIER": float(os.getenv("SAM_API_BACKOFF_MULTIPLIER", "3")),
        "SAM_API_DEFAULT_RETRY_AFTER": int(os.getenv("SAM_API_DEFAULT_RETRY_AFTER", "120")),
        "SAM_API_RETRY_BUFFER": int(os.getenv("SAM_API_RETRY_BUFFER", "30")),
        "SAM_API_CHUNK_SIZE": int(os.getenv("SAM_API_CHUNK_SIZE", "7")),
        "SAM_API_MAX_CONSECUTIVE_FAILURES": int(os.getenv("SAM_API_MAX_CONSECUTIVE_FAILURES", "3")),
        "DAILY_REQUEST_LIMIT": int(os.getenv("DAILY_REQUEST_LIMIT", "1000")),
        "SAM_API_BASE_URL": os.getenv("SAM_API_BASE_URL", "https://api.sam.gov/prod/opportunities/v1/search")
    }

def get_app_config() -> Dict[str, Any]:
    """
    Get application configuration from environment variables.
    
    Returns:
        Dictionary containing application configuration parameters
    """
    return {
        "DEBUG_MODE": os.getenv("DEBUG_MODE", "False").lower() == "true",
        "LOG_LEVEL": os.getenv("LOG_LEVEL", "INFO"),
        "DATA_DIR": os.getenv("DATA_DIR", os.path.join(os.path.dirname(__file__), "data")),
        "ENABLE_AI_FEATURES": os.getenv("ENABLE_AI_FEATURES", "True").lower() == "true",
        "MAX_ROWS_DISPLAY": int(os.getenv("MAX_ROWS_DISPLAY", "100")),
        "CACHE_TTL": int(os.getenv("CACHE_TTL", "3600")),  # Cache time-to-live in seconds
        "ADMIN_USER_IDS": os.getenv("ADMIN_USER_IDS", "").split(","),
        "CURRENT_DAYS_LOOKBACK": int(os.getenv("CURRENT_DAYS_LOOKBACK", "7")),
        "HISTORICAL_START_DATE": os.getenv("HISTORICAL_START_DATE", "2019-03-29"),
        "HISTORICAL_END_DATE": os.getenv("HISTORICAL_END_DATE", "2025-04-10"),
        "HISTORICAL_CHUNK_DAYS": int(os.getenv("HISTORICAL_CHUNK_DAYS", "2"))
    }

def get_ollama_config() -> Dict[str, Any]:
    """
    Get Ollama configuration from environment variables.
    
    Returns:
        Dictionary containing Ollama configuration parameters
    """
    return {
        "OLLAMA_BASE_URL": os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        "OLLAMA_MODEL": os.getenv("OLLAMA_MODEL", "llama2"),
        "TEMPERATURE": float(os.getenv("TEMPERATURE", "0.7")),
        "MAX_TOKENS": int(os.getenv("MAX_TOKENS", "2000"))
    }

def get_log_config() -> Dict[str, Any]:
    """
    Get logging configuration from environment variables.
    
    Returns:
        Dictionary containing logging configuration parameters
    """
    return {
        "LOG_LEVEL": os.getenv("LOG_LEVEL", "INFO"),
        "LOG_FILE": os.getenv("LOG_FILE", os.path.join(LOGS_DIR, "app.log")),
        "LOG_FORMAT": os.getenv("LOG_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(message)s"),
        "LOG_TO_CONSOLE": os.getenv("LOG_TO_CONSOLE", "True").lower() == "true",
        "LOG_MAX_BYTES": int(os.getenv("LOG_MAX_BYTES", "10485760")),  # 10MB
        "LOG_BACKUP_COUNT": int(os.getenv("LOG_BACKUP_COUNT", "5"))
    }

# Validate critical configuration on module load
def validate_config() -> bool:
    """
    Validate critical configuration parameters.
    
    Returns:
        True if configuration is valid, False otherwise
    """
    db_config = get_db_config()
    if not db_config["PG_USER"] or not db_config["PG_PASSWORD"] or not db_config["PG_DBNAME"]:
        logging.warning("Database configuration is incomplete. Check your .env file.")
        return False
    
    return True

# Ensure logs directory exists
os.makedirs("logs", exist_ok=True)

# Perform validation when module is loaded
config_valid = validate_config()
"""
Configuration settings for the Data Insights application.
Centralizes all configuration by loading from environment variables (.env file).
"""

import os
from pathlib import Path
from dotenv import load_dotenv

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
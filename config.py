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

# CALC+ API (Contract-Awarded Labor Category)
CALC_API_URL = "https://api.gsa.gov/acquisition/calc/v3/api/ceilingrates/"
#CALC_API_KEY = os.getenv("CALC_API_KEY") # GSA CALC+ uses a public API, no key required

# SDMX API (Statistical Data and Metadata eXchange) - ILOSTAT
SDMX_API_URL = "https://www.ilo.org/sdmx/rest"
#SDMX_API_KEY = os.getenv("SDMX_API_KEY") # ILOSTAT uses a public API, no key required

# BLS API (Bureau of Labor Statistics)
BLS_API_URL = "https://api.bls.gov/publicAPI/v2"
BLS_API_KEY = os.getenv("BLS_API_KEY", "048186641837463e8d5eccba12e798a4")

# AI and GPU Configuration
# Ollama Configuration
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen:14b")  # Tool-calling capable model (primary)
OLLAMA_BACKUP_MODEL = os.getenv("OLLAMA_BACKUP_MODEL", "phi3:medium")  # Backup model
OLLAMA_TEMPERATURE = float(os.getenv("OLLAMA_TEMPERATURE", "0.7"))

# CUDA Configuration for GPU acceleration
CUDA_ENABLED = os.getenv("CUDA_ENABLED", "true").lower() == "true"
CUDA_DEVICE = os.getenv("CUDA_DEVICE", "0")  # GPU device ID
GPU_MEMORY_FRACTION = float(os.getenv("GPU_MEMORY_FRACTION", "0.8"))  # Use 80% of GPU memory

# Performance Settings
MAX_TOKENS = int(os.getenv("MAX_TOKENS", "512"))  # Reduced for faster response
CONTEXT_WINDOW = int(os.getenv("CONTEXT_WINDOW", "2048"))  # Reduced memory usage
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "30"))  # Faster timeout
MAX_ITERATIONS = int(os.getenv("MAX_ITERATIONS", "5"))  # Limit agent iterations


# Prompt Repository (for agent/LLM prompt templates)
def get_prompt_repo_path() -> str:
    """
    Get the path to the prompt repository for agent/LLM prompt templates.
    Returns:
        Path as a string
    """
    return os.getenv("PROMPT_REPO_PATH", str(Path(__file__).parent / "src" / "backend" / "ai" / "prompt_templates"))

# Langfuse Observability Config
def get_langfuse_config() -> Dict[str, Any]:
    """
    Get Langfuse configuration from environment variables.
    Returns:
        Dictionary containing Langfuse configuration parameters
    """
    return {
        "LANGFUSE_PUBLIC_KEY": os.getenv("LANGFUSE_PUBLIC_KEY"),
        "LANGFUSE_SECRET_KEY": os.getenv("LANGFUSE_SECRET_KEY"),
        "LANGFUSE_HOST": os.getenv("LANGFUSE_HOST", "http://localhost:3000"),
        "LANGFUSE_PROJECT": os.getenv("LANGFUSE_PROJECT", "default"),
        "LANGFUSE_ENVIRONMENT": os.getenv("LANGFUSE_ENVIRONMENT", "development"),
    }

# Ollama LLM/AI Integration Config
def get_ollama_config() -> Dict[str, Any]:
    """
    Get Ollama configuration from environment variables.
    Returns optimized configuration for Data Insights with CUDA acceleration.
    
    Returns:
        Dictionary containing Ollama configuration parameters
    """
    return {
        "OLLAMA_BASE_URL": os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        "OLLAMA_MODEL": OLLAMA_MODEL,  # Use the optimized model from direct config
        "TEMPERATURE": OLLAMA_TEMPERATURE,
        "MAX_TOKENS": MAX_TOKENS,  # Optimized for performance
        "CONTEXT_WINDOW": CONTEXT_WINDOW,
        "REQUEST_TIMEOUT": REQUEST_TIMEOUT,
        "MAX_ITERATIONS": MAX_ITERATIONS,
        "CUDA_ENABLED": CUDA_ENABLED
    }

# Placeholders for future MCP/AI agent config
def get_mcp_config() -> Dict[str, Any]:
    """
    Get MCP/AI agent configuration from environment variables.
    Returns:
        Dictionary containing MCP/AI agent configuration parameters
    """
    return {
        "MCP_SERVER_URL": os.getenv("MCP_SERVER_URL", "http://localhost:8003"),  # Updated to FastMCP port
        "MCP_API_KEY": os.getenv("MCP_API_KEY", ""),
        "PYDANTIC_AI_MODEL": OLLAMA_MODEL,  # Use optimized model
        "FASTMCP_DATABASE_PORT": 8003,
        "LLAMAINDEX_ENABLED": True
    }

def get_ai_config() -> Dict[str, Any]:
    """
    Get comprehensive AI configuration for Data Insights platform.
    Combines Ollama, CUDA, and performance settings.
    
    Returns:
        Dictionary containing all AI-related configuration
    """
    return {
        # Model Configuration
        "MODEL_NAME": OLLAMA_MODEL,
        "MODEL_TEMPERATURE": OLLAMA_TEMPERATURE,
        "MODEL_HOST": OLLAMA_HOST,
        
        # Performance Configuration  
        "MAX_TOKENS": MAX_TOKENS,
        "CONTEXT_WINDOW": CONTEXT_WINDOW,
        "REQUEST_TIMEOUT": REQUEST_TIMEOUT,
        "MAX_ITERATIONS": MAX_ITERATIONS,
        
        # CUDA Configuration
        "CUDA_ENABLED": CUDA_ENABLED,
        "CUDA_DEVICE": CUDA_DEVICE,
        "GPU_MEMORY_FRACTION": GPU_MEMORY_FRACTION,
        
        # MCP Integration
        "FASTMCP_PORT": 8003,
        "LLAMAINDEX_ENABLED": True,
        
        # Optimization Flags
        "OPTIMIZED_MODEL": "data_insights_optimized",
        "PERFORMANCE_MODE": "high_speed_low_memory"
    }

# Reason: Centralizes all AI/LLM/MCP config for easy access and validation

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


# Business term to column mapping for AI/agent SQL generation
BUSINESS_TERM_TO_COLUMN = {
    # Obligations & Amounts
    "Obligation Amount": "federal_action_obligation",
    "Award Amount": "award_amount",
    "Base and All Options Value": "base_and_all_options_value",
    "Base and Exercised Options Value": "base_and_exercised_options_value",
    "Potential Award Amount": "potential_total_value_of_award",
    "Current Award Amount": "current_total_value_of_award",
    "Total Obligated Amount": "total_obligated_amount",
    "Total Awarded Amount": "total_awarded_amount",
    "Modification Amount": "modification_obligation",
    # Dates
    "Award Date": "award_date",
    "Action Date": "action_date",
    "Start Date": "period_of_performance_start_date",
    "End Date": "period_of_performance_current_end_date",
    "Completion Date": "period_of_performance_potential_end_date",
    # Entities
    "Contractor": "recipient_name",
    "Contractor Name": "recipient_name",
    "Awarding Agency": "awarding_agency_name",
    "Funding Agency": "funding_agency_name",
    "Awarding Sub Agency": "awarding_sub_agency_name",
    "Funding Sub Agency": "funding_sub_agency_name",
    # Identifiers
    "Award ID": "award_id",
    "PIID": "piid",
    "Parent Award ID": "parent_award_id",
    "DUNS": "recipient_unique_id",
    "UEI": "recipient_uei",
    # Codes
    "NAICS": "naics_code",
    "NAICS Code": "naics_code",
    "NAICS Description": "naics_description",
    "PSC": "product_or_service_code",
    "PSC Code": "product_or_service_code",
    "PSC Description": "product_or_service_code_description",
    # Contract Details
    "Contract Type": "type_of_contract_pricing",
    "Award Type": "award_type",
    "Award Description": "award_description",
    "Contract Description": "description",
    "Competition Type": "extent_competed",
    "Set Aside": "type_set_aside",
    # Locations
    "Place of Performance": "place_of_performance_city_name",
    "Place of Performance State": "place_of_performance_state_code",
    "Place of Performance Country": "place_of_performance_country_code",
    "Place of Performance Zip": "place_of_performance_zip",
    # Misc
    "Award Status": "award_status",
    "Contract Status": "contract_status",
    "Subcontracting Plan": "subcontracting_plan",
    "Small Business": "recipient_business_type",
    "Contracting Office": "contracting_office_name",
    "Contracting Office Code": "contracting_office_code",
    # Add more mappings as needed
}

# Reason: Maps user/business terms to actual database column names for robust, LLM-driven SQL generation and tool use.
# Centralized here for consistency and maintainability across all modules.
"""
BUSINESS_TERM_TO_COLUMN (dict):
    Maps common business terms to actual database column names for use by AI agents and SQL generation.
    This mapping should be updated as the schema evolves and new business terms are introduced.

    Example:
        BUSINESS_TERM_TO_COLUMN = {
            "contract id": "contract_transaction_unique_key",
            "obligation": "federal_action_obligation",
            ...
        }
"""

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
        "SAM_API_BASE_URL": os.getenv("SAM_API_BASE_URL", "https://api.sam.gov/prod/opportunities/v1/search"),
        "BLS_API_URL": os.getenv("BLS_API_URL", "https://api.bls.gov/publicAPI/v2"),
        "BLS_API_KEY": os.getenv("BLS_API_KEY", "048186641837463e8d5eccba12e798a4")
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

def print_ai_config_summary():
    """Print a summary of AI configuration for debugging."""
    print("🤖 Data Insights AI Configuration Summary")
    print("=" * 50)
    print(f"Model: {OLLAMA_MODEL}")
    print(f"Temperature: {OLLAMA_TEMPERATURE}")
    print(f"Max Tokens: {MAX_TOKENS}")
    print(f"Context Window: {CONTEXT_WINDOW}")
    print(f"Request Timeout: {REQUEST_TIMEOUT}s")
    print(f"Max Iterations: {MAX_ITERATIONS}")
    print(f"CUDA Enabled: {CUDA_ENABLED}")
    if CUDA_ENABLED:
        print(f"CUDA Device: {CUDA_DEVICE}")
        print(f"GPU Memory: {GPU_MEMORY_FRACTION*100}%")
    print(f"FastMCP Port: 8003")
    print(f"Config Valid: {config_valid}")
    print("=" * 50)
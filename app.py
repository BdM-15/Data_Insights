"""
Main entry point for the Data_Insights application.

This is the main entry point that launches the Streamlit interface
and sets up necessary configurations for the Data_Insights application.
"""

import os
import sys
import logging
from datetime import datetime
import streamlit as st

# Add the project root to the path to ensure imports work correctly
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

# Import from project modules
from config import get_db_config, get_app_config, get_log_config

# Configure logging
log_config = get_log_config()
log_file = log_config.get("LOG_FILE", "logs/app.log")

# Ensure log directory exists
os.makedirs(os.path.dirname(log_file), exist_ok=True)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

logger.info(f"Starting Data_Insights application at {datetime.now()}")

# Import and call the main function from strategic_dashboard instead of launching a new process
try:
    sys.path.append(os.path.join(os.path.dirname(__file__), "src"))
    dashboard_path = os.path.join("src", "frontend", "pages", "strategic_dashboard.py")
    
    if not os.path.exists(dashboard_path):
        st.error(f"Error: Could not find {dashboard_path}")
        logger.error(f"Error: Could not find {dashboard_path}")
    else:
        logger.info(f"Importing dashboard from: {dashboard_path}")
        
        # Use a redirect approach
        from src.frontend.pages.strategic_dashboard import main
        
        # Call the main function directly
        main()
except Exception as e:
    st.error(f"Error loading the strategic dashboard: {str(e)}")
    logger.error(f"Error loading the strategic dashboard: {str(e)}")
    import traceback
    logger.error(traceback.format_exc())
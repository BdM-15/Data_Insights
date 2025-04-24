"""
Main entry point for the Data_Insights application.

This is the main entry point that launches the Streamlit interface
and sets up necessary configurations for the Data_Insights application.
"""

import os
import sys
import logging
from datetime import datetime

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

def main():
    """
    Main function to start the application.
    
    This function sets up logging and launches the Streamlit application
    with the strategic dashboard as the entry point.
    """
    logger.info(f"Starting Data_Insights application at {datetime.now()}")
    
    # Launch Streamlit application with the strategic dashboard
    streamlit_path = os.path.join("src", "frontend", "pages", "strategic_dashboard.py")
    
    # Check if the file exists before trying to run it
    if not os.path.exists(streamlit_path):
        logger.error(f"Error: Could not find {streamlit_path}")
        print(f"Error: Could not find {streamlit_path}")
        return
    
    logger.info(f"Launching Streamlit with: {streamlit_path}")
    os.system(f"streamlit run {streamlit_path}")

if __name__ == "__main__":
    main()
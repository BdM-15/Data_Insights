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

# Set Streamlit page configuration - Must be called as the first Streamlit command
st.set_page_config(
    page_title="Data Insights", 
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

logger.info(f"Starting Data_Insights application at {datetime.now()}")

# Import page functions
try:
    sys.path.append(os.path.join(os.path.dirname(__file__), "src"))
    
    # Import page functions
    from src.frontend.pages.strategic_dashboard import main as strategic_dashboard_main
    from src.frontend.pages.advanced_opportunity_explorer import main as capture_profiles_main
    from src.frontend.pages.capability_stance import main as capability_stance_main
    from src.frontend.pages.ai_chat import main as ai_chat_main
    # Optionally import placeholders for capture_profiles and ai_tools if they exist
    # from src.frontend.pages.capture_profiles import main as capture_profiles_page_main
    # from src.frontend.pages.ai_tools import main as ai_tools_page_main
    from src.frontend.components.sidebar_navigation import render_custom_navigation, get_page_config, render_sidebar_footer

    # Initialize session state for navigation
    if "current_page" not in st.session_state:
        st.session_state.current_page = "dashboard"  # Default page

    # Define pages for navigation (hidden from default streamlit navigation)
    pages = [
        st.Page(strategic_dashboard_main, title="Strategic Dashboard", icon="📊", url_path="dashboard"),
        st.Page(capture_profiles_main, title="Advanced Opportunity Explorer", icon="🔍", url_path="advanced-explorer"),
        st.Page(capability_stance_main, title="Capability Stance", icon="🏆", url_path="capability-stance"),
        st.Page(ai_chat_main, title="AI Chat with the Data", icon="🤖", url_path="ai-chat"),
        # st.Page(capture_profiles_page_main, title="Capture Profiles", icon="📄", url_path="capture-profiles"),
        # st.Page(ai_tools_page_main, title="AI Tools", icon="🤖", url_path="ai-tools"),
    ]
    
    # Create hidden navigation (we'll handle navigation manually)
    pg = st.navigation(pages, position="hidden")
      # Custom sidebar navigation
    with st.sidebar:
        page_config = get_page_config()
        selected_page = render_custom_navigation(
            pages=page_config,
            current_page=st.session_state.current_page,
            logo_path="c:/GitHub/Data_Insights/assets/logo.png"
        )
        
        # Update current page if selection changed
        if selected_page != st.session_state.current_page:
            st.session_state.current_page = selected_page
            st.rerun()
        
        # Add separator before page-specific content
        st.markdown("---")
        
        # Create a placeholder for page-specific sidebar content
        # This will be filled by individual pages
        sidebar_placeholder = st.empty()
        
        # Store the placeholder in session state so pages can access it
        st.session_state.sidebar_placeholder = sidebar_placeholder
      # Run the appropriate page based on current selection
    if st.session_state.current_page == "dashboard":
        strategic_dashboard_main()
    elif st.session_state.current_page == "advanced-explorer":
        capture_profiles_main()
    elif st.session_state.current_page == "capability-stance":
        capability_stance_main()
    elif st.session_state.current_page == "ai-chat":
        ai_chat_main()
    else:
        # Fallback to dashboard
        strategic_dashboard_main()
    
    # Add footer to sidebar after page content is rendered
    with st.sidebar:
        render_sidebar_footer()

except Exception as e:
    st.error(f"Error loading the application: {str(e)}")
    logger.error(f"Error loading the application: {str(e)}")
    import traceback
    logger.error(traceback.format_exc())
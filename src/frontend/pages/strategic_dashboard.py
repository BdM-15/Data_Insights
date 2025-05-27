"""
Capture Dashboard for the Data_Insights application.

This dashboard provides a high-level view of the government acquisition landscape
with a focus on NAICS 561210 (Facilities Support Services). The dashboard
visualizes key metrics including total obligations, award actions, top agencies,
funding sub-agencies, and funding offices.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta, date # Added 'date' here
import os
import sys
import traceback
import logging

# Add the project root to the path to ensure imports work correctly
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "../../../"))
sys.path.insert(0, project_root)

# Set up robust file logging (not terminal)
LOG_DIR = os.path.join(project_root, 'logs')
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)
LOG_FILE = os.path.join(LOG_DIR, 'dashboard.log')
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Import from project modules
from config import get_db_config, get_log_config
from src.backend.core.database import get_db_engine
# Remove get_unique_values import, it's used internally by filters.py
from src.frontend.components.export import create_download_button, add_export_section
from src.frontend.styles.theme import THEME
from src.frontend.styles.custom_css import generate_theme_css
from src.backend.data.app_processors.awards import (
    get_naics_data_optimized, # Directly use the optimized function for data loading
    # Keep other specific data processing functions if they are used by tabs
    get_award_summary_optimized, 
    get_top_agencies_optimized, 
    get_quarterly_trends_optimized, 
    get_agency_obligation_ratio_optimized, 
    get_expiring_contracts_optimized,
    get_contract_vehicles # Example if used by a tab
)
from src.backend.data.app_processors.competition import get_treemap_data, get_competitive_landscape
from src.frontend.utils.formatting import format_value
from src.frontend.pages.tabs.market_overview import render_tab as render_market_overview
from src.frontend.pages.tabs.future_opportunities import render_tab as render_future_opportunities
from src.frontend.pages.tabs.agency_intelligence import render_tab as render_agency_intelligence
from src.frontend.pages.tabs.competitive_analysis import render_tab as render_competitive_analysis
from src.frontend.pages.tabs.contract_vehicle_analysis import render_tab as render_contract_vehicle_analysis
from src.frontend.pages.tabs.geographic_analysis import render_tab as render_geographic_analysis
# Remove sidebar_layout, we will use st.sidebar directly
from src.frontend.components.filters import sidebar_filters

# Set Streamlit page configuration - Must be called as the first Streamlit command
st.set_page_config(
    page_title="Capture Dashboard", 
    page_icon="📊", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inject theme CSS at the top of the app
st.markdown(generate_theme_css(THEME), unsafe_allow_html=True)

# Remove old get_db_connection and use backend utility
# from src.backend.core.database import get_db_connection_with_status # Already handled by filters.py if needed there

def initialize_filter_params():
    """Initialize or update filter parameters in session state."""
    today = datetime.now().date()
    default_start = today - timedelta(days=365 * 6)

    if "filter_params" not in st.session_state:
        st.session_state.filter_params = {
            "naics_code": "561210",  # Default NAICS
            "start_date": default_start,
            "end_date": today,
            "agency": "All"
        }
    # Ensure date objects are used if strings are somehow stored
    if isinstance(st.session_state.filter_params.get("start_date"), str):
        st.session_state.filter_params["start_date"] = datetime.strptime(st.session_state.filter_params["start_date"], "%Y-%m-%d").date()
    if isinstance(st.session_state.filter_params.get("end_date"), str):
        st.session_state.filter_params["end_date"] = datetime.strptime(st.session_state.filter_params["end_date"], "%Y-%m-%d").date()


def load_filtered_data() -> pd.DataFrame:
    """
    Loads data based on current st.session_state.filter_params.
    The get_naics_data_optimized function will update session state for diagnostics.
    """
    params = st.session_state.filter_params
    logger.info(f"Loading data with session state filters: {params}")

    # Ensure date objects are converted to strings for the data loading function if necessary
    start_date_str = params["start_date"].strftime("%Y-%m-%d") if isinstance(params["start_date"], date) else params["start_date"]
    end_date_str = params["end_date"].strftime("%Y-%m-%d") if isinstance(params["end_date"], date) else params["end_date"]

    try:
        df = get_naics_data_optimized(
            naics_code=params["naics_code"] if params["naics_code"] != "All" else None,
            start_date=start_date_str,
            end_date=end_date_str,
            agency=params["agency"] if params["agency"] != "All" else None
        )
        logger.info(f"Data loaded. Rows: {st.session_state.get('data_row_count', 'N/A')}, Time: {st.session_state.get('data_load_time', 'N/A')}s")
        return df
    except Exception as e:
        logger.error(f"Error in load_filtered_data (strategic_dashboard.py): {str(e)}")
        logger.error(traceback.format_exc())
        st.session_state.data_row_count = 0
        st.session_state.data_load_time = 0.0 # Or measure time until error
        st.session_state.data_load_error = str(e)
        st.session_state.data_load_traceback = traceback.format_exc()
        return pd.DataFrame()


def main():
    """Main function to render the capture dashboard."""
    st.markdown(generate_theme_css(THEME), unsafe_allow_html=True)
    
    initialize_filter_params() # Ensures filter_params is set up

    # --- Data Loading ---
    # This now happens before sidebar rendering, using st.session_state.filter_params
    # The called function (get_naics_data_optimized) updates session_state for diagnostics
    df = load_filtered_data()

    # --- Sidebar Rendering ---
    with st.sidebar:
        st.image("c:/GitHub/Data_Insights/assets/logo.png")
        st.markdown("## Navigation")
        st.markdown("""
        <style>
        .nav-item { display: flex; align-items: center; padding: 10px 15px; margin-bottom: 8px; background-color: rgba(5, 27, 48, 0.6); border-radius: 8px; transition: all 0.2s ease; cursor: pointer; border-left: 3px solid transparent; }
        .nav-item:hover { background-color: rgba(0, 195, 255, 0.1); border-left: 3px solid rgba(0, 195, 255, 0.5); transform: translateX(3px); }
        .nav-item.active { background-color: rgba(0, 195, 255, 0.2); border-left: 3px solid rgba(0, 195, 255, 1); }
        .nav-icon { margin-right: 10px; color: #00C3FF; width: 20px; text-align: center; }
        .nav-text { color: white; font-weight: 500; }
        </style>
        <div class="nav-item active"><div class="nav-icon">📊</div><div class="nav-text">Capture Dashboard</div></div>
        <div class="nav-item"><div class="nav-icon">🔍</div><div class="nav-text">Advanced Data Explorer</div></div>
        <div class="nav-item"><div class="nav-icon">📈</div><div class="nav-text">Visualizations</div></div>
        <div class="nav-item"><div class="nav-icon">📑</div><div class="nav-text">Capture Profiles</div></div>
        <div class="nav-item"><div class="nav-icon">🤖</div><div class="nav-text">AI Tools</div></div>
        """, unsafe_allow_html=True)
        
        # sidebar_filters will read from st.session_state.filter_params for initial values
        # and its buttons will update st.session_state.filter_params and rerun.
        # It also reads st.session_state.data_row_count etc. for diagnostics.
        sidebar_filters(
            default_start=st.session_state.filter_params["start_date"], 
            today=st.session_state.filter_params["end_date"]
        )
        
        st.markdown("""
        <div class="user-section">
            <h4>About</h4>
            <p style="font-size: 0.8rem;">Data Insights v1.0<br>Last updated: April 2025</p>
        </div>
        """, unsafe_allow_html=True)

    # --- Main Content Rendering ---
    st.title("Capture Dashboard")
    st.markdown("""
    This dashboard provides a high-level view of the government acquisition landscape with a focus on NAICS 561210 (Facilities Support Services).
    It visualizes key metrics including total obligations, award actions, top agencies, funding sub-agencies, and funding offices.
    """) # Truncated for brevity, keep original

    if df.empty and st.session_state.get("data_load_error"):
        st.error(f"Could not load data for the dashboard. Error: {st.session_state.data_load_error}")
        if st.session_state.get("data_load_traceback"):
            with st.expander("Error Details"):
                st.code(st.session_state.data_load_traceback)
    elif df.empty and not st.session_state.get("data_load_error"):
         st.warning("No data matches the current filter criteria.")
    # else: # Data is loaded (or empty but no error), proceed to render tabs
    # Main dashboard tabs
    tab1, tab_future, tab2, tab3, tab4, tab5 = st.tabs([
        "Market Overview", 
        "Future Opportunities",
        "Agency Intelligence",
        "Competitive Analysis",
        "Contract Vehicle Analysis",
        "Geographic Analysis"
    ])
    with tab1:
        render_market_overview(df)
    with tab_future:
        render_future_opportunities(df)
    with tab2:
        render_agency_intelligence(df)
    with tab3:
        render_competitive_analysis(df)
    with tab4:
        render_contract_vehicle_analysis(df)
    with tab5:
        render_geographic_analysis(df)

if __name__ == "__main__":
    main()
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
from datetime import datetime, timedelta
import os
import sys
import traceback

# Add the project root to the path to ensure imports work correctly
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "../../../"))
sys.path.insert(0, project_root)

# Import from project modules
from config import get_db_config, get_log_config
from src.backend.core.database import get_db_engine, get_db_connection
from src.backend.core.queries import get_naics_data, get_unique_naics_codes
from src.backend.core.utils import format_value
from src.backend.data.processors.awards import get_award_summary, get_quarterly_trends, get_contract_vehicles, get_recipient_award_counts, get_recipient_obligations, get_expiring_contracts_processor
from src.backend.data.processors.agencies import get_top_agencies, get_agency_obligation_ratio
from src.backend.data.processors.competition import get_treemap_data, get_competitive_landscape
from src.frontend.components.filters import get_unique_values
from src.frontend.components.export import create_download_button, add_export_section

# Set Streamlit page configuration - Must be called as the first Streamlit command
st.set_page_config(
    page_title="Capture Dashboard", 
    page_icon="📊", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Import theme and style modules
from src.frontend.styles.theme import THEME, COLOR_SCALES, CHART_DEFAULTS
from src.frontend.styles.custom_css import get_all_css

# Apply all CSS
st.markdown(get_all_css(), unsafe_allow_html=True)

# Main function with enhanced error handling
def main():
    """Main function to render the capture dashboard."""
    
    # Title and description
    st.title("Capture Dashboard")
    st.markdown("""
    This dashboard provides a high-level view of the government acquisition landscape with a focus on NAICS 561210 (Facilities Support Services).
    It visualizes key metrics including total obligations, award actions, top agencies, funding sub-agencies, and funding offices.
    """)
    
    # Create the sidebar layout for navigation and filters
    with st.sidebar:
        # Restore logo to original size (no style modifications)
        st.image("c:/GitHub/Data_Insights/assets/logo.png")
        
        # Create application navigation 
        st.markdown("## Navigation")
        
        # Modern navigation links with sleek style (not hyperlink appearance)
        st.markdown("""
        <style>
        .nav-item {
            display: flex;
            align-items: center;
            padding: 10px 15px;
            margin-bottom: 8px;
            background-color: rgba(5, 27, 48, 0.6);
            border-radius: 8px;
            transition: all 0.2s ease;
            cursor: pointer;
            border-left: 3px solid transparent;
        }
        .nav-item:hover {
            background-color: rgba(0, 195, 255, 0.1);
            border-left: 3px solid rgba(0, 195, 255, 0.5);
            transform: translateX(3px);
        }
        .nav-item.active {
            background-color: rgba(0, 195, 255, 0.2);
            border-left: 3px solid rgba(0, 195, 255, 1);
        }
        .nav-icon {
            margin-right: 10px;
            color: #00C3FF;
            width: 20px;
            text-align: center;
        }
        .nav-text {
            color: white;
            font-weight: 500;
        }
        </style>
        
        <div class="nav-item active">
            <div class="nav-icon">📊</div>
            <div class="nav-text">Capture Dashboard</div>
        </div>
        <div class="nav-item">
            <div class="nav-icon">🔍</div>
            <div class="nav-text">Advanced Data Explorer</div>
        </div>
        <div class="nav-item">
            <div class="nav-icon">📈</div>
            <div class="nav-text">Visualizations</div>
        </div>
        <div class="nav-item">
            <div class="nav-icon">📑</div>
            <div class="nav-text">Capture Profiles</div>
        </div>
        <div class="nav-item">
            <div class="nav-icon">🤖</div>
            <div class="nav-text">AI Tools</div>
        </div>
        """, unsafe_allow_html=True)
        
        # Filters section
        st.markdown("## Filters")
        
        # Get database connection for NAICS and agency lists
        try:
            # Create engine for database connection
            # engine = get_db_engine() # Engine not directly needed here for NAICS if get_unique_naics_codes handles its own connection
            
            # Get all unique NAICS codes from the database
            naics_models = get_unique_naics_codes() # Returns List[NAICSData]
            # Extract naics_code for the selectbox, assuming 'All' is handled separately or not needed if list is comprehensive
            # If you want to display "code - description", you'll need to format it here.
            # For now, just using the codes. Adding "All" manually.
            naics_options = ["All"] + sorted([model.naics_code for model in naics_models if model.naics_code])
            if not naics_models and "All" not in naics_options: # Fallback if db call fails or returns empty
                naics_options = ["561210", "All"]
            elif "561210" not in naics_options and "All" not in naics_options: # Ensure default is present if list is very short
                 naics_options.insert(0, "561210")


            # Agency filter if database connection works
            # Assuming get_unique_values still works as intended or is a simple helper.
            # If get_unique_values needs refactoring, that's a separate step.
            engine = get_db_engine() # get_unique_values might still need an engine
            agency_options = ["All"] + get_unique_values(engine, "parent_award_agency_name")
        except Exception as e:
            st.error(f"Error loading filter values: {str(e)}")
            naics_options = ["561210", "All"] # Fallback
        
        # NAICS code filter
        selected_naics = st.selectbox("NAICS Code", naics_options, index=0)
        
        # Date range
        st.subheader("Date Range")
        today = datetime.now().date()
        default_start = today - timedelta(days=365*5)  # 5 years back
        start_date = st.date_input("Start Date", value=default_start)
        end_date = st.date_input("End Date", value=today)
        
        # Date validation
        if start_date > end_date:
            st.error("Start date must be before end date")
            end_date = start_date
        
        selected_agency = st.selectbox("Agency", agency_options)
        
        # PLACEHOLDER - Competition Intensity Filter
        # competition_levels = ["All Levels", "Low Competition (1-2 bidders)", 
        #                       "Medium Competition (3-5 bidders)", 
        #                       "High Competition (6+ bidders)"]
        # selected_competition = st.selectbox(
        #     "Competition Level",
        #     options=competition_levels,
        #     index=0,
        #     help="Filter by historical competition intensity"
        # )
        
        # Filter buttons in a row (Apply and Clear)
        col1, col2 = st.columns(2)
        with col1:
            apply_filters = st.button("Apply Filters", use_container_width=True)
        with col2:
            clear_filters = st.button("Clear Filters", use_container_width=True)
        
        # Add settings/about section at bottom of sidebar
        st.markdown("""
        <div class="user-section">
            <h4>About</h4>
            <p style="font-size: 0.8rem;">Data Insights v1.0<br>
            Last updated: April 2025</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Initialize session state for filter state
    if "filter_applied" not in st.session_state:
        st.session_state.filter_applied = False
        st.session_state.filter_params = {
            "naics_code": "561210",
            "start_date": default_start.strftime("%Y-%m-%d"),
            "end_date": today.strftime("%Y-%m-%d"),
            "agency": "All"
        }
    
    # Update filter state when apply button is clicked
    if apply_filters:
        st.session_state.filter_applied = True
        st.session_state.filter_params = {
            "naics_code": selected_naics if selected_naics != "All" else None,
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
            "agency": selected_agency if selected_agency != "All" else None
        }
    
    # Handle Clear Filters button
    if clear_filters:
        # Reset all filters to default values
        st.session_state.filter_applied = False
        st.session_state.filter_params = {
            "naics_code": "561210",
            "start_date": default_start.strftime("%Y-%m-%d"),
            "end_date": today.strftime("%Y-%m-%d"),
            "agency": "All"
        }
        # Rerun the app to update the UI
        st.experimental_rerun()
    
    # Load data based on current filters
    with st.spinner("Loading data..."):
        try:
            naics_code = st.session_state.filter_params["naics_code"] or "561210"
            start_date_str = st.session_state.filter_params["start_date"]
            end_date_str = st.session_state.filter_params["end_date"]
            
            # Load the data
            df = get_naics_data(naics_code, start_date_str, end_date_str)
            
            # Apply agency filter if selected
            if st.session_state.filter_params["agency"] and st.session_state.filter_params["agency"] != "All":
                df = df[df["parent_award_agency_name"] == st.session_state.filter_params["agency"]]
        except Exception as e:
            st.error(f"Error loading data: {str(e)}")
            st.error(traceback.format_exc())
            df = pd.DataFrame()
      # Import tab rendering functions
    from src.frontend.pages.tabs import (
        render_market_overview,
        render_future_opportunities,
        render_agency_intelligence,
        render_competitive_analysis,
        render_contract_vehicle_analysis,
        render_geographic_analysis
    )
    
    # Main dashboard tabs
    # IMPORTANT: The functions below (render_market_overview, etc.) are defined elsewhere (likely src/frontend/pages/tabs.py).
    # These functions will need to be updated to:
    # 1. Call the refactored backend processor functions (e.g., get_award_summary(df), get_top_agencies(df)).
    # 2. Adapt their Plotly charts and Streamlit display elements to use the Pydantic models returned by these processors.
    tab1, tab_future, tab2, tab3, tab4, tab5 = st.tabs([
        "Market Overview", 
        "Future Opportunities",
        "Agency Intelligence",
        "Competitive Analysis",
        "Contract Vehicle Analysis",
        "Geographic Analysis"
    ])
    
    # Tab 1: Market Overview
    with tab1:
        render_market_overview(df)
    
    # Tab Future: Future Opportunities
    with tab_future:
        render_future_opportunities(df)
    
    # Tab 2: Agency Intelligence
    with tab2:
        render_agency_intelligence(df)
    
    # Tab 3: Competitive Analysis
    with tab3:
        render_competitive_analysis(df)
    
    # Tab 4: Contract Vehicle Analysis
    with tab4:
        render_contract_vehicle_analysis(df)
    
    # Tab 5: Geographic Analysis
    with tab5:
        render_geographic_analysis(df)

if __name__ == "__main__":
    main()
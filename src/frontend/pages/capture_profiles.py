"""
Capture Profiles page for the Data_Insights application.

This page allows users to search and filter contracts, select specific contracts,
and generate detailed capture profiles for business development and capture management.
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, date
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
LOG_FILE = os.path.join(LOG_DIR, 'capture_profiles.log')
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Import from project modules
from config import get_db_config
from src.backend.core.database import get_db_engine
from src.frontend.styles.theme import THEME
from src.frontend.styles.custom_css import generate_theme_css

def main():
    """Main function to render the Capture Profiles page."""
    
    # Apply theme CSS
    st.markdown(generate_theme_css(THEME), unsafe_allow_html=True)
    
    # Add filters to the existing sidebar (created by main app)
    with st.sidebar:
        st.markdown("## Filters")
        
        # Placeholder filters - these will be expanded with full functionality
        col1, col2 = st.columns(2)
        
        with col1:
            start_date = st.date_input(
                "Start Date",
                value=datetime(2020, 1, 1).date(),
                help="Filter contracts by start date"
            )
            
        with col2:
            end_date = st.date_input(
                "End Date", 
                value=datetime.now().date(),
                help="Filter contracts by end date"
            )
        
        naics_code = st.selectbox(
            "NAICS Code",
            ["All", "561210", "541330", "541511", "541512"],
            help="Filter by NAICS industry code"
        )
        
        agency = st.selectbox(
            "Awarding Agency",
            ["All", "Department of Defense", "General Services Administration", "Department of Veterans Affairs"],
            help="Filter by awarding agency"
        )
        
        contract_id = st.text_input(
            "Contract/Order ID",
            placeholder="Enter contract ID...",
            help="Search by specific contract identifier"
        )
        
        awardee = st.text_input(
            "Awardee",
            placeholder="Enter company name...",
            help="Search by awardee company name"
        )
        
        min_value = st.number_input(
            "Min Contract Value",
            min_value=0,
            value=0,
            step=1000,
            help="Minimum contract value filter"
        )
        
        max_value = st.number_input(
            "Max Contract Value", 
            min_value=0,
            value=0,
            step=1000,
            help="Maximum contract value filter (0 = no limit)"
        )        # Filter buttons in columns with icons
        col1, col2 = st.columns(2)
        with col1:
            apply_filters = st.button("🔍 Apply Filters", use_container_width=True)
        with col2:
            clear_filters = st.button("🗑️ Clear Filters", use_container_width=True)
    
    # Main page content
    st.title("📑 Capture Profiles")
    st.markdown("""
    Search and filter contracts to generate detailed capture profiles for business development and capture management.
    """)
    
    # Placeholder content - this will be expanded with the full functionality
    with st.container():
        st.info("🚧 **Under Development**")
        st.markdown("""
        This page will provide:
        
        **Part 1: Contract Search & Selection**
        - Advanced filtering capabilities (implemented in sidebar)
        - Searchable contract table with checkboxes
        - Multi-select support (up to 5 contracts)
        
        **Part 2: Capture Profile Generation**
        - Award Details
        - Requirements Details  
        - Competitor Details
        - Subawards Details
        - Customer Details
        - Solicitation Details
        
        Each profile will be displayed in an expandable container for easy navigation.
        """)
    
    # Contract selection table preview
    with st.expander("📋 Contract Selection Table", expanded=True):
        # Sample data for preview
        sample_data = {
            "Select": [False, False, False],
            "Contract ID": ["W52P1J21C0001", "GS35F0119Y", "VA26821C0245"],
            "Awardee": ["CACI Inc", "Booz Allen Hamilton", "SAIC"],
            "Agency": ["Department of Defense", "GSA", "Department of Veterans Affairs"],
            "Value": ["$50M", "$25M", "$75M"],
            "Start Date": ["2021-01-15", "2021-03-01", "2021-06-15"],
            "End Date": ["2026-01-15", "2026-03-01", "2026-06-15"]
        }
        
        df = pd.DataFrame(sample_data)
        st.dataframe(df, use_container_width=True)
        st.button("Create Capture Profile", disabled=True, help="Feature under development")
    
    with st.expander("📊 Preview: Capture Profile Layout"):
        st.markdown("""
        **Award Details**
        - Contract identifiers, dates, values, performance locations
        
        **Requirements Details** 
        - NAICS/PSC codes, descriptions, acquisition programs
        
        **Competitor Details**
        - Prime contractor information, parent companies
        
        **Subawards Details**
        - Subcontractor analysis, supply chain insights
        
        **Customer Details**
        - Agency structure, funding sources, offices
        
        **Solicitation Details**
        - Competition type, set-asides, procurement procedures
        """)

if __name__ == "__main__":
    main()

"""
Filter components for the Data_Insights application.

This module provides reusable filter components for the Streamlit UI.
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os
import sys

# Add the project root to the path to ensure imports work correctly
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../")))

# Import from project modules
from config import get_db_config
from src.backend.core.database import get_db_engine

def get_unique_values(engine, column: str, table: str = "usaprime_cleaned", 
                     condition: str = None, dependencies: dict = None, add_all: bool = True) -> list:
    """
    Get unique values for a column with optional filtering based on dependencies.
    
    Args:
        engine: SQLAlchemy engine object
        column: Column name to get unique values for
        table: Table name (defaults to usaprime_cleaned)
        condition: Additional SQL condition to apply
        dependencies: Dictionary of dependent column values
        add_all: Whether to add 'All' as the first option
        
    Returns:
        List of unique values for the column
    """
    try:
        query = f"SELECT DISTINCT {column} FROM {table}"
        params = {}
        
        # Add conditions from dependencies
        if dependencies:
            conditions = []
            for dep_col, dep_val in dependencies.items():
                if dep_val and dep_val != "All":
                    conditions.append(f"{dep_col} = :{dep_col}")
                    params[dep_col] = dep_val
                    
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
                
        # Add additional condition if specified
        if condition:
            if "WHERE" in query:
                query += f" AND {condition}"
            else:
                query += f" WHERE {condition}"
                
        # Add final ordering
        query += f" ORDER BY {column}"
        
        # Execute query
        with engine.connect() as conn:
            from sqlalchemy import text
            result = conn.execute(text(query), params).fetchall()
            
        # Extract values and handle nulls
        values = [row[0] for row in result if row[0] is not None]
        
        # Add "All" option if requested
        if add_all:
            values = ["All"] + values
            
        return values
        
    except Exception as e:
        st.error(f"Error fetching unique values for {column}: {str(e)}")
        return ["All"] if add_all else []

def display_sidebar_filters():
    """
    Display filter controls in the sidebar.
    
    Returns:
        Dictionary containing the selected filter values
    """
    # Get database engine
    engine = get_db_engine()
    
    # Initialize filter state
    if "filters" not in st.session_state:
        st.session_state.filters = {}
    
    # Create filter form
    with st.form("filter_form"):
        # Date Range Filter
        st.subheader("Date Range")
        
        # Default to last 5 years
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=5*365)
        
        col1, col2 = st.columns(2)
        with col1:
            selected_start_date = st.date_input("Start Date", value=start_date)
        with col2:
            selected_end_date = st.date_input("End Date", value=end_date)
            
        # Validate date range
        if selected_end_date < selected_start_date:
            st.error("End date must be after start date")
            selected_end_date = selected_start_date
        
        # Agency Filter
        st.subheader("Agency")
        agencies = get_unique_values(engine, "awarding_agency_name")
        selected_agency = st.selectbox("Awarding Agency", agencies)
        
        # Sub-Agency Filter (dependent on Agency)
        sub_agencies = get_unique_values(
            engine, 
            "awarding_sub_agency_name", 
            dependencies={"awarding_agency_name": selected_agency if selected_agency != "All" else None}
        )
        selected_sub_agency = st.selectbox("Awarding Sub-Agency", sub_agencies)
        
        # Office Filter (dependent on Sub-Agency)
        offices = get_unique_values(
            engine,
            "awarding_office_name",
            dependencies={
                "awarding_agency_name": selected_agency if selected_agency != "All" else None,
                "awarding_sub_agency_name": selected_sub_agency if selected_sub_agency != "All" else None
            }
        )
        selected_office = st.selectbox("Awarding Office", offices)
        
        # Contractor Filter
        st.subheader("Contractor")
        contractors = get_unique_values(engine, "recipient_name")
        selected_contractor = st.selectbox("Recipient", contractors)
        
        # NAICS Code Filter
        st.subheader("NAICS/PSC Codes")
        naics_codes = get_unique_values(engine, "naics_code")
        selected_naics = st.selectbox("NAICS Code", naics_codes)
        
        # PSC Code Filter
        psc_codes = get_unique_values(engine, "product_or_service_code")
        selected_psc = st.selectbox("PSC Code", psc_codes)
        
        # Contract Type Filter
        st.subheader("Contract Details")
        contract_types = get_unique_values(engine, "type_of_contract_pricing")
        selected_contract_type = st.selectbox("Contract Type", contract_types)
        
        # Extent Competed Filter
        extent_competed_options = get_unique_values(engine, "extent_competed")
        selected_extent_competeds = st.multiselect(
            "Extent Competed", 
            options=extent_competed_options,
            default=["All"]
        )
        
        # Set-Aside Type Filter
        set_aside_types = get_unique_values(engine, "type_of_set_aside")
        selected_set_aside = st.selectbox("Set-Aside Type", set_aside_types)
        
        # Submit button
        submitted = st.form_submit_button("Apply Filters")
        
    # Store filter values in session state if form was submitted
    if submitted:
        st.session_state.filters = {
            "start_date": selected_start_date,
            "end_date": selected_end_date,
            "agency": selected_agency,
            "sub_agency": selected_sub_agency,
            "office": selected_office,
            "contractor": selected_contractor,
            "naics": selected_naics,
            "psc": selected_psc,
            "contract_type": selected_contract_type,
            "extent_competeds": selected_extent_competeds,
            "set_aside": selected_set_aside
        }
        
    # Return current filter values
    return st.session_state.filters if "filters" in st.session_state else {}
"""
Filter components for the Data_Insights application.

This module provides reusable filter components for the Streamlit UI, specifically for sidebar and dashboard filtering.
All filter logic is centralized here for maintainability and consistency across the app.
"""

import streamlit as st
from datetime import datetime, timedelta
from typing import Any, Dict, Optional
from src.backend.core.database import get_db_engine

# --- Utility: Get unique values for a column (with dependency support) ---
def get_unique_values(
    engine,
    column: str,
    table: str = "s3_processed.usaspending_prime_awards",
    condition: Optional[str] = None,
    dependencies: Optional[dict] = None,
    add_all: bool = True
) -> list:
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
        if dependencies:
            conditions = []
            for dep_col, dep_val in dependencies.items():
                if dep_val and dep_val != "All":
                    conditions.append(f"{dep_col} = :{dep_col}")
                    params[dep_col] = dep_val
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
        if condition:
            if "WHERE" in query:
                query += f" AND {condition}"
            else:
                query += f" WHERE {condition}"
        query += f" ORDER BY {column}"
        with engine.connect() as conn:
            from sqlalchemy import text
            result = conn.execute(text(query), params).fetchall()
        values = [row[0] for row in result if row[0] is not None]
        if add_all:
            values = ["All"] + values
        return values
    except Exception as e:
        st.error(f"Error fetching unique values for {column}: {str(e)}")
        return ["All"] if add_all else []

# --- Sidebar Filter Block (for use in sidebar_layout) ---
def sidebar_filters(
    default_start: datetime.date,
    today: datetime.date
) -> Dict[str, Any]:
    """
    Render sidebar filter controls for the dashboard.
    Args:
        default_start: Default start date for date range
        today: Default end date (today)
    Returns:
        Dictionary of selected filter values
    """
    engine = get_db_engine()
    st.markdown("## Filters")
    # NAICS filter
    try:
        naics_options = get_unique_values(engine, "naics_code")
    except Exception:
        naics_options = ["561210", "All"]
    selected_naics = st.selectbox("NAICS Code", naics_options, index=0, key="sidebar_naics")
    # Date range
    st.subheader("Date Range")
    start_date = st.date_input("Start Date", value=default_start, key="sidebar_start_date")
    end_date = st.date_input("End Date", value=today, key="sidebar_end_date")
    if start_date > end_date:
        st.error("Start date must be before end date")
        end_date = start_date
    # Agency filter
    try:
        agency_options = get_unique_values(engine, "parent_award_agency_name")
    except Exception:
        agency_options = ["All"]
    selected_agency = st.selectbox("Agency", agency_options, key="sidebar_agency")
    # Filter buttons
    col1, col2 = st.columns(2)
    with col1:
        apply_filters = st.button("Apply Filters", use_container_width=True, key="sidebar_apply_filters")
    with col2:
        clear_filters = st.button("Clear Filters", use_container_width=True, key="sidebar_clear_filters")

    # Handle Clear Filters: reset all filters to default values and rerun
    if clear_filters:
        st.query_params.clear()  # Clear any query params (new Streamlit API)
        st.session_state.clear()  # Clear all session state (safe since filters are only widgets)
        st.rerun()  # Use new Streamlit rerun API

    return {
        "naics_code": selected_naics,
        "start_date": start_date,
        "end_date": end_date,
        "agency": selected_agency,
        "apply_filters": apply_filters,
        "clear_filters": clear_filters,
    }

# --- (Optional) Advanced Filter Block for future expansion ---
# def advanced_filters(...):
#     ...
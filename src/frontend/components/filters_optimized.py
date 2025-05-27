"""
Filter components for the Data_Insights application.

This module provides reusable filter components for the Streamlit UI, specifically for sidebar and dashboard filtering.
All filter logic is centralized here for maintainability and consistency across the app.
"""

import streamlit as st
from datetime import datetime, timedelta
from typing import Any, Dict, Optional
from src.backend.core.database import get_db_engine
from src.backend.core.cache import cache_filter_values

# --- Utility: Get unique values for a column (with caching) ---
@cache_filter_values
def get_unique_values(
    column: str,
    table: str = "s3_processed.usaspending_prime_awards",
    condition: Optional[str] = None,
    dependencies: Optional[dict] = None,
    add_all: bool = True
) -> list:
    """
    Get unique values for a column with optional filtering based on dependencies.
    CACHED: Results are cached for 10 minutes to improve performance.

    Args:
        column: Column name to get unique values for
        table: Table name (defaults to s3_processed.usaspending_prime_awards)
        condition: Additional SQL condition to apply
        dependencies: Dictionary of dependent column values
        add_all: Whether to add 'All' as the first option
    Returns:
        List of unique values for the column
    """
    engine = get_db_engine()
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
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error fetching unique values for {column}: {str(e)}")
        st.error(f"Error fetching unique values for {column}: {str(e)}")
        return ["All"] if add_all else []


@cache_filter_values 
def get_naics_codes_optimized() -> list:
    """
    OPTIMIZED: Get NAICS codes using filter values table or materialized view when possible.
    """
    engine = get_db_engine()
    
    try:
        with engine.connect() as conn:
            from sqlalchemy import text
            
            # Try filter values table first (fastest)
            try:
                result = conn.execute(text("""
                    SELECT DISTINCT value 
                    FROM s3_processed.filter_values_naics_code 
                    WHERE value IS NOT NULL 
                    ORDER BY value
                """)).fetchall()
                if result:
                    return ["All"] + [row[0] for row in result]
            except Exception:
                pass
            
            # Fallback to main table with limit for performance
            result = conn.execute(text("""
                SELECT DISTINCT naics_code 
                FROM s3_processed.usaspending_prime_awards 
                WHERE naics_code IS NOT NULL 
                ORDER BY naics_code 
                LIMIT 1000
            """)).fetchall()
            
            return ["All"] + [row[0] for row in result]
            
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error fetching NAICS codes: {str(e)}")
        return ["All", "561210"]  # Safe fallback


@cache_filter_values
def get_agencies_optimized() -> list:
    """
    OPTIMIZED: Get agencies using materialized view when possible.
    """
    engine = get_db_engine()
    
    try:
        with engine.connect() as conn:
            from sqlalchemy import text
            
            # Try materialized view first (fastest and most relevant)
            try:
                result = conn.execute(text("""
                    SELECT parent_award_agency_name 
                    FROM s3_processed.mv_top_agencies 
                    ORDER BY rank_by_obligation 
                    LIMIT 100
                """)).fetchall()
                if result:
                    return ["All"] + [row[0] for row in result]
            except Exception:
                pass
            
            # Fallback to filter values table
            try:
                result = conn.execute(text("""
                    SELECT DISTINCT value 
                    FROM s3_processed.filter_values_parent_award_agency_name 
                    WHERE value IS NOT NULL 
                    ORDER BY value 
                    LIMIT 100
                """)).fetchall()
                if result:
                    return ["All"] + [row[0] for row in result]
            except Exception:
                pass
            
            # Final fallback to main table with limit
            result = conn.execute(text("""
                SELECT DISTINCT parent_award_agency_name 
                FROM s3_processed.usaspending_prime_awards 
                WHERE parent_award_agency_name IS NOT NULL 
                ORDER BY parent_award_agency_name 
                LIMIT 100
            """)).fetchall()
            
            return ["All"] + [row[0] for row in result]
            
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error fetching agencies: {str(e)}")
        return ["All"]  # Safe fallback


# --- Legacy function for backward compatibility ---
def get_unique_values_legacy(
    engine,
    column: str,
    table: str = "s3_processed.usaspending_prime_awards",
    condition: Optional[str] = None,
    dependencies: Optional[dict] = None,
    add_all: bool = True
) -> list:
    """
    Legacy function for backward compatibility.
    Use get_unique_values() instead for better performance.
    """
    return get_unique_values(column, table, condition, dependencies, add_all)


# --- Sidebar Filter Block (for use in sidebar_layout) ---
def sidebar_filters(
    default_start: datetime.date,
    today: datetime.date
) -> Dict[str, Any]:
    """
    Render sidebar filter controls for the dashboard.
    OPTIMIZED: Uses cached filter values for better performance.
    
    Args:
        default_start: Default start date for date range
        today: Default end date (today)
    Returns:
        Dictionary of selected filter values
    """
    st.markdown("## Filters")
    
    # NAICS filter - Use optimized function
    try:
        naics_options = get_naics_codes_optimized()
    except Exception:
        naics_options = ["All", "561210"]
    
    # Set default to 561210 if available, otherwise first option
    default_naics_index = 0
    if "561210" in naics_options:
        default_naics_index = naics_options.index("561210")
    elif "All" in naics_options:
        default_naics_index = naics_options.index("All")
    
    selected_naics = st.selectbox("NAICS Code", naics_options, index=default_naics_index, key="sidebar_naics")
    
    # Date range
    st.subheader("Date Range")
    start_date = st.date_input("Start Date", value=default_start, key="sidebar_start_date")
    end_date = st.date_input("End Date", value=today, key="sidebar_end_date")
    if start_date > end_date:
        st.error("Start date must be before end date")
        end_date = start_date
    
    # Agency filter - Use optimized function
    try:
        agency_options = get_agencies_optimized()
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
        # Clear cache to ensure fresh data
        from src.backend.core.cache import invalidate_cache_pattern
        invalidate_cache_pattern("filter_values")
        
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

# --- Performance monitoring utility ---
def get_filter_performance_stats():
    """Get performance statistics for filter operations."""
    from src.backend.core.cache import get_cache_stats
    return get_cache_stats()

# --- (Optional) Advanced Filter Block for future expansion ---
# def advanced_filters(...):
#     ...

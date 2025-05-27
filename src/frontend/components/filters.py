"""
Filter components for the Data_Insights application.

This module provides reusable filter components for the Streamlit UI, specifically for sidebar and dashboard filtering.
All filter logic is centralized here for maintainability and consistency across the app.
"""

import streamlit as st
from datetime import datetime, timedelta
from typing import Any, Dict, Optional
from src.backend.core.database import get_db_engine

# Cache for filter values to avoid repeated database queries
_filter_cache = {}
_cache_timestamp = {}
CACHE_DURATION = 300  # 5 minutes in seconds

def _get_cache_key(column: str, table: str, condition: str, dependencies: dict) -> str:
    """Create a cache key from filter parameters."""
    dep_str = str(sorted(dependencies.items())) if dependencies else ""
    return f"{table}.{column}.{condition}.{dep_str}"

def _is_cache_valid(cache_key: str) -> bool:
    """Check if cached data is still valid."""
    if cache_key not in _cache_timestamp:
        return False
    age = datetime.now().timestamp() - _cache_timestamp[cache_key]
    return age < CACHE_DURATION

@st.cache_data(ttl=300)  # Streamlit cache for 5 minutes
def _get_unique_values_cached(
    column: str,
    table: str = "s3_processed.usaspending_prime_awards",
    condition: Optional[str] = None,
    dependencies: Optional[dict] = None,
    add_all: bool = True
) -> list:
    """Cached version of get_unique_values for better performance."""
    cache_key = _get_cache_key(column, table, condition or "", dependencies or {})
    
    # Check application-level cache first
    if cache_key in _filter_cache and _is_cache_valid(cache_key):
        return _filter_cache[cache_key]
    
    # Query database
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
            
        # Update cache
        _filter_cache[cache_key] = values
        _cache_timestamp[cache_key] = datetime.now().timestamp()
        
        return values
    except Exception as e:
        st.error(f"Error fetching unique values for {column}: {str(e)}")
        return ["All"] if add_all else []

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
    Uses caching for better performance.

    Args:
        engine: SQLAlchemy engine object (kept for compatibility)
        column: Column name to get unique values for
        table: Table name (defaults to s3_processed.usaspending_prime_awards)
        condition: Additional SQL condition to apply
        dependencies: Dictionary of dependent column values
        add_all: Whether to add 'All' as the first option
    Returns:
        List of unique values for the column    """
    # Use cached version for better performance
    return _get_unique_values_cached(column, table, condition, dependencies, add_all)

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
    
    # Add simple timing diagnostics
    filters_start = datetime.now()
    
    # NAICS filter
    naics_start = datetime.now()
    try:
        naics_options = get_unique_values(engine, "naics_code")
        naics_time = (datetime.now() - naics_start).total_seconds()
    except Exception:
        naics_options = ["561210", "All"]
        naics_time = 0
    selected_naics = st.selectbox("NAICS Code", naics_options, index=0, key="sidebar_naics")
    
    # Date range
    st.subheader("Date Range")
    start_date = st.date_input("Start Date", value=default_start, key="sidebar_start_date")
    end_date = st.date_input("End Date", value=today, key="sidebar_end_date")
    if start_date > end_date:
        st.error("Start date must be before end date")
        end_date = start_date
      # Agency filter
    agency_start = datetime.now()
    try:
        agency_options = get_unique_values(engine, "parent_award_agency_name")
        agency_time = (datetime.now() - agency_start).total_seconds()
    except Exception:
        agency_options = ["All"]
        agency_time = 0
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
        st.rerun()  # Use new Streamlit rerun API    # Performance Diagnostics Section (below filter buttons)
    total_filter_time = (datetime.now() - filters_start).total_seconds()
    
    st.markdown("---")  # Separator line
    with st.expander("⏱️ Performance Diagnostics", expanded=False):
        st.markdown("**Filter Loading Times:**")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("NAICS Options", f"{naics_time:.3f}s", delta=None)
            st.metric("Agency Options", f"{agency_time:.3f}s", delta=None)
        with col2:
            st.metric("Total Filter Load", f"{total_filter_time:.3f}s", delta=None)
            # Show data loading time if available in session state
            data_load_time = st.session_state.get("data_load_time", None)
            if data_load_time is not None:
                row_count = st.session_state.get("data_row_count", "N/A")
                st.metric("Data Load Time", f"{data_load_time:.1f}s", delta=f"{row_count} rows" if row_count != "N/A" else None)
            
        # Cache status
        st.markdown("**Cache Status:**")
        naics_cache_key = _get_cache_key("naics_code", "s3_processed.usaspending_prime_awards", "", {})
        agency_cache_key = _get_cache_key("parent_award_agency_name", "s3_processed.usaspending_prime_awards", "", {})
        
        cache_col1, cache_col2 = st.columns(2)
        with cache_col1:
            naics_cached = "✅ Cached" if _is_cache_valid(naics_cache_key) else "❌ Not Cached"
            st.write(f"NAICS: {naics_cached}")
        with cache_col2:
            agency_cached = "✅ Cached" if _is_cache_valid(agency_cache_key) else "❌ Not Cached"
            st.write(f"Agency: {agency_cached}")
            
        # Performance alerts
        if total_filter_time > 5:
            st.error("🔴 Slow filter loading detected (>5s)")
        elif total_filter_time > 2:
            st.warning("🟡 Moderate filter loading time (>2s)")
        else:
            st.success("🟢 Fast filter loading (<2s)")
            
        # Show timing breakdown
        st.markdown("**Detailed Breakdown:**")
        timing_data = {
            "Component": ["NAICS Query", "Agency Query", "UI Rendering", "Total"],
            "Time (ms)": [
                f"{naics_time*1000:.1f}",
                f"{agency_time*1000:.1f}", 
                f"{(total_filter_time - naics_time - agency_time)*1000:.1f}",
                f"{total_filter_time*1000:.1f}"
            ]
        }
        st.dataframe(timing_data, hide_index=True, use_container_width=True)
          # Performance tips
        if total_filter_time > 2:
            st.info("💡 **Performance Tips:** Clear browser cache or restart app to refresh caches")
            
        # Database Diagnostics Section
        st.markdown("**Database Status:**")
          # Show data loading status if available
        data_load_time = st.session_state.get("data_load_time", None)
        data_row_count = st.session_state.get("data_row_count", None)
        data_load_error = st.session_state.get("data_load_error", None)
        
        if data_load_error:
            # Show error information
            st.error(f"❌ Error loading data: {data_load_error}")
            # Optionally show traceback in an expander for debugging
            data_load_traceback = st.session_state.get("data_load_traceback", None)
            if data_load_traceback:
                with st.expander("🐛 Error Details (for debugging)", expanded=False):
                    st.code(data_load_traceback, language='python')
        elif data_load_time is not None and data_row_count is not None:
            if data_row_count > 0:
                st.success(f"✅ Data loaded successfully: {data_row_count:,} records in {data_load_time:.1f}s")
            else:
                st.warning(f"⚠️ No data returned from query (completed in {data_load_time:.1f}s)")
        
        try:
            from src.backend.core.database import get_db_connection_with_status
            engine, db_status = get_db_connection_with_status()
            for msg in db_status["messages"]:
                st.info(msg)
            if not db_status["success"]:
                st.error(db_status["error"])
            else:
                with engine.connect() as conn:
                    from sqlalchemy import text
                    table_exists = conn.execute(text("SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name = 'usaspending_prime_awards' AND table_schema = 's3_processed')")).fetchone()[0]
                    if table_exists:
                        st.success("[+] Table 's3_processed.usaspending_prime_awards' exists")
                        row_count = conn.execute(text("SELECT COUNT(*) FROM s3_processed.usaspending_prime_awards")).fetchone()[0]
                        st.info(f"Row count: {row_count:,}")
                        if row_count == 0:
                            st.warning("Table 's3_processed.usaspending_prime_awards' exists but contains 0 rows.")
                    else:
                        st.error("[-] Table 's3_processed.usaspending_prime_awards' does not exist!")
                        tables = conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 's3_processed' ORDER BY table_name")).fetchall()
                        table_list = [t[0] for t in tables]
                        st.info(f"Available tables: {', '.join(table_list)}")
        except Exception as e:
            st.error(f"Database diagnostics error: {str(e)}")
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Database diagnostics error: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())

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
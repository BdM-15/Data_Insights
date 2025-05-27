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
) -> None: # Return type is None as it now modifies session_state and reruns
    """
    Render sidebar filter controls for the dashboard.
    Reads initial filter values from st.session_state.filter_params.
    Updates st.session_state.filter_params on Apply/Clear and triggers a rerun.
    Displays diagnostics based on st.session_state (e.g., data_row_count).

    Args:
        default_start: Default start date for date range (used if session state is missing for some reason)
        today: Default end date (today)
    """
    engine = get_db_engine()
    st.markdown("## Filters")
    
    filters_start = datetime.now()

    # Get current filter values from session_state, or use defaults
    current_params = st.session_state.get("filter_params", {})
    naics_value = current_params.get("naics_code", "561210")
    start_date_value = current_params.get("start_date", default_start)
    end_date_value = current_params.get("end_date", today)
    agency_value = current_params.get("agency", "All")

    # NAICS filter
    naics_start_time = datetime.now()
    try:
        naics_options = get_unique_values(engine, "naics_code")
        # Ensure current session state value is in options, or add it (e.g., if manually set via URL)
        if naics_value not in naics_options and naics_value != "All":
            naics_options.append(naics_value) # Or handle as an error/reset
            naics_options.sort()
            if "All" in naics_options and naics_options[0] != "All":
                 naics_options.remove("All")
                 naics_options.insert(0, "All")
        naics_idx = naics_options.index(naics_value) if naics_value in naics_options else 0
    except Exception as e:
        st.error(f"Failed to load NAICS options: {e}")
        naics_options = ["561210", "All"]
        naics_idx = 0
    naics_load_duration = (datetime.now() - naics_start_time).total_seconds()
    selected_naics = st.selectbox("NAICS Code", naics_options, index=naics_idx, key="sidebar_naics_widget")
    
    # Date range
    st.subheader("Date Range")
    selected_start_date = st.date_input("Start Date", value=start_date_value, key="sidebar_start_date_widget")
    selected_end_date = st.date_input("End Date", value=end_date_value, key="sidebar_end_date_widget")
    if selected_start_date > selected_end_date:
        st.error("Start date must be before end date")
        # selected_end_date = selected_start_date # Keep it simple, user will correct

    # Agency filter
    agency_start_time = datetime.now()
    try:
        agency_options = get_unique_values(engine, "parent_award_agency_name")
        if agency_value not in agency_options and agency_value != "All":
            agency_options.append(agency_value)
            agency_options.sort()
            if "All" in agency_options and agency_options[0] != "All":
                agency_options.remove("All")
                agency_options.insert(0, "All")
        agency_idx = agency_options.index(agency_value) if agency_value in agency_options else 0
    except Exception as e:
        st.error(f"Failed to load Agency options: {e}")
        agency_options = ["All"]
        agency_idx = 0
    agency_load_duration = (datetime.now() - agency_start_time).total_seconds()
    selected_agency = st.selectbox("Agency", agency_options, index=agency_idx, key="sidebar_agency_widget")
    
    # Filter buttons
    col1, col2 = st.columns(2)
    with col1:
        apply_filters_button = st.button("Apply Filters", use_container_width=True, key="sidebar_apply_filters_button")
    with col2:
        clear_filters_button = st.button("Clear Filters", use_container_width=True, key="sidebar_clear_filters_button")

    if apply_filters_button:
        st.session_state.filter_params = {
            "naics_code": selected_naics,
            "start_date": selected_start_date,
            "end_date": selected_end_date,
            "agency": selected_agency
        }
        st.rerun()

    if clear_filters_button:
        today_date = datetime.now().date()
        default_start_date = today_date - timedelta(days=365 * 6)
        st.session_state.filter_params = {
            "naics_code": "561210",
            "start_date": default_start_date,
            "end_date": today_date,
            "agency": "All"
        }
        # Clear widget states by changing their keys or explicitly resetting them if Streamlit version allows
        # For simplicity, we rely on rerun and session_state to repopulate them correctly.
        st.rerun()

    # Performance Diagnostics Section (below filter buttons)
    total_filter_ui_time = (datetime.now() - filters_start).total_seconds()
    
    st.markdown("---")
    with st.expander("⏱️ Performance Diagnostics", expanded=False):
        st.markdown("**Filter UI Component Loading Times:**")
        diag_col1, diag_col2 = st.columns(2)
        with diag_col1:
            st.metric("NAICS Options Query", f"{naics_load_duration:.3f}s")
            st.metric("Agency Options Query", f"{agency_load_duration:.3f}s")
        with diag_col2:
            st.metric("Total Filter UI Render", f"{total_filter_ui_time:.3f}s")
        
        # Cache status (remains useful for get_unique_values)
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
        if total_filter_ui_time > 5:
            st.error("🔴 Slow filter loading detected (>5s)")
        elif total_filter_ui_time > 2:
            st.warning("🟡 Moderate filter loading time (>2s)")
        else:
            st.success("🟢 Fast filter loading (<2s)")
            
        # Show timing breakdown
        st.markdown("**Detailed Breakdown:**")
        timing_data = {
            "Component": ["NAICS Query", "Agency Query", "UI Rendering", "Total"],
            "Time (ms)": [
                f"{naics_load_duration*1000:.1f}",
                f"{agency_load_duration*1000:.1f}", 
                f"{(total_filter_ui_time - naics_load_duration - agency_load_duration)*1000:.1f}",
                f"{total_filter_ui_time*1000:.1f}"
            ]
        }
        st.dataframe(timing_data, hide_index=True, use_container_width=True)
          # Performance tips
        if total_filter_ui_time > 2:
            st.info("💡 **Performance Tips:** Clear browser cache or restart app to refresh caches")
            
        # Consolidated Database Diagnostics Section
        st.markdown("**Database Status:**")
        
        # Retrieve data loading status from session_state here
        data_load_time = st.session_state.get("data_load_time", None)
        data_row_count_session = st.session_state.get("data_row_count", None)
        data_load_error = st.session_state.get("data_load_error", None)
        data_load_traceback = st.session_state.get("data_load_traceback", None) # Ensure traceback is also fetched

        # General Database Information
        try:
            from src.backend.core.database import get_db_connection_with_status
            engine, db_status = get_db_connection_with_status()
            for msg in db_status["messages"]: # Displays Host, Port, DB Name
                st.info(msg)
            if not db_status["success"]:
                st.error(db_status["error"])
            else:
                with engine.connect() as conn:
                    from sqlalchemy import text
                    table_exists = conn.execute(text("SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name = 'usaspending_prime_awards' AND table_schema = 's3_processed')")).fetchone()[0]
                    if table_exists:
                        st.success("[+] Table 's3_processed.usaspending_prime_awards' exists")
                        db_table_total_row_count = conn.execute(text("SELECT COUNT(*) FROM s3_processed.usaspending_prime_awards")).fetchone()[0]
                        st.info(f"Total rows in table: {db_table_total_row_count:,}")
                        
                        if db_table_total_row_count == 0:
                            st.warning("Table 's3_processed.usaspending_prime_awards' exists but contains 0 rows.")
                    else:
                        st.error("[-] Table 's3_processed.usaspending_prime_awards' does not exist!")
                        tables = conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 's3_processed' ORDER BY table_name")).fetchall()
                        table_list = [t[0] for t in tables]
                        st.info(f"Available tables: {', '.join(table_list)}")
        except Exception as e:
            st.error(f"Database diagnostics error: {str(e)}")
            import logging
            logger = logging.getLogger(__name__) # Ensure logger is defined or imported
            logger.error(f"Database diagnostics error: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())

        # Data Loading Diagnostic Message (at the bottom of Database Status)
        if data_load_error:
            st.error(f"❌ Error loading data: {data_load_error}")
            if data_load_traceback:
                with st.expander("🐛 Error Details", expanded=False):
                    st.code(data_load_traceback, language='python')
        elif data_load_time is not None and data_row_count_session is not None:
            if isinstance(data_row_count_session, int):
                if data_row_count_session > 0:
                    st.info(f"Loaded {data_row_count_session:,} rows in {data_load_time:.2f} secs.")
                elif data_row_count_session == 0:
                    st.warning(f"Loaded 0 rows in {data_load_time:.2f} secs. (No data matches filters)")
                else: # Should not happen for counts
                    st.info(f"Loaded {data_row_count_session:,} rows in {data_load_time:.2f} secs.") 
            else: # Fallback for unexpected types
                 st.info(f"Data loading status: {data_row_count_session} records, {data_load_time:.2f}s")
        else:
            st.caption("Data loading status will appear here after filters are applied.")
            
    # This function no longer returns filter values directly.
    # It modifies st.session_state.filter_params and triggers st.rerun().
    # The main app (strategic_dashboard.py) reads from st.session_state.filter_params.

# --- (Optional) Advanced Filter Block for future expansion ---
# def advanced_filters(...):
#     ...
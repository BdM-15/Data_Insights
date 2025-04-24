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
from src.backend.core.database import get_db_engine
from src.frontend.components.filters import get_unique_values
from src.frontend.components.export import create_download_button, add_export_section

# Set Streamlit page configuration - Must be called as the first Streamlit command
st.set_page_config(
    page_title="Capture Dashboard", 
    page_icon="📊", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Define theme colors
THEME = {
    'bg_color': '#051B30',         # Deep navy background
    'primary_color': '#00C3FF',    # Electric blue for primary elements
    'highlight_color': '#38ECFF',  # Bright cyan for highlights
    'accent1_color': '#5271FF',    # Electric indigo
    'accent2_color': '#FF2EDF',    # Electric pink/magenta
    'text_color': '#FFFFFF',       # White text
    'grid_color': 'rgba(0,195,255,0.15)' # Subtle electric blue grid lines
}

# Add custom CSS for the electric theme
st.markdown(f"""
<style>
    .main .block-container {{
        padding-top: 1rem;
        padding-bottom: 1rem;
    }}
    h1, h2, h3, h4, h5, h6 {{
        color: {THEME['primary_color']};
    }}
    .stTabs [data-baseweb="tab-list"] {{
        gap: 2px;
    }}
    .stTabs [data-baseweb="tab"] {{
        background-color: {THEME['bg_color']};
        border-radius: 4px 4px 0px 0px;
        color: {THEME['text_color']};
        padding: 10px 20px;
    }}
    .stTabs [aria-selected="true"] {{
        background-color: {THEME['primary_color']};
        color: {THEME['bg_color']};
        font-weight: bold;
    }}
    /* Updated metric styling */
    [data-testid="metric-container"] {{
        background-color: {THEME['bg_color']};
        border-radius: 8px;
        padding: 15px 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
        border-left: 4px solid {THEME['primary_color']};
        width: 100%;
        text-align: center;
    }}
    div[data-testid="stMetricValue"] {{
        font-size: 2rem;
        color: {THEME['highlight_color']};
        text-align: center;
        width: 100%;
    }}
    div[data-testid="stMetricLabel"] {{
        font-size: 1rem;
        color: {THEME['text_color']};
        text-align: center;
        width: 100%;
    }}
    div[data-testid="stMetricDelta"] {{
        text-align: center;
        width: 100%;
    }}
    /* Add styling for metric titles (labels) to ensure they're centered */
    .css-1wivap2[data-testid="metric-container"] > div:nth-child(1) {{
        display: flex;
        justify-content: center;
        text-align: center;
    }}
    /* Style the sidebar */
    [data-testid="stSidebar"] {{
        background-color: {THEME['bg_color']};
        border-right: 1px solid rgba(0, 195, 255, 0.1);
    }}
    /* Style sidebar navigation links */
    .sidebar-nav {{
        padding: 0.5rem 0;
        margin-bottom: 1rem;
    }}
    .sidebar-nav-item {{
        padding: 0.5rem 1rem;
        border-radius: 4px;
        margin-bottom: 0.25rem;
        display: block;
        color: {THEME['text_color']};
        text-decoration: none;
        transition: background-color 0.2s;
    }}
    .sidebar-nav-item:hover {{
        background-color: rgba(0, 195, 255, 0.1);
    }}
    .sidebar-nav-item.active {{
        background-color: {THEME['primary_color']};
        color: {THEME['bg_color']};
    }}
    /* User section */
    .user-section {{
        border-top: 1px solid rgba(0, 195, 255, 0.1);
        padding-top: 1rem;
        margin-top: 1rem;
    }}
</style>
""", unsafe_allow_html=True)

# Get database connection with debugging
def get_db_connection():
    """Get SQLAlchemy engine for database connection."""
    try:
        # Get database configuration
        db_config = get_db_config()
        st.sidebar.write("**Database Configuration:**")
        st.sidebar.write(f"Host: {db_config['PG_HOST']}")
        st.sidebar.write(f"Port: {db_config['PG_PORT']}")
        st.sidebar.write(f"Database: {db_config['PG_DBNAME']}")
        
        # Create engine for database connection
        engine = get_db_engine()
        
        # Test connection
        try:
            with engine.connect() as conn:
                from sqlalchemy import text
                result = conn.execute(text("SELECT 1")).fetchone()
                st.sidebar.success(f"✓ Database connection successful: {result}")
                
                # Check if the table exists
                result = conn.execute(text("SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name = 'usaprime_cleaned')")).fetchone()
                if result and result[0]:
                    st.sidebar.success("✓ Table 'usaprime_cleaned' exists")
                else:
                    st.sidebar.warning("⚠️ Table 'usaprime_cleaned' does not exist")
                    # List available tables to help debugging
                    tables = conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")).fetchall()
                    if tables:
                        table_list = [t[0] for t in tables]
                        st.sidebar.info(f"Available tables: {', '.join(table_list)}")
        except Exception as e:
            st.sidebar.error(f"Error executing test query: {str(e)}")
            return None
            
        return engine
    except Exception as e:
        st.sidebar.error(f"Error connecting to database: {str(e)}")
        st.sidebar.error(traceback.format_exc())
        return None

# Query functions with enhanced error reporting
@st.cache_data(ttl=3600)  # Cache for 1 hour
def get_naics_data(naics_code="561210", start_date=None, end_date=None):
    """
    Get data for specified NAICS code with date filtering.
    
    Args:
        naics_code: NAICS code to filter by (default: 561210)
        start_date: Start date for filtering
        end_date: End date for filtering
        
    Returns:
        DataFrame containing filtered data
    """
    engine = get_db_connection()
    if not engine:
        st.error("Database connection failed. Cannot retrieve data.")
        return pd.DataFrame()
    
    # Define possible table names to check
    table_names = ["usaprime_cleaned", "usaspending_cleaned", "usaprime", "usaspending", 
                  "fetched_current_usaspending", "contracts"]
    
    # Log query parameters
    st.sidebar.info(f"**Query Parameters:**\nNAICS: {naics_code}\nDate range: {start_date} to {end_date}")
    
    # Try each table name until we find data
    for table_name in table_names:
        try:
            # Build query
            query = f"""
                SELECT 
                    action_date,
                    modification_number,
                    federal_action_obligation,
                    parent_award_agency_name,
                    funding_sub_agency_name,
                    funding_office_name,
                    recipient_name,
                    award_type,
                    naics_code,
                    type_of_idc,
                    multiple_or_single_award_idv,
                    type_of_contract_pricing,
                    extent_competed
                FROM {table_name}
                WHERE 1=1
            """
            
            params = {}
            
            # Add NAICS code filter if specified and not 'All'
            if naics_code and naics_code != "All":
                query += " AND naics_code = :naics_code"
                params["naics_code"] = naics_code
            
            # Add date filters if specified
            if start_date:
                query += " AND action_date >= :start_date"
                params["start_date"] = start_date
            
            if end_date:
                query += " AND action_date <= :end_date"
                params["end_date"] = end_date  # Add end_date to params dictionary
                
            # Execute query - removed LIMIT to process all rows
            from sqlalchemy import text
            st.sidebar.info(f"Trying table: {table_name}")
            st.sidebar.info(f"Query params: {params}")
            
            # Use pandas chunking to handle large datasets efficiently
            conn = engine.connect()
            
            # First count how many rows we'll be processing
            count_query = f"""
                SELECT COUNT(*) FROM {table_name}
                WHERE 1=1
            """
            
            # Add the same filters to the count query
            if naics_code and naics_code != "All":
                count_query += " AND naics_code = :naics_code"
            
            if start_date:
                count_query += " AND action_date >= :start_date"
            
            if end_date:
                count_query += " AND action_date <= :end_date"
            
            # Get total row count
            try:
                row_count = pd.read_sql(text(count_query), conn, params=params).iloc[0, 0]
                st.sidebar.info(f"Found {row_count:,} total rows matching criteria")
            except Exception as e:
                st.sidebar.warning(f"Could not determine total row count: {str(e)}")
                row_count = "unknown"
            
            # Process data in chunks to handle large datasets
            chunk_size = 100000  # Adjust based on memory constraints
            df_list = []
            
            # Use chunking for potentially large datasets
            with st.sidebar.status(f"Loading data from {table_name}..."):
                for chunk in pd.read_sql(text(query), conn, params=params, chunksize=chunk_size):
                    df_list.append(chunk)
                    if len(df_list) == 1:
                        st.sidebar.info(f"Loaded first chunk of {len(chunk):,} rows")
                    else:
                        st.sidebar.info(f"Loaded {len(df_list)} chunks ({len(df_list) * chunk_size:,} rows)")
            
            # Combine all chunks
            if df_list:
                df = pd.concat(df_list, ignore_index=True)
                st.sidebar.success(f"✓ Successfully loaded {len(df):,} rows from '{table_name}'")
                return df
            else:
                st.sidebar.warning(f"⚠️ Table '{table_name}' exists but returned no data")
                
        except Exception as e:
            error_str = str(e).lower()
            if "table" in error_str and "exist" in error_str:
                st.sidebar.warning(f"⚠️ Table '{table_name}' does not exist")
            else:
                st.sidebar.error(f"Error querying '{table_name}': {str(e)}")
    
    # If we got here, no data was found
    st.sidebar.error("❌ Could not find data in any of the checked tables")
    return pd.DataFrame()

@st.cache_data(ttl=3600)
def get_award_summary(df):
    """
    Calculate summary metrics from the data.
    
    Args:
        df: DataFrame containing award data
        
    Returns:
        Dictionary of summary metrics
    """
    if df.empty:
        return {
            "total_obligations": 0,
            "total_award_actions": 0,
            "avg_award_value": 0,
            "active_contracts": 0
        }
    
    # Filter for base awards (no modifications)
    base_awards = df[df['modification_number'] == '0']
    
    # Calculate metrics
    total_obligations = df['federal_action_obligation'].sum()
    total_award_actions = len(base_awards)
    avg_award_value = total_obligations / total_award_actions if total_award_actions > 0 else 0
    active_contracts = len(base_awards)
    
    return {
        "total_obligations": total_obligations,
        "total_award_actions": total_award_actions,
        "avg_award_value": avg_award_value,
        "active_contracts": active_contracts
    }

@st.cache_data(ttl=3600)
def get_top_agencies(df, metric="count", n=15):
    """
    Get top agencies by award count or obligation amount.
    
    Args:
        df: DataFrame containing award data
        metric: 'count' for award actions, 'obligation' for dollar amount
        n: Number of top agencies to return
        
    Returns:
        DataFrame with top agencies
    """
    if df.empty:
        return pd.DataFrame()
    
    if metric == "count":
        # Filter to base awards only (no modifications)
        base_df = df[df['modification_number'] == '0']
        # Group by agency and count
        agency_data = base_df.groupby('parent_award_agency_name').size().reset_index(name='award_count')
        agency_data = agency_data.sort_values('award_count', ascending=False).head(n)
        return agency_data
    else:
        # Group by agency and sum obligations
        agency_data = df.groupby('parent_award_agency_name')['federal_action_obligation'].sum().reset_index()
        agency_data = agency_data.sort_values('federal_action_obligation', ascending=False).head(n)
        return agency_data

@st.cache_data(ttl=3600)
def get_quarterly_trends(df):
    """
    Calculate quarterly trends for obligations and award actions.
    Both obligations and award actions should be cumulative within each fiscal year.
    
    Args:
        df: DataFrame containing award data
        
    Returns:
        DataFrame with quarterly aggregates
    """
    if df.empty:
        return pd.DataFrame()
    
    # Convert action_date to datetime
    df['action_date'] = pd.to_datetime(df['action_date'])
    
    # Calculate fiscal year (Oct 1 to Sep 30)
    # US Federal fiscal year runs from October 1 to September 30
    # So if the month is >= 10 (October), it's in the next fiscal year
    df['fiscal_year'] = df['action_date'].dt.year
    df.loc[df['action_date'].dt.month >= 10, 'fiscal_year'] = df['action_date'].dt.year + 1
    
    # Map calendar quarters to fiscal quarters
    # Calendar Q4 (Oct-Dec) = Fiscal Q1, Calendar Q1 (Jan-Mar) = Fiscal Q2, etc.
    month_to_fiscal_quarter = {
        1: 2, 2: 2, 3: 2,  # Calendar Q1 = Fiscal Q2
        4: 3, 5: 3, 6: 3,  # Calendar Q2 = Fiscal Q3
        7: 4, 8: 4, 9: 4,  # Calendar Q3 = Fiscal Q4
        10: 1, 11: 1, 12: 1,  # Calendar Q4 = Fiscal Q1
    }
    df['fiscal_quarter'] = df['action_date'].dt.month.map(month_to_fiscal_quarter)
    
    # Create fiscal period label
    df['fiscal_period'] = df['fiscal_year'].astype(str) + '-Q' + df['fiscal_quarter'].astype(str)
    
    # Filter base awards for award count - simply filter for modification_number == '0'
    # Reason: As per your feedback, we'll just use a direct string comparison for simplicity
    base_awards = df[df['modification_number'] == '0']
    
    # Group by fiscal period for award counts
    award_counts = base_awards.groupby(['fiscal_year', 'fiscal_quarter', 'fiscal_period']).size().reset_index(name='award_count')
    
    # Group by fiscal period for obligations
    obligations = df.groupby(['fiscal_year', 'fiscal_quarter', 'fiscal_period'])['federal_action_obligation'].sum().reset_index()
    
    # Sort by fiscal year and quarter
    award_counts = award_counts.sort_values(['fiscal_year', 'fiscal_quarter'])
    obligations = obligations.sort_values(['fiscal_year', 'fiscal_quarter'])
    
    # Calculate cumulative sum for BOTH obligations AND award counts by fiscal year
    obligations['federal_action_obligation'] = obligations.groupby('fiscal_year')['federal_action_obligation'].cumsum()
    award_counts['award_count'] = award_counts.groupby('fiscal_year')['award_count'].cumsum()
    
    # Merge the two datasets
    quarterly_data = pd.merge(award_counts, obligations, on=['fiscal_year', 'fiscal_quarter', 'fiscal_period'], how='outer').fillna(0)
    
    # Sort by fiscal year and quarter for display
    quarterly_data = quarterly_data.sort_values(['fiscal_year', 'fiscal_quarter'])
    
    return quarterly_data

@st.cache_data(ttl=3600)
def get_agency_obligation_ratio(df):
    """
    Calculate action-to-obligation ratio for the scatter plot analysis.
    Uses normalization to prevent outliers from bunching the visualization.
    
    Args:
        df: DataFrame containing award data
        
    Returns:
        DataFrame with agency metrics for ratio analysis
    """
    if df.empty:
        return pd.DataFrame()
    
    # Filter to base awards for count
    base_awards = df[df['modification_number'] == '0']
    
    # Count base awards by agency
    agency_counts = base_awards.groupby('parent_award_agency_name').size().reset_index(name='award_count')
    
    # Sum obligations by agency
    agency_obligations = df.groupby('parent_award_agency_name')['federal_action_obligation'].sum().reset_index()
    
    # Merge the datasets
    agency_ratio = pd.merge(agency_counts, agency_obligations, on='parent_award_agency_name', how='outer').fillna(0)
    
    # Calculate average award value
    agency_ratio['avg_award_value'] = agency_ratio['federal_action_obligation'] / agency_ratio['award_count']
    agency_ratio['avg_award_value'] = agency_ratio['avg_award_value'].fillna(0)
    
    # Handle infinite values
    agency_ratio['avg_award_value'] = agency_ratio['avg_award_value'].replace([np.inf, -np.inf], 0)
    
    # Normalize data to prevent bunching due to outliers
    # Apply log transformation for better visualization of skewed data
    agency_ratio['award_count_normalized'] = np.log1p(agency_ratio['award_count'])
    agency_ratio['obligation_normalized'] = np.log1p(agency_ratio['federal_action_obligation'])
    
    # Add original values as hover data for reference
    agency_ratio['award_count_original'] = agency_ratio['award_count']
    agency_ratio['obligation_original'] = agency_ratio['federal_action_obligation']
    
    return agency_ratio

@st.cache_data(ttl=3600)
def get_contract_vehicles(df):
    """
    Analyze contract vehicle distribution.
    
    Args:
        df: DataFrame containing award data
        
    Returns:
        DataFrame with contract vehicle distribution
    """
    if df.empty or 'award_type' not in df.columns:
        return pd.DataFrame()
    
    # Count by award type
    vehicle_counts = df[df['modification_number'] == '0'].groupby('award_type').size().reset_index(name='count')
    
    # Calculate percentages
    total = vehicle_counts['count'].sum()
    vehicle_counts['percentage'] = vehicle_counts['count'] / total * 100
    
    return vehicle_counts

@st.cache_data(ttl=3600)
def get_competitive_landscape(df):
    """
    Analyze competitive landscape among contractors.
    
    Args:
        df: DataFrame containing award data
        
    Returns:
        DataFrame with competitor analysis
    """
    if df.empty:
        return pd.DataFrame()
    
    # Simply filter for modification_number '0' directly
    # No need for regex patterns or string normalization
    base_awards = df[df['modification_number'] == '0']
    
    # Count awards by recipient
    award_counts = base_awards.groupby('recipient_name').size().reset_index(name='award_count')
    
    # Sum obligations by recipient (using all records including modifications)
    obligations = df.groupby('recipient_name')['federal_action_obligation'].sum().reset_index()
    
    # Merge the datasets
    competitors = pd.merge(award_counts, obligations, on='recipient_name', how='outer').fillna(0)
    
    # Calculate market share
    total_obligations = competitors['federal_action_obligation'].sum()
    competitors['market_share'] = (competitors['federal_action_obligation'] / total_obligations * 100) if total_obligations > 0 else 0
    
    # Calculate win rate (percentage of total awards won by this recipient)
    total_awards = competitors['award_count'].sum()
    competitors['win_rate'] = (competitors['award_count'] / total_awards * 100) if total_awards > 0 else 0
    
    # Sort by market share
    competitors = competitors.sort_values('market_share', ascending=False)
    
    return competitors

@st.cache_data(ttl=3600)
def get_expiring_contracts(df, months_ahead=24):
    """
    Calculate the number of contracts expiring in the specified months ahead.
    
    Args:
        df: DataFrame containing award data
        months_ahead: Number of months ahead to check for expiring contracts
        
    Returns:
        Number of contracts expiring in the given timeframe
    """
    if df.empty or 'action_date' not in df.columns:
        return 0
    
    # Convert action_date to datetime if it isn't already
    df['action_date'] = pd.to_datetime(df['action_date'])
    
    # Get today's date dynamically
    today = datetime.now().date()
    
    # Calculate the end date (24 months from today)
    end_date = today + timedelta(days=30.44 * months_ahead)  # Approximate days per month
    
    # Check if we have period_of_performance_end_date in the dataframe
    perf_end_date_col = None
    possible_cols = ['period_of_performance_end_date', 'period_of_performance_end', 'pop_end_date', 'contract_end_date']
    
    for col in possible_cols:
        if col in df.columns:
            perf_end_date_col = col
            break
    
    # Filter for base awards only (no modifications)
    # Use the more robust way to identify base awards
    df['modification_number'] = df['modification_number'].astype(str).str.strip().str.lower()
    base_patterns = ['^0+$', '^none$', '^$', '^original$', '^base$']
    df['is_base_award'] = df['modification_number'].str.match('|'.join(base_patterns))
    base_awards = df[df['is_base_award'] == True]
    
    # Use the appropriate date column for expiration calculations
    if perf_end_date_col:
        # Convert to datetime
        base_awards[perf_end_date_col] = pd.to_datetime(base_awards[perf_end_date_col], errors='coerce')
        
        # Filter for contracts with end dates in the window
        future_expiring = base_awards[
            (base_awards[perf_end_date_col] <= pd.Timestamp(end_date)) & 
            (base_awards[perf_end_date_col] > pd.Timestamp(today))
        ]
    else:
        # Fallback to using action_date + 1 year as a very rough estimate
        # This is a simplified approach for the demo - real implementation would use proper end dates
        estimated_end_date = base_awards['action_date'] + pd.DateOffset(years=1)
        
        # Filter for contracts with estimated end dates in the window
        future_expiring = base_awards[
            (estimated_end_date <= pd.Timestamp(end_date)) & 
            (estimated_end_date > pd.Timestamp(today))
        ]
    
    # Count the expiring contracts
    return len(future_expiring)

def format_value(value, is_currency=False):
    """
    Format large numbers with K, M, B suffixes for better readability.
    
    Args:
        value: Number to format
        is_currency: Whether to add a dollar sign
        
    Returns:
        Formatted string
    """
    if abs(value) >= 1_000_000_000:
        formatted = f"{value/1_000_000_000:.2f}B"
    elif abs(value) >= 1_000_000:
        formatted = f"{value/1_000_000:.2f}M"
    elif abs(value) >= 1_000:
        formatted = f"{value/1_000:.1f}K"
    else:
        formatted = f"{value:.2f}"
    
    # Remove trailing zeros after decimal
    if "." in formatted:
        formatted = formatted.rstrip("0").rstrip(".")
    
    return f"${formatted}" if is_currency else formatted

# Main function with enhanced error handling
def main():
    """Main function to render the strategic dashboard."""
    
    # Title and description
    st.title("Strategic Dashboard")
    st.markdown("""
    This dashboard provides a high-level view of the government acquisition landscape with a focus on NAICS 561210 (Facilities Support Services).
    It visualizes key metrics including total obligations, award actions, top agencies, funding sub-agencies, and funding offices.
    """)
    
    # Create the sidebar layout for navigation and filters
    with st.sidebar:
        st.image("c:/GitHub/Data_Insights/assets/logo.png", width=250)
        
        # Create application navigation 
        st.markdown("## Navigation")
        
        # Main navigation sections from project documentation
        st.markdown("""
        <div class="sidebar-nav">
            <a href="#" class="sidebar-nav-item active">📊 Strategic Dashboard</a>
            <a href="#" class="sidebar-nav-item">🔍 Data Explorer</a>
            <a href="#" class="sidebar-nav-item">📈 Visualizations</a>
            <a href="#" class="sidebar-nav-item">📑 Capture Profiles</a>
            <a href="#" class="sidebar-nav-item">🤖 AI Tools</a>
        </div>
        """, unsafe_allow_html=True)
        
        # Filters section
        st.markdown("## Filters")
        
        # NAICS code filter
        naics_options = ["561210", "All"]  # Default to 561210 or allow all
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
        
        # Get database connection for agency list
        try:
            # Create engine for database connection
            engine = get_db_engine()
            
            # Agency filter if database connection works
            agency_options = ["All"] + get_unique_values(engine, "parent_award_agency_name")
            selected_agency = st.selectbox("Agency", agency_options)
        except Exception as e:
            st.error("Agency filter unavailable.")
            selected_agency = "All"
        
        # Apply filters button
        apply_filters = st.button("Apply Filters")
        
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
    
    # Main dashboard tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Market Overview", 
        "Agency Intelligence",
        "Competitive Analysis",
        "Contract Vehicle Analysis",
        "Geographic Analysis"
    ])
    
    # Tab 1: Market Overview
    with tab1:
        if not df.empty:
            # Get summary metrics
            summary = get_award_summary(df)
            
            # KPI metrics row
            st.subheader("Executive Summary")
            col1, col2, col3, col4, col5 = st.columns(5)
            
            with col1:
                st.metric("Total Obligations", format_value(summary['total_obligations'], is_currency=True))
            
            with col2:
                st.metric("Total Award Actions", format_value(summary['total_award_actions']))
            
            with col3:
                st.metric("Average Award Value", format_value(summary['avg_award_value'], is_currency=True))
            
            with col4:
                st.metric("Active Contracts", format_value(summary['active_contracts']))
                
            with col5:
                # Calculate expiring contracts (next 24 months)
                expiring_contracts = get_expiring_contracts(df, months_ahead=24)
                st.metric(
                    "Expiring Contracts (24mo)", 
                    format_value(expiring_contracts),
                    help="Number of contracts expiring in the next 24 months from today"
                )
            
            # Row for the two main visualizations
            col1, col2 = st.columns(2)
            
            with col1:
                # Combined Obligations and Award Actions Trend
                st.subheader("Obligations and Award Actions Trend")
                
                quarterly_data = get_quarterly_trends(df)
                
                if not quarterly_data.empty:
                    # Create figure with secondary y-axis
                    fig = make_subplots(specs=[[{"secondary_y": True}]])
                    
                    # Change bar chart to line chart for obligations
                    fig.add_trace(
                        go.Scatter(
                            x=quarterly_data["fiscal_period"],
                            y=quarterly_data["federal_action_obligation"],
                            name="Obligations",
                            line=dict(color=THEME["primary_color"], width=3),
                            mode="lines+markers",
                            marker=dict(size=8)
                        ),
                        secondary_y=False
                    )
                    
                    # Add line chart for award actions
                    fig.add_trace(
                        go.Scatter(
                            x=quarterly_data["fiscal_period"],
                            y=quarterly_data["award_count"],
                            name="Award Actions",
                            line=dict(color=THEME["accent2_color"], width=3),
                            mode="lines+markers",
                            marker=dict(size=8)
                        ),
                        secondary_y=True
                    )
                    
                    # Update layout
                    fig.update_layout(
                        title="Quarterly Trends",
                        legend=dict(
                            orientation="h",
                            yanchor="bottom",
                            y=1.02,
                            xanchor="right",
                            x=1
                        ),
                        plot_bgcolor=THEME["bg_color"],
                        paper_bgcolor=THEME["bg_color"],
                        font=dict(color=THEME["text_color"]),
                        margin=dict(l=40, r=40, t=40, b=40),
                    )
                    
                    # Update axes
                    fig.update_xaxes(
                        title_text="Fiscal Period",
                        showgrid=True,
                        gridcolor=THEME["grid_color"],
                        tickangle=45
                    )
                    
                    fig.update_yaxes(
                        title_text="Obligations ($)",
                        secondary_y=False,
                        showgrid=True,
                        gridcolor=THEME["grid_color"],
                        tickprefix="$",
                        tickformat=",."
                    )
                    
                    fig.update_yaxes(
                        title_text="Award Actions",
                        secondary_y=True,
                        showgrid=False
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning("Insufficient data for quarterly trends visualization.")
            
            with col2:
                # Action-to-Obligation Ratio Analysis (renamed and using normalized data)
                st.subheader("Action-to-Obligation Ratio Analysis")
                
                agency_ratio = get_agency_obligation_ratio(df)
                
                if not agency_ratio.empty and len(agency_ratio) > 1:  # Need at least 2 points for a meaningful scatter plot
                    # Create quadrant thresholds using normalized values
                    median_count = agency_ratio["award_count_normalized"].median()
                    median_obligation = agency_ratio["obligation_normalized"].median()
                    
                    # Create scatter plot with normalized values
                    fig = px.scatter(
                        agency_ratio,
                        x="award_count_normalized",
                        y="obligation_normalized",
                        size="avg_award_value",
                        color="parent_award_agency_name",
                        hover_name="parent_award_agency_name",
                        hover_data={
                            "award_count_normalized": False,
                            "obligation_normalized": False,
                            "award_count_original": ":.0f",
                            "obligation_original": ":$.2s",
                            "avg_award_value": ":$.2s"
                        },
                        size_max=50,
                        title="Action-to-Obligation Ratio Analysis (Normalized Scale)",
                        labels={
                            "award_count_normalized": "Award Actions (log scale)",
                            "obligation_normalized": "Obligations (log scale)",
                            "avg_award_value": "Avg. Award Value"
                        }
                    )
                    
                    # Add quadrant lines
                    fig.add_shape(
                        type="line",
                        x0=median_count,
                        y0=0,
                        x1=median_count,
                        y1=agency_ratio["obligation_normalized"].max() * 1.1,
                        line=dict(color="White", width=1, dash="dash")
                    )
                    
                    fig.add_shape(
                        type="line",
                        x0=0,
                        y0=median_obligation,
                        x1=agency_ratio["award_count_normalized"].max() * 1.1,
                        y1=median_obligation,
                        line=dict(color="White", width=1, dash="dash")
                    )
                    
                    # Add quadrant labels
                    fig.add_annotation(
                        x=median_count/2,
                        y=median_obligation*1.5,
                        text="High Value, Low Volume",
                        showarrow=False,
                        font=dict(color=THEME["highlight_color"])
                    )
                    
                    fig.add_annotation(
                        x=median_count*1.5,
                        y=median_obligation*1.5,
                        text="High Value, High Volume",
                        showarrow=False,
                        font=dict(color=THEME["highlight_color"])
                    )
                    
                    # Update layout
                    fig.update_layout(
                        plot_bgcolor=THEME["bg_color"],
                        paper_bgcolor=THEME["bg_color"],
                        font=dict(color=THEME["text_color"]),
                        margin=dict(l=40, r=40, t=40, b=40),
                        showlegend=False
                    )
                    
                    # Update tooltip to show original values
                    fig.update_traces(
                        hovertemplate="<b>%{hovertext}</b><br>" +
                                     "Award Actions: %{customdata[0]:,.0f}<br>" +
                                     "Obligations: %{customdata[1]:$,.0f}<br>" +
                                     "Avg Award: %{customdata[2]:$,.0f}"
                    )
                    
                    # Update axes
                    fig.update_xaxes(
                        showgrid=True,
                        gridcolor=THEME["grid_color"],
                        title_text="Award Actions (log scale)"
                    )
                    
                    fig.update_yaxes(
                        showgrid=True,
                        gridcolor=THEME["grid_color"],
                        title_text="Obligations (log scale)"
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning("Insufficient data for agency ratio analysis.")
            
            # Second row for additional visualizations
            col1, col2 = st.columns(2)
            
            with col1:
                # Contract Vehicle Distribution
                st.subheader("Contract Vehicle Distribution")
                
                vehicle_data = get_contract_vehicles(df)
                
                if not vehicle_data.empty:
                    fig = px.pie(
                        vehicle_data,
                        values="count",
                        names="award_type",
                        title="Contract Vehicle Types",
                        hole=0.4,
                        color_discrete_sequence=px.colors.sequential.Plasma
                    )
                    
                    # Update layout
                    fig.update_layout(
                        plot_bgcolor=THEME["bg_color"],
                        paper_bgcolor=THEME["bg_color"],
                        font=dict(color=THEME["text_color"]),
                        margin=dict(l=40, r=40, t=40, b=40)
                    )
                    
                    # Update traces
                    fig.update_traces(
                        textposition="inside",
                        textinfo="percent+label",
                        hoverinfo="label+percent+value"
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning("Insufficient data for contract vehicle analysis.")
            
            with col2:
                # Competitive Landscape
                st.subheader("Competitive Landscape")
                
                competitors = get_competitive_landscape(df)
                
                if not competitors.empty:
                    # Use only top 10 competitors
                    top_competitors = competitors.head(10)
                    
                    fig = px.treemap(
                        top_competitors,
                        path=["recipient_name"],
                        values="federal_action_obligation",
                        color="win_rate",
                        color_continuous_scale="Viridis",
                        title="Top Competitors by Market Share",
                        hover_data=["award_count", "market_share"],
                    )
                    
                    # Update layout
                    fig.update_layout(
                        plot_bgcolor=THEME["bg_color"],
                        paper_bgcolor=THEME["bg_color"],
                        font=dict(color=THEME["text_color"]),
                        margin=dict(l=40, r=40, t=40, b=40)
                    )
                    
                    # Update traces for better readability with abbreviated values
                    fig.update_traces(
                        hovertemplate="<b>%{label}</b><br>Obligations: " + 
                                     "$%{value:,.2f}<br>" +
                                     "Market Share: %{customdata[1]:.1f}%<br>" +
                                     "Award Count: %{customdata[0]}<extra></extra>",
                        texttemplate="%{label}<br>%{customdata[1]:.1f}%",
                        textfont=dict(size=11)
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning("Insufficient data for competitive landscape analysis.")
            
            # Top Agencies Analysis
            st.subheader("Top Agencies Analysis")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Top Agencies by Award Actions
                top_agencies_count = get_top_agencies(df, metric="count", n=15)
                
                if not top_agencies_count.empty:
                    fig = px.bar(
                        top_agencies_count,
                        x="award_count",
                        y="parent_award_agency_name",
                        title="Top Agencies by Award Actions",
                        orientation="h",
                        color="award_count",
                        color_continuous_scale="Blues",
                        labels={
                            "award_count": "Award Actions",
                            "parent_award_agency_name": "Agency"
                        }
                    )
                    
                    # Update layout
                    fig.update_layout(
                        plot_bgcolor=THEME["bg_color"],
                        paper_bgcolor=THEME["bg_color"],
                        font=dict(color=THEME["text_color"]),
                        margin=dict(l=40, r=40, t=40, b=40),
                        coloraxis_showscale=False,
                        uniformtext_minsize=10,  # Ensure minimum text size
                        uniformtext_mode='hide'  # Hide labels that don't fit
                    )
                    
                    # Update axes
                    fig.update_xaxes(
                        showgrid=True,
                        gridcolor=THEME["grid_color"],
                        tickformat=",.0f"  # Format tick values with commas
                    )
                    
                    fig.update_yaxes(
                        showgrid=False,
                        categoryorder="total ascending",
                        title=None  # Remove y-axis title for cleaner look
                    )
                    
                    # Add value annotations
                    fig.update_traces(
                        texttemplate="%{x:,.0f}",  # Format with commas
                        textposition="outside",
                        cliponaxis=False
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning("Insufficient data for top agencies by award actions.")
            
            with col2:
                # Top Agencies by Obligation Amount
                top_agencies_dollars = get_top_agencies(df, metric="obligation", n=15)
                
                if not top_agencies_dollars.empty:
                    fig = px.bar(
                        top_agencies_dollars,
                        x="federal_action_obligation",
                        y="parent_award_agency_name",
                        title="Top Agencies by Obligation Amount",
                        orientation="h",
                        color="federal_action_obligation",
                        color_continuous_scale="Blues",
                        labels={
                            "federal_action_obligation": "Obligation Amount ($)",
                            "parent_award_agency_name": "Agency"
                        }
                    )
                    
                    # Update layout
                    fig.update_layout(
                        plot_bgcolor=THEME["bg_color"],
                        paper_bgcolor=THEME["bg_color"],
                        font=dict(color=THEME["text_color"]),
                        margin=dict(l=40, r=40, t=40, b=40),
                        coloraxis_showscale=False,
                        uniformtext_minsize=10,
                        uniformtext_mode='hide'
                    )
                    
                    # Update axes
                    fig.update_xaxes(
                        showgrid=True,
                        gridcolor=THEME["grid_color"],
                        tickprefix="$",
                        tickformat=",.0f"  # Format numbers with commas
                    )
                    
                    fig.update_yaxes(
                        showgrid=False,
                        categoryorder="total ascending",
                        title=None  # Remove y-axis title for cleaner look
                    )
                    
                    # Add formatted value annotations
                    # Use our format_value function to make readable labels
                    annotations = []
                    for i, row in top_agencies_dollars.iterrows():
                        annotations.append({
                            "x": row["federal_action_obligation"],
                            "y": row["parent_award_agency_name"],
                            "text": format_value(row["federal_action_obligation"], is_currency=True),
                            "showarrow": False,
                            "xanchor": "left",
                            "xshift": 5,
                            "font": {"color": "white", "size": 10}
                        })
                    
                    fig.update_layout(annotations=annotations)
                    
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning("Insufficient data for top agencies by obligation amount.")
        else:
            # Help the user understand why there's no data
            st.warning("No data available. Please check the database connection details in the sidebar.")
            st.info("Possible issues:")
            st.markdown("""
            1. **Database Connection**: Verify PostgreSQL is running and connection details are correct
            2. **Table Names**: The table 'usaprime_cleaned' may not exist (sidebar will show available tables)
            3. **Data Availability**: There may be no data for NAICS code 561210 in the database
            4. **Date Range**: Try expanding the date range to capture more data
            
            See the Diagnostics section in the sidebar for more details.
            """)
    
    # Tab 2: Agency Intelligence (placeholder for now)
    with tab2:
        st.header("Agency Intelligence")
        st.info("This tab will provide detailed analysis of agencies, sub-agencies, and offices.")
        
        # We'll implement the detailed visualizations in the next phase
        st.markdown("""
        Planned visualizations:
        - Agency hierarchy analysis
        - Agency spending patterns
        - Set-aside utilization by agency
        """)
    
    # Tab 3: Competitive Landscape (placeholder for now)
    with tab3:
        st.header("Competitive Landscape")
        st.info("This tab will provide detailed analysis of competitors and market positioning.")
        
        # We'll implement the detailed visualizations in the next phase
        st.markdown("""
        Planned visualizations:
        - Competitor-Agency relationships
        - Contract type success rates
        - Win rate analysis by vehicle type
        """)
    
    # Tab 4: Contract Vehicle Analysis (placeholder for now)
    with tab4:
        st.header("Contract Vehicle Analysis")
        st.info("This tab will provide detailed analysis of contract vehicles.")
        
        # We'll implement the detailed visualizations in the next phase
        st.markdown("""
        Planned visualizations:
        - Vehicle preference by agency
        - Award type distributions
        - Success rates by contract type
        """)
    
    # Tab 5: Geographic Analysis (placeholder for now)
    with tab5:
        st.header("Geographic Analysis")
        st.info("This tab will provide detailed geographic analysis.")
        
        # We'll implement the detailed visualizations in the next phase
        st.markdown("""
        Planned visualizations:
        - Regional spending patterns
        - Performance by location
        - Geographic concentration of awards
        """)

if __name__ == "__main__":
    main()
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

# Import theme and style modules
from src.frontend.styles.theme import THEME, COLOR_SCALES, CHART_DEFAULTS
from src.frontend.styles.custom_css import get_all_css

# Apply all CSS
st.markdown(get_all_css(), unsafe_allow_html=True)

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
                st.sidebar.success(f"[+] Database connection successful: {result}")
                
                # Check if the table exists
                result = conn.execute(text("SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name = 'usaprime_cleaned')")).fetchone()
                if result and result[0]:
                    st.sidebar.success("[+] Table 'usaprime_cleaned' exists")
                else:
                    st.sidebar.warning(f"[-] Table 'usaprime_cleaned' doesn't exist")
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
                    recipient_parent_name,
                    award_type,
                    naics_code,
                    type_of_idc,
                    multiple_or_single_award_idv,
                    type_of_contract_pricing,
                    extent_competed,
                    transaction_description
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
                with engine.connect() as conn:
                    row_count = pd.read_sql(text(count_query), conn, params=params).iloc[0, 0]
                    st.sidebar.info(f"Found {row_count:,} total rows matching criteria")
            except Exception as e:
                st.sidebar.warning(f"Could not determine total row count: {str(e)}")
                row_count = "unknown"
            
            # Process data in chunks to handle large datasets efficiently
            chunk_size = 100000  # Adjust based on memory constraints
            df_list = []
            
            # Use chunking with a status indicator
            with st.sidebar.status(f"Loading data from {table_name}...") as status:
                conn = engine.connect()
                total_loaded = 0
                
                for chunk_num, chunk in enumerate(pd.read_sql(text(query), conn, params=params, chunksize=chunk_size)):
                    df_list.append(chunk)
                    total_loaded += len(chunk)
                    status.update(label=f"Loading data: {total_loaded:,} rows loaded ({chunk_num+1} chunks)")
                    
                # Combine all chunks
                if df_list:
                    if len(df_list) == 1:
                        # Only one chunk, no need for concatenation
                        df = df_list[0]
                    else:
                        # Multiple chunks, concatenate them
                        df = pd.concat(df_list, ignore_index=True)
                    
                    status.update(label=f"Complete! Loaded {len(df):,} rows from {table_name}")
                    st.sidebar.success(f"[+] Successfully loaded {len(df):,} rows from '{table_name}'")
                    return df
                else:
                    status.update(label=f"No data found in {table_name}")
                    st.sidebar.warning(f"[-] Table {table_name} exists but returns no data")
                
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
    
    # Ensure that size values are positive for scatter plot
    # Reason: Plotly requires size values to be positive numbers
    agency_ratio['scatter_size'] = np.abs(agency_ratio['avg_award_value'])
    
    # Cap extremely large values to prevent dominating the visualization
    size_cap = agency_ratio['scatter_size'].quantile(0.95)  # Cap at 95th percentile
    agency_ratio['scatter_size'] = agency_ratio['scatter_size'].clip(upper=size_cap)
    
    # Ensure minimum size for visibility
    min_size = 5
    agency_ratio['scatter_size'] = agency_ratio['scatter_size'].apply(lambda x: max(x, min_size))
    
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
def get_recipient_award_counts(df):
    """
    Get award counts by recipient (base awards only).
    
    Args:
        df: DataFrame containing award data
        
    Returns:
        DataFrame with recipient award counts
    """
    if df.empty:
        return pd.DataFrame()
    
    # Filter for base awards only
    base_awards = df[df['modification_number'] == '0']
    
    # Count awards by recipient
    award_counts = base_awards.groupby('recipient_name').size().reset_index(name='award_count')
    
    return award_counts

@st.cache_data(ttl=3600)
def get_recipient_obligations(df):
    """
    Get total obligations by recipient (all awards including modifications).
    
    Args:
        df: DataFrame containing award data
        
    Returns:
        DataFrame with recipient obligations
    """
    if df.empty:
        return pd.DataFrame()
    
    # Sum obligations by recipient (all records including modifications)
    obligations = df.groupby('recipient_name')['federal_action_obligation'].sum().reset_index()
    
    return obligations

@st.cache_data(ttl=3600)
def get_treemap_data(df):
    """
    Prepare data specifically for the competitive landscape treemap.
    Debug version that includes detailed diagnostics for troubleshooting.
    
    Args:
        df: DataFrame containing award data
        
    Returns:
        DataFrame specifically formatted for the treemap visualization
    """
    if df.empty:
        return pd.DataFrame()
    
    # Debug info in an expander in the sidebar
    with st.sidebar.expander("Treemap Data Diagnostics", expanded=False):
        st.write(f"Total rows in dataset: {len(df)}")
        
        # Check for NAICS code distribution
        naics_counts = df['naics_code'].value_counts().head(5)
        st.write("Top NAICS codes in current data:")
        st.write(naics_counts)
        
        # Get modification number distribution
        mod_counts = df['modification_number'].value_counts().head(10)
        st.write("Modification number distribution:")
        st.write(mod_counts)
        
        # Check data types
        st.write("Modification number data type:", df['modification_number'].dtype)
        
        # Sample a few rows to see actual values
        st.write("Sample rows from dataset:")
        st.write(df[['recipient_name', 'modification_number', 'federal_action_obligation']].head(3))
    
    # Create a deep copy to avoid modifying original
    filtered_df = df.copy()
    
    # Ensure modification_number is properly handled as a string
    filtered_df['modification_number'] = filtered_df['modification_number'].astype(str).str.strip()
    
    # Directly identify and count base awards
    filtered_df['is_base'] = filtered_df['modification_number'] == '0'
    
    # Get a list of all recipients for processing
    recipients = filtered_df['recipient_name'].unique()
    
    # Process each recipient to ensure accurate counts
    result_data = []
    
    # Process by recipient and funding sub-agency
    # This approach allows us to maintain the hierarchy for treemap
    for recipient in recipients:
        # Get data for this recipient
        recipient_df = filtered_df[filtered_df['recipient_name'] == recipient]
        
        # Get parent company name (use recipient name if parent is missing)
        parent_name = recipient_df['recipient_parent_name'].iloc[0] if 'recipient_parent_name' in recipient_df.columns and not pd.isna(recipient_df['recipient_parent_name'].iloc[0]) else recipient
        
        # Get the funding sub-agencies for this recipient
        funding_sub_agencies = recipient_df['funding_sub_agency_name'].unique()
        
        # For each funding sub-agency, create a row in the result data
        for sub_agency in funding_sub_agencies:
            # Get data for this recipient and sub-agency
            sub_agency_df = recipient_df[recipient_df['funding_sub_agency_name'] == sub_agency]
            
            # Get base award count (exact '0' modification number)
            base_count = sub_agency_df['is_base'].sum()
            
            # Get total obligations for this recipient and sub-agency
            total_obligations = sub_agency_df['federal_action_obligation'].sum()
            
            # Only add rows with actual obligations
            if total_obligations > 0:
                # Process contract descriptions - identify significant contracts
                if 'transaction_description' in sub_agency_df.columns:
                    # Filter for base awards with valid descriptions
                    valid_desc_df = sub_agency_df[~sub_agency_df['transaction_description'].isna()]
                    
                    if not valid_desc_df.empty:
                        # Sort contracts by obligation amount in descending order
                        sorted_contracts = valid_desc_df.sort_values('federal_action_obligation', ascending=False)
                        
                        # Get top contracts (up to 5 largest or 20% of value)
                        top_n = min(5, len(sorted_contracts))
                        top_contracts = sorted_contracts.head(top_n)
                        
                        # For each significant contract, create an entry with rich description
                        for _, contract in top_contracts.iterrows():
                            # Clean and format description
                            description = str(contract['transaction_description'])
                            if description == 'nan' or not description or description.lower() in ['none', 'n/a']:
                                description = f"Contract #{contract['modification_number']}"
                            else:
                                description = description.strip().replace('\n', ' ').replace('\r', '')
                                if len(description) > 100:
                                    description = description[:97] + '...'
                            
                            # Format amount for better readability
                            amount = contract['federal_action_obligation']
                            amount_str = f"${amount/1_000_000:.1f}M" if amount >= 1_000_000 else f"${amount/1_000:.1f}K" if amount >= 1_000 else f"${amount:.0f}"
                            
                            # Add to results with rich description
                            result_data.append({
                                'recipient_parent_name': parent_name,
                                'recipient_name': recipient,
                                'funding_sub_agency_name': sub_agency if not pd.isna(sub_agency) else 'Unknown',
                                'transaction_description': f"{amount_str}: {description}",
                                'federal_action_obligation': contract['federal_action_obligation'],
                                'award_count': 1 if contract['is_base'] else 0
                            })
                            
                        # Add remaining as "Other Contracts"
                        remaining = sorted_contracts[~sorted_contracts.index.isin(top_contracts.index)]
                        if not remaining.empty:
                            remaining_value = remaining['federal_action_obligation'].sum()
                            remaining_count = len(remaining)
                            
                            result_data.append({
                                'recipient_parent_name': parent_name,
                                'recipient_name': recipient,
                                'funding_sub_agency_name': sub_agency if not pd.isna(sub_agency) else 'Unknown',
                                'transaction_description': f"Other Contracts ({remaining_count})",
                                'federal_action_obligation': remaining_value,
                                'award_count': sum(remaining['is_base'])
                            })
                    else:
                        # No valid descriptions
                        result_data.append({
                            'recipient_parent_name': parent_name,
                            'recipient_name': recipient,
                            'funding_sub_agency_name': sub_agency if not pd.isna(sub_agency) else 'Unknown',
                            'transaction_description': 'All Contracts',
                            'federal_action_obligation': total_obligations,
                            'award_count': base_count
                        })
                else:
                    # No transaction_description column
                    result_data.append({
                        'recipient_parent_name': parent_name,
                        'recipient_name': recipient,
                        'funding_sub_agency_name': sub_agency if not pd.isna(sub_agency) else 'Unknown',
                        'transaction_description': 'All Contracts',
                        'federal_action_obligation': total_obligations,
                        'award_count': base_count
                    })
    
    # Convert to DataFrame
    treemap_data = pd.DataFrame(result_data)
    
    # Calculate market share
    total_obligations = treemap_data['federal_action_obligation'].sum()
    if total_obligations > 0:
        treemap_data['market_share'] = treemap_data['federal_action_obligation'] / total_obligations * 100
    else:
        treemap_data['market_share'] = 0
    
    # Calculate win rate
    total_awards = treemap_data['award_count'].sum()
    if total_awards > 0:
        treemap_data['win_rate'] = treemap_data['award_count'] / total_awards * 100
    else:
        treemap_data['win_rate'] = 0
    
    # Sort by market share
    treemap_data = treemap_data.sort_values('market_share', ascending=False)
    
    # Debug specific recipients if they exist in the data
    problem_recipients = ['National Technology & Engineering Solutions of Sandia, LLC', 
                         'Vectrus Systems LLC', 
                         'NTESS, LLC']
    
    with st.sidebar.expander("Problem Recipients Analysis", expanded=False):
        for prob_recip in problem_recipients:
            matching_rows = filtered_df[filtered_df['recipient_name'].str.contains(prob_recip, case=False, na=False)]
            if not matching_rows.empty:
                st.write(f"Analysis for: {prob_recip}")
                st.write(f"Total rows: {len(matching_rows)}")
                
                # Show modification numbers for this recipient
                mod_dist = matching_rows['modification_number'].value_counts().head(5)
                st.write("Modification distribution:")
                st.write(mod_dist)
                
                # Check if there are any base awards with mod number = '0'
                base_rows = matching_rows[matching_rows['modification_number'] == '0']
                st.write(f"Base awards (mod='0'): {len(base_rows)}")
                
                # Result in treemap:
                recip_in_treemap = treemap_data[treemap_data['recipient_name'].str.contains(prob_recip, case=False, na=False)]
                if not recip_in_treemap.empty:
                    st.write("In treemap data:")
                    st.write(recip_in_treemap[['recipient_name', 'award_count', 'federal_action_obligation']])
    
    return treemap_data

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
    
    # Use only exact string comparison for modification_number
    base_awards = df[df['modification_number'] == '0']
    
    # Count awards by recipient
    award_counts = base_awards.groupby('recipient_name').size().reset_index(name='award_count')
    
    # Sum obligations by recipient (using all records including modifications)
    obligations = df.groupby('recipient_name')['federal_action_obligation'].sum().reset_index()
    
    # Merge the datasets - using outer join to include all recipients
    competitors = pd.merge(award_counts, obligations, on='recipient_name', how='outer').fillna(0)
    
    # Calculate market share
    total_obligations = competitors['federal_action_obligation'].sum()
    competitors['market_share'] = (competitors['federal_action_obligation'] / total_obligations * 100) if total_obligations > 0 else 0
    
    # Calculate win rate (percentage of total awards won by this recipient)
    total_awards = competitors['award_count'].sum()
    competitors['win_rate'] = (competitors['award_count'] / total_awards * 100) if total_awards > 0 else 0
    
    # Sort by market share
    competitors = competitors.sort_values('market_share', ascending=False)
    
    # Add debugging - examine data just before return for problem contractors
    with st.sidebar.expander("Competitive Landscape Analysis", expanded=False):
        st.write(f"Total competitors: {len(competitors)}")
        st.write(f"Total with zero award counts: {len(competitors[competitors['award_count'] == 0])}")
        
        # Look at top contractors by obligation
        top_by_obligation = competitors.nlargest(5, 'federal_action_obligation')
        st.write("Top 5 by obligation:")
        st.write(top_by_obligation[['recipient_name', 'award_count', 'federal_action_obligation', 'market_share']])
        
        # Show debug message explaining limited historical data
        st.info("Note: Zero award counts may appear for contractors whose base awards occurred before your data collection period began (~2.5 years). The treemap still accurately shows their market share based on obligations during the selected timeframe.")
    
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
    if (perf_end_date_col):
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

@st.cache_data(ttl=3600)
def get_unique_naics_codes(_engine):
    """
    Get all unique NAICS codes from the database filter_values_naics_code table.
    
    Args:
        _engine: SQLAlchemy engine (with leading underscore to prevent hashing issues)
        
    Returns:
        List of unique NAICS codes
    """
    try:
        # Get NAICS codes from the filter_values_naics_code table
        from sqlalchemy import text
        with _engine.connect() as conn:
            # Use the correct table and column name based on the database structure
            try:
                # Based on the screenshot, the column is named "value"
                query = "SELECT value FROM public.filter_values_naics_code ORDER BY value"
                result = conn.execute(text(query)).fetchall()
                if result:
                    # Add "All" as the first option
                    return ["All"] + [r[0] for r in result]
            except Exception as e:
                st.sidebar.warning(f"Error getting NAICS codes from filter_values_naics_code: {e}")
                # Try alternative column name
                try:
                    query = "SELECT code FROM public.filter_values_naics_code ORDER BY code"
                    result = conn.execute(text(query)).fetchall()
                    if result:
                        return ["All"] + [r[0] for r in result]
                except Exception as e2:
                    st.sidebar.warning(f"Error with alternative column name: {e2}")
                    pass
                
            # If no filter table exists or errors occurred, try getting unique values from main data tables
            table_names = ["usaprime_cleaned", "usaspending_cleaned", "usaprime", "usaspending", 
                          "fetched_current_usaspending", "contracts"]
            
            for table in table_names:
                try:
                    query = f"SELECT DISTINCT naics_code FROM {table} WHERE naics_code IS NOT NULL ORDER BY naics_code"
                    result = conn.execute(text(query)).fetchall()
                    if result:
                        return ["All"] + [r[0] for r in result]
                except Exception:
                    continue
                    
        # Default if no data found
        return ["561210", "All"]
    except Exception as e:
        st.sidebar.error(f"Error getting NAICS codes: {str(e)}")
        return ["561210", "All"]

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
            engine = get_db_engine()
            
            # Get all unique NAICS codes from the database
            naics_options = get_unique_naics_codes(engine)
            
            # Agency filter if database connection works
            agency_options = ["All"] + get_unique_values(engine, "parent_award_agency_name")
        except Exception as e:
            st.error(f"Error loading filter values: {str(e)}")
            naics_options = ["561210", "All"]
            agency_options = ["All"]
        
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
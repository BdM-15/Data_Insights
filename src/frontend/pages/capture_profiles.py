"""
Capture Profiles page for the Data_Insights application.

This page allows users to search and filter contracts, select specific contracts,
and generate detailed capture profiles for business development and capture management.
"""

import streamlit as st
import pandas as pd
import streamlit as st
import pandas as pd
import numpy as np
import json
from datetime import datetime, date, timedelta
import os
import sys
import traceback
import logging
from sqlalchemy import text

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

@st.cache_data(ttl=3600)  # Cache for 1 hour
def get_unique_values(column_name, filter_conditions=None):
    """Get unique values for a filter column, with support for hierarchical dependencies."""
    try:
        engine = get_db_engine()
        
        if not filter_conditions:
            # Try to get values from the dedicated filter table first
            table_name = f"s3_processed.filter_values_{column_name}"
            try:
                query = f"SELECT value FROM {table_name} ORDER BY record_count DESC"
                params = {}
                
                with engine.connect() as connection:
                    df = pd.read_sql(text(query), connection, params=params)
                    if not df.empty:
                        unique_values = df['value'].drop_duplicates().tolist()
                        return unique_values
                        
            except Exception as filter_table_error:
                # If filter table doesn't exist, fall back to main table
                logger.info(f"Filter table {table_name} not found, using main table fallback for {column_name}")
                pass  # Continue to fallback logic below
                  # Fallback to main table with full data (no limits per user requirements)
            query = f"""
                SELECT DISTINCT {column_name} as value
                FROM s3_processed.usaspending_prime_awards
                WHERE {column_name} IS NOT NULL 
                AND {column_name} != ''
                ORDER BY value
            """
            params = {}
                
        else:
            # Use filter_dependencies table for dependent filters
            parent_value = filter_conditions[0]["value"]
            child_column = filter_conditions[0]["child_column"]
            
            # Map child_column to relationship_type for our database structure
            relationship_mapping = {
                'funding_sub_agency_name': 'parent_agency_to_sub_agency',
                'funding_office_name': 'sub_agency_to_funding_office'
            }
            
            relationship_type = relationship_mapping.get(child_column)
            if not relationship_type:
                return []
                
            query = """
                SELECT child_value as value
                FROM s3_processed.filter_dependencies 
                WHERE parent_value = :parent_value AND relationship_type = :relationship_type
                ORDER BY record_count DESC
            """
            params = {
                "parent_value": parent_value, 
                "relationship_type": relationship_type
            }
        
        with engine.connect() as connection:
            df = pd.read_sql(text(query), connection, params=params)
            
        if not df.empty:
            unique_values = df['value'].drop_duplicates().tolist()
        else:
            unique_values = []
            
        return unique_values
        
    except Exception as e:
        logger.error(f"Error fetching unique values for {column_name}: {str(e)}")
        # Return empty list instead of showing error to user for better UX
        return []

@st.cache_data(ttl=3600)  # Cache for 1 hour  
def get_naics_options():
    """Get NAICS codes for display (codes only for performance)."""
    try:
        engine = get_db_engine()
        
        # Get NAICS codes from filter table without descriptions for better performance
        naics_query = text("""
            SELECT value
            FROM s3_processed.filter_values_naics_code
            ORDER BY record_count DESC
        """)
        
        with engine.connect() as conn:
            naics_df = pd.read_sql_query(naics_query, conn)
            
            if naics_df.empty:
                return ["All"]
            
            # Return just the codes for better performance
            naics_options = ["All"] + naics_df['value'].astype(str).tolist()
            
            return naics_options
            
    except Exception as e:
        logger.error(f"Error loading NAICS options: {str(e)}")
        return ["All"]

def build_where_clause(filters):
    """Build SQL WHERE clause from filter selections."""
    conditions = []
    if filters.get('start_date'):
        conditions.append(f"period_of_performance_start_date >= '{filters['start_date']}'")
    if filters.get('end_date'):
        # Handle IDV contracts (identified by CONT_IDV in first 8 characters of contract_award_unique_key)
        # For IDV contracts, check if they START before the end filter date (they may extend beyond)
        # For regular contracts, check if they END before the end filter date
        end_date_condition = f"""(
            (LEFT(contract_award_unique_key, 8) != 'CONT_IDV' AND period_of_performance_current_end_date <= '{filters['end_date']}')
            OR 
            (LEFT(contract_award_unique_key, 8) = 'CONT_IDV' AND period_of_performance_start_date <= '{filters['end_date']}')
        )"""
        conditions.append(end_date_condition)
    
    if filters.get('awarding_agency'):
        # Escape single quotes in agency names
        agency_name = filters['awarding_agency'].replace("'", "''")
        conditions.append(f"parent_award_agency_name = '{agency_name}'")
    
    if filters.get('funding_agency'):
        agency_name = filters['funding_agency'].replace("'", "''")
        conditions.append(f"funding_agency_name = '{agency_name}'")
    
    if filters.get('funding_sub_agency'):
        agency_name = filters['funding_sub_agency'].replace("'", "''")
        conditions.append(f"funding_sub_agency_name = '{agency_name}'")
    
    if filters.get('funding_office'):
        office_name = filters['funding_office'].replace("'", "''")
        conditions.append(f"funding_office_name = '{office_name}'")
    
    if filters.get('naics_code'):
        conditions.append(f"naics_code = '{filters['naics_code']}'")
    
    if filters.get('recipient'):
        recipient_name = filters['recipient'].replace("'", "''")
        conditions.append(f"recipient_name = '{recipient_name}'")
    
    if filters.get('recipient_parent'):
        parent_name = filters['recipient_parent'].replace("'", "''")
        conditions.append(f"recipient_parent_name = '{parent_name}'")
    
    if filters.get('recipient_uei'):
        conditions.append(f"recipient_uei ILIKE '%{filters['recipient_uei']}%'")
    
    if filters.get('recipient_parent_uei'):
        conditions.append(f"recipient_parent_uei ILIKE '%{filters['recipient_parent_uei']}%'")
    
    if filters.get('contract_id'):
        contract_id = filters['contract_id'].replace("'", "''")
        conditions.append(f"award_id_piid = '{contract_id}'")
        # Debug: Log the exact contract ID being searched
        logger.info(f"Searching for exact contract ID: '{contract_id}'")
    
    if filters.get('parent_contract_id'):
        parent_id = filters['parent_contract_id'].replace("'", "''")
        conditions.append(f"parent_award_id_piid = '{parent_id}'")
        # Debug: Log the exact parent contract ID being searched
        logger.info(f"Searching for exact parent contract ID: '{parent_id}'")
    
    if filters.get('min_obligated') and filters['min_obligated'] > 0:
        conditions.append(f"total_dollars_obligated >= {filters['min_obligated']}")
    
    if filters.get('max_obligated') and filters['max_obligated'] > 0:
        conditions.append(f"total_dollars_obligated <= {filters['max_obligated']}")
    
    if filters.get('min_potential') and filters['min_potential'] > 0:
        conditions.append(f"potential_total_value_of_award >= {filters['min_potential']}")
    
    if filters.get('max_potential') and filters['max_potential'] > 0:
        conditions.append(f"potential_total_value_of_award <= {filters['max_potential']}")
    
    where_clause = " AND ".join(conditions) if conditions else "1=1"
    logger.info(f"Individual conditions: {conditions}")
    return where_clause

@st.cache_data(ttl=300)  # Cache for 5 minutes  
def search_contracts(filters):
    """Search contracts based on filter criteria."""
    try:
        engine = get_db_engine()
        where_clause = build_where_clause(filters)        # Debug information - log the search criteria
        logger.info(f"Search filters: {filters}")
        logger.info(f"Generated WHERE clause: {where_clause}")
        
        query = text(f"""
            SELECT 
                contract_award_unique_key,
                contract_transaction_unique_key,
                award_id_piid as contract_id,
                parent_award_id_piid as parent_contract_id,
                modification_number,
                action_date,
                recipient_name as awardee,
                recipient_parent_name as awardee_parent,
                parent_award_agency_name as awarding_agency,
                funding_agency_name as funding_agency,
                federal_action_obligation,
                total_dollars_obligated as total_obligated,
                potential_total_value_of_award as potential_value,
                period_of_performance_start_date as start_date,
                COALESCE(
                    period_of_performance_current_end_date,
                    ordering_period_end_date,
                    period_of_performance_potential_end_date
                ) as end_date,
                naics_code,
                recipient_uei,
                recipient_parent_uei,
                idv_type,
                type_of_idc
            FROM s3_processed.usaspending_prime_awards
            WHERE {where_clause}
            ORDER BY award_id_piid, action_date DESC
            LIMIT 500
        """)
        
        logger.info(f"Final SQL query: {str(query)}")
        
        with engine.connect() as conn:
            df = pd.read_sql_query(query, conn)
            
        logger.info(f"Query returned {len(df)} results")
        
        # If no results and we have a contract_id filter, try a direct test query
        if df.empty and filters.get('contract_id'):
            test_query = text("""
                SELECT COUNT(*) as count, 
                       MIN(award_id_piid) as sample_award_id,
                       MIN(period_of_performance_start_date) as min_start_date,
                       MAX(period_of_performance_start_date) as max_start_date
                FROM s3_processed.usaspending_prime_awards 
                WHERE award_id_piid = :contract_id
            """)
            
            with engine.connect() as conn:
                test_df = pd.read_sql_query(test_query, conn, params={'contract_id': filters['contract_id']})
                logger.info(f"Direct contract search for '{filters['contract_id']}': {test_df.to_dict('records')}")
                st.info(f"🔍 Debug: Found {test_df.iloc[0]['count']} records for contract ID '{filters['contract_id']}' in database")
                if test_df.iloc[0]['count'] > 0:
                    st.info(f"📅 Date range for this contract: {test_df.iloc[0]['min_start_date']} to {test_df.iloc[0]['max_start_date']}")
        
        # Format the dataframe for display
        if not df.empty:
            df['total_obligated_formatted'] = df['total_obligated'].apply(lambda x: f"${x:,.0f}" if pd.notnull(x) else "N/A")
            df['potential_value_formatted'] = df['potential_value'].apply(lambda x: f"${x:,.0f}" if pd.notnull(x) else "N/A")
            df['start_date'] = pd.to_datetime(df['start_date'], errors='coerce').dt.strftime('%Y-%m-%d')
            df['end_date'] = pd.to_datetime(df['end_date'], errors='coerce').dt.strftime('%Y-%m-%d')
            
        return df
        
    except Exception as e:
        logger.error(f"Error searching contracts: {str(e)}")
        st.error(f"Error searching contracts: {str(e)}")
        return pd.DataFrame()

def search_contracts_debug(filters):
    """Debug version of search_contracts without caching."""
    try:
        engine = get_db_engine()
        where_clause = build_where_clause(filters)
        query = text(f"""
            SELECT 
                contract_award_unique_key,
                contract_transaction_unique_key,
                award_id_piid as contract_id,
                parent_award_id_piid as parent_contract_id,
                modification_number,
                action_date,
                recipient_name as awardee,
                recipient_parent_name as awardee_parent,
                parent_award_agency_name as awarding_agency,
                funding_agency_name as funding_agency,
                federal_action_obligation,
                total_dollars_obligated as total_obligated,
                potential_total_value_of_award as potential_value,
                period_of_performance_start_date as start_date,
                COALESCE(
                    period_of_performance_current_end_date,
                    ordering_period_end_date,
                    period_of_performance_potential_end_date
                ) as end_date,
                naics_code,
                recipient_uei,
                recipient_parent_uei,
                idv_type,
                type_of_idc
            FROM s3_processed.usaspending_prime_awards
            WHERE {where_clause}
            ORDER BY award_id_piid, action_date DESC
            LIMIT 500
        """)
        
        with engine.connect() as conn:
            df = pd.read_sql_query(query, conn)
            
        # Format the dataframe for display
        if not df.empty:
            df['total_obligated_formatted'] = df['total_obligated'].apply(lambda x: f"${x:,.0f}" if pd.notnull(x) else "N/A")
            df['potential_value_formatted'] = df['potential_value'].apply(lambda x: f"${x:,.0f}" if pd.notnull(x) else "N/A")
            df['start_date'] = pd.to_datetime(df['start_date'], errors='coerce').dt.strftime('%Y-%m-%d')
            df['end_date'] = pd.to_datetime(df['end_date'], errors='coerce').dt.strftime('%Y-%m-%d')
            
        return df
        
    except Exception as e:
        logger.error(f"Error in debug search: {str(e)}")
        st.error(f"Error in debug search: {str(e)}")
        return pd.DataFrame()

def get_contract_details(contract_unique_key):
    """Get detailed information for a specific contract."""
    try:
        engine = get_db_engine()
        
        # Get prime award details
        prime_query = text("""
            SELECT *
            FROM s3_processed.usaspending_prime_awards
            WHERE contract_award_unique_key = :contract_key
            ORDER BY action_date DESC
        """)
        
        # Get subawards if available
        subawards_query = text("""
            SELECT *
            FROM s3_processed.usaspending_subawards
            WHERE prime_award_unique_key = :contract_key
            ORDER BY subaward_action_date DESC
        """)
        
        with engine.connect() as conn:
            prime_df = pd.read_sql_query(prime_query, conn, params={'contract_key': contract_unique_key})
            subawards_df = pd.read_sql_query(subawards_query, conn, params={'contract_key': contract_unique_key})
            
        return prime_df, subawards_df
        
    except Exception as e:
        logger.error(f"Error getting contract details: {str(e)}")
        return pd.DataFrame(), pd.DataFrame()

def main():
    """Main function to render the Capture Profiles page."""
    
    # Apply theme CSS
    st.markdown(generate_theme_css(THEME), unsafe_allow_html=True)    # Initialize session state for selected contracts
    if 'selected_contracts' not in st.session_state:
        st.session_state.selected_contracts = []
    
    # Set default dates (same as strategic dashboard)
    today = datetime.now().date()
    default_start = today - timedelta(days=365 * 6)  # 6 years back like strategic dashboard    # Initialize all filter session state keys to prevent errors on clear filters
    filter_defaults = {
        'capture_awarding_agency': "All",  # String value, not index
        'capture_funding_sub_agency': "All",  # String value, not index
        'capture_funding_office': "All",  # String value, not index
        'capture_naics': "All",  # String value, not index
        'capture_contract_id': "",
        'capture_parent_contract_id': "",
        'capture_recipient': "All",  # String value, not index
        'capture_recipient_uei': "",
        'capture_recipient_parent': "All",  # String value, not index
        'capture_recipient_parent_uei': "",
        'contracts_selection': None
    }
    
    for key, default_value in filter_defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default_value
    
    # Add filters to the existing sidebar (created by main app)
    with st.sidebar:
        st.markdown("## Filters")
          # Date range filters
        st.markdown("**Performance Period**")
        col1, col2 = st.columns(2)
        
        with col1:
            start_date = st.date_input(
                "Start Date",
                value=default_start,
                help="Filter by performance period start date"
            )
            
        with col2:
            end_date = st.date_input(
                "End Date", 
                value=today,
                help="Filter by performance period end date"
            )
        
        # Agency filters with hierarchical dependency
        st.markdown("**Agencies**")
          # Get awarding agencies
        awarding_agencies = ["All"] + get_unique_values('parent_award_agency_name')
        
        # Calculate correct index for session state value
        awarding_agency_value = st.session_state.get('capture_awarding_agency', "All")
        try:
            awarding_agency_index = awarding_agencies.index(awarding_agency_value)
        except ValueError:            awarding_agency_index = 0  # Default to "All" if value not found
            
        selected_awarding_agency = st.selectbox(
            "Awarding Agency",
            awarding_agencies,
            index=awarding_agency_index,
            placeholder="Select an awarding agency...",
            help="Filter by awarding agency",
            key="capture_awarding_agency"
        )
        
        # Get funding sub-agencies (filtered by awarding agency)
        funding_sub_agencies = ["All"]
        if selected_awarding_agency == "All":
            # When "All" is selected, show all available funding sub-agencies
            funding_sub_agencies.extend(get_unique_values('funding_sub_agency_name'))
        elif selected_awarding_agency is not None:
            # When a specific agency is selected, show only its sub-agencies
            sub_agencies = get_unique_values('funding_sub_agency_name', 
                            filter_conditions=[{
                                "child_column": "funding_sub_agency_name", 
                                "value": selected_awarding_agency
                            }])
            funding_sub_agencies.extend(sub_agencies)
            
            # Only show warning if a specific agency was selected but has no sub-agencies
            if len(sub_agencies) == 0:
                st.warning(f"No funding sub-agencies found for {selected_awarding_agency}")
        
        # Calculate correct index for funding sub-agency
        funding_sub_agency_value = st.session_state.get('capture_funding_sub_agency', "All")
        try:
            funding_sub_agency_index = funding_sub_agencies.index(funding_sub_agency_value)
        except ValueError:
            funding_sub_agency_index = 0  # Default to "All" if value not found
            
        selected_funding_sub_agency = st.selectbox(
            "Funding Sub-Agency",
            funding_sub_agencies,
            index=funding_sub_agency_index,
            placeholder="Select a funding sub-agency...",
            help="Filter by funding sub-agency (depends on awarding agency)",
            key="capture_funding_sub_agency"        )
        
        # Get funding offices (filtered by funding sub-agency)
        funding_offices = ["All"]
        if selected_funding_sub_agency == "All":
            # When "All" is selected, show all available funding offices
            funding_offices.extend(get_unique_values('funding_office_name'))
        elif selected_funding_sub_agency is not None:
            # When a specific sub-agency is selected, show only its funding offices
            offices = get_unique_values('funding_office_name',
                            filter_conditions=[{
                                "child_column": "funding_office_name",
                                "value": selected_funding_sub_agency
                            }])
            funding_offices.extend(offices)
            
            # Only show warning if a specific sub-agency was selected but has no offices
            if len(offices) == 0:
                st.warning(f"No funding offices found for {selected_funding_sub_agency}")
        # Calculate correct index for funding office
        funding_office_value = st.session_state.get('capture_funding_office', "All")
        try:
            funding_office_index = funding_offices.index(funding_office_value)
        except ValueError:
            funding_office_index = 0  # Default to "All" if value not found
            
        selected_funding_office = st.selectbox(
            "Funding Office",
            funding_offices,
            index=funding_office_index,
            placeholder="Select a funding office...",
            help="Filter by funding office (depends on funding sub-agency)",
            key="capture_funding_office"        )
        
        # Funding agency (separate from hierarchical chain)
        # REMOVED - funding_agencies filter to simplify interface        
        
        # NAICS filter
        st.markdown("**Industry Classification**")
        naics_options = get_naics_options()
        
        # Calculate correct index for NAICS
        naics_value = st.session_state.get('capture_naics', "All")
        try:
            naics_index = naics_options.index(naics_value)
        except ValueError:
            naics_index = 0  # Default to "All" if value not found
            
        naics_selection = st.selectbox(
            "NAICS Code",
            naics_options,
            index=naics_index,
            placeholder="Select a NAICS code...",
            help="Filter by NAICS industry code",
            key="capture_naics"
        )
        
        # Extract actual NAICS code value
        naics_code = naics_selection if naics_selection != "All" else "All"
          # Contract identification filters - User input driven
        st.markdown("**Contract Identification**")
        selected_contract_id = st.text_input(
            "Contract/Order ID",
            placeholder="Enter contract/order ID...",
            help="Enter specific contract/order ID (award_id_piid)",
            key="capture_contract_id"
        )
        
        selected_parent_contract_id = st.text_input(
            "Parent Contract ID",
            placeholder="Enter parent contract ID...",
            help="Enter specific parent contract ID (parent_award_id_piid)",
            key="capture_parent_contract_id"
        )
        
        # Recipient filters
        st.markdown("**Awardee Information**")
        recipients = ["All"] + get_unique_values('recipient_name')
        
        # Calculate correct index for recipient
        recipient_value = st.session_state.get('capture_recipient', "All")
        try:
            recipient_index = recipients.index(recipient_value)
        except ValueError:
            recipient_index = 0  # Default to "All" if value not found
            
        selected_recipient = st.selectbox(
            "Awardee",
            recipients,
            index=recipient_index,
            placeholder="Select an awardee...",
            help="Filter by awardee company",
            key="capture_recipient"
        )
        
        # Awardee UEI right after Awardee filter
        recipient_uei = st.text_input(
            "Awardee UEI",
            placeholder="Enter UEI...",
            help="Search by awardee UEI",
            key="capture_recipient_uei"
        )
        
        recipient_parents = ["All"] + get_unique_values('recipient_parent_name')
        
        # Calculate correct index for recipient parent
        recipient_parent_value = st.session_state.get('capture_recipient_parent', "All")
        try:
            recipient_parent_index = recipient_parents.index(recipient_parent_value)
        except ValueError:
            recipient_parent_index = 0  # Default to "All" if value not found
            
        selected_recipient_parent = st.selectbox(
            "Awardee Parent Name",
            recipient_parents,
            index=recipient_parent_index,
            placeholder="Select an awardee parent...",
            help="Filter by awardee parent company",
            key="capture_recipient_parent"
        )
        
        # Awardee Parent UEI right after Awardee Parent filter
        recipient_parent_uei = st.text_input(
            "Awardee Parent UEI",
            placeholder="Enter parent UEI...",
            help="Search by awardee parent UEI",
            key="capture_recipient_parent_uei"
        )
        
        # Value range filters
        st.markdown("**Contract Values**")
        col1, col2 = st.columns(2)        
        with col1:
            min_obligated = st.number_input(
                "Min Total Obligated",
                min_value=0,
                value=0,
                step=1000,
                help="Minimum total obligated amount"
            )
            
            min_potential = st.number_input(
                "Min Potential Value",
                min_value=0,
                value=0,
                step=1000,
                help="Minimum potential value"
            )
        
        with col2:
            max_obligated = st.number_input(
                "Max Total Obligated",
                min_value=0,
                value=0,
                step=1000,
                help="Maximum total obligated amount (0 = no limit)"
            )
            
            max_potential = st.number_input(
                "Max Potential Value",
                min_value=0,
                value=0,
                step=1000,
                help="Maximum potential value (0 = no limit)"
            )        # Filter buttons in columns with icons
        col1, col2 = st.columns(2)
        
        with col1:
            apply_filters = st.button("🔍 Apply Filters", use_container_width=True)
        
        with col2:
            clear_filters = st.button("🗑️ Clear Filters", use_container_width=True)        # Debug button for troubleshooting
        if st.button("🐛 Debug Search Query", use_container_width=True):
            filters = {
                'start_date': start_date,
                'end_date': end_date,
                'awarding_agency': selected_awarding_agency if selected_awarding_agency != "All" else None,
                'funding_sub_agency': selected_funding_sub_agency if selected_funding_sub_agency != "All" else None,
                'funding_office': selected_funding_office if selected_funding_office != "All" else None,
                'naics_code': naics_code if naics_code != "All" else None,
                'recipient': selected_recipient if selected_recipient != "All" else None,
                'recipient_parent': selected_recipient_parent if selected_recipient_parent != "All" else None,
                'recipient_uei': recipient_uei.strip() if recipient_uei else None,
                'recipient_parent_uei': recipient_parent_uei.strip() if recipient_parent_uei else None,
                'contract_id': selected_contract_id.strip() if selected_contract_id else None,
                'parent_contract_id': selected_parent_contract_id.strip() if selected_parent_contract_id else None,
                'min_obligated': min_obligated if min_obligated > 0 else None,
                'max_obligated': max_obligated if max_obligated > 0 else None,
                'min_potential': min_potential if min_potential > 0 else None,
                'max_potential': max_potential if max_potential > 0 else None
            }
            where_clause = build_where_clause(filters)
            
            st.write("**Debug Information:**")
            st.write(f"**Filters:** {filters}")
            st.write(f"**Generated WHERE clause:** {where_clause}")
            st.write(f"**Date range:** {start_date} to {end_date}")
            
            if filters.get('contract_id'):
                st.write(f"**Contract ID being searched:** '{filters['contract_id']}'")
            if filters.get('parent_contract_id'):
                st.write(f"**Parent Contract ID being searched:** '{filters['parent_contract_id']}'")
            
            # Run an uncached search to see actual results
            st.write("**Running debug search (uncached)...**")
            debug_results = search_contracts_debug(filters)
            st.write(f"**Debug search found:** {len(debug_results)} records")
            if not debug_results.empty:
                st.dataframe(debug_results.head())
        # Clear filters functionality
        if clear_filters:
            # Clear results and selections first
            if 'search_results' in st.session_state:
                del st.session_state.search_results
            if 'selected_contracts' in st.session_state:
                st.session_state.selected_contracts = []
            if 'contracts_selection' in st.session_state:
                del st.session_state.contracts_selection
            
            # Reset filter session state values by deleting them (they'll be recreated with defaults)
            filter_keys_to_reset = [
                'capture_awarding_agency', 'capture_funding_sub_agency', 'capture_funding_office',
                'capture_naics', 'capture_contract_id', 'capture_parent_contract_id',
                'capture_recipient', 'capture_recipient_uei', 'capture_recipient_parent',
                'capture_recipient_parent_uei'
            ]
            
            for key in filter_keys_to_reset:
                if key in st.session_state:
                    del st.session_state[key]
            
            st.rerun()
    
    # Main page content
    st.title("📑 Capture Profiles")
    st.markdown("""
    Search and filter contracts to generate detailed capture profiles for business development and capture management.
    """)
    
    # Create filter dictionary
    filters = {
        'start_date': start_date,
        'end_date': end_date,
        'awarding_agency': selected_awarding_agency if selected_awarding_agency != "All" else None,
        'funding_sub_agency': selected_funding_sub_agency if selected_funding_sub_agency != "All" else None,
        'funding_office': selected_funding_office if selected_funding_office != "All" else None,
        'naics_code': naics_code if naics_code != "All" else None,
        'recipient': selected_recipient if selected_recipient != "All" else None,
        'recipient_parent': selected_recipient_parent if selected_recipient_parent != "All" else None,
        'recipient_uei': recipient_uei.strip() if recipient_uei else None,
        'recipient_parent_uei': recipient_parent_uei.strip() if recipient_parent_uei else None,
        'contract_id': selected_contract_id.strip() if selected_contract_id else None,
        'parent_contract_id': selected_parent_contract_id.strip() if selected_parent_contract_id else None,
        'min_obligated': min_obligated if min_obligated > 0 else None,
        'max_obligated': max_obligated if max_obligated > 0 else None,
        'min_potential': min_potential if min_potential > 0 else None,
        'max_potential': max_potential if max_potential > 0 else None
    }
    
    # Only search contracts when Apply Filters is clicked (no preloading)
    if apply_filters:
        with st.spinner("Searching contracts..."):
            st.session_state.search_results = search_contracts(filters)
    
    # Display search results
    if 'search_results' in st.session_state and not st.session_state.search_results.empty:
        df = st.session_state.search_results
        
        # Contract selection section
        st.subheader("📋 Contract Selection")
        st.info(f"Found {len(df)} contracts. Select up to 5 contracts for capture profile generation.")
          # Create display dataframe with proper column names - include modification info, exclude NAICS description
        display_df = df[[
            'contract_id', 'modification_number', 'action_date', 'awardee', 'awardee_parent', 
            'awarding_agency', 'funding_agency', 'federal_action_obligation', 'total_obligated_formatted', 
            'potential_value_formatted', 'start_date', 'end_date', 'naics_code'
        ]].copy()
        
        # Format federal_action_obligation for display
        display_df['federal_action_obligation_formatted'] = display_df['federal_action_obligation'].apply(
            lambda x: f"${x:,.0f}" if pd.notnull(x) and x != 0 else "N/A"
        )
        
        # Select final columns for display
        display_df = display_df[[
            'contract_id', 'modification_number', 'action_date', 'awardee', 'awardee_parent', 
            'awarding_agency', 'funding_agency', 'federal_action_obligation_formatted', 'total_obligated_formatted', 
            'potential_value_formatted', 'start_date', 'end_date', 'naics_code'
        ]].copy()
        
        display_df.columns = [
            'Contract ID', 'Mod #', 'Action Date', 'Awardee', 'Awardee Parent',
            'Awarding Agency', 'Funding Agency', 'Action Obligation', 'Total Obligated', 
            'Potential Value', 'Start Date', 'End Date', 'NAICS Code'
        ]
        
        # Use Streamlit's built-in selectable dataframe with proper multi-row selection
        event = st.dataframe(
            display_df, 
            use_container_width=True, 
            hide_index=True,
            on_select="rerun",
            selection_mode=["multi-row"],
            key="contracts_selection"
        )
        
        # Handle selection events
        if event and event.selection and 'rows' in event.selection:
            selected_indices = event.selection['rows']
            
            # Get the unique keys for selected rows
            selected_keys = []
            for idx in selected_indices:
                if idx < len(df):
                    selected_keys.append(df.iloc[idx]['contract_award_unique_key'])
            
            # Limit to maximum 5 selections
            if len(selected_keys) > 5:
                st.warning("⚠️ Maximum 5 contracts can be selected. Only the first 5 will be used.")
                selected_keys = selected_keys[:5]
            
            # Update session state
            st.session_state.selected_contracts = selected_keys
        
        # Display selection summary and generation button
        if st.session_state.selected_contracts:
            st.success(f"✅ Selected {len(st.session_state.selected_contracts)} contract(s) for capture profile generation.")
            
            # Show selected contract IDs for confirmation
            with st.expander("View Selected Contracts", expanded=False):
                for i, contract_key in enumerate(st.session_state.selected_contracts, 1):
                    # Find the corresponding row to show readable info
                    matching_row = df[df['contract_award_unique_key'] == contract_key]
                    if not matching_row.empty:
                        contract_info = matching_row.iloc[0]
                        st.write(f"{i}. **{contract_info['contract_id']}** - {contract_info['awardee']} ({contract_info['total_obligated_formatted']})")
            
            # Generate capture profiles button
            if st.button("📊 Generate Capture Profiles", type="primary", use_container_width=True):
                generate_capture_profiles(st.session_state.selected_contracts)
        else:
            st.info("💡 Select contracts from the table above to generate capture profiles. You can select up to 5 contracts.")
    
    elif apply_filters and ('search_results' not in st.session_state or st.session_state.search_results.empty):
        st.info("No contracts found. Please adjust your filters and try again.")
    elif not apply_filters and 'search_results' not in st.session_state:
        st.info("Use the filters in the sidebar and click 'Apply Filters' to search for contracts.")

def generate_capture_profiles(selected_contracts):
    """Generate detailed capture profiles for selected contracts."""
    st.subheader("📊 Capture Profiles")
    
    for i, contract_key in enumerate(selected_contracts, 1):
        with st.expander(f"Contract {i}: {contract_key}", expanded=True):
            try:
                prime_df, subawards_df = get_contract_details(contract_key)
                
                if prime_df.empty:
                    st.error("No data found for this contract.")
                    continue
                
                # Get the most recent record for basic info
                latest_record = prime_df.iloc[0]
                
                # Award Details Section
                with st.container():
                    st.markdown("### 🏆 Award Details")
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric("Contract Value", f"${latest_record.get('federal_action_obligation', 0):,.0f}")
                        st.write(f"**Contract ID:** {latest_record.get('award_id_piid', 'N/A')}")
                        st.write(f"**Awardee:** {latest_record.get('recipient_name', 'N/A')}")
                    
                    with col2:
                        st.write(f"**Start Date:** {latest_record.get('period_of_performance_start_date', 'N/A')}")
                        st.write(f"**End Date:** {latest_record.get('period_of_performance_current_end_date', 'N/A')}")
                        st.write(f"**Action Date:** {latest_record.get('action_date', 'N/A')}")
                    
                    with col3:
                        st.write(f"**Location:** {latest_record.get('primary_place_of_performance_city_name', 'N/A')}, {latest_record.get('primary_place_of_performance_state_code', 'N/A')}")
                        st.write(f"**Total Obligated:** ${latest_record.get('total_dollars_obligated', 0):,.0f}")
                
                # Requirements Details Section  
                with st.container():
                    st.markdown("### 📋 Requirements Details")
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**NAICS Code:** {latest_record.get('naics_code', 'N/A')}")
                        st.write(f"**NAICS Description:** {latest_record.get('naics_description', 'N/A')}")
                        st.write(f"**PSC Code:** {latest_record.get('product_or_service_code', 'N/A')}")
                    
                    with col2:
                        st.write(f"**PSC Description:** {latest_record.get('product_or_service_code_description', 'N/A')}")
                        st.write(f"**Program:** {latest_record.get('dod_acquisition_program_description', 'N/A')}")
                
                # Competitor Details Section
                with st.container():
                    st.markdown("### 🏢 Competitor Details")
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**Prime Contractor:** {latest_record.get('recipient_name', 'N/A')}")
                        st.write(f"**Parent Company:** {latest_record.get('recipient_parent_name', 'N/A')}")
                        st.write(f"**UEI:** {latest_record.get('recipient_uei', 'N/A')}")
                    
                    with col2:
                        st.write(f"**Parent UEI:** {latest_record.get('recipient_parent_uei', 'N/A')}")
                        st.write(f"**Offers Received:** {latest_record.get('number_of_offers_received', 'N/A')}")
                
                # Subawards Details Section
                with st.container():
                    st.markdown("### 🤝 Subawards Details")
                    if not subawards_df.empty:
                        st.write(f"**Total Subawards:** {len(subawards_df)}")
                        
                        # Show top subawards by value
                        top_subawards = subawards_df.nlargest(5, 'subaward_amount')[
                            ['subawardee_name', 'subaward_amount', 'subaward_action_date', 'subaward_description']
                        ]
                        top_subawards.columns = ['Subcontractor', 'Amount', 'Date', 'Description']
                        top_subawards['Amount'] = top_subawards['Amount'].apply(lambda x: f"${x:,.0f}" if pd.notnull(x) else "N/A")
                        
                        st.dataframe(top_subawards, use_container_width=True)
                    else:
                        st.info("No subaward data available for this contract.")
                
                # Customer Details Section
                with st.container():
                    st.markdown("### 🏛️ Customer Details")
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**Awarding Agency:** {latest_record.get('parent_award_agency_name', 'N/A')}")
                        st.write(f"**Awarding Sub-Agency:** {latest_record.get('awarding_sub_agency_name', 'N/A')}")
                        st.write(f"**Awarding Office:** {latest_record.get('awarding_office_name', 'N/A')}")
                    
                    with col2:
                        st.write(f"**Funding Agency:** {latest_record.get('funding_agency_name', 'N/A')}")
                        st.write(f"**Funding Sub-Agency:** {latest_record.get('funding_sub_agency_name', 'N/A')}")
                        st.write(f"**Funding Office:** {latest_record.get('funding_office_name', 'N/A')}")
                
                # Solicitation Details Section
                with st.container():
                    st.markdown("### 📄 Solicitation Details")
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**Competition Type:** {latest_record.get('extent_competed', 'N/A')}")
                        st.write(f"**Set-Aside Type:** {latest_record.get('type_of_set_aside', 'N/A')}")
                        st.write(f"**Contract Type:** {latest_record.get('type_of_contract_pricing', 'N/A')}")
                    
                    with col2:
                        st.write(f"**Solicitation Date:** {latest_record.get('solicitation_date', 'N/A')}")
                        st.write(f"**Award Type:** {latest_record.get('award_type', 'N/A')}")
                        st.write(f"**Action Type:** {latest_record.get('action_type', 'N/A')}")
                
                # Transaction History
                if len(prime_df) > 1:
                    with st.container():
                        st.markdown("### 📈 Transaction History")
                        history_df = prime_df[['action_date', 'modification_number', 'federal_action_obligation', 'transaction_description']].copy()
                        history_df.columns = ['Date', 'Mod #', 'Obligation', 'Description']
                        history_df['Obligation'] = history_df['Obligation'].apply(lambda x: f"${x:,.0f}" if pd.notnull(x) else "N/A")
                        st.dataframe(history_df, use_container_width=True)
                
            except Exception as e:
                st.error(f"Error generating capture profile: {str(e)}")
                logger.error(f"Error in capture profile generation: {str(e)}")

def display_contract_details(contract_key):
    """Display detailed information for a specific contract in a modal-like expander."""
    with st.expander(f"Contract Details: {contract_key}", expanded=True):
        try:
            prime_df, subawards_df = get_contract_details(contract_key)
            
            if not prime_df.empty:
                st.dataframe(prime_df, use_container_width=True)
                
                if not subawards_df.empty:
                    st.subheader("Subawards")
                    st.dataframe(subawards_df, use_container_width=True)
            else:
                st.error("No data found for this contract.")
                
        except Exception as e:
            st.error(f"Error loading contract details: {str(e)}")

if __name__ == "__main__":
    main()

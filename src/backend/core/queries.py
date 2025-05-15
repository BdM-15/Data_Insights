"""
This module contains functions for querying the database to retrieve specific datasets.
"""
# import streamlit as st # Removed Streamlit import
import pandas as pd
from sqlalchemy import text
from src.backend.core.database import get_db_connection
from src.backend.data.models.data_models import NAICSData
from typing import List
import logging # Added for logging

logger = logging.getLogger(__name__) # Added logger

# Query functions with enhanced error reporting
# @st.cache_data(ttl=3600) # Removed Streamlit decorator
def get_naics_data(naics_code="561210", start_date=None, end_date=None) -> pd.DataFrame: # Updated return type to pd.DataFrame
    """
    Get data for specified NAICS code with date filtering.
    
    Args:
        naics_code: NAICS code to filter by (default: 561210)
        start_date: Start date for filtering
        end_date: End date for filtering
        
    Returns:
        DataFrame containing filtered data, or an empty DataFrame on failure/no data.
    """
    engine = get_db_connection()
    if not engine:
        logger.error("Database connection failed. Cannot retrieve data.")
        return pd.DataFrame() # Return empty DataFrame on failure
    
    table_names = ["usaprime_cleaned", "usaspending_cleaned", "usaprime", "usaspending", 
                  "fetched_current_usaspending", "contracts"]
    
    logger.info(f"Query Parameters: NAICS: {naics_code}, Date range: {start_date} to {end_date}")
    
    for table_name in table_names:
        try:
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
                    naics_description, 
                    type_of_idc,
                    multiple_or_single_award_idv,
                    type_of_contract_pricing,
                    extent_competed,
                    transaction_description,
                    contract_award_unique_key,                     -- Added for get_expiring_contracts
                    period_of_performance_current_end_date,      -- Added for get_expiring_contracts
                    potential_total_value_of_award               -- Added for get_expiring_contracts
                FROM {table_name}
                WHERE 1=1
            """
            params = {}
            
            if naics_code and naics_code != "All":
                query += " AND naics_code = :naics_code"
                params["naics_code"] = naics_code
            
            if start_date:
                query += " AND action_date >= :start_date"
                params["start_date"] = start_date
            
            if end_date:
                query += " AND action_date <= :end_date"
                params["end_date"] = end_date
                
            logger.info(f"Trying table: {table_name} with params: {params}")
            
            # Removed count query for brevity in backend function, can be added if performance monitoring is critical
            
            df = pd.read_sql(text(query), engine, params=params)
            
            if not df.empty:
                logger.info(f"Successfully fetched {len(df):,} rows from {table_name}")
                return df # Return the DataFrame directly
            else:
                logger.info(f"No data found in {table_name} for the given criteria.")
                
        except Exception as e:
            logger.error(f"Error querying {table_name}: {e}", exc_info=True)
            continue
            
    logger.warning("No data found in any of the specified tables for the given criteria.")
    return pd.DataFrame() # Return empty DataFrame if no data found

# @st.cache_data(ttl=3600) # Removed Streamlit decorator
def get_unique_naics_codes() -> List[NAICSData]:
    """
    Retrieves unique NAICS codes and their descriptions from the database.

    Returns:
        List of NAICSData objects containing unique NAICS codes and descriptions.
        Returns an empty list on failure or if no data is found.
    """
    engine = get_db_connection()
    if not engine:
        logger.error("Database connection failed. Cannot retrieve unique NAICS codes.")
        return []

    table_names = ["usaprime_cleaned", "usaspending_cleaned", "usaprime", "usaspending", 
                   "fetched_current_usaspending", "contracts"]

    for table_name in table_names:
        try:
            query = f"""
                SELECT naics_code, MAX(naics_description) as naics_description 
                FROM {table_name}
                WHERE naics_code IS NOT NULL AND naics_code != ''
                GROUP BY naics_code
                ORDER BY naics_code;
            """
            logger.info(f"Trying to get unique NAICS codes from table: {table_name}")
            df = pd.read_sql(text(query), engine)

            if not df.empty:
                logger.info(f"Successfully fetched {len(df)} unique NAICS codes from {table_name}")
                unique_naics_list = [
                    NAICSData(naics_code=row['naics_code'], naics_description=row['naics_description'])
                    for index, row in df.iterrows()
                ]
                return unique_naics_list
            else:
                logger.info(f"No unique NAICS codes found in {table_name}.")
        except Exception as e:
            logger.error(f"Error querying unique NAICS codes from {table_name}: {e}", exc_info=True)
            continue
    
    logger.warning("No unique NAICS codes found in any of the specified tables.")
    return []

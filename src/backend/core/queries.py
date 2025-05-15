"""
SQL queries and database functions for Data Insights.
Organized by domain for maintainability and reuse.
"""

import pandas as pd
from sqlalchemy import text

# ------------------------------------------------------------
# NAICS Data Query
# ------------------------------------------------------------
def get_naics_data(engine, naics_code="561210", start_date=None, end_date=None):
    """
    Get data for specified NAICS code with date filtering.

    Args:
        engine: SQLAlchemy engine
        naics_code: NAICS code to filter by (default: 561210)
        start_date: Start date for filtering (YYYY-MM-DD or None)
        end_date: End date for filtering (YYYY-MM-DD or None)

    Returns:
        DataFrame containing filtered data
    """
    # If no engine is provided, return empty DataFrame
    if not engine:
        return pd.DataFrame()

    # List of table names to search for NAICS data
    table_names = [
        "usaprime_cleaned",
        "usaspending_cleaned",
        "usaprime",
        "usaspending",
        "fetched_current_usaspending",
        "contracts"
    ]

    # Try each table in order until data is found
    for table_name in table_names:
        try:
            # Build SQL query string
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
            # Parameters for query
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

            # Read in chunks for large tables
            chunk_size = 100000
            df_list = []
            with engine.connect() as conn:
                for chunk in pd.read_sql(text(query), conn, params=params, chunksize=chunk_size):
                    df_list.append(chunk)
                # If any data was found, return as DataFrame
                if df_list:
                    if len(df_list) == 1:
                        df = df_list[0]
                    else:
                        df = pd.concat(df_list, ignore_index=True)
                    return df
        except Exception:
            # If error (e.g., table doesn't exist), try next table
            continue
    # If no data found in any table, return empty DataFrame
    return pd.DataFrame()

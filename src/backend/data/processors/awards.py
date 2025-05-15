"""
Award data processing functions for Data Insights.
Move all award-related data processing logic here for modularization.
"""

import pandas as pd
import numpy as np
from datetime import datetime

def get_award_summary(df: pd.DataFrame) -> dict:
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

def get_top_agencies(df: pd.DataFrame, metric: str = "count", n: int = 15) -> pd.DataFrame:
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

def get_quarterly_trends(df: pd.DataFrame) -> pd.DataFrame:
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
    df['fiscal_year'] = df['action_date'].dt.year
    df.loc[df['action_date'].dt.month >= 10, 'fiscal_year'] = df['action_date'].dt.year + 1
    # Map calendar quarters to fiscal quarters
    month_to_fiscal_quarter = {
        1: 2, 2: 2, 3: 2,  # Calendar Q1 = Fiscal Q2
        4: 3, 5: 3, 6: 3,  # Calendar Q2 = Fiscal Q3
        7: 4, 8: 4, 9: 4,  # Calendar Q3 = Fiscal Q4
        10: 1, 11: 1, 12: 1  # Calendar Q4 = Fiscal Q1
    }
    df['fiscal_quarter'] = df['action_date'].dt.month.map(month_to_fiscal_quarter)
    # Create fiscal period label
    df['fiscal_period'] = df['fiscal_year'].astype(str) + '-Q' + df['fiscal_quarter'].astype(str)
    # Filter base awards for award count
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

def get_naics_data(engine, naics_code="561210", start_date=None, end_date=None):
    """
    Retrieve award data for a specified NAICS code and date range from the 'usaprime_cleaned' table only.
    Args:
        engine: SQLAlchemy engine for database connection
        naics_code: NAICS code to filter by (default: 561210)
        start_date: Start date for filtering (YYYY-MM-DD)
        end_date: End date for filtering (YYYY-MM-DD)
    Returns:
        DataFrame containing filtered data
    Raises:
        ValueError: If no data is found in the table or connection fails
    """
    import pandas as pd
    from sqlalchemy import text
    table_name = "usaprime_cleaned"
    params = {}
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
                type_of_idc,
                multiple_or_single_award_idv,
                type_of_contract_pricing,
                extent_competed,
                transaction_description
            FROM {table_name}
            WHERE 1=1
        """
        if naics_code and naics_code != "All":
            query += " AND naics_code = :naics_code"
            params["naics_code"] = naics_code
        if start_date:
            query += " AND action_date >= :start_date"
            params["start_date"] = start_date
        if end_date:
            query += " AND action_date <= :end_date"
            params["end_date"] = end_date
        with engine.connect() as conn:
            df = pd.read_sql(text(query), conn, params=params)
            if not df.empty:
                return df
    except Exception as e:
        raise ValueError(f"Error querying table '{table_name}': {str(e)}")
    raise ValueError("No data found in 'usaprime_cleaned' for the given filters.")

def get_unique_naics_codes(engine, table_names=None):
    """
    Get all unique NAICS codes from the database filter_values_naics_code table or fallback tables.
    Args:
        engine: SQLAlchemy engine
        table_names: Optional list of table names to check
    Returns:
        List of unique NAICS codes
    """
    from sqlalchemy import text
    if table_names is None:
        table_names = [
            "usaprime_cleaned", "usaspending_cleaned", "usaprime", "usaspending",
            "fetched_current_usaspending", "contracts"
        ]
    try:
        with engine.connect() as conn:
            try:
                query = "SELECT value FROM public.filter_values_naics_code ORDER BY value"
                result = conn.execute(text(query)).fetchall()
                if result:
                    return ["All"] + [r[0] for r in result]
            except Exception:
                try:
                    query = "SELECT code FROM public.filter_values_naics_code ORDER BY code"
                    result = conn.execute(text(query)).fetchall()
                    if result:
                        return ["All"] + [r[0] for r in result]
                except Exception:
                    pass
            for table in table_names:
                try:
                    query = f"SELECT DISTINCT naics_code FROM {table} WHERE naics_code IS NOT NULL ORDER BY naics_code"
                    result = conn.execute(text(query)).fetchall()
                    if result:
                        return ["All"] + [r[0] for r in result]
                except Exception:
                    continue
        return ["561210", "All"]
    except Exception:
        return ["561210", "All"]

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
    base_awards = df[df['modification_number'] == '0']
    agency_counts = base_awards.groupby('parent_award_agency_name').size().reset_index(name='award_count')
    agency_obligations = df.groupby('parent_award_agency_name')['federal_action_obligation'].sum().reset_index()
    agency_ratio = pd.merge(agency_counts, agency_obligations, on='parent_award_agency_name', how='outer').fillna(0)
    agency_ratio['avg_award_value'] = agency_ratio['federal_action_obligation'] / agency_ratio['award_count']
    agency_ratio['avg_award_value'] = agency_ratio['avg_award_value'].fillna(0)
    agency_ratio['avg_award_value'] = agency_ratio['avg_award_value'].replace([np.inf, -np.inf], 0)
    agency_ratio['scatter_size'] = np.abs(agency_ratio['avg_award_value'])
    size_cap = agency_ratio['scatter_size'].quantile(0.95)
    agency_ratio['scatter_size'] = agency_ratio['scatter_size'].clip(upper=size_cap)
    min_size = 5
    agency_ratio['scatter_size'] = agency_ratio['scatter_size'].apply(lambda x: max(x, min_size))
    agency_ratio['award_count_normalized'] = np.log1p(agency_ratio['award_count'])
    agency_ratio['obligation_normalized'] = np.log1p(agency_ratio['federal_action_obligation'])
    agency_ratio['award_count_original'] = agency_ratio['award_count']
    agency_ratio['obligation_original'] = agency_ratio['federal_action_obligation']
    return agency_ratio

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
    vehicle_counts = df[df['modification_number'] == '0'].groupby('award_type').size().reset_index(name='count')
    total = vehicle_counts['count'].sum()
    vehicle_counts['percentage'] = vehicle_counts['count'] / total * 100 if total > 0 else 0.0
    return vehicle_counts

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
    base_awards = df[df['modification_number'] == '0']
    award_counts = base_awards.groupby('recipient_name').size().reset_index(name='award_count')
    return award_counts

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
    obligations = df.groupby('recipient_name')['federal_action_obligation'].sum().reset_index()
    return obligations

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

    # Convert action_date to datetime for date calculations
    df['action_date'] = pd.to_datetime(df['action_date'])

    # Get today's date
    today = datetime.now().date()

    # Calculate the end date (e.g., 24 months from today)
    end_date = today + pd.Timedelta(days=30.44 * months_ahead)

    # Identify which column to use for contract end date
    perf_end_date_col = None
    possible_cols = [
        'period_of_performance_end_date',
        'period_of_performance_end',
        'pop_end_date',
        'contract_end_date'
    ]
    for col in possible_cols:
        if col in df.columns:
            perf_end_date_col = col
            break

    # Normalize modification_number for base award identification
    df['modification_number'] = df['modification_number'].astype(str).str.strip().str.lower()
    base_patterns = ['^0+$', '^none$', '^$', '^original$', '^base$']
    df['is_base_award'] = df['modification_number'].str.match('|'.join(base_patterns))

    # Filter for base awards only
    base_awards = df[df['is_base_award'] == True]

    # If a valid end date column exists, use it for expiration calculation
    if perf_end_date_col:
        # Convert end date column to datetime
        base_awards[perf_end_date_col] = pd.to_datetime(base_awards[perf_end_date_col], errors='coerce')

        # Filter for contracts expiring within the window
        future_expiring = base_awards[
            (base_awards[perf_end_date_col] <= pd.Timestamp(end_date)) &
            (base_awards[perf_end_date_col] > pd.Timestamp(today))
        ]
    else:
        # Fallback: estimate end date as action_date + 1 year
        estimated_end_date = base_awards['action_date'] + pd.DateOffset(years=1)
        future_expiring = base_awards[
            (estimated_end_date <= pd.Timestamp(end_date)) &
            (estimated_end_date > pd.Timestamp(today))
        ]

    # Return the number of expiring contracts
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
    # Format billions
    if abs(value) >= 1_000_000_000:
        formatted = f"{value/1_000_000_000:.2f}B"
    # Format millions
    elif abs(value) >= 1_000_000:
        formatted = f"{value/1_000_000:.2f}M"
    # Format thousands
    elif abs(value) >= 1_000:
        formatted = f"{value/1_000:.1f}K"
    # Format small numbers
    else:
        formatted = f"{value:.2f}"

    # Remove trailing zeros after decimal for cleaner display
    if "." in formatted:
        formatted = formatted.rstrip("0").rstrip(".")

    # Add dollar sign if requested
    return f"${formatted}" if is_currency else formatted

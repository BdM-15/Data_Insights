"""
Award data processing functions for Data Insights.
Move all award-related data processing logic here for modularization.
"""

import pandas as pd
import numpy as np
from datetime import datetime
from src.backend.data.models.data_models import (
    TopAgencyByCount, TopAgencyByObligation, AgencyRatioMetrics, AwardSummaryItem, QuarterlyTrend, ContractVehicleSummary, RecipientAwardCount, RecipientObligation, ExpiringContract
)

from src.backend.core.database import get_db_engine
from sqlalchemy import text
def get_award_summary(
    naics_code: str = None,
    start_date: str = None,
    end_date: str = None,
    agency: str = None,
    contractor: str = None,
    psc: str = None
) -> list:
    """
    Calculate executive summary metrics using direct SQL for performance.
    Args:
        naics_code: Optional NAICS code filter
        start_date: Optional start date (YYYY-MM-DD)
        end_date: Optional end date (YYYY-MM-DD)
        agency: Optional agency filter
        contractor: Optional contractor/recipient filter
        psc: Optional PSC code filter
    Returns:
        List of AwardSummaryItem models
    """
    engine = get_db_engine()
    filters = []
    params = {}
    if naics_code:
        filters.append("naics_code = :naics_code")
        params["naics_code"] = naics_code
    if start_date:
        filters.append("action_date >= :start_date")
        params["start_date"] = start_date
    if end_date:
        filters.append("action_date <= :end_date")
        params["end_date"] = end_date
    if agency:
        filters.append("parent_award_agency_name = :agency")
        params["agency"] = agency
    if contractor:
        filters.append("recipient_name = :contractor")
        params["contractor"] = contractor
    if psc:
        filters.append("product_or_service_code = :psc")
        params["psc"] = psc
    where_clause = ""
    if filters:
        where_clause = "WHERE " + " AND ".join(filters)
    query = f"""
        SELECT
            SUM(federal_action_obligation) AS total_obligations,
            COUNT(*) FILTER (WHERE modification_number = '0') AS total_award_actions,
            CASE WHEN COUNT(*) FILTER (WHERE modification_number = '0') > 0
                 THEN SUM(federal_action_obligation) / COUNT(*) FILTER (WHERE modification_number = '0')
                 ELSE 0 END AS avg_award_value,
            COUNT(DISTINCT contract_award_unique_key) FILTER (WHERE modification_number = '0') AS active_contracts
        FROM s3_processed.usaspending_prime_awards
        {where_clause}
    """
    with engine.connect() as connection:
        result = connection.execute(text(query), params).fetchone()
        return [
            AwardSummaryItem(category="total_obligations", value=float(result[0] or 0)),
            AwardSummaryItem(category="total_award_actions", value=int(result[1] or 0)),
            AwardSummaryItem(category="avg_award_value", value=float(result[2] or 0)),
            AwardSummaryItem(category="active_contracts", value=int(result[3] or 0))
        ]

def get_top_agencies(df: pd.DataFrame, metric: str = "count", n: int = 15) -> list:
    """
    Get top agencies by award count or obligation amount.
    Args:
        df: DataFrame containing award data
        metric: 'count' for award actions, 'obligation' for dollar amount
        n: Number of top agencies to return
    Returns:
        List of TopAgencyByCount or TopAgencyByObligation models
    """
    if df.empty:
        return []
    if metric == "count":
        base_df = df[df['modification_number'] == '0']
        agency_data = base_df.groupby('parent_award_agency_name').size().reset_index(name='award_count')
        agency_data = agency_data.sort_values('award_count', ascending=False).head(n)
        return [TopAgencyByCount(**row) for row in agency_data.to_dict(orient='records')]
    else:
        agency_data = df.groupby('parent_award_agency_name')['federal_action_obligation'].sum().reset_index()
        agency_data = agency_data.sort_values('federal_action_obligation', ascending=False).head(n)
        return [TopAgencyByObligation(**row) for row in agency_data.to_dict(orient='records')]

def get_quarterly_trends(df: pd.DataFrame) -> list:
    """
    Calculate quarterly trends for obligations and award actions.
    Both obligations and award actions should be cumulative within each fiscal year.
    Args:
        df: DataFrame containing award data
    Returns:
        List of QuarterlyTrend Pydantic models
    """
    if df.empty:
        return []
    df['action_date'] = pd.to_datetime(df['action_date'])
    df['fiscal_year'] = df['action_date'].dt.year
    df.loc[df['action_date'].dt.month >= 10, 'fiscal_year'] = df['action_date'].dt.year + 1
    month_to_fiscal_quarter = {
        1: 2, 2: 2, 3: 2,
        4: 3, 5: 3, 6: 3,
        7: 4, 8: 4, 9: 4,
        10: 1, 11: 1, 12: 1
    }
    df['fiscal_quarter'] = df['action_date'].dt.month.map(month_to_fiscal_quarter)
    df['fiscal_period'] = df['fiscal_year'].astype(str) + '-Q' + df['fiscal_quarter'].astype(str)
    base_awards = df[df['modification_number'] == '0']
    award_counts = base_awards.groupby(['fiscal_year', 'fiscal_quarter', 'fiscal_period']).size().reset_index(name='award_count')
    obligations = df.groupby(['fiscal_year', 'fiscal_quarter', 'fiscal_period'])['federal_action_obligation'].sum().reset_index()
    award_counts = award_counts.sort_values(['fiscal_year', 'fiscal_quarter'])
    obligations = obligations.sort_values(['fiscal_year', 'fiscal_quarter'])
    obligations['federal_action_obligation'] = obligations.groupby('fiscal_year')['federal_action_obligation'].cumsum()
    award_counts['award_count'] = award_counts.groupby('fiscal_year')['award_count'].cumsum()
    quarterly_data = pd.merge(award_counts, obligations, on=['fiscal_year', 'fiscal_quarter', 'fiscal_period'], how='outer').fillna(0)
    quarterly_data = quarterly_data.sort_values(['fiscal_year', 'fiscal_quarter'])
    # Convert to list of QuarterlyTrend models
    result = []
    for _, row in quarterly_data.iterrows():
        result.append(QuarterlyTrend(
            quarter=row['fiscal_period'],
            year=int(row['fiscal_year']),
            total_obligation=float(row['federal_action_obligation']),
            award_count=int(row['award_count'])
        ))
    return result

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
    # Use the new processed table for all queries
    table_name = "s3_processed.usaspending_prime_awards"
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
    raise ValueError(f"No data found in '{table_name}' for the given filters.")

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

def get_agency_obligation_ratio(df: pd.DataFrame) -> list:
    """
    Calculate agency obligation ratio metrics for scatter plot analysis.
    Args:
        df: DataFrame containing award data
    Returns:
        List of AgencyRatioMetrics models
    """
    if df.empty:
        return []
    # Calculate award actions (base awards only)
    base_awards = df[df['modification_number'] == '0']
    award_count_per_agency = base_awards.groupby('parent_award_agency_name').size().rename('award_count')

    # Calculate obligations (sum of all obligations for all rows, not just base awards)
    obligation_per_agency = df.groupby('parent_award_agency_name')['federal_action_obligation'].sum().rename('federal_action_obligation')

    # Merge to ensure all agencies are included
    agency_ratio = pd.concat([award_count_per_agency, obligation_per_agency], axis=1).fillna(0).reset_index()

    # Calculate average award value (obligations / award actions)
    agency_ratio['avg_award_value'] = agency_ratio.apply(
        lambda row: row['federal_action_obligation'] / row['award_count'] if row['award_count'] > 0 else 0,
        axis=1
    )
    # Reason: Use avg_award_value for scatter size, but cap for outliers
    agency_ratio['scatter_size'] = np.abs(agency_ratio['avg_award_value'])
    size_cap = agency_ratio['scatter_size'].quantile(0.95)
    agency_ratio['scatter_size'] = agency_ratio['scatter_size'].clip(upper=size_cap)
    min_size = 5
    agency_ratio['scatter_size'] = agency_ratio['scatter_size'].apply(lambda x: max(x, min_size))
    agency_ratio['award_count_normalized'] = np.log1p(agency_ratio['award_count'])
    agency_ratio['obligation_normalized'] = np.log1p(agency_ratio['federal_action_obligation'])
    agency_ratio['award_count_original'] = agency_ratio['award_count']
    agency_ratio['obligation_original'] = agency_ratio['federal_action_obligation']
    return [AgencyRatioMetrics(**row) for row in agency_ratio.to_dict(orient='records')]

def get_contract_vehicles(df: pd.DataFrame) -> list:
    """
    Analyze contract vehicle distribution.
    Args:
        df: DataFrame containing award data
    Returns:
        List of ContractVehicleSummary models
    """
    if df.empty or 'award_type' not in df.columns:
        return []
    vehicle_counts = df[df['modification_number'] == '0'].groupby('award_type').size().reset_index(name='count')
    total = vehicle_counts['count'].sum()
    vehicle_counts['percentage'] = vehicle_counts['count'] / total * 100 if total > 0 else 0.0
    vehicle_counts = vehicle_counts.rename(columns={'award_type': 'contract_vehicle', 'count': 'award_count'})
    return [ContractVehicleSummary(**row) for row in vehicle_counts.to_dict(orient='records')]

def get_recipient_award_counts(df: pd.DataFrame) -> list:
    """
    Get award counts by recipient (base awards only).
    Args:
        df: DataFrame containing award data
    Returns:
        List of RecipientAwardCount models
    """
    if df.empty:
        return []
    base_awards = df[df['modification_number'] == '0']
    award_counts = base_awards.groupby('recipient_name').size().reset_index(name='award_count')
    award_counts = award_counts.rename(columns={'recipient_name': 'recipient_identifier'})
    return [RecipientAwardCount(**row) for row in award_counts.to_dict(orient='records')]

def get_recipient_obligations(df: pd.DataFrame) -> list:
    """
    Get total obligations by recipient (all awards including modifications).
    Args:
        df: DataFrame containing award data
    Returns:
        List of RecipientObligation models
    """
    if df.empty:
        return []
    obligations = df.groupby('recipient_name')['federal_action_obligation'].sum().reset_index()
    obligations = obligations.rename(columns={'recipient_name': 'recipient_identifier', 'federal_action_obligation': 'total_obligation'})
    return [RecipientObligation(**row) for row in obligations.to_dict(orient='records')]

def get_expiring_contracts(df: pd.DataFrame, months_ahead: int = 24) -> list:
    """
    Get contracts expiring in the specified months ahead.
    Args:
        df: DataFrame containing award data
        months_ahead: Number of months ahead to check for expiring contracts
    Returns:
        List of ExpiringContract models
    """
    if df.empty or 'action_date' not in df.columns:
        return []
    df['action_date'] = pd.to_datetime(df['action_date'])
    today = datetime.now().date()
    end_date = today + pd.Timedelta(days=30.44 * months_ahead)
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
    df['modification_number'] = df['modification_number'].astype(str).str.strip().str.lower()
    base_patterns = ['^0+$', '^none$', '^$', '^original$', '^base$']
    df['is_base_award'] = df['modification_number'].str.match('|'.join(base_patterns))
    base_awards = df[df['is_base_award'] == True]
    if perf_end_date_col:
        base_awards[perf_end_date_col] = pd.to_datetime(base_awards[perf_end_date_col], errors='coerce')
        future_expiring = base_awards[
            (base_awards[perf_end_date_col] <= pd.Timestamp(end_date)) &
            (base_awards[perf_end_date_col] > pd.Timestamp(today))
        ]
        contracts = []
        for _, row in future_expiring.iterrows():
            contracts.append(ExpiringContract(
                contract_award_unique_key=row.get('award_id_piid', ''),
                recipient_name=row.get('recipient_name'),
                period_of_performance_current_end_date=row[perf_end_date_col].date() if pd.notnull(row[perf_end_date_col]) else None,
                potential_total_value_of_award=row.get('potential_total_value_of_award'),
                days_to_expiration=(row[perf_end_date_col].date() - today).days if pd.notnull(row[perf_end_date_col]) else None
            ))
        return contracts
    else:
        estimated_end_date = base_awards['action_date'] + pd.DateOffset(years=1)
        future_expiring = base_awards[
            (estimated_end_date <= pd.Timestamp(end_date)) &
            (estimated_end_date > pd.Timestamp(today))
        ]
        contracts = []
        for _, row in future_expiring.iterrows():
            contracts.append(ExpiringContract(
                contract_award_unique_key=row.get('award_id_piid', ''),
                recipient_name=row.get('recipient_name'),
                period_of_performance_current_end_date=(row['action_date'] + pd.DateOffset(years=1)).date(),
                potential_total_value_of_award=row.get('potential_total_value_of_award'),
                days_to_expiration=((row['action_date'] + pd.DateOffset(years=1)).date() - today).days
            ))
        return contracts

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

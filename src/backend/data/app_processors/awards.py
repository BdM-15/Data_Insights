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

from src.backend.core.database import get_db_engine
from sqlalchemy import text
def get_top_agencies(
    metric: str = "count",
    n: int = 15,
    naics_code: str = None,
    start_date: str = None,
    end_date: str = None,
    agency: str = None,
    contractor: str = None,
    psc: str = None
) -> list:
    """
    Get top agencies by award count or obligation amount using direct SQL.
    Args:
        metric: 'count' for award actions, 'obligation' for dollar amount
        n: Number of top agencies to return
        naics_code, start_date, end_date, agency, contractor, psc: Optional filters
    Returns:
        List of TopAgencyByCount or TopAgencyByObligation models
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
    if metric == "count":
        query = f"""
            SELECT parent_award_agency_name, COUNT(*) AS award_count
            FROM s3_processed.usaspending_prime_awards
            {where_clause}
            AND modification_number = '0'
            GROUP BY parent_award_agency_name
            ORDER BY award_count DESC
            LIMIT :n
        """
        params["n"] = n
        with engine.connect() as connection:
            result = connection.execute(text(query), params).fetchall()
            return [TopAgencyByCount(parent_award_agency_name=row[0], award_count=row[1]) for row in result]
    else:
        query = f"""
            SELECT parent_award_agency_name, SUM(federal_action_obligation) AS federal_action_obligation
            FROM s3_processed.usaspending_prime_awards
            {where_clause}
            GROUP BY parent_award_agency_name
            ORDER BY federal_action_obligation DESC
            LIMIT :n
        """
        params["n"] = n
        with engine.connect() as connection:
            result = connection.execute(text(query), params).fetchall()
            return [TopAgencyByObligation(parent_award_agency_name=row[0], federal_action_obligation=row[1]) for row in result]


# Supports: Strategic Dashboard > Market Overview tab > Obligations and Award Actions Trend section > Quarterly Trends Chart
def get_quarterly_trends(
    naics_code: str = None,
    start_date: str = None,
    end_date: str = None,
    agency: str = None,
    contractor: str = None,
    psc: str = None
) -> list:
    """
    Calculate quarterly trends for obligations and award actions using direct SQL.
    Both obligations and award actions are cumulative within each fiscal year.
    Supports: Strategic Dashboard > Market Overview tab > Obligations and Award Actions Trend section > Quarterly Trends Chart
    Args:
        naics_code, start_date, end_date, agency, contractor, psc: Optional filters
    Returns:
        List of QuarterlyTrend Pydantic models
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
    # SQL: Calculate fiscal year/quarter, obligations, and award actions (base awards only)
    query = f"""
        SELECT
            EXTRACT(YEAR FROM action_date + INTERVAL '3 months') AS fiscal_year,
            EXTRACT(QUARTER FROM action_date + INTERVAL '3 months') AS fiscal_quarter,
            CONCAT(EXTRACT(YEAR FROM action_date + INTERVAL '3 months'), '-Q', EXTRACT(QUARTER FROM action_date + INTERVAL '3 months')) AS fiscal_period,
            COUNT(*) FILTER (WHERE modification_number = '0') AS award_count,
            SUM(federal_action_obligation) AS total_obligation
        FROM s3_processed.usaspending_prime_awards
        {where_clause}
        GROUP BY fiscal_year, fiscal_quarter, fiscal_period
        ORDER BY fiscal_year, fiscal_quarter
    """
    with engine.connect() as connection:
        result = connection.execute(text(query), params).fetchall()
        # Convert to list of QuarterlyTrend models
        # Cumulative within each fiscal year
        from collections import defaultdict
        year_award_cum = defaultdict(int)
        year_ob_cum = defaultdict(float)
        trends = []
        for row in result:
            year = int(row[0])
            quarter = int(row[1])
            period = str(row[2])
            award_count = int(row[3] or 0)
            total_ob = float(row[4] or 0)
            year_award_cum[year] += award_count
            year_ob_cum[year] += total_ob
            trends.append(QuarterlyTrend(
                quarter=period,
                year=year,
                total_obligation=year_ob_cum[year],
                award_count=year_award_cum[year]
            ))
        return trends

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


# Supports: Strategic Dashboard > Market Overview tab > Capture Intensity section > Capture Intensity Scatter Plot
def get_agency_obligation_ratio(
    naics_code: str = None,
    start_date: str = None,
    end_date: str = None,
    agency: str = None,
    contractor: str = None,
    psc: str = None
) -> list:
    """
    Calculate agency obligation ratio metrics for scatter plot analysis using direct SQL.
    Supports: Strategic Dashboard > Market Overview tab > Capture Intensity section > Capture Intensity Scatter Plot
    Args:
        naics_code, start_date, end_date, agency, contractor, psc: Optional filters
    Returns:
        List of AgencyRatioMetrics models
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
    # SQL: Get award count (base awards), obligations, and avg award value per agency
    query = f"""
        SELECT
            parent_award_agency_name,
            COUNT(*) FILTER (WHERE modification_number = '0') AS award_count,
            SUM(federal_action_obligation) AS federal_action_obligation
        FROM s3_processed.usaspending_prime_awards
        {where_clause}
        GROUP BY parent_award_agency_name
    """
    with engine.connect() as connection:
        result = connection.execute(text(query), params).fetchall()
        # Prepare for normalization and scatter size logic
        rows = []
        for row in result:
            agency_name = row[0]
            award_count = int(row[1] or 0)
            obligation = float(row[2] or 0)
            avg_award_value = obligation / award_count if award_count > 0 else 0
            rows.append({
                "parent_award_agency_name": agency_name,
                "award_count": award_count,
                "federal_action_obligation": obligation,
                "avg_award_value": avg_award_value
            })
        # Reason: Use avg_award_value for scatter size, but cap for outliers
        import numpy as np
        scatter_sizes = np.array([abs(r["avg_award_value"]) for r in rows])
        if len(scatter_sizes) > 0:
            size_cap = np.quantile(scatter_sizes, 0.95)
        else:
            size_cap = 1
        min_size = 5
        for r in rows:
            r["scatter_size"] = max(min(r["avg_award_value"], size_cap), min_size)
            r["award_count_normalized"] = np.log1p(r["award_count"])
            r["obligation_normalized"] = np.log1p(r["federal_action_obligation"])
            r["award_count_original"] = r["award_count"]
            r["obligation_original"] = r["federal_action_obligation"]
        return [AgencyRatioMetrics(**r) for r in rows]

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

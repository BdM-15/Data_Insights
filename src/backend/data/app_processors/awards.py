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

def get_naics_data(engine, naics_code="561210", start_date=None, end_date=None, agency=None, limit=None):
    """
    OPTIMIZED: Get NAICS data using targeted queries instead of loading full DataFrames.
    Replaces the legacy DataFrame-loading approach with efficient SQL queries.
    
    Args:
        engine: Database engine (maintained for compatibility)
        naics_code: NAICS code to filter by (default: 561210)
        start_date: Start date for filtering (YYYY-MM-DD)
        end_date: End date for filtering (YYYY-MM-DD)
        agency: Optional agency filter
        limit: Optional row limit (None = no limit, returns all matching data)
    
    Returns:
        DataFrame containing essential columns for dashboard visualization
    """
    # Delegate to the optimized function
    return get_naics_data_optimized(
        naics_code=naics_code,
        start_date=start_date, 
        end_date=end_date,
        agency=agency,
        limit=limit
    )


def get_naics_data_optimized(
    naics_code: str = "561210", 
    start_date: str = None, 
    end_date: str = None,
    agency: str = None,    limit: int = None
):
    """
    OPTIMIZED: Get NAICS data using targeted queries with optimal performance.
    Returns complete dataset for comprehensive analysis and visualization.
    
    Args:
        naics_code: NAICS code to filter by (default: 561210)
        start_date: Start date for filtering (YYYY-MM-DD)
        end_date: End date for filtering (YYYY-MM-DD)
        agency: Optional agency filter
        limit: Optional row limit (None = no limit, returns all matching data)
    
    Returns:
        DataFrame containing essential columns for dashboard visualization
    """
    import pandas as pd
    import logging
    from sqlalchemy import text
    
    engine = get_db_engine()
    filters = []
    params = {}
    
    # Build filter conditions
    if naics_code and naics_code != "All":
        filters.append("naics_code = :naics_code")
        params["naics_code"] = naics_code
    if start_date:
        filters.append("action_date >= :start_date")
        params["start_date"] = start_date
    if end_date:
        filters.append("action_date <= :end_date")
        params["end_date"] = end_date
    if agency and agency != "All":
        filters.append("parent_award_agency_name = :agency")
        params["agency"] = agency
    
    where_clause = ""
    if filters:
        where_clause = "WHERE " + " AND ".join(filters)
    
    # Add limit only if specified
    limit_clause = ""
    if limit:
        limit_clause = "LIMIT :limit"
        params["limit"] = limit
    
    # Use targeted query that returns only essential columns for dashboard
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
            type_of_contract_pricing,
            extent_competed,
            product_or_service_code,
            contract_award_unique_key
        FROM s3_processed.usaspending_prime_awards
        {where_clause}
        ORDER BY federal_action_obligation DESC, action_date DESC
        {limit_clause}
    """
    
    try:
        with engine.connect() as conn:
            df = pd.read_sql(text(query), conn, params=params)
            
            # Log performance metrics
            logger = logging.getLogger(__name__)
            logger.info(f"get_naics_data_optimized returned {len(df):,} rows with filters: {params}")
            
            return df
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"Error in get_naics_data_optimized: {str(e)}")
        # Return empty DataFrame on error instead of raising
        return pd.DataFrame()

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

# Optimized query functions using materialized views where possible

def get_award_summary_optimized(
    naics_code: str = None,
    start_date: str = None,
    end_date: str = None,
    agency: str = None,
    contractor: str = None,
    psc: str = None
) -> list:
    """
    OPTIMIZED: Get award summary using materialized view when possible, fallback to direct query.
    Much faster for common filter patterns.
    """
    engine = get_db_engine()
    
    # If no date filters and single-filter queries, try materialized view first
    if not start_date and not end_date and not contractor:
        with engine.connect() as connection:
            # Try materialized view for common single-filter cases
            if naics_code and not agency and not psc:
                result = connection.execute(text("""
                    SELECT total_obligations, total_award_actions, avg_award_value, active_contracts
                    FROM s3_processed.mv_award_summary_metrics
                    WHERE filter_category = 'NAICS' AND filter_value = :naics_code
                """), {"naics_code": naics_code}).fetchone()
                if result:
                    return [
                        AwardSummaryItem(category="total_obligations", value=float(result[0] or 0)),
                        AwardSummaryItem(category="total_award_actions", value=int(result[1] or 0)),
                        AwardSummaryItem(category="avg_award_value", value=float(result[2] or 0)),
                        AwardSummaryItem(category="active_contracts", value=int(result[3] or 0))
                    ]
            elif agency and not naics_code and not psc:
                result = connection.execute(text("""
                    SELECT total_obligations, total_award_actions, avg_award_value, active_contracts
                    FROM s3_processed.mv_award_summary_metrics
                    WHERE filter_category = 'AGENCY' AND filter_value = :agency
                """), {"agency": agency}).fetchone()
                if result:
                    return [
                        AwardSummaryItem(category="total_obligations", value=float(result[0] or 0)),
                        AwardSummaryItem(category="total_award_actions", value=int(result[1] or 0)),
                        AwardSummaryItem(category="avg_award_value", value=float(result[2] or 0)),
                        AwardSummaryItem(category="active_contracts", value=int(result[3] or 0))
                    ]
            elif psc and not naics_code and not agency:
                result = connection.execute(text("""
                    SELECT total_obligations, total_award_actions, avg_award_value, active_contracts
                    FROM s3_processed.mv_award_summary_metrics
                    WHERE filter_category = 'PSC' AND filter_value = :psc
                """), {"psc": psc}).fetchone()
                if result:
                    return [
                        AwardSummaryItem(category="total_obligations", value=float(result[0] or 0)),
                        AwardSummaryItem(category="total_award_actions", value=int(result[1] or 0)),
                        AwardSummaryItem(category="avg_award_value", value=float(result[2] or 0)),
                        AwardSummaryItem(category="active_contracts", value=int(result[3] or 0))
                    ]
            elif not naics_code and not agency and not psc:
                # Global summary
                result = connection.execute(text("""
                    SELECT total_obligations, total_award_actions, avg_award_value, active_contracts
                    FROM s3_processed.mv_award_summary_metrics
                    WHERE filter_category = 'ALL' AND filter_value = 'ALL'
                """)).fetchone()
                if result:
                    return [
                        AwardSummaryItem(category="total_obligations", value=float(result[0] or 0)),
                        AwardSummaryItem(category="total_award_actions", value=int(result[1] or 0)),
                        AwardSummaryItem(category="avg_award_value", value=float(result[2] or 0)),
                        AwardSummaryItem(category="active_contracts", value=int(result[3] or 0))
                    ]
    
    # Fallback to original implementation for complex queries
    return get_award_summary(naics_code, start_date, end_date, agency, contractor, psc)


def get_top_agencies_optimized(
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
    OPTIMIZED: Get top agencies using materialized view when possible.
    Falls back to direct query for complex filters.
    """
    engine = get_db_engine()
    
    # Use materialized view for simple cases without date/contractor filters
    if not start_date and not end_date and not contractor and not agency:
        with engine.connect() as connection:
            if metric == "count":
                if not naics_code and not psc:
                    # Simple top agencies by count
                    result = connection.execute(text("""
                        SELECT parent_award_agency_name, award_count
                        FROM s3_processed.mv_top_agencies
                        ORDER BY rank_by_count
                        LIMIT :n
                    """), {"n": n}).fetchall()
                    return [TopAgencyByCount(parent_award_agency_name=row[0], award_count=row[1]) for row in result]
                elif naics_code:
                    # Filter by NAICS using string search (materialized view contains comma-separated NAICS codes)
                    result = connection.execute(text("""
                        SELECT parent_award_agency_name, award_count
                        FROM s3_processed.mv_top_agencies
                        WHERE all_naics_codes LIKE '%' || :naics_code || '%'
                        ORDER BY rank_by_count
                        LIMIT :n
                    """), {"naics_code": naics_code, "n": n}).fetchall()
                    return [TopAgencyByCount(parent_award_agency_name=row[0], award_count=row[1]) for row in result]
            else:  # obligation
                if not naics_code and not psc:
                    # Simple top agencies by obligation
                    result = connection.execute(text("""
                        SELECT parent_award_agency_name, federal_action_obligation
                        FROM s3_processed.mv_top_agencies
                        ORDER BY rank_by_obligation
                        LIMIT :n
                    """), {"n": n}).fetchall()
                    return [TopAgencyByObligation(parent_award_agency_name=row[0], federal_action_obligation=row[1]) for row in result]
                elif naics_code:
                    # Filter by NAICS using string search
                    result = connection.execute(text("""
                        SELECT parent_award_agency_name, federal_action_obligation
                        FROM s3_processed.mv_top_agencies
                        WHERE all_naics_codes LIKE '%' || :naics_code || '%'
                        ORDER BY rank_by_obligation
                        LIMIT :n
                    """), {"naics_code": naics_code, "n": n}).fetchall()
                    return [TopAgencyByObligation(parent_award_agency_name=row[0], federal_action_obligation=row[1]) for row in result]
    
    # Fallback to original implementation for complex queries
    return get_top_agencies(metric, n, naics_code, start_date, end_date, agency, contractor, psc)


def get_quarterly_trends_optimized(
    naics_code: str = None,
    start_date: str = None,
    end_date: str = None,
    agency: str = None,
    contractor: str = None,
    psc: str = None
) -> list:
    """
    OPTIMIZED: Get quarterly trends using materialized view when possible.
    Much faster for common agency/NAICS filtering patterns.
    """
    engine = get_db_engine()
    
    # Use materialized view for simple agency or NAICS filters without date/contractor restrictions
    if not start_date and not end_date and not contractor and not psc:
        with engine.connect() as connection:
            if agency and not naics_code:
                # Agency-specific trends
                result = connection.execute(text("""
                    SELECT fiscal_year, fiscal_quarter, fiscal_period, 
                           cumulative_award_count, cumulative_obligation
                    FROM s3_processed.mv_quarterly_trends_optimized
                    WHERE parent_award_agency_name = :agency
                        AND naics_code IS NULL
                    ORDER BY fiscal_year, fiscal_quarter
                """), {"agency": agency}).fetchall()
            elif naics_code and not agency:
                # NAICS-specific trends
                result = connection.execute(text("""
                    SELECT fiscal_year, fiscal_quarter, fiscal_period,
                           cumulative_award_count, cumulative_obligation
                    FROM s3_processed.mv_quarterly_trends_optimized
                    WHERE naics_code = :naics_code
                        AND parent_award_agency_name IS NULL
                    ORDER BY fiscal_year, fiscal_quarter
                """), {"naics_code": naics_code}).fetchall()
            elif not agency and not naics_code:
                # Overall trends
                result = connection.execute(text("""
                    SELECT fiscal_year, fiscal_quarter, fiscal_period,
                           cumulative_award_count, cumulative_obligation
                    FROM s3_processed.mv_quarterly_trends_optimized
                    WHERE parent_award_agency_name IS NULL
                        AND naics_code IS NULL
                    ORDER BY fiscal_year, fiscal_quarter
                """)).fetchall()
            else:
                # Both agency and NAICS specified - fall back to direct query
                return get_quarterly_trends(naics_code, start_date, end_date, agency, contractor, psc)
            
            # Convert to QuarterlyTrend models
            trends = []
            for row in result:
                trends.append(QuarterlyTrend(
                    quarter=str(row[2]),
                    year=int(row[0]),
                    total_obligation=float(row[4] or 0),
                    award_count=int(row[3] or 0)
                ))
            return trends
    
    # Fallback to original implementation for complex queries
    return get_quarterly_trends(naics_code, start_date, end_date, agency, contractor, psc)


def get_agency_obligation_ratio_optimized(
    naics_code: str = None,
    start_date: str = None,
    end_date: str = None,
    agency: str = None,
    contractor: str = None,
    psc: str = None
) -> list:
    """
    OPTIMIZED: Get agency obligation ratio using materialized view when possible.
    Provides pre-calculated scatter plot data for better performance.
    """
    engine = get_db_engine()
    
    # Use materialized view for simple cases without filters
    if not naics_code and not start_date and not end_date and not agency and not contractor and not psc:
        with engine.connect() as connection:
            result = connection.execute(text("""
                SELECT parent_award_agency_name, award_count, federal_action_obligation,
                       avg_award_value, scatter_size_raw, award_count_normalized, obligation_normalized
                FROM s3_processed.mv_agency_obligation_ratio
                ORDER BY federal_action_obligation DESC
            """)).fetchall()
            
            # Apply size capping logic
            scatter_sizes = [row[4] for row in result]
            size_cap = np.quantile(scatter_sizes, 0.95) if scatter_sizes else 100
            
            rows = []
            for row in result:
                scatter_size = min(max(row[4], 5), size_cap)  # Apply cap and minimum
                rows.append(AgencyRatioMetrics(
                    parent_award_agency_name=row[0],
                    award_count=int(row[1]),
                    federal_action_obligation=float(row[2]),
                    avg_award_value=float(row[3]),
                    scatter_size=scatter_size,
                    award_count_normalized=float(row[5]),
                    obligation_normalized=float(row[6]),
                    award_count_original=int(row[1]),
                    obligation_original=float(row[2])
                ))
            return rows
    
    # Fallback to original implementation for filtered queries
    return get_agency_obligation_ratio(naics_code, start_date, end_date, agency, contractor, psc)


def get_expiring_contracts_optimized(
    months_ahead: int = 24,
    naics_code: str = None,
    agency: str = None,
    contractor: str = None,
    limit: int = 100
) -> list:
    """
    OPTIMIZED: Get expiring contracts using materialized view.
    Much faster than calculating end dates on-the-fly.
    """
    engine = get_db_engine()
    
    with engine.connect() as connection:
        filters = []
        params = {"months_ahead": months_ahead, "limit": limit}
        
        if naics_code:
            filters.append("naics_code = :naics_code")
            params["naics_code"] = naics_code
        if agency:
            filters.append("parent_award_agency_name = :agency")
            params["agency"] = agency
        if contractor:
            filters.append("recipient_name = :contractor")
            params["contractor"] = contractor
        
        where_clause = ""
        if filters:
            where_clause = "WHERE " + " AND ".join(filters)
        
        # Use materialized view for fast expiring contracts lookup
        query = f"""
            SELECT contract_award_unique_key, award_id_piid, recipient_name,
                   parent_award_agency_name, funding_sub_agency_name,
                   federal_action_obligation, potential_total_value_of_award,
                   effective_end_date, days_to_expiration, expiration_timeframe,
                   date_quality
            FROM s3_processed.mv_expiring_contracts
            {where_clause}
            AND days_to_expiration <= :months_ahead * 30  -- Convert months to approximate days
            ORDER BY days_to_expiration, federal_action_obligation DESC
            LIMIT :limit
        """
        
        result = connection.execute(text(query), params).fetchall()
        
        contracts = []
        for row in result:
            contracts.append(ExpiringContract(
                contract_award_unique_key=row[0] or '',
                recipient_name=row[2],
                parent_award_agency_name=row[3],
                funding_sub_agency_name=row[4],
                federal_action_obligation=float(row[5] or 0),
                period_of_performance_current_end_date=row[7],
                potential_total_value_of_award=float(row[6] or 0),
                days_to_expiration=int(row[8] or 0)
            ))
        
        return contracts

def get_geographic_state_obligations(
    naics_code: str = None,
    start_date: str = None,
    end_date: str = None,
    agency: str = None,
    contractor: str = None,
    psc: str = None
) -> list:
    """
    OPTIMIZED: Get state obligations using SQL instead of pandas groupby.
    
    Args:
        naics_code, start_date, end_date, agency, contractor, psc: Optional filters
    
    Returns:
        List of dictionaries with location and value for geographic analysis
    """
    import logging
    from sqlalchemy import text
    
    engine = get_db_engine()
    filters = []
    params = {}
    
    if naics_code and naics_code != "All":
        filters.append("naics_code = :naics_code")
        params["naics_code"] = naics_code
    if start_date:
        filters.append("action_date >= :start_date")
        params["start_date"] = start_date
    if end_date:
        filters.append("action_date <= :end_date")
        params["end_date"] = end_date
    if agency and agency != "All":
        filters.append("parent_award_agency_name = :agency")
        params["agency"] = agency
    if contractor and contractor != "All":
        filters.append("recipient_name = :contractor")
        params["contractor"] = contractor
    if psc and psc != "All":
        filters.append("product_or_service_code = :psc")
        params["psc"] = psc
    
    where_clause = ""
    if filters:
        where_clause = "WHERE " + " AND ".join(filters)
    
    query = f"""
        SELECT 
            recipient_state_code as location,
            SUM(federal_action_obligation) as value
        FROM s3_processed.usaspending_prime_awards
        {where_clause}
        AND recipient_state_code IS NOT NULL
        GROUP BY recipient_state_code
        ORDER BY value DESC
    """
    
    try:
        with engine.connect() as conn:
            result = conn.execute(text(query), params).fetchall()
            return [{"location": row[0], "value": float(row[1])} for row in result]
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"Error in get_geographic_state_obligations: {str(e)}")
        return []

def get_contract_vehicle_agency_analysis(
    naics_code: str = None,
    start_date: str = None,
    end_date: str = None,
    agency: str = None,
    contractor: str = None,
    psc: str = None
) -> list:
    """
    OPTIMIZED: Get agency-vehicle preference data using SQL instead of pandas groupby.
    
    Args:
        naics_code, start_date, end_date, agency, contractor, psc: Optional filters
    
    Returns:
        List of dictionaries for agency-vehicle analysis
    """
    import logging
    from sqlalchemy import text
    
    engine = get_db_engine()
    filters = []
    params = {}
    
    if naics_code and naics_code != "All":
        filters.append("naics_code = :naics_code")
        params["naics_code"] = naics_code
    if start_date:
        filters.append("action_date >= :start_date")
        params["start_date"] = start_date
    if end_date:
        filters.append("action_date <= :end_date")
        params["end_date"] = end_date
    if agency and agency != "All":
        filters.append("parent_award_agency_name = :agency")
        params["agency"] = agency
    if contractor and contractor != "All":
        filters.append("recipient_name = :contractor")
        params["contractor"] = contractor
    if psc and psc != "All":
        filters.append("product_or_service_code = :psc")
        params["psc"] = psc
    
    where_clause = ""
    if filters:
        where_clause = "WHERE " + " AND ".join(filters)
    
    query = f"""
        SELECT 
            parent_award_agency_name,
            award_type,
            SUM(federal_action_obligation) as federal_action_obligation
        FROM s3_processed.usaspending_prime_awards
        {where_clause}
        AND modification_number = '0'
        GROUP BY parent_award_agency_name, award_type
        ORDER BY parent_award_agency_name, federal_action_obligation DESC
    """
    
    try:
        with engine.connect() as conn:
            result = conn.execute(text(query), params).fetchall()
            return [{"parent_award_agency_name": row[0], "award_type": row[1], "federal_action_obligation": float(row[2])} for row in result]
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"Error in get_contract_vehicle_agency_analysis: {str(e)}")
        return []

def get_contract_vehicle_success_rates(
    naics_code: str = None,
    start_date: str = None,
    end_date: str = None,
    agency: str = None,
    contractor: str = None,
    psc: str = None
) -> list:
    """
    OPTIMIZED: Get vehicle success rates (obligation by vehicle type) using SQL.
    
    Args:
        naics_code, start_date, end_date, agency, contractor, psc: Optional filters
    
    Returns:
        List of dictionaries for vehicle success rate analysis
    """
    import logging
    from sqlalchemy import text
    
    engine = get_db_engine()
    filters = []
    params = {}
    
    if naics_code and naics_code != "All":
        filters.append("naics_code = :naics_code")
        params["naics_code"] = naics_code
    if start_date:
        filters.append("action_date >= :start_date")
        params["start_date"] = start_date
    if end_date:
        filters.append("action_date <= :end_date")
        params["end_date"] = end_date
    if agency and agency != "All":
        filters.append("parent_award_agency_name = :agency")
        params["agency"] = agency
    if contractor and contractor != "All":
        filters.append("recipient_name = :contractor")
        params["contractor"] = contractor
    if psc and psc != "All":
        filters.append("product_or_service_code = :psc")
        params["psc"] = psc
    
    where_clause = ""
    if filters:
        where_clause = "WHERE " + " AND ".join(filters)
    
    query = f"""
        SELECT 
            award_type as contract_vehicle,
            SUM(federal_action_obligation) as obligation
        FROM s3_processed.usaspending_prime_awards
        {where_clause}
        AND modification_number = '0'
        GROUP BY award_type
        ORDER BY obligation DESC
    """
    
    try:
        with engine.connect() as conn:
            result = conn.execute(text(query), params).fetchall()
            return [{"contract_vehicle": row[0], "obligation": float(row[1])} for row in result]
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"Error in get_contract_vehicle_success_rates: {str(e)}")
        return []

def get_contract_type_analysis(
    naics_code: str = None,
    start_date: str = None,
    end_date: str = None,
    agency: str = None,
    contractor: str = None,
    psc: str = None
) -> dict:
    """
    OPTIMIZED: Get contract type competition and value analysis using SQL.
    
    Args:
        naics_code, start_date, end_date, agency, contractor, psc: Optional filters
    
    Returns:
        Dictionary with 'competition' and 'value' analysis data
    """
    import logging
    from sqlalchemy import text
    
    engine = get_db_engine()
    filters = []
    params = {}
    
    if naics_code and naics_code != "All":
        filters.append("naics_code = :naics_code")
        params["naics_code"] = naics_code
    if start_date:
        filters.append("action_date >= :start_date")
        params["start_date"] = start_date
    if end_date:
        filters.append("action_date <= :end_date")
        params["end_date"] = end_date
    if agency and agency != "All":
        filters.append("parent_award_agency_name = :agency")
        params["agency"] = agency
    if contractor and contractor != "All":
        filters.append("recipient_name = :contractor")
        params["contractor"] = contractor
    if psc and psc != "All":
        filters.append("product_or_service_code = :psc")
        params["psc"] = psc
    
    where_clause = ""
    if filters:
        where_clause = "WHERE " + " AND ".join(filters)
    
    # Competition analysis query
    competition_query = f"""
        SELECT 
            type_of_contract_pricing as contract_type,
            COUNT(DISTINCT recipient_name) as number_of_competitors
        FROM s3_processed.usaspending_prime_awards
        {where_clause}
        AND type_of_contract_pricing IS NOT NULL
        GROUP BY type_of_contract_pricing
        ORDER BY number_of_competitors DESC
        LIMIT 10
    """
    
    # Value analysis query  
    value_query = f"""
        SELECT 
            type_of_contract_pricing as contract_type,
            SUM(federal_action_obligation) as total_obligation,
            COUNT(DISTINCT recipient_name) as number_of_competitors
        FROM s3_processed.usaspending_prime_awards
        {where_clause}
        AND type_of_contract_pricing IS NOT NULL
        GROUP BY type_of_contract_pricing
        ORDER BY total_obligation DESC
        LIMIT 10
    """
    
    try:
        with engine.connect() as conn:
            # Get competition data
            competition_result = conn.execute(text(competition_query), params).fetchall()
            competition_data = []
            for row in competition_result:
                contract_type = row[0]
                contract_type_display = contract_type
                if 'FIXED PRICE WITH ECONOMIC PRICE ADJUST' in contract_type.upper():
                    contract_type_display = 'FIXED PRICE WITH EPA'
                elif contract_type.startswith('ORDER DEPENDENT'):
                    contract_type_display = 'ORDER DEPENDENT'
                
                contract_type_hover = ''
                if contract_type.startswith('ORDER DEPENDENT'):
                    contract_type_hover = 'IDV ALLOWS PRICING ARRANGEMENT TO BE DETERMINED SEPARATELY FOR EACH ORDER'
                
                competition_data.append({
                    "Contract Type": contract_type,
                    "Contract Type Display": contract_type_display,
                    "Contract Type Hover": contract_type_hover,
                    "Number of Competitors": int(row[1])
                })
            
            # Get value data
            value_result = conn.execute(text(value_query), params).fetchall()
            value_data = []
            for row in value_result:
                contract_type = row[0]
                contract_type_display = contract_type
                if 'FIXED PRICE WITH ECONOMIC PRICE ADJUST' in contract_type.upper():
                    contract_type_display = 'FIXED PRICE WITH EPA'
                elif contract_type.startswith('ORDER DEPENDENT'):
                    contract_type_display = 'ORDER DEPENDENT'
                
                contract_type_hover = ''
                if contract_type.startswith('ORDER DEPENDENT'):
                    contract_type_hover = 'IDV ALLOWS PRICING ARRANGEMENT TO BE DETERMINED SEPARATELY FOR EACH ORDER'
                
                total_obligation = float(row[1])
                number_of_competitors = int(row[2])
                avg_obligation = total_obligation / number_of_competitors if number_of_competitors > 0 else 0
                
                value_data.append({
                    "Contract Type": contract_type,
                    "Contract Type Display": contract_type_display,
                    "Contract Type Hover": contract_type_hover,
                    "Total Obligation": total_obligation,
                    "Number of Competitors": number_of_competitors,
                    "Average Obligation": avg_obligation
                })
            
            return {
                "competition": competition_data,
                "value": value_data
            }
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"Error in get_contract_type_analysis: {str(e)}")
        return {"competition": [], "value": []}

def get_agency_top_data(
    agency: str,
    naics_code: str = None,
    start_date: str = None,
    end_date: str = None,
    contractor: str = None,
    psc: str = None
) -> dict:
    """
    OPTIMIZED: Get top NAICS, PSC, and contractors for a specific agency using SQL.
    
    Args:
        agency: Required agency name
        naics_code, start_date, end_date, contractor, psc: Optional filters
    
    Returns:
        Dictionary with 'naics', 'psc', and 'contractors' data
    """
    import logging
    from sqlalchemy import text
    
    if not agency or agency == "All":
        return {"naics": [], "psc": [], "contractors": []}
    
    engine = get_db_engine()
    filters = ["parent_award_agency_name = :agency"]
    params = {"agency": agency}
    
    if naics_code and naics_code != "All":
        filters.append("naics_code = :naics_code")
        params["naics_code"] = naics_code
    if start_date:
        filters.append("action_date >= :start_date")
        params["start_date"] = start_date
    if end_date:
        filters.append("action_date <= :end_date")
        params["end_date"] = end_date
    if contractor and contractor != "All":
        filters.append("recipient_name = :contractor")
        params["contractor"] = contractor
    if psc and psc != "All":
        filters.append("product_or_service_code = :psc")
        params["psc"] = psc
    
    where_clause = "WHERE " + " AND ".join(filters)
    
    # Top NAICS query
    naics_query = f"""
        SELECT 
            naics_code,
            naics_description,
            SUM(federal_action_obligation) as federal_action_obligation
        FROM s3_processed.usaspending_prime_awards
        {where_clause}
        AND naics_code IS NOT NULL
        AND naics_description IS NOT NULL
        GROUP BY naics_code, naics_description
        ORDER BY federal_action_obligation DESC
        LIMIT 10
    """
    
    # Top PSC query
    psc_query = f"""
        SELECT 
            product_or_service_code,
            product_or_service_code_description,
            SUM(federal_action_obligation) as federal_action_obligation
        FROM s3_processed.usaspending_prime_awards
        {where_clause}
        AND product_or_service_code IS NOT NULL
        AND product_or_service_code_description IS NOT NULL
        GROUP BY product_or_service_code, product_or_service_code_description
        ORDER BY federal_action_obligation DESC
        LIMIT 10
    """
    
    # Top contractors query
    contractors_query = f"""
        SELECT 
            recipient_name,
            SUM(federal_action_obligation) as federal_action_obligation
        FROM s3_processed.usaspending_prime_awards
        {where_clause}
        AND recipient_name IS NOT NULL
        GROUP BY recipient_name
        ORDER BY federal_action_obligation DESC
        LIMIT 10
    """
    
    try:
        with engine.connect() as conn:
            # Get NAICS data
            naics_result = conn.execute(text(naics_query), params).fetchall()
            naics_data = [{"naics_code": row[0], "naics_description": row[1], "federal_action_obligation": float(row[2])} for row in naics_result]
            
            # Get PSC data
            psc_result = conn.execute(text(psc_query), params).fetchall()
            psc_data = [{"product_or_service_code": row[0], "product_or_service_code_description": row[1], "federal_action_obligation": float(row[2])} for row in psc_result]
            
            # Get contractors data
            contractors_result = conn.execute(text(contractors_query), params).fetchall()
            contractors_data = [{"recipient_name": row[0], "federal_action_obligation": float(row[1])} for row in contractors_result]
            
            return {
                "naics": naics_data,
                "psc": psc_data,
                "contractors": contractors_data
            }
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"Error in get_agency_top_data: {str(e)}")
        return {"naics": [], "psc": [], "contractors": []}

def get_competitor_agency_relationships(
    naics_code: str = None,
    start_date: str = None,
    end_date: str = None,
    agency: str = None,
    contractor: str = None,
    psc: str = None,
    top_n: int = 5
) -> list:
    """
    OPTIMIZED: Get competitor-agency relationships for heatmap visualization using SQL.
    
    Args:
        naics_code, start_date, end_date, agency, contractor, psc: Optional filters
        top_n: Number of top competitors to include (default 5)
    
    Returns:
        List of dictionaries for competitor-agency heatmap
    """
    import logging
    from sqlalchemy import text
    
    engine = get_db_engine()
    filters = []
    params = {}
    
    if naics_code and naics_code != "All":
        filters.append("naics_code = :naics_code")
        params["naics_code"] = naics_code
    if start_date:
        filters.append("action_date >= :start_date")
        params["start_date"] = start_date
    if end_date:
        filters.append("action_date <= :end_date")
        params["end_date"] = end_date
    if agency and agency != "All":
        filters.append("parent_award_agency_name = :agency")
        params["agency"] = agency
    if contractor and contractor != "All":
        filters.append("recipient_name = :contractor")
        params["contractor"] = contractor
    if psc and psc != "All":
        filters.append("product_or_service_code = :psc")
        params["psc"] = psc
    
    where_clause = ""
    if filters:
        where_clause = "WHERE " + " AND ".join(filters)
    
    params["top_n"] = top_n
    query = f"""
        WITH top_competitors AS (
            SELECT recipient_name
            FROM s3_processed.usaspending_prime_awards
            {where_clause}
            GROUP BY recipient_name
            ORDER BY SUM(federal_action_obligation) DESC
            LIMIT :top_n
        ),
        competitor_agencies AS (
            SELECT 
                recipient_name,
                parent_award_agency_name,
                SUM(federal_action_obligation) as federal_action_obligation,
                ROW_NUMBER() OVER (PARTITION BY recipient_name ORDER BY SUM(federal_action_obligation) DESC) as agency_rank
            FROM s3_processed.usaspending_prime_awards
            {where_clause}
            AND recipient_name IN (SELECT recipient_name FROM top_competitors)
            GROUP BY recipient_name, parent_award_agency_name
        )
        SELECT 
            recipient_name,
            parent_award_agency_name,
            federal_action_obligation
        FROM competitor_agencies
        WHERE agency_rank <= 3
        ORDER BY recipient_name, federal_action_obligation DESC
    """
    
    try:
        with engine.connect() as conn:
            result = conn.execute(text(query), params).fetchall()
            return [{"recipient_name": row[0], "parent_award_agency_name": row[1], "federal_action_obligation": float(row[2])} for row in result]
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"Error in get_competitor_agency_relationships: {str(e)}")
        return []

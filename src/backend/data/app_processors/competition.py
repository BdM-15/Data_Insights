"""
Competition analysis functions for Data Insights.
Move all competition-related data processing logic here for modularization.
"""

import pandas as pd
import numpy as np
from src.backend.data.models.data_models import TreemapPathElement, CompetitorPerformance


from sqlalchemy import text
from src.backend.core.database import get_db_engine

def get_treemap_data(
    naics_code: str = None,
    start_date: str = None,
    end_date: str = None,
    agency: str = None,
    contractor: str = None,
    psc: str = None,
    limit: int = 50
) -> list:
    """
    Prepare data for the competitive landscape treemap using optimized SQL.

    Args:
        naics_code: Optional NAICS code filter
        start_date: Optional start date filter (YYYY-MM-DD)
        end_date: Optional end date filter (YYYY-MM-DD)
        agency: Optional parent award agency filter
        contractor: Optional recipient name filter
        psc: Optional PSC code filter
        limit: Maximum number of results to return (default 50)

    Returns:
        List of TreemapPathElement models
    """
    engine = get_db_engine()
    filters = []
    params = {"limit": limit}
    
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
    
    # Optimized query: use MAX instead of MODE for better performance, add LIMIT
    query = f"""
        SELECT
            recipient_parent_name,
            recipient_name,
            funding_sub_agency_name,
            -- Use MAX for better performance than MODE()
            MAX(CASE WHEN transaction_description IS NOT NULL AND transaction_description != '' 
                     THEN transaction_description 
                     ELSE 'All Contracts' END) AS transaction_description,
            SUM(federal_action_obligation) AS federal_action_obligation,
            COUNT(*) FILTER (WHERE modification_number = '0') AS award_count
        FROM s3_processed.usaspending_prime_awards
        {where_clause}
        GROUP BY recipient_parent_name, recipient_name, funding_sub_agency_name
        ORDER BY SUM(federal_action_obligation) DESC
        LIMIT :limit
    """
    
    with engine.connect() as connection:
        result = connection.execute(text(query), params).fetchall()
        
        # Calculate market share and win rate from the limited result set
        total_obligations = sum(float(row[4] or 0) for row in result)
        total_awards = sum(int(row[5] or 0) for row in result)
        
        treemap_rows = []
        for row in result:
            market_share = (float(row[4]) / total_obligations * 100) if total_obligations > 0 else 0
            win_rate = (int(row[5]) / total_awards * 100) if total_awards > 0 else 0
            
            treemap_rows.append(TreemapPathElement(
                recipient_parent_name=row[0],
                recipient_name=row[1],
                funding_sub_agency_name=row[2],
                transaction_description=row[3] or 'All Contracts',
                federal_action_obligation=float(row[4] or 0),
                award_count=int(row[5] or 0),
                market_share=market_share,
                win_rate=win_rate
            ))
        
        # Already sorted by obligation descending due to ORDER BY
        return treemap_rows


def get_competitive_landscape(df: pd.DataFrame) -> list:
    """
    Analyze competitive landscape among contractors.

    Args:
        df: DataFrame containing award data

    Returns:
        List of CompetitorPerformance models
    """
    if df.empty:
        return []

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

    return [CompetitorPerformance(**row) for row in competitors.to_dict(orient='records')]

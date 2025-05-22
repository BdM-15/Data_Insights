"""
Agency data processing functions for Data Insights.
Move all agency-related data processing logic here for modularization.
"""

import pandas as pd
from src.backend.data.models.data_models import TopAgencyByCount, TopAgencyByObligation

def get_top_agencies_by_award_count(df, n=15) -> list:
    """
    Get top agencies by award count (base awards only).

    Args:
        df: DataFrame containing award data
        n: Number of top agencies to return

    Returns:
        List of TopAgencyByCount models
    """
    if df.empty:
        return []

    # Filter to base awards only (no modifications)
    base_df = df[df['modification_number'] == '0']

    # Group by agency and count
    agency_data = base_df.groupby('parent_award_agency_name').size().reset_index(name='award_count')
    agency_data = agency_data.sort_values('award_count', ascending=False).head(n)

    return [TopAgencyByCount(**row) for row in agency_data.to_dict(orient='records')]


def get_top_agencies_by_obligation(df, n=15) -> list:
    """
    Get top agencies by obligation amount.

    Args:
        df: DataFrame containing award data
        n: Number of top agencies to return

    Returns:
        List of TopAgencyByObligation models
    """
    if df.empty:
        return []

    # Group by agency and sum obligations
    agency_data = df.groupby('parent_award_agency_name')['federal_action_obligation'].sum().reset_index()
    agency_data = agency_data.sort_values('federal_action_obligation', ascending=False).head(n)

    return [TopAgencyByObligation(**row) for row in agency_data.to_dict(orient='records')]

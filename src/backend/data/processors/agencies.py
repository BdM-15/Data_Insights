"""
This module contains functions for processing and analyzing agency-related data.
"""
import pandas as pd
import numpy as np
from typing import List, Union
from src.backend.data.models.data_models import (
    TopAgencyByCount, TopAgencyByObligation, AgencyRatioMetrics
)

def get_top_agencies(df, metric="count", n=15) -> List[Union[TopAgencyByCount, TopAgencyByObligation]]:
    """
    Get top agencies by award count or obligation amount.
    
    Args:
        df: DataFrame containing award data
        metric: 'count' for award actions, 'obligation' for dollar amount
        n: Number of top agencies to return
        
    Returns:
        List of TopAgencyByCount or TopAgencyByObligation objects
    """
    if df.empty:
        return []
    
    if metric == "count":
        # Filter to base awards only (no modifications)
        base_df = df[df['modification_number'] == '0']
        # Group by agency and count
        agency_data = base_df.groupby('parent_award_agency_name').size().reset_index(name='award_count')
        agency_data = agency_data.sort_values('award_count', ascending=False).head(n)
        # Convert DataFrame to list of Pydantic models
        top_agencies_list = [
            TopAgencyByCount(
                parent_award_agency_name=row['parent_award_agency_name'],
                award_count=int(row['award_count'])
            )
            for index, row in agency_data.iterrows()
        ]
        return top_agencies_list
    else:
        # Group by agency and sum obligations
        agency_data = df.groupby('parent_award_agency_name')['federal_action_obligation'].sum().reset_index()
        agency_data = agency_data.sort_values('federal_action_obligation', ascending=False).head(n)
        # Convert DataFrame to list of Pydantic models
        top_agencies_list = [
            TopAgencyByObligation(
                parent_award_agency_name=row['parent_award_agency_name'],
                federal_action_obligation=float(row['federal_action_obligation'])
            )
            for index, row in agency_data.iterrows()
        ]
        return top_agencies_list

def get_agency_obligation_ratio(df) -> List[AgencyRatioMetrics]:
    """
    Calculate action-to-obligation ratio for the scatter plot analysis.
    Uses normalization to prevent outliers from bunching the visualization.
    
    Args:
        df: DataFrame containing award data
        
    Returns:
        List of AgencyRatioMetrics objects
    """
    if df.empty:
        return []
    
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
    
    # Convert DataFrame to list of Pydantic models
    ratio_metrics_list = [
        AgencyRatioMetrics(
            parent_award_agency_name=row['parent_award_agency_name'],
            award_count=int(row['award_count']),
            federal_action_obligation=float(row['federal_action_obligation']),
            avg_award_value=float(row['avg_award_value']),
            scatter_size=float(row['scatter_size']),
            award_count_normalized=float(row['award_count_normalized']),
            obligation_normalized=float(row['obligation_normalized']),
            award_count_original=int(row['award_count_original']),
            obligation_original=float(row['obligation_original'])
        )
        for index, row in agency_ratio.iterrows()
    ]
    return ratio_metrics_list

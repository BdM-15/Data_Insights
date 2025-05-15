"""
This module contains functions for processing and analyzing award-related data.
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Any
from src.backend.data.models.data_models import (
    AwardSummaryItem, QuarterlyTrend, ContractVehicleSummary, 
    RecipientAwardCount, RecipientObligation, ExpiringContract
)

def get_award_summary(df) -> List[AwardSummaryItem]:
    """
    Calculate summary metrics from the data.
    
    Args:
        df: DataFrame containing award data
        
    Returns:
        List of AwardSummaryItem objects
    """
    if df.empty:
        return [
            AwardSummaryItem(category="total_obligations", value=0, count=None),
            AwardSummaryItem(category="total_award_actions", value=0, count=0),
            AwardSummaryItem(category="avg_award_value", value=0, count=None),
            AwardSummaryItem(category="active_contracts", value=0, count=0)
        ]
    
    # Filter for base awards (no modifications)
    base_awards = df[df['modification_number'] == '0']
    
    # Calculate metrics
    total_obligations = df['federal_action_obligation'].sum()
    total_award_actions = len(base_awards)
    avg_award_value = total_obligations / total_award_actions if total_award_actions > 0 else 0
    active_contracts = len(base_awards)
    
    summary_items = [
        AwardSummaryItem(category="total_obligations", value=float(total_obligations), count=None),
        AwardSummaryItem(category="total_award_actions", value=float(total_award_actions), count=int(total_award_actions)),
        AwardSummaryItem(category="avg_award_value", value=float(avg_award_value), count=None),
        AwardSummaryItem(category="active_contracts", value=float(active_contracts), count=int(active_contracts))
    ]
    return summary_items

def get_quarterly_trends(df) -> List[QuarterlyTrend]:
    """
    Calculate quarterly trends for obligations and award actions.
    Both obligations and award actions should be cumulative within each fiscal year.
    
    Args:
        df: DataFrame containing award data
        
    Returns:
        List of QuarterlyTrend objects
    """
    if df.empty:
        return []
    
    # Convert action_date to datetime
    df['action_date'] = pd.to_datetime(df['action_date'])
    
    # Calculate fiscal year (Oct 1 to Sep 30)
    # US Federal fiscal year runs from October 1 to September 30
    # So if the month is >= 10 (October), it's in the next fiscal year
    df['fiscal_year'] = df['action_date'].dt.year
    df.loc[df['action_date'].dt.month >= 10, 'fiscal_year'] = df['action_date'].dt.year + 1
    
    # Map calendar quarters to fiscal quarters
    # Calendar Q4 (Oct-Dec) = Fiscal Q1, Calendar Q1 (Jan-Mar) = Fiscal Q2, etc.
    month_to_fiscal_quarter = {
        1: 2, 2: 2, 3: 2,  # Calendar Q1 = Fiscal Q2
        4: 3, 5: 3, 6: 3,  # Calendar Q2 = Fiscal Q3
        7: 4, 8: 4, 9: 4,  # Calendar Q3 = Fiscal Q4
        10: 1, 11: 1, 12: 1,  # Calendar Q4 = Fiscal Q1
    }
    df['fiscal_quarter'] = df['action_date'].dt.month.map(month_to_fiscal_quarter)
    
    # Create fiscal period label
    df['fiscal_period'] = df['fiscal_year'].astype(str) + '-Q' + df['fiscal_quarter'].astype(str)
    
    # Filter base awards for award count - simply filter for modification_number == '0'
    # Reason: As per your feedback, we'll just use a direct string comparison for simplicity
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
    
    # Convert DataFrame to list of Pydantic models
    trends_list = [
        QuarterlyTrend(
            quarter=f"Q{row['fiscal_quarter']}", 
            year=int(row['fiscal_year']),
            total_obligation=float(row['federal_action_obligation']),
            award_count=int(row['award_count'])
        )
        for index, row in quarterly_data.iterrows()
    ]
    return trends_list

def get_contract_vehicles(df) -> List[ContractVehicleSummary]:
    """
    Analyze contract vehicle distribution.
    
    Args:
        df: DataFrame containing award data
        
    Returns:
        List of ContractVehicleSummary objects
    """
    if df.empty or 'award_type' not in df.columns:
        return []
    
    # Count by award type (base awards only)
    base_awards = df[df['modification_number'] == '0']
    vehicle_counts = base_awards.groupby('award_type').size().reset_index(name='count')
    
    # Calculate percentages
    total_awards = vehicle_counts['count'].sum()
    if total_awards == 0: # Avoid division by zero if there are no base awards
        vehicle_counts['percentage'] = 0.0
    else:
        vehicle_counts['percentage'] = (vehicle_counts['count'] / total_awards) * 100
    
    # Convert DataFrame to list of Pydantic models
    vehicles_list = [
        ContractVehicleSummary(
            contract_vehicle=row['award_type'], 
            award_count=int(row['count']),
            percentage=float(row['percentage'])
        )
        for index, row in vehicle_counts.iterrows()
    ]
    return vehicles_list

def get_recipient_award_counts(df) -> List[RecipientAwardCount]:
    """
    Get award counts by recipient (base awards only).
    
    Args:
        df: DataFrame containing award data
        
    Returns:
        List of RecipientAwardCount objects
    """
    if df.empty:
        return []
    
    # Filter for base awards only
    base_awards = df[df['modification_number'] == '0']
    
    # Count awards by recipient
    award_counts = base_awards.groupby('recipient_name').size().reset_index(name='award_count')
    
    # Convert DataFrame to list of Pydantic models
    recipients_list = [
        RecipientAwardCount(
            recipient_identifier=row['recipient_name'], 
            award_count=int(row['award_count'])
        )
        for index, row in award_counts.iterrows()
    ]
    return recipients_list

def get_recipient_obligations(df) -> List[RecipientObligation]:
    """
    Get total obligations by recipient (all awards including modifications).
    
    Args:
        df: DataFrame containing award data
        
    Returns:
        List of RecipientObligation objects
    """
    if df.empty:
        return []
    
    # Sum obligations by recipient (all records including modifications)
    obligations = df.groupby('recipient_name')['federal_action_obligation'].sum().reset_index()
    
    # Convert DataFrame to list of Pydantic models
    obligations_list = [
        RecipientObligation(
            recipient_identifier=row['recipient_name'], 
            total_obligation=float(row['federal_action_obligation'])
        )
        for index, row in obligations.iterrows()
    ]
    return obligations_list

def get_expiring_contracts_processor(df, months_ahead=24) -> List[ExpiringContract]:
    """
    Calculate the number of contracts expiring in the specified months ahead.
    
    Args:
        df: DataFrame containing award data
        months_ahead: Number of months ahead to check for expiring contracts
        
    Returns:
        List of ExpiringContract objects
    """
    if df.empty or 'action_date' not in df.columns:
        return []
    
    # Convert action_date to datetime if it isn't already
    df['action_date'] = pd.to_datetime(df['action_date'])
    
    # Get today's date dynamically
    today = datetime.now().date()
    
    # Calculate the end date (e.g., 24 months from today)
    end_date_for_filtering = today + timedelta(days=30.44 * months_ahead)  # Approximate days per month

    # Define the order of preference for end date columns
    date_column_priority = [
        'period_of_performance_current_end_date',
        'period_of_performance_potential_end_date',
        'ordering_period_end_date'
    ]

    # Create a copy of the base_awards DataFrame to avoid SettingWithCopyWarning
    base_awards = df[df['modification_number'].astype(str).str.strip().str.lower().str.match('|'.join(['^0+$', '^none$', '^$', '^original$', '^base$'])) == True].copy()

    # Determine the actual end date to use for each contract
    base_awards['actual_end_date'] = pd.NaT
    for col_name in date_column_priority:
        if col_name in base_awards.columns:
            # Convert column to datetime, coercing errors to NaT
            base_awards[col_name] = pd.to_datetime(base_awards[col_name], errors='coerce')
            # Fill NaT in 'actual_end_date' with values from the current priority column
            base_awards['actual_end_date'] = base_awards['actual_end_date'].fillna(base_awards[col_name])

    # Fallback: If 'actual_end_date' is still NaT, estimate it using 'action_date' + 1 year
    base_awards.loc[base_awards['actual_end_date'].isnull(), 'actual_end_date'] = base_awards['action_date'] + pd.DateOffset(years=1)
    
    # Ensure 'actual_end_date' is in datetime format after all operations
    base_awards['actual_end_date'] = pd.to_datetime(base_awards['actual_end_date'], errors='coerce')

    # Filter for contracts with end dates in the window
    future_expiring = base_awards[
        (base_awards['actual_end_date'].notna()) &
        (base_awards['actual_end_date'].dt.date <= end_date_for_filtering) & 
        (base_awards['actual_end_date'].dt.date > today)
    ].copy() # Use .copy() to avoid SettingWithCopyWarning
    
    if future_expiring.empty:
        return []

    # Add 'days_to_expiration' column
    # Ensure that subtraction is between date objects, not datetime and date
    future_expiring['days_to_expiration'] = (future_expiring['actual_end_date'] - pd.Timestamp(today)).dt.days

    expiring_contracts_list = []
    for index, row in future_expiring.iterrows():
        contract_key = row.get('contract_award_unique_key', f"MISSING_KEY_{index}") 
        recipient_name = row.get('recipient_name', 'N/A')
        potential_value = row.get('potential_total_value_of_award', 0.0) 
        try:
            potential_value = float(potential_value) if potential_value is not None else 0.0
        except ValueError:
            potential_value = 0.0

        # Get the date part of 'actual_end_date'
        current_end_date_val = row['actual_end_date']
        if pd.notna(current_end_date_val):
            current_end_date_to_store = current_end_date_val.date()
        else:
            # This case should ideally not be hit if filtering is correct
            # but as a safeguard, use today's date or skip the record
            continue # Or assign a default like today, though filtering should prevent this

        expiring_contracts_list.append(
            ExpiringContract(
                contract_award_unique_key=str(contract_key),
                recipient_name=str(recipient_name),
                period_of_performance_current_end_date=current_end_date_to_store,
                potential_total_value_of_award=potential_value,
                days_to_expiration=int(row['days_to_expiration'])
            )
        )
        
    return expiring_contracts_list

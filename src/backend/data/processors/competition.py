"""
This module contains functions for analyzing the competitive landscape from award data.
"""
import pandas as pd
import numpy as np
from typing import List, Optional
from src.backend.data.models.data_models import TreemapPathElement, CompetitorPerformance

def get_treemap_data(df: pd.DataFrame) -> List[TreemapPathElement]:
    """
    Prepare data specifically for the competitive landscape treemap,
    matching the structure required for px.treemap with a path.

    Args:
        df: DataFrame containing award data.

    Returns:
        List of TreemapPathElement objects.
    """
    if df.empty:
        return []

    # Create a deep copy to avoid modifying original
    filtered_df = df.copy()

    # Ensure modification_number is properly handled as a string and identify base awards
    filtered_df['modification_number'] = filtered_df['modification_number'].astype(str).str.strip()
    filtered_df['is_base'] = filtered_df['modification_number'] == '0'
    
    # Ensure 'federal_action_obligation' is numeric
    filtered_df['federal_action_obligation'] = pd.to_numeric(filtered_df['federal_action_obligation'], errors='coerce').fillna(0)

    # --- BEGIN: Calculate recipient-level market share and win rate ---
    if not filtered_df.empty:
        base_awards_df = filtered_df[filtered_df['is_base']]
        
        recipient_award_counts = base_awards_df.groupby('recipient_name').size().reset_index(name='recipient_base_awards')
        recipient_obligations = filtered_df.groupby('recipient_name')['federal_action_obligation'].sum().reset_index(name='recipient_total_obligations')
        
        recipient_metrics_df = pd.merge(recipient_award_counts, recipient_obligations, on='recipient_name', how='outer')
        recipient_metrics_df['recipient_base_awards'] = recipient_metrics_df['recipient_base_awards'].fillna(0).astype(int)
        recipient_metrics_df['recipient_total_obligations'] = recipient_metrics_df['recipient_total_obligations'].fillna(0)

        overall_total_obligations = filtered_df['federal_action_obligation'].sum()
        overall_total_base_awards = filtered_df['is_base'].sum() # Total base awards in the entire dataset

        if overall_total_obligations > 0:
            recipient_metrics_df['market_share'] = (recipient_metrics_df['recipient_total_obligations'] / overall_total_obligations) * 100
        else:
            recipient_metrics_df['market_share'] = 0.0
            
        if overall_total_base_awards > 0:
            recipient_metrics_df['win_rate'] = (recipient_metrics_df['recipient_base_awards'] / overall_total_base_awards) * 100
        else:
            recipient_metrics_df['win_rate'] = 0.0
        
        recipient_metrics_df['recipient_name'] = recipient_metrics_df['recipient_name'].astype(str)
        metrics_map = recipient_metrics_df.set_index('recipient_name')[['market_share', 'win_rate']].to_dict('index')
    else:
        metrics_map = {}
    # --- END: Calculate recipient-level market share and win rate ---

    recipients = filtered_df['recipient_name'].unique()
    result_data = []

    for recipient_obj in recipients: # recipient_obj can be non-string if column is mixed type
        recipient = str(recipient_obj) # Ensure string for consistency and lookup
        recipient_df = filtered_df[filtered_df['recipient_name'] == recipient_obj]
        
        current_recipient_metrics = metrics_map.get(recipient, {'market_share': 0.0, 'win_rate': 0.0})
        recipient_market_share = current_recipient_metrics['market_share']
        recipient_win_rate = current_recipient_metrics['win_rate']

        parent_name_series = recipient_df['recipient_parent_name']
        parent_name = parent_name_series.iloc[0] if not parent_name_series.empty and pd.notna(parent_name_series.iloc[0]) else recipient

        funding_sub_agencies = recipient_df['funding_sub_agency_name'].unique()

        for sub_agency in funding_sub_agencies:
            sub_agency_df = recipient_df[recipient_df['funding_sub_agency_name'] == sub_agency]
            base_count_for_scope = int(sub_agency_df['is_base'].sum()) # Sum of booleans converted to int
            total_obligations_for_scope = sub_agency_df['federal_action_obligation'].sum()

            if total_obligations_for_scope > 0:
                current_path_data = {
                    'recipient_parent_name': parent_name,
                    'recipient_name': recipient,
                    'funding_sub_agency_name': sub_agency if pd.notna(sub_agency) else 'Unknown',
                    'federal_action_obligation': 0.0, # Will be summed up
                    'award_count': 0 # Will be summed up
                }
                
                if 'transaction_description' in sub_agency_df.columns:
                    valid_desc_df = sub_agency_df[sub_agency_df['transaction_description'].notna()]
                    
                    if not valid_desc_df.empty:
                        sorted_contracts = valid_desc_df.sort_values('federal_action_obligation', ascending=False)
                        top_n = min(5, len(sorted_contracts)) # As per original logic for top N contracts
                        top_contracts = sorted_contracts.head(top_n)

                        for _, contract_row in top_contracts.iterrows():
                            description = str(contract_row['transaction_description'])
                            if not description or description.lower() in ['none', 'n/a', 'nan']:
                                description = f"Contract Mod #{contract_row['modification_number']}" # More specific than original
                            else:
                                description = description.strip().replace("\\n", " ").replace("\\r", " ")
                                description = (description[:97] + '...') if len(description) > 100 else description
                            
                            amount = contract_row['federal_action_obligation']
                            amount_str = f"${amount/1_000_000:.1f}M" if amount >= 1_000_000 else f"${amount/1_000:.1f}K" if amount >= 1_000 else f"${amount:.0f}"
                            
                            result_data.append({
                                **current_path_data,
                                'transaction_description': f"{amount_str}: {description}",
                                'federal_action_obligation': float(amount),
                                'award_count': 1 if contract_row['is_base'] else 0,
                                'market_share': recipient_market_share,
                                'win_rate': recipient_win_rate
                            })
                        
                        remaining_contracts = sorted_contracts.iloc[top_n:]
                        if not remaining_contracts.empty:
                            remaining_value = remaining_contracts['federal_action_obligation'].sum()
                            remaining_base_count = int(remaining_contracts['is_base'].sum())
                            if remaining_value > 0 or remaining_base_count > 0:
                                result_data.append({
                                    **current_path_data,
                                    'transaction_description': f"Other Contracts ({len(remaining_contracts)})",
                                    'federal_action_obligation': float(remaining_value),
                                    'award_count': remaining_base_count,
                                    'market_share': recipient_market_share,
                                    'win_rate': recipient_win_rate
                                })
                    else: # No valid descriptions
                        result_data.append({
                            **current_path_data,
                            'transaction_description': 'All Contracts',
                            'federal_action_obligation': float(total_obligations_for_scope),
                            'award_count': base_count_for_scope,
                            'market_share': recipient_market_share,
                            'win_rate': recipient_win_rate
                        })
                else: # No transaction_description column
                    result_data.append({
                        **current_path_data,
                        'transaction_description': 'All Contracts',
                        'federal_action_obligation': float(total_obligations_for_scope),
                        'award_count': base_count_for_scope,
                        'market_share': recipient_market_share,
                        'win_rate': recipient_win_rate
                    })

    if not result_data:
        return []

    treemap_df = pd.DataFrame(result_data)
    
    # Fill NA for key columns before calculations if any dicts had missing keys
    treemap_df['federal_action_obligation'] = treemap_df['federal_action_obligation'].fillna(0)
    treemap_df['award_count'] = treemap_df['award_count'].fillna(0).astype(int)
    # market_share and win_rate are already populated with recipient-level data
    treemap_df['market_share'] = treemap_df['market_share'].fillna(0.0).astype(float)
    treemap_df['win_rate'] = treemap_df['win_rate'].fillna(0.0).astype(float)

    # Ensure all required fields for TreemapPathElement are present and have correct types
    treemap_df['recipient_parent_name'] = treemap_df['recipient_parent_name'].astype(str).fillna('') # Path elements should be strings
    treemap_df['recipient_name'] = treemap_df['recipient_name'].astype(str)
    treemap_df['funding_sub_agency_name'] = treemap_df['funding_sub_agency_name'].astype(str).fillna('')
    treemap_df['transaction_description'] = treemap_df['transaction_description'].astype(str)


    treemap_elements = [
        TreemapPathElement(
            recipient_parent_name=row['recipient_parent_name'] if pd.notna(row['recipient_parent_name']) and row['recipient_parent_name'] else None,
            recipient_name=row['recipient_name'],
            funding_sub_agency_name=row['funding_sub_agency_name'] if pd.notna(row['funding_sub_agency_name']) and row['funding_sub_agency_name'] else None,
            transaction_description=row['transaction_description'],
            federal_action_obligation=float(row['federal_action_obligation']),
            award_count=int(row['award_count']),
            market_share=float(row['market_share']),
            win_rate=float(row['win_rate'])
        )
        for _, row in treemap_df.iterrows()
    ]
    return treemap_elements

def get_competitive_landscape(df: pd.DataFrame) -> List[CompetitorPerformance]:
    """
    Analyze competitive landscape among contractors.
    Calculates market share, win rate, and total obligations for each recipient.

    Args:
        df: DataFrame containing award data.

    Returns:
        List of CompetitorPerformance objects.
    """
    if df.empty:
        return []

    # Ensure 'modification_number' and 'federal_action_obligation' columns exist
    if 'modification_number' not in df.columns or 'federal_action_obligation' not in df.columns or 'recipient_name' not in df.columns:
        # Log or handle missing critical columns appropriately
        return []

    # Convert 'federal_action_obligation' to numeric, coercing errors and filling NaNs
    df['federal_action_obligation'] = pd.to_numeric(df['federal_action_obligation'], errors='coerce').fillna(0)
    
    # Identify base awards (modification_number == '0')
    # Ensure modification_number is string for accurate comparison
    df['modification_number'] = df['modification_number'].astype(str).str.strip()
    base_awards = df[df['modification_number'] == '0']

    # Count base awards by recipient
    award_counts = base_awards.groupby('recipient_name').size().reset_index(name='award_count')

    # Sum total obligations by recipient (using all records including modifications)
    obligations = df.groupby('recipient_name')['federal_action_obligation'].sum().reset_index(name='total_obligations')

    # Merge award counts and obligations
    # Use outer join to include all recipients, then fillna(0) for counts/obligations
    # for recipients who might only have modifications or only base awards (though less likely for obligations).
    competitors_df = pd.merge(award_counts, obligations, on='recipient_name', how='outer')
    
    # Fill NaN values that can result from the outer join if a recipient has obligations but no base awards, or vice-versa
    competitors_df['award_count'] = competitors_df['award_count'].fillna(0).astype(int)
    competitors_df['total_obligations'] = competitors_df['total_obligations'].fillna(0)


    # Calculate total market obligations and total market awards for share/rate calculations
    total_market_obligations = competitors_df['total_obligations'].sum()
    total_market_awards = competitors_df['award_count'].sum() # Sum of base awards across all competitors

    # Calculate market share
    if total_market_obligations > 0:
        competitors_df['market_share'] = (competitors_df['total_obligations'] / total_market_obligations) * 100
    else:
        competitors_df['market_share'] = 0.0

    # Calculate win rate (percentage of total base awards won by this recipient)
    if total_market_awards > 0:
        competitors_df['win_rate'] = (competitors_df['award_count'] / total_market_awards) * 100
    else:
        competitors_df['win_rate'] = 0.0 # Ensure win_rate column is created and set to 0.0
        
    # Sort by market_share in descending order (as in original script)
    competitors_df.sort_values('market_share', ascending=False, inplace=True)

    # Ensure dtypes are correct before creating Pydantic models
    competitors_df['market_share'] = competitors_df['market_share'].astype(float)
    competitors_df['win_rate'] = competitors_df['win_rate'].astype(float)
    competitors_df['total_obligations'] = competitors_df['total_obligations'].astype(float)
    competitors_df['recipient_name'] = competitors_df['recipient_name'].astype(str)


    # Convert DataFrame to list of Pydantic models
    landscape_data = []
    for _, row in competitors_df.iterrows():
        landscape_data.append(
            CompetitorPerformance(
                recipient_name=row['recipient_name'],
                market_share=row['market_share'],
                win_rate=row['win_rate'],
                federal_action_obligation=row['total_obligations'] # Renamed from 'total_obligations' in df to match model
            )
        )
    
    return landscape_data

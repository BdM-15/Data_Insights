"""
Competition analysis functions for Data Insights.
Move all competition-related data processing logic here for modularization.
"""

import pandas as pd
import numpy as np
from src.backend.data.models.data_models import TreemapPathElement, CompetitorPerformance

def get_treemap_data(df: pd.DataFrame) -> list:
    """
    Prepare data for the competitive landscape treemap.

    Args:
        df: DataFrame containing award data

    Returns:
        List of TreemapPathElement models
    """
    if df.empty:
        return []

    # Create a deep copy to avoid modifying original
    filtered_df = df.copy()

    # Ensure modification_number is properly handled as a string
    filtered_df['modification_number'] = filtered_df['modification_number'].astype(str).str.strip()
    filtered_df['is_base'] = filtered_df['modification_number'] == '0'

    # Get a list of all recipients for processing
    recipients = filtered_df['recipient_name'].unique()
    result_data = []

    # Process by recipient and funding sub-agency
    for recipient in recipients:
        recipient_df = filtered_df[filtered_df['recipient_name'] == recipient]

        # Get parent company name (use recipient name if parent is missing)
        parent_name = recipient_df['recipient_parent_name'].iloc[0] if 'recipient_parent_name' in recipient_df.columns and not pd.isna(recipient_df['recipient_parent_name'].iloc[0]) else recipient

        # Get the funding sub-agencies for this recipient
        funding_sub_agencies = recipient_df['funding_sub_agency_name'].unique()

        for sub_agency in funding_sub_agencies:
            sub_agency_df = recipient_df[recipient_df['funding_sub_agency_name'] == sub_agency]

            # Get base award count (exact '0' modification number)
            base_count = sub_agency_df['is_base'].sum()

            # Get total obligations for this recipient and sub-agency
            total_obligations = sub_agency_df['federal_action_obligation'].sum()

            # Only add rows with actual obligations
            if total_obligations > 0:
                # Process contract descriptions - identify significant contracts
                if 'transaction_description' in sub_agency_df.columns:
                    valid_desc_df = sub_agency_df[~sub_agency_df['transaction_description'].isna()]

                    if not valid_desc_df.empty:
                        # Sort contracts by obligation amount in descending order
                        sorted_contracts = valid_desc_df.sort_values('federal_action_obligation', ascending=False)

                        # Get top contracts (up to 5 largest or 20% of value)
                        top_n = min(5, len(sorted_contracts))
                        top_contracts = sorted_contracts.head(top_n)

                        # For each significant contract, create an entry with rich description
                        for _, contract in top_contracts.iterrows():
                            description = str(contract['transaction_description'])
                            if description == 'nan' or not description or description.lower() in ['none', 'n/a']:
                                description = f"Contract #{contract['modification_number']}"
                            else:
                                description = description.strip().replace('\n', ' ').replace('\r', '')
                                if len(description) > 100:
                                    description = description[:97] + '...'

                            # Format amount for better readability
                            amount = contract['federal_action_obligation']
                            amount_str = f"${amount/1_000_000:.1f}M" if amount >= 1_000_000 else f"${amount/1_000:.1f}K" if amount >= 1_000 else f"${amount:.0f}"

                            # Add to results with rich description
                            result_data.append({
                                'recipient_parent_name': parent_name,
                                'recipient_name': recipient,
                                'funding_sub_agency_name': sub_agency if not pd.isna(sub_agency) else 'Unknown',
                                'transaction_description': f"{amount_str}: {description}",
                                'federal_action_obligation': contract['federal_action_obligation'],
                                'award_count': 1 if contract['is_base'] else 0
                            })

                        # Add remaining as "Other Contracts"
                        remaining = sorted_contracts[~sorted_contracts.index.isin(top_contracts.index)]
                        if not remaining.empty:
                            remaining_value = remaining['federal_action_obligation'].sum()
                            remaining_count = len(remaining)

                            result_data.append({
                                'recipient_parent_name': parent_name,
                                'recipient_name': recipient,
                                'funding_sub_agency_name': sub_agency if not pd.isna(sub_agency) else 'Unknown',
                                'transaction_description': f"Other Contracts ({remaining_count})",
                                'federal_action_obligation': remaining_value,
                                'award_count': sum(remaining['is_base'])
                            })
                    else:
                        # No valid descriptions
                        result_data.append({
                            'recipient_parent_name': parent_name,
                            'recipient_name': recipient,
                            'funding_sub_agency_name': sub_agency if not pd.isna(sub_agency) else 'Unknown',
                            'transaction_description': 'All Contracts',
                            'federal_action_obligation': total_obligations,
                            'award_count': base_count
                        })
                else:
                    # No transaction_description column
                    result_data.append({
                        'recipient_parent_name': parent_name,
                        'recipient_name': recipient,
                        'funding_sub_agency_name': sub_agency if not pd.isna(sub_agency) else 'Unknown',
                        'transaction_description': 'All Contracts',
                        'federal_action_obligation': total_obligations,
                        'award_count': base_count
                    })

    # Convert to DataFrame
    treemap_data = pd.DataFrame(result_data)

    # Calculate market share
    total_obligations = treemap_data['federal_action_obligation'].sum()
    if total_obligations > 0:
        treemap_data['market_share'] = treemap_data['federal_action_obligation'] / total_obligations * 100
    else:
        treemap_data['market_share'] = 0

    # Calculate win rate
    total_awards = treemap_data['award_count'].sum()
    if total_awards > 0:
        treemap_data['win_rate'] = treemap_data['award_count'] / total_awards * 100
    else:
        treemap_data['win_rate'] = 0

    # Sort by market share
    treemap_data = treemap_data.sort_values('market_share', ascending=False)

    return [TreemapPathElement(**row) for row in treemap_data.to_dict(orient='records')]


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

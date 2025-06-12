#!/usr/bin/env python3
"""Test script to verify filter functionality."""

import sys
sys.path.insert(0, 'c:/GitHub/Data_Insights')

from src.frontend.pages.capture_profiles import get_unique_values

def test_filters():
    print('Testing base filter (parent_award_agency_name)...')
    try:
        agencies = get_unique_values('parent_award_agency_name')
        print(f'Found {len(agencies)} agencies')
        print(f'First 5: {agencies[:5]}')
    except Exception as e:
        print(f'Error in base filter: {e}')

    print('\nTesting hierarchical filter...')
    try:
        sub_agencies = get_unique_values('funding_sub_agency_name', 
                                       filter_conditions=[{
                                           'child_column': 'funding_sub_agency_name', 
                                           'value': 'DEPT OF DEFENSE'
                                       }])
        print(f'Found {len(sub_agencies)} sub-agencies for DEPT OF DEFENSE')
        print(f'First 5: {sub_agencies[:5]}')
    except Exception as e:
        print(f'Error in hierarchical filter: {e}')

    print('✅ Filter test completed!')

if __name__ == '__main__':
    test_filters()

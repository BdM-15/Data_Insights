#!/usr/bin/env python3
"""
Test script to verify the optimized treemap function performance.
"""

import time
import sys
import os
sys.path.append(os.path.abspath('.'))

from src.backend.data.app_processors.competition import get_treemap_data

def test_optimized_treemap_function():
    """Test the optimized treemap function with different limits."""
    
    print("=== Testing Optimized Treemap Function ===")
    
    # Test with different limit values
    limits_to_test = [10, 50, 100]
    
    for limit in limits_to_test:
        print(f"\nTesting with limit={limit}...")
        start_time = time.time()
        
        # Call the optimized function
        treemap_data = get_treemap_data(limit=limit)
        
        end_time = time.time()
        
        print(f"  Execution time: {end_time - start_time:.2f} seconds")
        print(f"  Returned {len(treemap_data)} rows")
        
        if treemap_data:
            # Show top 3 results
            print("  Top 3 results:")
            for i, item in enumerate(treemap_data[:3]):
                print(f"    {i+1}. {item.recipient_parent_name} | ${item.federal_action_obligation:,.2f}")
    
    # Test with filters
    print(f"\nTesting with NAICS filter (336411 - Aircraft Manufacturing)...")
    start_time = time.time()
    
    treemap_data = get_treemap_data(naics_code="336411", limit=10)
    
    end_time = time.time()
    
    print(f"  Execution time: {end_time - start_time:.2f} seconds")
    print(f"  Returned {len(treemap_data)} rows")
    
    if treemap_data:
        print("  Top 3 aircraft manufacturers:")
        for i, item in enumerate(treemap_data[:3]):
            print(f"    {i+1}. {item.recipient_parent_name} | ${item.federal_action_obligation:,.2f}")

if __name__ == "__main__":
    test_optimized_treemap_function()

#!/usr/bin/env python3
"""
Test script for the new materialized views and performance indexes.
"""

import sys
import os
sys.path.append('src')

from backend.data.data_processing.transformation import create_materialized_views, create_performance_indexes

def test_optimizations():
    """Test the optimization implementations."""
    print('Testing database connection and optimization functions...')
    
    try:
        print('Creating materialized views...')
        create_materialized_views()
        print('✓ Materialized views created/updated')
        
        print('Creating performance indexes...')
        create_performance_indexes()
        print('✓ Performance indexes created/updated')
        
        print('All optimizations applied successfully!')
        return True
        
    except Exception as e:
        print(f'Error: {e}')
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_optimizations()
    sys.exit(0 if success else 1)

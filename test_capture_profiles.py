#!/usr/bin/env python3
"""
Test script for capture profiles functionality
"""

import sys
import os
sys.path.insert(0, os.path.abspath('.'))

def test_imports():
    """Test that all necessary modules can be imported"""
    try:
        from src.frontend.pages.capture_profiles import search_contracts, get_unique_values, get_naics_options
        from config import get_db_config
        from src.backend.core.database import get_db_engine
        print("✅ All imports successful")
        return True
    except Exception as e:
        print(f"❌ Import error: {e}")
        return False

def test_database_connection():
    """Test database connectivity"""
    try:
        from src.backend.core.database import get_db_engine
        from sqlalchemy import text
        engine = get_db_engine()
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1 as test"))
            print("✅ Database connection successful")
            return True
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        return False

def test_filter_tables():
    """Test that filter tables exist"""
    try:
        from src.backend.core.database import get_db_engine
        from sqlalchemy import text
        engine = get_db_engine()
        
        filter_tables = [
            'filter_values_parent_award_agency_name',
            'filter_values_funding_sub_agency_name', 
            'filter_values_funding_office_name',
            'filter_values_naics_code',
            'filter_values_recipient_name',
            'filter_values_extent_competed',
            'filter_values_product_or_service_code',
            'filter_values_type_of_contract_pricing',
            'filter_values_type_of_set_aside',
            'filter_values_funding_agency_name',
            'filter_values_recipient_parent_name',
            'filter_values_award_id_piid',
            'filter_values_parent_award_id_piid'
        ]
        
        with engine.connect() as conn:
            for table in filter_tables:
                result = conn.execute(text(f"SELECT COUNT(*) as count FROM {table}"))
                count = result.fetchone()[0]
                print(f"✅ {table}: {count:,} records")
        
        return True
    except Exception as e:
        print(f"❌ Filter table test error: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing Capture Profiles Functionality")
    print("=" * 50)
    
    success = True
    success &= test_imports()
    success &= test_database_connection() 
    success &= test_filter_tables()
    
    print("=" * 50)
    if success:
        print("🎉 All tests passed! Capture profiles functionality is ready.")
    else:
        print("❌ Some tests failed. Please check the errors above.")

#!/usr/bin/env python3
"""
Performance verification script to test the optimizations.
"""
import psycopg2
import os
import time
from dotenv import load_dotenv

load_dotenv()

def time_query(cursor, query_name, query):
    """Execute a query and return the execution time."""
    print(f"Testing {query_name}...")
    start_time = time.time()
    cursor.execute(query)
    results = cursor.fetchall()
    end_time = time.time()
    execution_time = end_time - start_time
    row_count = len(results)
    print(f"  ✅ {execution_time:.3f}s - {row_count:,} rows")
    return execution_time, row_count

def main():
    conn = psycopg2.connect(
        host=os.getenv('PG_HOST'),
        port=os.getenv('PG_PORT'),
        database=os.getenv('PG_DBNAME'),
        user=os.getenv('PG_USER'),
        password=os.getenv('PG_PASSWORD')
    )
    
    cursor = conn.cursor()
    
    print("🚀 PERFORMANCE VERIFICATION TESTS")
    print("=" * 50)
    
    # Test 1: Dashboard Summary Data (should be <1 second with materialized views)
    print("\n📊 DASHBOARD SUMMARY QUERIES:")
    
    time_query(cursor, "Top Agencies (Materialized)", 
               "SELECT * FROM s3_processed.mv_top_agencies LIMIT 10")
    
    time_query(cursor, "Award Summary Metrics (Materialized)", 
               "SELECT * FROM s3_processed.mv_award_summary_metrics LIMIT 1")
    
    time_query(cursor, "Quarterly Trends (Materialized)", 
               "SELECT * FROM s3_processed.mv_quarterly_trends_optimized LIMIT 20")
    
    # Test 2: Complex Analytics (should be very fast with materialized views)
    print("\n🎯 COMPLEX ANALYTICS QUERIES:")
    
    time_query(cursor, "Competitive Landscape Treemap (Materialized)", 
               "SELECT * FROM s3_processed.mv_treemap_competitive_landscape LIMIT 50")
    
    time_query(cursor, "Agency Analysis (Materialized)", 
               "SELECT * FROM s3_processed.mv_agency_analysis_summary LIMIT 20")
    
    time_query(cursor, "Contract Vehicle Analysis (Materialized)", 
               "SELECT * FROM s3_processed.mv_contract_vehicle_analysis LIMIT 10")
    
    # Test 3: Filter Operations (should be instant)
    print("\n🔍 FILTER OPERATIONS:")
    
    time_query(cursor, "Agency Filter Values", 
               "SELECT * FROM s3_processed.filter_values_parent_award_agency_name LIMIT 50")
    
    time_query(cursor, "Contractor Filter Values", 
               "SELECT * FROM s3_processed.filter_values_recipient_name LIMIT 50")
    
    time_query(cursor, "NAICS Filter Values", 
               "SELECT * FROM s3_processed.filter_values_naics_code LIMIT 50")
    
    # Test 4: Financial Analysis with Deobligations
    print("\n💰 FINANCIAL ANALYSIS:")
    
    time_query(cursor, "Contract Net Obligations (Materialized)", 
               "SELECT * FROM s3_processed.mv_contract_net_obligations WHERE contract_status = 'ACTIVE_POSITIVE' LIMIT 20")
    
    time_query(cursor, "Agency Net Obligations (Materialized)", 
               "SELECT * FROM s3_processed.mv_agency_net_obligations LIMIT 10")
    
    # Test 5: Raw Table Performance (should be fast with indexes)
    print("\n⚡ INDEXED RAW TABLE QUERIES:")
    
    time_query(cursor, "Recent Contracts (Date Index)", 
               "SELECT contract_award_unique_key, action_date, recipient_name, federal_action_obligation FROM s3_processed.usaspending_prime_awards WHERE action_date >= '2024-01-01' LIMIT 100")
    
    time_query(cursor, "Large Contracts (Obligation Index)", 
               "SELECT contract_award_unique_key, recipient_name, federal_action_obligation FROM s3_processed.usaspending_prime_awards WHERE federal_action_obligation > 1000000 ORDER BY federal_action_obligation DESC LIMIT 50")
    
    print("\n" + "=" * 50)
    print("🎉 PERFORMANCE VERIFICATION COMPLETE!")
    print("\nExpected performance targets:")
    print("  • Dashboard queries: <1 second")
    print("  • Filter operations: <0.1 seconds") 
    print("  • Complex analytics: <2 seconds")
    print("  • Raw table queries: <3 seconds")
    
    cursor.close()
    conn.close()

if __name__ == "__main__":
    main()

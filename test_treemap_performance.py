#!/usr/bin/env python3
"""
Test script to analyze treemap query performance and optimize it.
"""

import time
import sys
import os
sys.path.append(os.path.abspath('.'))

from sqlalchemy import text
from src.backend.core.database import get_db_engine

def test_current_query_performance():
    """Test the current treemap query performance."""
    engine = get_db_engine()
    
    # Current query from the competition.py file
    query = """
        SELECT
            recipient_parent_name,
            recipient_name,
            funding_sub_agency_name,
            -- Use mode() to get the most frequent transaction description, fallback to any description
            COALESCE(
                MODE() WITHIN GROUP (ORDER BY transaction_description) 
                FILTER (WHERE transaction_description IS NOT NULL AND transaction_description != ''),
                'All Contracts'
            ) AS transaction_description,
            SUM(federal_action_obligation) AS federal_action_obligation,
            COUNT(*) FILTER (WHERE modification_number = '0') AS award_count
        FROM s3_processed.usaspending_prime_awards
        GROUP BY recipient_parent_name, recipient_name, funding_sub_agency_name
        ORDER BY SUM(federal_action_obligation) DESC
    """
    
    with engine.connect() as connection:
        print("Testing current treemap query performance...")
        start_time = time.time()
        result = connection.execute(text(query)).fetchall()
        end_time = time.time()
        
        print(f"Query executed in {end_time - start_time:.2f} seconds")
        print(f"Returned {len(result)} rows")
        
        # Show top 5 results
        print("\nTop 5 results:")
        for i, row in enumerate(result[:5]):
            print(f"{i+1}. {row[0]} | {row[1]} | {row[2]} | ${row[4]:,.2f}")

def test_optimized_query_performance():
    """Test an optimized version of the treemap query."""
    engine = get_db_engine()
    
    # Optimized query - avoid MODE() function which can be expensive
    query = """
        SELECT
            recipient_parent_name,
            recipient_name,
            funding_sub_agency_name,
            -- Use MAX instead of MODE for better performance - gets any transaction description
            MAX(CASE WHEN transaction_description IS NOT NULL AND transaction_description != '' 
                     THEN transaction_description 
                     ELSE 'All Contracts' END) AS transaction_description,
            SUM(federal_action_obligation) AS federal_action_obligation,
            COUNT(*) FILTER (WHERE modification_number = '0') AS award_count
        FROM s3_processed.usaspending_prime_awards
        GROUP BY recipient_parent_name, recipient_name, funding_sub_agency_name
        ORDER BY SUM(federal_action_obligation) DESC
    """
    
    with engine.connect() as connection:
        print("\nTesting optimized treemap query performance...")
        start_time = time.time()
        result = connection.execute(text(query)).fetchall()
        end_time = time.time()
        
        print(f"Query executed in {end_time - start_time:.2f} seconds")
        print(f"Returned {len(result)} rows")
        
        # Show top 5 results
        print("\nTop 5 results:")
        for i, row in enumerate(result[:5]):
            print(f"{i+1}. {row[0]} | {row[1]} | {row[2]} | ${row[4]:,.2f}")

def create_treemap_indexes():
    """Create specific indexes for treemap query optimization."""
    engine = get_db_engine()
    
    indexes = [
        {
            "name": "s3p_idx_treemap_grouping",
            "columns": "recipient_parent_name, recipient_name, funding_sub_agency_name"
        },
        {
            "name": "s3p_idx_treemap_obligation", 
            "columns": "federal_action_obligation"
        },
        {
            "name": "s3p_idx_treemap_modification",
            "columns": "modification_number"
        },
        {
            "name": "s3p_idx_funding_sub_agency",
            "columns": "funding_sub_agency_name"
        }
    ]
    
    with engine.connect() as connection:
        with connection.begin():
            print("Creating treemap-specific indexes...")
            
            for idx in indexes:
                try:
                    # Check if index exists
                    exists = connection.execute(text(f"""
                        SELECT 1 FROM pg_indexes 
                        WHERE schemaname = 's3_processed' 
                        AND indexname = '{idx['name']}'
                    """)).fetchone()
                    
                    if exists:
                        print(f"Index {idx['name']} already exists, skipping...")
                        continue
                    
                    print(f"Creating index {idx['name']} on ({idx['columns']})...")
                    start_time = time.time()
                    connection.execute(text(f"""
                        CREATE INDEX {idx['name']} 
                        ON s3_processed.usaspending_prime_awards ({idx['columns']})
                    """))
                    end_time = time.time()
                    print(f"  [OK] Created in {end_time - start_time:.2f} seconds")
                    
                except Exception as e:
                    print(f"  [ERROR] Failed to create index {idx['name']}: {e}")

def get_table_stats():
    """Get basic statistics about the table."""
    engine = get_db_engine()
    
    with engine.connect() as connection:
        # Get row count
        row_count = connection.execute(text("""
            SELECT COUNT(*) FROM s3_processed.usaspending_prime_awards
        """)).scalar()
        
        # Get distinct values for key grouping columns
        distinct_stats = connection.execute(text("""
            SELECT 
                COUNT(DISTINCT recipient_parent_name) as distinct_parent_names,
                COUNT(DISTINCT recipient_name) as distinct_recipient_names,
                COUNT(DISTINCT funding_sub_agency_name) as distinct_agencies,
                COUNT(DISTINCT CONCAT(recipient_parent_name, '|', recipient_name, '|', funding_sub_agency_name)) as distinct_groups
            FROM s3_processed.usaspending_prime_awards
        """)).fetchone()
        
        print(f"\nTable Statistics:")
        print(f"Total rows: {row_count:,}")
        print(f"Distinct parent names: {distinct_stats[0]:,}")
        print(f"Distinct recipient names: {distinct_stats[1]:,}")
        print(f"Distinct funding agencies: {distinct_stats[2]:,}")
        print(f"Distinct grouping combinations: {distinct_stats[3]:,}")

if __name__ == "__main__":
    print("=== Treemap Query Performance Analysis ===")
    
    # Get basic table stats
    get_table_stats()
    
    # Test current query
    test_current_query_performance()
    
    # Test optimized query 
    test_optimized_query_performance()
    
    # Create indexes
    print("\n" + "="*50)
    create_treemap_indexes()
    
    # Test again after indexing
    print("\n" + "="*50)
    print("Testing performance after indexing...")
    test_optimized_query_performance()

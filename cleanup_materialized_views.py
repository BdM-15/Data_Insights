#!/usr/bin/env python3
"""
Clean up materialized views with CASCADE to resolve dependencies.
"""
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

conn = psycopg2.connect(
    host=os.getenv('PG_HOST'),
    port=os.getenv('PG_PORT'),
    database=os.getenv('PG_DBNAME'),
    user=os.getenv('PG_USER'),
    password=os.getenv('PG_PASSWORD')
)

cursor = conn.cursor()

# Drop all materialized views in the correct dependency order with CASCADE
materialized_views = [
    'mv_agency_net_obligations',  # Drop dependent views first
    'mv_contract_net_obligations',
    'mv_top_competitors_market_share',
    'mv_treemap_competitive_landscape', 
    'mv_quarterly_trends_analysis',
    'mv_agency_analysis_summary',
    'mv_contract_vehicle_analysis',
    'mv_award_summary_metrics',
    'mv_top_agencies',
    'mv_quarterly_trends_optimized',
    'mv_agency_obligation_ratio',
    'mv_expiring_contracts_optimized'
]

print("Dropping all materialized views with CASCADE...")
for view in materialized_views:
    try:
        cursor.execute(f'DROP MATERIALIZED VIEW IF EXISTS s3_processed.{view} CASCADE')
        print(f'Dropped s3_processed.{view}')
    except Exception as e:
        print(f'Error dropping {view}: {e}')

conn.commit()
cursor.close()
conn.close()
print('Materialized view cleanup complete!')

#!/usr/bin/env python3
"""
Clean up old lookup tables.
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

# Drop all old lookup tables
lookup_tables = [
    'lookup_awarding_sub_agency_name',
    'lookup_extent_competed', 
    'lookup_naics_code',
    'lookup_parent_award_agency_name',
    'lookup_product_or_service_code',
    'lookup_recipient_name',
    'lookup_type_of_contract_pricing'
]

for table in lookup_tables:
    try:
        cursor.execute(f'DROP TABLE IF EXISTS s3_processed.{table}')
        print(f'Dropped s3_processed.{table}')
    except Exception as e:
        print(f'Error dropping {table}: {e}')

conn.commit()
cursor.close()
conn.close()
print('Cleanup complete!')

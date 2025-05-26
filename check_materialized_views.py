#!/usr/bin/env python3
"""
Check materialized views specifically.
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

# Check for materialized views
print('Materialized views in s3_processed schema:')
cursor.execute("""
    SELECT matviewname 
    FROM pg_matviews 
    WHERE schemaname = 's3_processed'
    ORDER BY matviewname
""")

mvs = cursor.fetchall()
for (mv,) in mvs:
    print(f'  s3_processed.{mv}')

if not mvs:
    print('  No materialized views found')

# Check for any mv_ tables that might be regular tables
print('\nTables with mv_ prefix:')
cursor.execute("""
    SELECT tablename 
    FROM pg_tables 
    WHERE schemaname = 's3_processed' AND tablename LIKE 'mv_%'
    ORDER BY tablename
""")

mv_tables = cursor.fetchall()
for (table,) in mv_tables:
    print(f'  s3_processed.{table}')

if not mv_tables:
    print('  No tables with mv_ prefix found')

cursor.close()
conn.close()

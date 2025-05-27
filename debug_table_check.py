#!/usr/bin/env python3
"""
Quick script to check for problematic table references.
"""
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

# Connect to database
conn = psycopg2.connect(
    host=os.getenv('PG_HOST'),
    port=os.getenv('PG_PORT'),
    database=os.getenv('PG_DBNAME'),
    user=os.getenv('PG_USER'),
    password=os.getenv('PG_PASSWORD')
)

cursor = conn.cursor()

# Check if the problematic table exists
cursor.execute("""
    SELECT schemaname, tablename 
    FROM pg_tables 
    WHERE tablename LIKE '%lookup%' OR tablename LIKE '%awarding%'
    ORDER BY schemaname, tablename
""")

tables = cursor.fetchall()
print('Tables with lookup or awarding in name:')
for schema, table in tables:
    print(f'  {schema}.{table}')

if not tables:
    print('  No tables found with lookup or awarding in name')

# Also check all s3_processed tables
print('\nAll s3_processed tables:')
cursor.execute("""
    SELECT tablename 
    FROM pg_tables 
    WHERE schemaname = 's3_processed'
    ORDER BY tablename
""")

s3_tables = cursor.fetchall()
for (table,) in s3_tables:
    print(f'  s3_processed.{table}')

cursor.close()
conn.close()

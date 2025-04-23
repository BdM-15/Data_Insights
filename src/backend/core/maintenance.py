"""
PostgreSQL Database Maintenance Script

This script provides maintenance functions for the PostgreSQL database:
1. Remove duplicates from the usaprime_cleaned table
2. Verify existing indexes
3. Analyze tables for query optimization
"""

import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# PostgreSQL connection settings
pg_user = os.getenv('PG_USER')
pg_password = os.getenv('PG_PASSWORD')
pg_host = os.getenv('PG_HOST')
pg_port = os.getenv('PG_PORT')
pg_dbname = os.getenv('PG_DBNAME')
pg_schema = os.getenv('PG_SCHEMA', 'public')

# Create PostgreSQL engine
db_url = f"postgresql://{pg_user}:{pg_password}@{pg_host}:{pg_port}/{pg_dbname}"
engine = create_engine(db_url)

# Step 1: Remove Duplicates
def remove_duplicates():
    print(f"Removing duplicates from {pg_schema}.usaprime_cleaned table...")
    with engine.connect() as connection:
        # Create a temporary table with deduplicated data
        connection.execute(text(f"""
            CREATE TABLE {pg_schema}.usaprime_cleaned_deduplicated AS
            SELECT DISTINCT ON (award_id_piid, modification_number, action_date, federal_action_obligation, recipient_name) *
            FROM {pg_schema}.usaprime_cleaned
            ORDER BY award_id_piid, modification_number, action_date, federal_action_obligation, recipient_name, action_date DESC;
        """))
        
        # Get counts for reporting
        orig_count = connection.execute(text(f"SELECT COUNT(*) FROM {pg_schema}.usaprime_cleaned")).scalar()
        new_count = connection.execute(text(f"SELECT COUNT(*) FROM {pg_schema}.usaprime_cleaned_deduplicated")).scalar()
        duplicates_removed = orig_count - new_count
        
        # Replace the original table with the deduplicated one
        connection.execute(text(f"DROP TABLE {pg_schema}.usaprime_cleaned"))
        connection.execute(text(f"ALTER TABLE {pg_schema}.usaprime_cleaned_deduplicated RENAME TO usaprime_cleaned"))
        
        print(f"Duplicates removed: {duplicates_removed:,} rows ({duplicates_removed/orig_count*100:.2f}% of original data)")

# Step 2: Verify Existing Indexes
def verify_indexes():
    print(f"Verifying indexes on {pg_schema}.usaprime_cleaned table...")
    with engine.connect() as connection:
        result = connection.execute(text(f"""
            SELECT indexname, indexdef 
            FROM pg_indexes 
            WHERE schemaname = '{pg_schema}' AND tablename = 'usaprime_cleaned'
        """)).fetchall()
        
        if result:
            print(f"Found {len(result)} indexes:")
            for row in result:
                print(f"  - {row[0]}: {row[1]}")
        else:
            print("No indexes found. Consider running the transformation script to create them.")
            
# Step 3: Analyze Tables for Query Optimization
def analyze_tables():
    print("Analyzing tables for query optimization...")
    with engine.connect() as connection:
        connection.execute(text(f"ANALYZE {pg_schema}.usaprime_cleaned"))
        connection.execute(text(f"ANALYZE {pg_schema}.filter_dependencies"))
        
        # Also analyze any filter_values_* tables
        filter_tables = connection.execute(text(f"""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = '{pg_schema}' AND table_name LIKE 'filter_values_%'
        """)).fetchall()
        
        for table in filter_tables:
            connection.execute(text(f"ANALYZE {pg_schema}.{table[0]}"))
            
    print("Tables analyzed successfully.")

# Execute all steps
if __name__ == "__main__":
    print("=== PostgreSQL Database Maintenance ===")
    remove_duplicates()
    verify_indexes()
    analyze_tables()
    print("Maintenance completed successfully.")

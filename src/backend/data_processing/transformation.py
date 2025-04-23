# Data Preprocessing for App Performance - High Performance Edition
# This script handles preprocessing steps to optimize application performance:
# - Creating filter values tables
# - Precomputing dependent filter relationships
# - Pre-aggregating data for visualizations
# - Creating database indexes for query performance
#
# Optimized using direct SQL transformations for maximum performance

import pandas as pd
from sqlalchemy import create_engine, text
import time
import os
from dotenv import load_dotenv
import psycopg2
import psycopg2.extras
import concurrent.futures
import sys

# Load environment variables from .env file
load_dotenv()

# Get PostgreSQL connection details from environment variables
pg_user = os.getenv('PG_USER')
pg_password = os.getenv('PG_PASSWORD')
pg_host = os.getenv('PG_HOST')
pg_port = os.getenv('PG_PORT')
pg_dbname = os.getenv('PG_DBNAME')
schema_name = 'public'  # Explicitly set the schema name

# Connect to PostgreSQL database
db_url = f"postgresql://{pg_user}:{pg_password}@{pg_host}:{pg_port}/{pg_dbname}"
engine = create_engine(db_url)

def create_filter_values_table(connection, column):
    """Create a filter values table for a specific column using direct SQL"""
    print(f"  - Creating filter values for {column}...")
    table_name = f"{schema_name}.filter_values_{column}"
    
    # Use a single SQL statement to create the table with unique values
    query = f"""
    DROP TABLE IF EXISTS {table_name};
    
    CREATE TABLE {table_name} AS
    SELECT DISTINCT {column} AS value
    FROM {schema_name}.usaprime_cleaned
    WHERE {column} IS NOT NULL
    ORDER BY value;
    """
    
    connection.execute(text(query))
    connection.commit()  # Explicitly commit the transaction
    return f"Created filter values table for {column}"

def create_single_index(connection, column, table="usaprime_cleaned", index_type=None):
    """Create an index on a specific column"""
    index_name = f"idx_{column}"
    full_table_name = f"{schema_name}.{table}"
    
    if index_type:
        query = f"""
        CREATE INDEX IF NOT EXISTS {index_name}
        ON {full_table_name} USING {index_type} ({column});
        """
    else:
        query = f"""
        CREATE INDEX IF NOT EXISTS {index_name}
        ON {full_table_name} ({column});
        """
    
    connection.execute(text(query))
    connection.commit()  # Explicitly commit the transaction
    return f"Created index on {column}"

def verify_table_exists(connection, table_name):
    """Verify if a table exists in the database"""
    query = text(f"""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = '{schema_name}'
            AND table_name = '{table_name}'
        )
    """)
    return connection.execute(query).scalar()

def preprocess_data_optimized():
    """
    Optimized main function to preprocess data for app performance using direct SQL:
    1. Precompute filter values for dropdowns
    2. Precompute dependent filter relationships for cascading filters
    3. Pre-aggregate quarterly data for visualizations
    4. Create database indexes for performance
    """
    total_start_time = time.time()
    print("Starting optimized data preprocessing for app performance...")
    
    # Step 1: Verify the required table exists
    try:
        with engine.connect() as connection:
            connection.execution_options(isolation_level="AUTOCOMMIT")
            
            # Check if table exists
            table_check_query = text(f"""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = '{schema_name}'
                    AND table_name = 'usaprime_cleaned'
                )
            """)
            table_exists = connection.execute(table_check_query).scalar()
            
            if not table_exists:
                raise Exception("The usaprime_cleaned table does not exist. Please run data_cleansing.py first.")
            
            # Get row count to estimate processing time
            count_query = text(f"SELECT COUNT(*) FROM {schema_name}.usaprime_cleaned")
            row_count = connection.execute(count_query).scalar()
            print(f"Found usaprime_cleaned table with {row_count:,} rows.")
            
    except Exception as e:
        print(f"Error verifying source table: {str(e)}")
        raise
    
    # Step 2: Precompute filter values for dropdown menus using direct SQL
    print("\nPrecomputing filter values tables using direct SQL...")
    filter_start_time = time.time()
    
    filter_columns = [
        "parent_award_agency_name", "funding_sub_agency_name", "funding_office_name",
        "recipient_name", "naics_code", "product_or_service_code", "type_of_contract_pricing",
        "extent_competed", "type_of_set_aside"
    ]
    
    try:
        # Direct psycopg2 connection for better transaction control
        conn = psycopg2.connect(
            dbname=pg_dbname,
            user=pg_user,
            password=pg_password,
            host=pg_host,
            port=pg_port
        )
        conn.autocommit = True  # Enable autocommit mode
        
        with conn.cursor() as cursor:
            # Set PostgreSQL parameters for performance
            cursor.execute("SET work_mem = '256MB'")
            cursor.execute("SET maintenance_work_mem = '512MB'")
            
            # Process each filter column serially to avoid transaction conflicts
            for column in filter_columns:
                print(f"  - Creating filter values for {column}...")
                table_name = f"filter_values_{column}"
                
                # Use a single SQL statement to create the table with unique values
                query = f"""
                DROP TABLE IF EXISTS {schema_name}.{table_name};
                
                CREATE TABLE {schema_name}.{table_name} AS
                SELECT DISTINCT {column} AS value
                FROM {schema_name}.usaprime_cleaned
                WHERE {column} IS NOT NULL
                ORDER BY value;
                """
                
                cursor.execute(query)
                print(f"    ✓ Created filter values table for {column}")
            
            # Verify tables were created
            cursor.execute(f"""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = '{schema_name}'
                AND table_name LIKE 'filter_values_%'
            """)
            
            created_tables = cursor.fetchall()
            print(f"Successfully created {len(created_tables)} filter value tables:")
            for table in created_tables:
                print(f"    - {table[0]}")
            
            filter_end_time = time.time()
            print(f"Filter values tables created in {filter_end_time - filter_start_time:.2f} seconds.")
            
    except Exception as e:
        print(f"Error creating filter value tables: {str(e)}")
        raise
    finally:
        conn.close()
    
    # Step 3: Precompute dependent filter relationships using direct SQL
    print("\nPrecomputing dependent filter relationships using direct SQL...")
    try:
        # Create a new connection for this step
        conn = psycopg2.connect(
            dbname=pg_dbname,
            user=pg_user,
            password=pg_password,
            host=pg_host,
            port=pg_port
        )
        conn.autocommit = True
        
        with conn.cursor() as cursor:
            # Drop existing table if it exists
            cursor.execute(f"DROP TABLE IF EXISTS {schema_name}.filter_dependencies")
            
            # Create the filter_dependencies table structure
            cursor.execute(f"""
                CREATE TABLE {schema_name}.filter_dependencies (
                    parent_value TEXT,
                    child_values JSONB,
                    child_column TEXT
                )
            """)
            
            # Parent agency to sub-agency
            print("  - Creating agency to sub-agency dependencies...")
            cursor.execute(f"""
                INSERT INTO {schema_name}.filter_dependencies (parent_value, child_values, child_column)
                SELECT 
                    parent_award_agency_name as parent_value,
                    jsonb_agg(DISTINCT funding_sub_agency_name) as child_values,
                    'funding_sub_agency_name' as child_column
                FROM {schema_name}.usaprime_cleaned
                WHERE 
                    parent_award_agency_name IS NOT NULL 
                    AND funding_sub_agency_name IS NOT NULL
                GROUP BY parent_award_agency_name
            """)
            
            # Sub-agency to funding office
            print("  - Creating sub-agency to funding office dependencies...")
            cursor.execute(f"""
                INSERT INTO {schema_name}.filter_dependencies (parent_value, child_values, child_column)
                SELECT 
                    funding_sub_agency_name as parent_value,
                    jsonb_agg(DISTINCT funding_office_name) as child_values,
                    'funding_office_name' as child_column
                FROM {schema_name}.usaprime_cleaned
                WHERE 
                    funding_sub_agency_name IS NOT NULL 
                    AND funding_office_name IS NOT NULL
                GROUP BY funding_sub_agency_name
            """)
            
            # Create an index on the parent_value column for faster lookups
            cursor.execute(f"""
                CREATE INDEX idx_filter_dependencies_parent 
                ON {schema_name}.filter_dependencies (parent_value)
            """)
            
            # Count the rows to verify
            cursor.execute(f"SELECT COUNT(*) FROM {schema_name}.filter_dependencies")
            dependency_count = cursor.fetchone()[0]
            print(f"  ✓ Created filter_dependencies table with {dependency_count} relationships.")
            
            # Verify table was created
            cursor.execute(f"""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = '{schema_name}'
                    AND table_name = 'filter_dependencies'
                )
            """)
            if cursor.fetchone()[0]:
                print("    ✓ Confirmed filter_dependencies table exists in database")
            else:
                print("    ⚠ Warning: filter_dependencies table creation could not be confirmed")
            
    except Exception as e:
        print(f"Error creating filter_dependencies table: {str(e)}")
        raise
    finally:
        conn.close()
    
    # Step 4: Pre-aggregate quarterly data using direct SQL
    print("\nPre-aggregating data for visualizations using direct SQL...")
    try:
        # Create a new connection for this step
        conn = psycopg2.connect(
            dbname=pg_dbname,
            user=pg_user,
            password=pg_password,
            host=pg_host,
            port=pg_port
        )
        conn.autocommit = True
        
        with conn.cursor() as cursor:
            # Drop existing table if it exists
            cursor.execute(f"DROP TABLE IF EXISTS {schema_name}.quarterly_data")
            
            # Create quarterly_data table with direct SQL transformation
            print("  - Creating quarterly_data table with fiscal calculations...")
            cursor.execute(f"""
                CREATE TABLE {schema_name}.quarterly_data AS
                WITH fiscal_data AS (
                    SELECT
                        action_date,
                        federal_action_obligation,
                        modification_number,
                        -- Calculate fiscal year based on month (Oct-Sep)
                        CASE 
                            WHEN EXTRACT(MONTH FROM action_date) >= 10 
                            THEN EXTRACT(YEAR FROM action_date) + 1
                            ELSE EXTRACT(YEAR FROM action_date)
                        END AS fiscal_year,
                        -- Calculate fiscal quarter based on month
                        CASE 
                            WHEN EXTRACT(MONTH FROM action_date) BETWEEN 10 AND 12 THEN 1
                            WHEN EXTRACT(MONTH FROM action_date) BETWEEN 1 AND 3 THEN 2
                            WHEN EXTRACT(MONTH FROM action_date) BETWEEN 4 AND 6 THEN 3
                            WHEN EXTRACT(MONTH FROM action_date) BETWEEN 7 AND 9 THEN 4
                        END AS fiscal_quarter
                    FROM {schema_name}.usaprime_cleaned
                    WHERE action_date IS NOT NULL
                ),
                -- Format year_quarter for display
                year_quarter_data AS (
                    SELECT
                        'FY' || fiscal_year || ' Q' || fiscal_quarter AS year_quarter,
                        fiscal_year,
                        fiscal_quarter,
                        federal_action_obligation,
                        modification_number
                    FROM fiscal_data
                ),
                -- Aggregate spending by quarter
                quarterly_spending AS (
                    SELECT
                        year_quarter,
                        fiscal_year,
                        fiscal_quarter,
                        SUM(federal_action_obligation) AS federal_action_obligation
                    FROM year_quarter_data
                    GROUP BY year_quarter, fiscal_year, fiscal_quarter
                ),
                -- Count only original awards (modification_number = '0')
                quarterly_awards AS (
                    SELECT
                        year_quarter,
                        COUNT(*) AS award_count
                    FROM year_quarter_data
                    WHERE modification_number = '0'
                    GROUP BY year_quarter
                ),
                -- Merge spending and award counts
                quarterly_combined AS (
                    SELECT
                        qs.year_quarter,
                        qs.fiscal_year,
                        qs.fiscal_quarter,
                        qs.federal_action_obligation,
                        COALESCE(qa.award_count, 0) AS award_count
                    FROM quarterly_spending qs
                    LEFT JOIN quarterly_awards qa ON qs.year_quarter = qa.year_quarter
                )
                -- Calculate cumulative values by fiscal year
                SELECT
                    qc.year_quarter,
                    qc.fiscal_year::text,
                    qc.fiscal_quarter,
                    qc.federal_action_obligation,
                    qc.award_count,
                    SUM(qc.federal_action_obligation) OVER (
                        PARTITION BY qc.fiscal_year 
                        ORDER BY qc.fiscal_year, qc.fiscal_quarter
                        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
                    ) AS cumulative_spending,
                    SUM(qc.award_count) OVER (
                        PARTITION BY qc.fiscal_year 
                        ORDER BY qc.fiscal_year, qc.fiscal_quarter
                        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
                    ) AS cumulative_awards
                FROM quarterly_combined qc
                ORDER BY qc.fiscal_year, qc.fiscal_quarter
            """)
            
            # Create indexes on the quarterly_data table
            cursor.execute(f"""
                CREATE INDEX idx_quarterly_data_year_quarter 
                ON {schema_name}.quarterly_data (year_quarter)
            """)
            
            cursor.execute(f"""
                CREATE INDEX idx_quarterly_data_fiscal_year 
                ON {schema_name}.quarterly_data (fiscal_year)
            """)
            
            # Count the rows to verify
            cursor.execute(f"SELECT COUNT(*) FROM {schema_name}.quarterly_data")
            quarterly_count = cursor.fetchone()[0]
            print(f"  ✓ Created quarterly_data table with {quarterly_count} rows.")
            
            # Verify table was created
            cursor.execute(f"""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = '{schema_name}'
                    AND table_name = 'quarterly_data'
                )
            """)
            if cursor.fetchone()[0]:
                print("    ✓ Confirmed quarterly_data table exists in database")
            else:
                print("    ⚠ Warning: quarterly_data table creation could not be confirmed")
            
    except Exception as e:
        print(f"Error creating quarterly_data table: {str(e)}")
        raise
    finally:
        conn.close()
    
    # Step 5: Create indexes for better query performance
    print("\nCreating indexes for better performance...")
    index_start_time = time.time()
    
    try:
        # Create a new connection for this step
        conn = psycopg2.connect(
            dbname=pg_dbname,
            user=pg_user,
            password=pg_password,
            host=pg_host,
            port=pg_port
        )
        conn.autocommit = True
        
        with conn.cursor() as cursor:
            # Set maintenance_work_mem for faster index creation
            cursor.execute("SET maintenance_work_mem = '1GB'")
            cursor.execute("SET max_parallel_maintenance_workers = 4")
            
            # Define the columns to index
            index_columns = [
                "action_date", "period_of_performance_current_end_date", "modification_number",
                "parent_award_agency_name", "funding_sub_agency_name", "funding_office_name",
                "recipient_name", "naics_code", "product_or_service_code", "type_of_contract_pricing",
                "extent_competed", "type_of_set_aside"
            ]
            
            # Create B-tree indexes for all columns
            for column in index_columns:
                print(f"  - Creating index on {column}...")
                index_name = f"idx_{column}"
                cursor.execute(f"""
                    CREATE INDEX IF NOT EXISTS {index_name}
                    ON {schema_name}.usaprime_cleaned ({column})
                """)
                print(f"    ✓ Created index on {column}")
            
            # Create specialized index types
            print("  - Creating BRIN index on action_date...")
            cursor.execute(f"""
                CREATE INDEX IF NOT EXISTS idx_action_date_brin 
                ON {schema_name}.usaprime_cleaned USING BRIN (action_date)
            """)
            print("    ✓ Created BRIN index on action_date")
            
            print("  - Creating BRIN index on period_of_performance_current_end_date...")
            cursor.execute(f"""
                CREATE INDEX IF NOT EXISTS idx_perf_end_date_brin 
                ON {schema_name}.usaprime_cleaned USING BRIN (period_of_performance_current_end_date)
            """)
            print("    ✓ Created BRIN index on period_of_performance_current_end_date")
            
            # Create composite index for common filtering combinations
            print("  - Creating composite index for common filter combinations...")
            cursor.execute(f"""
                CREATE INDEX IF NOT EXISTS idx_filter_composite 
                ON {schema_name}.usaprime_cleaned (
                    parent_award_agency_name, 
                    funding_sub_agency_name,
                    funding_office_name,
                    recipient_name
                )
            """)
            print("    ✓ Created composite index for common filter combinations")
            
            # Analyze the tables for query optimization
            print("\nAnalyzing tables for query optimization...")
            cursor.execute(f"ANALYZE {schema_name}.usaprime_cleaned")
            print(f"  ✓ Analyzed usaprime_cleaned table")
            
            # Only analyze tables that exist
            for table_name in ['quarterly_data', 'filter_dependencies']:
                try:
                    cursor.execute(f"""
                        SELECT EXISTS (
                            SELECT FROM information_schema.tables 
                            WHERE table_schema = '{schema_name}'
                            AND table_name = '{table_name}'
                        )
                    """)
                    if cursor.fetchone()[0]:
                        cursor.execute(f"ANALYZE {schema_name}.{table_name}")
                        print(f"  ✓ Analyzed {table_name} table")
                except Exception as e:
                    print(f"  ✗ Error analyzing {table_name}: {str(e)}")
            
            # Analyze filter value tables
            for column in filter_columns:
                table_name = f"filter_values_{column}"
                try:
                    cursor.execute(f"""
                        SELECT EXISTS (
                            SELECT FROM information_schema.tables 
                            WHERE table_schema = '{schema_name}'
                            AND table_name = '{table_name}'
                        )
                    """)
                    if cursor.fetchone()[0]:
                        cursor.execute(f"ANALYZE {schema_name}.{table_name}")
                        print(f"  ✓ Analyzed {table_name} table")
                except Exception as e:
                    print(f"  ✗ Error analyzing {table_name}: {str(e)}")
            
            index_end_time = time.time()
            print(f"Indexes created and tables analyzed in {index_end_time - index_start_time:.2f} seconds.")
            
    except Exception as e:
        print(f"Error creating indexes: {str(e)}")
        print("Some indexes may still have been created successfully.")
    finally:
        conn.close()
    
    # Final step: Verify all tables were created successfully
    print("\nVerifying table creation...")
    try:
        conn = psycopg2.connect(
            dbname=pg_dbname,
            user=pg_user,
            password=pg_password,
            host=pg_host,
            port=pg_port
        )
        
        with conn.cursor() as cursor:
            # Get all tables in our schema
            cursor.execute(f"""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = '{schema_name}'
                AND table_type = 'BASE TABLE'
                ORDER BY table_name
            """)
            
            tables = cursor.fetchall()
            print(f"Found {len(tables)} tables in schema '{schema_name}':")
            for table in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {schema_name}.{table[0]}")
                row_count = cursor.fetchone()[0]
                print(f"  - {table[0]}: {row_count:,} rows")
    
    except Exception as e:
        print(f"Error verifying tables: {str(e)}")
    finally:
        conn.close()
    
    total_elapsed_time = time.time() - total_start_time
    minutes = int(total_elapsed_time // 60)
    seconds = int(total_elapsed_time % 60)
    
    print(f"\nData preprocessing complete! Total time: {minutes}m {seconds}s")
    print("Created and optimized:")
    print(f"  - {len(filter_columns)} filter value tables for dropdown menus")
    print(f"  - Filter dependencies table for cascading filters")
    print(f"  - Quarterly data table for visualizations with fiscal calculations")
    print(f"  - Multiple specialized indexes for query performance")
    print("\nThe application should now be ready to run with optimal performance!")
    print("\nTIP: If you don't see the new tables in pgAdmin 4, try the following steps:")
    print("  1. Right-click on the schema name (usually 'public') and select 'Refresh'")
    print("  2. Check that the tables exist by running this query in pgAdmin:")
    print("     SELECT tablename FROM pg_tables WHERE schemaname = 'public';")

if __name__ == "__main__":
    print(f"Python version: {sys.version}")
    print(f"Pandas version: {pd.__version__}")
    preprocess_data_optimized()
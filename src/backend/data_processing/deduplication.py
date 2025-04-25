"""
Data Deduplication Script for USASpending Contract Data.

This script handles the deduplication of the usaprime_cleaned table as a separate process.
It allows for more control over how duplicates are identified and handled.
"""

import pandas as pd
from sqlalchemy import create_engine, text
import time
import os
import sys
from dotenv import load_dotenv
import json
from datetime import datetime

# Load environment variables from .env file
load_dotenv()

# Get PostgreSQL connection details from environment variables
pg_user = os.getenv('PG_USER')
pg_password = os.getenv('PG_PASSWORD')
pg_host = os.getenv('PG_HOST')
pg_port = os.getenv('PG_PORT')
pg_dbname = os.getenv('PG_DBNAME')

# Basic engine for setup and queries
db_url = f"postgresql://{pg_user}:{pg_password}@{pg_host}:{pg_port}/{pg_dbname}"
engine = create_engine(db_url, echo=False)

def analyze_duplicates(save_report=True):
    """
    Analyze potential duplicates in the usaprime_cleaned table and generate a report.
    
    Parameters:
    -----------
    save_report : bool, default=True
        If True, saves the analysis report to a JSON file.
        
    Returns:
    --------
    dict
        A dictionary containing duplicate counts by different key combinations.
    """
    print("Analyzing potential duplicates in usaprime_cleaned table...")
    start_time = time.time()
    
    duplicate_analysis = {}
    
    # Get total row count
    with engine.connect() as connection:
        total_count = connection.execute(text("SELECT COUNT(*) FROM usaprime_cleaned")).scalar()
        duplicate_analysis["total_rows"] = total_count
        print(f"Total rows in usaprime_cleaned: {total_count:,}")
        
        # Check various combinations of columns that might indicate duplicates
        duplicate_checks = [
            {
                "name": "exact_match",
                "columns": ["award_id_piid", "modification_number", "action_date", "federal_action_obligation", "recipient_name"],
                "description": "Exact match on key identifiers and values"
            },
            {
                "name": "transaction_match",
                "columns": ["award_id_piid", "modification_number", "action_date"],
                "description": "Same contract modification on same date (possible duplicate transactions)"
            },
            {
                "name": "financial_match",
                "columns": ["award_id_piid", "federal_action_obligation", "action_date"],
                "description": "Same contract with identical dollar amount on same date"
            },
            {
                "name": "contract_match",
                "columns": ["award_id_piid", "modification_number"],
                "description": "Same contract modification (regardless of date)"
            }
        ]
        
        for check in duplicate_checks:
            # Create column list for SQL
            columns_str = ", ".join(check["columns"])
            
            # Query to count duplicates
            duplicate_query = text(f"""
                SELECT {columns_str}, COUNT(*) as duplicate_count
                FROM usaprime_cleaned
                GROUP BY {columns_str}
                HAVING COUNT(*) > 1
                ORDER BY COUNT(*) DESC
            """)
            
            # Get duplicate groups
            duplicate_groups = connection.execute(duplicate_query).fetchall()
            
            # Calculate total duplicated rows
            if duplicate_groups:
                total_duplicated = sum(row[-1] for row in duplicate_groups) - len(duplicate_groups)
                unique_groups = len(duplicate_groups)
                duplicate_percentage = (total_duplicated / total_count) * 100
                
                # Store analysis results
                check_results = {
                    "description": check["description"],
                    "duplicate_groups": unique_groups,
                    "total_duplicated_rows": total_duplicated,
                    "percentage_duplicated": round(duplicate_percentage, 2),
                    "sample_groups": [dict(zip(check["columns"] + ["count"], row)) for row in duplicate_groups[:5]]
                }
            else:
                check_results = {
                    "description": check["description"],
                    "duplicate_groups": 0,
                    "total_duplicated_rows": 0,
                    "percentage_duplicated": 0,
                    "sample_groups": []
                }
            
            duplicate_analysis[check["name"]] = check_results
            
            # Print summary for this check
            print(f"\nCheck: {check['name']} - {check['description']}")
            print(f"  Found {check_results['duplicate_groups']:,} duplicate groups")
            print(f"  Total duplicated rows: {check_results['total_duplicated_rows']:,} ({check_results['percentage_duplicated']}%)")
    
    elapsed = time.time() - start_time
    duplicate_analysis["analysis_time_seconds"] = round(elapsed, 2)
    
    if save_report:
        # Save analysis to a JSON file with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "logs")
        os.makedirs(report_dir, exist_ok=True)
        report_file = os.path.join(report_dir, f"duplicate_analysis_{timestamp}.json")
        
        with open(report_file, 'w') as f:
            json.dump(duplicate_analysis, f, indent=2)
        
        print(f"\nAnalysis report saved to: {report_file}")
    
    print(f"\nAnalysis completed in {elapsed:.2f} seconds")
    return duplicate_analysis

def deduplicate_data(strategy="exact_match", create_new_table=True, report=True):
    """
    Remove duplicates from the usaprime_cleaned table using the specified strategy.
    
    Parameters:
    -----------
    strategy : str, default="exact_match"
        The deduplication strategy to use. Options:
        - "exact_match": Remove duplicates with identical award_id_piid, modification_number, action_date, 
                         federal_action_obligation, recipient_name
        - "transaction_match": Remove duplicates with identical award_id_piid, modification_number, action_date
        - "financial_match": Remove duplicates with identical award_id_piid, federal_action_obligation, action_date
        - "contract_match": Remove duplicates with identical award_id_piid, modification_number
        - "custom": Use a custom deduplication query provided in the parameter custom_query
        
    create_new_table : bool, default=True
        If True, creates a new table (usaprime_deduplicated) with the deduplicated data.
        If False, applies deduplication to the existing usaprime_cleaned table directly.
        
    report : bool, default=True
        If True, generates a deduplication report.
        
    Returns:
    --------
    dict
        A dictionary containing the deduplication results.
    """
    start_time = time.time()
    results = {}
    
    # Define deduplication strategies
    strategies = {
        "exact_match": {
            "description": "Exact match on key identifiers and values",
            "columns": ["award_id_piid", "modification_number", "action_date", "federal_action_obligation", "recipient_name"]
        },
        "transaction_match": {
            "description": "Same contract modification on same date",
            "columns": ["award_id_piid", "modification_number", "action_date"]
        },
        "financial_match": {
            "description": "Same contract with identical dollar amount on same date",
            "columns": ["award_id_piid", "federal_action_obligation", "action_date"]
        },
        "contract_match": {
            "description": "Same contract modification (regardless of date)",
            "columns": ["award_id_piid", "modification_number"]
        }
    }
    
    # Validate strategy
    if strategy not in strategies:
        raise ValueError(f"Invalid deduplication strategy: {strategy}. Must be one of {list(strategies.keys())}")
    
    # Selected strategy
    selected_strategy = strategies[strategy]
    
    with engine.connect() as connection:
        # Get original row count
        original_count = connection.execute(text("SELECT COUNT(*) FROM usaprime_cleaned")).scalar()
        results["original_row_count"] = original_count
        
        if create_new_table:
            # Create deduplicated table
            print(f"Creating new deduplicated table using strategy: {strategy}")
            print(f"Strategy description: {selected_strategy['description']}")
            
            # Check if table exists and drop if needed
            table_exists = connection.execute(text(
                "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'usaprime_deduplicated')"
            )).scalar()
            
            if table_exists:
                print("usaprime_deduplicated table already exists and will be dropped")
                connection.execute(text("DROP TABLE IF EXISTS usaprime_deduplicated CASCADE"))
            
            # Prepare columns for DISTINCT ON clause
            distinct_columns = ", ".join(selected_strategy["columns"])
            
            # Create new table with deduplicated data
            create_dedupe_query = text(f"""
                CREATE TABLE usaprime_deduplicated AS
                SELECT DISTINCT ON ({distinct_columns}) *
                FROM usaprime_cleaned
                ORDER BY {distinct_columns}, action_date DESC
            """)
            
            connection.execute(create_dedupe_query)
            connection.commit()
            
            # Get deduplicated row count
            deduplicated_count = connection.execute(text("SELECT COUNT(*) FROM usaprime_deduplicated")).scalar()
            results["deduplicated_row_count"] = deduplicated_count
            
            # Create same indexes as on usaprime_cleaned
            print("Creating indexes on deduplicated table...")
            
            connection.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_dedupe_modification_number 
                ON usaprime_deduplicated(modification_number)
            """))
            
            connection.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_dedupe_award_id_piid 
                ON usaprime_deduplicated(award_id_piid)
            """))
            
            connection.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_dedupe_action_date 
                ON usaprime_deduplicated(action_date)
            """))
            
            connection.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_dedupe_recipient_name 
                ON usaprime_deduplicated(recipient_name)
            """))
            
            connection.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_dedupe_naics_code 
                ON usaprime_deduplicated(naics_code)
            """))
            
            connection.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_dedupe_agency_fiscal_year 
                ON usaprime_deduplicated(parent_award_agency_name, action_date_fiscal_year)
            """))
            
            # Analyze table for query optimization
            connection.execute(text("ANALYZE usaprime_deduplicated"))
            connection.commit()
            
        else:
            # In-place deduplication - create temporary table then swap
            print(f"Performing in-place deduplication using strategy: {strategy}")
            print(f"Strategy description: {selected_strategy['description']}")
            
            # Prepare columns for DISTINCT ON clause
            distinct_columns = ", ".join(selected_strategy["columns"])
            
            # Create temporary table with deduplicated data
            connection.execute(text("CREATE TABLE usaprime_temp AS SELECT * FROM usaprime_cleaned LIMIT 0"))
            
            # Insert deduplicated data
            dedupe_query = text(f"""
                INSERT INTO usaprime_temp
                SELECT DISTINCT ON ({distinct_columns}) *
                FROM usaprime_cleaned
                ORDER BY {distinct_columns}, action_date DESC
            """)
            
            connection.execute(dedupe_query)
            connection.commit()
            
            # Get deduplicated row count
            deduplicated_count = connection.execute(text("SELECT COUNT(*) FROM usaprime_temp")).scalar()
            results["deduplicated_row_count"] = deduplicated_count
            
            # Swap tables
            connection.execute(text("DROP TABLE usaprime_cleaned CASCADE"))
            connection.execute(text("ALTER TABLE usaprime_temp RENAME TO usaprime_cleaned"))
            
            # Recreate indexes
            print("Recreating indexes...")
            
            connection.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_modification_number 
                ON usaprime_cleaned(modification_number)
            """))
            
            connection.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_award_id_piid 
                ON usaprime_cleaned(award_id_piid)
            """))
            
            connection.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_action_date 
                ON usaprime_cleaned(action_date)
            """))
            
            connection.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_recipient_name 
                ON usaprime_cleaned(recipient_name)
            """))
            
            connection.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_naics_code 
                ON usaprime_cleaned(naics_code)
            """))
            
            connection.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_agency_fiscal_year 
                ON usaprime_cleaned(parent_award_agency_name, action_date_fiscal_year)
            """))
            
            # Analyze table for query optimization
            connection.execute(text("ANALYZE usaprime_cleaned"))
            connection.commit()
        
        # Calculate reduction statistics
        removed_rows = original_count - deduplicated_count
        reduction_percentage = (removed_rows / original_count) * 100 if original_count > 0 else 0
        
        results["removed_rows"] = removed_rows
        results["reduction_percentage"] = round(reduction_percentage, 2)
        results["strategy"] = strategy
        results["strategy_description"] = selected_strategy["description"]
        results["strategy_columns"] = selected_strategy["columns"]
        
    elapsed_time = time.time() - start_time
    minutes = int(elapsed_time // 60)
    seconds = int(elapsed_time % 60)
    
    results["processing_time_seconds"] = round(elapsed_time, 2)
    
    # Print summary
    target_table = "usaprime_deduplicated" if create_new_table else "usaprime_cleaned"
    print(f"\nDeduplication complete!")
    print(f"Strategy: {strategy} - {selected_strategy['description']}")
    print(f"Original row count: {original_count:,}")
    print(f"Deduplicated row count: {deduplicated_count:,}")
    print(f"Removed {removed_rows:,} duplicate rows ({reduction_percentage:.2f}%)")
    print(f"Target table: {target_table}")
    print(f"Processing time: {minutes}m {seconds}s")
    
    if report:
        # Save deduplication report to a JSON file with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "logs")
        os.makedirs(report_dir, exist_ok=True)
        report_file = os.path.join(report_dir, f"deduplication_report_{timestamp}.json")
        
        with open(report_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\nDeduplication report saved to: {report_file}")
    
    return results

if __name__ == "__main__":
    print(f"Python version: {sys.version}")
    print(f"Pandas version: {pd.__version__}")
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command == "analyze":
            analyze_duplicates()
        elif command == "deduplicate":
            # Check if strategy is provided
            strategy = "exact_match"
            create_new_table = True
            
            if len(sys.argv) > 2:
                strategy = sys.argv[2]
            
            if len(sys.argv) > 3 and sys.argv[3].lower() == "inplace":
                create_new_table = False
            
            deduplicate_data(strategy=strategy, create_new_table=create_new_table)
        else:
            print("Unknown command. Use 'analyze' or 'deduplicate'.")
    else:
        print("Data Deduplication Tool for USASpending Contract Data")
        print("\nUsage:")
        print("  python -m src.backend.data_processing.deduplication analyze")
        print("  python -m src.backend.data_processing.deduplication deduplicate [strategy] [inplace]")
        print("\nExamples:")
        print("  python -m src.backend.data_processing.deduplication analyze")
        print("  python -m src.backend.data_processing.deduplication deduplicate exact_match")
        print("  python -m src.backend.data_processing.deduplication deduplicate transaction_match inplace")
        print("\nAvailable deduplication strategies:")
        print("  - exact_match: Identical contract ID, modification, date, amount, and recipient")
        print("  - transaction_match: Identical contract ID, modification, and date")
        print("  - financial_match: Identical contract ID, amount, and date")
        print("  - contract_match: Identical contract ID and modification number")
"""
Data Deduplication Script for USASpending Contract Data.

This script handles the analysis and deduplication of the usaprime_cleaned table 
using contract_transaction_unique_key as the primary identifier for duplicates.
It creates a separate table with deduplicated data while preserving the raw source data.
"""

import pandas as pd
from sqlalchemy import create_engine, text
import time
import os
import sys
from dotenv import load_dotenv
import json
from datetime import datetime, date
import decimal
import logging

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

# Set up logging
logger = logging.getLogger(__name__)

# Custom JSON encoder to handle date objects and Decimal values
class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        if isinstance(obj, decimal.Decimal):
            return float(obj)
        return super(CustomJSONEncoder, self).default(obj)

def analyze_duplicates(save_report=True):
    """
    Analyze potential duplicates in the usaprime_cleaned table and generate a report.
    Focuses on contract_transaction_unique_key as the primary duplicate identifier.
    
    Parameters:
    -----------
    save_report : bool, default=True
        If True, saves the analysis report to a JSON file.
        
    Returns:
    --------
    dict
        A dictionary containing duplicate counts by different key combinations.
    """
    logger.info("Analyzing potential duplicates in usaprime_cleaned table...")
    start_time = time.time()
    
    duplicate_analysis = {}
    
    # Get total row count
    with engine.connect() as connection:
        total_count = connection.execute(text("SELECT COUNT(*) FROM usaprime_cleaned")).scalar()
        duplicate_analysis["total_rows"] = total_count
        logger.info(f"Total rows in usaprime_cleaned: {total_count:,}")
        
        # Since we're now using contract_transaction_unique_key as PRIMARY KEY,
        # there shouldn't be any duplicates in the cleaned table
        # But let's check if there are any NULL values or synthetic keys
        
        key_check_query = text("""
            SELECT 
                COUNT(*) FILTER (WHERE contract_transaction_unique_key IS NULL) AS null_keys,
                COUNT(*) FILTER (WHERE contract_transaction_unique_key LIKE 'GENERATED_KEY_%') AS synthetic_keys,
                COUNT(DISTINCT contract_transaction_unique_key) AS unique_keys
            FROM 
                usaprime_cleaned
        """)
        
        result = connection.execute(key_check_query).fetchone()
        null_keys, synthetic_keys, unique_keys = result[0], result[1], result[2]
        
        duplicate_analysis["key_stats"] = {
            "null_keys": null_keys,
            "synthetic_keys": synthetic_keys,
            "unique_keys": unique_keys
        }
        
        if null_keys > 0:
            logger.warning(f"Found {null_keys:,} rows with NULL transaction keys")
        
        if synthetic_keys > 0:
            logger.info(f"Found {synthetic_keys:,} rows with synthetic transaction keys (GENERATED_KEY_*)")
        
        # Check various combinations of columns that might indicate business-level duplicates
        duplicate_checks = [
            {
                "name": "contract_award_unique_key",
                "description": "Award key duplicates (same award, different transactions)"
            },
            {
                "name": "award_id_piid_with_modification",
                "columns": ["award_id_piid", "modification_number"],
                "description": "Same contract ID and modification number"
            },
            {
                "name": "award_date_obligation",
                "columns": ["award_id_piid", "action_date", "federal_action_obligation"],
                "description": "Same contract with identical dollar amount on same date"
            }
        ]
        
        # Check award key duplicates
        award_key_check = text("""
            SELECT 
                COUNT(*) - COUNT(DISTINCT contract_award_unique_key) AS duplicate_count,
                COUNT(DISTINCT contract_award_unique_key) AS unique_keys
            FROM 
                usaprime_cleaned
            WHERE 
                contract_award_unique_key IS NOT NULL
        """)
        
        result = connection.execute(award_key_check).fetchone()
        award_duplicates, unique_award_keys = result[0], result[1]
        
        duplicate_analysis["award_key_duplicates"] = {
            "duplicate_count": award_duplicates,
            "unique_keys": unique_award_keys,
            "percentage_duplicated": round((award_duplicates / total_count) * 100, 2) if total_count > 0 else 0
        }
        
        logger.info(f"Found {award_duplicates:,} rows that share the same contract_award_unique_key")
        logger.info(f"Data contains {unique_award_keys:,} unique award keys out of {total_count:,} total rows")
        
        # Check for other duplicates with compound keys
        for check in duplicate_checks[1:]:  # Skip the award key check as we did it separately
            if "columns" in check:
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
                logger.info(f"\nCheck: {check['name']} - {check['description']}")
                logger.info(f"  Found {check_results['duplicate_groups']:,} duplicate groups")
                logger.info(f"  Total duplicated rows: {check_results['total_duplicated_rows']:,} ({check_results['percentage_duplicated']}%)")
    
    elapsed = time.time() - start_time
    duplicate_analysis["analysis_time_seconds"] = round(elapsed, 2)
    
    if save_report:
        # Save analysis to a JSON file with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "logs")
        os.makedirs(report_dir, exist_ok=True)
        report_file = os.path.join(report_dir, f"duplicate_analysis_{timestamp}.json")
        
        # Use custom JSON encoder to handle date objects and Decimal values
        with open(report_file, 'w') as f:
            json.dump(duplicate_analysis, f, indent=2, cls=CustomJSONEncoder)
        
        logger.info(f"\nAnalysis report saved to: {report_file}")
    
    logger.info(f"\nAnalysis completed in {elapsed:.2f} seconds")
    return duplicate_analysis


def deduplicate_data(create_new_table=True, report=True):
    """
    Deduplicate both prime awards and subawards tables.
    - Prime awards: usaprime_cleaned → usaprime_deduplicated (key: contract_transaction_unique_key)
    - Subawards: usasubawards_cleaned → usasubawards_deduplicated (key: (prime_award_unique_key, subaward_number, subaward_action_date))

    Args:
        create_new_table (bool): If True, create new deduplicated tables. If False, only analyze.
        report (bool): If True, generate and save a report.
    Returns:
        dict: Results for both prime and subawards deduplication.
    """
    start_time = time.time()
    results = {}

    # --- Prime Awards Deduplication ---
    prime_source = "s2_interim.usaspending_prime_awards"  # Source table (cleaned, schema-qualified)
    prime_target = "s3_processed.usaspending_prime_awards"  # Deduplicated output table (schema-qualified)
    prime_key = "contract_transaction_unique_key"

    with engine.connect() as connection:
        # Check if source exists (schema-aware)
        source_exists = connection.execute(text(
            """
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables 
                WHERE table_schema = 's2_interim' AND table_name = 'usaspending_prime_awards'
            )
            """
        )).scalar()
        if not source_exists:
            logger.error(f"Error: Source table {prime_source} does not exist.")
            results["prime_awards"] = {"error": f"Source table {prime_source} not found"}
        else:
            original_count = connection.execute(text(f"SELECT COUNT(*) FROM {prime_source}")).scalar()
            # Always drop and recreate the deduplicated table for automation/flexibility
            connection.execute(text(f"DROP TABLE IF EXISTS {prime_target}"))
            connection.commit()
            logger.info(f"Creating {prime_target} table with distinct {prime_key} values...")
            create_query = text(f"""
                CREATE TABLE {prime_target} AS 
                SELECT DISTINCT ON ({prime_key}) * 
                FROM {prime_source}
                ORDER BY {prime_key}, action_date DESC
            """)
            connection.execute(create_query)
            connection.commit()
            deduped_count = connection.execute(text(f"SELECT COUNT(*) FROM {prime_target}")).scalar()
            removed = original_count - deduped_count
            removed_pct = (removed / original_count) * 100 if original_count > 0 else 0
            logger.info(f"Prime awards deduplication: {removed:,} duplicates removed ({removed_pct:.2f}%).")
            results["prime_awards"] = {
                "source_table": prime_source,
                "target_table": prime_target,
                "deduplication_key": prime_key,
                "original_count": original_count,
                "deduplicated_count": deduped_count,
                "removed_count": removed,
                "removed_percent": round(removed_pct, 2)
            }

    # --- Subawards Deduplication ---
    sub_source = "s2_interim.usaspending_subawards"  # Source table (cleaned, schema-qualified)
    sub_target = "s3_processed.usaspending_subawards"  # Deduplicated output table (schema-qualified)
    sub_keys = ["prime_award_unique_key", "subaward_number", "subaward_action_date", "subaward_amount"]
    sub_key_expr = ", ".join(sub_keys)

    with engine.connect() as connection:
        # Check if source exists (schema-aware)
        source_exists = connection.execute(text(
            """
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables 
                WHERE table_schema = 's2_interim' AND table_name = 'usaspending_subawards'
            )
            """
        )).scalar()
        if not source_exists:
            logger.error(f"Error: Source table {sub_source} does not exist.")
            results["subawards"] = {"error": f"Source table {sub_source} not found"}
        else:
            original_count = connection.execute(text(f"SELECT COUNT(*) FROM {sub_source}")).scalar()
            # Always drop and recreate the deduplicated table for automation/flexibility
            connection.execute(text(f"DROP TABLE IF EXISTS {sub_target}"))
            connection.commit()
            logger.info(f"Creating {sub_target} table with distinct ({sub_key_expr}) values...")
            create_query = text(f"""
                CREATE TABLE {sub_target} AS 
                SELECT DISTINCT ON ({sub_key_expr}) * 
                FROM {sub_source}
                ORDER BY {sub_key_expr}
            """)
            connection.execute(create_query)
            connection.commit()
            deduped_count = connection.execute(text(f"SELECT COUNT(*) FROM {sub_target}")).scalar()
            removed = original_count - deduped_count
            removed_pct = (removed / original_count) * 100 if original_count > 0 else 0
            logger.info(f"Subawards deduplication: {removed:,} duplicates removed ({removed_pct:.2f}%).")
            results["subawards"] = {
                "source_table": sub_source,
                "target_table": sub_target,
                "deduplication_key": sub_keys,
                "original_count": original_count,
                "deduplicated_count": deduped_count,
                "removed_count": removed,
                "removed_percent": round(removed_pct, 2)
            }

    # --- Reporting ---
    elapsed_time = time.time() - start_time
    results["processing_time_seconds"] = round(elapsed_time, 2)
    results["timestamp"] = datetime.now().isoformat()

    if report:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_filename = f"deduplication_report_{timestamp}.json"
        report_path = os.path.join("logs", report_filename)
        os.makedirs("logs", exist_ok=True)
        with open(report_path, 'w') as f:
            json.dump(results, f, indent=4, cls=CustomJSONEncoder)
        logger.info(f"\nDeduplication report saved to: {os.path.abspath(report_path)}")

    return results

if __name__ == "__main__":
    # Configure logging when run as a standalone script
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    logger.info(f"Python version: {sys.version}")
    logger.info(f"Pandas version: {pd.__version__}")
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command == "analyze":
            analyze_duplicates()
        elif command == "deduplicate":
            # Check if we should create a new table
            create_new_table = True
            if len(sys.argv) > 2 and sys.argv[2].lower() == "inplace":
                create_new_table = False
            deduplicate_data(create_new_table=create_new_table)
        else:
            logger.info("Unknown command. Use 'analyze' or 'deduplicate'.")
    else:
        # Default: run deduplication if no arguments are provided
        logger.info("No command-line arguments provided. Running deduplication by default...")
        deduplicate_data(create_new_table=True)
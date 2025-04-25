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
    Deduplicate data from usaprime_cleaned table using contract_transaction_unique_key
    as the primary key. Creates a new table with deduplicated data.
    
    Parameters:
    -----------
    create_new_table : bool, default=True
        If True, creates a new table for deduplicated data.
        If False, only analyzes potential duplicates without creating a new table.
    report : bool, default=True
        If True, generates and saves a detailed report.
        
    Returns:
    --------
    dict
        A dictionary containing deduplication results.
    """
    start_time = time.time()
    
    # Table names
    source_table = "usaprime_cleaned"
    target_table = "usaprime_deduplicated"
    
    # Key for deduplication
    primary_key = "contract_transaction_unique_key"
    
    # Check if source table exists
    with engine.connect() as connection:
        source_exists = connection.execute(text(
            f"SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = '{source_table}')"
        )).scalar()
        
        if not source_exists:
            logger.error(f"Error: Source table {source_table} does not exist.")
            return {"error": f"Source table {source_table} not found"}
    
    # Count original rows
    with engine.connect() as connection:
        original_count = connection.execute(text(f"SELECT COUNT(*) FROM {source_table}")).scalar()
        logger.info(f"Starting deduplication of {original_count:,} rows...")
    
    if create_new_table:
        # Create the deduplicated table using SQL DISTINCT ON
        with engine.connect() as connection:
            # Check if target table already exists and drop if needed
            target_exists = connection.execute(text(
                f"SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = '{target_table}')"
            )).scalar()
            
            if target_exists:
                logger.info(f"Dropping existing {target_table} table...")
                connection.execute(text(f"DROP TABLE IF EXISTS {target_table}"))
                connection.commit()
            
            # Create new table with distinct rows based on primary key
            logger.info(f"Creating {target_table} table with distinct {primary_key} values...")
            
            # Use CREATE TABLE AS with DISTINCT ON for better performance
            create_query = text(f"""
                CREATE TABLE {target_table} AS 
                SELECT DISTINCT ON ({primary_key}) * 
                FROM {source_table}
                ORDER BY {primary_key}, action_date DESC
            """)
            
            connection.execute(create_query)
            connection.commit()
            
            # Count deduplicated rows
            deduplicated_count = connection.execute(text(f"SELECT COUNT(*) FROM {target_table}")).scalar()
            
            # Calculate how many duplicates were removed
            removed_count = original_count - deduplicated_count
            removed_percent = (removed_count / original_count) * 100 if original_count > 0 else 0
            
            logger.info(f"Removed {removed_count:,} duplicate rows ({removed_percent:.2f}%).")
            
            # Create indexes on the deduplicated table for better performance
            logger.info("Creating indexes on deduplicated table for better performance...")
            
            indexes = [
                {"name": "idx_dedupe_award_id_piid", "columns": "award_id_piid"},
                {"name": "idx_dedupe_action_date", "columns": "action_date"},
                {"name": "idx_dedupe_recipient_name", "columns": "recipient_name"},
                {"name": "idx_dedupe_naics_code", "columns": "naics_code"},
                {"name": "idx_dedupe_agency_fiscal_year", "columns": "parent_award_agency_name, action_date_fiscal_year"}
            ]
            
            for index in indexes:
                index_name = index["name"]
                columns = index["columns"]
                
                connection.execute(text(f"DROP INDEX IF EXISTS {index_name}"))
                connection.execute(text(f"CREATE INDEX {index_name} ON {target_table} ({columns})"))
                connection.commit()
                
                logger.info(f"  [OK] Created index {index_name} on {columns}")
    
    else:
        # Just get counts for the report without creating a new table
        deduplicated_count = original_count  # Placeholder
        removed_count = 0
        removed_percent = 0
    
    # Calculate processing time
    elapsed_time = time.time() - start_time
    minutes = int(elapsed_time // 60)
    seconds = int(elapsed_time % 60)
    
    logger.info("\nDeduplication complete!")
    logger.info(f"Method: Using {primary_key} as PRIMARY KEY")
    logger.info(f"Original row count: {original_count:,}")
    logger.info(f"Deduplicated row count: {deduplicated_count:,}")
    logger.info(f"Removed {removed_count:,} duplicate rows ({removed_percent:.2f}%)")
    logger.info(f"Target table: {target_table}")
    logger.info(f"Processing time: {minutes}m {seconds}s")
    
    # Generate report
    results = {
        "source_table": source_table,
        "target_table": target_table,
        "deduplication_key": primary_key,
        "original_count": original_count,
        "deduplicated_count": deduplicated_count,
        "removed_count": removed_count,
        "removed_percent": round(removed_percent, 2),
        "processing_time_seconds": round(elapsed_time, 2),
        "timestamp": datetime.now().isoformat()
    }
    
    if report:
        # Save report to file
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
        logger.info("Data Deduplication Tool for USASpending Contract Data")
        logger.info("\nUsage:")
        logger.info("  python -m src.backend.data_processing.deduplication analyze")
        logger.info("  python -m src.backend.data_processing.deduplication deduplicate [inplace]")
        logger.info("\nExamples:")
        logger.info("  python -m src.backend.data_processing.deduplication analyze")
        logger.info("  python -m src.backend.data_processing.deduplication deduplicate")
        logger.info("  python -m src.backend.data_processing.deduplication deduplicate inplace")
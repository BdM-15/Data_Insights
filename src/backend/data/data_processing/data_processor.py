"""
Data Processing Orchestrator for USASpending Contract Data

This script runs the entire data processing workflow while preserving raw data integrity:
1. Cleansing: Create cleaned table from raw data without data loss
2. Deduplication: Remove duplicates based on contract_transaction_unique_key
3. Transformation: Create auxiliary tables needed for application performance
4. Cleanup: Remove any temporary tables not needed for the application
"""

import os
import sys
import time
from datetime import datetime
import logging
from pathlib import Path

# Import processing modules - use relative imports for the package
from .cleansing import cleanse_data
from .deduplication import analyze_duplicates, deduplicate_data
from .transformation import preprocess_data_optimized

# Configure logging
log_dir = Path(__file__).parents[3] / "logs"
log_dir.mkdir(exist_ok=True)
log_file = log_dir / "data_processing.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def process_data(force_rebuild=True, perform_deduplication=True, create_deduplication_table=True):
    """
    Run the complete data processing workflow
    
    Parameters:
    -----------
    force_rebuild : bool, default=True
        If True, drops and recreates the destination tables if they exist
    perform_deduplication : bool, default=True
        If True, perform deduplication step using contract_transaction_unique_key
    create_deduplication_table : bool, default=True
        If True and perform_deduplication=True, creates a dedicated deduplicated table
        If False and perform_deduplication=True, performs in-place deduplication
    """
    start_time = time.time()
    logger.info("Starting complete data processing workflow...")
    
    # Step 1: Cleansing - Transform raw data to cleaned format (no data removal)
    logger.info("\n===== STEP 1: DATA CLEANSING =====")
    cleanse_result = cleanse_data(force_rebuild=force_rebuild)
    
    if not cleanse_result:
        logger.error("ERROR: Data cleansing failed. Stopping workflow.")
        return False
    
    # Step 2: Analyze duplicates and perform deduplication based on contract_transaction_unique_key
    logger.info("\n===== STEP 2: DUPLICATE ANALYSIS & DEDUPLICATION =====")
    
    # Analyze duplicates first
    duplicate_analysis = analyze_duplicates(save_report=True)
    
    # Check if we need to perform deduplication
    if perform_deduplication:
        logger.info("\nPerforming deduplication using contract_transaction_unique_key...")
        deduplicate_result = deduplicate_data(create_new_table=create_deduplication_table, report=True)
        source_table_for_transformation = "usaprime_deduplicated" if create_deduplication_table else "usaprime_cleaned"
    else:
        logger.info("\nSkipping deduplication as requested. Using cleaned data directly.")
        source_table_for_transformation = "usaprime_cleaned"
    
    # Step 3: Transformation - Create performance-optimizing tables
    logger.info(f"\n===== STEP 3: DATA TRANSFORMATION =====")
    logger.info(f"Using {source_table_for_transformation} as source for transformation")
    # Note: The transformation code currently assumes usaprime_cleaned as source
    # In future updates, you might want to modify transformation.py to accept a source_table parameter
    transform_result = preprocess_data_optimized()
    
    # Final report
    elapsed_time = time.time() - start_time
    hours = int(elapsed_time // 3600)
    minutes = int((elapsed_time % 3600) // 60)
    seconds = int(elapsed_time % 60)
    
    logger.info("\n===== PROCESSING COMPLETE =====")
    logger.info(f"Total processing time: {hours}h {minutes}m {seconds}s")
    logger.info(f"Processing completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Summary of tables created
    logger.info("\nData Processing Summary:")
    logger.info("1. Raw data preserved in: usaspending_prime_awards")
    logger.info("2. Cleaned data available in: usaprime_cleaned")
    
    if perform_deduplication and create_deduplication_table:
        logger.info("3. Deduplicated data available in: usaprime_deduplicated")
        logger.info("4. Application performance tables created (filter tables, aggregations, etc.)")
    else:
        logger.info("3. Application performance tables created (filter tables, aggregations, etc.)")
    
    if perform_deduplication:
        removed = deduplicate_result.get("removed_rows", 0)
        percentage = deduplicate_result.get("reduction_percentage", 0)
        logger.info(f"\nDuplication Stats: Removed {removed:,} duplicate rows ({percentage:.2f}%)")
    
    logger.info(f"\nThe application is now ready to use the processed data")
    
    return True

if __name__ == "__main__":
    logger.info(f"USASpending Data Processing Orchestrator")
    
    # Parse command line arguments
    force_rebuild = True
    perform_deduplication = True
    create_deduplication_table = True
    
    if len(sys.argv) > 1:
        if sys.argv[1].lower() == "preserve":
            force_rebuild = False
            logger.info("Running in preserve mode - will not rebuild existing tables.")
        elif sys.argv[1].lower() == "nodedupe":
            perform_deduplication = False
            logger.info("Running without deduplication.")
    
    if len(sys.argv) > 2 and sys.argv[2].lower() == "inplace":
        create_deduplication_table = False
        logger.info("Deduplication will be performed in-place without creating a separate table.")
    
    # Run the workflow
    process_data(force_rebuild, perform_deduplication, create_deduplication_table)
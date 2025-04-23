"""
Main data fetching coordinator module.
Provides functions to fetch data from all sources and update the database.
"""

import logging
import time
from datetime import datetime
import argparse

import config
import sam_gov
import nato_nspa
import usaspending_current
import usaspending_historical

logger = logging.getLogger(__name__)

def setup_logging():
    """Set up logging for the data fetching process."""
    logging.basicConfig(
        filename=f"{config.LOGS_DIR}/data_fetcher.log",
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

def fetch_all_current_data():
    """
    Fetch current data from all sources and update the database.
    
    Returns:
        dict: Results of fetch operations for each source
    """
    results = {}
    start_time = time.time()
    
    print(f"Starting data fetch from all sources at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"Starting data fetch from all sources")
    
    # Fetch SAM.gov opportunities
    print("\n=== Fetching SAM.gov opportunities ===")
    sam_success = sam_gov.update_sam_opportunities()
    results['sam_gov'] = sam_success
    
    # Fetch NATO NSPA opportunities
    print("\n=== Fetching NATO NSPA opportunities ===")
    nato_success = nato_nspa.update_nato_opportunities()
    results['nato_nspa'] = nato_success
    
    # Fetch current USAspending awards
    print("\n=== Fetching current USAspending awards ===")
    usa_current_success = usaspending_current.update_current_usaspending()
    results['usaspending_current'] = usa_current_success
    
    # Calculate and log total time
    elapsed_time = time.time() - start_time
    minutes, seconds = divmod(elapsed_time, 60)
    print(f"\nFetch completed in {int(minutes)} minutes and {int(seconds)} seconds")
    logger.info(f"Fetch completed in {int(minutes)} minutes and {int(seconds)} seconds")
    
    # Log summary of results
    summary = ", ".join([f"{k}: {'✅' if v else '❌'}" for k, v in results.items()])
    print(f"Fetch results: {summary}")
    logger.info(f"Fetch results: {summary}")
    
    return results

def fetch_historical_data():
    """
    Fetch historical USAspending data.
    
    Returns:
        bool: True if successful, False otherwise
    """
    print(f"\n=== Fetching historical USAspending data ===")
    print("Note: This process may take a long time (hours to days) based on date range.")
    print(f"Date range: {config.HISTORICAL_START_DATE} to {config.HISTORICAL_END_DATE}")
    print(f"Chunk size: {config.HISTORICAL_CHUNK_DAYS} days")
    
    start_time = time.time()
    
    success = usaspending_historical.fetch_usaspending_historical()
    
    elapsed_time = time.time() - start_time
    hours, remainder = divmod(elapsed_time, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    print(f"\nHistorical fetch {'completed successfully' if success else 'failed'}")
    print(f"Total time: {int(hours)} hours, {int(minutes)} minutes, and {int(seconds)} seconds")
    
    if success:
        success, count = usaspending_historical.count_historical_records()
        if success:
            print(f"Total historical records: {count:,}")
    
    return success

def main():
    """Main entry point with command-line argument parsing."""
    parser = argparse.ArgumentParser(description='Fetch data from various sources')
    parser.add_argument('--current', action='store_true', help='Fetch current data from all sources')
    parser.add_argument('--historical', action='store_true', help='Fetch historical USAspending data')
    parser.add_argument('--sam', action='store_true', help='Fetch only SAM.gov data')
    parser.add_argument('--nato', action='store_true', help='Fetch only NATO NSPA data')
    parser.add_argument('--usa-current', action='store_true', help='Fetch only current USAspending data')
    args = parser.parse_args()
    
    setup_logging()
    
    # If no specific options provided, fetch current data by default
    if not any(vars(args).values()):
        args.current = True
    
    results = {}
    
    # Fetch current data from all sources
    if args.current:
        results = fetch_all_current_data()
    
    # Fetch historical USAspending data
    if args.historical:
        historical_success = fetch_historical_data()
        results['usaspending_historical'] = historical_success
    
    # Fetch individual sources
    if args.sam:
        sam_success = sam_gov.update_sam_opportunities()
        results['sam_gov'] = sam_success
    
    if args.nato:
        nato_success = nato_nspa.update_nato_opportunities()
        results['nato_nspa'] = nato_success
    
    if args.usa_current:
        usa_current_success = usaspending_current.update_current_usaspending()
        results['usaspending_current'] = usa_current_success
    
    # Print results summary
    if results:
        print("\n=== Results Summary ===")
        for source, success in results.items():
            print(f"{source}: {'Succeeded' if success else 'Failed'}")

if __name__ == "__main__":
    main()
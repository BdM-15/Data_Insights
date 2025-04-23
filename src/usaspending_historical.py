"""
USAspending.gov historical data fetching module.
Fetches historical contract award data from USAspending.gov API and stores in the database.
"""

from typing import List, Dict, Any, Optional, Tuple
import logging
import time
import zipfile
import io
import os
import requests
import pandas as pd
from datetime import datetime, timedelta
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type, RetryError

import config
import database
from usaspending_current import fetch_usaspending_chunk

logger = logging.getLogger(__name__)

def fetch_usaspending_historical() -> bool:
    """
    Fetch historical USAspending.gov award data in chunks, working backward in time.
    Stores data in PostgreSQL database and archives CSVs.
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        print(f"Starting historical USAspending fetch...")
        
        # Define date range
        start_date = datetime.strptime(config.HISTORICAL_START_DATE, "%Y-%m-%d")
        end_date = datetime.strptime(config.HISTORICAL_END_DATE, "%Y-%m-%d")
        
        # Get the last fetched date (if any)
        last_fetched = database.get_last_fetched_date(config.TABLE_HISTORICAL_USASPENDING)
        if last_fetched:
            print(f"Resuming from last fetched date: {last_fetched}")
            # Start from the day before last_fetched
            current_end = datetime.strptime(last_fetched, "%Y-%m-%d") - timedelta(days=1)
        else:
            current_end = end_date
        
        while current_end >= start_date:
            # Fetch data in configurable chunks, working backward
            current_start = max(current_end - timedelta(days=config.HISTORICAL_CHUNK_DAYS - 1), start_date)
            start_str = current_start.strftime("%Y-%m-%d")
            end_str = current_end.strftime("%Y-%m-%d")
            
            print(f"Fetching historical data for {start_str} to {end_str}...")
            
            try:
                # Fetch the data chunk
                df = fetch_usaspending_chunk(start_str, end_str)
                
                if df.empty:
                    logger.warning(f"No data returned for {start_str} to {end_str}")
                    print(f"No data returned for {start_str} to {end_str}, continuing to next chunk...")
                else:
                    # Add source information
                    df['data_source'] = 'USAspending.gov Historical'
                    df['fetch_date'] = datetime.now().strftime("%Y-%m-%d")
                    df['chunk_start_date'] = start_str
                    df['chunk_end_date'] = end_str
                    
                    # Store in database
                    success = database.insert_dataframe(
                        df=df,
                        table_name=config.TABLE_HISTORICAL_USASPENDING,
                        if_exists='append'
                    )
                    
                    if success:
                        print(f"Successfully stored {len(df)} records for {start_str} to {end_str}")
                        
                        # Save CSV to archive
                        csv_filename = f"usaspending_{start_str}_to_{end_str}.csv"
                        csv_path = os.path.join(config.ARCHIVE_DIR, csv_filename)
                        df.to_csv(csv_path, index=False)
                        print(f"Archived CSV to {csv_path}")
                        
                        # Update the last fetched date (store the earliest date of the chunk)
                        database.update_last_fetched_date(
                            config.TABLE_HISTORICAL_USASPENDING, 
                            current_start.strftime("%Y-%m-%d")
                        )
                    else:
                        logger.error(f"Failed to store data for {start_str} to {end_str}")
                        print(f"Failed to store data for {start_str} to {end_str}, continuing...")
                
            except Exception as e:
                logger.error(f"Error processing chunk {start_str} to {end_str}: {str(e)}")
                print(f"Error processing chunk {start_str} to {end_str}: {str(e)}")
                # Continue to the next chunk instead of stopping
            
            # Move to the next chunk back in time
            current_end = current_start - timedelta(days=1)
        
        print("Historical USAspending fetch completed")
        return True
        
    except Exception as e:
        logger.error(f"USAspending historical fetch failed: {str(e)}")
        print(f"Failed to fetch USAspending historical data: {str(e)}")
        return False

def count_historical_records() -> Tuple[bool, int]:
    """
    Count total records in the historical USAspending database.
    
    Returns:
        Tuple[bool, int]: Success flag and count of records
    """
    try:
        engine = database.get_engine()
        with engine.connect() as connection:
            result = connection.execute(f"SELECT COUNT(*) FROM {config.TABLE_HISTORICAL_USASPENDING}")
            count = result.scalar()
            print(f"Total records in historical USAspending database: {count}")
            return True, count
    except Exception as e:
        logger.error(f"Failed to count historical records: {str(e)}")
        print(f"Failed to count historical records: {str(e)}")
        return False, 0

if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(
        filename=f"{config.LOGS_DIR}/usaspending_historical.log",
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    success = fetch_usaspending_historical()
    if success:
        print("Historical USAspending data fetch completed successfully.")
        success, count = count_historical_records()
        if success:
            print(f"Total historical records: {count}")
    else:
        print("Historical USAspending data fetch failed.")
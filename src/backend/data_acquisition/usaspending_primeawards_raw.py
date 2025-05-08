# usaspending_historical_pg.py
"""
Enhanced USAspending.gov historical data acquisition script with PostgreSQL support.

This script fetches historical contract award data from USAspending.gov using
their bulk download API and stores it in a PostgreSQL database for further analysis.
It includes improved pagination, enhanced logging, and better error handling.
"""

import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
import logging
import time
import zipfile
import io
import shutil
import json
from pathlib import Path
import psycopg2
from psycopg2 import sql
from psycopg2.extras import execute_values
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import requests.exceptions
from tqdm import tqdm
import sys
from typing import Dict, List, Optional, Tuple, Union, Any

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))
import config

# Configure rich and colorful logging
def setup_logging(log_file: str = 'logs/usaspending_historical.log'):
    """Set up enhanced logging with formatting."""
    # Create logs directory if it doesn't exist
    log_dir = os.path.dirname(log_file)
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Configure logger
    logger = logging.getLogger("usaspending_historical")
    logger.setLevel(logging.INFO)
    
    # Clear existing handlers
    if logger.handlers:
        logger.handlers.clear()
    
    # Create file handler
    file_handler = logging.FileHandler(log_file)
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(file_formatter)
    
    # Create console handler with a cleaner formatter (no duplicate info)
    console_handler = logging.StreamHandler()
    console_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(console_formatter)
    
    # Add handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    # Prevent propagation to root logger (this avoids duplicate messages)
    logger.propagate = False
    
    # Disable the root logger handlers to prevent duplicate logging
    root_logger = logging.getLogger()
    root_logger.handlers = []
    
    return logger

# Set up logging
logger = setup_logging()

# FEATURE: Constants
USASPENDING_API_URL = "https://api.usaspending.gov/api/v2/bulk_download/awards/"
CUSTOM_ARCHIVE_DIR = r'D:\Github - Working\archive'  # Custom archive location as specified
REQUEST_TIMEOUT = 60  # Increased timeout
DOWNLOAD_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}
MAX_WAIT_SECONDS = 900  # 15 minutes maximum wait time
MAX_CONSECUTIVE_FAILURES = 3  # Maximum number of consecutive failures before backing off
CHUNK_DAYS = 7  # Increased from 2 to 7 days for faster processing

# Ensure archive directory exists
os.makedirs(CUSTOM_ARCHIVE_DIR, exist_ok=True)

# Target field list for our raw table - these are the exact fields we want from the API
TARGET_FIELDS = [
    "contract_transaction_unique_key",
    "contract_award_unique_key",
    "action_date_fiscal_year",
    "action_date",
    "parent_award_id_piid",
    "award_id_piid",
    "modification_number",
    "federal_action_obligation",
    "total_dollars_obligated",
    "potential_total_value_of_award",
    "total_outlayed_amount_for_overall_award",
    "period_of_performance_start_date",
    "period_of_performance_current_end_date",
    "period_of_performance_potential_end_date",
    "ordering_period_end_date",
    "primary_place_of_performance_city_name",
    "primary_place_of_performance_state_code",
    "prime_award_base_transaction_description",
    "transaction_description",
    "naics_code",
    "naics_description",
    "product_or_service_code",
    "product_or_service_code_description",
    "dod_acquisition_program_description",
    "parent_award_agency_name",
    "awarding_sub_agency_name",
    "awarding_office_name",
    "funding_agency_name",
    "funding_sub_agency_name",
    "funding_office_name",
    "recipient_name",
    "recipient_uei",
    "recipient_parent_name",
    "recipient_parent_uei",
    "solicitation_date",
    "solicitation_procedures", 
    "extent_competed",
    "type_of_set_aside",
    "fair_opportunity_limited_sources",
    "other_than_full_and_open_competition",
    "number_of_offers_received",
    "subcontracting_plan",
    "government_furnished_property",
    "type_of_contract_pricing",
    "action_type",
    "award_type",
    "type_of_idc",
    "idv_type",
    "undefinitized_action",
    "program_acronym",
    "multi_year_contract",
    "multiple_or_single_award_idv",
    "usaspending_permalink"
]

# DB Table name
TABLE_NAME = "usaspending_prime_awards_slim"

# FEATURE: PostgreSQL Database Connection
def get_db_connection():
    """
    Create a connection to the PostgreSQL database.
    Returns:
        Connection: PostgreSQL database connection
    """
    try:
        conn = psycopg2.connect(
            host=config.PG_HOST,
            port=config.PG_PORT,
            dbname=config.PG_DATABASE,
            user=config.PG_USER,
            password=config.PG_PASSWORD
        )
        logger.info("Connected to PostgreSQL database")
        return conn
    except Exception as e:
        logger.error(f"Error connecting to PostgreSQL database: {e}")
        raise

# FEATURE: Database Management Functions
def setup_progress_tracking(conn):
    """
    Create a dedicated usaspending_historical_progress table for tracking progress.
    This function will check if the table exists and preserve it if it does.
    Args:
        conn: PostgreSQL connection
    """
    cursor = conn.cursor()
    try:
        # Check if the table exists
        cursor.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_name = 'usaspending_historical_progress'
        )
        """)
        
        table_exists = cursor.fetchone()[0]
        
        if not table_exists:
            # Create a dedicated progress tracking table if it doesn't exist
            cursor.execute("""
            CREATE TABLE usaspending_historical_progress (
                id SERIAL PRIMARY KEY,
                last_fetched_date DATE,
                last_page_processed INTEGER DEFAULT 0,
                total_records_processed BIGINT DEFAULT 0,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            )
            """)
            
            # Insert initial record
            cursor.execute("""
            INSERT INTO usaspending_historical_progress 
            (last_fetched_date, status)
            VALUES (%s, %s)
            """, (None, 'pending'))
            
            conn.commit()
            logger.info("Created dedicated progress tracking table: usaspending_historical_progress")
        else:
            # Table exists, retrieve current progress
            cursor.execute("""
            SELECT last_fetched_date, status FROM usaspending_historical_progress WHERE id = 1
            """)
            result = cursor.fetchone()
            if result:
                logger.info(f"Found existing progress tracking with last fetch date: {result[0]}")
            else:
                logger.warning("Progress tracking table exists but has no records")
                
    except Exception as e:
        conn.rollback()
        logger.error(f"Error setting up progress tracking: {e}")
        raise
    finally:
        cursor.close()

def setup_awards_table(conn):
    """
    Create the usaspending_prime_awards_slim table if it doesn't exist.
    Uses dynamic column creation based on the columns we get from the API.
    Args:
        conn: PostgreSQL connection
    """
    cursor = conn.cursor()
    try:
        # First check if table exists
        cursor.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_name = %s
        )
        """, (TABLE_NAME,))
        
        table_exists = cursor.fetchone()[0]
        
        if not table_exists:
            # Create a simple table with TEXT columns for all fields
            columns = []
            for field in TARGET_FIELDS:
                # contract_transaction_unique_key is our primary key
                if field == "contract_transaction_unique_key":
                    columns.append(f"{field} TEXT PRIMARY KEY")
                else:
                    columns.append(f"{field} TEXT")
            
            # Add tracking columns
            columns.append("created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP")
            columns.append("updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP")
            columns.append("fetch_date DATE")
            
            # Join columns and create table
            columns_sql = ", ".join(columns)
            cursor.execute(f"""
            CREATE TABLE {TABLE_NAME} (
                {columns_sql}
            )
            """)
            
            conn.commit()
            logger.info(f"Created table {TABLE_NAME}")
        else:
            logger.info(f"Table {TABLE_NAME} already exists")
            
    except Exception as e:
        conn.rollback()
        logger.error(f"Error creating awards table: {e}")
        raise
    finally:
        cursor.close()

def get_last_fetched_progress(conn):
    """
    Get the last fetched date and page from the progress table.
    Args:
        conn: PostgreSQL connection
    Returns:
        tuple: (last_fetched_date, last_page_processed)
    """
    cursor = conn.cursor()
    try:
        cursor.execute("""
        SELECT last_fetched_date, last_page_processed
        FROM usaspending_historical_progress
        WHERE id = 1
        """)
        result = cursor.fetchone()
        
        if result and result[0]:
            # Convert date to datetime for consistency
            fetched_date = result[0]
            if hasattr(fetched_date, 'year') and not hasattr(fetched_date, 'hour'):
                # It's a date but not a datetime
                fetched_date = datetime.combine(fetched_date, datetime.min.time())
                logger.info(f"Converted date {result[0]} to datetime {fetched_date}")
            return fetched_date, result[1]
        return None, 0
    except Exception as e:
        logger.error(f"Error retrieving last fetched progress: {e}")
        return None, 0
    finally:
        cursor.close()

def update_fetch_progress(conn, date=None, page=0, records=0, status='in_progress'):
    """
    Update the fetch progress in the database.
    Args:
        conn: PostgreSQL connection
        date: Date that was fetched
        page: Last page processed
        records: Records processed in this batch
        status: Current status of the process
    """
    cursor = conn.cursor()
    try:
        if date:
            cursor.execute("""
            UPDATE usaspending_historical_progress
            SET last_fetched_date = %s,
                last_page_processed = %s,
                total_records_processed = total_records_processed + %s,
                status = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = 1
            """, (date, page, records, status))
        else:
            cursor.execute("""
            UPDATE usaspending_historical_progress
            SET last_page_processed = %s,
                total_records_processed = total_records_processed + %s,
                status = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = 1
            """, (page, records, status))
        
        conn.commit()
    except Exception as e:
        conn.rollback()
        logger.error(f"Error updating fetch progress: {e}")
    finally:
        cursor.close()

# FEATURE: Data Fetching with Improved Error Handling
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=30),
    retry=retry_if_exception_type((requests.exceptions.RequestException,)),
    before_sleep=lambda retry_state: logger.info(f"Retrying USAspending fetch (attempt {retry_state.attempt_number})...")
)
def request_usaspending_download(start_str, end_str):
    """
    Request a bulk download from USAspending.gov API.
    Args:
        start_str: Start date string (YYYY-MM-DD)
        end_str: End date string (YYYY-MM-DD)
    Returns:
        tuple: (status_url, file_url)
    """
    payload = {
        "filters": {
            "prime_award_types": [
                "A", "B", "C", "D", "IDV_A", "IDV_B", "IDV_B_A", "IDV_B_B", 
                "IDV_B_C", "IDV_C", "IDV_D", "IDV_E"
            ],
            "date_type": "action_date",
            "date_range": {
                "start_date": start_str,
                "end_date": end_str
            },
            "agencies": [
                {
                    "type": "awarding",
                    "tier": "toptier",
                    "name": "All"
                }
            ]
        },
        "file_format": "csv",
        "columns": TARGET_FIELDS  # Only request the columns we need
    }
    
    logger.info(f"Requesting USAspending data for {start_str} to {end_str}")
    response = requests.post(USASPENDING_API_URL, json=payload, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()
    result = response.json()
    
    status_url = result.get("status_url")
    file_url = result.get("file_url")
    
    if not status_url or not file_url:
        raise ValueError("No download URL or status URL returned from USAspending API")
    
    logger.info(f"Request submitted successfully. Status URL: {status_url}")
    return status_url, file_url

def wait_for_file_generation(status_url):
    """
    Check the status until the file is ready for download.
    Args:
        status_url: URL to check generation status
    Returns:
        bool: True if file is ready, False otherwise
    """
    max_status_attempts = 60  # Increased from 20
    wait_seconds = 30
    total_waited = 0
    
    logger.info("Waiting for file generation to complete...")
    progress_bar = tqdm(total=100, desc="File Generation", ncols=100)
    last_pct = 0
    
    for attempt in range(max_status_attempts):
        if total_waited >= MAX_WAIT_SECONDS:
            logger.error(f"USAspending file not ready after waiting {total_waited} seconds")
            return False
        
        try:
            status_response = requests.get(status_url, timeout=REQUEST_TIMEOUT)
            status_response.raise_for_status()
            
            # Get status data, handle case where response might be invalid
            try:
                status_data = status_response.json()
            except Exception as e:
                logger.warning(f"Failed to parse JSON response: {e}")
                logger.warning(f"Raw response: {status_response.text[:200]}")
                status_data = {}
            
            # More defensive handling of response data
            if not status_data:
                logger.warning("Empty or null response from status API")
                time.sleep(wait_seconds)
                total_waited += wait_seconds
                continue
                
            # Check status first before trying to access percent_complete
            status = status_data.get("status")
            
            # If status is finished, we're done
            if status == "finished":
                progress_bar.update(100 - last_pct)  # Complete the progress bar
                progress_bar.close()
                logger.info("File generation completed successfully")
                return True
                
            # Try to get percentage, with multiple fallback paths
            current_pct = 0
            message_obj = status_data.get("message", {})
            
            # Handle different response formats
            if isinstance(message_obj, dict):
                current_pct = int(message_obj.get("percent_complete", 0))
            elif isinstance(message_obj, str):
                # Try to extract percentage from string if it contains a number
                logger.debug(f"Message is string: {message_obj}")
                if "%" in message_obj:
                    try:
                        current_pct = int(message_obj.split("%")[0].strip().split()[-1])
                    except (ValueError, IndexError):
                        current_pct = 0
            
            # Update progress bar if needed
            if current_pct > last_pct:
                progress_bar.update(current_pct - last_pct)
                last_pct = current_pct
            
            # Log detailed status information
            logger.debug(f"Status check {attempt + 1}: {status_data}")
            logger.info(f"File generation in progress: {current_pct}% complete, waited {total_waited}s, status: {status}")
            
            # If we have an error status, log it and keep waiting
            if status == "failed" or status == "error":
                error_message = str(message_obj) if message_obj else "Unknown error"
                logger.warning(f"File generation encountered an issue: {error_message}")
                
            time.sleep(wait_seconds)
            total_waited += wait_seconds
            
        except Exception as e:
            logger.error(f"Error checking status: {e}")
            time.sleep(wait_seconds)
            total_waited += wait_seconds
    
    progress_bar.close()
    logger.error(f"File not ready after {max_status_attempts} status checks")
    return False

def download_and_process_file(file_url, start_str, end_str):
    """
    Download the generated file and process it.
    Args:
        file_url: URL to download the file
        start_str: Start date string for naming
        end_str: End date string for naming
    Returns:
        DataFrame: Raw data as DataFrame
    """
    max_download_attempts = 10
    
    # Create a progress bar for the download
    logger.info("Downloading generated file...")
    
    for attempt in range(max_download_attempts):
        try:
            # Stream download with progress indication
            file_response = requests.get(file_url, headers=DOWNLOAD_HEADERS, timeout=REQUEST_TIMEOUT, stream=True)
            file_response.raise_for_status()
            
            # Get content length if available
            total_size = int(file_response.headers.get('content-length', 0))
            
            # Initialize progress bar
            progress_bar = tqdm(total=total_size, unit='B', unit_scale=True, desc="Downloading")
            
            # Download file with progress updates
            content = io.BytesIO()
            for data in file_response.iter_content(chunk_size=1024):
                progress_bar.update(len(data))
                content.write(data)
            
            progress_bar.close()
            content.seek(0)
            break
        except Exception as e:
            logger.error(f"Download attempt {attempt + 1} failed: {e}")
            if attempt < max_download_attempts - 1:
                time.sleep(15)
            else:
                raise ValueError("Failed to download file after multiple attempts")
    
    # Archive the downloaded file
    csv_filename = f"usaspending_{start_str}_to_{end_str}.csv"
    archive_path = os.path.join(CUSTOM_ARCHIVE_DIR, csv_filename)
    
    # Extract the zip file
    logger.info("Extracting and processing downloaded file...")
    try:
        with zipfile.ZipFile(content) as z:
            csv_files = [f for f in z.namelist() if f.endswith('.csv')]
            if not csv_files:
                raise ValueError("No CSV files found in the USAspending zip file")
                
            # Save the CSV to the archive folder
            with z.open(csv_files[0]) as csv_file:
                with open(archive_path, 'wb') as f:
                    shutil.copyfileobj(csv_file, f)
                logger.info(f"Saved CSV backup to: {archive_path}")
                
            # Read the CSV into a DataFrame without any transformations
            with z.open(csv_files[0]) as csv_file:
                df = pd.read_csv(csv_file, low_memory=False)
                logger.info(f"Loaded {len(df)} records from CSV")
                
                # Add fetch date only
                df['fetch_date'] = datetime.now().strftime('%Y-%m-%d')
                
                return df
    except Exception as e:
        logger.error(f"Error extracting or processing zip file: {e}")
        raise

def insert_into_postgres(conn, df, batch_size=5000):
    """
    Insert raw data into PostgreSQL with batching and proper error handling.
    Args:
        conn: PostgreSQL connection
        df: DataFrame to insert
        batch_size: Number of records per batch insertion
    """
    cursor = conn.cursor()
    
    try:
        # Prepare for batch processing
        total_records = len(df)
        batches = (total_records // batch_size) + (1 if total_records % batch_size > 0 else 0)
        
        logger.info(f"Inserting {total_records} records into {TABLE_NAME} in {batches} batches")
        
        # Create progress bar
        progress_bar = tqdm(total=total_records, desc="DB Insert", unit="records")
        
        # Process in batches
        for i in range(0, total_records, batch_size):
            batch_df = df.iloc[i:i+batch_size]
            
            # Get column names from the dataframe
            columns = [col for col in batch_df.columns]
            
            # Create column list and SQL for insertion
            columns_sql = ', '.join([f'"{col}"' for col in columns])
            placeholders = ', '.join(['%s'] * len(columns))
            
            # Handle conflicts - update if record exists
            on_conflict = """
            ON CONFLICT (contract_transaction_unique_key) 
            DO UPDATE SET 
                updated_at = CURRENT_TIMESTAMP,
                fetch_date = EXCLUDED.fetch_date
            """
            
            # Prepare SQL
            insert_sql = f"""
            INSERT INTO {TABLE_NAME} ({columns_sql})
            VALUES ({placeholders})
            {on_conflict}
            """
            
            # Convert DataFrame to list of tuples
            rows = [tuple(row) for row in batch_df[columns].replace({np.nan: None}).values]
            
            # Execute with batch insert
            cursor.executemany(insert_sql, rows)
            conn.commit()
            
            # Update progress
            progress_bar.update(len(batch_df))
        
        progress_bar.close()
        logger.info(f"Successfully inserted {total_records} records into {TABLE_NAME}")
        
        return total_records
    except Exception as e:
        conn.rollback()
        logger.error(f"Error inserting data into PostgreSQL: {e}")
        raise
    finally:
        cursor.close()

# FEATURE: Advanced Fetch with Date Chunking
def fetch_historical_chunk(conn, start_date, end_date, page=0):
    """
    Fetch a chunk of historical USAspending data.
    Args:
        conn: PostgreSQL connection
        start_date: Start date as datetime
        end_date: End date as datetime
        page: Current page number (not used for pagination, kept for compatibility)
    Returns:
        tuple: (records_processed, current_page, success)
    """
    records_processed = 0
    current_page = page
    
    try:
        # Format dates for API
        start_str = start_date.strftime("%Y-%m-%d")
        end_str = end_date.strftime("%Y-%m-%d")
        
        # Step 1: Request the download
        status_url, file_url = request_usaspending_download(start_str, end_str)
        
        # Step 2: Wait for file generation
        if not wait_for_file_generation(status_url):
            logger.error(f"File generation timed out for {start_str} to {end_str}")
            return records_processed, current_page, False
        
        # Step 3: Download and process the file (no transformations)
        df = download_and_process_file(file_url, start_str, end_str)
        
        # Step 4: Insert raw data into PostgreSQL
        records_processed = insert_into_postgres(conn, df)
        
        logger.info(f"Successfully processed {records_processed} records for {start_str} to {end_str}")
        return records_processed, current_page + 1, True
        
    except Exception as e:
        logger.error(f"Error in fetch_historical_chunk: {e}")
        return records_processed, current_page, False

# FEATURE: Main Function with Enhanced Progress Tracking
def fetch_usaspending_historical():
    """Main function to fetch historical USAspending data with enhanced tracking."""
    conn = None
    consecutive_failures = 0
    
    try:
        logger.info("Starting USAspending historical data acquisition")
        logger.info(f"Using archive directory: {CUSTOM_ARCHIVE_DIR}")
        
        # Define date range - adjusted to start from 2022-02-02 and go back to 2012-09-30
        start_date = datetime.strptime("2022-01-27", "%Y-%m-%d")
        end_date = datetime.strptime("2025-04-30", "%Y-%m-%d")
        
        logger.info(f"Date range set: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
        
        # Connect to PostgreSQL
        conn = get_db_connection()
        
        # Set up tables
        setup_progress_tracking(conn)
        setup_awards_table(conn)
        
        # Get last fetched progress
        last_fetched_date, last_page = get_last_fetched_progress(conn)
        
        # If we have a last fetched date, start from there
        if last_fetched_date:
            logger.info(f"Resuming from last fetched date: {last_fetched_date}")
            # Subtract one day to ensure overlap and no missed data
            current_end = last_fetched_date - timedelta(days=1)
        else:
            # If no previous fetch, start from the end date (2022-02-02)
            current_end = end_date
            logger.info(f"Starting new fetch from {current_end.strftime('%Y-%m-%d')}")
        
        # Create a progress bar for the entire date range
        total_days = (current_end - start_date).days
        with tqdm(total=total_days, desc="Overall Progress", unit="days") as progress_bar:
            # Process in chunks, working backward
            while current_end >= start_date:
                try:
                    # Calculate chunk start date (7 days at a time)
                    current_start = max(current_end - timedelta(days=CHUNK_DAYS - 1), start_date)
                    chunk_days = (current_end - current_start).days + 1
                    
                    logger.info(f"Processing chunk: {current_start.strftime('%Y-%m-%d')} to {current_end.strftime('%Y-%m-%d')} ({chunk_days} days)")
                    
                    # Fetch the chunk
                    records, page, success = fetch_historical_chunk(conn, current_start, current_end, last_page)
                    
                    if success:
                        # Update progress and reset failure counter
                        update_fetch_progress(conn, current_start, page, records, 'completed')
                        consecutive_failures = 0
                        
                        # Update progress bar
                        progress_bar.update(chunk_days)
                        
                        # Move to next chunk
                        current_end = current_start - timedelta(days=1)
                        last_page = 0  # Reset page for new date
                    else:
                        consecutive_failures += 1
                        if consecutive_failures >= MAX_CONSECUTIVE_FAILURES:
                            logger.error(f"Too many consecutive failures ({consecutive_failures}). Backing off...")
                            time.sleep(300)  # 5-minute backoff
                            consecutive_failures = 0
                        else:
                            logger.warning(f"Chunk failed. Retry {consecutive_failures}/{MAX_CONSECUTIVE_FAILURES}")
                            time.sleep(60)  # 1-minute delay between retries
                
                except KeyboardInterrupt:
                    logger.info("Process interrupted by user")
                    update_fetch_progress(conn, current_start, last_page, 0, 'interrupted')
                    return False
                except Exception as e:
                    logger.error(f"Error processing chunk: {e}")
                    if consecutive_failures >= MAX_CONSECUTIVE_FAILURES:
                        logger.error("Too many errors. Stopping process.")
                        update_fetch_progress(conn, current_start, last_page, 0, 'error')
                        return False
                    consecutive_failures += 1
                    time.sleep(60)  # Wait before retry
        
        # All done
        update_fetch_progress(conn, start_date, 0, 0, 'completed')
        logger.info("Historical data acquisition completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"USAspending historical fetch failed: {str(e)}")
        if conn:
            update_fetch_progress(conn, None, 0, 0, 'error')
        return False
        
    finally:
        if conn:
            conn.close()
            logger.info("Database connection closed")

if __name__ == "__main__":
    fetch_usaspending_historical()
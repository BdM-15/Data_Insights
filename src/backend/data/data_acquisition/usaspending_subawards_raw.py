# usaspending_subawards.py
"""
USAspending.gov subaward data acquisition script using bulk download API.

This script fetches subaward data from USAspending.gov using
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

# Configure logging
def setup_logging(log_file: str = 'logs/usaspending_subawards.log'):
    """Set up enhanced logging with formatting."""
    # Create logs directory if it doesn't exist
    log_dir = os.path.dirname(log_file)
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Configure logger
    logger = logging.getLogger("usaspending_subawards")
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
    
    return logger

# Set up logging
logger = setup_logging()

# CONSTANTS
USASPENDING_API_URL = "https://api.usaspending.gov/api/v2/bulk_download/awards/"
CUSTOM_ARCHIVE_DIR = r'D:\Github - Working\archive\subawards'  # Custom archive location as specified
REQUEST_TIMEOUT = 60  # Timeout for requests
DOWNLOAD_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}
MAX_WAIT_SECONDS = 900  # 15 minutes maximum wait time
MAX_CONSECUTIVE_FAILURES = 3  # Maximum number of consecutive failures before backing off
CHUNK_DAYS = 7  # Days per chunk for processing

# Ensure archive directory exists
os.makedirs(CUSTOM_ARCHIVE_DIR, exist_ok=True)

# DB Table name (fully qualified for s1_raw schema)
TABLE_NAME = "s1_raw.usaspending_subawards"

# Database Connection
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

# Database Management Functions
def setup_progress_tracking(conn):
    """
    Create a dedicated usaspending_subawards_progress table for tracking progress.
    Args:
        conn: PostgreSQL connection
    """
    cursor = conn.cursor()
    try:
        # Check if the table exists
        cursor.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_name = 'usaspending_subawards_progress'
        )
        """)
        
        table_exists = cursor.fetchone()[0]
        
        if not table_exists:
            # Create a dedicated progress tracking table if it doesn't exist
            cursor.execute("""
            CREATE TABLE usaspending_subawards_progress (
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
            INSERT INTO usaspending_subawards_progress 
            (last_fetched_date, status)
            VALUES (%s, %s)
            """, (None, 'pending'))
            
            conn.commit()
            logger.info("Created dedicated progress tracking table: usaspending_subawards_progress")
        else:
            # Table exists, retrieve current progress
            cursor.execute("""
            SELECT last_fetched_date, status FROM usaspending_subawards_progress WHERE id = 1
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
        FROM usaspending_subawards_progress
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
            UPDATE usaspending_subawards_progress
            SET last_fetched_date = %s,
                last_page_processed = %s,
                total_records_processed = total_records_processed + %s,
                status = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = 1
            """, (date, page, records, status))
        else:
            cursor.execute("""
            UPDATE usaspending_subawards_progress
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

def setup_subawards_table(conn):
    """
    Create the usaspending_subawards table if it doesn't exist.
    The table structure will be created dynamically based on the actual data received.
    Args:
        conn: PostgreSQL connection
    """
    cursor = conn.cursor()
    try:
        # First check if table exists
        cursor.execute(f"""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = 's1_raw' AND table_name = 'usaspending_subawards'
        )
        """)
        table_exists = cursor.fetchone()[0]
        if not table_exists:
            cursor.execute(f"""
            CREATE TABLE {TABLE_NAME} (
                id SERIAL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                fetch_date DATE
            )
            """)
            conn.commit()
            logger.info(f"Created initial table {TABLE_NAME}")
        else:
            logger.info(f"Table {TABLE_NAME} already exists")
            
    except Exception as e:
        conn.rollback()
        logger.error(f"Error creating subawards table: {e}")
        raise
    finally:
        cursor.close()

def ensure_columns_exist(conn, df):
    """
    Ensure all columns from the DataFrame exist in the database table.
    Args:
        conn: PostgreSQL connection
        df: DataFrame with data to insert
    """
    if df.empty:
        return
    
    # Get column names from the DataFrame
    df_columns = df.columns.tolist()
    
    cursor = conn.cursor()
    try:
        # Get existing columns from the database
        cursor.execute(f"""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_schema = 's1_raw' AND table_name = 'usaspending_subawards'
        """)
        
        existing_columns = [row[0] for row in cursor.fetchall()]
        
        # Add any missing columns
        for col in df_columns:
            if col.lower() not in [c.lower() for c in existing_columns]:
                # Add the column if it doesn't exist
                try:
                    cursor.execute(f"""
                    ALTER TABLE {TABLE_NAME} 
                    ADD COLUMN "{col}" TEXT
                    """)
                    logger.info(f"Added column '{col}' to {TABLE_NAME}")
                except Exception as e:
                    logger.warning(f"Could not add column {col}: {e}")
        
        conn.commit()
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Error ensuring columns exist: {e}")
        raise
    finally:
        cursor.close()

# Data Fetching with Improved Error Handling
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=60),
    retry=retry_if_exception_type((requests.exceptions.RequestException,)),
    before_sleep=lambda retry_state: logger.info(f"Retrying USAspending fetch (attempt {retry_state.attempt_number})...")
)
def request_subawards_download(start_str, end_str):
    """
    Request a bulk download of subawards from USAspending.gov API.
    Args:
        start_str: Start date string (YYYY-MM-DD)
        end_str: End date string (YYYY-MM-DD)
    Returns:
        tuple: (status_url, file_url)
    """
    payload = {
        "filters": {
            "sub_award_types": ["procurement"],  # Request only procurement subawards
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
        "file_format": "csv"
    }
    
    logger.info(f"Requesting USAspending subawards data for {start_str} to {end_str}")
    
    try:
        # Log the payload for debugging
        logger.debug(f"Request payload: {json.dumps(payload, indent=2)}")
        
        response = requests.post(USASPENDING_API_URL, json=payload, timeout=REQUEST_TIMEOUT)
        
        # Log response details for debugging
        logger.debug(f"Response status: {response.status_code}")
        
        # Try to get response content
        try:
            response_data = response.json()
            logger.debug(f"Response data: {json.dumps(response_data, indent=2)[:1000]}")
        except:
            logger.warning(f"Could not parse response as JSON: {response.text[:200]}")
            
        # Raise for HTTP errors
        response.raise_for_status()
        
        result = response.json()
        
        status_url = result.get("status_url")
        file_url = result.get("file_url")
        
        if not status_url or not file_url:
            raise ValueError(f"No download URL or status URL returned from USAspending API: {result}")
        
        logger.info(f"Request submitted successfully. Status URL: {status_url}")
        return status_url, file_url
        
    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP error occurred: {e}")
        logger.error(f"Response content: {e.response.text[:500]}")
        raise
    except Exception as e:
        logger.error(f"Error requesting download: {e}")
        raise

def wait_for_file_generation(status_url):
    """
    Check the status until the file is ready for download.
    Args:
        status_url: URL to check generation status
    Returns:
        bool: True if file is ready, False otherwise
    """
    # ...existing code...
    max_status_attempts = 60
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
    max_download_attempts = 5
    
    # Create a progress bar for the download
    logger.info("Downloading generated file...")
    
    for attempt in range(max_download_attempts):
        try:
            # Stream download with progress indication
            file_response = requests.get(file_url, headers=DOWNLOAD_HEADERS, timeout=REQUEST_TIMEOUT * 2, stream=True)
            file_response.raise_for_status()
            
            # Get content length if available
            total_size = int(file_response.headers.get('content-length', 0))
            
            # Initialize progress bar
            progress_bar = tqdm(total=total_size, unit='B', unit_scale=True, desc="Downloading")
            
            # Download file with progress updates
            content = io.BytesIO()
            for data in file_response.iter_content(chunk_size=1024 * 1024):  # 1MB chunks
                progress_bar.update(len(data))
                content.write(data)
            
            progress_bar.close()
            content.seek(0)
            break
        except Exception as e:
            logger.error(f"Download attempt {attempt + 1} failed: {e}")
            if attempt < max_download_attempts - 1:
                wait_time = (attempt + 1) * 60  # Exponential backoff
                logger.info(f"Waiting {wait_time} seconds before retrying...")
                time.sleep(wait_time)
            else:
                raise ValueError("Failed to download file after multiple attempts")
    
    # Extract and process the CSV file
    logger.info("Extracting and processing downloaded file...")
    try:
        with zipfile.ZipFile(content) as z:
            csv_files = [f for f in z.namelist() if f.endswith('.csv')]
            if not csv_files:
                raise ValueError("No CSV files found in the USAspending zip file")
            
            # Get CSV file info
            csv_info = z.getinfo(csv_files[0])
            csv_size = csv_info.file_size
            
            # Save the CSV to the archive folder with a formatted name
            csv_filename = f"usaspending_subawards_{start_str}_to_{end_str}.csv"
            csv_path = os.path.join(CUSTOM_ARCHIVE_DIR, csv_filename)
            
            with z.open(csv_files[0]) as csv_file:
                with open(csv_path, 'wb') as f:
                    logger.info(f"Saving extracted CSV ({csv_size:,} bytes) to: {csv_path}")
                    shutil.copyfileobj(csv_file, f)
                
            # Read the CSV into a DataFrame
            logger.info(f"Reading CSV data from: {csv_path}")
            df = pd.read_csv(csv_path, dtype=str, low_memory=False)
            
            # Just log the count of columns without printing them all
            logger.info(f"CSV contains {len(df.columns)} columns")
            
            # Add fetch date
            df['fetch_date'] = datetime.now().strftime('%Y-%m-%d')
            
            logger.info(f"Successfully loaded {len(df)} records from CSV")
            
            # We don't need to save the zip file
            logger.info(f"Skipping ZIP file storage to save space")
            
            return df
                
    except Exception as e:
        logger.error(f"Error extracting or processing zip file: {e}")
        raise

def insert_into_postgres(conn, df, batch_size=1000):
    """
    Insert raw data into PostgreSQL with batching and proper error handling.
    Args:
        conn: PostgreSQL connection
        df: DataFrame to insert
        batch_size: Number of records per batch insertion
    """
    if df.empty:
        logger.warning("No data to insert into PostgreSQL")
        return 0
    
    # Ensure all columns exist in the database table
    ensure_columns_exist(conn, df)
        
    cursor = conn.cursor()
    
    try:
        # Prepare for batch processing
        total_records = len(df)
        batches = (total_records // batch_size) + (1 if total_records % batch_size > 0 else 0)
        
        logger.info(f"Inserting {total_records} records into {TABLE_NAME} in {batches} batches")
        
        # Create progress bar
        progress_bar = tqdm(total=total_records, desc="DB Insert", unit="records")
        
        # Process in batches
        records_inserted = 0
        for i in range(0, total_records, batch_size):
            batch_df = df.iloc[i:i+batch_size]
            
            # Get column names from the dataframe
            columns = batch_df.columns.tolist()
            
            # Create SQL for insertion - simple insert with no conflict handling
            columns_sql = ', '.join([f'"{col}"' for col in columns])
            placeholders = ', '.join(['%s'] * len(columns))
            
            # Simple insert SQL without ON CONFLICT clause
            insert_sql = f"""
            INSERT INTO {TABLE_NAME} ({columns_sql})
            VALUES ({placeholders})
            """
            
            # Convert DataFrame to list of tuples
            rows = []
            for _, row in batch_df.iterrows():
                row_values = [row.get(col) if pd.notna(row.get(col)) else None for col in columns]
                rows.append(tuple(row_values))
            
            # Execute batch insert
            cursor.executemany(insert_sql, rows)
            conn.commit()
            
            # Update progress
            records_inserted += len(batch_df)
            progress_bar.update(len(batch_df))
        
        progress_bar.close()
        logger.info(f"Successfully inserted {records_inserted} records into {TABLE_NAME}")
        
        return records_inserted
    except Exception as e:
        conn.rollback()
        logger.error(f"Error inserting data into PostgreSQL: {e}")
        raise
    finally:
        cursor.close()

def fetch_subawards_chunk(conn, start_date, end_date):
    """
    Fetch a chunk of subawards data.
    Args:
        conn: PostgreSQL connection
        start_date: Start date as datetime
        end_date: End date as datetime
    Returns:
        tuple: (records_processed, success)
    """
    records_processed = 0
    
    try:
        # Format dates for API
        start_str = start_date.strftime("%Y-%m-%d")
        end_str = end_date.strftime("%Y-%m-%d")
        
        # Step 1: Request the download
        status_url, file_url = request_subawards_download(start_str, end_str)
        
        # Step 2: Wait for file generation
        if not wait_for_file_generation(status_url):
            logger.error(f"File generation timed out for {start_str} to {end_str}")
            return records_processed, False
        
        # Step 3: Download and process the file
        df = download_and_process_file(file_url, start_str, end_str)
        
        # Step 4: Insert raw data into PostgreSQL
        records_processed = insert_into_postgres(conn, df)
        
        logger.info(f"Successfully processed {records_processed} records for {start_str} to {end_str}")
        return records_processed, True
        
    except Exception as e:
        logger.error(f"Error in fetch_subawards_chunk: {e}")
        return records_processed, False

def fetch_subawards_historical(start_date_str="2012-10-01", end_date_str="2025-04-30"):
    """
    Main function to fetch historical USAspending subawards data.
    Args:
        start_date_str: Start date string (YYYY-MM-DD)
        end_date_str: End date string (YYYY-MM-DD)
    """
    conn = None
    consecutive_failures = 0
    
    try:
        logger.info("Starting USAspending subawards data acquisition")
        logger.info(f"Using archive directory: {CUSTOM_ARCHIVE_DIR}")
        
        # Define date range
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d")
        
        logger.info(f"Date range set: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
        
        # Connect to PostgreSQL
        conn = get_db_connection()
        
        # Set up tables
        setup_progress_tracking(conn)
        setup_subawards_table(conn)
        
        # Get last fetched progress
        last_fetched_date, _ = get_last_fetched_progress(conn)
        
        # If we have a last fetched date, start from there
        if last_fetched_date:
            logger.info(f"Resuming from last fetched date: {last_fetched_date}")
            # Add one day to ensure we start from the next period
            current_start = last_fetched_date + timedelta(days=1)
        else:
            # If no previous fetch, start from the start date
            current_start = start_date
            logger.info(f"Starting new fetch from {current_start.strftime('%Y-%m-%d')}")
        
        # Create a progress bar for the entire date range
        total_days = (end_date - current_start).days + 1
        with tqdm(total=total_days, desc="Overall Progress", unit="days") as progress_bar:
            # Process in chunks
            while current_start <= end_date:
                try:
                    # Calculate chunk end date
                    current_end = min(current_start + timedelta(days=CHUNK_DAYS - 1), end_date)
                    chunk_days = (current_end - current_start).days + 1
                    
                    logger.info(f"Processing chunk: {current_start.strftime('%Y-%m-%d')} to {current_end.strftime('%Y-%m-%d')} ({chunk_days} days)")
                    
                    # Fetch the chunk
                    records, success = fetch_subawards_chunk(conn, current_start, current_end)
                    
                    if success:
                        # Update progress and reset failure counter
                        update_fetch_progress(conn, current_end, 0, records, 'completed')
                        consecutive_failures = 0
                        
                        # Update progress bar
                        progress_bar.update(chunk_days)
                        
                        # Move to next chunk
                        current_start = current_end + timedelta(days=1)
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
                    update_fetch_progress(conn, current_start, 0, 0, 'interrupted')
                    return False
                except Exception as e:
                    logger.error(f"Error processing chunk: {e}")
                    if consecutive_failures >= MAX_CONSECUTIVE_FAILURES:
                        logger.error("Too many errors. Stopping process.")
                        update_fetch_progress(conn, current_start, 0, 0, 'error')
                        return False
                    consecutive_failures += 1
                    time.sleep(60)  # Wait before retry
        
        # All done
        update_fetch_progress(conn, end_date, 0, 0, 'completed')
        logger.info("Subawards data acquisition completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"USAspending subawards fetch failed: {str(e)}")
        if conn:
            update_fetch_progress(conn, None, 0, 0, 'error')
        return False
        
    finally:
        if conn:
            conn.close()
            logger.info("Database connection closed")

if __name__ == "__main__":
    fetch_subawards_historical()
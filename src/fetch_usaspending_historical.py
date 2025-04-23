# fetch_usaspending_historical.py

import requests
import pandas as pd
from datetime import datetime, timedelta
import os
import logging
import time
import sqlite3
import zipfile
import io
import shutil
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import requests.exceptions

# FEATURE: Ensure Log File Exists
def ensure_log_file_exists(log_file_path):
    folder_path = os.path.dirname(log_file_path)
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
        print(f"Created folder: {folder_path}")
    if not os.path.exists(log_file_path):
        with open(log_file_path, 'w') as f:
            pass
        print(f"Created log file: {log_file_path}")

# Set up logging
ensure_log_file_exists('logs/errors.log')
logging.basicConfig(filename='logs/errors.log', level=logging.INFO,
                    format='%(asctime)s - %(message)s')
logger = logging.getLogger()

# FEATURE: Constants
USASPENDING_API_URL = "https://api.usaspending.gov/api/v2/bulk_download/awards/"
DATA_DIR = r'C:\GitHub\Data_Insights\data'
ARCHIVE_DIR = os.path.join(DATA_DIR, "archive")  # Archive folder for CSVs
USASPENDING_DB = os.path.join(DATA_DIR, "usaspending_historical.db")
REQUEST_TIMEOUT = 30
DOWNLOAD_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}
MAX_WAIT_SECONDS = 900  # 15 minutes maximum wait time
CHUNK_DAYS = 2  # 2-day chunks
CLEAR_DATABASE = False  # Set to True for the first run, False for subsequent runs

# Ensure archive directory exists
os.makedirs(ARCHIVE_DIR, exist_ok=True)

# FEATURE: Set up SQLite Database
def setup_sqlite_db():
    # Clear the database if CLEAR_DATABASE is True
    if CLEAR_DATABASE and os.path.exists(USASPENDING_DB):
        os.remove(USASPENDING_DB)
        print(f"Cleared existing database: {USASPENDING_DB}")
    
    conn = sqlite3.connect(USASPENDING_DB)
    cursor = conn.cursor()
    
    # Create a table to store the last fetched date
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS fetch_progress (
        id INTEGER PRIMARY KEY,
        last_fetched_date TEXT
    )
    """)
    conn.commit()
    
    return conn, cursor

# FEATURE: Get the last fetched date
def get_last_fetched_date(cursor):
    cursor.execute("SELECT last_fetched_date FROM fetch_progress WHERE id = 1")
    result = cursor.fetchone()
    if result and result[0]:
        return datetime.strptime(result[0], "%Y-%m-%d")
    return None

# FEATURE: Update the last fetched date
def update_last_fetched_date(cursor, conn, date):
    cursor.execute("INSERT OR REPLACE INTO fetch_progress (id, last_fetched_date) VALUES (1, ?)", (date.strftime("%Y-%m-%d"),))
    conn.commit()

# FEATURE: Fetch USAspending.gov Data - Historical pull in 2-day chunks
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    retry=retry_if_exception_type((requests.exceptions.RequestException,)),
    before_sleep=lambda retry_state: print(f"Retrying USAspending fetch (attempt {retry_state.attempt_number})...")
)
def fetch_usaspending_chunk(start_str, end_str):
    payload = {
        "filters": {
            "prime_award_types": [
                "A", "B", "C", "D", "IDV_A", "IDV_B", "IDV_B_A", "IDV_B_B", 
                "IDV_B_C", "IDV_C", "IDV_D", "IDV_E", "02", "03", "04", "05", 
                "06", "07", "08", "09", "10", "11", "-1"
            ],
            "date_type": "action_date",
            "date_range": {
                "start_date": start_str,
                "end_date": end_str
            }
        },
        "file_format": "csv"
    }
    print(f"Sending USAspending request to URL: {USASPENDING_API_URL}")
    print(f"Payload for {start_str} to {end_str}: {payload}")
    response = requests.post(USASPENDING_API_URL, json=payload, timeout=REQUEST_TIMEOUT)
    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        print(f"USAspending request failed with status {response.status_code}: {response.text}")
        logger.error(f"USAspending request failed with status {response.status_code}: {response.text}")
        raise e
    result = response.json()
    print(f"USAspending response for {start_str} to {end_str}: {result}")
    
    status_url = result.get("status_url")
    download_url = result.get("file_url")
    if not download_url or not status_url:
        raise ValueError("No download URL or status URL returned from USAspending API")
    
    # Check the status until the file is ready
    max_status_attempts = 20
    wait_seconds = 30
    total_waited = 0
    for attempt in range(max_status_attempts):
        if total_waited >= MAX_WAIT_SECONDS:
            raise ValueError(f"USAspending file not ready after waiting {total_waited} seconds (max: {MAX_WAIT_SECONDS} seconds)")
        
        status_response = requests.get(status_url, timeout=REQUEST_TIMEOUT)
        status_response.raise_for_status()
        status_data = status_response.json()
        print(f"Status check {attempt + 1} for {start_str} to {end_str}: {status_data}")
        if status_data.get("status") == "finished":
            break
        # Handle case where seconds_elapsed is "None" (string) or None (NoneType)
        seconds_elapsed_str = status_data.get("seconds_elapsed", "0")
        if seconds_elapsed_str is None or seconds_elapsed_str == "None":
            seconds_elapsed = 0.0
        else:
            try:
                seconds_elapsed = float(seconds_elapsed_str)
            except (ValueError, TypeError) as e:
                logger.error(f"Invalid seconds_elapsed value: {seconds_elapsed_str}. Setting to 0.0. Error: {str(e)}")
                seconds_elapsed = 0.0
        print(f"File not ready (status: {status_data.get('status')}, seconds_elapsed: {seconds_elapsed}), waiting {wait_seconds} seconds...")
        time.sleep(wait_seconds)
        total_waited += wait_seconds
    else:
        raise ValueError(f"USAspending file not ready after {max_status_attempts} status checks (total waited: {total_waited} seconds)")
    
    # Download the zip file
    max_download_attempts = 10
    for attempt in range(max_download_attempts):
        print(f"Attempt {attempt + 1}: Downloading USAspending data from: {download_url}")
        file_response = requests.get(download_url, headers=DOWNLOAD_HEADERS, timeout=REQUEST_TIMEOUT)
        if file_response.status_code == 200:
            break
        print(f"Download failed (status {file_response.status_code}), waiting 15 seconds...")
        time.sleep(15)
    else:
        raise ValueError("Failed to download USAspending file after multiple attempts")
    
    # Extract the zip file
    zip_file = io.BytesIO(file_response.content)
    with zipfile.ZipFile(zip_file, 'r') as z:
        csv_files = [f for f in z.namelist() if f.endswith('.csv')]
        if not csv_files:
            raise ValueError("No CSV files found in the USAspending zip file")
        
        # Save the CSV to the archive folder
        csv_filename = f"usaspending_{start_str}_to_{end_str}.csv"
        csv_path = os.path.join(ARCHIVE_DIR, csv_filename)
        with z.open(csv_files[0]) as csv_file:
            with open(csv_path, 'wb') as f:
                shutil.copyfileobj(csv_file, f)
            print(f"Saved CSV to archive: {csv_path}")
        
        # Read the CSV into a DataFrame
        with z.open(csv_files[0]) as csv_file:
            df = pd.read_csv(csv_file, low_memory=False)
    
    if 'award_id' in df.columns:
        df['UniqueID'] = df['award_id'].astype(str)
    else:
        df['UniqueID'] = df.index.astype(str)
    
    return df

# FEATURE: Insert Data into SQLite
def insert_into_sqlite(df, conn, cursor, table_created):
    # Replace invalid characters in column names (e.g., spaces, slashes) with underscores
    df.columns = [col.replace(' ', '_').replace('/', '_').replace('(', '').replace(')', '') for col in df.columns]
    
    # If the table hasn't been created yet, create it based on the first chunk's columns
    if not table_created[0]:
        columns = ', '.join([f'"{col}" TEXT' for col in df.columns])
        create_table_query = f"""
        CREATE TABLE IF NOT EXISTS awards (
            {columns}
        )
        """
        cursor.execute(create_table_query)
        conn.commit()
        table_created[0] = True
    
    # Insert the data into the table (no deduplication)
    placeholders = ', '.join(['?' for _ in df.columns])
    columns = ', '.join([f'"{col}"' for col in df.columns])
    insert_query = f"INSERT INTO awards ({columns}) VALUES ({placeholders})"
    
    # Convert DataFrame to list of tuples for insertion
    records = [tuple(row) for row in df.to_numpy()]
    cursor.executemany(insert_query, records)
    conn.commit()
    
    # Count total records after insertion
    cursor.execute("SELECT COUNT(*) FROM awards")
    total_records = cursor.fetchone()[0]
    print(f"Inserted {len(records)} records into SQLite database. Total records: {total_records}")

def fetch_usaspending_historical():
    try:
        print(f"Storing database at: {USASPENDING_DB}")
        print(f"Archiving CSVs at: {ARCHIVE_DIR}")
        
        start_date = datetime.strptime("2019-03-29", "%Y-%m-%d")
        end_date = datetime.strptime("2025-04-10", "%Y-%m-%d")
        
        # Set up SQLite database
        conn, cursor = setup_sqlite_db()
        table_created = [False]  # Use a list to allow modification in the function
        
        # Get the last fetched date (if any)
        last_fetched = get_last_fetched_date(cursor)
        if last_fetched:
            print(f"Resuming from last fetched date: {last_fetched.strftime('%Y-%m-%d')}")
            current_end = last_fetched - timedelta(days=1)
        else:
            current_end = end_date
        
        while current_end >= start_date:
            # Fetch 2 days at a time, working backward
            current_start = max(current_end - timedelta(days=CHUNK_DAYS - 1), start_date)
            start_str = current_start.strftime("%Y-%m-%d")
            end_str = current_end.strftime("%Y-%m-%d")
            
            print(f"Fetching historical data for {start_str} to {end_str}...")
            # Stop on failure instead of skipping
            df = fetch_usaspending_chunk(start_str, end_str)
            
            # Insert the chunk into SQLite
            insert_into_sqlite(df, conn, cursor, table_created)
            
            # Update the last fetched date (store the earliest date of the chunk)
            update_last_fetched_date(cursor, conn, current_start)
            
            current_end = current_start - timedelta(days=1)
        
        # Count total records in the database
        cursor.execute("SELECT COUNT(*) FROM awards")
        total_records = cursor.fetchone()[0]
        print(f"Total records in SQLite database: {total_records}")
        
        conn.close()
        return True
    except Exception as e:
        logger.error(f"USAspending historical fetch failed: {str(e)}")
        print(f"Failed to fetch USAspending historical data: {str(e)}. Stopping script. Rerun to retry the failed chunk.")
        if 'conn' in locals():
            conn.close()
        raise  # Re-raise the exception to stop the script
        return False

if __name__ == "__main__":
    fetch_usaspending_historical()
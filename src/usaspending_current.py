"""
USAspending.gov current data fetching module.
Fetches recent contract award data from USAspending.gov API and stores in the database.
"""

from typing import List, Dict, Any, Optional, Tuple
import logging
import time
import zipfile
import io
import requests
import pandas as pd
from datetime import datetime, timedelta
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type, RetryError
from sqlalchemy import text, inspect

# Import only the specific config values needed for USASpending
from config import (
    USASPENDING_API_URL, REQUEST_TIMEOUT, MAX_WAIT_SECONDS, 
    DOWNLOAD_HEADERS, CURRENT_DAYS_LOOKBACK, LOGS_DIR
)
import database

logger = logging.getLogger(__name__)

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    retry=retry_if_exception_type((requests.exceptions.RequestException,)),
    before_sleep=lambda retry_state: print(f"Retrying USAspending fetch (attempt {retry_state.attempt_number})...")
)
def fetch_usaspending_chunk(start_str: str, end_str: str) -> pd.DataFrame:
    """
    Fetch a chunk of USAspending.gov award data for a date range.
    
    Args:
        start_str: Start date in YYYY-MM-DD format
        end_str: End date in YYYY-MM-DD format
        
    Returns:
        pd.DataFrame: DataFrame containing awards for the date range, or empty DataFrame on error
        
    Raises:
        requests.exceptions.RequestException: On failed request after retries
        ValueError: On API error or download failure
    """
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
    
    print(f"Sending USAspending request for {start_str} to {end_str}")
    response = requests.post(
        USASPENDING_API_URL, 
        json=payload, 
        timeout=REQUEST_TIMEOUT
    )
    
    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        print(f"USAspending request failed with status {response.status_code}: {response.text}")
        logger.error(f"USAspending request failed with status {response.status_code}: {response.text}")
        raise e
    
    result = response.json()
    
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
            raise ValueError(f"USAspending file not ready after waiting {total_waited} seconds")
        
        status_response = requests.get(status_url, timeout=REQUEST_TIMEOUT)
        status_response.raise_for_status()
        status_data = status_response.json()
        
        if status_data.get("status") == "finished":
            break
            
        # Handle case where seconds_elapsed is "None" or None
        seconds_elapsed_str = status_data.get("seconds_elapsed", "0")
        if seconds_elapsed_str is None or seconds_elapsed_str == "None":
            seconds_elapsed = 0.0
        else:
            try:
                seconds_elapsed = float(seconds_elapsed_str)
            except (ValueError, TypeError):
                logger.error(f"Invalid seconds_elapsed value: {seconds_elapsed_str}. Setting to 0.0.")
                seconds_elapsed = 0.0
                
        print(f"File not ready (status: {status_data.get('status')}, seconds_elapsed: {seconds_elapsed}), waiting {wait_seconds} seconds...")
        time.sleep(wait_seconds)
        total_waited += wait_seconds
    else:
        raise ValueError(f"USAspending file not ready after {max_status_attempts} status checks")
    
    # Download the zip file
    max_download_attempts = 10
    for attempt in range(max_download_attempts):
        print(f"Attempt {attempt + 1}: Downloading USAspending data from: {download_url}")
        file_response = requests.get(
            download_url, 
            headers=DOWNLOAD_HEADERS, 
            timeout=REQUEST_TIMEOUT
        )
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
            
        with z.open(csv_files[0]) as csv_file:
            df = pd.read_csv(csv_file, low_memory=False)
    
    # Add source information and unique ID
    df['data_source'] = 'USAspending.gov'
    df['fetch_date'] = datetime.now().strftime("%Y-%m-%d")
    
    if 'award_id' in df.columns:
        df['UniqueID'] = df['award_id'].astype(str)
    else:
        df['UniqueID'] = df.index.astype(str)
        
    return df

def get_last_action_date() -> Optional[datetime]:
    """
    Get the last action date from the USAspending table.
    
    Returns:
        Optional[datetime]: The latest action date in the table or None if no data exists
    """
    try:
        engine = database.get_engine()
        with engine.connect() as connection:
            # Check if table exists (use the correct prime awards table)
            result = connection.execute(text(
                f"SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'usaspending_prime_awards')"
            ))
            table_exists = result.scalar()
            
            if not table_exists:
                logger.info("USAspending prime awards table doesn't exist yet")
                return None
                
            # Try to find the action_date column (might be lowercase due to PostgreSQL)
            result = connection.execute(text(
                f"SELECT column_name FROM information_schema.columns WHERE table_name = 'usaspending_prime_awards' "
                f"AND column_name IN ('action_date', 'action_date_fiscal_year', 'last_modified_date')"
            ))
            
            date_columns = [row[0] for row in result.fetchall()]
            
            if not date_columns:
                logger.warning("No action date columns found in the USAspending prime awards table")
                return None
                
            # Use the first available date column
            date_column = date_columns[0]
            
            # Get the maximum date
            result = connection.execute(text(
                f"SELECT MAX({date_column}) FROM usaspending_prime_awards"
            ))
            
            max_date_str = result.scalar()
            
            if not max_date_str:
                return None
                
            # Try different date formats
            try:
                # Try ISO format first (YYYY-MM-DD)
                return datetime.fromisoformat(max_date_str.split()[0])
            except (ValueError, AttributeError):
                try:
                    # Try mm/dd/yyyy format
                    return datetime.strptime(max_date_str, "%m/%d/%Y")
                except ValueError:
                    logger.error(f"Could not parse date: {max_date_str}")
                    return None
    except Exception as e:
        logger.error(f"Error getting last action date: {str(e)}")
        return None

def generate_date_chunks(start_date: datetime, end_date: datetime, days_per_chunk: int = 2) -> List[Tuple[datetime, datetime]]: 
    """
    Generate a list of date chunks between start_date and end_date.
    
    Args:
        start_date: The start date
        end_date: The end date
        days_per_chunk: Number of days per chunk
        
    Returns:
        List[Tuple[datetime, datetime]]: List of (chunk_start, chunk_end) tuples
    """
    chunks = []
    current_start = start_date
    
    while current_start < end_date:
        current_end = min(current_start + timedelta(days=days_per_chunk - 1), end_date)
        chunks.append((current_start, current_end))
        current_start = current_end + timedelta(days=1)
        
    return chunks

def get_table_columns(table_name: str) -> List[str]:
    """
    Get the list of column names for a table.
    
    Args:
        table_name: The name of the table
        
    Returns:
        List[str]: List of column names
    """
    try:
        engine = database.get_engine()
        inspector = inspect(engine)
        columns = [col['name'] for col in inspector.get_columns(table_name)]
        return columns
    except Exception as e:
        logger.error(f"Error getting columns for table {table_name}: {str(e)}")
        print(f"Error getting columns for table {table_name}: {str(e)}")
        return []

def insert_dataframe_with_matching_columns(df: pd.DataFrame, table_name: str, unique_id_field: str) -> bool:
    """
    Insert a DataFrame into a table, ensuring only existing columns are used.
    
    Args:
        df: DataFrame to insert
        table_name: Target table name
        unique_id_field: Column name to use for identifying duplicates
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        engine = database.get_engine()
        
        # Get the existing table columns
        existing_columns = get_table_columns(table_name)
        if not existing_columns:
            print(f"Could not get columns for table {table_name}")
            return False
            
        print(f"Found {len(existing_columns)} columns in existing table {table_name}")
        
        # Make column names lowercase and handle problematic column names (with hyphens)
        lowercase_df = df.copy()
        
        # Replace problematic characters in column names
        column_mapping = {}
        sanitized_columns = []
        for col in df.columns:
            # Convert to lowercase and replace problematic characters
            sanitized_col = col.lower().replace('-', '_').replace(' ', '_')
            column_mapping[sanitized_col] = col
            sanitized_columns.append(sanitized_col)
            
        # Rename DataFrame columns to sanitized versions
        lowercase_df.columns = sanitized_columns
        
        # Find columns in the DataFrame that exist in the table (comparing in lowercase)
        existing_columns_lower = [c.lower() for c in existing_columns]
        
        # Match sanitized column names with existing table columns
        common_columns = []
        for col in sanitized_columns:
            # Find the matching column in the existing table (case-insensitive)
            matches = [c for c in existing_columns_lower if c == col]
            if matches:
                common_columns.append(col)
                
        missing_columns = [col for col in existing_columns if col.lower() not in [c.lower() for c in sanitized_columns]]
        
        print(f"Found {len(common_columns)} matching columns between DataFrame and table")
        if missing_columns:
            print(f"Note: Table has {len(missing_columns)} columns not present in the fetched data")
            
        # Make sure the unique ID field is in the sanitized form
        unique_id_field_sanitized = unique_id_field.lower().replace('-', '_').replace(' ', '_')
            
        # Check if unique ID field exists in common columns
        if unique_id_field_sanitized not in common_columns:
            print(f"Error: Unique ID field '{unique_id_field}' (sanitized: '{unique_id_field_sanitized}') not found in common columns")
            return False
            
        # Select only columns that exist in the table
        filtered_df = lowercase_df[common_columns]
        
        # Create a temporary table with just the columns we need
        temp_table = f"temp_{table_name}"
        filtered_df.to_sql(
            name=temp_table,
            con=engine,
            if_exists='replace',
            index=False
        )
        
        # Properly quote column names for the SQL query
        # PostgreSQL uses double quotes for identifiers
        quoted_columns = []
        for col in common_columns:
            # Find the original column name in the database (case-sensitive match)
            matching_col = None
            for existing_col in existing_columns:
                if existing_col.lower() == col.lower():
                    matching_col = existing_col
                    break
                    
            if matching_col:
                quoted_columns.append(f'"{matching_col}"')
            else:
                # Fallback to the sanitized name with quotes
                quoted_columns.append(f'"{col}"')
                
        columns_list = ", ".join(quoted_columns)
        
        # Perform the merge operation
        with engine.connect() as connection:
            # Check if the table has data
            count_result = connection.execute(text(f'SELECT COUNT(*) FROM "{table_name}"'))
            count = count_result.scalar()
            
            if count > 0:
                # Find the correctly cased unique ID column in the database
                unique_id_col = None
                for existing_col in existing_columns:
                    if existing_col.lower() == unique_id_field_sanitized.lower():
                        unique_id_col = existing_col
                        break
                        
                if not unique_id_col:
                    unique_id_col = unique_id_field_sanitized
                    
                # Delete records in the main table that exist in the temp table (by unique ID)
                unique_id_quoted = f'"{unique_id_col}"'
                connection.execute(text(
                    f'DELETE FROM "{table_name}" WHERE {unique_id_quoted} IN '
                    f'(SELECT "{unique_id_field_sanitized}" FROM "{temp_table}")'
                ))
            
            # Insert from temp table to main table with explicit and quoted column list
            connection.execute(text(
                f'INSERT INTO "{table_name}" ({columns_list}) '
                f'SELECT {columns_list} FROM "{temp_table}"'
            ))
            
            # Drop the temporary table
            connection.execute(text(f'DROP TABLE IF EXISTS "{temp_table}"'))
            
            connection.commit()
        
        logger.info(f"Inserted {len(filtered_df)} rows into table {table_name} with column matching")
        return True
    except Exception as e:
        logger.error(f"Database error during column-matched insert into {table_name}: {str(e)}")
        print(f"Database error during column-matched insert into {table_name}: {str(e)}")
        
        # Try to clean up the temporary table if it exists
        try:
            with engine.connect() as connection:
                connection.execute(text(f'DROP TABLE IF EXISTS "{temp_table}"'))
                connection.commit()
        except Exception:
            pass
            
        return False

def fetch_usaspending_data_in_chunks(start_date: datetime, end_date: datetime, days_per_chunk: int = 2) -> pd.DataFrame:
    """
    Fetch USAspending.gov award data in chunks between start_date and end_date.
    
    Args:
        start_date: The start date to fetch from
        end_date: The end date to fetch to
        days_per_chunk: Number of days per chunk
        
    Returns:
        pd.DataFrame: Combined DataFrame of all fetched chunks
    """
    all_data = []
    chunks = generate_date_chunks(start_date, end_date, days_per_chunk)
    
    print(f"Fetching USAspending data from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')} in {len(chunks)} chunks...")
    
    for i, (chunk_start, chunk_end) in enumerate(chunks):
        start_str = chunk_start.strftime('%Y-%m-%d')
        end_str = chunk_end.strftime('%Y-%m-%d')
        
        print(f"Fetching chunk {i+1}/{len(chunks)}: {start_str} to {end_str}")
        
        try:
            df = fetch_usaspending_chunk(start_str, end_str)
            
            if not df.empty:
                all_data.append(df)
                print(f"Retrieved {len(df)} records for the period.")
                
                # Save each chunk immediately to avoid losing data
                if len(df) > 0:
                    print(f"Saving chunk of {len(df)} records to database...")
                    
                    # Use the column-matching insert function instead of direct deduplication
                    success = insert_dataframe_with_matching_columns(
                        df=df,
                        table_name="usaspending_prime_awards",
                        unique_id_field='UniqueID'
                    )
                    
                    if success:
                        print(f"Successfully saved chunk of {len(df)} records.")
                    else:
                        print("Failed to save chunk.")
            else:
                print(f"No data found for period {start_str} to {end_str}.")
                
            # Add a delay between chunks to avoid rate limiting
            if i < len(chunks) - 1:
                delay = 5
                print(f"Waiting {delay} seconds before next chunk...")
                time.sleep(delay)
                
        except Exception as e:
            logger.error(f"Error fetching chunk {start_str} to {end_str}: {str(e)}")
            print(f"Error fetching chunk {start_str} to {end_str}: {str(e)}")
            # Continue with next chunk despite errors
    
    if all_data:
        result_df = pd.concat(all_data, ignore_index=True)
        print(f"Total records fetched across all chunks: {len(result_df)}")
        return result_df
    else:
        print("No data retrieved from any chunk.")
        return pd.DataFrame()

def fetch_current_usaspending_data() -> pd.DataFrame:
    """
    Fetch recent USAspending.gov award data.
    
    Returns:
        pd.DataFrame: DataFrame containing awards, or empty DataFrame on error
    """
    try:
        # Fetch the last N days of data (configurable)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=CURRENT_DAYS_LOOKBACK)
        start_str = start_date.strftime("%Y-%m-%d")
        end_str = end_date.strftime("%Y-%m-%d")
        
        print(f"Fetching recent USAspending data for {start_str} to {end_str}...")
        df = fetch_usaspending_chunk(start_str, end_str)
        
        return df
        
    except (requests.exceptions.RequestException, ValueError) as e:
        logger.error(f"USAspending current fetch failed: {str(e)}")
        print(f"Failed to fetch USAspending current data: {str(e)}")
        return pd.DataFrame()
    except Exception as e:
        logger.error(f"Unexpected error in USAspending current fetch: {str(e)}")
        print(f"Unexpected error fetching USAspending current data: {str(e)}")
        return pd.DataFrame()

def update_current_usaspending() -> bool:
    """
    Fetch recent USAspending awards and update the database.
    Checks for data gaps and fills them in 2-day chunks.
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Check the last action date in our database
        last_action_date = get_last_action_date()
        
        # Set default start date if we don't have data
        today = datetime.now()
        if last_action_date is None:
            # If no data exists, start with a default lookback period
            start_date = today - timedelta(days=CURRENT_DAYS_LOOKBACK)
            print(f"No existing USAspending data found. Starting with default lookback of {CURRENT_DAYS_LOOKBACK} days.")
        else:
            # Start from the day after the last action date
            start_date = last_action_date + timedelta(days=1)
            print(f"Found existing USAspending data with last action date {last_action_date.strftime('%Y-%m-%d')}.")
            
            # If the gap is very large, limit it to avoid overwhelming the system
            days_gap = (today - start_date).days
            if days_gap > 180:  # Cap at 6 months
                start_date = today - timedelta(days=180)
                print(f"Gap to fill is very large ({days_gap} days). Limiting to last 180 days.")
        
        # Check if we need to fetch any data
        if start_date >= today:
            print("No data gap to fill. Already up to date.")
            return True
        
        days_to_fetch = (today - start_date).days
        print(f"Fetching {days_to_fetch} days of USAspending data in 2-day chunks.")
        
        # Fetch the data in chunks
        df = fetch_usaspending_data_in_chunks(start_date, today, days_per_chunk=2)
        
        if df.empty and days_to_fetch > 0:
            print("No USAspending awards fetched despite data gap.")
            return False
        
        # Always update the last fetched date, even if df is empty but we're already up to date
        today_str = today.strftime("%Y-%m-%d")
        # Use the usaspending_prime_awards table name for tracking fetches
        database.update_last_fetched_date("usaspending_prime_awards", today_str)
        
        return True
    
    except Exception as e:
        logger.error(f"Failed to update current USAspending awards: {str(e)}")
        print(f"Failed to update current USAspending awards: {str(e)}")
        return False

if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(
        filename=f"{LOGS_DIR}/usaspending_current.log",
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    success = update_current_usaspending()
    if (success):
        print("Current USAspending awards update completed successfully.")
    else:
        print("Current USAspending awards update failed.")
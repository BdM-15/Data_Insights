"""
SAM.gov data fetching module.
Fetches current and historical opportunity data from SAM.gov API and stores in the database.
"""

from typing import List, Dict, Any, Optional, Tuple
import logging
import time
import requests
import pandas as pd
from datetime import datetime, timedelta
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type, RetryError
from sqlalchemy import text

# Import only the specific config values needed for SAM.gov
from config import (
    SAM_API_URL, SAM_API_KEY, SAM_PTYPE, SAM_TYPE_OF_SET_ASIDE, 
    SAM_NAICS_CODE, SAM_STATE, SAM_ZIP, SAM_API_RATE_LIMIT,
    SAM_API_MAX_ATTEMPTS, SAM_API_BATCH_DELAY, SAM_API_MIN_WAIT,
    SAM_API_MAX_WAIT, SAM_API_BACKOFF_MULTIPLIER, SAM_API_DEFAULT_RETRY_AFTER,
    SAM_API_RETRY_BUFFER, SAM_API_CHUNK_SIZE, SAM_API_MAX_CONSECUTIVE_FAILURES,
    TABLE_SAM_GOV, REQUEST_TIMEOUT, CURRENT_DAYS_LOOKBACK, LOGS_DIR
)
import database

logger = logging.getLogger(__name__)

# Add rate limiting state tracking
_rate_limit_state = {
    "last_request_time": 0,
    "request_count": 0,
    "window_start_time": 0,
    "retry_count": 0,
    "dynamic_wait_time": SAM_API_MIN_WAIT
}

def flatten_dict(d: Dict[str, Any], parent_key: str = '', sep: str = '_') -> Dict[str, Any]:
    """
    Flatten a nested dictionary into a single level with keys joined by separator.
    
    Args:
        d: Dictionary to flatten
        parent_key: Prefix for keys from parent dictionaries
        sep: Separator to use between key levels
        
    Returns:
        Dict[str, Any]: Flattened dictionary
    """
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep).items())
        elif isinstance(v, list):
            items.append((new_key, str(v)))
        else:
            items.append((new_key, v))
    return dict(items)

def respect_rate_limit():
    """
    Implements a dynamic rate limiting algorithm to prevent 429 errors.
    Adjusts wait times based on previous API responses and recent error history.
    
    Returns:
        None
    """
    global _rate_limit_state
    
    # Get current time
    current_time = time.time()
    
    # Reset window if more than a minute has passed
    if current_time - _rate_limit_state["window_start_time"] > 60:
        _rate_limit_state["window_start_time"] = current_time
        _rate_limit_state["request_count"] = 0
    
    # Check if we're about to exceed rate limit
    if _rate_limit_state["request_count"] >= SAM_API_RATE_LIMIT:
        # Calculate time to wait until the minute window resets
        wait_time = 60 - (current_time - _rate_limit_state["window_start_time"])
        
        # Add buffer to ensure we're safely past the window
        wait_time += SAM_API_RETRY_BUFFER
        
        if wait_time > 0:
            logger.info(f"Rate limit approaching. Waiting {wait_time:.2f} seconds before next request")
            print(f"Approaching rate limit. Waiting {wait_time:.2f} seconds...")
            time.sleep(wait_time)
            
            # Reset window after waiting
            _rate_limit_state["window_start_time"] = time.time()
            _rate_limit_state["request_count"] = 0
    
    # Calculate delay since last request to maintain spacing
    time_since_last_request = current_time - _rate_limit_state["last_request_time"]
    
    # Use dynamic wait time based on retry history - increases with failures
    current_min_spacing = _rate_limit_state["dynamic_wait_time"]
    
    # If we've been having issues, gradually increase the wait time
    if _rate_limit_state["retry_count"] > 0:
        # For each retry, add progressively more wait time
        current_min_spacing = max(
            current_min_spacing,
            60.0 / (SAM_API_RATE_LIMIT - (_rate_limit_state["retry_count"] * 2))
        )
    else:
        # When things are running well, use standard spacing
        current_min_spacing = max(
            SAM_API_MIN_WAIT,
            60.0 / SAM_API_RATE_LIMIT  # Time per request to stay under limit
        )
    
    if time_since_last_request < current_min_spacing:
        wait_time = current_min_spacing - time_since_last_request
        print(f"Spacing requests. Waiting {wait_time:.2f} seconds...")
        time.sleep(wait_time)
    
    # Update state
    _rate_limit_state["last_request_time"] = time.time()
    _rate_limit_state["request_count"] += 1

@retry(
    stop=stop_after_attempt(SAM_API_MAX_ATTEMPTS),
    wait=wait_exponential(multiplier=SAM_API_BACKOFF_MULTIPLIER, 
                         min=SAM_API_MIN_WAIT, 
                         max=SAM_API_MAX_WAIT),
    retry=retry_if_exception_type((requests.exceptions.RequestException,)),
    before_sleep=lambda retry_state: print(f"Retrying SAM.gov fetch (attempt {retry_state.attempt_number}/{SAM_API_MAX_ATTEMPTS})...")
)
def fetch_sam_page(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Fetch a single page of SAM.gov opportunities with retry logic.
    
    Args:
        params: Request parameters for the API call
        
    Returns:
        Dict[str, Any]: JSON response from SAM.gov API
        
    Raises:
        requests.exceptions.RequestException: On failed request after retries
    """
    # Apply rate limiting before making request
    respect_rate_limit()
    
    # Make the request with timeout
    response = requests.get(
        SAM_API_URL, 
        params=params, 
        timeout=REQUEST_TIMEOUT
    )
    print(f"Fetching SAM.gov page: {response.url}")
    
    # Handle rate limiting (429 Too Many Requests) with the Retry-After header
    if response.status_code == 429:
        global _rate_limit_state
        # Increase retry count for tracking
        _rate_limit_state["retry_count"] += 1
        
        # Get the wait time from Retry-After header, or use a default based on the API spec
        retry_after = int(response.headers.get('Retry-After', str(SAM_API_DEFAULT_RETRY_AFTER)))
        print(f"Rate limit exceeded. API requires waiting {retry_after} seconds before next request.")
        
        # Increase the dynamic wait time based on retry count
        _rate_limit_state["dynamic_wait_time"] = min(
            SAM_API_MAX_WAIT,  # Don't exceed max wait
            retry_after + (SAM_API_RETRY_BUFFER * _rate_limit_state["retry_count"])
        )
        
        # Wait the required time plus buffer
        wait_time = _rate_limit_state["dynamic_wait_time"]
        logger.warning(f"Rate limit exceeded. Waiting {wait_time} seconds before retry.")
        time.sleep(wait_time)
        
        # Reset the window after waiting
        _rate_limit_state["window_start_time"] = time.time()
        _rate_limit_state["request_count"] = 0
        
        raise requests.exceptions.HTTPError(f"429 Client Error: Too Many Requests - Waited {wait_time} seconds")
    elif response.status_code == 200:
        # On success, reduce retry count and dynamic wait time gradually
        if _rate_limit_state["retry_count"] > 0:
            _rate_limit_state["retry_count"] = max(0, _rate_limit_state["retry_count"] - 1)
            # Gradually reduce wait time on success but don't go below minimum
            _rate_limit_state["dynamic_wait_time"] = max(
                SAM_API_MIN_WAIT,
                _rate_limit_state["dynamic_wait_time"] * 0.8  # Reduce by 20%
            )
    
    # Handle other potential error status codes
    if response.status_code >= 400:
        error_message = f"HTTP Error {response.status_code}"
        try:
            # Try to extract error details from JSON response
            error_data = response.json()
            if 'errorMessage' in error_data:
                error_message += f": {error_data['errorMessage']}"
        except Exception:
            # If JSON parsing fails, use the response text
            error_message += f": {response.text[:100]}"
        
        logger.error(error_message)
        print(error_message)
        response.raise_for_status()
    
    return response.json()

def build_sam_api_params(start_date: datetime, end_date: datetime, offset: int = 0) -> Dict[str, Any]:
    """
    Build API parameters for SAM.gov API based on configuration and date range.
    
    Args:
        start_date: Start date for the opportunity search
        end_date: End date for the opportunity search
        offset: Pagination offset value
        
    Returns:
        Dict[str, Any]: Parameter dictionary for API request
    """
    # Required parameters
    params = {
        "api_key": SAM_API_KEY,
        "limit": 1000,  # Maximum allowed by API
        "offset": offset,
        "postedFrom": start_date.strftime("%m/%d/%Y"),
        "postedTo": end_date.strftime("%m/%d/%Y")
    }
    
    # Add optional parameters only if they exist in config
    if SAM_PTYPE:
        params["ptype"] = SAM_PTYPE
        
    if SAM_TYPE_OF_SET_ASIDE:
        params["typeOfSetAside"] = SAM_TYPE_OF_SET_ASIDE
        
    if SAM_NAICS_CODE:
        params["ncode"] = SAM_NAICS_CODE
        
    if SAM_STATE:
        params["state"] = SAM_STATE
        
    if SAM_ZIP:
        params["zip"] = SAM_ZIP
    
    return params

def fetch_sam_opportunities(start_date: datetime, end_date: datetime) -> pd.DataFrame:
    """
    Fetch SAM.gov opportunities for a date range, handling pagination and rate limits.
    
    Args:
        start_date: Start date for the opportunity search
        end_date: End date for the opportunity search
        
    Returns:
        pd.DataFrame: DataFrame containing all fetched opportunities, or empty DataFrame on error
    """
    try:
        # Verify that the dates are valid
        now = datetime.now()
        if start_date > now or end_date > now:
            print(f"Warning: Can't fetch future opportunities. Adjusting date range to only include past dates.")
            if start_date > now:
                start_date = now - timedelta(days=30)  # Default to last 30 days
            if end_date > now:
                end_date = now
        
        # Initialize params with required and optional parameters based on the API spec
        params = build_sam_api_params(start_date, end_date)
        
        # Log the actual dates being used
        print(f"Using date range: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
        
        all_data = []
        retry_count = 0
        max_retry_count = 5
        
        while True:
            try:
                result = fetch_sam_page(params)
                # Reset retry counter on successful request
                retry_count = 0
            except requests.exceptions.HTTPError as e:
                if "429 Client Error" in str(e):
                    retry_count += 1
                    if (retry_count > max_retry_count):
                        logger.error(f"SAM.gov fetch failed after {max_retry_count} rate limit retries")
                        print(f"Giving up after {max_retry_count} rate limit errors. Try again later.")
                        break
                        
                    # Get the wait time from the error message if possible
                    wait_time = 60  # Default
                    import re
                    match = re.search(r"Waited (\d+) seconds", str(e))
                    if match:
                        # Already waited this long in the fetch_sam_page function
                        logger.info(f"Rate limit hit, already waited {match.group(1)} seconds")
                        continue
                    
                    logger.error(f"SAM.gov fetch failed due to rate limit. Waiting {wait_time} seconds")
                    print(f"Rate limit exceeded. Waiting {wait_time} seconds before retrying...")
                    time.sleep(wait_time)
                    continue
                else:
                    print(f"HTTP Error from SAM.gov API: {str(e)}")
                    raise e  # Re-raise other HTTP errors
            
            # Process the response data
            opportunities_data = result.get("opportunitiesData", [])
            if not opportunities_data:
                print("No opportunities data returned in this page.")
                break
                
            flattened_data = [flatten_dict(item) for item in opportunities_data]
            all_data.extend(flattened_data)
            
            # Check for more pages
            total_records = result.get("totalRecords", 0)
            print(f"Retrieved page with {len(opportunities_data)} records. Total records: {total_records}")
            
            params["offset"] += params["limit"]
            if params["offset"] >= total_records:
                print(f"Reached end of data at offset {params['offset']}.")
                break
            
            # Add a small delay to avoid rate limits - dynamically adjusted based on API behavior
            # Start with minimal delay, but increase if we hit rate limits
            delay = 2 if retry_count == 0 else 5 * retry_count
            print(f"Waiting {delay} seconds before next request...")
            time.sleep(delay)
        
        if all_data:
            # Convert to DataFrame
            df = pd.DataFrame(all_data)
            # Add source information
            df['data_source'] = 'SAM.gov'
            df['fetch_date'] = datetime.now().strftime("%Y-%m-%d")
            df['date_range_start'] = start_date.strftime("%Y-%m-%d")
            df['date_range_end'] = end_date.strftime("%Y-%m-%d")
            return df
        else:
            print("No data retrieved from SAM.gov API for this date range.")
            return pd.DataFrame()
            
    except RetryError as e:
        logger.error(f"SAM.gov fetch failed after retries: {str(e)}")
        print("Failed to fetch SAM.gov data after multiple retries. Please check your internet connection or try again later.")
        return pd.DataFrame()
    except Exception as e:
        logger.error(f"Unexpected error in SAM.gov fetch: {str(e)}")
        print(f"Unexpected error fetching SAM.gov data: {str(e)}")
        return pd.DataFrame()

def fetch_recent_sam_opportunities() -> pd.DataFrame:
    """
    Fetch SAM.gov opportunities for the recent lookback period.
    
    Returns:
        pd.DataFrame: DataFrame containing recent opportunities
    """
    end_date = datetime.now()
    start_date = end_date - timedelta(days=CURRENT_DAYS_LOOKBACK)
    
    print(f"Fetching recent SAM.gov opportunities from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}...")
    return fetch_sam_opportunities(start_date, end_date)

def get_date_ranges_to_fetch(months: int = 6, force_initial_load: bool = False) -> List[Tuple[datetime, datetime]]:
    """
    Get a list of date ranges that need to be fetched based on what's already in the database.
    
    Args:
        months: Number of months to look back
        force_initial_load: If True, will return the full date range regardless of existing data
        
    Returns:
        List[Tuple[datetime, datetime]]: List of (start_date, end_date) tuples to fetch
    """
    now = datetime.now()
    target_start_date = now - timedelta(days=months*30)  # Approximate months in days
    
    # Initialize with the full range
    ranges_to_fetch = [(target_start_date, now)]
    
    # If forcing initial load, return the full range immediately
    if force_initial_load:
        print("Forcing initial load of the full historical period.")
        return ranges_to_fetch
        
    try:
        # Check if we have a date range tracking table
        engine = database.get_engine()
        with engine.connect() as connection:
            # Create the table if it doesn't exist
            connection.execute(text("""
                CREATE TABLE IF NOT EXISTS sam_gov_date_ranges (
                    id SERIAL PRIMARY KEY,
                    start_date DATE NOT NULL,
                    end_date DATE NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            connection.commit()
            
            # Get existing date ranges
            result = connection.execute(text(
                "SELECT start_date, end_date FROM sam_gov_date_ranges ORDER BY start_date"
            ))
            existing_ranges = [(datetime.fromisoformat(str(r[0])), 
                              datetime.fromisoformat(str(r[1]))) for r in result.fetchall()]
            
            if not existing_ranges:
                print("No existing date ranges found. Will fetch the full historical period.")
                return ranges_to_fetch
                
            # Identify gaps in the date ranges
            # Sort ranges chronologically
            existing_ranges.sort(key=lambda x: x[0])
            
            # Find gaps
            gaps = []
            for i in range(len(existing_ranges) - 1):
                current_end = existing_ranges[i][1]
                next_start = existing_ranges[i+1][0]
                
                # If there's a gap of more than 1 day
                if (next_start - current_end).days > 1:
                    gap_start = current_end + timedelta(days=1)
                    gap_end = next_start - timedelta(days=1)
                    gaps.append((gap_start, gap_end))
            
            # Check if we need data before the first range
            if existing_ranges[0][0] > target_start_date:
                gaps.append((target_start_date, existing_ranges[0][0] - timedelta(days=1)))
                
            # Check if we need data after the last range
            if existing_ranges[-1][1] < now - timedelta(days=1):
                gaps.append((existing_ranges[-1][1] + timedelta(days=1), now))
            
            if gaps:
                print(f"Found {len(gaps)} date range gaps to fetch.")
                return gaps
            else:
                print("No date range gaps found. Historical data is complete.")
                # If the sam_gov table is empty, still return the full range
                count_result = connection.execute(text(f"SELECT COUNT(*) FROM {TABLE_SAM_GOV}"))
                count = count_result.scalar()
                if count == 0:
                    print(f"But {TABLE_SAM_GOV} table is empty. Will fetch the full historical period.")
                    return ranges_to_fetch
                return []
                
    except Exception as e:
        logger.error(f"Error determining date ranges to fetch: {str(e)}")
        print(f"Error determining date ranges to fetch: {str(e)}. Will fetch the full range.")
        # Return the full range as a fallback
        return ranges_to_fetch

def record_fetched_date_range(start_date: datetime, end_date: datetime) -> bool:
    """
    Record a successfully fetched date range in the database.
    
    Args:
        start_date: Start date of the fetched range
        end_date: End date of the fetched range
        
    Returns:
        bool: True if successfully recorded, False otherwise
    """
    try:
        engine = database.get_engine()
        with engine.connect() as connection:
            connection.execute(text("""
                INSERT INTO sam_gov_date_ranges (start_date, end_date)
                VALUES (:start_date, :end_date)
            """), {"start_date": start_date.strftime("%Y-%m-%d"), 
                   "end_date": end_date.strftime("%Y-%m-%d")})
            connection.commit()
            return True
    except Exception as e:
        logger.error(f"Error recording fetched date range: {str(e)}")
        print(f"Error recording fetched date range: {str(e)}")
        return False

def fetch_historical_sam_opportunities(months: int = 6) -> pd.DataFrame:
    """
    Fetch historical SAM.gov opportunities for a specified number of months.
    Fetches in 30-day chunks to prevent timeouts and rate limits.
    Only fetches from past dates, not future dates.
    
    Args:
        months: Number of months to look back
        
    Returns:
        pd.DataFrame: DataFrame containing all historical opportunities
    """
    all_data = []
    success_count = 0
    failure_count = 0
    max_failures = 3  # Stop after 3 consecutive failures
    consecutive_failures = 0
    
    # Get the date ranges that need to be fetched
    date_ranges = get_date_ranges_to_fetch(months)
    
    if not date_ranges:
        print("No date ranges need to be fetched. Historical data is complete.")
        return pd.DataFrame()
    
    print(f"Fetching historical SAM.gov opportunities for {len(date_ranges)} date ranges...")
    print("This process may take some time due to API rate limits. Data will be saved in chunks.")
    
    for full_range_start, full_range_end in date_ranges:
        print(f"Processing date range: {full_range_start.strftime('%Y-%m-%d')} to {full_range_end.strftime('%Y-%m-%d')}")
        
        # Process this range in 30-day chunks
        chunk_end = full_range_end
        while chunk_end >= full_range_start:
            # Ensure we're only requesting historical data (not future data)
            now = datetime.now()
            if chunk_end > now:
                chunk_end = now
                
            chunk_start = max(chunk_end - timedelta(days=30), full_range_start)
            
            # Skip chunks in the future
            if chunk_start > now:
                print(f"Skipping future date range: {chunk_start.strftime('%Y-%m-%d')} to {chunk_end.strftime('%Y-%m-%d')}")
                chunk_end = chunk_start - timedelta(days=1)
                continue
                
            print(f"Fetching chunk from {chunk_start.strftime('%Y-%m-%d')} to {chunk_end.strftime('%Y-%m-%d')}...")
            
            try:
                df = fetch_sam_opportunities(chunk_start, chunk_end)
                
                if not df.empty:
                    all_data.append(df)
                    print(f"Retrieved {len(df)} opportunities for the period.")
                    
                    # Save the chunk to the database immediately
                    if len(all_data) >= 2:  # Save every 2 chunks to avoid memory issues
                        result_df = pd.concat(all_data, ignore_index=True)
                        print(f"Saving intermediate batch of {len(result_df)} records to database...")
                        
                        # Add unique ID if needed
                        if 'noticeId' not in result_df.columns:
                            print("Adding missing noticeId column...")
                            result_df['noticeId'] = result_df.index.astype(str)
                        
                        # Save to database using our custom function to handle case issues
                        success = insert_with_deduplication(
                            df=result_df,
                            table_name=TABLE_SAM_GOV,
                            unique_id_field='noticeId'
                        )
                        
                        if success:
                            print(f"Successfully saved batch of {len(result_df)} records.")
                            # Record this date range as successfully fetched
                            record_fetched_date_range(chunk_start, chunk_end)
                            # Clear the list but keep the newest chunk for deduplication
                            newest_chunk = all_data[-1]
                            all_data = [newest_chunk]
                        else:
                            print("Failed to save batch. Will try again with the next batch.")
                    
                    success_count += 1
                    consecutive_failures = 0  # Reset consecutive failures counter
                else:
                    print(f"No opportunities found for the period.")
                    # Still record this as a fetched range to avoid re-fetching
                    record_fetched_date_range(chunk_start, chunk_end)
                    failure_count += 1
                    consecutive_failures += 1
                    
                    # Stop if we have too many consecutive failures
                    if consecutive_failures >= max_failures:
                        print(f"Stopping after {consecutive_failures} consecutive failures")
                        break
            except Exception as e:
                print(f"Error processing chunk {chunk_start.strftime('%Y-%m-%d')} to {chunk_end.strftime('%Y-%m-%d')}: {str(e)}")
                logger.error(f"Error processing chunk {chunk_start.strftime('%Y-%m-%d')} to {chunk_end.strftime('%Y-%m-%d')}: {str(e)}")
                failure_count += 1
                consecutive_failures += 1
                
                # Stop if we have too many consecutive failures
                if consecutive_failures >= max_failures:
                    print(f"Stopping after {consecutive_failures} consecutive failures")
                    break
            
            # Move to previous chunk
            chunk_end = chunk_start - timedelta(days=1)
            
            # Add longer delay between chunks to avoid rate limits
            delay = 15  # Increased from 10 to 15 seconds between chunks
            print(f"Waiting {delay} seconds before next chunk to avoid rate limits...")
            time.sleep(delay)
    
    # Save any remaining data
    if all_data:
        result_df = pd.concat(all_data, ignore_index=True)
        print(f"Total historical opportunities fetched: {len(result_df)}")
        return result_df
    
    if success_count > 0:
        print(f"Successfully processed {success_count} chunks. Some chunks may have failed, but data was saved incrementally.")
        # Return an empty DataFrame, but the fetch is considered partially successful
        return pd.DataFrame()
    
    print(f"Failed to fetch any data after {failure_count} failures.")
    return pd.DataFrame()

def update_sam_opportunities(historical: bool = False, months: int = 6) -> bool:
    """
    Fetch SAM.gov opportunities and update the database.
    
    Args:
        historical: If True, fetch historical data instead of recent data
        months: Number of months to look back for historical data
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        if historical:
            print("Fetching historical SAM.gov opportunities...")
            df = fetch_historical_sam_opportunities(months)
            
            # If we've already saved the data in chunks and have an empty DataFrame,
            # but some chunks were successful, consider the operation a success
            if df.empty:
                # Check if we have any data in the table
                engine = database.get_engine()
                with engine.connect() as connection:
                    count_result = connection.execute(text(f"SELECT COUNT(*) FROM {TABLE_SAM_GOV}"))
                    count = count_result.scalar()
                    
                    if count > 0:
                        print(f"Data was saved in chunks. Total records in database: {count}")
                        # Update the last fetched date
                        today = datetime.now().strftime("%Y-%m-%d")
                        database.update_last_fetched_date(TABLE_SAM_GOV, today)
                        return True
                    else:
                        print("No data was saved. The operation failed.")
                        return False
        else:
            print("Fetching recent SAM.gov opportunities...")
            df = fetch_recent_sam_opportunities()
        
        if df.empty:
            print("No SAM.gov opportunities fetched.")
            return False
        
        print(f"Fetched {len(df)} SAM.gov opportunities.")
        
        # Ensure noticeId exists for unique identification
        if 'noticeId' not in df.columns:
            print("Warning: noticeId not found in SAM.gov data.")
            if len(df) > 0:
                df['noticeId'] = df.index.astype(str)
        
        # Store in database with deduplication
        success = database.insert_with_deduplication(
            df=df,
            table_name=TABLE_SAM_GOV,
            unique_id_field='noticeId'
        )
        
        if success:
            # Update the last fetched date
            today = datetime.now().strftime("%Y-%m-%d")
            database.update_last_fetched_date(TABLE_SAM_GOV, today)
            
        return success
    
    except Exception as e:
        logger.error(f"Failed to update SAM.gov opportunities: {str(e)}")
        print(f"Failed to update SAM.gov opportunities: {str(e)}")
        return False

def insert_with_deduplication(df: pd.DataFrame, table_name: str, unique_id_field: str) -> bool:
    """
    Insert a DataFrame into a table with deduplication based on a unique ID field.
    Handles case-sensitivity issues with column names.
    
    Args:
        df: DataFrame to insert
        table_name: Target table name
        unique_id_field: Column name to use for identifying duplicates
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        engine = database.get_engine()
        
        # Create a temp table with the same name but a prefix
        temp_table = f"temp_{table_name}"
        
        # Convert column names to lowercase for consistency
        df_lowercase = df.copy()
        df_lowercase.columns = [col.lower() for col in df_lowercase.columns]
        
        # Ensure the unique_id_field is lowercase for comparison
        unique_id_field_lower = unique_id_field.lower()
        
        # Check if the unique ID field exists
        if unique_id_field_lower not in [col.lower() for col in df_lowercase.columns]:
            logger.error(f"Unique ID field '{unique_id_field}' not found in DataFrame columns")
            print(f"Error: Unique ID field '{unique_id_field}' not found in DataFrame columns")
            return False
            
        # Save to temp table first
        df_lowercase.to_sql(
            name=temp_table,
            con=engine,
            if_exists='replace',
            index=False
        )
        
        with engine.connect() as connection:
            # Check if the main table exists
            check_table = connection.execute(text(
                f"SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = '{table_name}')"
            ))
            table_exists = check_table.scalar()
            
            if not table_exists:
                # Table doesn't exist yet, create it based on the temp table
                print(f"Creating table {table_name} from temp data")
                connection.execute(text(f'CREATE TABLE "{table_name}" AS SELECT * FROM "{temp_table}"'))
                connection.commit()
                logger.info(f"Created table {table_name}")
                print(f"Created table {table_name}")
            else:
                # Table exists, check if it has any data
                count_query = connection.execute(text(f'SELECT COUNT(*) FROM "{table_name}"'))
                count = count_query.scalar()
                
                if count == 0:
                    # Table exists but is empty, copy all data from temp table
                    print(f"Table {table_name} exists but is empty. Copying all data from temporary table.")
                    # Get column names from both tables to ensure we map correctly
                    table_cols = connection.execute(text(
                        f"SELECT column_name FROM information_schema.columns WHERE table_name = '{table_name}'"
                    ))
                    existing_columns = [row[0] for row in table_cols.fetchall()]
                    
                    temp_cols = connection.execute(text(
                        f"SELECT column_name FROM information_schema.columns WHERE table_name = '{temp_table}'"
                    ))
                    temp_columns = [row[0] for row in temp_cols.fetchall()]
                    
                    # Find columns that exist in both tables (case-insensitive matching)
                    common_columns = []
                    for temp_col in temp_columns:
                        for db_col in existing_columns:
                            if temp_col.lower() == db_col.lower():
                                common_columns.append({
                                    'temp_col': temp_col,
                                    'db_col': db_col
                                })
                                break
                    
                    # Build the column lists for the INSERT statement
                    db_cols = [f'"{col["db_col"]}"' for col in common_columns]
                    temp_cols = [f'"{col["temp_col"]}"' for col in common_columns]
                    
                    # Construct and execute the INSERT query
                    if db_cols and temp_cols:
                        db_cols_str = ", ".join(db_cols)
                        temp_cols_str = ", ".join(temp_cols)
                        
                        insert_query = text(f'''
                            INSERT INTO "{table_name}" ({db_cols_str})
                            SELECT {temp_cols_str} FROM "{temp_table}"
                        ''')
                        connection.execute(insert_query)
                        connection.commit()
                        print(f"Copied all data from temporary table to {table_name}")
                    else:
                        logger.error(f"No common columns found between temp table and {table_name}")
                        print(f"Error: No common columns found between temp table and {table_name}")
                        return False
                else:
                    # Table exists and has data, perform deduplication
                    # Query to get all column names from the existing table (with case preserved)
                    table_cols = connection.execute(text(
                        f"SELECT column_name FROM information_schema.columns WHERE table_name = '{table_name}'"
                    ))
                    existing_columns = [row[0] for row in table_cols.fetchall()]
                    
                    # Find the actual case of the unique ID column in the table
                    db_unique_id_col = None
                    for col in existing_columns:
                        if col.lower() == unique_id_field_lower:
                            db_unique_id_col = col
                            break
                    
                    if not db_unique_id_col:
                        logger.error(f"Unique ID column '{unique_id_field}' not found in database table {table_name}")
                        print(f"Error: Unique ID column '{unique_id_field}' not found in database table {table_name}")
                        return False
                    
                    # Get the correct column name in the temp table
                    temp_unique_id_col = None
                    temp_cols = connection.execute(text(
                        f"SELECT column_name FROM information_schema.columns WHERE table_name = '{temp_table}'"
                    ))
                    temp_columns = [row[0] for row in temp_cols.fetchall()]
                    for col in temp_columns:
                        if col.lower() == unique_id_field_lower:
                            temp_unique_id_col = col
                            break
                            
                    if not temp_unique_id_col:
                        logger.error(f"Unique ID column '{unique_id_field}' not found in temp table")
                        print(f"Error: Unique ID column '{unique_id_field}' not found in temp table")
                        return False
                    
                    # Delete existing records that match the IDs in the temp table
                    query = text(f'''
                        DELETE FROM "{table_name}" 
                        WHERE "{db_unique_id_col}" IN (
                            SELECT "{temp_unique_id_col}" FROM "{temp_table}"
                        )
                    ''')
                    connection.execute(query)
                    
                    # Now insert the new records
                    # First get common columns between temp table and main table
                    # Build the column lists for the INSERT statement
                    db_cols = [f'"{col["db_col"]}"' for col in common_columns]
                    temp_cols = [f'"{col["temp_col"]}"' for col in common_columns]
                    
                    # Construct and execute the INSERT query
                    if db_cols and temp_cols:
                        db_cols_str = ", ".join(db_cols)
                        temp_cols_str = ", ".join(temp_cols)
                        
                        query = text(f'''
                            INSERT INTO "{table_name}" ({db_cols_str})
                            SELECT {temp_cols_str} FROM "{temp_table}"
                        ''')
                        connection.execute(query)
                        connection.commit()
                    else:
                        logger.error(f"No common columns found between temp table and {table_name}")
                        print(f"Error: No common columns found between temp table and {table_name}")
                        return False
                    
            # Drop the temp table
            connection.execute(text(f'DROP TABLE IF EXISTS "{temp_table}"'))
            connection.commit()
            
            # Get the count of rows in the table
            count_query = connection.execute(text(f'SELECT COUNT(*) FROM "{table_name}"'))
            count = count_query.scalar()
            
            logger.info(f"Inserted data into {table_name} with deduplication. Total records: {count}")
            print(f"Inserted data into {table_name} with deduplication. Total records: {count}")
            
            return True
    except Exception as e:
        logger.error(f"Database error during deduplication insert into {table_name}: {str(e)}")
        print(f"Database error during deduplication insert into {table_name}: {str(e)}")
        
        # Try to clean up the temporary table if it exists
        try:
            with engine.connect() as connection:
                connection.execute(text(f'DROP TABLE IF EXISTS "{temp_table}"'))
                connection.commit()
        except Exception:
            pass
            
        return False

def transfer_temp_data_to_final():
    """
    Manually transfer data from the temporary SAM.gov table to the final table.
    This function is useful for recovering from situations where data was successfully
    fetched into the temporary table but failed to transfer to the final table.
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        engine = database.get_engine()
        temp_table = f"temp_{TABLE_SAM_GOV}"
        final_table = TABLE_SAM_GOV
        
        print(f"Attempting to transfer data from {temp_table} to {final_table}...")
        
        with engine.connect() as connection:
            # Check if both tables exist
            check_temp = connection.execute(text(
                f"SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = '{temp_table}')"
            ))
            temp_exists = check_temp.scalar()
            
            check_final = connection.execute(text(
                f"SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = '{final_table}')"
            ))
            final_exists = check_final.scalar()
            
            if not temp_exists:
                print(f"Error: Temporary table {temp_table} does not exist")
                return False
                
            if not final_exists:
                # Create final table from temp table structure
                print(f"Creating final table {final_table} from temporary table structure")
                connection.execute(text(f'CREATE TABLE "{final_table}" AS SELECT * FROM "{temp_table}" WHERE 1=0'))
                connection.commit()
            
            # Get column names from both tables
            temp_cols = connection.execute(text(
                f"SELECT column_name FROM information_schema.columns WHERE table_name = '{temp_table}'"
            ))
            temp_columns = [row[0] for row in temp_cols.fetchall()]
            
            final_cols = connection.execute(text(
                f"SELECT column_name FROM information_schema.columns WHERE table_name = '{final_table}'"
            ))
            final_columns = [row[0] for row in final_cols.fetchall()]
            
            # Find matching columns (case-insensitive)
            common_columns = []
            for temp_col in temp_columns:
                for final_col in final_columns:
                    if temp_col.lower() == final_col.lower():
                        common_columns.append({
                            'temp_col': temp_col,
                            'final_col': final_col
                        })
                        break
            
            if not common_columns:
                print(f"Error: No common columns found between {temp_table} and {final_table}")
                return False
            
            # Build column lists for INSERT
            final_cols_list = [f'"{col["final_col"]}"' for col in common_columns]
            temp_cols_list = [f'"{col["temp_col"]}"' for col in common_columns]
            
            final_cols_str = ", ".join(final_cols_list)
            temp_cols_str = ", ".join(temp_cols_list)
            
            # Count rows in temp table
            count_query = connection.execute(text(f'SELECT COUNT(*) FROM "{temp_table}"'))
            temp_count = count_query.scalar()
            
            if temp_count == 0:
                print(f"No data in temporary table {temp_table}")
                return False
            
            # Execute INSERT
            print(f"Transferring {temp_count} rows from {temp_table} to {final_table}...")
            
            try:
                # Insert data from temp to final
                insert_query = text(f'''
                    INSERT INTO "{final_table}" ({final_cols_str})
                    SELECT {temp_cols_str} FROM "{temp_table}"
                ''')
                connection.execute(insert_query)
                connection.commit()
                
                # Verify the transfer
                count_query = connection.execute(text(f'SELECT COUNT(*) FROM "{final_table}"'))
                final_count = count_query.scalar()
                
                print(f"Successfully transferred data. Rows in {final_table}: {final_count}")
                return True
            except Exception as e:
                print(f"Error during data transfer: {str(e)}")
                return False
                
    except Exception as e:
        print(f"Failed to transfer data: {str(e)}")
        return False

def fix_sam_gov_data_transfer() -> bool:
    """
    Fix the SAM.gov data transfer issue by manually transferring data from 
    the temporary table to the final table.
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        engine = database.get_engine()
        temp_table = f"temp_{TABLE_SAM_GOV}"
        final_table = TABLE_SAM_GOV
        
        print(f"Fixing data transfer from {temp_table} to {final_table}...")
        
        with engine.connect() as connection:
            # Check if both tables exist
            check_temp = connection.execute(text(
                f"SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = '{temp_table}')"
            ))
            temp_exists = check_temp.scalar()
            
            check_final = connection.execute(text(
                f"SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = '{final_table}')"
            ))
            final_exists = check_final.scalar()
            
            if not temp_exists:
                print(f"Error: Temporary table {temp_table} does not exist")
                return False
                
            if not final_exists:
                print(f"Error: Final table {final_table} does not exist")
                return False
            
            # Check row counts
            temp_count_query = connection.execute(text(f'SELECT COUNT(*) FROM "{temp_table}"'))
            temp_count = temp_count_query.scalar()
            
            final_count_query = connection.execute(text(f'SELECT COUNT(*) FROM "{final_table}"'))
            final_count = final_count_query.scalar()
            
            print(f"Found {temp_count} records in temporary table and {final_count} in final table")
            
            if temp_count == 0:
                print("No data to transfer")
                return False
                
            if final_count > 0:
                print(f"Final table already has {final_count} records. Using deduplication strategy.")
                # Get column names for both tables
                temp_cols_query = connection.execute(text(
                    f"SELECT column_name FROM information_schema.columns WHERE table_name = '{temp_table}'"
                ))
                temp_columns = [row[0] for row in temp_cols_query.fetchall()]
                
                final_cols_query = connection.execute(text(
                    f"SELECT column_name FROM information_schema.columns WHERE table_name = '{final_table}'"
                ))
                final_columns = [row[0] for row in final_cols_query.fetchall()]
                
                # Find common columns (case-insensitive)
                common_columns = []
                for temp_col in temp_columns:
                    for final_col in final_columns:
                        if temp_col.lower() == final_col.lower():
                            common_columns.append({
                                'temp_col': temp_col,
                                'final_col': final_col
                            })
                            break
                
                if not common_columns:
                    print(f"Error: No common columns found between {temp_table} and {final_table}")
                    return False
                
                # Find the notice_id column in both tables
                temp_notice_id = None
                final_notice_id = None
                
                for temp_col in temp_columns:
                    if temp_col.lower() == 'noticeid':
                        temp_notice_id = temp_col
                        break
                        
                for final_col in final_columns:
                    if final_col.lower() == 'noticeid':
                        final_notice_id = final_col
                        break
                
                if not temp_notice_id or not final_notice_id:
                    print("Error: Could not find noticeId column in either temp or final table")
                    return False
                
                # Delete existing records that match the notice IDs in temp table
                delete_query = text(f'''
                    DELETE FROM "{final_table}" 
                    WHERE "{final_notice_id}" IN (
                        SELECT "{temp_notice_id}" FROM "{temp_table}"
                    )
                ''')
                connection.execute(delete_query)
                
                # Build column lists for INSERT
                final_cols_list = [f'"{col["final_col"]}"' for col in common_columns]
                temp_cols_list = [f'"{col["temp_col"]}"' for col in common_columns]
                
                final_cols_str = ", ".join(final_cols_list)
                temp_cols_str = ", ".join(temp_cols_list)
                
                # Insert from temp to final
                insert_query = text(f'''
                    INSERT INTO "{final_table}" ({final_cols_str})
                    SELECT {temp_cols_str} FROM "{temp_table}"
                ''')
                connection.execute(insert_query)
                connection.commit()
            else:
                print(f"Final table is empty. Copying all data from temp table.")
                
                # Get column names for both tables
                temp_cols_query = connection.execute(text(
                    f"SELECT column_name FROM information_schema.columns WHERE table_name = '{temp_table}'"
                ))
                temp_columns = [row[0] for row in temp_cols_query.fetchall()]
                
                final_cols_query = connection.execute(text(
                    f"SELECT column_name FROM information_schema.columns WHERE table_name = '{final_table}'"
                ))
                final_columns = [row[0] for row in final_cols_query.fetchall()]
                
                # Find common columns (case-insensitive)
                common_columns = []
                for temp_col in temp_columns:
                    for final_col in final_columns:
                        if temp_col.lower() == final_col.lower():
                            common_columns.append({
                                'temp_col': temp_col,
                                'final_col': final_col
                            })
                            break
                
                if not common_columns:
                    print(f"Error: No common columns found between {temp_table} and {final_table}")
                    return False
                
                # Build column lists for INSERT
                final_cols_list = [f'"{col["final_col"]}"' for col in common_columns]
                temp_cols_list = [f'"{col["temp_col"]}"' for col in common_columns]
                
                final_cols_str = ", ".join(final_cols_list)
                temp_cols_str = ", ".join(temp_cols_list)
                
                # Insert from temp to final
                insert_query = text(f'''
                    INSERT INTO "{final_table}" ({final_cols_str})
                    SELECT {temp_cols_str} FROM "{temp_table}"
                ''')
                connection.execute(insert_query)
                connection.commit()
            
            # Verify the data transfer
            final_count_after = connection.execute(text(f'SELECT COUNT(*) FROM "{final_table}"')).scalar()
            print(f"Transfer complete. Final table now has {final_count_after} records.")
            
            # Update the last fetched date
            today = datetime.now().strftime("%Y-%m-%d")
            database.update_last_fetched_date(TABLE_SAM_GOV, today)
            
            return True
            
    except Exception as e:
        logger.error(f"Failed to fix SAM.gov data transfer: {str(e)}")
        print(f"Failed to fix SAM.gov data transfer: {str(e)}")
        return False

def transfer_data_from_temp_to_final() -> bool:
    """
    Transfer data from temporary SAM.gov table to the final table.
    This function is specifically designed to fix cases where data was fetched
    but not properly transferred from temp_fetched_opp_sam_gov to fetched_opp_sam_gov.
    
    Returns:
        bool: True if the transfer was successful, False otherwise.
    """
    try:
        engine = database.get_engine()
        with engine.connect() as connection:
            # Check if both tables exist
            temp_check = connection.execute(text(
                "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'temp_fetched_opp_sam_gov')"
            ))
            final_check = connection.execute(text(
                f"SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = '{TABLE_SAM_GOV}')"
            ))
            
            temp_exists = temp_check.scalar()
            final_exists = final_check.scalar()
            
            if not temp_exists:
                logger.error("Temporary SAM.gov table does not exist.")
                print("Error: Temporary SAM.gov table does not exist.")
                return False
                
            if not final_exists:
                # Create the final table based on temp table structure
                logger.info(f"Creating table {TABLE_SAM_GOV} from temporary table")
                connection.execute(text(f'CREATE TABLE "{TABLE_SAM_GOV}" AS SELECT * FROM "temp_fetched_opp_sam_gov"'))
                connection.commit()
                
                # Get the count of rows transferred
                count_query = connection.execute(text(f'SELECT COUNT(*) FROM "{TABLE_SAM_GOV}"'))
                count = count_query.scalar()
                
                logger.info(f"Created {TABLE_SAM_GOV} with {count} records from temporary table")
                print(f"Created {TABLE_SAM_GOV} with {count} records from temporary table")
                return True
            
            # Both tables exist, get column names from both tables
            temp_cols_query = connection.execute(text(
                "SELECT column_name FROM information_schema.columns WHERE table_name = 'temp_fetched_opp_sam_gov'"
            ))
            temp_columns = [row[0] for row in temp_cols_query.fetchall()]
            
            final_cols_query = connection.execute(text(
                f"SELECT column_name FROM information_schema.columns WHERE table_name = '{TABLE_SAM_GOV}'"
            ))
            final_columns = [row[0] for row in final_cols_query.fetchall()]
            
            # Find common columns between tables (case-insensitive matching)
            common_columns = []
            for temp_col in temp_columns:
                for final_col in final_columns:
                    if temp_col.lower() == final_col.lower():
                        common_columns.append({
                            'temp_col': temp_col,
                            'final_col': final_col
                        })
                        break
            
            # Build the column lists for the INSERT statement
            final_cols = [f'"{col["final_col"]}"' for col in common_columns]
            temp_cols = [f'"{col["temp_col"]}"' for col in common_columns]
            
            if not final_cols or not temp_cols:
                logger.error("No common columns found between temporary and final tables")
                print("Error: No common columns found between temporary and final tables")
                return False
                
            final_cols_str = ", ".join(final_cols)
            temp_cols_str = ", ".join(temp_cols)
            
            # Count rows in temp table
            temp_count_query = connection.execute(text('SELECT COUNT(*) FROM "temp_fetched_opp_sam_gov"'))
            temp_count = temp_count_query.scalar()
            
            if temp_count == 0:
                logger.info("No data in temporary table to transfer")
                print("No data in temporary table to transfer")
                return True
                
            # Transfer the data using common columns
            insert_query = text(f'''
                INSERT INTO "{TABLE_SAM_GOV}" ({final_cols_str})
                SELECT {temp_cols_str} FROM "temp_fetched_opp_sam_gov"
            ''')
            connection.execute(insert_query)
            connection.commit()
            
            # Confirm the transfer by counting rows
            final_count_query = connection.execute(text(f'SELECT COUNT(*) FROM "{TABLE_SAM_GOV}"'))
            final_count = final_count_query.scalar()
            
            logger.info(f"Successfully transferred {temp_count} records from temporary table to {TABLE_SAM_GOV}")
            print(f"Successfully transferred {temp_count} records from temporary table to {TABLE_SAM_GOV}")
            print(f"Total records in {TABLE_SAM_GOV} now: {final_count}")
            
            return True
            
    except Exception as e:
        logger.error(f"Error transferring data from temporary to final table: {str(e)}")
        print(f"Error transferring data from temporary to final table: {str(e)}")
        return False


def fix_sam_gov_data_transfer() -> bool:
    """
    Run this function to check and fix issues with SAM.gov data not being 
    properly transferred from temporary to final tables.
    
    Returns:
        bool: True if the fix was successful or not needed, False otherwise.
    """
    try:
        engine = database.get_engine()
        with engine.connect() as connection:
            # Check if both tables exist
            temp_check = connection.execute(text(
                "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'temp_fetched_opp_sam_gov')"
            ))
            final_check = connection.execute(text(
                f"SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = '{TABLE_SAM_GOV}')"
            ))
            
            temp_exists = temp_check.scalar()
            final_exists = final_check.scalar()
            
            if temp_exists and final_exists:
                # Count rows in both tables
                temp_count_query = connection.execute(text('SELECT COUNT(*) FROM "temp_fetched_opp_sam_gov"'))
                final_count_query = connection.execute(text(f'SELECT COUNT(*) FROM "{TABLE_SAM_GOV}"'))
                
                temp_count = temp_count_query.scalar()
                final_count = final_count_query.scalar()
                
                # If temp table has data and final table doesn't, transfer the data
                if temp_count > 0 and final_count == 0:
                    print(f"Found {temp_count} records in temporary table but final table is empty.")
                    print("Transferring data from temporary to final table...")
                    return transfer_data_from_temp_to_final()
                else:
                    print(f"No fix needed. Temporary table has {temp_count} records, final table has {final_count} records.")
                    return True
            elif not final_exists and temp_exists:
                # Final table doesn't exist but temp table does - create final table from temp
                print(f"Final table {TABLE_SAM_GOV} doesn't exist but temporary table does.")
                return transfer_data_from_temp_to_final()
            else:
                print("No data transfer fix needed or possible.")
                return True
                
    except Exception as e:
        logger.error(f"Error checking/fixing SAM.gov data transfer: {str(e)}")
        print(f"Error checking/fixing SAM.gov data transfer: {str(e)}")
        return False

if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(
        filename=f"{LOGS_DIR}/sam_gov.log",
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # First check if we have any existing data
    engine = database.get_engine()
    with engine.connect() as connection:
        tables = connection.execute(text(f"SELECT * FROM information_schema.tables WHERE table_name = '{TABLE_SAM_GOV}'"))
        table_exists = bool(tables.fetchone())
        
        if table_exists:
            count_result = connection.execute(text(f"SELECT COUNT(*) FROM {TABLE_SAM_GOV}"))
            count = count_result.scalar()
            
            if count == 0:
                print("No existing SAM.gov data found. Performing initial historical pull...")
                success = update_sam_opportunities(historical=True, months=6)
            else:
                # Check if we have complete historical data
                print(f"Found {count} existing SAM.gov records. Checking for date gaps...")
                date_ranges = get_date_ranges_to_fetch(months=6)
                
                if date_ranges:
                    print(f"Found {len(date_ranges)} date gaps. Performing historical pull to fill gaps...")
                    success = update_sam_opportunities(historical=True, months=6)
                else:
                    print("Historical data is complete. Performing incremental update...")
                    success = update_sam_opportunities(historical=False)
        else:
            print("SAM.gov table doesn't exist yet. Performing initial historical pull...")
            success = update_sam_opportunities(historical=True, months=6)
    
    if success:
        print("SAM.gov opportunities update completed successfully.")
    else:
        print("SAM.gov opportunities update failed.")
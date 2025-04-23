# backend/main.py

import requests
import pandas as pd
from datetime import datetime, timedelta
import os
import logging
import xml.etree.ElementTree as ET
import time
import warnings
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type, RetryError
import requests.exceptions
import zipfile
import io

# FEATURE: Suppress Warnings
warnings.filterwarnings("ignore", category=UserWarning)

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
SAM_API_URL = "https://api.sam.gov/opportunities/v2/search"
SAM_API_KEY = "bGrMUWmmQMopU8jKnN3Q0KTplTXomxMwkIRfNzG0"
NATO_BASE_XML = "https://eportal.nspa.nato.int/eProcurement/XML/eprocurementdata.xml"
USASPENDING_API_URL = "https://api.usaspending.gov/api/v2/bulk_download/awards/"
DATA_DIR = r'C:\GitHub\Opp_Sem_Search\backend\data'
SAM_CSV = os.path.join(DATA_DIR, "sam_opportunities.csv")
NATO_CSV = os.path.join(DATA_DIR, "nato_opportunities.csv")
USASPENDING_CSV = os.path.join(DATA_DIR, "usaspending_awards.csv")
REQUEST_TIMEOUT = 30
DOWNLOAD_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}
MAX_WAIT_SECONDS = 900  # 15 minutes maximum wait time

# FEATURE: Flatten Nested Data (for SAM.gov)
def flatten_dict(d, parent_key='', sep='_'):
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

# FEATURE: Fetch SAM.gov Data - Pulls raw opportunities with pagination and rate limit handling
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    retry=retry_if_exception_type((requests.exceptions.RequestException,)),
    before_sleep=lambda retry_state: print(f"Retrying SAM.gov fetch (attempt {retry_state.attempt_number})...")
)
def fetch_sam_data_page(params):
    response = requests.get(SAM_API_URL, params=params, timeout=REQUEST_TIMEOUT)
    print(f"Fetching SAM.gov page: {response.url}")
    if response.status_code == 429:
        raise requests.exceptions.HTTPError("429 Client Error: Too Many Requests")
    response.raise_for_status()
    return response.json()

def fetch_sam_data():
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        params = {
            "api_key": SAM_API_KEY,
            "limit": 1000, #Limit Range is 0-1000
            "postedFrom": start_date.strftime("%m/%d/%Y"),
            "postedTo": end_date.strftime("%m/%d/%Y"),
            "ptype": "o",
            "offset": 0
        }
        
        all_data = []
        while True:
            try:
                result = fetch_sam_data_page(params)
            except requests.exceptions.HTTPError as e:
                if "429 Client Error" in str(e):
                    logger.error(f"SAM.gov fetch failed due to rate limit: {str(e)}. Skipping to next fetch.")
                    print("SAM.gov rate limit exceeded. Skipping SAM.gov fetch and continuing with NATO and USAspending fetches.")
                    return []
                else:
                    raise e  # Re-raise other HTTP errors to be handled by retry logic
            
            data = result.get("opportunitiesData", [])
            if not data:
                break
            flattened_data = [flatten_dict(item) for item in data]
            all_data.extend(flattened_data)
            
            # Check if there are more pages
            total_records = result.get("totalRecords", 0)
            params["offset"] += params["limit"]
            if params["offset"] >= total_records:
                break
            
            # Add a small delay to avoid hitting rate limits
            time.sleep(1)
        
        return all_data
    except requests.exceptions.RequestException as e:
        logger.error(f"SAM.gov fetch failed: {str(e)}")
        print("Failed to fetch SAM.gov data. This might be due to a network issue. Please check your internet connection or try again later.")
        return []
    except RetryError as e:
        logger.error(f"SAM.gov fetch failed after retries: {str(e)}")
        print("Failed to fetch SAM.gov data after multiple retries. Please check your internet connection or try again later.")
        return []

# FEATURE: Fetch NATO XML Data - Pulls raw XML data
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    retry=retry_if_exception_type((requests.exceptions.RequestException,)),
    before_sleep=lambda retry_state: print(f"Retrying NATO fetch (attempt {retry_state.attempt_number})...")
)
def fetch_nato_xml():
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}
        response = requests.get(NATO_BASE_XML, headers=headers, timeout=REQUEST_TIMEOUT)
        print(f"Fetching NATO XML: {NATO_BASE_XML}")
        response.raise_for_status()
        root = ET.fromstring(response.content)
        opportunities = []
        for item in root.findall(".//FBOItem") + root.findall(".//NOIItem") + root.findall(".//RFPItem"):
            opportunity = {
                "OpportunityID": item.findtext("OpportunityID", ""),
                "CollectiveNumber": item.findtext("CollectiveNumber", ""),
                "UniqueID": f"{item.findtext('OpportunityID', '')}_{item.findtext('CollectiveNumber', '')}",
                "ProductNameEN": item.findtext("ProductNameEN", ""),
                "ProductNameFR": item.findtext("ProductNameFR", ""),
                "Title": item.findtext("Title", ""),
                "Type": item.findtext("Type", ""),
                "PublicationDate": item.findtext("PublicationDate", ""),
                "RFPTentativeDate": item.findtext("RFPTentativeDate", ""),
                "DetailsPage": item.findtext("DetailsPage", ""),
                "RFPClosingDate": item.findtext("RFPClosingDate", ""),
                "Source": "NSPA NATO"
            }
            opportunities.append(opportunity)
        return opportunities
    except requests.exceptions.RequestException as e:
        logger.error(f"NATO XML fetch failed: {str(e)}")
        print("Failed to fetch NATO XML data. This might be due to a network issue or DNS resolution failure. Please check your internet connection, DNS settings (try using Google DNS: 8.8.8.8), or try again later.")
        return []

# FEATURE: Fetch USAspending.gov Data - Recurring daily pull (last 7 days, daily in production)
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
        seconds_elapsed = float(status_data.get("seconds_elapsed", 0))
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
        with z.open(csv_files[0]) as csv_file:
            df = pd.read_csv(csv_file, low_memory=False)  # Set low_memory=False to suppress DtypeWarning
    
    if 'award_id' in df.columns:
        df['UniqueID'] = df['award_id'].astype(str)
    else:
        df['UniqueID'] = df.index.astype(str)
    data = df.to_dict('records')
    return data

def fetch_usaspending_data():
    try:
        # Fetch the last 7 days of data (in production, change to 1 day: end_date - timedelta(days=1))
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)  # Reduced from 30 days to 7 days
        start_str = start_date.strftime("%Y-%m-%d")
        end_str = end_date.strftime("%Y-%m-%d")
        
        print(f"Fetching recent USAspending data for {start_str} to {end_str}...")
        data = fetch_usaspending_chunk(start_str, end_str)
        return data
    except Exception as e:
        logger.error(f"USAspending fetch failed: {str(e)}")
        print("Failed to fetch USAspending data. This might be due to a network issue, DNS resolution failure, or the file taking too long to generate. Please check your internet connection, DNS settings (try using Google DNS: 8.8.8.8), or try again later.")
        return []

# FEATURE: Update CSV with New Entries Only
def update_csv_with_new_entries(new_data, csv_file, unique_id_field):
    if not new_data:
        print(f"No new data to update for {csv_file}")
        return
    
    new_df = pd.DataFrame(new_data)
    
    if unique_id_field not in new_df.columns:
        print(f"Warning: {unique_id_field} not found in new data for {csv_file}")
        new_df[unique_id_field] = new_df.index.astype(str)
    
    if os.path.exists(csv_file):
        try:
            existing_df = pd.read_csv(csv_file, low_memory=False)  # Set low_memory=False to suppress DtypeWarning
        except pd.errors.EmptyDataError:
            existing_df = pd.DataFrame()
    else:
        existing_df = pd.DataFrame()
    
    if not existing_df.empty:
        combined_df = pd.concat([existing_df, new_df])
        combined_df = combined_df.drop_duplicates(subset=[unique_id_field], keep='last')
    else:
        combined_df = new_df
    
    os.makedirs(os.path.dirname(csv_file), exist_ok=True)
    combined_df.to_csv(csv_file, index=False)
    print(f"Updated {csv_file} with {len(new_data)} new records (total: {len(combined_df)})")

# FEATURE: Main Process - Fetches and updates CSVs (daily recurring pull)
def main():
    sam_data = fetch_sam_data()
    update_csv_with_new_entries(sam_data, SAM_CSV, "noticeId")
    
    nato_data = fetch_nato_xml()
    update_csv_with_new_entries(nato_data, NATO_CSV, "UniqueID")
    
    usaspending_data = fetch_usaspending_data()
    update_csv_with_new_entries(usaspending_data, USASPENDING_CSV, "UniqueID")

if __name__ == "__main__":
    main()
"""
NATO NSPA data fetching module.
Fetches opportunity data from NATO's XML feed and stores in the database.
"""

from typing import List, Dict, Any, Optional
import logging
import requests
import pandas as pd
import xml.etree.ElementTree as ET
from datetime import datetime
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type, RetryError
from sqlalchemy import text

# Import only the specific config values needed for NATO NSPA
from config import NATO_BASE_XML, TABLE_NATO_NSPA, REQUEST_TIMEOUT, LOGS_DIR
import database

logger = logging.getLogger(__name__)

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    retry=retry_if_exception_type((requests.exceptions.RequestException,)),
    before_sleep=lambda retry_state: print(f"Retrying NATO fetch (attempt {retry_state.attempt_number})...")
)
def fetch_nato_xml() -> List[Dict[str, Any]]:
    """
    Fetch opportunity data from NATO NSPA XML feed with retry logic.
    
    Returns:
        List[Dict[str, Any]]: List of opportunity dictionaries or empty list on error
    """
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(
            NATO_BASE_XML, 
            headers=headers, 
            timeout=REQUEST_TIMEOUT
        )
        print(f"Fetching NATO XML: {NATO_BASE_XML}")
        response.raise_for_status()
        
        root = ET.fromstring(response.content)
        opportunities = []
        
        # Process all item types in a single loop, determining type by tag name
        item_types = [
            (".//FBOItem", "FBO"), 
            (".//NOIItem", "NOI"), 
            (".//RFPItem", "RFP")
        ]
        
        for xpath, item_type in item_types:
            for item in root.findall(xpath):
                # Initialize a base dictionary with all possible fields
                opportunity = {
                    "OpportunityId": "",
                    "ProductNameEN": "",
                    "ProductNameFR": "",
                    "PublicationDate": "",
                    "RFPTentativeDate": "",
                    "DetailsPage": "",
                    "Type": "",
                    "IsRFPPublished": "",
                    "CollectiveNumber": "",
                    "Title": "",
                    "RFPClosingDate": "",
                    "ItemType": item_type,
                    "Source": "NSPA NATO",
                    "data_source": "NATO NSPA",
                    "fetch_date": datetime.now().strftime("%Y-%m-%d")
                }
                
                # Extract all available fields from the XML element
                for child in item:
                    field_name = child.tag
                    field_value = child.text if child.text else ""
                    opportunity[field_name] = field_value
                
                # Set the UniqueID based on item type
                if item_type in ["FBO", "NOI"]:
                    opportunity["UniqueID"] = opportunity.get("OpportunityId", "")
                else:  # RFP
                    opportunity["UniqueID"] = opportunity.get("CollectiveNumber", "")
                
                opportunities.append(opportunity)
        
        print(f"Extracted {len(opportunities)} opportunities from NATO XML feed.")
        return opportunities
    
    except requests.exceptions.RequestException as e:
        logger.error(f"NATO XML fetch failed: {str(e)}")
        print("Failed to fetch NATO XML data. This might be due to a network issue or DNS resolution failure.")
        return []
    except ET.ParseError as e:
        logger.error(f"NATO XML parsing failed: {str(e)}")
        print("Failed to parse NATO XML data. The XML format may have changed.")
        return []
    except Exception as e:
        logger.error(f"Unexpected error in NATO fetch: {str(e)}")
        print(f"Unexpected error fetching NATO data: {str(e)}")
        return []

def record_nato_fetch() -> bool:
    """
    Record a successful NATO NSPA fetch in the tracking table.
    
    Returns:
        bool: True if recorded successfully, False otherwise
    """
    try:
        today = datetime.now().strftime("%Y-%m-%d")
        
        engine = database.get_engine()
        with engine.connect() as connection:
            # Create tracking table if it doesn't exist
            connection.execute(text("""
                CREATE TABLE IF NOT EXISTS nato_nspa_fetches (
                    id SERIAL PRIMARY KEY,
                    fetch_date DATE NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            
            # Record the fetch
            connection.execute(text("""
                INSERT INTO nato_nspa_fetches (fetch_date)
                VALUES (:fetch_date)
            """), {"fetch_date": today})
            
            connection.commit()
        return True
    except Exception as e:
        logger.error(f"Error recording NATO fetch: {str(e)}")
        print(f"Error recording NATO fetch: {str(e)}")
        return False

def check_last_nato_fetch() -> Optional[datetime]:
    """
    Check when NATO NSPA data was last fetched.
    
    Returns:
        Optional[datetime]: Date of last fetch or None if never fetched
    """
    try:
        engine = database.get_engine()
        with engine.connect() as connection:
            # Create table if it doesn't exist
            connection.execute(text("""
                CREATE TABLE IF NOT EXISTS nato_nspa_fetches (
                    id SERIAL PRIMARY KEY,
                    fetch_date DATE NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            connection.commit()
            
            # Get the last fetch date
            result = connection.execute(text(
                "SELECT fetch_date FROM nato_nspa_fetches ORDER BY fetch_date DESC LIMIT 1"
            ))
            row = result.fetchone()
            
            if row and row[0]:
                return datetime.fromisoformat(str(row[0]))
            return None
    except Exception as e:
        logger.error(f"Error checking last NATO fetch: {str(e)}")
        print(f"Error checking last NATO fetch: {str(e)}")
        return None

def update_nato_opportunities() -> bool:
    """
    Fetch NATO NSPA opportunities and update the database.
    All available opportunities are fetched since NATO's XML feed 
    already contains a limited set of active opportunities.
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        print("Fetching NATO NSPA opportunities...")
        opportunities = fetch_nato_xml()
        
        if not opportunities:
            print("No NATO NSPA opportunities fetched.")
            return False
        
        print(f"Fetched {len(opportunities)} NATO NSPA opportunities.")
        
        # Convert to DataFrame
        df = pd.DataFrame(opportunities)
        
        # Check for and handle schema changes before inserting data
        # This ensures the table structure evolves with the XML format
        database.handle_schema_changes(df, TABLE_NATO_NSPA)
        
        # Store in database with deduplication
        success = database.insert_with_deduplication(
            df=df,
            table_name=TABLE_NATO_NSPA,
            unique_id_field='UniqueID'
        )
        
        if success:
            # Update the last fetched date
            today = datetime.now().strftime("%Y-%m-%d")
            database.update_last_fetched_date(TABLE_NATO_NSPA, today)
            
            # Record in tracking table
            record_nato_fetch()
            
        return success
    
    except Exception as e:
        logger.error(f"Failed to update NATO NSPA opportunities: {str(e)}")
        print(f"Failed to update NATO NSPA opportunities: {str(e)}")
        return False

if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(
        filename=f"{LOGS_DIR}/nato_nspa.log",
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # First check if we have any existing data and when we last fetched
    engine = database.get_engine()
    with engine.connect() as connection:
        tables = connection.execute(text(f"SELECT * FROM information_schema.tables WHERE table_name = '{TABLE_NATO_NSPA}'"))
        table_exists = bool(tables.fetchone())
        
        if table_exists:
            count_result = connection.execute(text(f"SELECT COUNT(*) FROM {TABLE_NATO_NSPA}"))
            count = count_result.scalar()
            
            # Check last fetch date
            last_fetch = check_last_nato_fetch()
            today = datetime.now()
            
            if count == 0:
                print("No existing NATO NSPA data found. Performing initial pull...")
                success = update_nato_opportunities()
            elif last_fetch is None:
                print(f"Found {count} existing NATO NSPA records but no fetch history. Recording the fetch...")
                record_nato_fetch()
                success = True
            elif (today - last_fetch).days >= 1:
                print(f"Found {count} existing NATO NSPA records. Last fetch was on {last_fetch.strftime('%Y-%m-%d')}.")
                print("Updating with new opportunities...")
                success = update_nato_opportunities()
            else:
                print(f"NATO NSPA data was already fetched today ({last_fetch.strftime('%Y-%m-%d')}). Skipping update.")
                success = True
        else:
            print("NATO NSPA table doesn't exist yet. Performing initial pull...")
            success = update_nato_opportunities()
    
    if success:
        print("NATO NSPA opportunities update completed successfully.")
    else:
        print("NATO NSPA opportunities update failed.")
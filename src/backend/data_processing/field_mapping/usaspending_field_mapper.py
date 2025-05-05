#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
USAspending Field Mapper

This script maps the fields from the USAspending database to the usaspending_prime_awards
table in the capture_insights database, focusing on the key fields needed for capture analysis.

The script outputs:
1. A CSV file with the mapping information for key capture fields
2. A comprehensive CSV mapping the entire USAspending database schema to capture_insights
3. A CSV mapping raw.source_procurement_transaction to rpt schema tables
4. Individual CSV files for each table in the raw and rpt schemas
5. A CSV mapping award_search to subaward_search schema
6. A CSV mapping award_search to usaspending_prime_awards schema
"""

import os
import pandas as pd
import psycopg2
from sqlalchemy import create_engine, inspect, text
import logging
# Fix the datetime imports to avoid confusion between module and class
from datetime import date, datetime
import glob
from dotenv import load_dotenv
import shutil
import re
import concurrent.futures
import json
from functools import lru_cache

# Determine base directory (repository root)
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../../../"))

# Ensure logs directory exists
LOGS_DIR = os.path.join(BASE_DIR, "logs")
os.makedirs(LOGS_DIR, exist_ok=True)

# Load environment variables
load_dotenv(os.path.join(BASE_DIR, ".env"))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join(LOGS_DIR, "usaspending_field_mapper.log"))
    ]
)

logger = logging.getLogger("usaspending_field_mapper")

# Connection parameters from environment variables
USASPENDING_PARAMS = {
    "dbname": os.getenv("USASPENDING_PG_DBNAME", "usaspending_full_db_download"),
    "user": os.getenv("USASPENDING_PG_USER", "root"),
    "password": os.getenv("USASPENDING_PG_PASSWORD", "password"),
    "host": os.getenv("USASPENDING_PG_HOST", "localhost"),
    "port": int(os.getenv("USASPENDING_PG_PORT", 5433))
}

CAPTURE_PARAMS = {
    "dbname": os.getenv("PG_DBNAME", "capture_insights"),
    "user": os.getenv("PG_USER", "postgres"), 
    "password": os.getenv("PG_PASSWORD", "admin"),
    "host": os.getenv("PG_HOST", "localhost"),
    "port": int(os.getenv("PG_PORT", 5432))
}

# Field mapping by category
FIELD_MAPPING = {
    "Contract Identification": {
        "piid": {"schema": "rpt", "table": "award_search"},
        "parent_award_id": {"schema": "rpt", "table": "award_search", "column_name": "parent_award_piid"},
        "award_id": {"schema": "rpt", "table": "award_search"},
        "generated_unique_award_id": {"schema": "rpt", "table": "award_search"},
        "unique_award_key": {"schema": "raw", "table": "source_procurement_transaction"}
    },
    "Contract Details": {
        "award_description": {"schema": "rpt", "table": "award_search"},
        "type_of_contract_pricing": {"schema": "rpt", "table": "transaction_search_fpds"},
        "contract_award_type": {"schema": "rpt", "table": "transaction_search_fpds"},
        "contract_award_type_desc": {"schema": "rpt", "table": "transaction_search_fpds"},
        "base_and_all_options_value": {"schema": "rpt", "table": "award_search"},
        "base_exercised_options_val": {"schema": "rpt", "table": "award_search"},
        "total_obligation": {"schema": "rpt", "table": "award_search"},
        "potential_total_value_awar": {"schema": "rpt", "table": "transaction_search_fpds"}
    },
    "Competitive Information": {
        "extent_competed": {"schema": "rpt", "table": "transaction_search_fpds"},
        "type_set_aside": {"schema": "rpt", "table": "transaction_search_fpds"},
        "number_of_offers_received": {"schema": "rpt", "table": "transaction_search_fpds"},
        "solicitation_procedures": {"schema": "rpt", "table": "transaction_search_fpds"},
        "fair_opportunity_limited_s": {"schema": "rpt", "table": "transaction_search_fpds"},
        "other_than_full_and_open_c": {"schema": "rpt", "table": "transaction_search_fpds"}
    },
    "Contract Timing": {
        "action_date": {"schema": "rpt", "table": "award_search"},
        "period_of_performance_star": {"schema": "rpt", "table": "award_search", "column_name": "period_of_performance_start_date"},
        "period_of_performance_curr": {"schema": "rpt", "table": "award_search", "column_name": "period_of_performance_current_end_date"},
        "ordering_period_end_date": {"schema": "rpt", "table": "award_search"},
        "solicitation_date": {"schema": "raw", "table": "source_procurement_transaction"}
    },
    "Agency Information": {
        "awarding_agency_name": {"schema": "rpt", "table": "award_search", "column_name": "awarding_toptier_agency_name"},
        "funding_agency_name": {"schema": "rpt", "table": "award_search", "column_name": "funding_toptier_agency_name"},
        "awarding_office_name": {"schema": "rpt", "table": "transaction_search_fpds"},
        "funding_office_name": {"schema": "rpt", "table": "transaction_search_fpds"},
        "awarding_sub_tier_agency_n": {"schema": "rpt", "table": "award_search", "column_name": "awarding_subtier_agency_name"}
    },
    "Classification Information": {
        "product_or_service_code": {"schema": "rpt", "table": "award_search"},
        "product_or_service_co_desc": {"schema": "rpt", "table": "award_search", "column_name": "product_or_service_description"},
        "naics_code": {"schema": "rpt", "table": "award_search"},
        "naics_description": {"schema": "rpt", "table": "award_search"},
        "major_program": {"schema": "raw", "table": "source_procurement_transaction"}
    },
    "Competitor Information": {
        "awardee_or_recipient_legal": {"schema": "raw", "table": "source_procurement_transaction"},
        "awardee_or_recipient_uniqu": {"schema": "rpt", "table": "award_search", "column_name": "recipient_unique_id"},
        "awardee_or_recipient_uei": {"schema": "rpt", "table": "award_search", "column_name": "recipient_uei"},
        "business_categories": {"schema": "rpt", "table": "award_search"},
        "ultimate_parent_legal_enti": {"schema": "raw", "table": "source_procurement_transaction"},
        "ultimate_parent_unique_ide": {"schema": "rpt", "table": "award_search", "column_name": "parent_recipient_unique_id"},
        "ultimate_parent_uei": {"schema": "rpt", "table": "award_search", "column_name": "parent_uei"}
    },
    "Subaward Information": {
        "subaward_id": {"schema": "rpt", "table": "subaward_search"},
        "subaward_amount": {"schema": "rpt", "table": "subaward_search", "column_name": "amount"},
        "subawardee_name": {"schema": "rpt", "table": "subaward_search", "column_name": "recipient_name"},
        "subawardee_uei": {"schema": "rpt", "table": "subaward_search", "column_name": "recipient_uei"},
        "subaward_description": {"schema": "rpt", "table": "subaward_search", "column_name": "description"},
        "subaward_date": {"schema": "rpt", "table": "subaward_search", "column_name": "action_date"},
        "subaward_place_of_performance": {"schema": "rpt", "table": "subaward_search", "column_name": "place_of_performance_scope"},
        "subawardee_business_types": {"schema": "rpt", "table": "subaward_search", "column_name": "business_categories"}
    },
    "Small Business Designations": {
        "small_business_competitive": {"schema": "raw", "table": "source_procurement_transaction"},
        "emerging_small_business": {"schema": "raw", "table": "source_procurement_transaction"},
        "c8a_program_participant": {"schema": "raw", "table": "source_procurement_transaction"},
        "woman_owned_business": {"schema": "raw", "table": "source_procurement_transaction"},
        "women_owned_small_business": {"schema": "raw", "table": "source_procurement_transaction"},
        "service_disabled_veteran_o": {"schema": "raw", "table": "source_procurement_transaction"},
        "veteran_owned_business": {"schema": "raw", "table": "source_procurement_transaction"},
        "small_disadvantaged_busine": {"schema": "raw", "table": "source_procurement_transaction"},
        "historically_underutilized": {"schema": "raw", "table": "source_procurement_transaction"}
    },
    "Place of Performance": {
        "place_of_perform_city_name": {"schema": "rpt", "table": "award_search", "column_name": "pop_city_name"},
        "place_of_perform_state_nam": {"schema": "rpt", "table": "award_search", "column_name": "pop_state_name"},
        "place_of_perform_country_n": {"schema": "rpt", "table": "award_search", "column_name": "pop_country_name"},
        "place_of_perform_zip_last4": {"schema": "rpt", "table": "transaction_search_fpds"},
        "place_of_performance_congr": {"schema": "rpt", "table": "award_search", "column_name": "pop_congressional_code"}
    }
}

SAMPLE_CACHE_FILE = os.path.join("data", "field_mapping", "sample_values_cache.json")

def get_field_description(field):
    """Return description for a given field"""
    descriptions = {
        "piid": "Procurement Instrument Identifier (contract number)",
        "parent_award_id": "Parent award identifier for tracking IDVs",
        "award_id": "Internal unique identifier",
        "generated_unique_award_id": "System-generated unique award identifier",
        "unique_award_key": "USAspending unique award key",
        "award_description": "Description of the contract",
        "type_of_contract_pricing": "Contract pricing type (FFP, T&M, CPFF, etc.)",
        "contract_award_type": "Type of contract award",
        "contract_award_type_desc": "Description of contract award type",
        "base_and_all_options_value": "Total potential contract value",
        "base_exercised_options_val": "Current exercised contract value",
        "total_obligation": "Total funding obligated to date",
        "potential_total_value_awar": "Maximum potential value of the award",
        "extent_competed": "Extent to which the contract was competed",
        "type_set_aside": "Set-aside type (small business, 8(a), etc.)",
        "number_of_offers_received": "Number of bids/proposals received",
        "solicitation_procedures": "Procedures used for solicitation",
        "fair_opportunity_limited_s": "Fair opportunity limited sources justification",
        "other_than_full_and_open_c": "Other than full and open competition justification",
        "action_date": "Date of the action",
        "period_of_performance_star": "Start date of performance",
        "period_of_performance_curr": "Current end date of performance",
        "ordering_period_end_date": "End date of ordering period",
        "solicitation_date": "Date of solicitation",
        "awarding_agency_name": "Name of awarding agency",
        "funding_agency_name": "Name of funding agency",
        "awarding_office_name": "Name of contracting office",
        "funding_office_name": "Name of funding office",
        "awarding_sub_tier_agency_n": "Name of sub-tier agency awarding the contract",
        "product_or_service_code": "Product or Service Code",
        "product_or_service_co_desc": "Description of PSC",
        "naics_code": "NAICS code",
        "naics_description": "Description of NAICS code",
        "major_program": "Major program name",
        "awardee_or_recipient_legal": "Legal name of competitor",
        "awardee_or_recipient_uniqu": "DUNS number",
        "awardee_or_recipient_uei": "Unique Entity Identifier (UEI)",
        "business_categories": "Array of business categories",
        "ultimate_parent_legal_enti": "Ultimate parent company name",
        "ultimate_parent_unique_ide": "Parent DUNS number",
        "ultimate_parent_uei": "Parent UEI",
        "subaward_id": "Unique identifier for subawards",
        "subaward_amount": "Dollar value of the subaward",
        "subawardee_name": "Name of the subcontractor",
        "subawardee_uei": "Unique Entity Identifier for subcontractor",
        "subaward_description": "Description of subcontracted work",
        "subaward_date": "Date subaward was issued",
        "subaward_place_of_performance": "Location where subcontracted work is performed",
        "subawardee_business_types": "Business size and socioeconomic categories of subcontractor",
        "small_business_competitive": "Small business competitiveness",
        "emerging_small_business": "Emerging small business",
        "c8a_program_participant": "8(a) program participant",
        "woman_owned_business": "Woman-owned business",
        "women_owned_small_business": "Women-owned small business",
        "service_disabled_veteran_o": "Service-disabled veteran-owned",
        "veteran_owned_business": "Veteran-owned business",
        "small_disadvantaged_busine": "Small disadvantaged business",
        "historically_underutilized": "HUBZone business",
        "place_of_perform_city_name": "City of performance",
        "place_of_perform_state_nam": "State of performance",
        "place_of_perform_country_n": "Country of performance",
        "place_of_perform_zip_last4": "ZIP code of performance",
        "place_of_performance_congr": "Congressional district of performance"
    }
    
    return descriptions.get(field, "")

class USAspendingFieldMapper:
    """Maps fields from USAspending database to the capture_insights database."""
    
    def __init__(self):
        """Initialize the mapper with database connections."""
        self.usaspending_engine = None
        self.capture_engine = None
        self.output_dir = os.path.join(BASE_DIR, "data", "field_mapping")
        self.schema_dir = os.path.join(self.output_dir, "schema_tables")
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.schema_dir, exist_ok=True)
        self.file_prefix = datetime.now().strftime("%Y%m%d")
        
        # Connection pools
        self.usa_pool = None
        self.capture_pool = None
        
        # Sample value cache
        self.sample_cache = {}
        self.load_sample_cache()
    
    def load_sample_cache(self):
        """Load sample values from cache file if it exists"""
        try:
            if os.path.exists(SAMPLE_CACHE_FILE):
                with open(SAMPLE_CACHE_FILE, 'r') as f:
                    self.sample_cache = json.load(f)
                logger.info(f"Loaded {len(self.sample_cache)} sample values from cache")
        except Exception as e:
            logger.warning(f"Could not load sample cache: {str(e)}")
            self.sample_cache = {}
    
    def save_sample_cache(self):
        """Save sample values to cache file"""
        try:
            with open(SAMPLE_CACHE_FILE, 'w') as f:
                json.dump(self.sample_cache, f)
            logger.info(f"Saved {len(self.sample_cache)} sample values to cache")
        except Exception as e:
            logger.warning(f"Could not save sample cache: {str(e)}")
    
    def clean_previous_files(self, file_pattern):
        """Delete previous files matching the pattern"""
        try:
            existing_files = glob.glob(os.path.join(self.output_dir, file_pattern))
            for file_path in existing_files:
                os.remove(file_path)
                logger.info(f"Removed previous file: {file_path}")
        except Exception as e:
            logger.warning(f"Error cleaning previous files: {str(e)}")
    
    def clean_directory(self, dir_path):
        """Clean a directory but keep the directory itself"""
        try:
            if os.path.exists(dir_path):
                for file_name in os.listdir(dir_path):
                    file_path = os.path.join(dir_path, file_name)
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                        logger.info(f"Removed file: {file_path}")
            else:
                os.makedirs(dir_path, exist_ok=True)
        except Exception as e:
            logger.warning(f"Error cleaning directory {dir_path}: {str(e)}")
        
    def connect_to_databases(self):
        """Connect to both databases."""
        try:
            self.usaspending_engine = create_engine(
                f"postgresql://{USASPENDING_PARAMS['user']}:{USASPENDING_PARAMS['password']}@"
                f"{USASPENDING_PARAMS['host']}:{USASPENDING_PARAMS['port']}/{USASPENDING_PARAMS['dbname']}"
            )
            logger.info("Connected to USAspending database")
            
            self.capture_engine = create_engine(
                f"postgresql://{CAPTURE_PARAMS['user']}:{CAPTURE_PARAMS['password']}@"
                f"{CAPTURE_PARAMS['host']}:{CAPTURE_PARAMS['port']}/{CAPTURE_PARAMS['dbname']}"
            )
            logger.info("Connected to Capture Insights database")
            
            return True
        except Exception as e:
            logger.error(f"Error connecting to databases: {str(e)}")
            return False
    
    def create_connection_pools(self):
        """Create connection pools for both databases"""
        try:
            # Create a pool of connections for USAspending
            usa_conn_string = f"host={USASPENDING_PARAMS['host']} " \
                            f"port={USASPENDING_PARAMS['port']} " \
                            f"dbname={USASPENDING_PARAMS['dbname']} " \
                            f"user={USASPENDING_PARAMS['user']} " \
                            f"password={USASPENDING_PARAMS['password']}"
                            
            # For PostgreSQL, create a simple pool
            self.usa_pool = []
            for _ in range(8):  # Create 8 connections in the pool
                try:
                    conn = psycopg2.connect(usa_conn_string)
                    conn.set_session(autocommit=True)  # Avoid transaction overhead
                    self.usa_pool.append(conn)
                except Exception as e:
                    logger.warning(f"Failed to create a connection in USA pool: {str(e)}")
            
            if not self.usa_pool:
                logger.error("Failed to create any connections in USAspending pool")
                return False
                
            # Create a pool of connections for Capture
            capture_conn_string = f"host={CAPTURE_PARAMS['host']} " \
                                f"port={CAPTURE_PARAMS['port']} " \
                                f"dbname={CAPTURE_PARAMS['dbname']} " \
                                f"user={CAPTURE_PARAMS['user']} " \
                                f"password={CAPTURE_PARAMS['password']}"
                                
            self.capture_pool = []
            for _ in range(8):  # Create 8 connections in the pool
                try:
                    conn = psycopg2.connect(capture_conn_string)
                    conn.set_session(autocommit=True)  # Avoid transaction overhead
                    self.capture_pool.append(conn)
                except Exception as e:
                    logger.warning(f"Failed to create a connection in Capture pool: {str(e)}")
            
            if not self.capture_pool:
                logger.error("Failed to create any connections in Capture pool")
                return False
                
            logger.info(f"Created connection pools: {len(self.usa_pool)} USAspending connections, {len(self.capture_pool)} Capture connections")
            return True
        except Exception as e:
            logger.error(f"Error creating connection pools: {str(e)}")
            return False
    
    def close_connection_pools(self):
        """Close all connections in the pools"""
        try:
            if self.usa_pool:
                for conn in self.usa_pool:
                    try:
                        conn.close()
                    except:
                        pass
                self.usa_pool = []
                
            if self.capture_pool:
                for conn in self.capture_pool:
                    try:
                        conn.close()
                    except:
                        pass
                self.capture_pool = []
                
            logger.info("Closed all database connections in pools")
        except Exception as e:
            logger.warning(f"Error closing connection pools: {str(e)}")
        
    def get_capture_table_schema(self, table_name="usaspending_prime_awards"):
        """Get the schema of the specified table in capture_insights database."""
        try:
            query = f"""
            SELECT column_name, data_type, character_maximum_length
            FROM information_schema.columns
            WHERE table_name = '{table_name}'
            ORDER BY ordinal_position;
            """
            
            df = pd.read_sql(query, self.capture_engine)
            logger.info(f"Retrieved {len(df)} columns from {table_name} table")
            return df
        except Exception as e:
            logger.error(f"Error getting {table_name} schema: {str(e)}")
            return pd.DataFrame()
    
    def get_usaspending_full_schema(self):
        """Get the complete schema from all tables in the USAspending database"""
        try:
            # Use direct psycopg2 connection to avoid SQLAlchemy issues
            conn_string = f"host={USASPENDING_PARAMS['host']} " \
                         f"port={USASPENDING_PARAMS['port']} " \
                         f"dbname={USASPENDING_PARAMS['dbname']} " \
                         f"user={USASPENDING_PARAMS['user']} " \
                         f"password={USASPENDING_PARAMS['password']}"
            
            conn = psycopg2.connect(conn_string)
            cursor = conn.cursor()
            
            schema_query = """
            SELECT 
                table_schema,
                table_name,
                column_name,
                data_type,
                character_maximum_length
            FROM 
                information_schema.columns
            WHERE 
                table_schema IN ('public', 'raw', 'rpt', 'int')
                AND table_name NOT LIKE 'pg_%'
                AND table_name NOT LIKE 'sql_%'
            ORDER BY 
                table_schema, table_name, ordinal_position;
            """
            
            cursor.execute(schema_query)
            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            
            # Create DataFrame from results
            data = []
            for row in rows:
                data.append(dict(zip(columns, row)))
                
            df = pd.DataFrame(data)
            
            cursor.close()
            conn.close()
            
            logger.info(f"Retrieved {len(df)} columns from {df['table_name'].nunique()} tables in USAspending database")
            return df
            
        except Exception as e:
            logger.error(f"Error getting USAspending schema: {str(e)}")
            return pd.DataFrame()
    
    def get_schema_tables(self, schema_name):
        """Get all tables in a specific schema"""
        try:
            conn_string = f"host={USASPENDING_PARAMS['host']} " \
                        f"port={USASPENDING_PARAMS['port']} " \
                        f"dbname={USASPENDING_PARAMS['dbname']} " \
                        f"user={USASPENDING_PARAMS['user']} " \
                        f"password={USASPENDING_PARAMS['password']}"
            
            conn = psycopg2.connect(conn_string)
            cursor = conn.cursor()
            
            tables_query = f"""
            SELECT 
                table_name
            FROM 
                information_schema.tables
            WHERE 
                table_schema = '{schema_name}'
                AND table_type = 'BASE TABLE'
            ORDER BY 
                table_name;
            """
            
            cursor.execute(tables_query)
            tables = [row[0] for row in cursor.fetchall()]
            
            cursor.close()
            conn.close()
            
            logger.info(f"Retrieved {len(tables)} tables from {schema_name} schema")
            return tables
            
        except Exception as e:
            logger.error(f"Error getting tables from {schema_name} schema: {str(e)}")
            return []
    
    def get_table_schema(self, schema_name, table_name):
        """Get the schema for a specific table"""
        try:
            conn_string = f"host={USASPENDING_PARAMS['host']} " \
                        f"port={USASPENDING_PARAMS['port']} " \
                        f"dbname={USASPENDING_PARAMS['dbname']} " \
                        f"user={USASPENDING_PARAMS['user']} " \
                        f"password={USASPENDING_PARAMS['password']}"
            
            conn = psycopg2.connect(conn_string)
            cursor = conn.cursor()
            
            schema_query = f"""
            SELECT 
                column_name, 
                data_type, 
                character_maximum_length
            FROM 
                information_schema.columns
            WHERE 
                table_schema = '{schema_name}'
                AND table_name = '{table_name}'
            ORDER BY 
                ordinal_position;
            """
            
            cursor.execute(schema_query)
            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            
            # Create DataFrame from results
            data = []
            for row in rows:
                data.append(dict(zip(columns, row)))
                
            df = pd.DataFrame(data)
            
            cursor.close()
            conn.close()
            
            logger.info(f"Retrieved {len(df)} columns from {schema_name}.{table_name}")
            return df
            
        except Exception as e:
            logger.error(f"Error getting schema for {schema_name}.{table_name}: {str(e)}")
            return pd.DataFrame()
    
    def get_raw_to_rpt_mapping(self):
        """Map fields from raw.source_procurement_transaction to rpt schema tables"""
        try:
            conn_string = f"host={USASPENDING_PARAMS['host']} " \
                        f"port={USASPENDING_PARAMS['port']} " \
                        f"dbname={USASPENDING_PARAMS['dbname']} " \
                        f"user={USASPENDING_PARAMS['user']} " \
                        f"password={USASPENDING_PARAMS['password']}"
            
            conn = psycopg2.connect(conn_string)
            
            # Get columns from raw.source_procurement_transaction
            raw_query = """
            SELECT 
                column_name, data_type
            FROM 
                information_schema.columns
            WHERE 
                table_schema = 'raw'
                AND table_name = 'source_procurement_transaction'
            ORDER BY 
                ordinal_position;
            """
            
            raw_df = pd.read_sql(raw_query, conn)
            logger.info(f"Retrieved {len(raw_df)} columns from raw.source_procurement_transaction table")
            
            # Get columns from rpt schema tables focusing on award_search and transaction_search_fpds
            rpt_query = """
            SELECT 
                table_name, column_name, data_type
            FROM 
                information_schema.columns
            WHERE 
                table_schema = 'rpt'
                AND table_name IN ('award_search', 'transaction_search_fpds')
            ORDER BY 
                table_name, ordinal_position;
            """
            
            rpt_df = pd.read_sql(rpt_query, conn)
            logger.info(f"Retrieved {len(rpt_df)} columns from rpt schema tables")
            
            # Get the schema from capture_insights.usaspending_prime_awards
            capture_query = """
            SELECT 
                column_name, data_type
            FROM 
                information_schema.columns
            WHERE 
                table_name = 'usaspending_prime_awards'
            ORDER BY 
                ordinal_position;
            """
            
            capture_df = pd.read_sql(capture_query, self.capture_engine)
            logger.info(f"Retrieved {len(capture_df)} columns from usaspending_prime_awards table")
            
            # Get the schema from capture_insights.usaprime_cleaned
            try:
                cleaned_query = """
                SELECT 
                    column_name, data_type
                FROM 
                    information_schema.columns
                WHERE 
                    table_name = 'usaprime_cleaned'
                ORDER BY 
                    ordinal_position;
                """
                
                cleaned_df = pd.read_sql(cleaned_query, self.capture_engine)
                logger.info(f"Retrieved {len(cleaned_df)} columns from usaprime_cleaned table")
            except Exception as e:
                logger.warning(f"Could not retrieve usaprime_cleaned schema: {e}")
                cleaned_df = pd.DataFrame(columns=['column_name', 'data_type'])
            
            # Create mapping based on column name matches and field mapping knowledge
            mapping_rows = []
            
            for _, raw_row in raw_df.iterrows():
                raw_column = raw_row['column_name']
                raw_type = raw_row['data_type']
                
                # Find exact matches in rpt schema
                exact_matches = rpt_df[rpt_df['column_name'] == raw_column]
                
                # Check for matches in capture_insights.usaspending_prime_awards
                capture_match = raw_column in capture_df['column_name'].values
                capture_data_type = capture_df[capture_df['column_name'] == raw_column]['data_type'].values[0] if capture_match else "N/A"
                
                # Check for matches in capture_insights.usaprime_cleaned
                cleaned_match = raw_column in cleaned_df['column_name'].values
                cleaned_data_type = cleaned_df[cleaned_df['column_name'] == raw_column]['data_type'].values[0] if cleaned_match else "N/A"
                
                if not exact_matches.empty:
                    for _, match_row in exact_matches.iterrows():
                        mapping_rows.append({
                            'Raw Column': raw_column,
                            'Raw Data Type': raw_type,
                            'RPT Table': match_row['table_name'],
                            'RPT Column': match_row['column_name'],
                            'RPT Data Type': match_row['data_type'],
                            'Match Type': 'Direct',
                            'In Capture Table': 'Yes' if capture_match else 'No',
                            'Capture Column': raw_column if capture_match else 'N/A',
                            'Capture Data Type': capture_data_type,
                            'In Cleaned Table': 'Yes' if cleaned_match else 'No',
                            'Cleaned Column': raw_column if cleaned_match else 'N/A',
                            'Cleaned Data Type': cleaned_data_type
                        })
                else:
                    # Check our field mapping for known relationships
                    found = False
                    for field, info in {f: i for c in FIELD_MAPPING.values() for f, i in c.items()}.items():
                        if field == raw_column and info['schema'] == 'rpt':
                            rpt_matches = rpt_df[(rpt_df['table_name'] == info['table']) & 
                                            (rpt_df['column_name'] == info.get('column_name', field))]
                            if not rpt_matches.empty:
                                for _, match_row in rpt_matches.iterrows():
                                    mapping_rows.append({
                                        'Raw Column': raw_column,
                                        'Raw Data Type': raw_type,
                                        'RPT Table': info['table'],
                                        'RPT Column': info.get('column_name', field),
                                        'RPT Data Type': match_row['data_type'],
                                        'Match Type': 'Mapped',
                                        'In Capture Table': 'Yes' if capture_match else 'No',
                                        'Capture Column': raw_column if capture_match else 'N/A',
                                        'Capture Data Type': capture_data_type,
                                        'In Cleaned Table': 'Yes' if cleaned_match else 'No',
                                        'Cleaned Column': raw_column if cleaned_match else 'N/A',
                                        'Cleaned Data Type': cleaned_data_type
                                    })
                                found = True
                                break
                    
                    # If no direct match or mapping, check for potential related columns
                    # using a more controlled approach
                    if not found:
                        # Only look for potential matches if they follow a naming convention pattern
                        # This helps avoid false positives like 'port_authority' matching 'airport_authority'
                        potential_matches = []
                        
                        # Check for columns that might be related in a predictable way
                        # 1. Check if column is renamed with underscore prefix/suffix
                        for _, rpt_row in rpt_df.iterrows():
                            rpt_column = rpt_row['column_name']
                            rpt_parts = rpt_column.split('_')
                            raw_parts = raw_column.split('_')
                            
                            # Skip if either is a substring of the other but not equal
                            # This prevents matches like "port_authority" matching with "airport_authority"
                            if (raw_column in rpt_column or rpt_column in raw_column) and raw_column != rpt_column:
                                # Only consider a match if it's a clean prefix/suffix pattern:
                                # e.g., "pop_city_name" matching with "city_name" is OK
                                # but "port_authority" matching with "airport_authority" is not
                                
                                # Check if one is a prefix/suffix extension of the other
                                if (len(rpt_parts) > len(raw_parts) and 
                                    '_'.join(rpt_parts[-(len(raw_parts)):]) == raw_column) or \
                                   (len(rpt_parts) > len(raw_parts) and 
                                    '_'.join(rpt_parts[:len(raw_parts)]) == raw_column) or \
                                   (len(raw_parts) > len(rpt_parts) and 
                                    '_'.join(raw_parts[-(len(rpt_parts)):]) == rpt_column) or \
                                   (len(raw_parts) > len(rpt_parts) and 
                                    '_'.join(raw_parts[:len(rpt_parts)]) == rpt_column):
                                    potential_matches.append(rpt_row)
                        
                        # If we found potential matches, add them
                        if potential_matches:
                            for match in potential_matches:
                                mapping_rows.append({
                                    'Raw Column': raw_column,
                                    'Raw Data Type': raw_type,
                                    'RPT Table': match['table_name'],
                                    'RPT Column': match['column_name'],
                                    'RPT Data Type': match['data_type'],
                                    'Match Type': 'Partial',
                                    'In Capture Table': 'Yes' if capture_match else 'No',
                                    'Capture Column': raw_column if capture_match else 'N/A',
                                    'Capture Data Type': capture_data_type,
                                    'In Cleaned Table': 'Yes' if cleaned_match else 'No',
                                    'Cleaned Column': raw_column if cleaned_match else 'N/A',
                                    'Cleaned Data Type': cleaned_data_type
                                })
                        else:
                            mapping_rows.append({
                                'Raw Column': raw_column,
                                'Raw Data Type': raw_type,
                                'RPT Table': 'Not Found',
                                'RPT Column': 'Not Found',
                                'RPT Data Type': 'N/A',
                                'Match Type': 'No Match',
                                'In Capture Table': 'Yes' if capture_match else 'No',
                                'Capture Column': raw_column if capture_match else 'N/A',
                                'Capture Data Type': capture_data_type,
                                'In Cleaned Table': 'Yes' if cleaned_match else 'No',
                                'Cleaned Column': raw_column if cleaned_match else 'N/A',
                                'Cleaned Data Type': cleaned_data_type
                            })
            
            # Now map the remaining columns from usaprime_cleaned that don't have matches in raw.source_procurement_transaction
            if not cleaned_df.empty:
                unmapped_cleaned_cols = [col for col in cleaned_df['column_name'] if col not in [r['Cleaned Column'] for r in mapping_rows if r['In Cleaned Table'] == 'Yes']]
                
                for col in unmapped_cleaned_cols:
                    col_type = cleaned_df[cleaned_df['column_name'] == col]['data_type'].values[0]
                    
                    # Check if this column exists in rpt tables
                    rpt_matches = rpt_df[rpt_df['column_name'] == col]
                    
                    # Check if this column exists in capture_insights.usaspending_prime_awards
                    capture_match = col in capture_df['column_name'].values
                    capture_data_type = capture_df[capture_df['column_name'] == col]['data_type'].values[0] if capture_match else "N/A"
                    
                    if not rpt_matches.empty:
                        for _, match_row in rpt_matches.iterrows():
                            mapping_rows.append({
                                'Raw Column': 'N/A',
                                'Raw Data Type': 'N/A',
                                'RPT Table': match_row['table_name'],
                                'RPT Column': match_row['column_name'],
                                'RPT Data Type': match_row['data_type'],
                                'Match Type': 'Cleaned-Only',
                                'In Capture Table': 'Yes' if capture_match else 'No',
                                'Capture Column': col if capture_match else 'N/A',
                                'Capture Data Type': capture_data_type,
                                'In Cleaned Table': 'Yes',
                                'Cleaned Column': col,
                                'Cleaned Data Type': col_type
                            })
                    else:
                        mapping_rows.append({
                            'Raw Column': 'N/A',
                            'Raw Data Type': 'N/A',
                            'RPT Table': 'Not Found',
                            'RPT Column': 'Not Found',
                            'RPT Data Type': 'N/A',
                            'Match Type': 'Cleaned-Only',
                            'In Capture Table': 'Yes' if capture_match else 'No',
                            'Capture Column': col if capture_match else 'N/A',
                            'Capture Data Type': capture_data_type,
                            'In Cleaned Table': 'Yes',
                            'Cleaned Column': col,
                            'Cleaned Data Type': col_type
                        })
            
            conn.close()
            
            # Create DataFrame from results
            mapping_df = pd.DataFrame(mapping_rows)
            return mapping_df
            
        except Exception as e:
            logger.error(f"Error generating raw to rpt mapping: {str(e)}")
            return pd.DataFrame()

    def generate_field_mapping_table(self):
        """Generate a mapping table between USAspending fields and capture_insights fields."""
        if not self.connect_to_databases():
            logger.error("Failed to connect to databases, aborting")
            return None
            
        # Get the capture table schema
        capture_schema_df = self.get_capture_table_schema()
        
        if capture_schema_df.empty:
            logger.error("Failed to retrieve capture table schema, aborting")
            return None
            
        capture_columns = capture_schema_df['column_name'].tolist()
        logger.info(f"Found {len(capture_columns)} columns in usaspending_prime_awards table")
        
        # Create the mapping dataframe
        rows = []
        
        for category, fields in FIELD_MAPPING.items():
            for field, info in fields.items():
                schema = info["schema"]
                table = info["table"]
                column = info.get("column_name", field)
                description = get_field_description(field)
                
                # Check if this field exists in the capture_insights table
                in_capture = field in capture_columns
                capture_column = field if in_capture else "N/A"
                
                rows.append({
                    "Category": category,
                    "Field Name": field,
                    "Field Description": description,
                    "USAspending Schema": schema,
                    "USAspending Table": table, 
                    "USAspending Column": column,
                    "In Capture Table": "Yes" if in_capture else "No",
                    "Capture Column": capture_column,
                    "Data Type": capture_schema_df.loc[capture_schema_df['column_name'] == field, 'data_type'].values[0] if in_capture else "N/A"
                })
        
        # Convert to DataFrame and save to CSV
        df = pd.DataFrame(rows)
        
        # Clean previous files for this type
        self.clean_previous_files("field_mapping_*.csv")
        
        # Save the new file
        filename = os.path.join(self.output_dir, f"field_mapping_{self.file_prefix}.csv")
        df.to_csv(filename, index=False)
        logger.info(f"Field mapping saved to {filename}")
        
        # Return the mapping DataFrame
        return df

    def generate_complete_schema_mapping(self):
        """Generate a comprehensive mapping of all USAspending tables/columns to capture_insights."""
        if not self.connect_to_databases():
            logger.error("Failed to connect to databases, aborting")
            return None

        # Get the capture table schema
        capture_schema_df = self.get_capture_table_schema()
        
        if capture_schema_df.empty:
            logger.error("Failed to retrieve capture table schema, aborting")
            return None
            
        capture_columns = capture_schema_df['column_name'].tolist()
        
        # Get the complete USAspending schema
        usaspending_schema_df = self.get_usaspending_full_schema()
        
        if usaspending_schema_df.empty:
            logger.error("Failed to retrieve USAspending schema, aborting")
            return None
        
        # Create rows for the comprehensive mapping
        rows = []
        
        # For each column in the USAspending database
        for _, row in usaspending_schema_df.iterrows():
            schema = row['table_schema']
            table = row['table_name']
            column = row['column_name']
            data_type = row['data_type']
            max_length = row['character_maximum_length']
            
            # Check if this column name exists in the capture table
            in_capture = column in capture_columns
            capture_column = column if in_capture else None
            capture_data_type = capture_schema_df.loc[capture_schema_df['column_name'] == column, 'data_type'].values[0] if in_capture else None
            
            rows.append({
                "USAspending Schema": schema,
                "USAspending Table": table,
                "USAspending Column": column,
                "USAspending Data Type": data_type,
                "USAspending Max Length": max_length,
                "In Capture Table": "Yes" if in_capture else "No",
                "Capture Column": capture_column if in_capture else "N/A",
                "Capture Data Type": capture_data_type if in_capture else "N/A"
            })
        
        # Convert to DataFrame and save to CSV
        df = pd.DataFrame(rows)
        
        # Clean previous files for this type
        self.clean_previous_files("complete_schema_mapping_*.csv")
        
        # Save the new file
        filename = os.path.join(self.output_dir, f"complete_schema_mapping_{self.file_prefix}.csv")
        df.to_csv(filename, index=False)
        logger.info(f"Complete schema mapping saved to {filename}")
        
        # Generate summary statistics
        tables_count = usaspending_schema_df['table_name'].nunique()
        columns_count = len(usaspending_schema_df)
        mapped_columns_count = df['In Capture Table'].value_counts().get('Yes', 0)
        
        logger.info(f"USAspending schema has {tables_count} tables with {columns_count} total columns")
        logger.info(f"Mapped {mapped_columns_count} columns to the usaspending_prime_awards table")
        
        return df

    def generate_raw_to_rpt_mapping(self):
        """Generate mapping between raw.source_procurement_transaction and rpt schema tables"""
        if not self.connect_to_databases():
            logger.error("Failed to connect to databases for raw to rpt mapping, aborting")
            return None
        
        # Get the raw to rpt mapping
        mapping_df = self.get_raw_to_rpt_mapping()
        
        if mapping_df.empty:
            logger.error("Failed to generate raw to rpt mapping, aborting")
            return None
        
        # Clean previous files for this type
        self.clean_previous_files("raw_to_rpt_mapping_*.csv")
        
        # Save the new file
        filename = os.path.join(self.output_dir, f"raw_to_rpt_mapping_{self.file_prefix}.csv")
        mapping_df.to_csv(filename, index=False)
        logger.info(f"Raw to RPT mapping saved to {filename}")
        
        # Generate summary statistics
        total_raw_cols = len(mapping_df[mapping_df['Raw Column'] != 'N/A'])  # Count only raw columns
        cleaned_only_cols = len(mapping_df[mapping_df['Raw Column'] == 'N/A'])  # Count cleaned-only columns
        mapped_cols = len(mapping_df[(mapping_df['Raw Column'] != 'N/A') & (mapping_df['Match Type'] != 'No Match')])
        mapped_percent = (mapped_cols / total_raw_cols) * 100 if total_raw_cols > 0 else 0
        
        logger.info(f"Raw to RPT mapping: {mapped_cols} of {total_raw_cols} raw columns mapped ({mapped_percent:.1f}%)")
        logger.info(f"Raw to RPT mapping: {cleaned_only_cols} additional columns from usaprime_cleaned included")
        
        return mapping_df
    
    def generate_schema_table_csvs(self):
        """Generate CSV files for each table in raw and rpt schemas"""
        if not self.connect_to_databases():
            logger.error("Failed to connect to databases, aborting")
            return False
        
        # Clean the schema tables directory
        self.clean_directory(self.schema_dir)
        
        # Get tables from raw schema
        raw_tables = self.get_schema_tables('raw')
        for table_name in raw_tables:
            table_df = self.get_table_schema('raw', table_name)
            if not table_df.empty:
                filename = os.path.join(self.schema_dir, f"raw_{table_name}_schema.csv")
                table_df.to_csv(filename, index=False)
                logger.info(f"Saved schema for raw.{table_name} to {filename}")
        
        # Get tables from rpt schema
        rpt_tables = self.get_schema_tables('rpt')
        for table_name in rpt_tables:
            table_df = self.get_table_schema('rpt', table_name)
            if not table_df.empty:
                filename = os.path.join(self.schema_dir, f"rpt_{table_name}_schema.csv")
                table_df.to_csv(filename, index=False)
                logger.info(f"Saved schema for rpt.{table_name} to {filename}")
        
        return True
    
    def generate_award_to_subaward_mapping(self):
        """Generate a mapping between award_search and subaward_search schemas"""
        if not self.connect_to_databases():
            logger.error("Failed to connect to databases, aborting")
            return False
            
        try:
            # Load the award_search schema from file
            award_schema_path = os.path.join(self.schema_dir, "rpt_award_search_schema.csv")
            if not os.path.exists(award_schema_path):
                logger.error(f"Award schema file not found: {award_schema_path}")
                return False
                
            award_schema_df = pd.read_csv(award_schema_path)
            
            # Load the subaward_search schema from file
            subaward_schema_path = os.path.join(self.schema_dir, "rpt_subaward_search_schema.csv")
            if not os.path.exists(subaward_schema_path):
                logger.error(f"Subaward schema file not found: {subaward_schema_path}")
                return False
                
            subaward_schema_df = pd.read_csv(subaward_schema_path)
            
            # Create a mapping table
            mapping_rows = []
            
            # Get the list of columns from each schema
            award_columns = award_schema_df['column_name'].tolist()
            subaward_columns = subaward_schema_df['column_name'].tolist()
            
            # Direct column name matches
            for award_col in award_columns:
                if award_col in subaward_columns:
                    # Direct match
                    award_type = award_schema_df[award_schema_df['column_name'] == award_col]['data_type'].values[0]
                    subaward_type = subaward_schema_df[subaward_schema_df['column_name'] == award_col]['data_type'].values[0]
                    
                    mapping_rows.append({
                        'Award Column': award_col,
                        'Award Data Type': award_type,
                        'Subaward Column': award_col,
                        'Subaward Data Type': subaward_type,
                        'Match Type': 'Direct',
                        'Notes': 'Same column name in both schemas'
                    })
                else:
                    # Check for prefix/suffix matches
                    matches = []
                    for subaward_col in subaward_columns:
                        # Skip if already matched
                        if any(r.get('Subaward Column') == subaward_col for r in mapping_rows):
                            continue
                            
                        # Check for "award_" prefix in subaward
                        if subaward_col.startswith('award_') and subaward_col[6:] == award_col:
                            matches.append(subaward_col)
                        # Check for "sub_" prefix in subaward that might correspond to the award column
                        elif subaward_col.startswith('sub_') and subaward_col[4:] == award_col:
                            matches.append(subaward_col)
                        # Check if award column has a prefix compared to subaward
                        elif award_col.startswith('award_') and award_col[6:] == subaward_col:
                            matches.append(subaward_col)
                        # Check for semantic matches (e.g., "recipient_name" vs "sub_recipient_name")
                        elif award_col == 'recipient_name' and subaward_col == 'sub_recipient_name':
                            matches.append(subaward_col)
                        elif award_col == 'recipient_unique_id' and subaward_col == 'sub_recipient_unique_id':
                            matches.append(subaward_col)
                    
                    # If we found semantic matches
                    if matches:
                        for match in matches:
                            award_type = award_schema_df[award_schema_df['column_name'] == award_col]['data_type'].values[0]
                            subaward_type = subaward_schema_df[subaward_schema_df['column_name'] == match]['data_type'].values[0]
                            
                            mapping_rows.append({
                                'Award Column': award_col,
                                'Award Data Type': award_type,
                                'Subaward Column': match,
                                'Subaward Data Type': subaward_type,
                                'Match Type': 'Semantic',
                                'Notes': 'Related by naming convention or purpose'
                            })
                    else:
                        # No match found
                        award_type = award_schema_df[award_schema_df['column_name'] == award_col]['data_type'].values[0]
                        
                        mapping_rows.append({
                            'Award Column': award_col,
                            'Award Data Type': award_type,
                            'Subaward Column': 'N/A',
                            'Subaward Data Type': 'N/A',
                            'Match Type': 'No Match',
                            'Notes': 'No equivalent in subaward schema'
                        })
            
            # Add subaward columns that don't have matches in award schema
            for subaward_col in subaward_columns:
                if not any(r.get('Subaward Column') == subaward_col for r in mapping_rows):
                    subaward_type = subaward_schema_df[subaward_schema_df['column_name'] == subaward_col]['data_type'].values[0]
                    
                    mapping_rows.append({
                        'Award Column': 'N/A',
                        'Award Data Type': 'N/A',
                        'Subaward Column': subaward_col,
                        'Subaward Data Type': subaward_type,
                        'Match Type': 'Subaward Only',
                        'Notes': 'No equivalent in award schema'
                    })
                    
            # Create DataFrame from the mapping
            mapping_df = pd.DataFrame(mapping_rows)
            
            # Sort by match type and column names
            match_type_order = {
                'Direct': 0,
                'Semantic': 1,
                'No Match': 2,
                'Subaward Only': 3
            }
            
            mapping_df['Sort Order'] = mapping_df['Match Type'].map(match_type_order)
            mapping_df = mapping_df.sort_values(['Sort Order', 'Award Column', 'Subaward Column'])
            mapping_df = mapping_df.drop(columns=['Sort Order'])
            
            # Clean previous files
            self.clean_previous_files("award_to_subaward_mapping_*.csv")
            
            # Save to CSV
            filename = os.path.join(self.output_dir, f"award_to_subaward_mapping_{self.file_prefix}.csv")
            mapping_df.to_csv(filename, index=False)
            logger.info(f"Award to subaward mapping saved to: {filename}")
            
            # Generate summary statistics
            direct_matches = len(mapping_df[mapping_df['Match Type'] == 'Direct'])
            semantic_matches = len(mapping_df[mapping_df['Match Type'] == 'Semantic'])
            no_matches_award = len(mapping_df[mapping_df['Match Type'] == 'No Match'])
            subaward_only = len(mapping_df[mapping_df['Match Type'] == 'Subaward Only'])
            
            logger.info(f"Award to Subaward mapping summary:")
            logger.info(f"  Direct matches: {direct_matches}")
            logger.info(f"  Semantic matches: {semantic_matches}")
            logger.info(f"  Award columns without matches: {no_matches_award}")
            logger.info(f"  Subaward-only columns: {subaward_only}")
            
            return mapping_df
            
        except Exception as e:
            logger.error(f"Error generating award to subaward mapping: {str(e)}")
            return pd.DataFrame()
    
    def generate_award_to_usaspending_prime_mapping(self):
        """Generate a mapping between award_search schema and usaspending_prime_awards schema"""
        if not self.connect_to_databases():
            logger.error("Failed to connect to databases, aborting")
            return False
            
        try:
            # Get the schema for rpt.award_search
            award_schema_path = os.path.join(self.schema_dir, "rpt_award_search_schema.csv")
            if not os.path.exists(award_schema_path):
                # Try to get the schema directly from the database
                award_schema_df = self.get_table_schema('rpt', 'award_search')
                if award_schema_df.empty:
                    logger.error("Could not retrieve award_search schema")
                    return False
                
                # Save the schema file for future use
                award_schema_path = os.path.join(self.schema_dir, "rpt_award_search_schema.csv")
                award_schema_df.to_csv(award_schema_path, index=False)
            else:
                award_schema_df = pd.read_csv(award_schema_path)
            
            # Get the schema for capture_insights.usaspending_prime_awards
            capture_schema_df = self.get_capture_table_schema()
            if capture_schema_df.empty:
                logger.error("Failed to retrieve usaspending_prime_awards schema")
                return False
            
            # Create connection pools for parallel processing
            if not self.create_connection_pools():
                logger.error("Failed to create connection pools")
                return False
            
            # Get the list of columns from each schema
            award_columns = award_schema_df['column_name'].tolist()
            capture_columns = capture_schema_df['column_name'].tolist()
            
            logger.info("Retrieving sample values for columns (this may take a while)...")
            
            # Use ThreadPoolExecutor to get sample values in parallel
            award_samples = {}
            capture_samples = {}
            
            # Function to get sample value for a column and store in dictionary
            def get_award_sample(col):
                value = self.get_sample_values('rpt', 'award_search', col)
                return (col, value)
            
            def get_capture_sample(col):
                value = self.get_sample_values('capture', 'usaspending_prime_awards', col)
                return (col, value)
            
            # Use thread pool for parallel execution
            with concurrent.futures.ThreadPoolExecutor(max_workers=16) as executor:
                # Submit all award column tasks
                award_futures = {executor.submit(get_award_sample, col): col for col in award_columns}
                
                # Submit all capture column tasks
                capture_futures = {executor.submit(get_capture_sample, col): col for col in capture_columns}
                
                # Process award results as they complete
                for future in concurrent.futures.as_completed(award_futures):
                    col = award_futures[future]
                    try:
                        col_name, sample_value = future.result()
                        award_samples[col_name] = sample_value
                        logger.info(f"Retrieved sample values for rpt.award_search.{col_name}")
                    except Exception as e:
                        logger.error(f"Error getting sample for award column {col}: {str(e)}")
                        award_samples[col] = "N/A"
                
                # Process capture results as they complete
                for future in concurrent.futures.as_completed(capture_futures):
                    col = capture_futures[future]
                    try:
                        col_name, sample_value = future.result()
                        capture_samples[col_name] = sample_value
                        logger.info(f"Retrieved sample values for usaspending_prime_awards.{col_name}")
                    except Exception as e:
                        logger.error(f"Error getting sample for capture column {col}: {str(e)}")
                        capture_samples[col] = "N/A"
            
            # Save sample cache for future runs
            self.save_sample_cache()
            
            # Function to compare sample values and calculate similarity score
            def calculate_sample_similarity(award_sample, capture_sample):
                if award_sample == "N/A" or capture_sample == "N/A":
                    return 0, "Unable to compare samples"
                
                # Convert to lists of strings for comparison
                award_sample_list = [str(s).strip().lower() for s in award_sample.split(',')]
                capture_sample_list = [str(s).strip().lower() for s in capture_sample.split(',')]
                
                # Check for exact matches
                exact_matches = set(award_sample_list).intersection(capture_sample_list)
                if exact_matches:
                    return 3, f"Found {len(exact_matches)} exact matching values"
                
                # Check for substring matches (one value contains the other)
                substring_matches = []
                for a_val in award_sample_list:
                    for c_val in capture_sample_list:
                        if a_val in c_val or c_val in a_val:
                            substring_matches.append((a_val, c_val))
                
                if substring_matches:
                    return 2, f"Found {len(substring_matches)} substring matches"
                
                # Check for pattern similarity (e.g., same format but different values)
                pattern_similarity = False
                
                # Check if both contain formatted dates
                date_formats = [
                    r'\d{4}-\d{2}-\d{2}',  # YYYY-MM-DD
                    r'\d{2}/\d{2}/\d{4}'    # MM/DD/YYYY
                ]
                
                award_has_dates = any(re.search(pattern, sample) for pattern in date_formats for sample in award_sample_list)
                capture_has_dates = any(re.search(pattern, sample) for pattern in date_formats for sample in capture_sample_list)
                
                if award_has_dates and capture_has_dates:
                    pattern_similarity = True
                
                # Check if both contain numeric patterns
                award_has_numbers = any(re.search(r'\d+\.?\d*', sample) for sample in award_sample_list)
                capture_has_numbers = any(re.search(r'\d+\.?\d*', sample) for sample in capture_sample_list)
                
                if award_has_numbers and capture_has_numbers:
                    pattern_similarity = True
                
                # Check if both contain similar code patterns (e.g., A12345, B67890)
                award_code_pattern = [re.findall(r'[A-Za-z]\d+', sample) for sample in award_sample_list]
                capture_code_pattern = [re.findall(r'[A-Za-z]\d+', sample) for sample in capture_sample_list]
                
                if any(award_code_pattern) and any(capture_code_pattern):
                    pattern_similarity = True
                
                if pattern_similarity:
                    return 1, "Similar patterns detected in values"
                
                return 0, "No similarity detected in sample values"
            
            # Process mappings using the retrieved sample values
            logger.info("Processing column mappings...")
            
            # Create a mapping table
            mapping_rows = []
            
            # Direct column name matches
            for award_col in award_columns:
                award_type = award_schema_df[award_schema_df['column_name'] == award_col]['data_type'].values[0]
                award_sample = award_samples.get(award_col, "N/A")
                
                if award_col in capture_columns:
                    # Direct match
                    capture_type = capture_schema_df[capture_schema_df['column_name'] == award_col]['data_type'].values[0]
                    capture_sample = capture_samples.get(award_col, "N/A")
                    
                    # Compare samples for data consistency
                    similarity_score, similarity_reason = calculate_sample_similarity(award_sample, capture_sample)
                    
                    mapping_rows.append({
                        'Award Search Column': award_col,
                        'Award Search Data Type': award_type,
                        'Award Search Sample Values': award_sample,
                        'Usaspending Prime Awards Column': award_col,
                        'Usaspending Prime Awards Data Type': capture_type,
                        'Usaspending Prime Awards Sample Values': capture_sample,
                        'Match Type': 'Direct',
                        'Sample Similarity': similarity_score,
                        'Notes': f'Same column name in both schemas. {similarity_reason}'
                    })
                else:
                    # Check for common prefix/suffix patterns
                    potential_matches = []
                    
                    # Check for common prefixes/suffixes or semantic relationships
                    for capture_col in capture_columns:
                        # Skip columns already matched
                        if any(r.get('Usaspending Prime Awards Column') == capture_col for r in mapping_rows):
                            continue
                        
                        capture_type = capture_schema_df[capture_schema_df['column_name'] == capture_col]['data_type'].values[0]
                        capture_sample = capture_samples.get(capture_col, "N/A")
                        name_similarity_score = 0
                        reason = "Potential Match"  # Initialize reason variable with default value
                        
                        # Check if capture column is a substring of award column or vice versa
                        if award_col in capture_col or capture_col in award_col:
                            # Validate it's actually related, not just a substring coincidence
                            if award_col.startswith(capture_col + '_') or capture_col.startswith(award_col + '_'):
                                name_similarity_score += 2
                                reason = 'Prefix/Suffix Pattern'
                            
                            # Specific known patterns
                            elif (award_col == 'recipient_name' and capture_col == 'recipient_name') or \
                                 (award_col == 'recipient_uei' and capture_col == 'uei'):
                                name_similarity_score += 3
                                reason = 'Semantic Match'
                        
                        # Special semantic matches
                        elif (award_col == 'award_amount' and capture_col in ['total_obligation', 'total_value_of_award']) or \
                             (award_col == 'award_category' and capture_col == 'category'):
                            name_similarity_score += 3
                            reason = 'Semantic Match'
                            
                        # Check if they're likely the same with different naming conventions
                        elif (award_col.replace('_', '') == capture_col.replace('_', '')) or \
                             (award_col.lower() == capture_col.lower()):
                            name_similarity_score += 2
                            reason = 'Different Format'
                            
                        # Compare data types for additional confidence
                        if award_type == capture_type:
                            name_similarity_score += 1
                            
                        # Compare sample values for additional confidence
                        sample_similarity_score, sample_reason = calculate_sample_similarity(award_sample, capture_sample)
                        
                        # Combine name similarity and sample similarity for overall score
                        total_similarity_score = name_similarity_score + sample_similarity_score
                        
                        if total_similarity_score > 0:
                            potential_matches.append((
                                capture_col, 
                                reason, 
                                capture_type, 
                                capture_sample, 
                                total_similarity_score, 
                                sample_similarity_score,
                                sample_reason
                            ))
                    
                    # Sort potential matches by similarity score
                    potential_matches.sort(key=lambda x: x[4], reverse=True)
                    
                    if potential_matches:
                        # Take top matches (up to 2)
                        for match, reason, c_type, c_sample, total_score, sample_score, sample_reason in potential_matches[:2]:
                            confidence = "High" if total_score >= 4 else "Medium" if total_score >= 2 else "Low"
                            
                            mapping_rows.append({
                                'Award Search Column': award_col,
                                'Award Search Data Type': award_type,
                                'Award Search Sample Values': award_sample,
                                'Usaspending Prime Awards Column': match,
                                'Usaspending Prime Awards Data Type': c_type,
                                'Usaspending Prime Awards Sample Values': c_sample,
                                'Match Type': 'Potential',
                                'Sample Similarity': sample_score,
                                'Notes': f'{reason} ({confidence} confidence). {sample_reason}.'
                            })
                    else:
                        # No match found
                        mapping_rows.append({
                            'Award Search Column': award_col,
                            'Award Search Data Type': award_type,
                            'Award Search Sample Values': award_sample,
                            'Usaspending Prime Awards Column': 'N/A',
                            'Usaspending Prime Awards Data Type': 'N/A',
                            'Usaspending Prime Awards Sample Values': 'N/A',
                            'Match Type': 'No Match',
                            'Sample Similarity': 0,
                            'Notes': 'No equivalent in usaspending_prime_awards schema'
                        })
            
            # Add capture_insights columns that don't have matches in award_search schema
            for capture_col in capture_columns:
                if not any(r.get('Usaspending Prime Awards Column') == capture_col for r in mapping_rows if r['Match Type'] != 'No Match'):
                    capture_type = capture_schema_df[capture_schema_df['column_name'] == capture_col]['data_type'].values[0]
                    capture_sample = capture_samples.get(capture_col, "N/A")
                    
                    mapping_rows.append({
                        'Award Search Column': 'N/A',
                        'Award Search Data Type': 'N/A',
                        'Award Search Sample Values': 'N/A',
                        'Usaspending Prime Awards Column': capture_col,
                        'Usaspending Prime Awards Data Type': capture_type,
                        'Usaspending Prime Awards Sample Values': capture_sample,
                        'Match Type': 'Capture Only',
                        'Sample Similarity': 0,
                        'Notes': 'No equivalent in award_search schema'
                    })
                    
            # Create DataFrame from the mapping
            mapping_df = pd.DataFrame(mapping_rows)
            
            # Sort by match type and column names
            match_type_order = {
                'Direct': 0,
                'Potential': 1,
                'No Match': 2,
                'Capture Only': 3
            }
            
            mapping_df['Sort Order'] = mapping_df['Match Type'].map(match_type_order)
            mapping_df = mapping_df.sort_values(['Sort Order', 'Award Search Column', 'Usaspending Prime Awards Column'])
            mapping_df = mapping_df.drop(columns=['Sort Order'])
            
            # Clean up database connections
            self.close_connection_pools()
            
            # Clean previous files
            self.clean_previous_files("award_to_usaspending_prime_mapping_*.csv")
            
            # Save to CSV
            filename = os.path.join(self.output_dir, f"award_to_usaspending_prime_mapping_{self.file_prefix}.csv")
            mapping_df.to_csv(filename, index=False)
            logger.info(f"Award to usaspending_prime_awards mapping saved to: {filename}")
            
            # Generate summary statistics
            direct_matches = len(mapping_df[mapping_df['Match Type'] == 'Direct'])
            potential_matches = len(mapping_df[mapping_df['Match Type'] == 'Potential'])
            no_matches_award = len(mapping_df[mapping_df['Match Type'] == 'No Match'])
            capture_only = len(mapping_df[mapping_df['Match Type'] == 'Capture Only'])
            
            # Calculate statistics about sample similarities
            high_sample_similarity = len(mapping_df[mapping_df['Sample Similarity'] >= 3])
            medium_sample_similarity = len(mapping_df[(mapping_df['Sample Similarity'] >= 1) & (mapping_df['Sample Similarity'] < 3)])
            no_sample_similarity = len(mapping_df[mapping_df['Sample Similarity'] == 0])
            
            logger.info(f"Award to usaspending_prime_awards mapping summary:")
            logger.info(f"  Direct matches: {direct_matches}")
            logger.info(f"  Potential matches: {potential_matches}")
            logger.info(f"  Award columns without matches: {no_matches_award}")
            logger.info(f"  Capture-only columns: {capture_only}")
            logger.info(f"  High sample similarity: {high_sample_similarity}")
            logger.info(f"  Medium sample similarity: {medium_sample_similarity}")
            logger.info(f"  No sample similarity: {no_sample_similarity}")
            
            return mapping_df
            
        except Exception as e:
            logger.error(f"Error generating award to usaspending_prime_awards mapping: {str(e)}")
            self.close_connection_pools()
            return pd.DataFrame()
    
    @lru_cache(maxsize=1024)
    def get_sample_values(self, schema_name, table_name, column_name, limit=5):
        """Get sample values from a table and column with caching"""
        # Generate a cache key
        cache_key = f"{schema_name}.{table_name}.{column_name}"
        
        # Return from cache if available
        if cache_key in self.sample_cache:
            return self.sample_cache[cache_key]
        
        try:
            # Get a connection from the appropriate pool
            if schema_name == 'capture':
                if not self.capture_pool:
                    return "N/A"
                
                # Find a free connection or use the first one
                conn = None
                for c in self.capture_pool:
                    if not c.closed:
                        conn = c
                        break
                
                if conn is None:
                    logger.warning("No available connections in Capture pool")
                    return "N/A"
                
                query = f"""SELECT DISTINCT {column_name} 
                          FROM usaspending_prime_awards 
                          WHERE {column_name} IS NOT NULL
                          ORDER BY {column_name}
                          LIMIT {limit}"""
            else:
                if not self.usa_pool:
                    return "N/A"
                
                # Find a free connection or use the first one
                conn = None
                for c in self.usa_pool:
                    if not c.closed:
                        conn = c
                        break
                
                if conn is None:
                    logger.warning("No available connections in USAspending pool")
                    return "N/A"
                
                query = f"""SELECT DISTINCT {column_name} 
                          FROM {schema_name}.{table_name} 
                          WHERE {column_name} IS NOT NULL
                          ORDER BY {column_name}
                          LIMIT {limit}"""
            
            cursor = conn.cursor()
            cursor.execute(query)
            results = cursor.fetchall()
            cursor.close()
            
            # Format results for display
            sample_values = []
            for row in results:
                val = row[0]
                # Truncate long strings
                if isinstance(val, str) and len(val) > 30:
                    val = val[:27] + '...'
                # Format dates
                if isinstance(val, (date, datetime)):
                    val = val.isoformat()
                sample_values.append(str(val))
            
            result = ', '.join(sample_values)
            
            # Cache the result
            self.sample_cache[cache_key] = result
            return result
        except Exception as e:
            logger.warning(f"Could not get sample values for {schema_name}.{table_name}.{column_name}: {str(e)}")
            return "N/A"

def main():
    """Main function to execute the field mapping."""
    # Use absolute paths based on BASE_DIR for all directories
    logger.info("Starting USAspending Field Mapper")
    
    mapper = USAspendingFieldMapper()
    
    # Generate standard field mapping for key capture fields
    logger.info("Generating field mapping for key capture fields...")
    mapping_df = mapper.generate_field_mapping_table()
    
    # Generate comprehensive schema mapping
    logger.info("Generating comprehensive schema mapping for all USAspending tables/columns...")
    complete_mapping_df = mapper.generate_complete_schema_mapping()
    
    # Generate raw to rpt mapping
    logger.info("Generating mapping from raw.source_procurement_transaction to rpt schema tables...")
    raw_rpt_mapping_df = mapper.generate_raw_to_rpt_mapping()
    
    # Generate CSV files for each table in raw and rpt schemas
    logger.info("Generating CSV files for each table in raw and rpt schemas...")
    mapper.generate_schema_table_csvs()
    
    # Generate award to subaward mapping
    logger.info("Generating mapping between award_search and subaward_search schemas...")
    award_subaward_mapping_df = mapper.generate_award_to_subaward_mapping()
    
    # Generate award to usaspending_prime_awards mapping
    logger.info("Generating mapping between award_search and usaspending_prime_awards schemas...")
    award_capture_mapping_df = mapper.generate_award_to_usaspending_prime_mapping()
    
    success = mapping_df is not None and complete_mapping_df is not None and \
              raw_rpt_mapping_df is not None and award_subaward_mapping_df is not None and \
              award_capture_mapping_df is not None
    
    if success:
        logger.info(f"Successfully mapped {len(mapping_df)} key fields, {len(complete_mapping_df)} total columns, and {len(raw_rpt_mapping_df)} raw to rpt columns")
        print(f"Field mapping completed successfully. See logs for details.")
        print(f"Mapping files saved to: {os.path.join(BASE_DIR, 'data', 'field_mapping')}")
        print(f"Individual schema tables saved to: {os.path.join(BASE_DIR, 'data', 'field_mapping', 'schema_tables')}")
        
        # Print a summary of the mapping
        print("\nField Mapping Summary:")
        print(f"Total fields mapped: {len(mapping_df)}")
        print(f"Fields available in capture table: {mapping_df['In Capture Table'].value_counts().get('Yes', 0)}")
        print(f"Fields not available in capture table: {mapping_df['In Capture Table'].value_counts().get('No', 0)}")
        print("\nMapping by Category:")
        category_counts = mapping_df.groupby(['Category', 'In Capture Table']).size().unstack(fill_value=0)
        print(category_counts)
        
        print("\nComplete Schema Mapping Summary:")
        print(f"Total USAspending columns: {len(complete_mapping_df)}")
        print(f"Columns available in capture table: {complete_mapping_df['In Capture Table'].value_counts().get('Yes', 0)}")
        print(f"Columns not in capture table: {complete_mapping_df['In Capture Table'].value_counts().get('No', 0)}")
        
        print("\nRaw to RPT Mapping Summary:")
        print(f"Total raw.source_procurement_transaction columns: {len(raw_rpt_mapping_df[raw_rpt_mapping_df['Raw Column'] != 'N/A'])}")
        print(f"Total usaprime_cleaned columns (including unmapped): {len(raw_rpt_mapping_df[raw_rpt_mapping_df['In Cleaned Table'] == 'Yes'])}")
        match_type_counts = raw_rpt_mapping_df['Match Type'].value_counts()
        for match_type, count in match_type_counts.items():
            print(f"  {match_type} matches: {count}")
            
        print("\nAward to Subaward Mapping Summary:")
        print(f"Total columns mapped: {len(award_subaward_mapping_df)}")
        print(f"Direct matches: {len(award_subaward_mapping_df[award_subaward_mapping_df['Match Type'] == 'Direct'])}")
        print(f"Semantic matches: {len(award_subaward_mapping_df[award_subaward_mapping_df['Match Type'] == 'Semantic'])}")
        print(f"Award columns without matches: {len(award_subaward_mapping_df[award_subaward_mapping_df['Match Type'] == 'No Match'])}")
        print(f"Subaward-only columns: {len(award_subaward_mapping_df[award_subaward_mapping_df['Match Type'] == 'Subaward Only'])}")
        
        print("\nAward to Usaspending Prime Awards Mapping Summary:")
        print(f"Total columns mapped: {len(award_capture_mapping_df)}")
        print(f"Direct matches: {len(award_capture_mapping_df[award_capture_mapping_df['Match Type'] == 'Direct'])}")
        print(f"Potential matches: {len(award_capture_mapping_df[award_capture_mapping_df['Match Type'] == 'Potential'])}")
        print(f"Award columns without matches: {len(award_capture_mapping_df[award_capture_mapping_df['Match Type'] == 'No Match'])}")
        print(f"Capture-only columns: {len(award_capture_mapping_df[award_capture_mapping_df['Match Type'] == 'Capture Only'])}")
    else:
        logger.error("Field mapping failed")
        print("Field mapping failed. See logs for details.")

if __name__ == "__main__":
    main()
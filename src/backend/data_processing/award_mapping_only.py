#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Optimized Award to USAspending Prime Awards Mapping

This specialized script only runs the award_to_usaspending_prime_mapping function
with enhanced performance optimizations.
"""

import os
import pandas as pd
import psycopg2
import logging
from datetime import date, datetime
import re
import json
import concurrent.futures
from functools import lru_cache
import time
import multiprocessing
from tqdm import tqdm

# Determine base directory (repository root)
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../../"))

# Ensure logs directory exists
LOGS_DIR = os.path.join(BASE_DIR, "logs")
os.makedirs(LOGS_DIR, exist_ok=True)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join(LOGS_DIR, "award_mapping_only.log"))
    ]
)

logger = logging.getLogger("award_mapping")

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

# Output directories
OUTPUT_DIR = os.path.join(BASE_DIR, "data", "field_mapping")
SCHEMA_DIR = os.path.join(OUTPUT_DIR, "schema_tables")
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(SCHEMA_DIR, exist_ok=True)
FILE_PREFIX = datetime.now().strftime("%Y%m%d")

# Sample value cache file
SAMPLE_CACHE_FILE = os.path.join(OUTPUT_DIR, "sample_values_cache.json")
COLUMN_BATCH_SIZE = 20  # Number of columns to process in a batch
CONNECTION_POOL_SIZE = min(32, multiprocessing.cpu_count() * 2)  # Use more connections for larger systems

class AwardMapper:
    """Optimized class to map award_search to usaspending_prime_awards."""
    
    def __init__(self):
        """Initialize the mapper."""
        self.usa_pool = []
        self.capture_pool = []
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
    
    def create_connection_pools(self):
        """Create optimized connection pools for both databases"""
        logger.info(f"Creating connection pools with {CONNECTION_POOL_SIZE} connections per database")
        try:
            # Create a pool of connections for USAspending
            usa_conn_string = f"host={USASPENDING_PARAMS['host']} " \
                            f"port={USASPENDING_PARAMS['port']} " \
                            f"dbname={USASPENDING_PARAMS['dbname']} " \
                            f"user={USASPENDING_PARAMS['user']} " \
                            f"password={USASPENDING_PARAMS['password']}"
            
            # Create connections with increased network buffers and reduced query execution time
            # Windows-compatible parameter settings
            for _ in range(CONNECTION_POOL_SIZE):
                try:
                    conn = psycopg2.connect(usa_conn_string)
                    conn.set_session(autocommit=True)
                    
                    # Set session parameters for performance (Windows-compatible)
                    cursor = conn.cursor()
                    cursor.execute("SET work_mem = '128MB'")  # More memory for sorting operations
                    cursor.execute("SET maintenance_work_mem = '256MB'")  # More memory for maintenance
                    cursor.execute("SET statement_timeout = '300s'")  # 5-minute statement timeout
                    # Skip effective_io_concurrency which isn't supported on Windows
                    cursor.close()
                    
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
            
            for _ in range(CONNECTION_POOL_SIZE):
                try:
                    conn = psycopg2.connect(capture_conn_string)
                    conn.set_session(autocommit=True)
                    
                    # Set session parameters for performance (Windows-compatible)
                    cursor = conn.cursor()
                    cursor.execute("SET work_mem = '128MB'")
                    cursor.execute("SET maintenance_work_mem = '256MB'")
                    cursor.execute("SET statement_timeout = '300s'")
                    # Skip effective_io_concurrency which isn't supported on Windows
                    cursor.close()
                    
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
            if hasattr(self, 'usa_pool') and self.usa_pool:
                for conn in self.usa_pool:
                    try:
                        conn.close()
                    except:
                        pass
                self.usa_pool = []
            
            if hasattr(self, 'capture_pool') and self.capture_pool:
                for conn in self.capture_pool:
                    try:
                        conn.close()
                    except:
                        pass
                self.capture_pool = []
            
            logger.info("Closed all database connections in pools")
        except Exception as e:
            logger.warning(f"Error closing connection pools: {str(e)}")
    
    @lru_cache(maxsize=2048)
    def get_sample_values(self, schema_name, table_name, column_name, limit=5):
        """Get sample values from a table and column with caching"""
        # Generate a cache key
        cache_key = f"{schema_name}.{table_name}.{column_name}"
        
        # Return from cache if available
        if cache_key in self.sample_cache:
            return self.sample_cache[cache_key]
        
        try:
            # Handle column names with dashes by quoting them
            quoted_column_name = f'"{column_name}"' if '-' in column_name else column_name
            
            # Get a connection from the appropriate pool
            if schema_name == 'capture':
                if not self.capture_pool:
                    return "N/A"
                
                # Find a free connection
                conn = None
                for c in self.capture_pool:
                    if not c.closed:
                        conn = c
                        break
                
                if conn is None:
                    logger.warning("No available connections in Capture pool")
                    return "N/A"
                
                query = f"""SELECT DISTINCT {quoted_column_name} 
                          FROM usaspending_prime_awards 
                          WHERE {quoted_column_name} IS NOT NULL
                          ORDER BY {quoted_column_name}
                          LIMIT {limit}"""
            else:
                if not self.usa_pool:
                    return "N/A"
                
                # Find a free connection
                conn = None
                for c in self.usa_pool:
                    if not c.closed:
                        conn = c
                        break
                
                if conn is None:
                    logger.warning("No available connections in USAspending pool")
                    return "N/A"
                
                query = f"""SELECT DISTINCT {quoted_column_name} 
                          FROM {schema_name}.{table_name} 
                          WHERE {quoted_column_name} IS NOT NULL
                          ORDER BY {quoted_column_name}
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
    
    def batch_get_sample_values(self, schema_name, table_name, columns):
        """Efficiently get sample values for multiple columns at once"""
        results = {}
        
        if not columns:
            return results
            
        try:
            # Use appropriate pool
            if schema_name == 'capture':
                pool = self.capture_pool
                table_full_name = "usaspending_prime_awards"
            else:
                pool = self.usa_pool
                table_full_name = f"{schema_name}.{table_name}"
                
            if not pool:
                return {col: "N/A" for col in columns}
                
            # Find a free connection
            conn = None
            for c in pool:
                if not c.closed:
                    conn = c
                    break
            
            if conn is None:
                logger.warning(f"No available connections in {schema_name} pool")
                return {col: "N/A" for col in columns}
                
            # Process columns in batches to avoid too large queries
            for i in range(0, len(columns), 10):
                batch = columns[i:i+10]
                # Only fetch columns not already in cache
                uncached_cols = [col for col in batch if f"{schema_name}.{table_name}.{col}" not in self.sample_cache]
                
                if not uncached_cols:
                    continue
                    
                # Quote column names that contain dashes
                quoted_cols = [f'"{col}"' if '-' in col else col for col in uncached_cols]
                
                # Create a query that fetches samples for multiple columns efficiently
                query_parts = []
                for col in quoted_cols:
                    query_parts.append(f"""
                    SELECT '{col.strip('"')}' as col_name, {col} as value
                    FROM {table_full_name}
                    WHERE {col} IS NOT NULL
                    ORDER BY {col}
                    LIMIT 5
                    """)
                
                query = " UNION ALL ".join(query_parts)
                
                cursor = conn.cursor()
                cursor.execute(query)
                rows = cursor.fetchall()
                cursor.close()
                
                # Process results
                col_values = {}
                for row in rows:
                    col_name = row[0]
                    val = row[1]
                    
                    if col_name not in col_values:
                        col_values[col_name] = []
                    
                    # Format the value
                    if isinstance(val, str) and len(val) > 30:
                        val = val[:27] + '...'
                    elif isinstance(val, (date, datetime)):
                        val = val.isoformat()
                    
                    col_values[col_name].append(str(val))
                
                # Convert lists to formatted strings and update cache
                for col in uncached_cols:
                    if col in col_values:
                        value_str = ', '.join(col_values[col])
                        cache_key = f"{schema_name}.{table_name}.{col}"
                        self.sample_cache[cache_key] = value_str
                        results[col] = value_str
                    else:
                        results[col] = "N/A"
                        self.sample_cache[f"{schema_name}.{table_name}.{col}"] = "N/A"
            
            # Add cached values to results
            for col in columns:
                cache_key = f"{schema_name}.{table_name}.{col}"
                if col not in results and cache_key in self.sample_cache:
                    results[col] = self.sample_cache[cache_key]
                elif col not in results:
                    results[col] = "N/A"
            
            return results
            
        except Exception as e:
            logger.error(f"Error in batch_get_sample_values: {str(e)}")
            return {col: "N/A" for col in columns}

    def load_award_schema(self):
        """Load award_search schema from file or database"""
        award_schema_path = os.path.join(SCHEMA_DIR, "rpt_award_search_schema.csv")
        if os.path.exists(award_schema_path):
            return pd.read_csv(award_schema_path)
        else:
            logger.error(f"Award schema file not found: {award_schema_path}")
            return None
    
    def load_capture_schema(self):
        """Load usaspending_prime_awards schema"""
        try:
            # Use a direct connection to the capture database
            conn_string = f"host={CAPTURE_PARAMS['host']} " \
                        f"port={CAPTURE_PARAMS['port']} " \
                        f"dbname={CAPTURE_PARAMS['dbname']} " \
                        f"user={CAPTURE_PARAMS['user']} " \
                        f"password={CAPTURE_PARAMS['password']}"
            
            conn = psycopg2.connect(conn_string)
            
            query = """
            SELECT 
                column_name, data_type, character_maximum_length
            FROM 
                information_schema.columns
            WHERE 
                table_name = 'usaspending_prime_awards'
            ORDER BY 
                ordinal_position;
            """
            
            df = pd.read_sql(query, conn)
            conn.close()
            
            logger.info(f"Retrieved {len(df)} columns from usaspending_prime_awards table")
            return df
        except Exception as e:
            logger.error(f"Error getting usaspending_prime_awards schema: {str(e)}")
            return None
    
    def calculate_sample_similarity(self, award_sample, capture_sample):
        """Compare sample values and calculate similarity score"""
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

    def process_mapping_batch(self, award_columns_batch, award_schema_df, capture_schema_df, award_samples, capture_samples):
        """Process a batch of award columns and generate mapping rows"""
        mapping_rows = []
        
        for award_col in award_columns_batch:
            award_type = award_schema_df[award_schema_df['column_name'] == award_col]['data_type'].values[0]
            award_sample = award_samples.get(award_col, "N/A")
            
            if award_col in capture_schema_df['column_name'].values:
                # Direct match
                capture_type = capture_schema_df[capture_schema_df['column_name'] == award_col]['data_type'].values[0]
                capture_sample = capture_samples.get(award_col, "N/A")
                
                # Compare samples for data consistency
                similarity_score, similarity_reason = self.calculate_sample_similarity(award_sample, capture_sample)
                
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
                capture_columns = capture_schema_df['column_name'].values
                
                # Check for common prefixes/suffixes or semantic relationships
                for capture_col in capture_columns:
                    # Skip columns already matched
                    if any(r.get('Usaspending Prime Awards Column') == capture_col for r in mapping_rows):
                        continue
                    
                    capture_type = capture_schema_df[capture_schema_df['column_name'] == capture_col]['data_type'].values[0]
                    capture_sample = capture_samples.get(capture_col, "N/A")
                    name_similarity_score = 0
                    reason = "Potential Match"  # Initialize with default value
                    
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
                    sample_similarity_score, sample_reason = self.calculate_sample_similarity(award_sample, capture_sample)
                    
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
        
        return mapping_rows

    def generate_mapping(self):
        """Generate a mapping between award_search and usaspending_prime_awards schemas with optimized performance"""
        start_time = time.time()
        logger.info("Starting optimized award to usaspending mapping generation")
        
        # Load schemas
        award_schema_df = self.load_award_schema()
        if award_schema_df is None:
            return False
            
        capture_schema_df = self.load_capture_schema()
        if capture_schema_df is None:
            return False
        
        # Create connection pools
        if not self.create_connection_pools():
            logger.error("Failed to create connection pools")
            return False
        
        try:
            # Get column lists
            award_columns = award_schema_df['column_name'].tolist()
            capture_columns = capture_schema_df['column_name'].tolist()
            
            logger.info(f"Retrieved {len(award_columns)} columns from award_search and {len(capture_columns)} columns from usaspending_prime_awards")
            
            # Use improved batch sample value retrieval
            logger.info("Retrieving sample values in batches (this may take a while)...")
            
            # Process award columns in batches
            award_samples = {}
            capture_samples = {}
            
            # Retrieve sample values efficiently in batches
            for i in tqdm(range(0, len(award_columns), COLUMN_BATCH_SIZE), desc="Award columns"):
                batch = award_columns[i:i+COLUMN_BATCH_SIZE]
                batch_samples = self.batch_get_sample_values('rpt', 'award_search', batch)
                award_samples.update(batch_samples)
            
            # Show progress with a progress bar
            for i in tqdm(range(0, len(capture_columns), COLUMN_BATCH_SIZE), desc="Capture columns"):
                batch = capture_columns[i:i+COLUMN_BATCH_SIZE]
                batch_samples = self.batch_get_sample_values('capture', 'usaspending_prime_awards', batch)
                capture_samples.update(batch_samples)
            
            logger.info("Finished retrieving sample values")
            
            # Save cache for future runs
            self.save_sample_cache()
            
            # Process mappings using parallel processing
            logger.info("Processing column mappings using parallel processing...")
            
            mapping_rows = []
            
            # Process award columns in parallel batches
            with concurrent.futures.ThreadPoolExecutor(max_workers=multiprocessing.cpu_count()) as executor:
                # Prepare batches for parallel processing
                batches = [award_columns[i:i+10] for i in range(0, len(award_columns), 10)]
                
                # Submit batch processing tasks
                futures = []
                for batch in batches:
                    future = executor.submit(
                        self.process_mapping_batch,
                        batch,
                        award_schema_df,
                        capture_schema_df,
                        award_samples,
                        capture_samples
                    )
                    futures.append(future)
                
                # Collect results as they complete
                for future in tqdm(concurrent.futures.as_completed(futures), total=len(futures), desc="Processing mappings"):
                    batch_rows = future.result()
                    mapping_rows.extend(batch_rows)
            
            # Add capture_insights columns that don't have matches
            logger.info("Adding capture-only columns...")
            for capture_col in capture_columns:
                if not any(r.get('Usaspending Prime Awards Column') == capture_col for r in mapping_rows if r.get('Match Type') != 'No Match'):
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
            
            # Save to CSV
            filename = os.path.join(OUTPUT_DIR, f"award_to_usaspending_prime_mapping_{FILE_PREFIX}.csv")
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
            
            end_time = time.time()
            execution_time = end_time - start_time
            
            logger.info(f"Award to usaspending_prime_awards mapping summary:")
            logger.info(f"  Direct matches: {direct_matches}")
            logger.info(f"  Potential matches: {potential_matches}")
            logger.info(f"  Award columns without matches: {no_matches_award}")
            logger.info(f"  Capture-only columns: {capture_only}")
            logger.info(f"  High sample similarity: {high_sample_similarity}")
            logger.info(f"  Medium sample similarity: {medium_sample_similarity}")
            logger.info(f"  No sample similarity: {no_sample_similarity}")
            logger.info(f"  Execution time: {execution_time:.2f} seconds")
            
            # Print nice summary to console
            print("\nAward to Usaspending Prime Awards Mapping Summary:")
            print(f"  Total columns mapped: {len(mapping_df)}")
            print(f"  Direct matches: {direct_matches}")
            print(f"  Potential matches: {potential_matches}")
            print(f"  Award columns without matches: {no_matches_award}")
            print(f"  Capture-only columns: {capture_only}")
            print(f"  High sample similarity: {high_sample_similarity}")
            print(f"  Medium sample similarity: {medium_sample_similarity}")
            print(f"  No sample similarity: {no_sample_similarity}")
            print(f"  Execution time: {execution_time:.2f} seconds")
            print(f"\nMapping file saved to: {filename}")
            
            return mapping_df
            
        except Exception as e:
            logger.error(f"Error generating mapping: {str(e)}", exc_info=True)
            return None
        finally:
            self.close_connection_pools()

if __name__ == "__main__":
    mapper = AwardMapper()
    mapper.generate_mapping()
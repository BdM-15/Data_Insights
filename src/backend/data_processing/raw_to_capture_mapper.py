#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Comprehensive Schema Mapper

Maps fields between multiple tables:
1. raw.source_procurement_transaction to public.usaspending_prime_awards
2. raw.source_procurement_transaction to public.usaprime_cleaned
3. rpt.award_search to public.usaprime_cleaned

This script provides a clear understanding of how data flows between various database tables
in the data processing pipeline.
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
        logging.FileHandler(os.path.join(LOGS_DIR, "raw_to_capture_mapper.log"))
    ]
)

logger = logging.getLogger("raw_to_capture_mapper")

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
os.makedirs(OUTPUT_DIR, exist_ok=True)
FILE_PREFIX = datetime.now().strftime("%Y%m%d")

# Sample value cache file
SAMPLE_CACHE_FILE = os.path.join(OUTPUT_DIR, "raw_to_capture_sample_cache.json")
COLUMN_BATCH_SIZE = 20  # Number of columns to process in a batch
CONNECTION_POOL_SIZE = min(32, multiprocessing.cpu_count() * 2)  # Use more connections for larger systems

class RawToCaptureMapper:
    """Maps raw.source_procurement_transaction to public.usaspending_prime_awards and public.usaprime_cleaned."""
    
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
    
    def get_raw_schema(self):
        """Get schema information for raw.source_procurement_transaction table"""
        try:
            conn_string = f"host={USASPENDING_PARAMS['host']} " \
                        f"port={USASPENDING_PARAMS['port']} " \
                        f"dbname={USASPENDING_PARAMS['dbname']} " \
                        f"user={USASPENDING_PARAMS['user']} " \
                        f"password={USASPENDING_PARAMS['password']}"
            
            conn = psycopg2.connect(conn_string)
            
            query = """
            SELECT 
                column_name, data_type, character_maximum_length
            FROM 
                information_schema.columns
            WHERE 
                table_schema = 'raw'
                AND table_name = 'source_procurement_transaction'
            ORDER BY 
                ordinal_position;
            """
            
            df = pd.read_sql(query, conn)
            conn.close()
            
            logger.info(f"Retrieved {len(df)} columns from raw.source_procurement_transaction table")
            return df
        except Exception as e:
            logger.error(f"Error getting raw schema: {str(e)}")
            return None
    
    def get_capture_schema(self):
        """Get schema information for public.usaspending_prime_awards table"""
        try:
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
                table_schema = 'public'
                AND table_name = 'usaspending_prime_awards'
            ORDER BY 
                ordinal_position;
            """
            
            df = pd.read_sql(query, conn)
            conn.close()
            
            logger.info(f"Retrieved {len(df)} columns from public.usaspending_prime_awards table")
            return df
        except Exception as e:
            logger.error(f"Error getting capture schema: {str(e)}")
            return None

    def get_cleaned_schema(self):
        """Get schema information for public.usaprime_cleaned table"""
        try:
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
                table_schema = 'public'
                AND table_name = 'usaprime_cleaned'
            ORDER BY 
                ordinal_position;
            """
            
            df = pd.read_sql(query, conn)
            conn.close()
            
            logger.info(f"Retrieved {len(df)} columns from public.usaprime_cleaned table")
            return df
        except Exception as e:
            logger.error(f"Error getting usaprime_cleaned schema: {str(e)}")
            return None

    def get_award_search_schema(self):
        """Get schema information for rpt.award_search table"""
        try:
            conn_string = f"host={USASPENDING_PARAMS['host']} " \
                        f"port={USASPENDING_PARAMS['port']} " \
                        f"dbname={USASPENDING_PARAMS['dbname']} " \
                        f"user={USASPENDING_PARAMS['user']} " \
                        f"password={USASPENDING_PARAMS['password']}"
            
            conn = psycopg2.connect(conn_string)
            
            query = """
            SELECT 
                column_name, data_type, character_maximum_length
            FROM 
                information_schema.columns
            WHERE 
                table_schema = 'rpt'
                AND table_name = 'award_search'
            ORDER BY 
                ordinal_position;
            """
            
            df = pd.read_sql(query, conn)
            conn.close()
            
            logger.info(f"Retrieved {len(df)} columns from rpt.award_search table")
            return df
        except Exception as e:
            logger.error(f"Error getting award_search schema: {str(e)}")
            return None

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
            if schema_name == 'public':
                if not self.capture_pool:
                    return "N/A"
                
                conn = self.capture_pool[0]  # Use the first connection
                table_full_name = f"public.usaspending_prime_awards"
            else:
                if not self.usa_pool:
                    return "N/A"
                
                conn = self.usa_pool[0]  # Use the first connection
                table_full_name = f"{schema_name}.{table_name}"
            
            query = f"""
            SELECT DISTINCT {quoted_column_name} 
            FROM {table_full_name} 
            WHERE {quoted_column_name} IS NOT NULL
            ORDER BY {quoted_column_name}
            LIMIT {limit}
            """
            
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
            if schema_name == 'public':
                pool = self.capture_pool
                if table_name == 'usaspending_prime_awards':
                    table_full_name = "public.usaspending_prime_awards"
                elif table_name == 'usaprime_cleaned':
                    table_full_name = "public.usaprime_cleaned"
                else:
                    table_full_name = f"public.{table_name}"
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

    def calculate_sample_similarity(self, raw_sample, capture_sample):
        """Compare sample values and calculate similarity score"""
        if raw_sample == "N/A" or capture_sample == "N/A":
            return 0, "Unable to compare samples"
        
        # Convert to lists of strings for comparison
        raw_sample_list = [str(s).strip().lower() for s in raw_sample.split(',')]
        capture_sample_list = [str(s).strip().lower() for s in capture_sample.split(',')]
        
        # Check for exact matches
        exact_matches = set(raw_sample_list).intersection(capture_sample_list)
        if exact_matches:
            return 3, f"Found {len(exact_matches)} exact matching values"
        
        # Check for substring matches
        substring_matches = []
        for r_val in raw_sample_list:
            for c_val in capture_sample_list:
                if r_val in c_val or c_val in r_val:
                    substring_matches.append((r_val, c_val))
        
        if substring_matches:
            return 2, f"Found {len(substring_matches)} substring matches"
        
        # Check for pattern similarity
        pattern_similarity = False
        
        # Check date patterns
        date_formats = [
            r'\d{4}-\d{2}-\d{2}',  # YYYY-MM-DD
            r'\d{2}/\d{2}/\d{4}'    # MM/DD/YYYY
        ]
        
        raw_has_dates = any(re.search(pattern, sample) for pattern in date_formats for sample in raw_sample_list)
        capture_has_dates = any(re.search(pattern, sample) for pattern in date_formats for sample in capture_sample_list)
        
        if raw_has_dates and capture_has_dates:
            pattern_similarity = True
        
        # Check numeric patterns
        raw_has_numbers = any(re.search(r'\d+\.?\d*', sample) for sample in raw_sample_list)
        capture_has_numbers = any(re.search(r'\d+\.?\d*', sample) for sample in capture_sample_list)
        
        if raw_has_numbers and capture_has_numbers:
            pattern_similarity = True
        
        if pattern_similarity:
            return 1, "Similar patterns detected in values"
        
        return 0, "No similarity detected in sample values"
    
    def process_mapping_batch(self, raw_columns_batch, raw_schema_df, capture_schema_df, raw_samples, capture_samples):
        """Process a batch of raw columns and generate mapping rows"""
        mapping_rows = []
        
        for raw_col in raw_columns_batch:
            raw_type = raw_schema_df[raw_schema_df['column_name'] == raw_col]['data_type'].values[0]
            raw_sample = raw_samples.get(raw_col, "N/A")
            
            # Check for exact column name matches
            if raw_col in capture_schema_df['column_name'].values:
                capture_type = capture_schema_df[capture_schema_df['column_name'] == raw_col]['data_type'].values[0]
                capture_sample = capture_samples.get(raw_col, "N/A")
                
                # Compare samples for data consistency
                similarity_score, similarity_reason = self.calculate_sample_similarity(raw_sample, capture_sample)
                
                mapping_rows.append({
                    'Raw Column': raw_col,
                    'Raw Data Type': raw_type,
                    'Raw Sample Values': raw_sample,
                    'Capture Column': raw_col,
                    'Capture Data Type': capture_type,
                    'Capture Sample Values': capture_sample,
                    'Match Type': 'Direct',
                    'Sample Similarity': similarity_score,
                    'Notes': f'Same column name in both tables. {similarity_reason}'
                })
            else:
                # Check for similar columns
                potential_matches = []
                capture_columns = capture_schema_df['column_name'].tolist()
                
                for capture_col in capture_columns:
                    # Skip columns already matched
                    if any(r.get('Capture Column') == capture_col for r in mapping_rows):
                        continue
                    
                    capture_type = capture_schema_df[capture_schema_df['column_name'] == capture_col]['data_type'].values[0]
                    capture_sample = capture_samples.get(capture_col, "N/A")
                    name_similarity_score = 0
                    reason = "Potential Match"
                    
                    # Check for substring matches
                    if raw_col in capture_col or capture_col in raw_col:
                        # Check if it's a prefix/suffix pattern
                        if raw_col.startswith(capture_col + '_') or capture_col.startswith(raw_col + '_'):
                            name_similarity_score += 2
                            reason = 'Prefix/Suffix Pattern'
                        
                        # Known semantic matches
                        elif (raw_col == 'awardee_or_recipient_legal' and capture_col == 'recipient_name') or \
                             (raw_col == 'awardee_or_recipient_uniqu' and capture_col == 'recipient_unique_id'):
                            name_similarity_score += 3
                            reason = 'Semantic Match'
                    
                    # Special semantic matches based on field meanings
                    elif (raw_col == 'unique_award_key' and capture_col == 'contract_award_unique_key') or \
                         (raw_col == 'award_id_piid' and capture_col == 'piid') or \
                         (raw_col == 'federal_action_obligation' and capture_col in ['total_obligation', 'total_dollars_obligated']):
                        name_similarity_score += 3
                        reason = 'Semantic Match'
                        
                    # Check for similar names with different formats
                    elif (raw_col.replace('_', '') == capture_col.replace('_', '')) or \
                         (raw_col.lower() == capture_col.lower()):
                        name_similarity_score += 2
                        reason = 'Different Format'
                        
                    # Compare data types for additional confidence
                    if raw_type == capture_type:
                        name_similarity_score += 1
                    
                    # Compare sample values for additional confidence
                    sample_similarity_score, sample_reason = self.calculate_sample_similarity(raw_sample, capture_sample)
                    
                    # Combine scores for overall similarity
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
                    # Take best match
                    match, reason, c_type, c_sample, total_score, sample_score, sample_reason = potential_matches[0]
                    confidence = "High" if total_score >= 4 else "Medium" if total_score >= 2 else "Low"
                    
                    mapping_rows.append({
                        'Raw Column': raw_col,
                        'Raw Data Type': raw_type,
                        'Raw Sample Values': raw_sample,
                        'Capture Column': match,
                        'Capture Data Type': c_type,
                        'Capture Sample Values': c_sample,
                        'Match Type': 'Potential',
                        'Sample Similarity': sample_score,
                        'Notes': f'{reason} ({confidence} confidence). {sample_reason}.'
                    })
                else:
                    # No match found
                    mapping_rows.append({
                        'Raw Column': raw_col,
                        'Raw Data Type': raw_type,
                        'Raw Sample Values': raw_sample,
                        'Capture Column': 'N/A',
                        'Capture Data Type': 'N/A',
                        'Capture Sample Values': 'N/A',
                        'Match Type': 'No Match',
                        'Sample Similarity': 0,
                        'Notes': 'No equivalent in usaspending_prime_awards table'
                    })
        
        return mapping_rows

    def generate_raw_to_cleaned_mapping(self, raw_schema_df, cleaned_schema_df, raw_samples, cleaned_samples):
        """Generate mapping between raw.source_procurement_transaction and public.usaprime_cleaned"""
        logger.info("Processing raw to cleaned mapping...")
        
        raw_columns = raw_schema_df['column_name'].tolist()
        cleaned_columns = cleaned_schema_df['column_name'].tolist()
        
        # Process mappings in parallel
        mapping_rows = []
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=multiprocessing.cpu_count()) as executor:
            # Create batches for processing
            batches = [raw_columns[i:i+10] for i in range(0, len(raw_columns), 10)]
            
            # Submit batches for parallel processing
            futures = []
            for batch in batches:
                future = executor.submit(
                    self.process_cleaned_mapping_batch,
                    batch,
                    raw_schema_df,
                    cleaned_schema_df,
                    raw_samples,
                    cleaned_samples
                )
                futures.append(future)
            
            # Collect results
            for future in tqdm(concurrent.futures.as_completed(futures), total=len(futures), desc="Processing cleaned mappings"):
                batch_rows = future.result()
                mapping_rows.extend(batch_rows)
        
        # Process cleaned-only columns
        logger.info("Processing cleaned-only columns...")
        mapped_cleaned_cols = set(row['Cleaned Column'] for row in mapping_rows if row['Match Type'] != 'No Match')
        unmapped_cleaned_cols = [col for col in cleaned_columns if col not in mapped_cleaned_cols]
        
        for cleaned_col in unmapped_cleaned_cols:
            cleaned_type = cleaned_schema_df[cleaned_schema_df['column_name'] == cleaned_col]['data_type'].values[0]
            cleaned_sample = cleaned_samples.get(cleaned_col, "N/A")
            
            mapping_rows.append({
                'Raw Column': 'N/A',
                'Raw Data Type': 'N/A',
                'Raw Sample Values': 'N/A',
                'Cleaned Column': cleaned_col,
                'Cleaned Data Type': cleaned_type,
                'Cleaned Sample Values': cleaned_sample,
                'Match Type': 'Cleaned Only',
                'Sample Similarity': 0,
                'Notes': 'No equivalent in raw.source_procurement_transaction table'
            })
        
        # Create DataFrame
        mapping_df = pd.DataFrame(mapping_rows)
        
        # Sort results
        match_type_order = {
            'Direct': 0,
            'Potential': 1,
            'No Match': 2,
            'Cleaned Only': 3
        }
        
        mapping_df['Sort Order'] = mapping_df['Match Type'].map(match_type_order)
        mapping_df = mapping_df.sort_values(['Sort Order', 'Raw Column', 'Cleaned Column'])
        mapping_df = mapping_df.drop(columns=['Sort Order'])
        
        # Save results
        output_file = os.path.join(OUTPUT_DIR, f"raw_to_usaprime_cleaned_mapping_{FILE_PREFIX}.csv")
        mapping_df.to_csv(output_file, index=False)
        
        # Generate summary statistics
        direct_matches = len(mapping_df[mapping_df['Match Type'] == 'Direct'])
        potential_matches = len(mapping_df[mapping_df['Match Type'] == 'Potential'])
        no_matches = len(mapping_df[mapping_df['Match Type'] == 'No Match'])
        cleaned_only = len(mapping_df[mapping_df['Match Type'] == 'Cleaned Only'])
        
        total_raw = len(raw_columns)
        total_cleaned = len(cleaned_columns)
        mapped_raw = direct_matches + potential_matches
        mapping_coverage = (mapped_raw / total_raw) * 100 if total_raw > 0 else 0
        
        # Print summary
        logger.info(f"Raw to Cleaned mapping summary:")
        logger.info(f"  Direct matches: {direct_matches}")
        logger.info(f"  Potential matches: {potential_matches}")
        logger.info(f"  Raw columns without matches: {no_matches}")
        logger.info(f"  Cleaned-only columns: {cleaned_only}")
        logger.info(f"  Raw columns mapped: {mapped_raw}/{total_raw} ({mapping_coverage:.1f}%)")
        
        # Print nice summary for user
        print("\nRaw to UsaPrime Cleaned Mapping Summary:")
        print(f"  Total raw.source_procurement_transaction columns: {total_raw}")
        print(f"  Total public.usaprime_cleaned columns: {total_cleaned}")
        print(f"  Direct matches: {direct_matches}")
        print(f"  Potential matches: {potential_matches}")
        print(f"  Raw columns without matches: {no_matches}")
        print(f"  Cleaned-only columns: {cleaned_only}")
        print(f"  Raw columns mapped: {mapped_raw}/{total_raw} ({mapping_coverage:.1f}%)")
        print(f"\nMapping file saved to: {output_file}")
        
        return mapping_df

    def process_cleaned_mapping_batch(self, raw_columns_batch, raw_schema_df, cleaned_schema_df, raw_samples, cleaned_samples):
        """Process a batch of raw columns for mapping to cleaned columns"""
        mapping_rows = []
        
        for raw_col in raw_columns_batch:
            raw_type = raw_schema_df[raw_schema_df['column_name'] == raw_col]['data_type'].values[0]
            raw_sample = raw_samples.get(raw_col, "N/A")
            
            # Check for exact column name matches
            if raw_col in cleaned_schema_df['column_name'].values:
                cleaned_type = cleaned_schema_df[cleaned_schema_df['column_name'] == raw_col]['data_type'].values[0]
                cleaned_sample = cleaned_samples.get(raw_col, "N/A")
                
                # Compare samples for data consistency
                similarity_score, similarity_reason = self.calculate_sample_similarity(raw_sample, cleaned_sample)
                
                mapping_rows.append({
                    'Raw Column': raw_col,
                    'Raw Data Type': raw_type,
                    'Raw Sample Values': raw_sample,
                    'Cleaned Column': raw_col,
                    'Cleaned Data Type': cleaned_type,
                    'Cleaned Sample Values': cleaned_sample,
                    'Match Type': 'Direct',
                    'Sample Similarity': similarity_score,
                    'Notes': f'Same column name in both tables. {similarity_reason}'
                })
            else:
                # Check for similar columns
                potential_matches = []
                cleaned_columns = cleaned_schema_df['column_name'].tolist()
                
                for cleaned_col in cleaned_columns:
                    # Skip columns already matched
                    if any(r.get('Cleaned Column') == cleaned_col for r in mapping_rows):
                        continue
                    
                    cleaned_type = cleaned_schema_df[cleaned_schema_df['column_name'] == cleaned_col]['data_type'].values[0]
                    cleaned_sample = cleaned_samples.get(cleaned_col, "N/A")
                    name_similarity_score = 0
                    reason = "Potential Match"
                    
                    # Check for substring matches
                    if raw_col in cleaned_col or cleaned_col in raw_col:
                        # Check if it's a prefix/suffix pattern
                        if raw_col.startswith(cleaned_col + '_') or cleaned_col.startswith(raw_col + '_'):
                            name_similarity_score += 2
                            reason = 'Prefix/Suffix Pattern'
                        
                        # Known semantic matches
                        elif (raw_col == 'awardee_or_recipient_legal' and cleaned_col == 'recipient_name') or \
                             (raw_col == 'awardee_or_recipient_uniqu' and cleaned_col == 'duns_number'):
                            name_similarity_score += 3
                            reason = 'Semantic Match'
                    
                    # Special semantic matches based on field meanings
                    elif (raw_col == 'unique_award_key' and cleaned_col == 'contract_award_unique_key') or \
                         (raw_col == 'award_id_piid' and cleaned_col == 'piid') or \
                         (raw_col == 'federal_action_obligation' and cleaned_col in ['total_obligation', 'dollars_obligated']):
                        name_similarity_score += 3
                        reason = 'Semantic Match'
                        
                    # Check for similar names with different formats
                    elif (raw_col.replace('_', '') == cleaned_col.replace('_', '')) or \
                         (raw_col.lower() == cleaned_col.lower()):
                        name_similarity_score += 2
                        reason = 'Different Format'
                        
                    # Compare data types for additional confidence
                    if raw_type == cleaned_type:
                        name_similarity_score += 1
                    
                    # Compare sample values for additional confidence
                    sample_similarity_score, sample_reason = self.calculate_sample_similarity(raw_sample, cleaned_sample)
                    
                    # Combine scores for overall similarity
                    total_similarity_score = name_similarity_score + sample_similarity_score
                    
                    if total_similarity_score > 0:
                        potential_matches.append((
                            cleaned_col,
                            reason,
                            cleaned_type,
                            cleaned_sample,
                            total_similarity_score,
                            sample_similarity_score,
                            sample_reason
                        ))
                
                # Sort potential matches by similarity score
                potential_matches.sort(key=lambda x: x[4], reverse=True)
                
                if potential_matches:
                    # Take best match
                    match, reason, c_type, c_sample, total_score, sample_score, sample_reason = potential_matches[0]
                    confidence = "High" if total_score >= 4 else "Medium" if total_score >= 2 else "Low"
                    
                    mapping_rows.append({
                        'Raw Column': raw_col,
                        'Raw Data Type': raw_type,
                        'Raw Sample Values': raw_sample,
                        'Cleaned Column': match,
                        'Cleaned Data Type': c_type,
                        'Cleaned Sample Values': c_sample,
                        'Match Type': 'Potential',
                        'Sample Similarity': sample_score,
                        'Notes': f'{reason} ({confidence} confidence). {sample_reason}.'
                    })
                else:
                    # No match found
                    mapping_rows.append({
                        'Raw Column': raw_col,
                        'Raw Data Type': raw_type,
                        'Raw Sample Values': raw_sample,
                        'Cleaned Column': 'N/A',
                        'Cleaned Data Type': 'N/A',
                        'Cleaned Sample Values': 'N/A',
                        'Match Type': 'No Match',
                        'Sample Similarity': 0,
                        'Notes': 'No equivalent in usaprime_cleaned table'
                    })
        
        return mapping_rows

    def process_award_to_cleaned_mapping_batch(self, award_columns_batch, award_schema_df, cleaned_schema_df, award_samples, cleaned_samples):
        """Process a batch of award columns for mapping to cleaned columns"""
        mapping_rows = []
        
        for award_col in award_columns_batch:
            award_type = award_schema_df[award_schema_df['column_name'] == award_col]['data_type'].values[0]
            award_sample = award_samples.get(award_col, "N/A")
            
            # Check for exact column name matches
            if award_col in cleaned_schema_df['column_name'].values:
                cleaned_type = cleaned_schema_df[cleaned_schema_df['column_name'] == award_col]['data_type'].values[0]
                cleaned_sample = cleaned_samples.get(award_col, "N/A")
                
                # Compare samples for data consistency
                similarity_score, similarity_reason = self.calculate_sample_similarity(award_sample, cleaned_sample)
                
                mapping_rows.append({
                    'Award Search Column': award_col,
                    'Award Search Data Type': award_type,
                    'Award Search Sample Values': award_sample,
                    'Cleaned Column': award_col,
                    'Cleaned Data Type': cleaned_type,
                    'Cleaned Sample Values': cleaned_sample,
                    'Match Type': 'Direct',
                    'Sample Similarity': similarity_score,
                    'Notes': f'Same column name in both tables. {similarity_reason}'
                })
            else:
                # Check for similar columns
                potential_matches = []
                cleaned_columns = cleaned_schema_df['column_name'].tolist()
                
                for cleaned_col in cleaned_columns:
                    # Skip columns already matched
                    if any(r.get('Cleaned Column') == cleaned_col for r in mapping_rows):
                        continue
                    
                    cleaned_type = cleaned_schema_df[cleaned_schema_df['column_name'] == cleaned_col]['data_type'].values[0]
                    cleaned_sample = cleaned_samples.get(cleaned_col, "N/A")
                    name_similarity_score = 0
                    reason = "Potential Match"
                    
                    # Check for substring matches
                    if award_col in cleaned_col or cleaned_col in award_col:
                        # Check if it's a prefix/suffix pattern
                        if award_col.startswith(cleaned_col + '_') or cleaned_col.startswith(award_col + '_'):
                            name_similarity_score += 2
                            reason = 'Prefix/Suffix Pattern'
                        
                        # Known semantic matches
                        elif (award_col == 'recipient_name' and cleaned_col == 'recipient_name') or \
                             (award_col == 'recipient_duns' and cleaned_col == 'duns_number'):
                            name_similarity_score += 3
                            reason = 'Semantic Match'
                    
                    # Special semantic matches based on field meanings
                    elif (award_col == 'award_id_piid' and cleaned_col == 'piid') or \
                         (award_col == 'award_amount' and cleaned_col in ['total_obligation', 'dollars_obligated']) or \
                         (award_col == 'awarding_agency_name' and cleaned_col == 'awarding_agency'):
                        name_similarity_score += 3
                        reason = 'Semantic Match'
                        
                    # Check for similar names with different formats
                    elif (award_col.replace('_', '') == cleaned_col.replace('_', '')) or \
                         (award_col.lower() == cleaned_col.lower()):
                        name_similarity_score += 2
                        reason = 'Different Format'
                        
                    # Compare data types for additional confidence
                    if award_type == cleaned_type:
                        name_similarity_score += 1
                    
                    # Compare sample values for additional confidence
                    sample_similarity_score, sample_reason = self.calculate_sample_similarity(award_sample, cleaned_sample)
                    
                    # Combine scores for overall similarity
                    total_similarity_score = name_similarity_score + sample_similarity_score
                    
                    if total_similarity_score > 0:
                        potential_matches.append((
                            cleaned_col,
                            reason,
                            cleaned_type,
                            cleaned_sample,
                            total_similarity_score,
                            sample_similarity_score,
                            sample_reason
                        ))
                
                # Sort potential matches by similarity score
                potential_matches.sort(key=lambda x: x[4], reverse=True)
                
                if potential_matches:
                    # Take best match
                    match, reason, c_type, c_sample, total_score, sample_score, sample_reason = potential_matches[0]
                    confidence = "High" if total_score >= 4 else "Medium" if total_score >= 2 else "Low"
                    
                    mapping_rows.append({
                        'Award Search Column': award_col,
                        'Award Search Data Type': award_type,
                        'Award Search Sample Values': award_sample,
                        'Cleaned Column': match,
                        'Cleaned Data Type': c_type,
                        'Cleaned Sample Values': c_sample,
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
                        'Cleaned Column': 'N/A',
                        'Cleaned Data Type': 'N/A',
                        'Cleaned Sample Values': 'N/A',
                        'Match Type': 'No Match',
                        'Sample Similarity': 0,
                        'Notes': 'No equivalent in usaprime_cleaned table'
                    })
        
        return mapping_rows
        
    def generate_award_search_to_cleaned_mapping(self, award_schema_df, cleaned_schema_df, award_samples, cleaned_samples):
        """Generate mapping between rpt.award_search and public.usaprime_cleaned"""
        logger.info("Processing award search to cleaned mapping...")
        
        award_columns = award_schema_df['column_name'].tolist()
        cleaned_columns = cleaned_schema_df['column_name'].tolist()
        
        # Process mappings in parallel
        mapping_rows = []
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=multiprocessing.cpu_count()) as executor:
            # Create batches for processing
            batches = [award_columns[i:i+10] for i in range(0, len(award_columns), 10)]
            
            # Submit batches for parallel processing
            futures = []
            for batch in batches:
                future = executor.submit(
                    self.process_award_to_cleaned_mapping_batch,
                    batch,
                    award_schema_df,
                    cleaned_schema_df,
                    award_samples,
                    cleaned_samples
                )
                futures.append(future)
            
            # Collect results
            for future in tqdm(concurrent.futures.as_completed(futures), total=len(futures), desc="Processing award to cleaned mappings"):
                batch_rows = future.result()
                mapping_rows.extend(batch_rows)
        
        # Process cleaned-only columns
        logger.info("Processing cleaned-only columns...")
        mapped_cleaned_cols = set(row['Cleaned Column'] for row in mapping_rows if row['Match Type'] != 'No Match')
        unmapped_cleaned_cols = [col for col in cleaned_columns if col not in mapped_cleaned_cols]
        
        for cleaned_col in unmapped_cleaned_cols:
            cleaned_type = cleaned_schema_df[cleaned_schema_df['column_name'] == cleaned_col]['data_type'].values[0]
            cleaned_sample = cleaned_samples.get(cleaned_col, "N/A")
            
            mapping_rows.append({
                'Award Search Column': 'N/A',
                'Award Search Data Type': 'N/A',
                'Award Search Sample Values': 'N/A',
                'Cleaned Column': cleaned_col,
                'Cleaned Data Type': cleaned_type,
                'Cleaned Sample Values': cleaned_sample,
                'Match Type': 'Cleaned Only',
                'Sample Similarity': 0,
                'Notes': 'No equivalent in rpt.award_search table'
            })
        
        # Create DataFrame
        mapping_df = pd.DataFrame(mapping_rows)
        
        # Sort results
        match_type_order = {
            'Direct': 0,
            'Potential': 1,
            'No Match': 2,
            'Cleaned Only': 3
        }
        
        mapping_df['Sort Order'] = mapping_df['Match Type'].map(match_type_order)
        mapping_df = mapping_df.sort_values(['Sort Order', 'Award Search Column', 'Cleaned Column'])
        mapping_df = mapping_df.drop(columns=['Sort Order'])
        
        # Save results
        output_file = os.path.join(OUTPUT_DIR, f"award_search_to_usaprime_cleaned_mapping_{FILE_PREFIX}.csv")
        mapping_df.to_csv(output_file, index=False)
        
        # Generate summary statistics
        direct_matches = len(mapping_df[mapping_df['Match Type'] == 'Direct'])
        potential_matches = len(mapping_df[mapping_df['Match Type'] == 'Potential'])
        no_matches = len(mapping_df[mapping_df['Match Type'] == 'No Match'])
        cleaned_only = len(mapping_df[mapping_df['Match Type'] == 'Cleaned Only'])
        
        total_award = len(award_columns)
        total_cleaned = len(cleaned_columns)
        mapped_award = direct_matches + potential_matches
        mapping_coverage = (mapped_award / total_award) * 100 if total_award > 0 else 0
        
        # Print summary
        logger.info(f"Award Search to Cleaned mapping summary:")
        logger.info(f"  Direct matches: {direct_matches}")
        logger.info(f"  Potential matches: {potential_matches}")
        logger.info(f"  Award Search columns without matches: {no_matches}")
        logger.info(f"  Cleaned-only columns: {cleaned_only}")
        logger.info(f"  Award Search columns mapped: {mapped_award}/{total_award} ({mapping_coverage:.1f}%)")
        
        # Print nice summary for user
        print("\nAward Search to UsaPrime Cleaned Mapping Summary:")
        print(f"  Total rpt.award_search columns: {total_award}")
        print(f"  Total public.usaprime_cleaned columns: {total_cleaned}")
        print(f"  Direct matches: {direct_matches}")
        print(f"  Potential matches: {potential_matches}")
        print(f"  Award Search columns without matches: {no_matches}")
        print(f"  Cleaned-only columns: {cleaned_only}")
        print(f"  Award Search columns mapped: {mapped_award}/{total_award} ({mapping_coverage:.1f}%)")
        print(f"\nMapping file saved to: {output_file}")
        
        return mapping_df

    def generate_mapping(self):
        """Generate the mappings between raw.source_procurement_transaction and various capture tables"""
        start_time = time.time()
        logger.info("Starting raw to capture mapping generation")
        
        # Get schemas
        raw_schema_df = self.get_raw_schema()
        if raw_schema_df is None:
            return None
            
        capture_schema_df = self.get_capture_schema()
        if capture_schema_df is None:
            return None
            
        cleaned_schema_df = self.get_cleaned_schema()
        if cleaned_schema_df is None:
            logger.warning("Could not retrieve usaprime_cleaned schema. Only generating raw to usaspending_prime_awards mapping.")
            cleaned_schema_df = pd.DataFrame(columns=["column_name", "data_type", "character_maximum_length"])
        
        award_search_schema_df = self.get_award_search_schema()
        if award_search_schema_df is None:
            logger.warning("Could not retrieve award_search schema. Only generating raw to usaspending_prime_awards and raw to usaprime_cleaned mappings.")
            award_search_schema_df = pd.DataFrame(columns=["column_name", "data_type", "character_maximum_length"])
        
        # Create connection pools
        if not self.create_connection_pools():
            logger.error("Failed to create connection pools")
            return None
        
        try:
            # Get column lists
            raw_columns = raw_schema_df['column_name'].tolist()
            capture_columns = capture_schema_df['column_name'].tolist()
            cleaned_columns = cleaned_schema_df['column_name'].tolist()
            award_search_columns = award_search_schema_df['column_name'].tolist()
            
            logger.info(f"Processing mappings between {len(raw_columns)} raw columns, {len(capture_columns)} capture columns, {len(cleaned_columns)} cleaned columns, and {len(award_search_columns)} award search columns")
            
            # Use batch sample retrieval for better performance
            logger.info("Retrieving sample values in batches (this may take a while)...")
            
            # Get sample values for raw columns
            raw_samples = {}
            for i in tqdm(range(0, len(raw_columns), COLUMN_BATCH_SIZE), desc="Raw columns"):
                batch = raw_columns[i:i+COLUMN_BATCH_SIZE]
                batch_samples = self.batch_get_sample_values('raw', 'source_procurement_transaction', batch)
                raw_samples.update(batch_samples)
            
            # Get sample values for usaspending_prime_awards columns
            capture_samples = {}
            for i in tqdm(range(0, len(capture_columns), COLUMN_BATCH_SIZE), desc="Capture columns"):
                batch = capture_columns[i:i+COLUMN_BATCH_SIZE]
                batch_samples = self.batch_get_sample_values('public', 'usaspending_prime_awards', batch)
                capture_samples.update(batch_samples)
                
            # Get sample values for usaprime_cleaned columns
            cleaned_samples = {}
            if len(cleaned_columns) > 0:
                for i in tqdm(range(0, len(cleaned_columns), COLUMN_BATCH_SIZE), desc="Cleaned columns"):
                    batch = cleaned_columns[i:i+COLUMN_BATCH_SIZE]
                    batch_samples = self.batch_get_sample_values('public', 'usaprime_cleaned', batch)
                    cleaned_samples.update(batch_samples)
            
            # Get sample values for award_search columns
            award_search_samples = {}
            if len(award_search_columns) > 0:
                for i in tqdm(range(0, len(award_search_columns), COLUMN_BATCH_SIZE), desc="Award Search columns"):
                    batch = award_search_columns[i:i+COLUMN_BATCH_SIZE]
                    batch_samples = self.batch_get_sample_values('rpt', 'award_search', batch)
                    award_search_samples.update(batch_samples)
            
            # Save sample cache
            self.save_sample_cache()
            
            # Process mappings in parallel
            logger.info("Processing column mappings using parallel processing...")
            
            # Process raw columns in batches for usaspending_prime_awards mapping
            mapping_rows = []
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=multiprocessing.cpu_count()) as executor:
                # Create batches for processing
                batches = [raw_columns[i:i+10] for i in range(0, len(raw_columns), 10)]
                
                # Submit batches for parallel processing
                futures = []
                for batch in batches:
                    future = executor.submit(
                        self.process_mapping_batch,
                        batch,
                        raw_schema_df,
                        capture_schema_df,
                        raw_samples,
                        capture_samples
                    )
                    futures.append(future)
                
                # Collect results
                for future in tqdm(concurrent.futures.as_completed(futures), total=len(futures), desc="Processing prime mappings"):
                    batch_rows = future.result()
                    mapping_rows.extend(batch_rows)
            
            # Process capture-only columns
            logger.info("Processing capture-only columns...")
            mapped_capture_cols = set(row['Capture Column'] for row in mapping_rows if row['Match Type'] != 'No Match')
            unmapped_capture_cols = [col for col in capture_columns if col not in mapped_capture_cols]
            
            for capture_col in unmapped_capture_cols:
                capture_type = capture_schema_df[capture_schema_df['column_name'] == capture_col]['data_type'].values[0]
                capture_sample = capture_samples.get(capture_col, "N/A")
                
                mapping_rows.append({
                    'Raw Column': 'N/A',
                    'Raw Data Type': 'N/A',
                    'Raw Sample Values': 'N/A',
                    'Capture Column': capture_col,
                    'Capture Data Type': capture_type,
                    'Capture Sample Values': capture_sample,
                    'Match Type': 'Capture Only',
                    'Sample Similarity': 0,
                    'Notes': 'No equivalent in raw.source_procurement_transaction table'
                })
            
            # Create DataFrame for prime awards
            mapping_df = pd.DataFrame(mapping_rows)
            
            # Sort results
            match_type_order = {
                'Direct': 0,
                'Potential': 1,
                'No Match': 2,
                'Capture Only': 3
            }
            
            mapping_df['Sort Order'] = mapping_df['Match Type'].map(match_type_order)
            mapping_df = mapping_df.sort_values(['Sort Order', 'Raw Column', 'Capture Column'])
            mapping_df = mapping_df.drop(columns=['Sort Order'])
            
            # Save results for prime awards
            output_file = os.path.join(OUTPUT_DIR, f"raw_to_usaspending_prime_mapping_{FILE_PREFIX}.csv")
            mapping_df.to_csv(output_file, index=False)
            
            # Generate summary statistics for prime awards
            direct_matches = len(mapping_df[mapping_df['Match Type'] == 'Direct'])
            potential_matches = len(mapping_df[mapping_df['Match Type'] == 'Potential'])
            no_matches = len(mapping_df[mapping_df['Match Type'] == 'No Match'])
            capture_only = len(mapping_df[mapping_df['Match Type'] == 'Capture Only'])
            
            total_raw = len(raw_columns)
            total_capture = len(capture_columns)
            mapped_raw = direct_matches + potential_matches
            mapping_coverage = (mapped_raw / total_raw) * 100 if total_raw > 0 else 0
            
            # Generate mapping for usaprime_cleaned if schema is available
            cleaned_mapping_df = None
            if len(cleaned_columns) > 0:
                cleaned_mapping_df = self.generate_raw_to_cleaned_mapping(raw_schema_df, cleaned_schema_df, raw_samples, cleaned_samples)
            
            # Generate mapping for award_search to usaprime_cleaned if schema is available
            award_search_mapping_df = None
            if len(award_search_columns) > 0:
                award_search_mapping_df = self.generate_award_search_to_cleaned_mapping(award_search_schema_df, cleaned_schema_df, award_search_samples, cleaned_samples)
            
            # Calculate execution time
            end_time = time.time()
            execution_time = end_time - start_time
            
            # Print summary for prime awards
            logger.info(f"Raw to Capture mapping summary:")
            logger.info(f"  Direct matches: {direct_matches}")
            logger.info(f"  Potential matches: {potential_matches}")
            logger.info(f"  Raw columns without matches: {no_matches}")
            logger.info(f"  Capture-only columns: {capture_only}")
            logger.info(f"  Raw columns mapped: {mapped_raw}/{total_raw} ({mapping_coverage:.1f}%)")
            logger.info(f"  Execution time: {execution_time:.2f} seconds")
            
            # Print nice summary for user
            print("\nRaw to Usaspending Prime Awards Mapping Summary:")
            print(f"  Total raw.source_procurement_transaction columns: {total_raw}")
            print(f"  Total public.usaspending_prime_awards columns: {total_capture}")
            print(f"  Direct matches: {direct_matches}")
            print(f"  Potential matches: {potential_matches}")
            print(f"  Raw columns without matches: {no_matches}")
            print(f"  Capture-only columns: {capture_only}")
            print(f"  Raw columns mapped: {mapped_raw}/{total_raw} ({mapping_coverage:.1f}%)")
            print(f"  Execution time: {execution_time:.2f} seconds")
            print(f"\nMapping file saved to: {output_file}")
            
            return {
                'prime_mapping': mapping_df,
                'cleaned_mapping': cleaned_mapping_df,
                'award_search_mapping': award_search_mapping_df
            }
            
        except Exception as e:
            logger.error(f"Error generating raw to capture mapping: {str(e)}", exc_info=True)
            return None
        finally:
            self.close_connection_pools()

if __name__ == "__main__":
    import sys
    
    # Check for command line arguments
    if len(sys.argv) > 1 and sys.argv[1] == "--award-to-cleaned-only":
        # Run only the award_search to usaprime_cleaned mapping
        print("Running award_search to usaprime_cleaned mapping only...")
        mapper = RawToCaptureMapper()
        
        # Create connection pools
        if not mapper.create_connection_pools():
            logger.error("Failed to create connection pools")
            sys.exit(1)
            
        try:
            # Get required schemas
            award_search_schema_df = mapper.get_award_search_schema()
            if award_search_schema_df is None:
                logger.error("Could not retrieve award_search schema.")
                sys.exit(1)
                
            cleaned_schema_df = mapper.get_cleaned_schema()
            if cleaned_schema_df is None:
                logger.error("Could not retrieve usaprime_cleaned schema.")
                sys.exit(1)
                
            # Get column lists
            award_search_columns = award_search_schema_df['column_name'].tolist()
            cleaned_columns = cleaned_schema_df['column_name'].tolist()
            
            # Get sample values for award_search columns
            award_search_samples = {}
            for i in tqdm(range(0, len(award_search_columns), COLUMN_BATCH_SIZE), desc="Award Search columns"):
                batch = award_search_columns[i:i+COLUMN_BATCH_SIZE]
                batch_samples = mapper.batch_get_sample_values('rpt', 'award_search', batch)
                award_search_samples.update(batch_samples)
            
            # Get sample values for usaprime_cleaned columns
            cleaned_samples = {}
            for i in tqdm(range(0, len(cleaned_columns), COLUMN_BATCH_SIZE), desc="Cleaned columns"):
                batch = cleaned_columns[i:i+COLUMN_BATCH_SIZE]
                batch_samples = mapper.batch_get_sample_values('public', 'usaprime_cleaned', batch)
                cleaned_samples.update(batch_samples)
                
            # Save sample cache
            mapper.save_sample_cache()
            
            # Generate the mapping
            mapper.generate_award_search_to_cleaned_mapping(award_search_schema_df, cleaned_schema_df, award_search_samples, cleaned_samples)
            
        except Exception as e:
            logger.error(f"Error in award_search to usaprime_cleaned mapping: {str(e)}", exc_info=True)
            sys.exit(1)
        finally:
            mapper.close_connection_pools()
    else:
        # Run all mappings
        mapper = RawToCaptureMapper()
        mapper.generate_mapping()
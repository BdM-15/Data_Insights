"""
Database utility module for PostgreSQL operations.
Provides connection management and common database operations.
"""

import os
import sys
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd
from sqlalchemy import create_engine, Table, Column, MetaData, String, text
from sqlalchemy.exc import SQLAlchemyError
import logging

# Add the project root to the path to ensure imports work correctly
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../")))

# Import from project config
from config import get_db_config

logger = logging.getLogger(__name__)

def get_db_engine():
    """
    Create and return a SQLAlchemy engine for PostgreSQL connection.
    Uses the configuration from config.py.
    
    Returns:
        SQLAlchemy engine instance for database connection
    """
    try:
        # Get PostgreSQL connection details from config
        pg_config = get_db_config()
        pg_user = pg_config.get("PG_USER")
        pg_password = pg_config.get("PG_PASSWORD")
        pg_host = pg_config.get("PG_HOST")
        pg_port = pg_config.get("PG_PORT")
        pg_dbname = pg_config.get("PG_DBNAME")
        
        # Create connection string and engine
        db_url = f"postgresql://{pg_user}:{pg_password}@{pg_host}:{pg_port}/{pg_dbname}"
        engine = create_engine(db_url)
        
        return engine
    except Exception as e:
        logger.error(f"Failed to create database engine: {str(e)}")
        raise

def get_engine():
    """
    Legacy function for backward compatibility.
    
    Returns:
        SQLAlchemy engine object
    """
    return get_db_engine()

def ensure_table_exists(table_name: str, df: Optional[pd.DataFrame] = None) -> bool:
    """
    Ensure that a table exists in the database, create it if it doesn't.
    
    Args:
        table_name: Name of the table to check/create
        df: Optional DataFrame with column structure to use if table needs to be created
        
    Returns:
        bool: True if table exists or was created, False on error
    """
    try:
        engine = get_engine()
        metadata = MetaData()
        
        with engine.connect() as connection:
            # Check if table exists
            result = connection.execute(text(
                f"SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = '{table_name}')"
            ))
            table_exists = result.scalar()
            
            if not table_exists and df is not None:
                # Preserve original column names exactly as they are
                # Create table with DataFrame columns using original case
                columns = [Column(col, String) for col in df.columns]
                Table(table_name, metadata, *columns)
                metadata.create_all(engine)
                logger.info(f"Created table {table_name} with original column names preserved")
                return True
                
        return table_exists
    except SQLAlchemyError as e:
        logger.error(f"Database error when ensuring table {table_name} exists: {str(e)}")
        return False

def insert_dataframe(df: pd.DataFrame, table_name: str, if_exists: str = 'append') -> bool:
    """
    Insert a pandas DataFrame into a database table.
    
    Args:
        df: DataFrame to insert
        table_name: Target table name
        if_exists: Strategy if table exists ('fail', 'replace', or 'append')
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        engine = get_engine()
        
        # Ensure the table exists with the right structure
        ensure_table_exists(table_name, df)
        
        # Insert the data
        df.to_sql(
            name=table_name,
            con=engine,
            if_exists=if_exists,
            index=False,
            method='multi',
            chunksize=5000
        )
        logger.info(f"Inserted {len(df)} rows into table {table_name}")
        return True
    except SQLAlchemyError as e:
        logger.error(f"Database error when inserting into table {table_name}: {str(e)}")
        return False

def insert_with_deduplication(df: pd.DataFrame, table_name: str, unique_id_field: str) -> bool:
    """
    Insert a DataFrame into a table with deduplication based on a unique ID field.
    
    Args:
        df: DataFrame to insert
        table_name: Target table name
        unique_id_field: Column name to use for identifying duplicates
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        engine = get_engine()
        
        # Create a temp table with the same name but a prefix
        temp_table = f"temp_{table_name}"
        
        # Save original DataFrame to temp table (preserving case of column names)
        df.to_sql(
            name=temp_table,
            con=engine,
            if_exists='replace',
            index=False
        )
        
        # Perform the merge operation with proper case handling
        with engine.connect() as connection:
            # Check if main table exists, create it if not
            table_exists = connection.execute(text(
                f"SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = '{table_name}')"
            )).scalar()
            
            if not table_exists:
                # Create main table with same structure as temp table if it doesn't exist
                connection.execute(text(f'CREATE TABLE "{table_name}" AS SELECT * FROM "{temp_table}" WHERE 1=0'))
                connection.commit()
                logger.info(f"Created table {table_name}")
                print(f"Created table {table_name}")
            
            # Get column names from both tables to properly handle case sensitivity
            main_table_cols = connection.execute(text(
                f"SELECT column_name FROM information_schema.columns WHERE table_name = '{table_name}'"
            ))
            main_columns = [row[0] for row in main_table_cols.fetchall()]
            
            temp_table_cols = connection.execute(text(
                f"SELECT column_name FROM information_schema.columns WHERE table_name = '{temp_table}'"
            ))
            temp_columns = [row[0] for row in temp_table_cols.fetchall()]
            
            # Find the actual case of the unique ID column in both tables
            main_unique_id_col = None
            temp_unique_id_col = None
            
            for col in main_columns:
                if col.lower() == unique_id_field.lower():
                    main_unique_id_col = col
                    break
            
            for col in temp_columns:
                if col.lower() == unique_id_field.lower():
                    temp_unique_id_col = col
                    break
            
            if not main_unique_id_col:
                logger.error(f"Unique ID column '{unique_id_field}' not found in main table {table_name}")
                print(f"Error: Unique ID column '{unique_id_field}' not found in main table {table_name}")
                if main_columns:
                    logger.info(f"Available columns in main table: {', '.join(main_columns)}")
                    print(f"Available columns in main table: {', '.join(main_columns)}")
                return False
                
            if not temp_unique_id_col:
                logger.error(f"Unique ID column '{unique_id_field}' not found in temp table")
                print(f"Error: Unique ID column '{unique_id_field}' not found in temp table")
                if temp_columns:
                    logger.info(f"Available columns in temp table: {', '.join(temp_columns)}")
                    print(f"Available columns in temp table: {', '.join(temp_columns)}")
                return False
            
            # Find common columns between the tables (case-insensitive matching)
            common_columns = []
            for main_col in main_columns:
                for temp_col in temp_columns:
                    if main_col.lower() == temp_col.lower():
                        common_columns.append({
                            'main_col': main_col,
                            'temp_col': temp_col
                        })
                        break
            
            # Check if there are any records in the main table
            count_result = connection.execute(text(f'SELECT COUNT(*) FROM "{table_name}"'))
            count = count_result.scalar()
            
            if count > 0:
                # Delete records in the main table that exist in the temp table (by unique ID)
                # Use proper column case in the SQL query
                connection.execute(text(
                    f'DELETE FROM "{table_name}" WHERE "{main_unique_id_col}" IN '
                    f'(SELECT "{temp_unique_id_col}" FROM "{temp_table}")'
                ))
            
            # Insert records from temp table to main table
            # Build column lists for INSERT using the exact column names from each table
            main_cols = [f'"{col["main_col"]}"' for col in common_columns]
            temp_cols = [f'"{col["temp_col"]}"' for col in common_columns]
            
            if not main_cols or not temp_cols:
                logger.error(f"No common columns found between tables")
                print(f"Error: No common columns found between tables")
                return False
                
            main_cols_str = ", ".join(main_cols)
            temp_cols_str = ", ".join(temp_cols)
            
            # Execute the INSERT with proper column names
            connection.execute(text(
                f'INSERT INTO "{table_name}" ({main_cols_str}) SELECT {temp_cols_str} FROM "{temp_table}"'
            ))
            
            # Drop the temporary table
            connection.execute(text(f'DROP TABLE IF EXISTS "{temp_table}"'))
            
            connection.commit()
            
            # Get final row count
            count_after = connection.execute(text(f'SELECT COUNT(*) FROM "{table_name}"')).scalar()
            
            logger.info(f"Inserted data into {table_name} with deduplication. Total records: {count_after}")
            print(f"Inserted data into {table_name} with deduplication. Total records: {count_after}")
            
            return True
    except SQLAlchemyError as e:
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

def get_last_fetched_date(table_name: str) -> Optional[str]:
    """
    Get the last fetched date from a progress tracking table.
    
    Args:
        table_name: Source table name to check
        
    Returns:
        Optional[str]: Last fetched date as string or None if not found
    """
    try:
        engine = get_engine()
        # Create progress tracking table if it doesn't exist
        with engine.connect() as connection:
            connection.execute(text("""
                CREATE TABLE IF NOT EXISTS fetch_progress (
                    table_name VARCHAR(255) PRIMARY KEY,
                    last_fetched_date DATE
                )
            """))
            connection.commit()
            
            # Query the last fetched date
            result = connection.execute(text(
                "SELECT last_fetched_date FROM fetch_progress WHERE table_name = :table_name"
            ), {"table_name": table_name})
            row = result.fetchone()
            
            if (row and row[0]):
                return str(row[0])
            return None
    except SQLAlchemyError as e:
        logger.error(f"Database error when getting last fetched date for {table_name}: {str(e)}")
        return None

def update_last_fetched_date(table_name: str, date_str: str) -> bool:
    """
    Update the last fetched date in the progress tracking table.
    
    Args:
        table_name: Source table name
        date_str: Date string to store in ISO format (YYYY-MM-DD)
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        engine = get_engine()
        with engine.connect() as connection:
            connection.execute(text("""
                INSERT INTO fetch_progress (table_name, last_fetched_date) 
                VALUES (:table_name, :date)
                ON CONFLICT (table_name) 
                DO UPDATE SET last_fetched_date = :date
            """), {"table_name": table_name, "date": date_str})
            connection.commit()
            logger.info(f"Updated last fetched date for {table_name} to {date_str}")
            return True
    except SQLAlchemyError as e:
        logger.error(f"Database error when updating last fetched date for {table_name}: {str(e)}")
        return False

def handle_schema_changes(df: pd.DataFrame, table_name: str) -> bool:
    """
    Detect and handle schema changes between incoming data and existing table.
    
    This function identifies columns in the DataFrame that don't exist in the 
    target database table and adds them dynamically, allowing the data structure
    to evolve over time without requiring manual table recreation.
    
    Args:
        df: DataFrame with potentially new data structure
        table_name: Target table name
        
    Returns:
        bool: True if schema was changed/updated, False otherwise
    """
    try:
        engine = get_engine()
        
        # Check if table exists
        with engine.connect() as connection:
            result = connection.execute(text(
                f"SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = '{table_name}')"
            ))
            table_exists = result.scalar()
            
            if not table_exists:
                logger.info(f"Table {table_name} doesn't exist yet. No schema changes needed.")
                return False
            
            # Get existing columns from the database
            result = connection.execute(text(
                f"SELECT column_name FROM information_schema.columns WHERE table_name = '{table_name}'"
            ))
            existing_columns = [row[0] for row in result.fetchall()]
            logger.info(f"Existing columns in {table_name}: {existing_columns}")
            
            # Get new columns from the DataFrame (preserving case)
            new_columns = list(df.columns)
            logger.info(f"Columns in new data: {new_columns}")
            
            # Find missing columns (case-insensitive comparison)
            existing_lowercase = [col.lower() for col in existing_columns]
            missing_columns = [col for col in new_columns if col.lower() not in existing_lowercase]
            
            if missing_columns:
                logger.info(f"Detected {len(missing_columns)} new columns: {missing_columns}")
                print(f"Detected schema changes: {len(missing_columns)} new columns")
                
                # Add new columns to the existing table
                for col in missing_columns:
                    # Add column with appropriate data type (default to TEXT)
                    # Use double quotes to preserve case
                    connection.execute(text(f'ALTER TABLE "{table_name}" ADD COLUMN "{col}" TEXT'))
                
                connection.commit()
                logger.info(f"Added {len(missing_columns)} new columns to {table_name}")
                print(f"Schema updated: Added {len(missing_columns)} new columns to {table_name}")
                return True
            
            # Check if the unique ID column exists in different case
            # This would help with the UniqueID vs uniqueid problem
            return False
        
    except SQLAlchemyError as e:
        logger.error(f"Database error during schema change detection: {str(e)}")
        print(f"Database error during schema change detection: {str(e)}")
        return False

def execute_query(query: str, params: Optional[Dict[str, Any]] = None) -> pd.DataFrame:
    """
    Execute a SQL query and return the results as a pandas DataFrame.
    
    Args:
        query: SQL query to execute
        params: Query parameters (optional)
        
    Returns:
        pandas DataFrame with query results
    """
    engine = get_db_engine()
    try:
        with engine.connect() as connection:
            return pd.read_sql(text(query), connection, params=params)
    except Exception as e:
        logger.error(f"Query execution failed: {str(e)}")
        logger.error(f"Query: {query}")
        logger.error(f"Params: {params}")
        raise

def get_table_schema(table_name: str) -> List[Dict[str, Any]]:
    """
    Get the schema information for a table.
    
    Args:
        table_name: Name of the table
        
    Returns:
        List of dictionaries with column information
    """
    query = """
    SELECT 
        column_name, 
        data_type, 
        character_maximum_length, 
        is_nullable
    FROM 
        information_schema.columns
    WHERE 
        table_name = :table_name
    ORDER BY 
        ordinal_position
    """
    
    try:
        df = execute_query(query, {'table_name': table_name})
        return df.to_dict('records')
    except Exception as e:
        logger.error(f"Failed to get schema for table {table_name}: {str(e)}")
        return []

def table_exists(table_name: str) -> bool:
    """
    Check if a table exists in the database.
    
    Args:
        table_name: Name of the table to check
        
    Returns:
        True if the table exists, False otherwise
    """
    query = """
    SELECT EXISTS (
        SELECT FROM information_schema.tables 
        WHERE table_name = :table_name
    )
    """
    
    try:
        result = execute_query(query, {'table_name': table_name})
        return result.iloc[0, 0]
    except Exception as e:
        logger.error(f"Failed to check if table {table_name} exists: {str(e)}")
        return False

def get_db_connection_with_status():
    """
    Get SQLAlchemy engine for database connection and perform connection diagnostics.
    Returns a tuple: (engine, status_dict)
    status_dict contains keys: 'success', 'messages' (list of str), 'error' (str or None)
    This function does not use Streamlit; UI should be handled in the frontend.
    """
    from sqlalchemy import text
    import traceback
    status = {"success": False, "messages": [], "error": None}
    try:
        db_config = get_db_config()
        status["messages"].append(f"Host: {db_config['PG_HOST']}")
        status["messages"].append(f"Port: {db_config['PG_PORT']}")
        status["messages"].append(f"Database: {db_config['PG_DBNAME']}")
        engine = get_db_engine()
        try:
            with engine.connect() as conn:
                result = conn.execute(text("SELECT 1")).fetchone()
                status["messages"].append(f"[+] Database connection successful: {result}")
                # Check if the table exists
                result = conn.execute(text("SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name = 'usaprime_cleaned')")).fetchone()
                if result and result[0]:
                    status["messages"].append("[+] Table 'usaprime_cleaned' exists")
                else:
                    status["messages"].append("[-] Table 'usaprime_cleaned' doesn't exist")
                    tables = conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")).fetchall()
                    if tables:
                        table_list = [t[0] for t in tables]
                        status["messages"].append(f"Available tables: {', '.join(table_list)}")
            status["success"] = True
        except Exception as e:
            status["error"] = f"Error executing test query: {str(e)}"
            status["messages"].append(status["error"])
            return None, status
        return engine, status
    except Exception as e:
        status["error"] = f"Error connecting to database: {str(e)}"
        status["messages"].append(status["error"])
        status["messages"].append(traceback.format_exc())
        return None, status
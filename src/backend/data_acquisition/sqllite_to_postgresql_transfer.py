"""
SQLite to PostgreSQL Data Migration Script
This script uses pgloader via Docker to migrate the awards table from SQLite to PostgreSQL.
Docker provides a clean, consistent environment for running pgloader without installation hassles.
Database connection settings are loaded from .env file.
"""

import os
import time
import subprocess
import sys
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from sqlalchemy import create_engine, text, inspect
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# SQLite connection settings from .env
sqlite_db_path = os.getenv('SQLITE_DB_PATH')
sqlite_timeout = int(os.getenv('SQLITE_TIMEOUT', '30'))

# PostgreSQL connection settings from .env
pg_user = os.getenv('PG_USER')
pg_password = os.getenv('PG_PASSWORD')
pg_host = os.getenv('PG_HOST')
pg_port = os.getenv('PG_PORT')
pg_dbname = os.getenv('PG_DBNAME')

def create_database_if_not_exists():
    """Create the PostgreSQL database if it doesn't exist with proper collation settings"""
    try:
        # Connect to default 'postgres' database first
        conn = psycopg2.connect(
            user=pg_user,
            password=pg_password,
            host=pg_host,
            port=pg_port,
            dbname="postgres"
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Check if our database exists
        cursor.execute("SELECT 1 FROM pg_catalog.pg_database WHERE datname = %s", (pg_dbname,))
        exists = cursor.fetchone()
        
        if not exists:
            # Create database with C locale to avoid OS collation issues
            print(f"Creating database '{pg_dbname}' with C locale to avoid OS collation issues...")
            cursor.execute(f"CREATE DATABASE {pg_dbname} WITH ENCODING='UTF8' LC_COLLATE='C' LC_CTYPE='C' TEMPLATE=template0")
            print(f"Database '{pg_dbname}' created successfully.")
        else:
            print(f"Database '{pg_dbname}' already exists.")
            
        # Check collation using pg_database catalog instead of SHOW command
        cursor.execute("""
            SELECT datcollate, datctype 
            FROM pg_database 
            WHERE datname = %s
        """, (pg_dbname,))
        collation_result = cursor.fetchone()
        if collation_result:
            collate, ctype = collation_result
            print(f"Database collation settings: LC_COLLATE={collate}, LC_CTYPE={ctype}")
            
            if collate != 'C' or ctype != 'C':
                print("Warning: Database uses non-C locale which may cause collation issues.")
        
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"Error creating/checking database: {str(e)}")
        return False

def check_docker_installation():
    """Check if Docker is installed and running"""
    try:
        # Check if Docker is installed
        result = subprocess.run(["docker", "--version"], capture_output=True, text=True)
        if result.returncode != 0:
            print("Docker is not installed or not in PATH. Please install Docker Desktop for Windows.")
            return False
        
        print(f"Docker is installed: {result.stdout.strip()}")
        
        # Check if Docker is running
        result = subprocess.run(["docker", "info"], capture_output=True, text=True)
        if result.returncode != 0:
            print("Docker is installed but not running. Please start Docker Desktop.")
            return False
        
        print("Docker is running.")
        return True
    except Exception as e:
        print(f"Error checking Docker installation: {str(e)}")
        return False

def migrate_with_pgloader_docker():
    """Migrate using pgloader via Docker for faster performance"""
    # Get full absolute paths
    sqlite_full_path = os.path.abspath(sqlite_db_path)
    
    # Get the directory and filename separately
    sqlite_dir = os.path.dirname(sqlite_full_path)
    sqlite_filename = os.path.basename(sqlite_full_path)
    
    # Format paths for Docker (convert Windows backslashes to forward slashes)
    sqlite_dir_docker = sqlite_dir.replace('\\', '/')
    current_dir = os.getcwd().replace('\\', '/')
    
    # Create a load file for pgloader with the most basic syntax possible
    load_file_path = "migrate_awards.load"
    with open(load_file_path, "w") as f:
        f.write(f"""LOAD DATABASE
     FROM sqlite:///sqlite_data/{sqlite_filename}
     INTO postgresql://{pg_user}:{pg_password}@host.docker.internal:{pg_port}/{pg_dbname}

-- Only include the awards table and rename it
EXCLUDING TABLE NAMES LIKE 'sqlite_%'
EXCLUDING TABLE NAMES LIKE '%_idx'
EXCLUDING TABLE NAMES LIKE '%_sequence'
EXCLUDING TABLE NAMES LIKE '%_content'
EXCLUDING TABLE NAMES LIKE '%_stat'
EXCLUDING TABLE NAMES LIKE '%_master'
EXCLUDING TABLE NAMES LIKE '%_temp'
ALTER TABLE NAMES MATCHING 'awards' RENAME TO 'usaspending_prime_awards';
""")
    
    print("Created pgloader configuration file.")
    
    # Save configuration to log file for debugging
    with open("migration.log", "w") as log:
        log.write(f"Migration started at: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        log.write(f"SQLite path: {sqlite_full_path}\n")
        log.write(f"PostgreSQL: {pg_host}:{pg_port}/{pg_dbname}\n\n")
        
        # Also save the configuration
        log.write("--- pgloader configuration ---\n")
        with open(load_file_path, "r") as config:
            log.write(config.read())
        log.write("\n----------------------------\n\n")
    
    print("Starting migration with pgloader via Docker...")
    
    try:
        start_time = time.time()
        
        # First, ensure the destination table doesn't exist
        pg_engine = create_engine(f'postgresql://{pg_user}:{pg_password}@{pg_host}:{pg_port}/{pg_dbname}')
        with pg_engine.connect() as conn:
            conn.execute(text("DROP TABLE IF EXISTS usaspending_prime_awards"))
            print("Dropped existing usaspending_prime_awards table if it existed.")
        
        # Run pgloader in Docker with volume mounts
        cmd = [
            "docker", "run", "--rm",
            "-v", f"{current_dir}/{load_file_path}:/migrate.load",
            "-v", f"{sqlite_dir_docker}:/sqlite_data",
            "ghcr.io/dimitri/pgloader:latest", 
            "pgloader", "--verbose", "/migrate.load"
        ]
        
        print(f"Executing Docker command: {' '.join(cmd)}")
        
        # Run with unbuffered output to see progress in real-time
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )
        
        # Stream the output as it comes and also log it
        with open("migration.log", "a") as log:
            for line in process.stdout:
                print(line, end='')
                log.write(line)
        
        # Wait for the process to complete
        return_code = process.wait()
        
        elapsed_time = time.time() - start_time
        
        if return_code == 0:
            print(f"Migration completed successfully with pgloader!")
            print(f"Total time elapsed: {elapsed_time/60:.2f} minutes")
            print("Run your indexing scripts to optimize the PostgreSQL database.")
            return True
        else:
            print(f"Error: pgloader exited with code {return_code}")
            return False
        
    except Exception as e:
        print(f"Error during pgloader Docker migration: {str(e)}")
        return False

if __name__ == "__main__":
    print("=== SQLite to PostgreSQL Migration Tool using Docker + pgloader ===")
    print(f"Source: SQLite database '{sqlite_db_path}', 'awards' table")
    print(f"Destination: PostgreSQL database '{pg_dbname}' on {pg_host}:{pg_port} as 'usaspending_prime_awards' table")
    
    # First check if Docker is installed and running
    if not check_docker_installation():
        print("Docker is required for this migration method. Please install and start Docker Desktop.")
        sys.exit(1)
    
    # Then create the database if it doesn't exist
    if not create_database_if_not_exists():
        print("Failed to create or connect to the PostgreSQL database.")
        sys.exit(1)
    
    print("\nPulling the pgloader Docker image...")
    pull_result = subprocess.run(["docker", "pull", "ghcr.io/dimitri/pgloader:latest"], 
                                capture_output=True, text=True)
    if pull_result.returncode != 0:
        print(f"Error pulling pgloader Docker image: {pull_result.stderr}")
        sys.exit(1)
    
    print("Docker image pulled successfully.")
    
    # Start migration
    proceed = input("Ready to start migration. This might take several hours for a 150GB dataset. Proceed? (y/n): ")
    if proceed.lower() == 'y':
        success = migrate_with_pgloader_docker()
        if success:
            print("Migration completed successfully.")
        else:
            print("Migration failed or was incomplete.")
    else:
        print("Migration cancelled by user.")
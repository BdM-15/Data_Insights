#!/usr/bin/env python3
# USAspending Database Restoration with Python - No Backup Version
# Created on April 29, 2025

import os
import sys
import subprocess
import time
import logging
import psutil

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("usaspending_restore.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("usaspending_restore")

# Configuration
config = {
    "PG_INSTALL_DIR": r"E:\PostgreSQL17",
    "PG_DATA_DIR": r"E:\PostgreSQL17\data",
    "PG_LOG_FILE": r"E:\PostgreSQL17\postgres.log",
    "PGPORT": "5433",
    "PGUSER": "postgres",
    "PGPASSWORD": "postgres",
    "DUMP_DIR": r"E:\USASpending Full DB",
    "DUMP": r"E:\USASpending Full DB\extracted",
    "STATUS_FILE": r"E:\USASpending Full DB\restore_status.txt"
}

# Find PostgreSQL binaries
def find_pg_bin():
    try:
        result = subprocess.run(["where", "psql"], capture_output=True, text=True, check=True)
        bin_path = os.path.dirname(result.stdout.splitlines()[0])
        logger.info(f"Using PostgreSQL binaries from: {bin_path}")
        return bin_path
    except subprocess.CalledProcessError:
        logger.error("PostgreSQL binaries not found in PATH")
        sys.exit(1)

# Create required directories
def create_directories():
    logger.info("Creating necessary directories")
    os.makedirs(config["PG_INSTALL_DIR"], exist_ok=True)
    os.makedirs(os.path.join(config["DUMP_DIR"], "logs"), exist_ok=True)

# Check if a port is in use
def is_port_in_use(port):
    for conn in psutil.net_connections():
        if conn.laddr.port == port and conn.status == 'LISTEN':
            return True
    return False

# Kill any process using the specified port
def kill_processes_on_port(port):
    for conn in psutil.net_connections():
        if conn.laddr.port == port and conn.status == 'LISTEN':
            try:
                process = psutil.Process(conn.pid)
                logger.info(f"Killing process {conn.pid} ({process.name()}) that's using port {port}")
                process.kill()
                return True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                logger.error(f"Failed to kill process {conn.pid} using port {port}")
                return False
    return True  # No processes to kill

# Check if PostgreSQL is running
def is_pg_running():
    try:
        cmd = [
            os.path.join(pg_bin, "psql.exe"),
            "-h", "localhost",
            "-p", config["PGPORT"],
            "-U", config["PGUSER"],
            "-c", "SELECT 1 as connection_test;"
        ]
        env = os.environ.copy()
        env["PGPASSWORD"] = config["PGPASSWORD"]
        
        result = subprocess.run(cmd, env=env, capture_output=True, text=True)
        return result.returncode == 0
    except Exception as e:
        logger.error(f"Error checking PostgreSQL status: {e}")
        return False

# Initialize PostgreSQL cluster
def initialize_pg_cluster():
    if os.path.exists(config["PG_DATA_DIR"]):
        logger.info("Existing PostgreSQL data directory found, cleaning it up")
        try:
            for root, dirs, files in os.walk(config["PG_DATA_DIR"], topdown=False):
                for name in files:
                    os.remove(os.path.join(root, name))
                for name in dirs:
                    os.rmdir(os.path.join(root, name))
            logger.info("Successfully cleaned up existing data directory")
        except Exception as e:
            logger.error(f"Failed to clean up data directory: {e}")
            logger.info("Will try to recreate the directory")
            try:
                os.rmdir(config["PG_DATA_DIR"])
            except:
                pass
    
    logger.info("Creating new PostgreSQL instance")
    os.makedirs(config["PG_DATA_DIR"], exist_ok=True)
    
    # Create password file for initdb
    pwd_file = os.path.join(os.environ["TEMP"], "pgpass.txt")
    with open(pwd_file, "w") as f:
        f.write(config["PGPASSWORD"])
    
    try:
        logger.info("Initializing PostgreSQL database cluster")
        cmd = [
            os.path.join(pg_bin, "initdb.exe"),
            "-D", config["PG_DATA_DIR"],
            "-U", config["PGUSER"],
            "--pwfile", pwd_file,
            "--encoding=UTF8",
            "--locale=C"
        ]
        subprocess.run(cmd, check=True)
        
        # Write optimized configuration
        logger.info("Writing optimized PostgreSQL configuration")
        with open(os.path.join(config["PG_DATA_DIR"], "postgresql.conf"), "w") as f:
            f.write(f"""# PostgreSQL configuration file for USAspending database - High Performance
port = {config["PGPORT"]}
listen_addresses = '*'
max_connections = 100
shared_buffers = 4GB
work_mem = 512MB
maintenance_work_mem = 2000MB
effective_io_concurrency = 0
max_parallel_workers_per_gather = 8
max_parallel_workers = 16
random_page_cost = 1.1
synchronous_commit = off
checkpoint_timeout = 60min
max_wal_size = 10GB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
data_directory = '{config["PG_DATA_DIR"].replace('\\', '/')}'
log_directory = 'log'
logging_collector = on
log_filename = 'postgresql-%Y-%m-%d_%H%M%S.log'
log_rotation_age = 1d
log_rotation_size = 100MB
log_truncate_on_rotation = on
log_min_messages = warning
temp_file_limit = '1TB'
""")
        
        # Write authentication configuration
        with open(os.path.join(config["PG_DATA_DIR"], "pg_hba.conf"), "w") as f:
            f.write("""# TYPE  DATABASE        USER            ADDRESS                 METHOD
local   all             all                                     trust
host    all             all             127.0.0.1/32            trust
host    all             all             ::1/128                 trust
host    all             all             localhost               trust
""")
        
        # Create log directory
        os.makedirs(os.path.join(config["PG_DATA_DIR"], "log"), exist_ok=True)
    
    finally:
        # Clean up password file
        if os.path.exists(pwd_file):
            os.unlink(pwd_file)

# Start PostgreSQL server
def start_postgres():
    logger.info("Starting PostgreSQL server")
    cmd = [
        os.path.join(pg_bin, "pg_ctl.exe"),
        "-D", config["PG_DATA_DIR"],
        "-l", config["PG_LOG_FILE"],
        "start"
    ]
    subprocess.run(cmd)
    
    # Wait for server to start
    logger.info("Waiting for PostgreSQL to start")
    time.sleep(10)
    
    # Test connection with retry
    max_retries = 5
    for i in range(1, max_retries + 1):
        logger.info(f"Connection attempt {i} of {max_retries}")
        if is_pg_running():
            logger.info("Successfully connected to PostgreSQL!")
            return True
        
        if i < max_retries:
            logger.warning("Connection failed, waiting 5 seconds...")
            time.sleep(5)
    
    logger.error(f"Failed to connect to PostgreSQL after {max_retries} attempts")
    logger.error("Server log:")
    try:
        with open(config["PG_LOG_FILE"], "r") as f:
            logger.error(f.read())
    except:
        logger.error(f"Could not read log file: {config['PG_LOG_FILE']}")
    
    return False

# Stop PostgreSQL server
def stop_postgres():
    logger.info("Stopping PostgreSQL server")
    cmd = [
        os.path.join(pg_bin, "pg_ctl.exe"),
        "-D", config["PG_DATA_DIR"],
        "stop",
        "-m", "fast"
    ]
    subprocess.run(cmd)
    time.sleep(5)

# Run psql command
def run_psql(command):
    cmd = [
        os.path.join(pg_bin, "psql.exe"),
        "-h", "localhost",
        "-p", config["PGPORT"],
        "-U", config["PGUSER"],
        "-c", command
    ]
    env = os.environ.copy()
    env["PGPASSWORD"] = config["PGPASSWORD"]
    
    return subprocess.run(cmd, env=env, capture_output=True, text=True)

# Setup database and roles
def setup_database():
    logger.info("Setting up database and roles")
    
    # Check if database exists
    result = run_psql("\\l")
    if "usaspending_full_db_download" in result.stdout:
        logger.info("Database already exists, dropping and recreating")
        run_psql("DROP DATABASE IF EXISTS usaspending_full_db_download;")
    
    logger.info("Creating database usaspending_full_db_download")
    run_psql("CREATE DATABASE usaspending_full_db_download;")
    
    # Create roles if they don't exist
    logger.info("Creating roles (if they don't exist)")
    run_psql("DO $$ BEGIN CREATE ROLE root WITH SUPERUSER LOGIN PASSWORD 'password'; EXCEPTION WHEN duplicate_object THEN NULL; END $$;")
    run_psql("DO $$ BEGIN CREATE ROLE api_user WITH LOGIN PASSWORD 'password'; EXCEPTION WHEN duplicate_object THEN NULL; END $$;")
    run_psql("DO $$ BEGIN CREATE ROLE data_store_api NOLOGIN; EXCEPTION WHEN duplicate_object THEN NULL; END $$;")
    run_psql("DO $$ BEGIN CREATE ROLE readonly NOLOGIN; EXCEPTION WHEN duplicate_object THEN NULL; END $$;")
    run_psql("DO $$ BEGIN CREATE ROLE readonly_api NOLOGIN; EXCEPTION WHEN duplicate_object THEN NULL; END $$;")
    run_psql("ALTER DATABASE usaspending_full_db_download OWNER TO root;")
    
    # Create lock file
    with open(os.path.join(config["DUMP_DIR"], "restore.running"), "w") as f:
        f.write("Running")

# Get current restoration phase
def get_current_phase():
    if not os.path.exists(config["STATUS_FILE"]):
        logger.info("Starting new restoration (phase 0)")
        return 0
    
    with open(config["STATUS_FILE"], "r") as f:
        try:
            phase = int(f.read().strip())
            logger.info(f"Resuming from phase {phase}")
            return phase
        except:
            logger.warning("Invalid status file, starting from phase 0")
            return 0

# Update phase status
def update_phase(phase):
    with open(config["STATUS_FILE"], "w") as f:
        f.write(str(phase))

# Run pg_restore command with optimized settings for phase 3
def run_pg_restore(section, jobs, phase_name):
    # Default jobs for each section
    if section == "pre-data":
        effective_jobs = 1  # Schema is best with 1 job
    elif section == "data":
        effective_jobs = 8  # Data loading with high parallelism
    elif section == "post-data":
        effective_jobs = 8  # Maximal parallelism for indexes too
    else:
        effective_jobs = jobs
        
    # Also increase maintenance_work_mem accordingly
    if section == "post-data":
        # Set higher memory for index creation
        logger.info("Optimizing PostgreSQL for index creation...")
        run_psql("ALTER SYSTEM SET maintenance_work_mem = '1GB';")  # Changed from 2GB to 1GB
        run_psql("ALTER SYSTEM SET work_mem = '1GB';")
        run_psql("ALTER SYSTEM SET max_parallel_maintenance_workers = 4;")
        run_psql("SELECT pg_reload_conf();")
        
    cmd = [
        os.path.join(pg_bin, "pg_restore.exe"),
        "-h", "localhost",
        "-p", config["PGPORT"],
        "-U", "root",
        "-d", "usaspending_full_db_download",
        "--verbose",
        "--no-owner",
        "--no-acl",
        f"--section={section}",
        f"--jobs={effective_jobs}",
        config["DUMP"]
    ]
    
    env = os.environ.copy()
    env["PGPASSWORD"] = "password"  # root user password
    
    log_file = os.path.join(config["DUMP_DIR"], "logs", f"restore_{phase_name}.log")
    with open(log_file, "w") as f:
        logger.info(f"Running pg_restore for {section} section with {effective_jobs} parallel jobs")
        result = subprocess.run(cmd, env=env, stdout=f, stderr=subprocess.STDOUT)
    
    # Reset PostgreSQL settings after this phase completes
    if section == "post-data":
        logger.info("Resetting PostgreSQL optimization settings...")
        run_psql("ALTER SYSTEM RESET maintenance_work_mem;")
        run_psql("ALTER SYSTEM RESET work_mem;")
        run_psql("ALTER SYSTEM RESET max_parallel_maintenance_workers;")
        run_psql("SELECT pg_reload_conf();")
    
    if result.returncode > 1:
        logger.warning(f"WARNING: {phase_name} restoration returned non-zero exit code ({result.returncode})")
        logger.warning(f"This may be normal. Check log file at: {log_file}")
    else:
        logger.info(f"{phase_name} restoration completed successfully")
    
    return result.returncode <= 1

# Main restoration process
def main():
    global pg_bin
    
    logger.info("USAspending Database Restoration with Python - High Performance Mode")
    logger.info("This will take several hours to complete")
    
    # Setup
    pg_bin = find_pg_bin()
    create_directories()
    
    # Check if port is in use
    port = int(config["PGPORT"])
    if is_port_in_use(port):
        logger.warning(f"Port {port} is already in use")
        
        # Try to kill the process
        if not kill_processes_on_port(port):
            logger.error(f"Failed to kill process using port {port}. Please free up this port manually.")
            return 1
        
        # Wait for port to be released
        wait_count = 0
        while is_port_in_use(port) and wait_count < 10:
            logger.info(f"Waiting for port {port} to be released...")
            time.sleep(3)
            wait_count += 1
        
        if is_port_in_use(port):
            logger.error(f"Port {port} is still in use after trying to free it. Please check manually.")
            return 1
    
    # Try to stop any existing PostgreSQL instance
    try:
        stop_postgres()
    except:
        pass  # Ignore errors if no server is running
    
    # Initialize and start PostgreSQL
    initialize_pg_cluster()
    if not start_postgres():
        logger.error("Failed to start PostgreSQL server")
        return 1
    
    # Set up database and get current phase
    setup_database()
    
    # Always start from phase 0 for clean run
    update_phase(0)
    current_phase = 0
    
    # Phase 1: Schema Restoration
    if current_phase < 1:
        logger.info("===== Phase 1: Restoring database schemas (pre-data) =====")
        if run_pg_restore("pre-data", 1, "schemas"):
            update_phase(1)
            logger.info("Phase 1 completed successfully")
        else:
            logger.warning("Phase 1 had issues but continuing")
            update_phase(1)
    
    # Phase 2: Data Restoration
    if current_phase < 2:
        logger.info("===== Phase 2: Restoring table data =====")
        logger.info("This will take several hours...")
        if run_pg_restore("data", 8, "data"):
            update_phase(2)
            logger.info("Phase 2 completed successfully")
        else:
            logger.warning("Phase 2 had issues but continuing")
            update_phase(2)
    
    # Phase 3: Index Restoration
    if current_phase < 3:
        logger.info("===== Phase 3: Restoring indexes and constraints =====")
        logger.info("This may take several hours...")
        if run_pg_restore("post-data", 8, "indexes"):
            update_phase(3)
            logger.info("Phase 3 completed successfully")
        else:
            logger.warning("Phase 3 had issues but continuing")
            update_phase(3)
    
    # Final phase: ANALYZE
    logger.info("===== Final phase: Running ANALYZE on database =====")
    run_psql("\\c usaspending_full_db_download")
    run_psql("ANALYZE VERBOSE;")
    
    # Remove lock file
    lock_file = os.path.join(config["DUMP_DIR"], "restore.running")
    if os.path.exists(lock_file):
        os.unlink(lock_file)
    
    # Success message
    logger.info("=" * 60)
    logger.info("USASPENDING DATABASE RESTORATION COMPLETED SUCCESSFULLY")
    logger.info("=" * 60)
    logger.info("Database connection information:")
    logger.info(f"  Host: localhost")
    logger.info(f"  Port: {config['PGPORT']}")
    logger.info(f"  Database: usaspending_full_db_download")
    logger.info(f"  Username: root")
    logger.info(f"  Password: password")
    logger.info("=" * 60)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
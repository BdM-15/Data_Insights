# This script will remain standalone for data ingestion.

import pandas as pd
from sqlalchemy import create_engine
from datetime import datetime, timedelta
import os
import glob

# Define paths
csv_directory = r"C:\GitHub\Opp_Sem_Search\backend\data\archive"  # Updated directory path
db_path = r"sqlite:///C:\GitHub\Opp_Sem_Search\backend\data\usaspending_historical.db?timeout=30"

# Define the date range for the data to upload
start_date = datetime(2024, 10, 1)  # October 1, 2024
end_date = datetime(2025, 3, 15)    # March 15, 2025

# Connect to the SQLite database
engine = create_engine(db_path, connect_args={'timeout': 30})

# Function to generate two-day date ranges between start_date and end_date
def generate_date_ranges(start_date, end_date):
    date_ranges = []
    current_date = start_date
    while current_date < end_date:
        next_date = current_date + timedelta(days=1)
        if next_date > end_date:
            next_date = end_date
        date_ranges.append((current_date, next_date))
        current_date = next_date
    return date_ranges

# Generate the list of date ranges (two-day chunks)
date_ranges = generate_date_ranges(start_date, end_date)

# Counter for tracking progress
total_files_processed = 0
total_rows_inserted = 0

# Process each date range
for start, end in date_ranges:
    # Format the dates for the file name (e.g., "usaspending_2024-10-01_to_2024-10-02.csv")
    start_str = start.strftime("%Y-%m-%d")
    end_str = end.strftime("%Y-%m-%d")
    file_name = f"usaspending_{start_str}_to_{end_str}.csv"  # Updated naming convention
    file_path = os.path.join(csv_directory, file_name)

    # Check if the file exists
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}. Skipping...")
        continue

    try:
        # Read the CSV file, treating all columns as strings
        print(f"Reading file: {file_path}")
        df = pd.read_csv(file_path, dtype=str, low_memory=False)

        # Insert the data into the 'awards' table
        print(f"Inserting {len(df)} rows into the 'awards' table...")
        df.to_sql('awards', engine, if_exists='append', index=False)

        # Update counters
        total_files_processed += 1
        total_rows_inserted += len(df)
        print(f"Successfully inserted {len(df)} rows from {file_name}")

    except Exception as e:
        print(f"Error processing {file_name}: {str(e)}. Skipping...")

# Print summary
print("\nUpload Summary:")
print(f"Total files processed: {total_files_processed}")
print(f"Total rows inserted: {total_rows_inserted}")
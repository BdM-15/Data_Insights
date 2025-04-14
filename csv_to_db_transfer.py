# import pandas as pd
# from sqlalchemy import create_engine
# from datetime import datetime, timedelta
# import os

# # Define paths and database connection
# CSV_DIR = r"C:\GitHub\Opp_Sem_Search\backend\data\archive"  # Replace with the directory containing your CSV files
# DB_PATH = r"sqlite:///C:\GitHub\Opp_Sem_Search\backend\data\usaspending_historical.db?timeout=30"
# TABLE_NAME = "awards"

# # Define the date range for the missing data
# START_DATE = datetime(2024, 10, 1)
# END_DATE = datetime(2025, 3, 13)

# # Function to generate two-day date ranges and corresponding file names
# def generate_file_names(start_date, end_date):
#     current_date = start_date
#     file_names = []
    
#     while current_date < end_date:
#         # Calculate the end date for the two-day chunk
#         chunk_end_date = current_date + timedelta(days=1)
#         if chunk_end_date > end_date:
#             chunk_end_date = end_date
        
#         # Format the file name
#         file_name = f"usaspending_{current_date.strftime('%Y-%m-%d')}_to_{chunk_end_date.strftime('%Y-%m-%d')}.csv"
#         file_names.append(file_name)
        
#         # Move to the next two-day chunk
#         current_date += timedelta(days=2)
    
#     return file_names

# # Function to upload CSV data to SQLite
# def upload_csv_to_db(csv_file_path, engine, table_name):
#     try:
#         # Read the CSV file
#         df = pd.read_csv(csv_file_path)
#         print(f"Loaded {csv_file_path} with {len(df)} rows.")
        
#         # Ensure date columns are in the correct format (if needed)
#         if 'action_date' in df.columns:
#             df['action_date'] = pd.to_datetime(df['action_date']).dt.strftime('%Y-%m-%d')
        
#         # Upload to SQLite (append mode)
#         df.to_sql(table_name, engine, if_exists='append', index=False)
#         print(f"Successfully uploaded {csv_file_path} to {table_name}.")
        
#     except Exception as e:
#         print(f"Error uploading {csv_file_path}: {str(e)}")

# # Function to verify the data in the database
# def verify_data(engine, table_name, start_date, end_date):
#     query = f"""
#     SELECT action_date, COUNT(*) as row_count
#     FROM {table_name}
#     WHERE action_date BETWEEN '{start_date.strftime('%Y-%m-%d')}' AND '{end_date.strftime('%Y-%m-%d')}'
#     GROUP BY action_date
#     ORDER BY action_date
#     """
#     with engine.connect() as connection:
#         result = pd.read_sql(query, connection)
#     print("Verification - Data in the database:")
#     print(result)

# # Main script
# def main():
#     # Connect to the SQLite database
#     engine = create_engine(DB_PATH, connect_args={'timeout': 30})
    
#     # Generate the list of CSV file names
#     file_names = generate_file_names(START_DATE, END_DATE)
#     print(f"Generated {len(file_names)} file names to process.")
    
#     # Process each CSV file
#     for file_name in file_names:
#         file_path = os.path.join(CSV_DIR, file_name)
#         if os.path.exists(file_path):
#             upload_csv_to_db(file_path, engine, TABLE_NAME)
#         else:
#             print(f"File not found: {file_path}")
    
#     # Verify the uploaded data
#     verify_data(engine, TABLE_NAME, START_DATE, END_DATE)

# if __name__ == "__main__":
#     main()

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
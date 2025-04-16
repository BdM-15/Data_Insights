# This script will remain standalone for database inspection.
import pandas as pd
from sqlalchemy import create_engine, text

# Connect to the database
db_path = r'sqlite:///C:\GitHub\Opp_Sem_Search\backend\data\usaspending_historical.db'
engine = create_engine(db_path)

# # Use a connection to execute the query
# with engine.connect() as connection:
#     tables = connection.execute(text("SELECT name FROM sqlite_master WHERE type='table';")).fetchall()
#     print("Tables in the database:", tables)

# # Optionally, inspect the schema of a specific table (replace 'awards' with the actual table name)
# with engine.connect() as connection:
#     schema = connection.execute(text("PRAGMA table_info(awards);")).fetchall()
#     print("Columns in the 'awards' table:", schema)

# Query to check for FY2025 data (action_date between 2024-10-01 and 2025-04-10)
query = "SELECT * FROM awards_slim WHERE action_date BETWEEN '2024-10-01' AND '2025-04-10'"
df = pd.read_sql(query, engine)

# Display the results
print(f"Number of rows in FY2025: {len(df)}")
print(df.head())
print(df.tail())
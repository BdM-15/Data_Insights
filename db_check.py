from sqlalchemy import create_engine, text

# Connect to the database
db_path = r'sqlite:///C:\GitHub\Opp_Sem_Search\backend\data\usaspending_historical.db'
engine = create_engine(db_path)

# Use a connection to execute the query
with engine.connect() as connection:
    tables = connection.execute(text("SELECT name FROM sqlite_master WHERE type='table';")).fetchall()
    print("Tables in the database:", tables)

# Optionally, inspect the schema of a specific table (replace 'awards' with the actual table name)
with engine.connect() as connection:
    schema = connection.execute(text("PRAGMA table_info(awards);")).fetchall()
    print("Columns in the 'awards' table:", schema)
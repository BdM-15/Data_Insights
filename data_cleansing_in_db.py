# data_cleansing.py
import pandas as pd
from sqlalchemy import create_engine, text

# Connect to the SQLite database
db_path = r'sqlite:///C:\GitHub\Opp_Sem_Search\backend\data\usaspending_historical.db'
engine = create_engine(db_path)

# Step 1: Replace blanks with "DEPT OF DEFENSE"
with engine.connect() as connection:
    # Update NULL or empty/whitespace values to "DEPT OF DEFENSE"
    connection.execute(text("""
        UPDATE awards_slim
        SET parent_award_agency_name = 'DEPT OF DEFENSE'
        WHERE parent_award_agency_name IS NULL OR TRIM(parent_award_agency_name) = '';
    """))

# Step 2: Fetch the data, apply title case, and update the table
# Since SQLite doesn't have a proper title case function, we'll use Python
with engine.connect() as connection:
    # Fetch the parent_award_agency_name column
    df = pd.read_sql(text("SELECT rowid, parent_award_agency_name FROM awards_slim"), connection)
    
    # Apply title case transformation
    df['parent_award_agency_name'] = df['parent_award_agency_name'].str.title()
    
    # Update the table with the transformed values
    for index, row in df.iterrows():
        connection.execute(
            text("UPDATE awards_slim SET parent_award_agency_name = :name WHERE rowid = :rowid"),
            {"name": row['parent_award_agency_name'], "rowid": row['rowid']}
        )

print("Data cleansing completed: parent_award_agency_name transformed.")
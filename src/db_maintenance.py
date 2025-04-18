# Consolidated Database Maintenance Script

from sqlalchemy import create_engine, text

# Connect to the SQLite database
db_path = r'sqlite:///C:\GitHub\Data_Insights\data\usaspending_historical.db?timeout=30'
engine = create_engine(db_path, connect_args={'timeout': 30})

# Step 1: Remove Duplicates
def remove_duplicates():
    print("Removing duplicates from awards_slim_cleaned table...")
    with engine.connect() as connection:
        connection.execute(text("""
            CREATE TABLE awards_slim_cleaned_deduplicated AS
            SELECT *
            FROM awards_slim_cleaned
            WHERE ROWID IN (
                SELECT MIN(ROWID)
                FROM awards_slim_cleaned
                GROUP BY award_id_piid, modification_number, action_date, federal_action_obligation, recipient_name
            );
        """))
        connection.execute(text("DROP TABLE awards_slim_cleaned"))
        connection.execute(text("ALTER TABLE awards_slim_cleaned_deduplicated RENAME TO awards_slim_cleaned"))
    print("Duplicates removed.")

# Step 2: Verify Existing Indexes
def verify_indexes():
    print("Verifying indexes on awards_slim_cleaned table...")
    with engine.connect() as connection:
        result = connection.execute(text("""
            SELECT name FROM sqlite_master 
            WHERE type='index' AND tbl_name='awards_slim_cleaned'
        """)).fetchall()
        
        if result:
            print(f"Found {len(result)} indexes:")
            for row in result:
                print(f"  - {row[0]}")
        else:
            print("No indexes found. Consider running data_processing.py to create them.")
            
# Step 3: Optimize Database
def optimize_database():
    print("Optimizing database...")
    with engine.connect() as connection:
        connection.execute(text("VACUUM;"))
    print("Database optimized.")

# Execute all steps
if __name__ == "__main__":
    remove_duplicates()
    verify_indexes()
    optimize_database()

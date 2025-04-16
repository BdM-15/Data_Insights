# Consolidated Database Maintenance Script

from sqlalchemy import create_engine, text

# Connect to the SQLite database
db_path = r'sqlite:///C:\GitHub\Opp_Sem_Search\backend\data\usaspending_historical.db?timeout=30'
engine = create_engine(db_path, connect_args={'timeout': 30})

# Step 1: Remove Duplicates
def remove_duplicates():
    print("Removing duplicates from awards_slim table...")
    with engine.connect() as connection:
        connection.execute(text("""
            CREATE TABLE awards_slim_deduplicated AS
            SELECT *
            FROM awards_slim
            WHERE ROWID IN (
                SELECT MIN(ROWID)
                FROM awards_slim
                GROUP BY award_id_piid, modification_number, action_date, federal_action_obligation, recipient_name
            );
        """))
        connection.execute(text("DROP TABLE awards_slim"))
        connection.execute(text("ALTER TABLE awards_slim_deduplicated RENAME TO awards_slim"))
    print("Duplicates removed.")

# Step 2: Create Indexes
def create_indexes():
    print("Creating indexes on awards_slim table...")
    with engine.connect() as connection:
        columns_to_index = [
            "action_date", "period_of_performance_current_end_date", "modification_number",
            "parent_award_agency_name", "funding_sub_agency_name", "funding_office_name",
            "recipient_name", "naics_code", "product_or_service_code", "type_of_contract_pricing",
            "extent_competed", "type_of_set_aside"
        ]
        for column in columns_to_index:
            index_name = f"idx_{column}"
            connection.execute(text(f"CREATE INDEX IF NOT EXISTS {index_name} ON awards_slim({column});"))
    print("Indexes created.")

# Execute all steps
if __name__ == "__main__":
    remove_duplicates()
    create_indexes()

from sqlalchemy import create_engine, text

# Connect to the SQLite database
db_path = r'sqlite:///C:\GitHub\Opp_Sem_Search\backend\data\usaspending_historical.db?timeout=30'
engine = create_engine(db_path, connect_args={'timeout': 30})

# Step 1: Count total rows
with engine.connect() as connection:
    total_rows = connection.execute(text("SELECT COUNT(*) FROM awards_slim")).scalar()
print(f"Total rows before deduplication: {total_rows}")

# Step 2: Create a new table with deduplicated rows using ROWID to keep the first occurrence
with engine.connect() as connection:
    with connection.begin():
        # Create a temporary table with deduplicated rows
        connection.execute(text("""
            CREATE TABLE awards_slim_deduplicated AS
            SELECT *
            FROM awards_slim
            WHERE ROWID IN (
                SELECT MIN(ROWID)
                FROM awards_slim
                GROUP BY award_id_piid, modification_number, action_date, federal_action_obligation, recipient_name
            )
        """))

        # Count rows after deduplication
        deduplicated_rows = connection.execute(text("SELECT COUNT(*) FROM awards_slim_deduplicated")).scalar()
        print(f"Number of duplicate rows removed: {total_rows - deduplicated_rows}")
        print(f"Rows after deduplication: {deduplicated_rows}")

        # Drop the original table and rename the deduplicated table
        connection.execute(text("DROP TABLE awards_slim"))
        connection.execute(text("ALTER TABLE awards_slim_deduplicated RENAME TO awards_slim"))

        # Recreate indexes for performance
        connection.execute(text("CREATE INDEX idx_action_date ON awards_slim(action_date);"))
        connection.execute(text("CREATE INDEX idx_parent_award_agency_name ON awards_slim(parent_award_agency_name);"))
        connection.execute(text("CREATE INDEX idx_funding_sub_agency_name ON awards_slim(funding_sub_agency_name);"))
        connection.execute(text("CREATE INDEX idx_funding_office_name ON awards_slim(funding_office_name);"))
        connection.execute(text("CREATE INDEX idx_recipient_name ON awards_slim(recipient_name);"))
        connection.execute(text("CREATE INDEX idx_naics_code ON awards_slim(naics_code);"))
        connection.execute(text("CREATE INDEX idx_product_or_service_code ON awards_slim(product_or_service_code);"))
        connection.execute(text("CREATE INDEX idx_type_of_contract_pricing ON awards_slim(type_of_contract_pricing);"))
        connection.execute(text("CREATE INDEX idx_extent_competed ON awards_slim(extent_competed);"))
        connection.execute(text("CREATE INDEX idx_type_of_set_aside ON awards_slim(type_of_set_aside);"))

print("Duplicates removed and table updated successfully.")
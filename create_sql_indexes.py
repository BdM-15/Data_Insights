# create_indexes.py
from sqlalchemy import create_engine, text

# Connect to the SQLite database
db_path = r'sqlite:///C:\GitHub\Opp_Sem_Search\backend\data\usaspending_historical.db?timeout=30'
engine = create_engine(db_path, connect_args={'timeout': 30})

# List of columns to index
columns_to_index = [
    "action_date", "period_of_performance_current_end_date", "modification_number",
    "parent_award_agency_name", "funding_sub_agency_name", "funding_office_name",
    "recipient_name", "naics_code", "product_or_service_code", "type_of_contract_pricing",
    "extent_competed", "type_of_set_aside"
]

# Create indexes
with engine.connect() as connection:
    for column in columns_to_index:
        index_name = f"idx_{column}"
        sql = f"CREATE INDEX IF NOT EXISTS {index_name} ON awards_slim({column});"
        connection.execute(text(sql))
        print(f"Created index {index_name} on column {column}")

print("All indexes created successfully.")
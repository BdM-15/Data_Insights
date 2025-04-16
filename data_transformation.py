# data_transformation.py
import pandas as pd
from sqlalchemy import create_engine, text
import json

# Connect to the SQLite database
db_path = r'sqlite:///C:\GitHub\Opp_Sem_Search\backend\data\usaspending_historical.db?timeout=30'
engine = create_engine(db_path, connect_args={'timeout': 30})

# Define the columns to select
required_columns = [
    "action_date", "modification_number", "federal_action_obligation", "total_dollars_obligated", "period_of_performance_start_date",
    "period_of_performance_current_end_date", "recipient_name", "naics_code",
    "parent_award_agency_name", "funding_sub_agency_name", "funding_office_name",
    "product_or_service_code", "type_of_contract_pricing", "extent_competed", "type_of_set_aside",
    "parent_award_id_piid", "award_id_piid", "potential_total_value_of_award",
    "primary_place_of_performance_city_name", "primary_place_of_performance_state_code",
    "prime_award_base_transaction_description", "transaction_description", "naics_description",
    "product_or_service_code_description", "awarding_office_name", "recipient_uei",
    "recipient_parent_name", "recipient_parent_uei", "solicitation_date", "solicitation_procedures",
    "fair_opportunity_limited_sources", "other_than_full_and_open_competition",
    "number_of_offers_received", "subcontracting_plan", "government_furnished_property",
    "usaspending_permalink"
]

# Load the data
print("Loading data from awards_slim...")
with engine.connect() as connection:
    df = pd.read_sql(text(f"SELECT {', '.join(required_columns)} FROM awards_slim"), connection)

# Perform cleaning and transformations
print("Cleaning data...")

# 1. Clean NAICS codes
df['naics_code'] = df['naics_code'].astype(str).str.replace(r'\.0$', '', regex=True).str.slice(0, 6)

# 2. Convert date columns to datetime and remove timestamps
df['action_date'] = pd.to_datetime(df['action_date'], errors='coerce').dt.date
df['period_of_performance_start_date'] = pd.to_datetime(df['period_of_performance_start_date'], errors='coerce').dt.date
df['period_of_performance_current_end_date'] = pd.to_datetime(df['period_of_performance_current_end_date'], errors='coerce').dt.date

# 3. Convert monetary columns to numeric
monetary_columns = ['federal_action_obligation', 'total_dollars_obligated', 'potential_total_value_of_award']
for col in monetary_columns:
    df[col] = pd.to_numeric(df[col], errors='coerce')

# 4. Convert string columns to uppercase for filtering
string_columns = [
    "parent_award_agency_name", "funding_sub_agency_name", "funding_office_name",
    "recipient_name", "naics_code", "product_or_service_code", "type_of_contract_pricing",
    "extent_competed", "type_of_set_aside"
]
for col in string_columns:
    df[col] = df[col].str.upper()

# 5. Drop rows with missing critical columns
# df = df.dropna(subset=['action_date', 'period_of_performance_current_end_date'])

# Create a new table for the cleaned data
print("Creating new table awards_slim_cleaned...")
with engine.connect() as connection:
    # Drop the table if it exists
    connection.execute(text("DROP TABLE IF EXISTS awards_slim_cleaned"))
    # Write the cleaned DataFrame to the new table
    df.to_sql('awards_slim_cleaned', engine, if_exists='replace', index=False)

# Precompute filter values and store in separate tables
filter_columns = [
    "parent_award_agency_name", "funding_sub_agency_name", "funding_office_name",
    "recipient_name", "naics_code", "product_or_service_code", "type_of_contract_pricing",
    "extent_competed", "type_of_set_aside"
]

with engine.connect() as connection:
    for column in filter_columns:
        print(f"Precomputing filter values for {column}...")
        # Get unique values, sorted alphabetically
        unique_values = df[column].dropna().drop_duplicates().sort_values().tolist()
        # Create a DataFrame for the unique values
        filter_df = pd.DataFrame(unique_values, columns=["value"])
        # Create a table for the filter values
        table_name = f"filter_values_{column}"
        connection.execute(text(f"DROP TABLE IF EXISTS {table_name}"))
        filter_df.to_sql(table_name, engine, if_exists='replace', index=False)

# Precompute dependent filter relationships
print("Precomputing dependent filter relationships...")
# Parent agency to sub-agency
parent_to_sub = df[['parent_award_agency_name', 'funding_sub_agency_name']].drop_duplicates().dropna()
parent_to_sub = parent_to_sub.groupby('parent_award_agency_name')['funding_sub_agency_name'].apply(list).reset_index()
parent_to_sub.columns = ['parent_value', 'child_values']
parent_to_sub['child_column'] = 'funding_sub_agency_name'

# Sub-agency to funding office
sub_to_office = df[['funding_sub_agency_name', 'funding_office_name']].drop_duplicates().dropna()
sub_to_office = sub_to_office.groupby('funding_sub_agency_name')['funding_office_name'].apply(list).reset_index()
sub_to_office.columns = ['parent_value', 'child_values']
sub_to_office['child_column'] = 'funding_office_name'

# Combine into a single table
filter_dependencies = pd.concat([parent_to_sub, sub_to_office], ignore_index=True)

# Serialize child_values as JSON strings
filter_dependencies['child_values'] = filter_dependencies['child_values'].apply(json.dumps)

# Save to database
with engine.connect() as connection:
    connection.execute(text("DROP TABLE IF EXISTS filter_dependencies"))
    filter_dependencies.to_sql('filter_dependencies', engine, if_exists='replace', index=False)

# Pre-aggregate data for visualizations (e.g., quarterly spending and award counts)
print("Pre-aggregating data for visualizations...")
# Convert action_date to datetime for fiscal year calculation
df['action_date'] = pd.to_datetime(df['action_date'], errors='coerce')
# Calculate fiscal year and quarter
months = df['action_date'].dt.month
years = df['action_date'].dt.year
fiscal_years = years + (months >= 10).astype(int)
fiscal_quarters = pd.cut(
    months,
    bins=[0, 3, 6, 9, 12],
    labels=[2, 3, 4, 1],
    include_lowest=True,
    right=True
).astype(int)
fiscal_quarters = fiscal_quarters.where(months < 10, 1)
df['fiscal_year'] = fiscal_years
df['fiscal_quarter'] = fiscal_quarters
df['year_quarter'] = 'FY' + df['fiscal_year'].astype(str) + ' Q' + df['fiscal_quarter'].astype(str)

# Aggregate quarterly spending and award counts
quarterly_spending = df.groupby('year_quarter')['federal_action_obligation'].sum().reset_index()
quarterly_awards = df[df['modification_number'] == '0'].groupby('year_quarter').size().reset_index(name='award_count')

# Merge into a single table
quarterly_data = quarterly_spending.merge(quarterly_awards, on='year_quarter', how='outer').fillna(0)
quarterly_data['fiscal_year'] = quarterly_data['year_quarter'].str.extract(r'(FY\d{4})')[0]
quarterly_data['cumulative_spending'] = quarterly_data.groupby('fiscal_year')['federal_action_obligation'].cumsum()
quarterly_data['cumulative_awards'] = quarterly_data.groupby('fiscal_year')['award_count'].cumsum()

# Save to database
with engine.connect() as connection:
    connection.execute(text("DROP TABLE IF EXISTS quarterly_data"))
    quarterly_data.to_sql('quarterly_data', engine, if_exists='replace', index=False)

print("Data cleaning complete. New tables created: awards_slim_cleaned, filter values, filter_dependencies, quarterly_data.")
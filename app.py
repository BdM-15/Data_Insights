import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
import plotly.express as px

# Set page config FIRST
st.set_page_config(page_title="USAspending.gov Dashboard", layout="wide")

# Connect to the SQLite database
db_path = r'sqlite:///C:\GitHub\Opp_Sem_Search\backend\data\usaspending_historical.db'
engine = create_engine(db_path)

# Define the updated column mapping with human-readable names
column_mapping = {
    "award_id_piid": "Award ID",
    "parent_award_id_piid": "Parent Award ID",
    "naics_code": "NAICS Code",
    "product_or_service_code": "PSC Code",
    "transaction_description": "Contract Description",
    "federal_action_obligation": "Contract Award Amount",
    "total_dollars_obligated": "Total Obligated Amount",
    "current_total_value_of_award": "Current Contract Value",
    "potential_total_value_of_award": "Potential Contract Value",
    "action_date": "Award Date",
    "period_of_performance_start_date": "Period of Performance Start Date",
    "period_of_performance_current_end_date": "Period of Performance End Date",
    "ordering_period_end_date": "Last Date to Order",
    "awarding_agency_name": "Awarding Agency Name",
    "awarding_sub_agency_name": "Awarding Sub-Agency Name",
    "awarding_office_name": "Contracting Office Name",
    "funding_agency_name": "Funding Agency Name",
    "recipient_name": "Contractor Name",
    "recipient_duns": "Contractor DUNS Number",
    "recipient_parent_name": "Parent Company Name",
    "recipient_address_line_1": "Contractor Address",
    "type_of_contract_pricing": "Type of Contract",
    "extent_competed": "Extent Competed",
    "number_of_offers_received": "Number of Offers Received",
    "type_of_set_aside": "Set-Aside Type",
    "solicitation_procedures": "Solicitation Procedures",
    "primary_place_of_performance_state_name": "Place of Performance State",
    "primary_place_of_performance_zip_4": "Place of Performance Zip Code",
    "primary_place_of_performance_city_name": "Principal Place of Performance",
    "award_type": "Contract Type"
}

# Function to fetch unique values for dropdowns
@st.cache_data
def get_unique_values(column_name, table_name='awards'):
    query = f"SELECT DISTINCT {column_name} FROM {table_name} WHERE {column_name} IS NOT NULL ORDER BY {column_name}"
    try:
        with engine.connect() as connection:
            df = pd.read_sql(text(query), connection)
        return df[column_name].tolist()
    except Exception as e:
        st.error(f"Error fetching unique values for {column_name}: {str(e)}")
        return []

# Main app title
st.title("USAspending.gov Data Explorer")

# Display the table name professionally
st.subheader("Data Source")
st.markdown(
    """
    <div style="background-color: #2E2E2E; padding: 10px; border-radius: 5px; border: 1px solid #555;">
        <p style="color: #FFFFFF; margin: 0;">Table: <strong>awards</strong></p>
    </div>
    """,
    unsafe_allow_html=True
)

# Sidebar for filters
with st.sidebar:
    st.header("Filters")
    
    # Date range selection
    start_date = st.date_input("Start Date", value=pd.to_datetime("2018-01-01"))
    end_date = st.date_input("End Date", value=pd.to_datetime("2023-12-31"))
    
    # Convert dates to string format for SQLite
    start_date_str = start_date.strftime('%Y-%m-%d')
    end_date_str = end_date.strftime('%Y-%m-%d')
    
    # Dropdowns based on unique values
    agencies = get_unique_values('awarding_agency_name', table_name='awards')
    selected_agency = st.selectbox("Select Awarding Agency", ["All"] + agencies)
    
    sub_agencies = get_unique_values('awarding_sub_agency_name', table_name='awards')
    selected_sub_agency = st.selectbox("Select Awarding Sub-Agency", ["All"] + sub_agencies)
    
    contractors = get_unique_values('recipient_name', table_name='awards')
    selected_contractor = st.selectbox("Select Contractor", ["All"] + contractors)
    
    naics_codes = get_unique_values('naics_code', table_name='awards')
    selected_naics = st.selectbox("Select NAICS Code", ["All"] + naics_codes)
    
    psc_codes = get_unique_values('product_or_service_code', table_name='awards')
    selected_psc = st.selectbox("Select PSC Code", ["All"] + psc_codes)
    
    contract_types = get_unique_values('type_of_contract_pricing', table_name='awards')
    selected_contract_type = st.selectbox("Select Type of Contract", ["All"] + contract_types)
    
    extent_competeds = get_unique_values('extent_competed', table_name='awards')
    selected_extent_competed = st.selectbox("Select Extent Competed", ["All"] + extent_competeds)
    
    set_aside_types = get_unique_values('type_of_set_aside', table_name='awards')
    selected_set_aside = st.selectbox("Select Set-Aside Type", ["All"] + set_aside_types)

# Build the SQL query dynamically with named placeholders
columns_to_select = list(column_mapping.keys())
query = f"SELECT {', '.join(columns_to_select)} FROM awards WHERE action_date BETWEEN :start_date AND :end_date"
params = {"start_date": start_date_str, "end_date": end_date_str}

# Add filters to the query if selections are made
if selected_agency != "All":
    query += " AND awarding_agency_name = :agency"
    params["agency"] = selected_agency
if selected_sub_agency != "All":
    query += " AND awarding_sub_agency_name = :sub_agency"
    params["sub_agency"] = selected_sub_agency
if selected_contractor != "All":
    query += " AND recipient_name = :contractor"
    params["contractor"] = selected_contractor
if selected_naics != "All":
    query += " AND naics_code = :naics"
    params["naics"] = selected_naics
if selected_psc != "All":
    query += " AND product_or_service_code = :psc"
    params["psc"] = selected_psc
if selected_contract_type != "All":
    query += " AND type_of_contract_pricing = :contract_type"
    params["contract_type"] = selected_contract_type
if selected_extent_competed != "All":
    query += " AND extent_competed = :extent_competed"
    params["extent_competed"] = selected_extent_competed
if selected_set_aside != "All":
    query += " AND type_of_set_aside = :set_aside"
    params["set_aside"] = selected_set_aside

# Display results
if st.button("Run Query"):
    try:
        with engine.connect() as connection:
            df = pd.read_sql(text(query), connection, params=params)
        
        # Display the results with human-readable column names
        st.write("Query Results", df.rename(columns=column_mapping))
        
        # Convert federal_action_obligation to numeric for visualization
        df['federal_action_obligation'] = pd.to_numeric(df['federal_action_obligation'], errors='coerce')
        
        # Visualize spending trends over time
        st.subheader("Spending Trends")
        df['award_year'] = pd.to_datetime(df['action_date']).dt.year
        fig = px.line(df.groupby('award_year')['federal_action_obligation'].sum(), 
                      title="Total Spending by Year")
        st.plotly_chart(fig)
    except Exception as e:
        st.error(f"Error executing query: {str(e)}")
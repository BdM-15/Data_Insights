import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
import plotly.express as px
from datetime import datetime
import re

# Set page config FIRST
st.set_page_config(page_title="USAspending.gov Dashboard", layout="wide")

# Increase the maximum number of cells for Pandas Styler
pd.set_option('styler.render.max_elements', 1000000)

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

# Function to fetch unique values for dropdowns with cleaning
@st.cache_data
def get_unique_values(column_name, table_name='awards', filter_conditions=None):
    # Special handling for naics_code to ensure it's treated as a string
    if column_name == 'naics_code':
        query = f"SELECT DISTINCT TRIM(CAST({column_name} AS TEXT)) AS {column_name} FROM {table_name} WHERE {column_name} IS NOT NULL"
    else:
        query = f"SELECT DISTINCT TRIM({column_name}) AS {column_name} FROM {table_name} WHERE {column_name} IS NOT NULL"
    
    params = {}
    if filter_conditions:
        conditions = []
        for condition in filter_conditions:
            if condition["value"] not in ["All", None]:
                # Convert the filter value to uppercase to match the database case
                condition_value = str(condition["value"]).upper()
                if isinstance(condition["value"], list):
                    conditions.append(f"UPPER({condition['column']}) IN :{condition['column']}")
                    params[condition["column"]] = tuple(condition_value)
                else:
                    conditions.append(f"UPPER({condition['column']}) = :{condition['column']}")
                    params[condition["column"]] = condition_value
        if conditions:
            query += " AND " + " AND ".join(conditions)
    query += f" ORDER BY {column_name}"
    try:
        with engine.connect() as connection:
            df = pd.read_sql(text(query), connection, params=params)
        # Convert to uppercase and remove duplicates
        unique_values = df[column_name].str.upper().drop_duplicates().tolist()
        # Clean up NAICS codes to remove .0 suffix using re.sub
        if column_name == 'naics_code':
            unique_values = [re.sub(r'\.0$', '', str(val)) for val in unique_values]
        return unique_values
    except Exception as e:
        st.error(f"Error fetching unique values for {column_name}: {str(e)}")
        return []

# Function to generate all quarters between start and end dates
def generate_quarters(start_date, end_date):
    quarters = []
    current_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)
    while current_date <= end_date:
        year = current_date.year
        quarter = (current_date.month - 1) // 3 + 1
        quarters.append(f"{year} Q{quarter}")
        current_date = current_date + pd.offsets.QuarterBegin(1)
    return quarters

# Main app title
st.title("USAspending.gov Data Explorer")

# Display the table name professionally
st.subheader("Data Source")
st.markdown(
    """
    <div style="background-color: #2E2E2E; padding: 10px; border-radius: 5px; border: 1px solid #555;">
        <p style="color: #FFFFFF; margin: 0;">Table: <strong>Awards</strong></p>
    </div>
    """,
    unsafe_allow_html=True
)

# Sidebar for filters
with st.sidebar:
    st.header("Filters")
    
    # Date range selection
    start_date = st.date_input("Start Date", value=pd.to_datetime("2019-03-29"))
    end_date = st.date_input("End Date", value=pd.to_datetime("2024-09-30"))
    
    # Convert dates to string format for SQLite
    start_date_str = start_date.strftime('%Y-%m-%d')
    end_date_str = end_date.strftime('%Y-%m-%d')
    
    # Single-select dropdown for awarding agency
    agencies = ["All"] + get_unique_values('awarding_agency_name', table_name='awards')
    selected_agency = st.selectbox("Select Awarding Agency", agencies, index=0, key="agency")
    
    # Filter sub-agencies based on selected agency
    sub_agencies = ["All"]
    if selected_agency != "All":
        sub_agencies.extend(get_unique_values('awarding_sub_agency_name', table_name='awards', 
                                             filter_conditions=[{"column": "awarding_agency_name", "value": selected_agency}]))
        if len(sub_agencies) == 1:  # Only "All" is present
            st.warning(f"No sub-agencies found for {selected_agency}. Check the data or select a different agency.")
    selected_sub_agency = st.selectbox("Select Awarding Sub-Agency", sub_agencies, index=None, 
                                       placeholder="Select a sub-agency...", key="sub_agency")
    
    # Fetch contractors without dependencies
    contractors = ["All"] + get_unique_values('recipient_name', table_name='awards')
    selected_contractor = st.selectbox("Select Contractor", contractors, index=None, 
                                       placeholder="Select a contractor...", key="contractor")
    
    # Fetch NAICS codes without dependencies
    naics_codes = ["All"] + get_unique_values('naics_code', table_name='awards')
    selected_naics = st.selectbox("Select NAICS Code", naics_codes, index=None, 
                                  placeholder="Select a NAICS code...", key="naics")
    
    # Fetch PSC codes without dependencies
    psc_codes = ["All"] + get_unique_values('product_or_service_code', table_name='awards')
    selected_psc = st.selectbox("Select PSC Code", psc_codes, index=None, 
                                placeholder="Select a PSC code...", key="psc")
    
    # Fetch contract types without dependencies
    contract_types = ["All"] + get_unique_values('type_of_contract_pricing', table_name='awards')
    selected_contract_type = st.selectbox("Select Type of Contract", contract_types, index=None, 
                                          placeholder="Select a contract type...", key="contract_type")
    
    # Fetch extent competed without dependencies
    extent_competeds = ["All"] + get_unique_values('extent_competed', table_name='awards')
    selected_extent_competed = st.selectbox("Select Extent Competed", extent_competeds, index=None, 
                                            placeholder="Select an extent competed...", key="extent_competed")
    
    # Fetch set-aside types without dependencies
    set_aside_types = ["All"] + get_unique_values('type_of_set_aside', table_name='awards')
    selected_set_aside = st.selectbox("Select Set-Aside Type", set_aside_types, index=None, 
                                      placeholder="Select a set-aside type...", key="set_aside")

# Build the SQL query dynamically with named placeholders
columns_to_select = list(column_mapping.keys())
query = f"SELECT {', '.join(columns_to_select)} FROM awards WHERE action_date BETWEEN :start_date AND :end_date"
params = {"start_date": start_date_str, "end_date": end_date_str}

# Add filters to the query if selections are made
if selected_agency != "All":
    query += " AND UPPER(awarding_agency_name) = :agency"
    params["agency"] = str(selected_agency).upper()
if selected_sub_agency not in ["All", None]:
    query += " AND UPPER(awarding_sub_agency_name) = :sub_agency"
    params["sub_agency"] = str(selected_sub_agency).upper()
if selected_contractor not in ["All", None]:
    query += " AND UPPER(recipient_name) = :contractor"
    params["contractor"] = str(selected_contractor).upper()
if selected_naics not in ["All", None]:
    query += " AND UPPER(naics_code) = :naics"
    params["naics"] = str(selected_naics).upper()
if selected_psc not in ["All", None]:
    query += " AND UPPER(product_or_service_code) = :psc"
    params["psc"] = str(selected_psc).upper()
if selected_contract_type not in ["All", None]:
    query += " AND UPPER(type_of_contract_pricing) = :contract_type"
    params["contract_type"] = str(selected_contract_type).upper()
if selected_extent_competed not in ["All", None]:
    query += " AND UPPER(extent_competed) = :extent_competed"
    params["extent_competed"] = str(selected_extent_competed).upper()
if selected_set_aside not in ["All", None]:
    query += " AND UPPER(type_of_set_aside) = :set_aside"
    params["set_aside"] = str(selected_set_aside).upper()

# Display results
if st.button("Run Query"):
    try:
        with engine.connect() as connection:
            df = pd.read_sql(text(query), connection, params=params)
        
        # Convert monetary columns to numeric for formatting
        monetary_columns = ['federal_action_obligation', 'total_dollars_obligated', 
                           'current_total_value_of_award', 'potential_total_value_of_award']
        for col in monetary_columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Clean up NAICS codes in the DataFrame
        df['naics_code'] = df['naics_code'].astype(str).str.replace(r'\.0$', '', regex=True)
        
        # Rename columns for display
        df_display = df.rename(columns=column_mapping)
        
        # Sort by federal_action_obligation (Contract Award Amount) in descending order
        df_display = df_display.sort_values(by="Contract Award Amount", ascending=False)
        
        # Limit to top 100 rows before styling
        df_display_limited = df_display.head(100)
        
        # Format monetary columns as currency
        format_dict = {col: "${:,.2f}" for col in [column_mapping[col] for col in monetary_columns]}
        styled_df = df_display_limited.style.format(format_dict)
        
        # Display the styled DataFrame (limited to top 100 rows)
        st.subheader("Query Results (Top 100 Rows)")
        st.dataframe(styled_df, use_container_width=True)
        
        # Provide a download button for the full dataset
        csv = df_display.to_csv(index=False)
        st.download_button(
            label="Download Full Results as CSV",
            data=csv,
            file_name="usaspending_query_results.csv",
            mime="text/csv",
        )
        
        # Create a quarter column for the chart
        df['action_date'] = pd.to_datetime(df['action_date'])
        df['year'] = df['action_date'].dt.year
        df['quarter'] = df['action_date'].dt.quarter
        df['year_quarter'] = df['year'].astype(str) + ' Q' + df['quarter'].astype(str)
        
        # Generate all quarters between start and end dates
        all_quarters = generate_quarters(start_date, end_date)
        
        # Group by quarter and calculate total spending
        quarterly_spending = df.groupby('year_quarter')['federal_action_obligation'].sum().reset_index()
        
        # Create a DataFrame with all quarters and merge with spending data
        quarterly_df = pd.DataFrame({'year_quarter': all_quarters})
        quarterly_df = quarterly_df.merge(quarterly_spending, on='year_quarter', how='left')
        quarterly_df['federal_action_obligation'] = quarterly_df['federal_action_obligation'].fillna(0)
        
        # Visualize spending trends by quarter
        st.subheader("Spending Trends")
        fig = px.line(quarterly_df, x='year_quarter', y='federal_action_obligation', 
                      title="Total Spending by Quarter")
        fig.update_layout(xaxis_title="Quarter", yaxis_title="Total Spending ($)")
        st.plotly_chart(fig)
    except Exception as e:
        st.error(f"Error executing query: {str(e)}")

# Note about database optimization
st.markdown(
    """
    **Performance Note**: To improve filter performance, consider adding indexes to the following columns in the `awards` table: 
    `awarding_agency_name`, `awarding_sub_agency_name`, `recipient_name`, `naics_code`, `product_or_service_code`, 
    `type_of_contract_pricing`, `extent_competed`, `type_of_set_aside`. 
    Example SQL: `CREATE INDEX idx_awarding_agency_name ON awards(awarding_agency_name);`
    """
)
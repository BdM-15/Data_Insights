import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import re

# Set page config FIRST
st.set_page_config(page_title="USAspending.gov Dashboard", layout="wide")

# Increase the maximum number of cells for Pandas Styler
pd.set_option('styler.render.max_elements', 1000000)

# Connect to the SQLite database with a timeout
db_path = r'sqlite:///C:\GitHub\Opp_Sem_Search\backend\data\usaspending_historical.db?timeout=30'
engine = create_engine(db_path, connect_args={'timeout': 30})

# Define the updated column mapping with human-readable names
column_mapping = {
    "action_date_fiscal_year": "Award Fiscal Year",
    "action_date": "Award Date",
    "parent_award_id_piid": "Parent Award ID",
    "award_id_piid": "Award ID",
    "modification_number": "Modification Number",
    "federal_action_obligation": "Contract Award Amount",
    "total_dollars_obligated": "Total Obligated Amount",
    "potential_total_value_of_award": "Potential Contract Value",
    "total_outlayed_amount_for_overall_award": "Total Outlayed Amount",
    "period_of_performance_start_date": "Period of Performance Start Date",
    "period_of_performance_current_end_date": "Period of Performance End Date",
    "period_of_performance_potential_end_date": "Period of Performance Potential End Date",
    "ordering_period_end_date": "Last Date to Order",
    "primary_place_of_performance_city_name": "Principal Place of Performance",
    "primary_place_of_performance_state_code": "Place of Performance State",
    "prime_award_base_transaction_description": "Prime Award Transaction Description",
    "transaction_description": "Contract Description",
    "naics_code": "NAICS Code",
    "naics_description": "NAICS Description",
    "product_or_service_code": "PSC Code",
    "product_or_service_code_description": "PSC Description",
    "dod_acquisition_program_description": "DoD Acquisition Program Description",
    "parent_award_agency_name": "Awarding Agency Name",
    "awarding_sub_agency_name": "Awarding Sub-Agency Name",
    "awarding_office_name": "Contracting Office Name",
    "funding_agency_name": "Funding Agency Name",
    "funding_sub_agency_name": "Funding Sub-Agency Name",
    "funding_office_name": "Funding Office Name",
    "recipient_name": "Contractor Name",
    "recipient_uei": "Contractor UEI",
    "recipient_parent_name": "Parent Company Name",
    "recipient_parent_uei": "Parent Company UEI",
    "solicitation_date": "Solicitation Date",
    "solicitation_procedures": "Solicitation Procedures",
    "extent_competed": "Extent Competed",
    "type_of_set_aside": "Set-Aside Type",
    "fair_opportunity_limited_sources": "Fair Opportunity Limited Sources",
    "other_than_full_and_open_competition": "Other Than Full and Open Competition",
    "number_of_offers_received": "Number of Offers Received",
    "subcontracting_plan": "Subcontracting Plan",
    "government_furnished_property": "Government Furnished Property",
    "type_of_contract_pricing": "Type of Contract",
    "action_type": "Action Type",
    "award_type": "Award Type",
    "type_of_idc": "IDC Type",
    "idv_type": "IDV Type",
    "undefinitized_action": "Undefinitized Action",
    "program_acronym": "Program Acronym",
    "multi_year_contract": "Multi-Year Contract",
    "multiple_or_single_award_idv": "Multiple or Single Award IDV",
    "usaspending_permalink": "USAspending Permalink"
}

# Function to fetch unique values for dropdowns with cleaning
@st.cache_data
def get_unique_values(column_name, table_name='awards_slim', filter_conditions=None):
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

# Function to calculate the federal fiscal year and quarter (vectorized)
def calculate_fiscal_year_quarter(dates):
    # Federal fiscal year runs from October 1 to September 30
    # Q1: Oct 1 - Dec 31
    # Q2: Jan 1 - Mar 31
    # Q3: Apr 1 - Jun 30
    # Q4: Jul 1 - Sep 30
    months = dates.dt.month
    years = dates.dt.year
    
    # Fiscal year: If the date is on or after October 1, it belongs to the next fiscal year
    fiscal_years = years + (months >= 10).astype(int)
    
    # Fiscal quarter
    fiscal_quarters = pd.cut(
        months,
        bins=[0, 3, 6, 9, 12],
        labels=[2, 3, 4, 1],
        include_lowest=True,
        right=True
    ).astype(int)
    
    # Adjust quarters for dates in October-December (Q1 of the next fiscal year)
    fiscal_quarters = fiscal_quarters.where(months < 10, 1)
    
    return fiscal_years, fiscal_quarters

# Function to generate all fiscal quarters between start and end dates
def generate_fiscal_quarters(start_date, end_date):
    start_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)
    
    # Calculate the fiscal year and quarter for the start and end dates
    start_fy, start_fq = calculate_fiscal_year_quarter(pd.Series([start_date]))[0][0], calculate_fiscal_year_quarter(pd.Series([start_date]))[1][0]
    end_fy, end_fq = calculate_fiscal_year_quarter(pd.Series([end_date]))[0][0], calculate_fiscal_year_quarter(pd.Series([end_date]))[1][0]
    
    quarters = []
    current_fy = start_fy
    current_fq = start_fq
    
    while True:
        quarters.append(f"FY{current_fy} Q{current_fq}")
        if current_fy == end_fy and current_fq == end_fq:
            break
        
        # Increment the fiscal quarter
        current_fq += 1
        if current_fq > 4:
            current_fq = 1
            current_fy += 1
    
    return quarters

# Main app title
st.title("USAspending.gov Data Explorer")

# Display the table name professionally
st.subheader("Data Source")
st.markdown(
    """
    <div style="background-color: #2E2E2E; padding: 10px; border-radius: 5px; border: 1px solid #555;">
        <p style="color: #FFFFFF; margin: 0;">Table: <strong>awards_slim</strong></p>
    </div>
    """,
    unsafe_allow_html=True
)

# Sidebar for filters
with st.sidebar:
    st.header("Filters")
    
    # Date range selection with updated default dates
    start_date = st.date_input("Start Date", value=pd.to_datetime("2021-03-31"))
    end_date = st.date_input("End Date", value=pd.to_datetime("2024-03-31"))
    
    # Convert dates to string format for SQLite
    start_date_str = start_date.strftime('%Y-%m-%d')
    end_date_str = end_date.strftime('%Y-%m-%d')
    
    # Single-select dropdown for awarding agency (now using parent_award_agency_name)
    agencies = ["All"] + get_unique_values('parent_award_agency_name', table_name='awards_slim')
    selected_agency = st.selectbox("Select Awarding Agency", agencies, index=0, key="agency")
    
    # Filter sub-agencies based on selected agency
    sub_agencies = ["All"]
    if selected_agency != "All":
        sub_agencies.extend(get_unique_values('awarding_sub_agency_name', table_name='awards_slim', 
                                             filter_conditions=[{"column": "parent_award_agency_name", "value": selected_agency}]))
        if len(sub_agencies) == 1:  # Only "All" is present
            st.warning(f"No sub-agencies found for {selected_agency}. Check the data or select a different agency.")
    selected_sub_agency = st.selectbox("Select Awarding Sub-Agency", sub_agencies, index=None, 
                                       placeholder="Select a sub-agency...", key="sub_agency")
    
    # Fetch contractors without dependencies
    contractors = ["All"] + get_unique_values('recipient_name', table_name='awards_slim')
    selected_contractor = st.selectbox("Select Contractor", contractors, index=None, 
                                       placeholder="Select a contractor...", key="contractor")
    
    # Fetch NAICS codes without dependencies
    naics_codes = ["All"] + get_unique_values('naics_code', table_name='awards_slim')
    selected_naics = st.selectbox("Select NAICS Code", naics_codes, index=None, 
                                  placeholder="Select a NAICS code...", key="naics")
    
    # Fetch PSC codes without dependencies
    psc_codes = ["All"] + get_unique_values('product_or_service_code', table_name='awards_slim')
    selected_psc = st.selectbox("Select PSC Code", psc_codes, index=None, 
                                placeholder="Select a PSC code...", key="psc")
    
    # Fetch contract types without dependencies
    contract_types = ["All"] + get_unique_values('type_of_contract_pricing', table_name='awards_slim')
    selected_contract_type = st.selectbox("Select Type of Contract", contract_types, index=None, 
                                          placeholder="Select a contract type...", key="contract_type")
    
    # Fetch extent competed without dependencies
    extent_competeds = ["All"] + get_unique_values('extent_competed', table_name='awards_slim')
    selected_extent_competed = st.selectbox("Select Extent Competed", extent_competeds, index=None, 
                                            placeholder="Select an extent competed...", key="extent_competed")
    
    # Fetch set-aside types without dependencies
    set_aside_types = ["All"] + get_unique_values('type_of_set_aside', table_name='awards_slim')
    selected_set_aside = st.selectbox("Select Set-Aside Type", set_aside_types, index=None, 
                                      placeholder="Select a set-aside type...", key="set_aside")

# Build the SQL query dynamically with named placeholders
columns_to_select = list(column_mapping.keys())
query = f"SELECT {', '.join(columns_to_select)} FROM awards_slim WHERE action_date BETWEEN :start_date AND :end_date"
params = {"start_date": start_date_str, "end_date": end_date_str}

# Add filters to the query if selections are made
if selected_agency != "All":
    query += " AND UPPER(parent_award_agency_name) = :agency"
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
                           'potential_total_value_of_award', 'total_outlayed_amount_for_overall_award']
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
        
        # Create a fiscal quarter column for the chart (vectorized)
        df['action_date'] = pd.to_datetime(df['action_date'])
        fiscal_years, fiscal_quarters = calculate_fiscal_year_quarter(df['action_date'])
        df['fiscal_year'] = fiscal_years
        df['fiscal_quarter'] = fiscal_quarters
        df['year_quarter'] = df.apply(lambda x: f"FY{x['fiscal_year']} Q{x['fiscal_quarter']}", axis=1)
        
        # Generate all fiscal quarters between start and end dates
        all_quarters = generate_fiscal_quarters(start_date, end_date)
        
        # Group by fiscal quarter and calculate total spending and number of award actions
        # Award actions are counted where modification_number = '0' (as a string)
        quarterly_spending = df.groupby('year_quarter')['federal_action_obligation'].sum().reset_index()
        quarterly_awards = df[df['modification_number'] == '0'].groupby('year_quarter').size().reset_index(name='award_count')
        
        # Create a DataFrame with all quarters and merge with spending and award count data
        quarterly_df = pd.DataFrame({'year_quarter': all_quarters})
        quarterly_df = quarterly_df.merge(quarterly_spending, on='year_quarter', how='left')
        quarterly_df = quarterly_df.merge(quarterly_awards, on='year_quarter', how='left')
        quarterly_df['federal_action_obligation'] = quarterly_df['federal_action_obligation'].fillna(0)
        quarterly_df['award_count'] = quarterly_df['award_count'].fillna(0)
        
        # Determine tick values for the right y-axis (Number of Award Actions)
        max_awards = quarterly_df['award_count'].max()
        num_ticks = 5  # Number of ticks to display on the right y-axis
        award_step = max_awards / (num_ticks - 1) if max_awards > 0 else 1
        award_ticks = [i * award_step for i in range(num_ticks)]
        
        # Visualize spending trends by quarter with award actions overlaid (dual-axis)
        st.subheader("Spending and Award Actions by Quarter")
        fig = go.Figure()
        
        # Add line for total spending (left y-axis)
        fig.add_trace(
            go.Scatter(
                x=quarterly_df['year_quarter'],
                y=quarterly_df['federal_action_obligation'],
                name="Total Spending ($)",
                line=dict(color='blue')
            )
        )
        
        # Add line for number of award actions (right y-axis, unscaled)
        fig.add_trace(
            go.Scatter(
                x=quarterly_df['year_quarter'],
                y=quarterly_df['award_count'],
                name="Number of Award Actions",
                line=dict(color='orange'),
                yaxis="y2"
            )
        )
        
        # Update layout for dual-axis
        fig.update_layout(
            title="Spending and Award Actions by Quarter",
            xaxis=dict(title="Fiscal Quarter"),
            yaxis=dict(
                title="Total Spending ($)",
                title_font=dict(color="blue", size=14),
                tickfont=dict(color="blue", size=12),
                gridcolor="lightgrey"
            ),
            yaxis2=dict(
                title="Number of Award Actions",
                title_font=dict(color="orange", size=14),
                tickfont=dict(color="orange", size=12),
                overlaying="y",
                side="right",
                showgrid=False,  # Hide the grid lines for the right y-axis
                range=[0, max_awards * 1.1],  # Add some padding to the top
                tickvals=award_ticks,  # Set tick values based on award count
                ticktext=[f"{int(tick):,}" for tick in award_ticks]  # Show the actual award count values, formatted with commas
            ),
            legend=dict(x=0, y=1.1, orientation="h")
        )
        st.plotly_chart(fig)
        
        # Visualize Top 20 Recipients by Total Awards Made
        st.subheader("Top 20 Recipients by Total Awards Made")
        top_recipients_awards = df[df['modification_number'] == '0'].groupby('recipient_name').size().reset_index(name='award_count')
        top_recipients_awards = top_recipients_awards.sort_values(by='award_count', ascending=False).head(20)
        
        fig_recipients_awards = px.bar(
            top_recipients_awards,
            x='recipient_name',
            y='award_count',
            title="Top 20 Recipients by Total Awards Made",
            labels={'recipient_name': 'Recipient Name', 'award_count': 'Number of Awards'}
        )
        fig_recipients_awards.update_layout(xaxis_tickangle=45)
        st.plotly_chart(fig_recipients_awards)
        
        # Visualize Top 20 Recipients by Total Dollars Obligated
        st.subheader("Top 20 Recipients by Total Dollars Obligated")
        top_recipients_dollars = df.groupby('recipient_name')['total_dollars_obligated'].sum().reset_index()
        top_recipients_dollars = top_recipients_dollars.sort_values(by='total_dollars_obligated', ascending=False).head(20)
        
        fig_recipients_dollars = px.bar(
            top_recipients_dollars,
            x='recipient_name',
            y='total_dollars_obligated',
            title="Top 20 Recipients by Total Dollars Obligated",
            labels={'recipient_name': 'Recipient Name', 'total_dollars_obligated': 'Total Dollars Obligated ($)'}
        )
        fig_recipients_dollars.update_layout(xaxis_tickangle=45)
        st.plotly_chart(fig_recipients_dollars)
        
    except Exception as e:
        st.error(f"Error executing query: {str(e)}")

# Note about database optimization
st.markdown(
    """
    **Performance Note**: The `awards_slim` table has been updated with fewer columns to improve query performance. 
    To further optimize, consider adding indexes to the following columns: 
    `parent_award_agency_name`, `awarding_sub_agency_name`, `recipient_name`, `naics_code`, `product_or_service_code`, 
    `type_of_contract_pricing`, `extent_competed`, `type_of_set_aside`, `action_date`. 
    Example SQL: `CREATE INDEX idx_parent_award_agency_name ON awards_slim(parent_award_agency_name);`
    """
)
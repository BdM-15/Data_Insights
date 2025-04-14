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

# Define a color palette for all bar charts
color_palette = px.colors.qualitative.Plotly * 2  # Repeat to ensure at least 20 colors

# Cached function to fetch unique values for dropdowns
@st.cache_data
def get_unique_values(column_name, table_name='awards_slim', filter_conditions=None):
    if column_name == 'naics_code':
        query = f"SELECT DISTINCT TRIM(CAST({column_name} AS TEXT)) AS {column_name} FROM {table_name} WHERE {column_name} IS NOT NULL"
    else:
        query = f"SELECT DISTINCT TRIM({column_name}) AS {column_name} FROM {table_name} WHERE {column_name} IS NOT NULL"
    
    params = {}
    if filter_conditions:
        conditions = []
        for condition in filter_conditions:
            if condition["value"] not in ["All", None]:
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
        unique_values = df[column_name].str.upper().drop_duplicates().tolist()
        if column_name == 'naics_code':
            unique_values = [re.sub(r'\.0$', '', str(val))[:6] for val in unique_values]
        return unique_values
    except Exception as e:
        st.error(f"Error fetching unique values for {column_name}: {str(e)}")
        return []

# Function to calculate the federal fiscal year and quarter (vectorized)
def calculate_fiscal_year_quarter(dates):
    months = dates.dt.month
    years = dates.dt.year
    fiscal_years = years + (months >= 10).astype(int)
    fiscal_quarters = pd.cut(
        months,
        bins=[0, 3, 6, 9, 12],
        labels=[2, 3, 4, 1],
        include_lowest=True,
        right=True
    ).astype(int)
    fiscal_quarters = fiscal_quarters.where(months < 10, 1)
    return fiscal_years, fiscal_quarters

# Function to generate all fiscal quarters between start and end dates
def generate_fiscal_quarters(start_date, end_date):
    start_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)
    start_fy, start_fq = calculate_fiscal_year_quarter(pd.Series([start_date]))[0][0], calculate_fiscal_year_quarter(pd.Series([start_date]))[1][0]
    end_fy, end_fq = calculate_fiscal_year_quarter(pd.Series([end_date]))[0][0], calculate_fiscal_year_quarter(pd.Series([end_date]))[1][0]
    quarters = []
    current_fy = start_fy
    current_fq = start_fq
    while True:
        quarters.append(f"FY{current_fy} Q{current_fq}")
        if current_fy == end_fy and current_fq == end_fq:
            break
        current_fq += 1
        if current_fq > 4:
            current_fq = 1
            current_fy += 1
    return quarters

# Cached function to load data
@st.cache_data
def load_data(query, params):
    with engine.connect() as connection:
        df = pd.read_sql(text(query), connection, params=params)
    return df

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

# Sidebar for filters with session state to force rerun on change
with st.sidebar:
    st.header("Filters")
    
    start_date = st.date_input("Start Date", value=pd.to_datetime("2022-10-01"), key="start_date")
    end_date = st.date_input("End Date", value=pd.to_datetime("2025-03-31"), key="end_date")
    
    start_date_str = start_date.strftime('%Y-%m-%d')
    end_date_str = end_date.strftime('%Y-%m-%d')
    
    agencies = ["All"] + get_unique_values('parent_award_agency_name', table_name='awards_slim')
    selected_agency = st.selectbox("Select Awarding Agency", agencies, index=0, key="agency")
    
    funding_sub_agencies = ["All"]
    if selected_agency != "All":
        funding_sub_agencies.extend(get_unique_values('funding_sub_agency_name', table_name='awards_slim', 
                                                     filter_conditions=[{"column": "parent_award_agency_name", "value": selected_agency}]))
        if len(funding_sub_agencies) == 1:
            st.warning(f"No funding sub-agencies found for {selected_agency}. Check the data or select a different agency.")
    selected_funding_sub_agency = st.selectbox("Select Funding Sub-Agency", funding_sub_agencies, index=None, 
                                               placeholder="Select a funding sub-agency...", key="funding_sub_agency")
    
    funding_office_names = ["All"]
    if selected_funding_sub_agency not in ["All", None]:
        funding_office_names.extend(get_unique_values('funding_office_name', table_name='awards_slim', 
                                                     filter_conditions=[{"column": "funding_sub_agency_name", "value": selected_funding_sub_agency}]))
        if len(funding_office_names) == 1:
            st.warning(f"No funding offices found for {selected_funding_sub_agency}. Check the data or select a different sub-agency.")
    selected_funding_office = st.selectbox("Select Funding Office", funding_office_names, index=None, 
                                           placeholder="Select a funding office...", key="funding_office")
    
    contractors = ["All"] + get_unique_values('recipient_name', table_name='awards_slim')
    selected_contractor = st.selectbox("Select Contractor", contractors, index=None, 
                                       placeholder="Select a contractor...", key="contractor")
    
    naics_codes = ["All"] + get_unique_values('naics_code', table_name='awards_slim')
    selected_naics = st.selectbox("Select NAICS Code", naics_codes, index=None, 
                                  placeholder="Select a NAICS code...", key="naics")
    
    psc_codes = ["All"] + get_unique_values('product_or_service_code', table_name='awards_slim')
    selected_psc = st.selectbox("Select PSC Code", psc_codes, index=None, 
                                placeholder="Select a PSC code...", key="psc")
    
    contract_types = ["All"] + get_unique_values('type_of_contract_pricing', table_name='awards_slim')
    selected_contract_type = st.selectbox("Select Type of Contract", contract_types, index=None, 
                                          placeholder="Select a contract type...", key="contract_type")
    
    extent_competeds = get_unique_values('extent_competed', table_name='awards_slim')
    selected_extent_competeds = st.multiselect("Select Extent Competed", extent_competeds, 
                                               placeholder="Select extent competed options...", key="extent_competed")
    
    set_aside_types = ["All"] + get_unique_values('type_of_set_aside', table_name='awards_slim')
    selected_set_aside = st.selectbox("Select Set-Aside Type", set_aside_types, index=None, 
                                      placeholder="Select a set-aside type...", key="set_aside")

# Define the minimal set of columns needed
columns_needed = [
    "action_date", "federal_action_obligation", "modification_number", "total_dollars_obligated",
    "period_of_performance_current_end_date", "recipient_name", "naics_code",
    "parent_award_agency_name", "funding_sub_agency_name", "funding_office_name",
    "parent_award_id_piid", "award_id_piid", "potential_total_value_of_award",
    "primary_place_of_performance_city_name", "primary_place_of_performance_state_code",
    "prime_award_base_transaction_description", "transaction_description",
    "naics_description", "product_or_service_code", "product_or_service_code_description",
    "awarding_office_name", "recipient_uei", "recipient_parent_name", "recipient_parent_uei",
    "solicitation_date", "solicitation_procedures", "extent_competed", "type_of_set_aside",
    "fair_opportunity_limited_sources", "other_than_full_and_open_competition",
    "number_of_offers_received", "subcontracting_plan", "government_furnished_property",
    "type_of_contract_pricing", "usaspending_permalink"
]

# Build the SQL query dynamically with named placeholders
query = f"SELECT {', '.join(columns_needed)} FROM awards_slim WHERE action_date BETWEEN :start_date AND :end_date"
# Add condition for period_of_performance_current_end_date
query += " AND period_of_performance_current_end_date >= :start_date"
query += " AND period_of_performance_current_end_date IS NOT NULL"
params = {"start_date": start_date_str, "end_date": end_date_str}

if selected_agency != "All":
    query += " AND UPPER(parent_award_agency_name) = :agency"
    params["agency"] = str(selected_agency).upper()
if selected_funding_sub_agency not in ["All", None]:
    query += " AND UPPER(funding_sub_agency_name) = :funding_sub_agency"
    params["funding_sub_agency"] = str(selected_funding_sub_agency).upper()
if selected_funding_office not in ["All", None]:
    query += " AND UPPER(funding_office_name) = :funding_office"
    params["funding_office"] = str(selected_funding_office).upper()
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
if selected_extent_competeds:
    extent_competeds_tuple = tuple(str(val).upper() for val in selected_extent_competeds)
    placeholders = ', '.join([f":extent_competed_{i}" for i in range(len(extent_competeds_tuple))])
    query += f" AND UPPER(extent_competed) IN ({placeholders})"
    for i, val in enumerate(extent_competeds_tuple):
        params[f"extent_competed_{i}"] = val
if selected_set_aside not in ["All", None]:
    query += " AND UPPER(type_of_set_aside) = :set_aside"
    params["set_aside"] = str(selected_set_aside).upper()

# Display results with a spinner
if st.button("Run Query"):
    with st.spinner("Running query..."):
        try:
            # Load data using cached function
            df = load_data(query, params)
            
            # Convert only necessary columns to numeric
            monetary_columns_to_convert = ['federal_action_obligation', 'total_dollars_obligated', 'potential_total_value_of_award']
            for col in monetary_columns_to_convert:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # Convert period_of_performance_current_end_date to datetime
            df['period_of_performance_current_end_date'] = pd.to_datetime(df['period_of_performance_current_end_date'], errors='coerce')
            
            # Diagnostic: Check the filtered data
            st.write(f"Number of rows in filtered DataFrame: {len(df)}")
            total_obligated = df['total_dollars_obligated'].sum()
            if pd.isna(total_obligated):
                st.write("Total Dollars Obligated in filtered DataFrame: $0.00 (No valid numeric data)")
            else:
                st.write(f"Total Dollars Obligated in filtered DataFrame: ${total_obligated:,.2f}")
            
            # Diagnostic: Check the range of period_of_performance_current_end_date
            min_end_date = df['period_of_performance_current_end_date'].min()
            max_end_date = df['period_of_performance_current_end_date'].max()
            st.write(f"Range of Period of Performance Current End Date in filtered DataFrame: {min_end_date} to {max_end_date}")
            
            # Clean up NAICS codes in the DataFrame: ensure they are trimmed to a maximum of 6 characters
            df['naics_code'] = df['naics_code'].astype(str).str.replace(r'\.0$', '', regex=True).str.slice(0, 6)
            
            # Rename columns for display
            df_display = df.rename(columns=column_mapping)
            
            # Sort by federal_action_obligation (Contract Award Amount) in descending order
            df_display = df_display.sort_values(by="Contract Award Amount", ascending=False)
            
            # Limit to top 50 rows before styling
            df_display_limited = df_display.head(50)
            
            # Format monetary columns as currency
            format_dict = {col: "${:,.2f}" for col in [column_mapping[col] for col in monetary_columns_to_convert]}
            styled_df = df_display_limited.style.format(format_dict)
            
            # Display the styled DataFrame (limited to top 50 rows)
            st.subheader("Query Results (Top 50 Rows)")
            st.dataframe(styled_df, use_container_width=True)
            st.markdown("*Note: Only the top 50 rows are displayed. Download the full results using the button above.*")
            
            # Provide a download button for the full dataset
            csv = df_display.to_csv(index=False)
            st.download_button(
                label="Download Full Results as CSV",
                data=csv,
                file_name="usaspending_query_results.csv",
                mime="text/csv",
            )
            
            # Precompute fiscal year and quarter for visualizations
            df['action_date'] = pd.to_datetime(df['action_date'])
            fiscal_years, fiscal_quarters = calculate_fiscal_year_quarter(df['action_date'])
            df['fiscal_year'] = fiscal_years
            df['fiscal_quarter'] = fiscal_quarters
            df['year_quarter'] = df.apply(lambda x: f"FY{x['fiscal_year']} Q{x['fiscal_quarter']}", axis=1)
            
            # Generate all fiscal quarters between start and end dates
            all_quarters = generate_fiscal_quarters(start_date, end_date)
            
            # Group by fiscal quarter and calculate total spending and number of award actions
            quarterly_spending = df.groupby('year_quarter')['federal_action_obligation'].sum().reset_index()
            quarterly_awards = df[df['modification_number'] == '0'].groupby('year_quarter').size().reset_index(name='award_count')

            # Create a DataFrame with all quarters and merge with spending and award count data
            quarterly_df = pd.DataFrame({'year_quarter': all_quarters})
            quarterly_df = quarterly_df.merge(quarterly_spending, on='year_quarter', how='left')
            quarterly_df = quarterly_df.merge(quarterly_awards, on='year_quarter', how='left')
            quarterly_df['federal_action_obligation'] = quarterly_df['federal_action_obligation'].fillna(0)
            quarterly_df['award_count'] = quarterly_df['award_count'].fillna(0)

            # Extract fiscal year from year_quarter (e.g., "FY2023" from "FY2023 Q1")
            quarterly_df['fiscal_year'] = quarterly_df['year_quarter'].str.extract(r'(FY\d{4})')[0]

            # Calculate cumulative sums within each fiscal year
            quarterly_df['cumulative_spending'] = quarterly_df.groupby('fiscal_year')['federal_action_obligation'].cumsum()
            quarterly_df['cumulative_awards'] = quarterly_df.groupby('fiscal_year')['award_count'].cumsum()

            # Determine tick values for the right y-axis (Number of Award Actions) using cumulative awards
            max_cumulative_awards = quarterly_df['cumulative_awards'].max()
            num_ticks = 5
            award_step = max_cumulative_awards / (num_ticks - 1) if max_cumulative_awards > 0 else 1
            award_ticks = [i * award_step for i in range(num_ticks)]

            # Create two columns for the Spending visual and Expiring Contracts DataFrame
            col1, col2 = st.columns([1, 1])  # Equal width columns

            # Left column: Spending and Award Actions by Quarter
            with col1:
                st.subheader("Spending and Award Actions by Quarter")
                fig = go.Figure()
                # Add Cumulative Spending trace (bottom layer)
                fig.add_trace(go.Scatter(
                    x=quarterly_df['year_quarter'],
                    y=quarterly_df['cumulative_spending'],
                    name="Cumulative Spending ($)",
                    line=dict(color='#00FFFF')  # Bright cyan
                ))
                # Add Cumulative Award Actions trace (top layer)
                fig.add_trace(go.Scatter(
                    x=quarterly_df['year_quarter'],
                    y=quarterly_df['cumulative_awards'],
                    name="Cumulative Award Actions",
                    line=dict(color='#FFFF00'),  # Bright yellow
                    yaxis="y2"
                ))
                fig.update_layout(
                    title="Spending and Award Actions by Quarter (Cumulative Within Fiscal Year)",
                    xaxis=dict(title="Fiscal Quarter"),
                    yaxis=dict(
                        title="Cumulative Spending ($)",
                        title_font=dict(color="#00FFFF", size=14),
                        tickfont=dict(color="#00FFFF", size=12),
                        gridcolor="lightgrey",
                        range=[0, quarterly_df['cumulative_spending'].max() * 1.1]
                    ),
                    yaxis2=dict(
                        title="Cumulative Award Actions",
                        title_font=dict(color="#FFFF00", size=14),
                        tickfont=dict(color="#FFFF00", size=12),
                        overlaying="y",
                        side="right",
                        showgrid=False,
                        range=[0, max_cumulative_awards * 1.1],
                        tickvals=award_ticks,
                        ticktext=[f"{int(tick):,}" for tick in award_ticks]
                    ),
                    legend=dict(x=0, y=1.1, orientation="h")
                )
                st.plotly_chart(fig, use_container_width=True)

            # Right column: Contracts Expiring in the Next 24 Months
            with col2:
                st.subheader("Contracts Expiring in the Next 24 Months")
                # Define date range for expiring contracts
                today = pd.to_datetime("2025-04-14")  # Current date
                end_date_expiring = today + pd.DateOffset(months=24)  # 24 months from today
                
                # Filter for base awards (modification_number = '0') and contracts expiring between today and 24 months from today
                expiring_contracts = df[
                    (df['modification_number'] == '0') &
                    (df['period_of_performance_current_end_date'] >= today) &
                    (df['period_of_performance_current_end_date'] <= end_date_expiring)
                ]
                
                # Select only the specified columns
                expiring_columns = [
                    "parent_award_id_piid", "award_id_piid", "modification_number",
                    "federal_action_obligation", "total_dollars_obligated", "potential_total_value_of_award",
                    "period_of_performance_current_end_date", "primary_place_of_performance_city_name",
                    "primary_place_of_performance_state_code", "prime_award_base_transaction_description",
                    "transaction_description", "naics_code", "naics_description", "product_or_service_code",
                    "product_or_service_code_description", "awarding_office_name", "funding_office_name",
                    "recipient_name", "recipient_uei", "recipient_parent_name", "recipient_parent_uei",
                    "solicitation_date", "solicitation_procedures", "extent_competed", "type_of_set_aside",
                    "fair_opportunity_limited_sources", "other_than_full_and_open_competition",
                    "number_of_offers_received", "subcontracting_plan", "government_furnished_property",
                    "type_of_contract_pricing", "usaspending_permalink"
                ]
                expiring_df = expiring_contracts[expiring_columns].copy()
                
                # Sort by total_dollars_obligated in descending order
                expiring_df = expiring_df.sort_values(by='total_dollars_obligated', ascending=False)
                
                # Rename columns for display
                expiring_df_display = expiring_df.rename(columns=column_mapping)
                
                # Format monetary columns
                expiring_monetary_columns = ["Contract Award Amount", "Total Obligated Amount", "Potential Contract Value"]
                format_dict = {col: "${:,.2f}" for col in expiring_monetary_columns}
                styled_expiring_df = expiring_df_display.style.format(format_dict)
                
                # Display the DataFrame
                st.dataframe(styled_expiring_df, use_container_width=True)
                
                # Provide a download button for the expiring contracts
                csv_expiring = expiring_df_display.to_csv(index=False)
                st.download_button(
                    label="Download Expiring Contracts as CSV",
                    data=csv_expiring,
                    file_name="expiring_contracts.csv",
                    mime="text/csv",
                )
            
            # Visualize Top Recipients by Total Awards Made (only base awards)
            top_recipients_awards = df[df['modification_number'] == '0'].groupby('recipient_name').size().reset_index(name='award_count')
            top_recipients_awards = top_recipients_awards.sort_values(by='award_count', ascending=False).head(20)
            num_recipients_awards = len(top_recipients_awards)
            st.subheader(f"Top {num_recipients_awards} Recipients by Total Awards Made")
            fig_recipients_awards = px.bar(
                top_recipients_awards,
                x='recipient_name',
                y='award_count',
                title=f"Top {num_recipients_awards} Recipients by Total Awards Made",
                labels={'recipient_name': 'Recipient Name', 'award_count': 'Number of Awards'},
                color='recipient_name',
                color_discrete_sequence=color_palette
            )
            fig_recipients_awards.update_layout(xaxis_tickangle=45, showlegend=False)
            st.plotly_chart(fig_recipients_awards)
            
            # Visualize Top Recipients by Total Dollars Obligated (include modifications)
            top_recipients_dollars = df.groupby('recipient_name')['total_dollars_obligated'].sum().reset_index()
            top_recipients_dollars = top_recipients_dollars.sort_values(by='total_dollars_obligated', ascending=False).head(20)
            num_recipients_dollars = len(top_recipients_dollars)
            st.subheader(f"Top {num_recipients_dollars} Recipients by Total Dollars Obligated")
            fig_recipients_dollars = px.bar(
                top_recipients_dollars,
                x='recipient_name',
                y='total_dollars_obligated',
                title=f"Top {num_recipients_dollars} Recipients by Total Dollars Obligated",
                labels={'recipient_name': 'Recipient Name', 'total_dollars_obligated': 'Total Dollars Obligated ($)'},
                color='recipient_name',
                color_discrete_sequence=color_palette
            )
            fig_recipients_dollars.update_layout(xaxis_tickangle=45, showlegend=False)
            st.plotly_chart(fig_recipients_dollars)
            
            # Only display NAICS visualizations if no specific NAICS code is selected
            if selected_naics in ["All", None]:
                # Visualize Top NAICS by Award Actions (only base awards)
                top_naics_awards = df[df['modification_number'] == '0'].groupby('naics_code').size().reset_index(name='award_count')
                top_naics_awards = top_naics_awards.sort_values(by='award_count', ascending=False).head(20)
                num_naics_awards = len(top_naics_awards)
                st.subheader(f"Top {num_naics_awards} NAICS by Award Actions")
                fig_naics_awards = px.bar(
                    top_naics_awards,
                    x='naics_code',
                    y='award_count',
                    title=f"Top {num_naics_awards} NAICS by Award Actions",
                    labels={'naics_code': 'NAICS Code', 'award_count': 'Number of Awards'},
                    color='naics_code',
                    color_discrete_sequence=color_palette
                )
                fig_naics_awards.update_layout(xaxis_tickangle=45, xaxis_type='category', showlegend=False)
                st.plotly_chart(fig_naics_awards)

                # Visualize Top NAICS by Total Dollars Obligated (include modifications)
                top_naics_dollars = df.groupby('naics_code')['total_dollars_obligated'].sum().reset_index()
                top_naics_dollars = top_naics_dollars.sort_values(by='total_dollars_obligated', ascending=False).head(20)
                num_naics_dollars = len(top_naics_dollars)
                st.subheader(f"Top {num_naics_dollars} NAICS by Total Dollars Obligated")
                fig_naics_dollars = px.bar(
                    top_naics_dollars,
                    x='naics_code',
                    y='total_dollars_obligated',
                    title=f"Top {num_naics_dollars} NAICS by Total Dollars Obligated",
                    labels={'naics_code': 'NAICS Code', 'total_dollars_obligated': 'Total Dollars Obligated ($)'},
                    color='naics_code',
                    color_discrete_sequence=color_palette
                )
                fig_naics_dollars.update_layout(xaxis_tickangle=45, xaxis_type='category', showlegend=False)
                st.plotly_chart(fig_naics_dollars)
            
            # Visualize Top Agencies, Sub-Agencies, or Offices based on the lowest level of selection
            if selected_funding_office not in ["All", None]:
                pass  # Skip visuals if a funding office is selected
            elif selected_funding_sub_agency not in ["All", None]:
                # Sub-agency selected: Show Top Funding Offices
                top_offices_awards = df[df['modification_number'] == '0'].groupby('funding_office_name').size().reset_index(name='award_count')
                top_offices_awards = top_offices_awards.sort_values(by='award_count', ascending=False).head(20)
                num_offices_awards = len(top_offices_awards)
                st.subheader(f"Top {num_offices_awards} Funding Offices by Award Actions")
                fig_offices_awards = px.bar(
                    top_offices_awards,
                    x='funding_office_name',
                    y='award_count',
                    title=f"Top {num_offices_awards} Funding Offices by Award Actions",
                    labels={'funding_office_name': 'Funding Office Name', 'award_count': 'Number of Awards'},
                    color='funding_office_name',
                    color_discrete_sequence=color_palette
                )
                fig_offices_awards.update_layout(xaxis_tickangle=45, showlegend=False)
                st.plotly_chart(fig_offices_awards)

                top_offices_dollars = df.groupby('funding_office_name')['total_dollars_obligated'].sum().reset_index()
                top_offices_dollars = top_offices_dollars.sort_values(by='total_dollars_obligated', ascending=False).head(20)
                num_offices_dollars = len(top_offices_dollars)
                st.subheader(f"Top {num_offices_dollars} Funding Offices by Total Dollars Obligated")
                fig_offices_dollars = px.bar(
                    top_offices_dollars,
                    x='funding_office_name',
                    y='total_dollars_obligated',
                    title=f"Top {num_offices_dollars} Funding Offices by Total Dollars Obligated",
                    labels={'funding_office_name': 'Funding Office Name', 'total_dollars_obligated': 'Total Dollars Obligated ($)'},
                    color='funding_office_name',
                    color_discrete_sequence=color_palette
                )
                fig_offices_dollars.update_layout(xaxis_tickangle=45, showlegend=False)
                st.plotly_chart(fig_offices_dollars)
            elif selected_agency != "All":
                # Parent agency selected: Show Top Funding Sub-Agencies
                top_sub_agencies_awards = df[df['modification_number'] == '0'].groupby('funding_sub_agency_name').size().reset_index(name='award_count')
                top_sub_agencies_awards = top_sub_agencies_awards.sort_values(by='award_count', ascending=False).head(20)
                num_sub_agencies_awards = len(top_sub_agencies_awards)
                st.subheader(f"Top {num_sub_agencies_awards} Funding Sub-Agencies by Award Actions")
                fig_sub_agencies_awards = px.bar(
                    top_sub_agencies_awards,
                    x='funding_sub_agency_name',
                    y='award_count',
                    title=f"Top {num_sub_agencies_awards} Funding Sub-Agencies by Award Actions",
                    labels={'funding_sub_agency_name': 'Funding Sub-Agency Name', 'award_count': 'Number of Awards'},
                    color='funding_sub_agency_name',
                    color_discrete_sequence=color_palette
                )
                fig_sub_agencies_awards.update_layout(xaxis_tickangle=45, showlegend=False)
                st.plotly_chart(fig_sub_agencies_awards)

                top_sub_agencies_dollars = df.groupby('funding_sub_agency_name')['total_dollars_obligated'].sum().reset_index()
                top_sub_agencies_dollars = top_sub_agencies_dollars.sort_values(by='total_dollars_obligated', ascending=False).head(20)
                num_sub_agencies_dollars = len(top_sub_agencies_dollars)
                st.subheader(f"Top {num_sub_agencies_dollars} Funding Sub-Agencies by Total Dollars Obligated")
                fig_sub_agencies_dollars = px.bar(
                    top_sub_agencies_dollars,
                    x='funding_sub_agency_name',
                    y='total_dollars_obligated',
                    title=f"Top {num_sub_agencies_dollars} Funding Sub-Agencies by Total Dollars Obligated",
                    labels={'funding_sub_agency_name': 'Funding Sub-Agency Name', 'total_dollars_obligated': 'Total Dollars Obligated ($)'},
                    color='funding_sub_agency_name',
                    color_discrete_sequence=color_palette
                )
                fig_sub_agencies_dollars.update_layout(xaxis_tickangle=45, showlegend=False)
                st.plotly_chart(fig_sub_agencies_dollars)
            else:
                # No agency selected: Show Top Awarding Agencies
                top_agencies_awards = df[df['modification_number'] == '0'].groupby('parent_award_agency_name').size().reset_index(name='award_count')
                top_agencies_awards = top_agencies_awards.sort_values(by='award_count', ascending=False).head(20)
                num_agencies_awards = len(top_agencies_awards)
                st.subheader(f"Top {num_agencies_awards} Awarding Agencies by Award Actions")
                fig_agencies_awards = px.bar(
                    top_agencies_awards,
                    x='parent_award_agency_name',
                    y='award_count',
                    title=f"Top {num_agencies_awards} Awarding Agencies by Award Actions",
                    labels={'parent_award_agency_name': 'Awarding Agency Name', 'award_count': 'Number of Awards'},
                    color='parent_award_agency_name',
                    color_discrete_sequence=color_palette
                )
                fig_agencies_awards.update_layout(xaxis_tickangle=45, showlegend=False)
                st.plotly_chart(fig_agencies_awards)

                top_agencies_dollars = df.groupby('parent_award_agency_name')['total_dollars_obligated'].sum().reset_index()
                top_agencies_dollars = top_agencies_dollars.sort_values(by='total_dollars_obligated', ascending=False).head(20)
                num_agencies_dollars = len(top_agencies_dollars)
                st.subheader(f"Top {num_agencies_dollars} Awarding Agencies by Total Dollars Obligated")
                fig_agencies_dollars = px.bar(
                    top_agencies_dollars,
                    x='parent_award_agency_name',
                    y='total_dollars_obligated',
                    title=f"Top {num_agencies_dollars} Awarding Agencies by Total Dollars Obligated",
                    labels={'parent_award_agency_name': 'Awarding Agency Name', 'total_dollars_obligated': 'Total Dollars Obligated ($)'},
                    color='parent_award_agency_name',
                    color_discrete_sequence=color_palette
                )
                fig_agencies_dollars.update_layout(xaxis_tickangle=45, showlegend=False)
                st.plotly_chart(fig_agencies_dollars)
            
        except Exception as e:
            st.error(f"Error executing query: {str(e)}")

# Note about database optimization
st.markdown(
    """
    **Performance Note**: Indexes have been added to improve query performance. The following indexes were created:
    - idx_action_date
    - idx_period_of_performance_current_end_date
    - idx_parent_award_agency_name
    - idx_funding_sub_agency_name
    - idx_funding_office_name
    - idx_recipient_name
    - idx_naics_code
    - idx_product_or_service_code
    - idx_type_of_contract_pricing
    - idx_extent_competed
    - idx_type_of_set_aside
    - idx_modification_number
    """
)
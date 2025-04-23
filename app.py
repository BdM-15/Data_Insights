"""
Main entry point for the Data_Insights application.

This Streamlit application serves as the home page and dashboard for the 
USAspending.gov Data Explorer, with links to other pages in the application.
"""

import os
import sys
import streamlit as st
import pandas as pd
from datetime import datetime

# Add the project root to the path to ensure imports work correctly
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

# Import from project modules
from config import get_db_config, get_app_config
from src.backend.core.database import get_db_engine
from src.frontend.components.filters import display_sidebar_filters
from src.frontend.visualizations.charts import create_quarterly_spending_chart
from src.frontend.components.export import create_download_button

# Set page config (must be the first Streamlit command)
st.set_page_config(
    page_title="USAspending.gov Data Explorer",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Application title and description
st.title("USAspending.gov Data Explorer")
st.markdown("""
This dashboard provides insights into federal spending data from USAspending.gov, 
enabling business development teams to identify opportunities, analyze market trends, 
and support capture management activities.
""")

# Main dashboard content
st.header("Strategic Dashboard")

# Create tabs for different dashboard views
tab1, tab2, tab3 = st.tabs(["Overview", "Trends", "Opportunities"])

with tab1:
    st.subheader("Federal Contract Award Overview")
    
    # Get app configuration
    app_config = get_app_config()
    
    # Display data source info
    st.markdown(
        """
        <div style="background-color: #2E2E2E; padding: 10px; border-radius: 5px; border: 1px solid #555;">
            <p style="color: #FFFFFF; margin: 0;">Data Source: <strong>usaprime_cleaned</strong> (PostgreSQL)</p>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # Add a summary metrics section
    col1, col2, col3, col4 = st.columns(4)
    
    # These would normally be calculated from the database
    # Here we're using placeholder values
    with col1:
        st.metric(label="Total Contract Actions", value="1.2M")
    with col2:
        st.metric(label="Total Obligations", value="$125.7B")
    with col3:
        st.metric(label="Active Contracts", value="25,421")
    with col4:
        st.metric(label="Expiring in Next 12 Mo", value="4,890", delta="12%")
    
    # Display a placeholder for the quarterly spending chart
    st.markdown("### Quarterly Spending Trends")
    st.info("Use the filters in the sidebar and press 'Run Query' to view spending trends.")
    
    # Agency distribution placeholder
    st.markdown("### Top Awarding Agencies")
    st.info("Agency distribution will appear after running a query.")

with tab2:
    st.subheader("Spending Trends Analysis")
    st.markdown("""
    This tab will provide detailed trend analysis of federal spending over time, 
    including seasonal patterns, year-over-year comparisons, and forecasts.
    
    To view trend data, use the filters in the sidebar and click 'Run Query'.
    """)
    
    # Placeholder for a trend chart
    st.markdown("### Year-over-Year Comparison")
    st.info("Year-over-year comparison will appear after running a query.")

with tab3:
    st.subheader("Upcoming Opportunities")
    st.markdown("""
    This tab highlights contracts that are expiring in the next 6-24 months,
    helping you identify potential recompete opportunities.
    
    Contracts are ranked by total obligation amount to focus on high-value opportunities.
    """)
    
    # Placeholder for expiring contracts
    st.markdown("### Contracts Expiring in Next 6-24 Months")
    st.info("Expiring contracts will appear after running a query.")

# Sidebar information
with st.sidebar:
    st.header("Navigation")
    st.markdown("""
    **Pages:**
    - 📊 Home (current)
    - 🔍 Data Explorer
    - 📈 Visualizations
    - 🤖 AI Tools
    
    Use the filters below to customize your dashboard view.
    """)
    
    # Display filters section header
    st.header("Filters")
    st.markdown("Select filters and click 'Run Query' to update the dashboard.")
    
    # Placeholder for filters (would be implemented in src.frontend.components.filters)
    # ...

# Footer
st.markdown("---")
st.markdown("""
**Note**: This dashboard uses data from USAspending.gov and is optimized for PostgreSQL. 
For best performance, ensure your database has the appropriate indexes on frequently queried columns.
""")

"""
Chart generation functions for the Data_Insights application.

This module provides functions to create various visualizations for the application.
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import os
import sys

# Add the project root to the path to ensure imports work correctly
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../")))

# Import from project modules
from config import get_db_config
from src.backend.core.database import get_db_engine
from src.backend.core.utils import calculate_fiscal_year_quarter, format_currency

def create_quarterly_spending_chart(fiscal_quarters, spending_data):
    """
    Create a line chart showing quarterly spending trends.
    
    Args:
        fiscal_quarters: List of fiscal quarter labels
        spending_data: List of spending amounts corresponding to quarters
        
    Returns:
        Plotly figure object
    """
    # Create DataFrame for plotting
    df = pd.DataFrame({
        'Fiscal Quarter': fiscal_quarters,
        'Spending': spending_data
    })
    
    # Create line chart
    fig = px.line(
        df, 
        x='Fiscal Quarter', 
        y='Spending',
        markers=True,
        title='Quarterly Spending Trends',
        labels={'Spending': 'Obligations ($)'},
        template='plotly_white'
    )
    
    # Add a trend line (simple moving average)
    fig.add_trace(
        go.Scatter(
            x=df['Fiscal Quarter'],
            y=df['Spending'].rolling(window=4, min_periods=1).mean(),
            mode='lines',
            name='4-Quarter Moving Average',
            line=dict(color='red', dash='dot')
        )
    )
    
    # Update layout
    fig.update_layout(
        xaxis_title='Fiscal Quarter',
        yaxis_title='Obligations ($)',
        legend_title='',
        hovermode='x unified',
        height=500
    )
    
    # Update y-axis to use currency format
    fig.update_yaxes(tickprefix='$', tickformat=',.0f')
    
    return fig

def create_agency_distribution_chart(data):
    """
    Create a bar chart showing spending distribution by agency.
    
    Args:
        data: DataFrame with agency and spending amount data
        
    Returns:
        Plotly figure object
    """
    # Sort by spending amount in descending order
    data = data.sort_values('Amount', ascending=False)
    
    # Create bar chart
    fig = px.bar(
        data,
        x='Agency',
        y='Amount',
        title='Spending by Agency',
        text_auto='.2s',
        template='plotly_white'
    )
    
    # Update layout
    fig.update_layout(
        xaxis_title='Agency',
        yaxis_title='Total Obligations ($)',
        height=500
    )
    
    # Update y-axis to use currency format
    fig.update_yaxes(tickprefix='$', tickformat=',.0f')
    
    return fig

def create_expiring_contracts_chart(data):
    """
    Create a bar chart showing contracts expiring by month.
    
    Args:
        data: DataFrame with expiration dates and contract values
        
    Returns:
        Plotly figure object
    """
    # Group by month and sum contract values
    monthly_data = data.groupby(pd.Grouper(key='Expiration Date', freq='M')).sum().reset_index()
    
    # Create bar chart
    fig = px.bar(
        monthly_data,
        x='Expiration Date',
        y='Value',
        title='Contracts Expiring by Month',
        text_auto='.2s',
        template='plotly_white'
    )
    
    # Update layout
    fig.update_layout(
        xaxis_title='Month',
        yaxis_title='Contract Value ($)',
        height=500
    )
    
    # Update y-axis to use currency format
    fig.update_yaxes(tickprefix='$', tickformat=',.0f')
    
    return fig

"""
Export functionality components for the Data_Insights application.

This module provides functions to export data in various formats.
"""

import streamlit as st
import pandas as pd
import base64
import io

def create_download_button(df, button_text="Download CSV", file_name="data.csv"):
    """
    Create a download button for a DataFrame.
    
    Args:
        df: pandas DataFrame to export
        button_text: Text to display on the button
        file_name: Name of the file to download
        
    Returns:
        None
    """
    # Convert DataFrame to CSV
    csv = df.to_csv(index=False)
    
    # Create a download button
    st.download_button(
        label=button_text,
        data=csv,
        file_name=file_name,
        mime="text/csv"
    )
    
def export_to_excel(df, file_name="data.xlsx"):
    """
    Export DataFrame to Excel and provide a download link.
    
    Args:
        df: pandas DataFrame to export
        file_name: Name of the file to download
        
    Returns:
        Download link HTML
    """
    # Create a BytesIO buffer for Excel data
    output = io.BytesIO()
    
    # Write DataFrame to Excel
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Data')
        
    # Get the binary data and encode as base64
    excel_data = output.getvalue()
    b64 = base64.b64encode(excel_data).decode()
    
    # Create download link
    href = f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download="{file_name}">Download Excel file</a>'
    
    return href
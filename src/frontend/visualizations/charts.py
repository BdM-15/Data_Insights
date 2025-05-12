"""
Chart generation functions for the Data_Insights application.

This module provides functions to create various visualizations for the application,
focusing on contract spending trends, agency distributions, and expiration timelines.
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from typing import List, Dict, Any, Optional
import os
import sys
from datetime import datetime

# Add the project root to the path to ensure imports work correctly
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../")))

# Import from project modules
from config import get_db_config
from src.backend.core.database import get_db_engine
from src.backend.core.utils import calculate_fiscal_year_quarter, format_currency

def create_quarterly_spending_chart(
    fiscal_quarters: List[str], 
    spending_data: List[float],
    title: str = "Quarterly Spending Trends"
) -> go.Figure:
    """
    Create a line chart showing quarterly spending trends.
    
    Args:
        fiscal_quarters: List of fiscal quarter labels
        spending_data: List of spending amounts corresponding to quarters
        title: Chart title
        
    Returns:
        Plotly figure object with quarterly spending visualization
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
        title=title,
        labels={'Spending': 'Obligations ($)'}
    )
      # Apply custom theme settings with better overlay visibility
    fig.update_layout(
        plot_bgcolor='#051B30',
        paper_bgcolor='#051B30',
        font_color='#FFFFFF',
        title_font=dict(color='#FFFFFF', size=16),
        legend=dict(
            bgcolor='rgba(22, 45, 69, 0.8)',
            bordercolor='rgba(255, 255, 255, 0.2)',
            borderwidth=1
        ),
        modebar=dict(
            bgcolor='rgba(22, 45, 69, 0.8)',
            color='#FFFFFF'
        )
    )
    
    # Reason: Add a trend line using moving average to show overall trends
    # This helps identify whether spending is increasing or decreasing over time
    if len(spending_data) > 3:
        window_size = min(4, len(spending_data) - 1)  # Use appropriate window size
        fig.add_trace(
            go.Scatter(
                x=df['Fiscal Quarter'],
                y=df['Spending'].rolling(window=window_size, min_periods=1).mean(),
                mode='lines',
                name=f'{window_size}-Quarter Moving Average',
                line=dict(color='red', dash='dot')
            )
        )
    
    # Update layout for better readability
    fig.update_layout(
        xaxis_title='Fiscal Quarter',
        yaxis_title='Obligations ($)',
        legend_title='',
        hovermode='x unified',
        height=500,
        margin=dict(l=50, r=50, t=80, b=50)
    )
    
    # Update y-axis to use currency format
    fig.update_yaxes(tickprefix='$', tickformat=',.0f')
    
    return fig

def create_agency_distribution_chart(
    data: pd.DataFrame,
    limit: int = 10
) -> go.Figure:
    """
    Create a bar chart showing spending distribution by agency.
    
    Args:
        data: DataFrame with agency and spending amount data
        limit: Maximum number of agencies to display (top N by value)
        
    Returns:
        Plotly figure object with agency spending distribution
    """
    # Ensure we have the required columns
    if 'Agency' not in data.columns or 'Amount' not in data.columns:
        raise ValueError("Data must contain 'Agency' and 'Amount' columns")
    
    # Sort by spending amount in descending order and limit to top N
    data = data.sort_values('Amount', ascending=False).head(limit)
      # Create bar chart
    fig = px.bar(
        data,
        x='Agency',
        y='Amount',
        title=f'Top {limit} Agencies by Spending',
        text_auto='.2s'  # Automatically format text on bars
    )
      # Update layout for readability with better overlay visibility
    fig.update_layout(
        xaxis_title='Agency',
        yaxis_title='Total Obligations ($)',
        plot_bgcolor='#051B30',
        paper_bgcolor='#051B30',
        font_color='#FFFFFF',
        title_font=dict(color='#FFFFFF', size=16),
        legend=dict(
            bgcolor='rgba(22, 45, 69, 0.8)',
            bordercolor='rgba(255, 255, 255, 0.2)',
            borderwidth=1
        ),
        modebar=dict(
            bgcolor='rgba(22, 45, 69, 0.8)',
            color='#FFFFFF'
        )
    )
    
    # Rotate x-axis labels for better readability with long agency names
    fig.update_xaxes(tickangle=45)
    
    # Update y-axis to use currency format
    fig.update_yaxes(tickprefix='$', tickformat=',.0f')
    
    return fig

def create_expiring_contracts_chart(
    data: pd.DataFrame,
    date_column: str = 'Expiration Date',
    value_column: str = 'Value'
) -> go.Figure:
    """
    Create a bar chart showing contracts expiring by month.
    
    Args:
        data: DataFrame with expiration dates and contract values
        date_column: Name of column containing expiration dates
        value_column: Name of column containing contract values
        
    Returns:
        Plotly figure object with expiring contracts visualization
    """
    # Ensure date column is datetime
    if data[date_column].dtype != 'datetime64[ns]':
        data[date_column] = pd.to_datetime(data[date_column], errors='coerce')
    
    # Drop rows with NaT dates to prevent groupby errors
    data = data.dropna(subset=[date_column])
    
    # Group by month and sum contract values
    monthly_data = data.groupby(pd.Grouper(key=date_column, freq='M')).sum().reset_index()
      # Create bar chart
    fig = px.bar(
        monthly_data,
        x=date_column,
        y=value_column,
        title='Contracts Expiring by Month',
        text_auto='.2s'
    )
      # Update layout for readability with better overlay visibility
    fig.update_layout(
        xaxis_title='Month',
        yaxis_title='Contract Value ($)',
        plot_bgcolor='#051B30',
        paper_bgcolor='#051B30',
        font_color='#FFFFFF',
        title_font=dict(color='#FFFFFF', size=16),
        legend=dict(
            bgcolor='rgba(22, 45, 69, 0.8)',
            bordercolor='rgba(255, 255, 255, 0.2)',
            borderwidth=1
        ),
        modebar=dict(
            bgcolor='rgba(22, 45, 69, 0.8)',
            color='#FFFFFF'
        )
    )
    
    # Update y-axis to use currency format
    fig.update_yaxes(tickprefix='$', tickformat=',.0f')
    
    # Highlight the next 12 months
    today = pd.Timestamp.today()
    one_year_from_now = today + pd.DateOffset(months=12)
    
    # Add a rectangle highlighting the next 12 months if they exist in the data
    if (monthly_data[date_column].min() <= one_year_from_now and 
        monthly_data[date_column].max() >= today):
        fig.add_shape(
            type="rect",
            x0=today,
            y0=0,
            x1=one_year_from_now,
            y1=monthly_data[value_column].max() * 1.1,
            fillcolor="rgba(255, 230, 230, 0.3)",
            line=dict(width=0),
            layer="below"
        )
          # Add annotation for highlighted region with improved visibility
        fig.add_annotation(
            x=(today + (one_year_from_now - today) / 2),
            y=monthly_data[value_column].max() * 0.95,
            text="Next 12 Months",
            showarrow=False,
            font=dict(size=14, color="#FFFFFF"),
            bgcolor="rgba(22, 45, 69, 0.9)",
            bordercolor="rgba(255, 0, 0, 0.8)",
            borderwidth=2,
            borderpad=4
        )
    
    return fig

def fetch_quarterly_spending_data(
    filters: Dict[str, Any] = None
) -> tuple:
    """
    Fetch quarterly spending data from database.
    
    Args:
        filters: Dictionary of filters to apply to the query
        
    Returns:
        Tuple containing (fiscal_quarters, spending_data)
    """
    engine = get_db_engine()
    
    # Build query base
    query = """
    SELECT 
        fiscal_year, 
        fiscal_quarter, 
        SUM(federal_action_obligation) as total_spending
    FROM 
        usaprime_cleaned
    WHERE 
        federal_action_obligation IS NOT NULL
    """
    
    # Add filters if provided
    params = {}
    if filters:
        if filters.get('start_date') and filters.get('end_date'):
            query += " AND action_date BETWEEN :start_date AND :end_date"
            params['start_date'] = filters['start_date']
            params['end_date'] = filters['end_date']
            
        if filters.get('agency') and filters['agency'] != "All":
            query += " AND awarding_agency_name = :agency"
            params['agency'] = filters['agency']
            
        if filters.get('sub_agency') and filters['sub_agency'] != "All":
            query += " AND awarding_sub_agency_name = :sub_agency"
            params['sub_agency'] = filters['sub_agency']
            
        if filters.get('office') and filters['office'] != "All":
            query += " AND awarding_office_name = :office"
            params['office'] = filters['office']
            
        if filters.get('contractor') and filters['contractor'] != "All":
            query += " AND recipient_name = :contractor"
            params['contractor'] = filters['contractor']
            
        if filters.get('naics') and filters['naics'] != "All":
            query += " AND naics_code = :naics"
            params['naics'] = filters['naics']
            
        if filters.get('psc') and filters['psc'] != "All":
            query += " AND product_or_service_code = :psc"
            params['psc'] = filters['psc']
    
    # Group by fiscal year and quarter
    query += """
    GROUP BY 
        fiscal_year, fiscal_quarter
    ORDER BY 
        fiscal_year, fiscal_quarter
    """
    
    try:
        # Execute query
        from sqlalchemy import text
        with engine.connect() as conn:
            df = pd.read_sql(text(query), conn, params=params)
            
        if df.empty:
            return [], []
            
        # Format quarter labels and extract values
        quarters = [f"FY{row.fiscal_year} Q{row.fiscal_quarter}" for _, row in df.iterrows()]
        spending = df['total_spending'].tolist()
        
        return quarters, spending
    except Exception as e:
        st.error(f"Error fetching quarterly spending data: {str(e)}")
        return [], []
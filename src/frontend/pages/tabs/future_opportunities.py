"""
Future Opportunities tab for the Strategic Dashboard.

This module provides visualization functions for the Future Opportunities tab content.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from src.frontend.styles.theme import THEME
from src.backend.data.processors.awards import get_expiring_contracts_processor
from src.backend.data.models.data_models import ExpiringContract


def render_future_opportunities(df: pd.DataFrame):
    """
    Render the Future Opportunities tab content.
    
    Args:
        df: DataFrame containing award data filtered by NAICS code
    """
    st.header("Future Opportunities")
    
    expiring_contracts_data = get_expiring_contracts_processor(df)

    if not expiring_contracts_data:
        st.info("No expiring contracts found for the selected criteria.")
    else:
        st.subheader("Expiring Contracts (Next 6-24 Months)")
        
        # Convert Pydantic models to a DataFrame for easier manipulation and display
        expiring_contracts_df = pd.DataFrame([model.model_dump() for model in expiring_contracts_data])
        
        # Ensure 'period_of_performance_current_end_date' is datetime
        expiring_contracts_df['period_of_performance_current_end_date'] = pd.to_datetime(expiring_contracts_df['period_of_performance_current_end_date'])
        expiring_contracts_df['year_month'] = expiring_contracts_df['period_of_performance_current_end_date'].dt.to_period('M')

        # Display data in a table
        st.dataframe(
            expiring_contracts_df[[
                'contract_award_unique_key', 
                'recipient_name', 
                'period_of_performance_current_end_date', 
                'potential_total_value_of_award'
            ]].rename(columns={
                'contract_award_unique_key': "Contract Award Unique Key",
                'recipient_name': "Recipient Name",
                'period_of_performance_current_end_date': "End Date",
                'potential_total_value_of_award': "Potential Value"
            }), 
            use_container_width=True
        )

        # Create a timeline/bar chart of expiring contracts
        expiring_counts_by_month = expiring_contracts_df.groupby('year_month').size().reset_index(name='count')
        expiring_counts_by_month['year_month'] = expiring_counts_by_month['year_month'].astype(str) # Convert Period to string for Plotly

        if not expiring_counts_by_month.empty:
            fig = px.bar(
                expiring_counts_by_month, 
                x='year_month', 
                y='count', 
                title="Number of Contracts Expiring by Month",
                labels={'year_month': "Month", 'count': "Number of Expiring Contracts"}
            )
            fig.update_layout(**THEME)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Not enough data to display expiring contracts timeline.")

    st.info("Additional planned visualizations for SAM.gov, NATO NSPA, and Strategic Alignment Analysis will be implemented in a future phase.")
    
    # Placeholder for other planned visualizations
    st.markdown("""
    Further planned visualizations:
    - Strategic Alignment Analysis (Suitability vs. Synergy quadrant chart)
    - Active SAM.gov Opportunities with capability match scoring
    - NATO NSPA Opportunities with capability match scoring  
    - Strategic Connections between historical performance and future opportunities
    """)

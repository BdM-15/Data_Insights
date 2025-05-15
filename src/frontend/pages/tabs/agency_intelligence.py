"""
Agency Intelligence tab for the Strategic Dashboard.

This module provides visualization functions for the Agency Intelligence tab content.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from src.frontend.styles.theme import THEME
from src.backend.data.processors.agencies import get_top_agencies, get_agency_obligation_ratio
from src.backend.data.models.data_models import TopAgencyByCount, TopAgencyByObligation, AgencyRatioMetrics

def render_agency_intelligence(df: pd.DataFrame):
    """
    Render the Agency Intelligence tab content.
    
    Args:
        df: DataFrame containing award data filtered by NAICS code
    """
    st.header("Agency Intelligence")

    top_agencies_count_data = get_top_agencies(df, metric='count', n=10)
    top_agencies_obligation_data = get_top_agencies(df, metric='obligation', n=10)
    agency_ratio_metrics_data = get_agency_obligation_ratio(df)

    if not top_agencies_count_data and not top_agencies_obligation_data and not agency_ratio_metrics_data:
        st.info("No agency data available for the selected criteria.")
        return

    col1, col2 = st.columns(2)

    with col1:
        if top_agencies_count_data:
            st.subheader("Top 10 Agencies by Number of Awards")
            agencies_count_df = pd.DataFrame([model.model_dump() for model in top_agencies_count_data])
            fig_count = px.bar(
                agencies_count_df, 
                x='agency_name', 
                y='award_count', 
                title="Top Agencies by Award Count",
                labels={'agency_name': "Agency Name", 'award_count': "Number of Awards"}
            )
            fig_count.update_layout(**THEME)
            st.plotly_chart(fig_count, use_container_width=True)
            st.dataframe(agencies_count_df, use_container_width=True)
        else:
            st.info("No data for Top Agencies by Award Count.")

    with col2:
        if top_agencies_obligation_data:
            st.subheader("Top 10 Agencies by Total Obligation")
            agencies_obligation_df = pd.DataFrame([model.model_dump() for model in top_agencies_obligation_data])
            fig_obligation = px.bar(
                agencies_obligation_df, 
                x='agency_name', 
                y='total_obligation', 
                title="Top Agencies by Total Obligation",
                labels={'agency_name': "Agency Name", 'total_obligation': "Total Obligation ($)"}
            )
            fig_obligation.update_layout(**THEME)
            st.plotly_chart(fig_obligation, use_container_width=True)
            st.dataframe(agencies_obligation_df, use_container_width=True)
        else:
            st.info("No data for Top Agencies by Total Obligation.")

    if agency_ratio_metrics_data:
        st.subheader("Agency Competition and Win Rate Metrics")
        metrics_df = pd.DataFrame([model.model_dump() for model in agency_ratio_metrics_data])
        
        st.dataframe(metrics_df.rename(columns={
            'agency_name': 'Agency Name',
            'competition_rate': 'Competition Rate (%)',
            'win_rate': 'Win Rate (%)',
            'market_share_by_obligation': 'Market Share by Obligation (%)'
        }), use_container_width=True)
        
        if 'competition_rate' in metrics_df.columns:
            fig_comp_rate = px.bar(
                metrics_df.sort_values(by='competition_rate', ascending=False).head(15),
                x='agency_name',
                y='competition_rate',
                title='Agency Competition Rate',
                labels={'agency_name': 'Agency Name', 'competition_rate': 'Competition Rate (%)'}
            )
            fig_comp_rate.update_layout(**THEME)
            st.plotly_chart(fig_comp_rate, use_container_width=True)

        if 'win_rate' in metrics_df.columns and metrics_df['win_rate'].notna().any():
            fig_win_rate = px.bar(
                metrics_df.sort_values(by='win_rate', ascending=False).head(15),
                x='agency_name',
                y='win_rate',
                title='Agency Win Rate (Illustrative - if applicable)',
                labels={'agency_name': 'Agency Name', 'win_rate': 'Win Rate (%)'}
            )
            fig_win_rate.update_layout(**THEME)
            st.plotly_chart(fig_win_rate, use_container_width=True)
        elif 'win_rate' in metrics_df.columns:
            st.info("Win rate data is not available or not applicable for the selected agencies.")

    else:
        st.info("No Agency Ratio Metrics available.")

    st.markdown("--- ")
    st.info("Further planned visualizations for competitor-agency relationships, contract type success rates, and win rate analysis by vehicle type will be implemented based on refined data models and processor availability.")

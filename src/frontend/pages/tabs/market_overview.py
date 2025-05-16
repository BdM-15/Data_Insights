"""
Market Overview tab for the strategic dashboard.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import List

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))

from src.frontend.utils.formatting import format_value
from src.backend.data.processors.awards import (
    get_award_summary,
    get_top_agencies,
    get_quarterly_trends,
    get_agency_obligation_ratio,
    get_contract_vehicles,
    get_expiring_contracts,
    get_unique_naics_codes,
)
from src.backend.data.processors.competition import get_treemap_data
from src.backend.data.models.data_models import (
    AwardSummaryItem, TopAgencyByCount, TopAgencyByObligation, AgencyRatioMetrics, ContractVehicleSummary, TreemapPathElement
)
from src.frontend.styles.theme import THEME
from src.frontend.visualizations.charts.trend_charts import plot_quarterly_trends
from src.frontend.visualizations.charts.distribution_charts import plot_capture_intensity_scatter, plot_treemap_competitive_landscape
from src.frontend.visualizations.charts.comparison_charts import plot_contract_vehicle_pie, plot_top_agencies_bar, plot_top_agencies_obligation_bar
from src.frontend.visualizations.components.metric_cards import display_summary_metrics

def render_tab(df: pd.DataFrame):
    """
    Render the Market Overview tab content.

    Args:
        df: Filtered DataFrame for the dashboard
    """
    if not df.empty:
        # Executive Summary Metrics
        st.subheader("Executive Summary")
        summary: List[AwardSummaryItem] = get_award_summary(df)
        expiring_contracts = get_expiring_contracts(df, months_ahead=24)
        display_summary_metrics(summary, len(expiring_contracts), THEME)

        # Obligations and Award Actions Trend
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Obligations and Award Actions Trend")
            quarterly_data = get_quarterly_trends(df)
            if quarterly_data:
                qtr_df = pd.DataFrame([q.dict() for q in quarterly_data])
                fig = plot_quarterly_trends(qtr_df, THEME)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("Insufficient data for quarterly trends visualization.")
        with col2:
            st.subheader("Capture Intensity")
            agency_ratio: List[AgencyRatioMetrics] = get_agency_obligation_ratio(df)
            if agency_ratio and len(agency_ratio) > 1:
                agency_df = pd.DataFrame([a.dict() for a in agency_ratio])
                fig = plot_capture_intensity_scatter(agency_df, THEME)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("Insufficient data for agency ratio analysis.")

        # Contract Vehicle Distribution and Competitive Landscape
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Contract Vehicle Distribution")
            vehicle_data: List[ContractVehicleSummary] = get_contract_vehicles(df)
            if vehicle_data:
                vehicle_df = pd.DataFrame([v.dict() for v in vehicle_data])
                fig = plot_contract_vehicle_pie(vehicle_df, THEME)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("Insufficient data for contract vehicle analysis.")
        with col2:
            st.subheader("Competitive Landscape")
            treemap_data: List[TreemapPathElement] = get_treemap_data(df)
            if treemap_data:
                treemap_df = pd.DataFrame([t.dict() for t in treemap_data]).head(10)
                fig = plot_treemap_competitive_landscape(treemap_df, THEME)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("Insufficient data for competitive landscape analysis.")

        # Top Agencies Analysis
        st.subheader("Top Agencies Analysis")
        col1, col2 = st.columns(2)
        with col1:
            top_agencies_count: List[TopAgencyByCount] = get_top_agencies(df, metric="count", n=15)
            if top_agencies_count:
                count_df = pd.DataFrame([a.dict() for a in top_agencies_count])
                fig = plot_top_agencies_bar(count_df, value_col="award_count", label_col="parent_award_agency_name", theme=THEME, config={"title": "Top Agencies by Award Actions", "x_label": "Award Actions", "y_label": "Agency"})
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("Insufficient data for top agencies by award actions.")
        with col2:
            top_agencies_dollars: List[TopAgencyByObligation] = get_top_agencies(df, metric="obligation", n=15)
            if top_agencies_dollars:
                dollars_df = pd.DataFrame([a.dict() for a in top_agencies_dollars])
                fig = plot_top_agencies_obligation_bar(dollars_df, THEME)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("Insufficient data for top agencies by obligation amount.")
    else:
        st.warning("No data available. Please check the database connection details in the sidebar.")
        st.info("Possible issues:")
        st.markdown(
            """
            1. **Database Connection**: Verify PostgreSQL is running and connection details are correct
            2. **Table Names**: The table 'usaprime_cleaned' may not exist (sidebar will show available tables)
            3. **Data Availability**: There may be no data for NAICS code 561210 in the database
            4. **Date Range**: Try expanding the date range to capture more data
            See the Diagnostics section in the sidebar for more details.
            """
        )

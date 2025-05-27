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
from src.backend.data.app_processors.awards import (
    get_award_summary,
    get_top_agencies,
    get_quarterly_trends,
    get_agency_obligation_ratio,
    get_contract_vehicles,
    get_expiring_contracts,
    get_unique_naics_codes,
    # Import optimized functions for better performance
    get_award_summary_optimized,
    get_top_agencies_optimized, 
    get_quarterly_trends_optimized,
    get_agency_obligation_ratio_optimized,
    get_expiring_contracts_optimized
)
from src.backend.data.app_processors.competition import get_treemap_data
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
        # Executive Summary Metrics (SQL-based, filter-aware)
        st.subheader("Executive Summary")
        # Extract filters from DataFrame if possible (fallback to defaults)
        # Handle both pd.Timestamp and datetime.date for min/max
        def _to_str_date(val):
            if pd.isnull(val):
                return None
            if hasattr(val, 'date'):
                return str(val.date())
            return str(val)

        start_date = _to_str_date(df['action_date'].min()) if 'action_date' in df.columns and not df.empty else None
        end_date = _to_str_date(df['action_date'].max()) if 'action_date' in df.columns and not df.empty else None
        agency = df['parent_award_agency_name'].iloc[0] if 'parent_award_agency_name' in df.columns and len(df['parent_award_agency_name'].unique()) == 1 else None
        naics = df['naics_code'].iloc[0] if 'naics_code' in df.columns and len(df['naics_code'].unique()) == 1 else None        # Use optimized SQL-backed summary function for better performance
        summary = get_award_summary_optimized(
            naics_code=naics,
            start_date=start_date,
            end_date=end_date,
            agency=agency
        )
        expiring_contracts = get_expiring_contracts(df, months_ahead=24)
        from src.frontend.visualizations.components.metric_cards import metric_card
        st.markdown("""
            <div style='display: flex; justify-content: center; align-items: flex-end; width: 100%; margin-bottom: 0.5rem;'>
        """, unsafe_allow_html=True)
        col1, col2, col3, col4, col5, col6, col7 = st.columns(7)
        summary_dict = {item.category: item for item in summary}
        with col1:
            metric_card(
                label="Total Obligations",
                value=format_value(summary_dict['total_obligations'].value, is_currency=True)
            )
        with col2:
            metric_card(
                label="Total Award Actions",
                value=format_value(summary_dict['total_award_actions'].value)
            )
        with col3:
            metric_card(
                label="Average Award Value",
                value=format_value(summary_dict['avg_award_value'].value, is_currency=True)
            )
        with col4:
            metric_card(
                label="Active Contracts",
                value=format_value(summary_dict['active_contracts'].value)
            )
        with col5:
            metric_card(
                label="Expiring Contracts",
                value=format_value(len(expiring_contracts)),
                help_text="Number of contracts expiring in the next 6 to 24 months from today"
            )
        with col6:
            metric_card(
                label="Suitability",
                value="35%",
                help_text="The percentage of expiring contracts suitable for R&S based on comparing company capabilities to expiring contract descriptions"
            )
        with col7:
            metric_card(
                label="Synergy",
                value="55%",
                help_text="The percentage of expiring contracts suitable across MTS based on comparing company capabilities to expiring contract descriptions"
            )
        st.markdown("</div>", unsafe_allow_html=True)

        # Obligations and Award Actions Trend
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Obligations and Award Actions Trend")            
            quarterly_data = get_quarterly_trends_optimized(
                naics_code=naics,
                start_date=start_date,
                end_date=end_date,
                agency=agency
            )
            if quarterly_data:
                qtr_df = pd.DataFrame([q.dict() for q in quarterly_data])
                fig = plot_quarterly_trends(qtr_df, THEME)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("Insufficient data for quarterly trends visualization.")
        with col2:
            st.subheader("Capture Intensity")
            agency_ratio: List[AgencyRatioMetrics] = get_agency_obligation_ratio(
                naics_code=naics,
                start_date=start_date,
                end_date=end_date,
                agency=agency
            )
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
            # Use SQL-backed, filter-aware treemap data function
            treemap_data: List[TreemapPathElement] = get_treemap_data(
                naics_code=naics,
                start_date=start_date,
                end_date=end_date,
                agency=agency,
                limit=10
            )
            if treemap_data:
                treemap_df = pd.DataFrame([t.dict() for t in treemap_data])
                fig = plot_treemap_competitive_landscape(treemap_df, THEME)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("Insufficient data for competitive landscape analysis.")

        # Top Agencies Analysis
        st.subheader("Top Agencies Analysis")
        col1, col2 = st.columns(2)
        with col1:
            top_agencies_count: List[TopAgencyByCount] = get_top_agencies(
                naics_code=naics,
                start_date=start_date,
                end_date=end_date,
                agency=agency,
                metric="count",
                n=15
            )
            if top_agencies_count:
                count_df = pd.DataFrame([a.dict() for a in top_agencies_count])
                fig = plot_top_agencies_bar(count_df, value_col="award_count", label_col="parent_award_agency_name", theme=THEME, config={"title": "Top Agencies by Award Actions", "x_label": "Award Actions", "y_label": "Agency"})
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("Insufficient data for top agencies by award actions.")
        with col2:
            top_agencies_dollars: List[TopAgencyByObligation] = get_top_agencies(
                naics_code=naics,
                start_date=start_date,
                end_date=end_date,
                agency=agency,
                metric="obligation",
                n=15
            )
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

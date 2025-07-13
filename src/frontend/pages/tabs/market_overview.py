"""
Market Overview tab for the strategic dashboard.
"""


import streamlit as st
import pandas as pd
import numpy as np
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
    get_expiring_contracts,
    get_unique_naics_codes,
    # Import optimized functions for better performance
    get_award_summary_optimized,
    get_top_agencies_optimized, 
    get_quarterly_trends_optimized,
    get_agency_obligation_ratio_optimized,
    get_expiring_contracts_optimized,
    get_five_year_projection
)
from src.backend.data.app_processors.competition import get_treemap_data
from src.backend.data.models.data_models import (
    AwardSummaryItem, TopAgencyByCount, TopAgencyByObligation, AgencyRatioMetrics, ContractVehicleSummary, TreemapPathElement, ProjectionTrend
)
from src.frontend.styles.theme import THEME
from src.frontend.visualizations.charts.trend_charts import plot_quarterly_trends, plot_five_year_projection
from src.frontend.visualizations.charts.distribution_charts import plot_capture_intensity_scatter, plot_sankey_competitive_landscape
from src.frontend.visualizations.charts.comparison_charts import plot_top_agencies_bar, plot_top_agencies_obligation_bar
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
                value="9%",
                help_text="The percentage of expiring contracts suitable for R&S based on comparing company capabilities to expiring contract descriptions"
            )
        with col7:
            metric_card(
                label="Synergy",
                value="14%",
                help_text="The percentage of expiring contracts suitable across MTS based on comparing company capabilities to expiring contract descriptions"
            )
        st.markdown("</div>", unsafe_allow_html=True)

        # Obligations and Award Actions Trend (Row 1)
        col1, col2 = st.columns([2, 2])
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
            st.subheader("5-Year Projection")
            projection_data = get_five_year_projection(
                naics_code=naics,
                start_date=start_date,
                end_date=end_date,
                agency=agency,
                suitability_percentage=9.0  # From metric card
            )
            if projection_data:
                projection_df = pd.DataFrame([p.dict() for p in projection_data])
                fig = plot_five_year_projection(projection_df, THEME)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No projection data available. This could be due to insufficient expiring contracts in the next 5 years.")

        # Capture Intensity Row (New Row)
        st.markdown("<hr style='margin: 1.5rem 0;'>", unsafe_allow_html=True)
        col1, col2 = st.columns([2, 2])
        with col1:
            st.subheader("Capture Intensity")
            agency_ratio: List[AgencyRatioMetrics] = get_agency_obligation_ratio(
                naics_code=naics,
                start_date=start_date,
                end_date=end_date,
                agency=agency
            )
            agency_df = None
            if agency_ratio and len(agency_ratio) > 1:
                agency_df = pd.DataFrame([a.dict() for a in agency_ratio])
                fig = plot_capture_intensity_scatter(agency_df, THEME)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("Insufficient data for agency ratio analysis.")
        with col2:
            st.subheader("Agencies Above the Line")
            if agency_ratio and len(agency_ratio) > 1:
                if agency_df is None:
                    agency_df = pd.DataFrame([a.dict() for a in agency_ratio])
                # Calculate medians
                median_count = agency_df["award_count_normalized"].median()
                median_obligation = agency_df["obligation_normalized"].median()
                # Percentile-based Intensity Score: average of percentiles for award count and obligation
                agency_df["ac_pct"] = agency_df["award_count_normalized"].rank(pct=True)
                agency_df["ob_pct"] = agency_df["obligation_normalized"].rank(pct=True)
                # Clean up any non-finite values in percentiles
                agency_df["ac_pct"] = agency_df["ac_pct"].replace([np.inf, -np.inf], 0).fillna(0)
                agency_df["ob_pct"] = agency_df["ob_pct"].replace([np.inf, -np.inf], 0).fillna(0)
                agency_df["Intensity"] = ((agency_df["ac_pct"] + agency_df["ob_pct"]) / 2 * 100)
                agency_df["Intensity"] = agency_df["Intensity"].replace([np.inf, -np.inf], 0).fillna(0).round(0).astype(int)
                # Above the line mask
                above_mask = (agency_df["award_count_normalized"] > median_count) & (agency_df["obligation_normalized"] > median_obligation)
                # Agencies above both medians
                above_df = agency_df[above_mask]
                if not above_df.empty:
                    # Sort by intensity, descending
                    above_df = above_df.sort_values("Intensity", ascending=False)
                    # Format obligations and avg award value as currency, no decimals
                    def fmt_currency(val):
                        return f"${val:,.0f}" if pd.notnull(val) else "-"
                    table_df = above_df[["Intensity", "parent_award_agency_name", "award_count", "federal_action_obligation", "avg_award_value"]].rename(columns={
                        "parent_award_agency_name": "Agency",
                        "award_count": "Award Actions",
                        "federal_action_obligation": "Obligations",
                        "avg_award_value": "Avg Award Value"
                    })
                    table_df["Obligations"] = table_df["Obligations"].apply(fmt_currency)
                    table_df["Avg Award Value"] = table_df["Avg Award Value"].apply(fmt_currency)
                    st.dataframe(
                        table_df,
                        use_container_width=True,
                        height=450,
                        hide_index=True
                    )
                    # Intensity Score explanation:
                    # The Intensity Score is a percentile-based metric (0–100) that reflects how active an agency is in both award actions and total obligations, relative to its peers.
                    # A higher score means the agency is above more of its peers in both contract volume and spending. Agencies with high Intensity Scores are strong candidates for focused capture efforts.
                else:
                    st.info("No agencies above the median for both award actions and obligations.")
            else:
                st.info("Agency data not available for table.")        # Follow the Action Analysis (Full Width Row)
        st.markdown("<hr style='margin: 1.5rem 0;'>", unsafe_allow_html=True)
        st.subheader("Follow the Action")
        
        # Get treemap data for the sankey visualization
        treemap_data: List[TreemapPathElement] = get_treemap_data(
            naics_code=naics,
            start_date=start_date,
            end_date=end_date,
            agency=agency,
            limit=10
        )
        
        if treemap_data:
            treemap_df = pd.DataFrame([t.dict() for t in treemap_data])
            fig = plot_sankey_competitive_landscape(treemap_df, THEME, config={"title": "Follow the Action: Companies → Agencies → Contracts"})
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("Insufficient data for contract flow analysis.")

        # (AI Chatbot removed: see standalone AI Chat page)
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

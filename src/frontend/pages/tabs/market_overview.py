"""
Market Overview tab for the strategic dashboard.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

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
from src.frontend.styles.theme import THEME


def render_tab(df: pd.DataFrame):
    """
    Render the Market Overview tab content.

    Args:
        df: Filtered DataFrame for the dashboard
    """
    # Check if data is available
    if not df.empty:
        # Executive Summary Metrics
        st.subheader("Executive Summary")
        col1, col2, col3, col4, col5, col6, col7 = st.columns(7)
        with col1:
            st.metric("Total Obligations", format_value(get_award_summary(df)['total_obligations'], is_currency=True))
        with col2:
            st.metric("Total Award Actions", format_value(get_award_summary(df)['total_award_actions']))
        with col3:
            st.metric("Average Award Value", format_value(get_award_summary(df)['avg_award_value'], is_currency=True))
        with col4:
            st.metric("Active Contracts", format_value(get_award_summary(df)['active_contracts']))
        with col5:
            expiring_contracts = get_expiring_contracts(df, months_ahead=24)
            st.metric(
                "Expiring Contracts",
                format_value(expiring_contracts),
                help="Number of contracts expiring in the next 6 to 24 months from today"
            )
        with col6:
            st.metric(
                "Suitability",
                "35%",
                help="The percentage of expiring contracts suitable for R&S based on comparing company capabilities to expiring contract descriptions"
            )
        with col7:
            st.metric(
                "Synergy",
                "55%",
                help="The percentage of expiring contracts suitable across MTS based on comparing company capabilities to expiring contract descriptions"
            )

        # Obligations and Award Actions Trend
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Obligations and Award Actions Trend")
            quarterly_data = get_quarterly_trends(df)
            if not quarterly_data.empty:
                fig = make_subplots(specs=[[{"secondary_y": True}]])
                fig.add_trace(
                    go.Scatter(
                        x=quarterly_data["fiscal_period"],
                        y=quarterly_data["federal_action_obligation"],
                        name="Obligations",
                        line=dict(color=THEME["primary_color"], width=3),
                        mode="lines+markers",
                        marker=dict(size=8),
                        hovertemplate="<b>%{x}</b><br>Obligations: $%{y:,.0f}<extra></extra>"
                    ),
                    secondary_y=False
                )
                fig.add_trace(
                    go.Scatter(
                        x=quarterly_data["fiscal_period"],
                        y=quarterly_data["award_count"],
                        name="Award Actions",
                        line=dict(color=THEME["accent2_color"], width=3),
                        mode="lines+markers",
                        marker=dict(size=8),
                        hovertemplate="<b>%{x}</b><br>Award Actions: %{y:,.0f}<extra></extra>"
                    ),
                    secondary_y=True
                )
                fig.update_layout(
                    title="Quarterly Trends",
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                    plot_bgcolor=THEME["bg_color"],
                    paper_bgcolor=THEME["bg_color"],
                    font=dict(color=THEME["text_color"]),
                    margin=dict(l=40, r=40, t=40, b=40),
                )
                fig.update_xaxes(title_text="Fiscal Period", showgrid=True, gridcolor=THEME["grid_color"], tickangle=45)
                fig.update_yaxes(title_text="Obligations ($)", secondary_y=False, showgrid=True, gridcolor=THEME["grid_color"], tickprefix="$", tickformat=",.")
                fig.update_yaxes(title_text="Award Actions", secondary_y=True, showgrid=False)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("Insufficient data for quarterly trends visualization.")

        with col2:
            st.subheader("Capture Intensity")
            agency_ratio = get_agency_obligation_ratio(df)
            if not agency_ratio.empty and len(agency_ratio) > 1:
                median_count = agency_ratio["award_count_normalized"].median()
                median_obligation = agency_ratio["obligation_normalized"].median()
                fig = px.scatter(
                    agency_ratio,
                    x="award_count_normalized",
                    y="obligation_normalized",
                    size="scatter_size",
                    color="parent_award_agency_name",
                    hover_name="parent_award_agency_name",
                    hover_data={
                        "award_count_normalized": False,
                        "obligation_normalized": False,
                        "award_count_original": ":.0f",
                        "obligation_original": ":$.2s",
                        "avg_award_value": ":$.2s"
                    },
                    size_max=50,
                    title="Action-to-Obligation Ratio Analysis (Normalized Scale)",
                    labels={
                        "award_count_normalized": "Award Actions (log scale)",
                        "obligation_normalized": "Obligations (log scale)",
                        "avg_award_value": "Avg. Award Value"
                    }
                )
                fig.add_shape(
                    type="line",
                    x0=median_count,
                    y0=0,
                    x1=median_count,
                    y1=agency_ratio["obligation_normalized"].max() * 1.1,
                    line=dict(color="White", width=1, dash="dash")
                )
                fig.add_shape(
                    type="line",
                    x0=0,
                    y0=median_obligation,
                    x1=agency_ratio["award_count_normalized"].max() * 1.1,
                    y1=median_obligation,
                    line=dict(color="White", width=1, dash="dash")
                )
                fig.add_annotation(
                    x=median_count/2,
                    y=median_obligation*1.5,
                    text="High Value, Low Volume",
                    showarrow=False,
                    font=dict(color=THEME["highlight_color"])
                )
                fig.add_annotation(
                    x=median_count*1.5,
                    y=median_obligation*1.5,
                    text="High Value, High Volume",
                    showarrow=False,
                    font=dict(color=THEME["highlight_color"])
                )
                fig.update_layout(
                    plot_bgcolor=THEME["bg_color"],
                    paper_bgcolor=THEME["bg_color"],
                    font=dict(color=THEME["text_color"]),
                    margin=dict(l=40, r=40, t=40, b=40),
                    showlegend=False
                )
                fig.update_traces(
                    hovertemplate="<b>%{hovertext}</b><br>"
                                 "Award Actions: %{customdata[0]:,.0f}<br>"
                                 "Obligations: %{customdata[1]:$,.0f}<br>"
                                 "Avg Award: %{customdata[2]:$,.0f}"
                )
                fig.update_xaxes(showgrid=True, gridcolor=THEME["grid_color"], title_text="Award Actions (log scale)")
                fig.update_yaxes(showgrid=True, gridcolor=THEME["grid_color"], title_text="Obligations (log scale)")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("Insufficient data for agency ratio analysis.")

        # Contract Vehicle Distribution and Competitive Landscape
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Contract Vehicle Distribution")
            vehicle_data = get_contract_vehicles(df)
            if not vehicle_data.empty:
                fig = px.pie(
                    vehicle_data,
                    values="count",
                    names="award_type",
                    title="Contract Vehicle Types",
                    hole=0.4,
                    color_discrete_sequence=px.colors.sequential.Plasma
                )
                fig.update_layout(
                    plot_bgcolor=THEME["bg_color"],
                    paper_bgcolor=THEME["bg_color"],
                    font=dict(color=THEME["text_color"]),
                    margin=dict(l=40, r=40, t=40, b=40)
                )
                fig.update_traces(
                    textposition="inside",
                    textinfo="percent+label",
                    hoverinfo="label+percent+value"
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("Insufficient data for contract vehicle analysis.")

        with col2:
            st.subheader("Competitive Landscape")
            treemap_data = get_treemap_data(df)
            if not treemap_data.empty:
                top_competitors = treemap_data.head(10)
                fig = px.treemap(
                    top_competitors,
                    path=["recipient_parent_name", "recipient_name", "funding_sub_agency_name", "transaction_description"],
                    values="federal_action_obligation",
                    color="win_rate",
                    color_continuous_scale="Viridis",
                    title="Top Competitors by Market Share",
                    hover_data=["award_count", "market_share"],
                )
                fig.update_layout(
                    plot_bgcolor=THEME["bg_color"],
                    paper_bgcolor=THEME["bg_color"],
                    font=dict(color=THEME["text_color"]),
                    margin=dict(l=40, r=40, t=40, b=40)
                )
                fig.update_traces(
                    hovertemplate="<b>%{label}</b><br>Obligations: $%{value:,.2f}<br>Market Share: %{customdata[1]:.1f}%<br>Award Count: %{customdata[0]}<extra></extra>",
                    texttemplate="%{label}<br>%{customdata[1]:.1f}%",
                    textfont=dict(size=11)
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("Insufficient data for competitive landscape analysis.")

        # Top Agencies Analysis
        st.subheader("Top Agencies Analysis")
        col1, col2 = st.columns(2)
        with col1:
            top_agencies_count = get_top_agencies(df, metric="count", n=15)
            if not top_agencies_count.empty:
                fig = px.bar(
                    top_agencies_count,
                    x="award_count",
                    y="parent_award_agency_name",
                    title="Top Agencies by Award Actions",
                    orientation="h",
                    color="award_count",
                    color_continuous_scale="Blues",
                    labels={
                        "award_count": "Award Actions",
                        "parent_award_agency_name": "Agency"
                    }
                )
                fig.update_layout(
                    plot_bgcolor=THEME["bg_color"],
                    paper_bgcolor=THEME["bg_color"],
                    font=dict(color=THEME["text_color"]),
                    margin=dict(l=40, r=40, t=40, b=40),
                    coloraxis_showscale=False,
                    uniformtext_minsize=10,
                    uniformtext_mode='hide'
                )
                fig.update_xaxes(showgrid=True, gridcolor=THEME["grid_color"], tickformat=",.0f")
                fig.update_yaxes(showgrid=False, categoryorder="total ascending", title=None)
                fig.update_traces(texttemplate="%{x:,.0f}", textposition="outside", cliponaxis=False)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("Insufficient data for top agencies by award actions.")

        with col2:
            top_agencies_dollars = get_top_agencies(df, metric="obligation", n=15)
            if not top_agencies_dollars.empty:
                fig = px.bar(
                    top_agencies_dollars,
                    x="federal_action_obligation",
                    y="parent_award_agency_name",
                    title="Top Agencies by Obligation Amount",
                    orientation="h",
                    color="federal_action_obligation",
                    color_continuous_scale="Blues",
                    labels={
                        "federal_action_obligation": "Obligation Amount ($)",
                        "parent_award_agency_name": "Agency"
                    }
                )
                fig.update_layout(
                    plot_bgcolor=THEME["bg_color"],
                    paper_bgcolor=THEME["bg_color"],
                    font=dict(color=THEME["text_color"]),
                    margin=dict(l=40, r=40, t=40, b=40),
                    coloraxis_showscale=False,
                    uniformtext_minsize=10,
                    uniformtext_mode='hide'
                )
                fig.update_xaxes(showgrid=True, gridcolor=THEME["grid_color"], tickprefix="$", tickformat=",.0f")
                fig.update_yaxes(showgrid=False, categoryorder="total ascending", title=None)
                # Add formatted value annotations
                annotations = []
                for i, row in top_agencies_dollars.iterrows():
                    annotations.append({
                        'x': row['federal_action_obligation'],
                        'y': row['parent_award_agency_name'],
                        'text': format_value(row['federal_action_obligation'], is_currency=True),
                        'showarrow': False,
                        'xanchor': 'left',
                        'xshift': 5,
                        'font': {'color': 'white', 'size': 10}
                    })
                fig.update_layout(annotations=annotations)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("Insufficient data for top agencies by obligation amount.")

    # If no data is available, show helpful warnings
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

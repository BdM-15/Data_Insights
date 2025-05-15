"""
Market Overview tab for the Strategic Dashboard.

This module provides visualization functions for the Market Overview tab content.
"""

import streamlit as st
import pandas as pd
# import numpy as np # Not directly used in the visible snippet
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
# import plotly.io as pio # pio setup is done, but pio itself not directly used in render function

# Backend processors - aliased to avoid potential naming conflicts
from src.backend.data.processors.awards import (
    get_award_summary as get_award_summary_processor,
    get_quarterly_trends as get_quarterly_trends_processor,
    get_contract_vehicles as get_contract_vehicles_processor,
    get_expiring_contracts_processor  # Corrected import
)
from src.backend.data.processors.agencies import (
    get_top_agencies as get_top_agencies_processor,
    get_agency_obligation_ratio as get_agency_obligation_ratio_processor
)
from src.backend.data.processors.competition import (
    get_treemap_data as get_treemap_data_processor
)

# Utilities
from src.backend.core.utils import format_value

# Frontend styles
from src.frontend.styles.theme import THEME #, COLOR_SCALES, CHART_DEFAULTS

# Note: Plotly template setup (pio.templates.default) should ideally be done once globally (e.g., in app.py or strategic_dashboard.py).
# Assuming it's active from a higher level.

def render_market_overview(df: pd.DataFrame):
    """
    Render the Market Overview tab content.
    
    Args:
        df: DataFrame containing award data
    """
    if df.empty:
        st.error("No data available. Please check your filter settings or database connection.")
        return

    # Call backend processors to get Pydantic model lists
    summary_data_list = get_award_summary_processor(df)
    expiring_contracts_list = get_expiring_contracts_processor(df, months_ahead=24)
    quarterly_trends_list = get_quarterly_trends_processor(df)
    agency_ratio_list = get_agency_obligation_ratio_processor(df)
    contract_vehicles_list = get_contract_vehicles_processor(df)
    treemap_elements_list = get_treemap_data_processor(df)
    top_agencies_count_list = get_top_agencies_processor(df, metric="count", n=15)
    top_agencies_dollars_list = get_top_agencies_processor(df, metric="obligation", n=15)

    # --- Executive Summary KPIs ---
    st.subheader("Executive Summary")

    def get_summary_value(category: str, data_list: list, default_value=0.0) -> float:
        for item in data_list:
            if item.category == category:
                return item.value
        return default_value
    
    def get_summary_count(category: str, data_list: list, default_count=0) -> int:
        for item in data_list:
            if item.category == category:
                return item.count if item.count is not None else default_count
        return default_count

    total_obligations_val = get_summary_value("Total Obligations", summary_data_list)
    total_award_actions_val = get_summary_count("Total Award Actions", summary_data_list)
    avg_award_value_val = get_summary_value("Average Award Value", summary_data_list)
    active_contracts_val = get_summary_count("Active Contracts", summary_data_list)
    num_expiring_contracts = len(expiring_contracts_list)

    col1, col2, col3, col4, col5, col6, col7 = st.columns(7)
    with col1:
        st.metric("Total Obligations", format_value(total_obligations_val, is_currency=True))
    with col2:
        st.metric("Total Award Actions", format_value(total_award_actions_val))
    with col3:
        st.metric("Average Award Value", format_value(avg_award_value_val, is_currency=True))
    with col4:
        st.metric("Active Contracts", format_value(active_contracts_val))
    with col5:
        st.metric(
            "Expiring Contracts", 
            format_value(num_expiring_contracts),
            help="Number of contracts expiring in the next 6 to 24 months from today"
        )
    with col6: # Hardcoded
        st.metric("Suitability", "35%", help="...")
    with col7: # Hardcoded
        st.metric("Synergy", "42%", help="...")
    
    # --- Trends and analysis section ---
    col_trend_1, col_trend_2 = st.columns(2)
    
    with col_trend_1:
        st.subheader("Obligations and Award Actions Trend")
        if quarterly_trends_list:
            # Prepare data for Plotly
            fiscal_periods = [f"{item.year}-{item.quarter}" for item in quarterly_trends_list]
            obligations = [item.total_obligation for item in quarterly_trends_list]
            award_counts = [item.award_count for item in quarterly_trends_list]

            fig = make_subplots(specs=[[{"secondary_y": True}]])
            fig.add_trace(
                go.Scatter(
                    x=fiscal_periods, y=obligations, name="Obligations",
                    line=dict(color=THEME['primary_color'], width=4), mode='lines+markers',
                    marker=dict(size=8, color=THEME['primary_color'], line=dict(width=2, color='white')),
                    hovertemplate="<b>%{x}</b><br>Obligations: $%{y:,.2f}<extra></extra>"
                ), secondary_y=False,
            )
            fig.add_trace(
                go.Scatter(
                    x=fiscal_periods, y=award_counts, name="Award Actions",
                    line=dict(color=THEME['accent2_color'], width=4), mode='lines+markers',
                    marker=dict(size=8, color=THEME['accent2_color'], line=dict(width=2, color='white')),
                    hovertemplate="<b>%{x}</b><br>Award Actions: %{y:,.0f}<extra></extra>"
                ), secondary_y=True,
            )
            # ... (rest of fig.update_layout and fig.update_xaxes/yaxes from original) ...
            fig.update_layout(
                title="Quarterly Trends",
                plot_bgcolor=THEME["sidebar_bg"], paper_bgcolor=THEME["sidebar_bg"],
                font=dict(color=THEME["text_color"]),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                hovermode="x unified", margin=dict(l=40, r=40, t=40, b=40)
            )
            fig.update_xaxes(
                title_text="Fiscal Period", showgrid=True, gridcolor="rgba(255,255,255,0.2)",
                tickangle=45, title_font=dict(size=14, color=THEME["text_color"]),
                tickfont=dict(size=12, color=THEME["text_color"]),
                showline=True, linecolor="rgba(255,255,255,0.5)"
            )
            fig.update_yaxes(
                title_text="Obligations ($)", secondary_y=False, showgrid=True,
                gridcolor="rgba(255,255,255,0.2)", tickformat="$,.0f",
                title_font=dict(size=14, color=THEME["text_color"]),
                tickfont=dict(size=12, color=THEME["text_color"]),
                showline=True, linecolor="rgba(255,255,255,0.5)"
            )
            fig.update_yaxes(
                title_text="Award Actions", secondary_y=True, showgrid=False, tickformat=",d",
                title_font=dict(size=14, color=THEME["text_color"]),
                tickfont=dict(size=12, color=THEME["text_color"]),
                showline=True, linecolor="rgba(255,255,255,0.5)"
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("Insufficient data for trend analysis.")
    
    with col_trend_2:
        st.subheader("Capture Intensity")
        if agency_ratio_list and len(agency_ratio_list) > 1:
            agency_ratio_df = pd.DataFrame([model.model_dump() for model in agency_ratio_list])
            median_count = agency_ratio_df["award_count_normalized"].median()
            median_obligation = agency_ratio_df["obligation_normalized"].median()
            
            fig = px.scatter(
                agency_ratio_df, x="award_count_normalized", y="obligation_normalized",
                size="scatter_size", color="parent_award_agency_name",
                hover_name="parent_award_agency_name",
                hover_data={
                    "award_count_normalized": False, "obligation_normalized": False,
                    "award_count_original": ":.0f", "obligation_original": ":$.2s",
                    "avg_award_value": ":$.2s"
                },
                size_max=50, title="Action-to-Obligation Ratio Analysis (Normalized Scale)",
                labels={
                    "award_count_normalized": "Award Actions (log scale)",
                    "obligation_normalized": "Obligations (log scale)",
                    "avg_award_value": "Avg. Award Value"
                }
            )
            # ... (add_shape, add_annotation, update_layout, update_traces, update_xaxes/yaxes from original) ...
            fig.add_shape(type="line", x0=median_count, y0=0, x1=median_count, y1=agency_ratio_df["obligation_normalized"].max() * 1.1, line=dict(color="White", width=1, dash="dash"))
            fig.add_shape(type="line", x0=0, y0=median_obligation, x1=agency_ratio_df["award_count_normalized"].max() * 1.1, y1=median_obligation, line=dict(color="White", width=1, dash="dash"))
            fig.add_annotation(x=median_count/2, y=median_obligation*1.5, text="High Value, Low Volume", showarrow=False, font=dict(color=THEME["highlight_color"]))
            fig.add_annotation(x=median_count*1.5, y=median_obligation*1.5, text="High Value, High Volume", showarrow=False, font=dict(color=THEME["highlight_color"]))
            fig.update_layout(
                plot_bgcolor=THEME["sidebar_bg"], paper_bgcolor=THEME["sidebar_bg"], font=dict(color=THEME["text_color"]),
                margin=dict(l=40, r=40, t=40, b=40), showlegend=False, title_font=dict(size=16, color=THEME["text_color"]),
                hoverlabel=dict(bgcolor="rgba(50, 50, 50, 0.9)", font_size=14, font_color="white")
            )
            fig.update_traces(marker=dict(line=dict(width=1, color="white")), opacity=0.9)
            fig.update_traces(
                hovertemplate="<b>%{hovertext}</b><br>" +
                                "Award Actions: %{customdata[0]:,.0f}<br>" +
                                "Obligations: %{customdata[1]:$,.0f}<br>" +
                                "Avg Award: %{customdata[2]:$,.0f}"
            ) # Ensure customdata aligns if AgencyRatioMetrics model fields changed for hover_data
            fig.update_xaxes(showgrid=True, gridcolor=THEME["grid_color"], title_text="Award Actions (log scale)")
            fig.update_yaxes(showgrid=True, gridcolor=THEME["grid_color"], title_text="Obligations (log scale)")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("Insufficient data for agency ratio analysis.")
    
    # --- Second row for additional visualizations ---
    col_viz_1, col_viz_2 = st.columns(2)
    
    with col_viz_1:
        st.subheader("Contract Vehicle Distribution")
        if contract_vehicles_list:
            # ContractVehicleSummary has: contract_vehicle: str, award_count: int, percentage: float
            # For px.pie, we can pass the list of models directly if we map fields, or convert to DF
            cv_df = pd.DataFrame([model.model_dump() for model in contract_vehicles_list])
            if not cv_df.empty:
                fig = px.pie(
                    cv_df, values="award_count", names="contract_vehicle", # Changed from 'count' and 'award_type'
                    title="Contract Vehicle Types", hole=0.4,
                    color_discrete_sequence=px.colors.qualitative.Bold
                )
                # ... (update_layout, update_traces from original) ...
                fig.update_layout(
                    plot_bgcolor=THEME["sidebar_bg"], paper_bgcolor=THEME["sidebar_bg"], font=dict(color=THEME["text_color"]),
                    margin=dict(l=40, r=40, t=40, b=40), title_font=dict(size=16, color=THEME["text_color"])
                )
                fig.update_traces(
                    textposition="inside", textinfo="percent+label", hoverinfo="label+percent+value",
                    textfont=dict(size=14, color="white", family="Arial"),
                    marker=dict(line=dict(color='rgba(0, 0, 0, 0.5)', width=1.5)),
                    insidetextorientation='radial'
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("No contract vehicle data to display.")
        else:
            st.warning("Insufficient data for contract vehicle analysis.")
            
    with col_viz_2:
        st.subheader("Competitive Landscape")
        if treemap_elements_list:
            treemap_df = pd.DataFrame([model.model_dump() for model in treemap_elements_list])
            if not treemap_df.empty:
                # Original code used .head(10) - assuming this meant top 10 by federal_action_obligation
                # This logic should ideally be in the backend processor or clearly defined here.
                # For now, let's sort and take top 10 as an example if that was the intent.
                # If the processor already provides data suitable for direct use, this can be simpler.
                # top_competitors_df = treemap_df.sort_values("federal_action_obligation", ascending=False).head(10)
                # Using the full treemap_df for now, as "top 10" logic wasn't fully clear from original snippet for treemap.
                
                fig = px.treemap(
                    treemap_df, # Use treemap_df or top_competitors_df
                    path=["recipient_parent_name", "recipient_name", "funding_sub_agency_name", "transaction_description"],
                    values="federal_action_obligation", color="win_rate",
                    color_continuous_scale="Viridis", title="Top Competitors by Market Share",
                    hover_data=["award_count", "market_share"], # These are Optional in Pydantic model
                    branchvalues="total",
                )
                # ... (update_layout, update_traces from original) ...
                # Ensure customdata in update_traces aligns with hover_data if used explicitly.
                # Plotly express usually handles hover_data well.
                fig.update_layout(
                    plot_bgcolor=THEME["sidebar_bg"], paper_bgcolor=THEME["sidebar_bg"], font=dict(color=THEME["text_color"]),
                    margin=dict(l=40, r=40, t=40, b=40), title_font=dict(size=16, color=THEME["text_color"]),
                    coloraxis_colorbar=dict(title="Win Rate", title_side="top", tickmode="array", tickvals=[0, 0.25, 0.5, 0.75, 1], ticktext=["0%", "25%", "50%", "75%", "100%"], ticks="outside")
                )
                fig.update_traces(
                    hovertemplate="<b>%{label}</b><br>Obligations: $%{value:,.2f}<br>Market Share: %{customdata[1]:.1f}%<br>Award Count: %{customdata[0]}<extra></extra>",
                    texttemplate="%{label}<br>%{customdata[1]:.1f}%", # Check customdata indices
                    textfont=dict(size=12, color="#FFFFFF"),
                    marker=dict(line=dict(width=1, color="rgba(0,0,0,0.3)")),
                    root_color="rgba(0,0,0,0.2)"
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("No data for competitive landscape treemap.")
        else:
            st.warning("Insufficient data for competitive landscape analysis.")

    # --- Top Agencies Analysis ---
    st.subheader("Top Agencies Analysis")
    col_agencies_1, col_agencies_2 = st.columns(2)
    
    with col_agencies_1:
        # st.subheader("Top Agencies by Award Actions") # Already part of the main subheader
        if top_agencies_count_list:
            agencies_count_df = pd.DataFrame([model.model_dump() for model in top_agencies_count_list])
            if not agencies_count_df.empty:
                fig = px.bar(
                    agencies_count_df, x="award_count", y="parent_award_agency_name",
                    title="Top Agencies by Award Actions", orientation="h",
                    color="award_count", color_continuous_scale="dense",
                    labels={"award_count": "Award Actions", "parent_award_agency_name": "Agency"}
                )
                # ... (update_layout, update_xaxes, update_yaxes, update_traces from original) ...
                fig.update_layout(
                    plot_bgcolor=THEME["sidebar_bg"], paper_bgcolor=THEME["sidebar_bg"], font=dict(color=THEME["text_color"]),
                    margin=dict(l=40, r=40, t=40, b=40), coloraxis_showscale=False,
                    uniformtext_minsize=10, uniformtext_mode='hide', title_font=dict(size=16, color=THEME["text_color"])
                )
                fig.update_xaxes(
                    showgrid=True, gridcolor="rgba(255,255,255,0.2)", tickformat=",.0f",
                    title_font=dict(size=14, color=THEME["text_color"]), tickfont=dict(size=12, color=THEME["text_color"]),
                    showline=True, linecolor="rgba(255,255,255,0.5)"
                )
                fig.update_yaxes(
                    showgrid=False, categoryorder="total ascending", title=None,
                    tickfont=dict(size=12, color=THEME["text_color"]),
                    showline=True, linecolor="rgba(255,255,255,0.5)"
                )
                fig.update_traces(texttemplate="%{x:,.0f}", textposition="outside", cliponaxis=False)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("No data for top agencies by award actions.")
        else:
            st.warning("Insufficient data for top agencies by award actions.")
            
    with col_agencies_2:
        # st.subheader("Top Agencies by Obligation Amount") # Already part of the main subheader
        if top_agencies_dollars_list:
            agencies_dollars_df = pd.DataFrame([model.model_dump() for model in top_agencies_dollars_list])
            if not agencies_dollars_df.empty:
                fig = px.bar(
                    agencies_dollars_df, x="federal_action_obligation", y="parent_award_agency_name",
                    title="Top Agencies by Obligation Amount", orientation="h",
                    color="federal_action_obligation", color_continuous_scale="dense",
                    labels={"federal_action_obligation": "Obligation Amount ($)", "parent_award_agency_name": "Agency"}
                )
                # ... (update_layout, update_xaxes, update_yaxes from original) ...
                fig.update_layout(
                    plot_bgcolor=THEME["sidebar_bg"], paper_bgcolor=THEME["sidebar_bg"], font=dict(color=THEME["text_color"]),
                    margin=dict(l=40, r=40, t=40, b=40), coloraxis_showscale=False,
                    uniformtext_minsize=10, uniformtext_mode='hide', title_font=dict(size=16, color=THEME["text_color"])
                )
                fig.update_xaxes(showgrid=True, gridcolor=THEME["grid_color"], tickprefix="$", tickformat=",.0f")
                fig.update_yaxes(showgrid=False, categoryorder="total ascending", title=None)
                
                annotations = []
                for _, row in agencies_dollars_df.iterrows(): # Iterate over DataFrame rows
                    annotations.append({
                        'x': row['federal_action_obligation'],
                        'y': row['parent_award_agency_name'],
                        'text': format_value(row['federal_action_obligation'], is_currency=True),
                        'showarrow': False, 'xanchor': 'left', 'xshift': 5,
                        'font': {'color': 'white', 'size': 10}
                    })
                fig.update_layout(annotations=annotations)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("No data for top agencies by obligation amount.")
        else:
            st.warning("Insufficient data for top agencies by obligation amount.")
# ... (rest of the file, if any) ...

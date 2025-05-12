"""
Market Overview tab for the Strategic Dashboard.

This module provides visualization functions for the Market Overview tab content.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.io as pio

from src.frontend.styles.theme import THEME, COLOR_SCALES, CHART_DEFAULTS

# Configure default Plotly template for better visibility on dark backgrounds
pio.templates["custom_dark"] = pio.templates["plotly_dark"]
pio.templates["custom_dark"].layout.update(
    font=dict(color=THEME["text_color"]),
    plot_bgcolor=THEME["sidebar_bg"],
    paper_bgcolor=THEME["sidebar_bg"],
    xaxis=dict(
        gridcolor='rgba(255, 255, 255, 0.15)',
        zerolinecolor='rgba(255, 255, 255, 0.3)',
        showgrid=True
    ),
    yaxis=dict(
        gridcolor='rgba(255, 255, 255, 0.15)',
        zerolinecolor='rgba(255, 255, 255, 0.3)',
        showgrid=True
    ),
)
pio.templates.default = "custom_dark"


def render_market_overview(df):
    """
    Render the Market Overview tab content.
    
    Args:
        df: DataFrame containing award data
    """
    if not df.empty:
        from src.frontend.pages.strategic_dashboard import (
            get_award_summary, format_value, get_top_agencies, get_quarterly_trends, 
            get_expiring_contracts, get_agency_obligation_ratio as get_capture_intensity,
            get_contract_vehicles, get_treemap_data
        )
        
        summary = get_award_summary(df)
        
        # Calculate expiring contracts directly since it's not part of the summary
        expiring_contracts = get_expiring_contracts(df, months_ahead=24)
        
        # KPI metrics row
        st.subheader("Executive Summary")
        col1, col2, col3, col4, col5, col6, col7 = st.columns(7)
        
        with col1:
            st.metric("Total Obligations", format_value(summary['total_obligations'], is_currency=True))
        
        with col2:
            st.metric("Total Award Actions", format_value(summary['total_award_actions']))
        
        with col3:
            st.metric("Average Award Value", format_value(summary['avg_award_value'], is_currency=True))
        
        with col4:
            st.metric("Active Contracts", format_value(summary['active_contracts']))
        
        with col5:
            st.metric(
                "Expiring Contracts", 
                format_value(expiring_contracts),
                help="Number of contracts expiring in the next 6 to 24 months from today"
            )
        
        with col6:
            # Hardcoded suitability value since it's not calculated in get_award_summary
            st.metric(
                "Suitability", 
                "35%",
                help="The percentage of expiring contracts suitable for R&S based on comparing company capabilities to expiring contract descriptions"
            )
        
        with col7:
            # Hardcoded synergy value since it's not calculated in get_award_summary
            st.metric(
                "Synergy", 
                "42%",
                help="The percentage of market solutions that can be bundled with R&S services"
            )
        
        # Trends and analysis section - Use 2-column layout
        col1, col2 = st.columns(2)
        
        # Column 1: Obligations and Award Actions Trend
        with col1:
            st.subheader("Obligations and Award Actions Trend")
            
            # Get quarterly trends data
            quarterly_data = get_quarterly_trends(df)
            
            if not quarterly_data.empty:
                # Create the visualization with two y-axes
                fig = make_subplots(specs=[[{"secondary_y": True}]])
                
                # Add traces for obligations (primary y-axis)
                fig.add_trace(
                    go.Scatter(
                        x=quarterly_data['fiscal_period'],
                        y=quarterly_data['federal_action_obligation'],
                        name="Obligations",
                        line=dict(color=THEME['primary_color'], width=4),  # Increased width
                        mode='lines+markers',  # Added markers for better visibility
                        marker=dict(size=8, color=THEME['primary_color'], line=dict(width=2, color='white')),
                        hovertemplate="<b>%{x}</b><br>Obligations: $%{y:,.2f}<extra></extra>"
                    ),
                    secondary_y=False,
                )
                
                # Add traces for award counts (secondary y-axis)
                fig.add_trace(
                    go.Scatter(
                        x=quarterly_data['fiscal_period'],
                        y=quarterly_data['award_count'],
                        name="Award Actions",
                        line=dict(color=THEME['accent2_color'], width=4),  # Increased width
                        mode='lines+markers',  # Added markers for better visibility
                        marker=dict(size=8, color=THEME['accent2_color'], line=dict(width=2, color='white')),
                        hovertemplate="<b>%{x}</b><br>Award Actions: %{y:,.0f}<extra></extra>"
                    ),
                    secondary_y=True,
                )
                
                # Add titles and labels
                fig.update_layout(
                    title="Quarterly Trends",
                    plot_bgcolor=THEME["sidebar_bg"],
                    paper_bgcolor=THEME["sidebar_bg"],
                    font=dict(color=THEME["text_color"]),
                    legend=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=1.02,
                        xanchor="right",
                        x=1
                    ),
                    hovermode="x unified",
                    margin=dict(l=40, r=40, t=40, b=40)
                )
                
                # Update axes
                fig.update_xaxes(
                    title_text="Fiscal Period",
                    showgrid=True,
                    gridcolor="rgba(255,255,255,0.2)",  # Brighter grid lines
                    tickangle=45,
                    title_font=dict(size=14, color=THEME["text_color"]),
                    tickfont=dict(size=12, color=THEME["text_color"]),
                    showline=True,
                    linecolor="rgba(255,255,255,0.5)"
                )
                
                # Update y-axes
                fig.update_yaxes(
                    title_text="Obligations ($)",
                    secondary_y=False,
                    showgrid=True,
                    gridcolor="rgba(255,255,255,0.2)",  # Brighter grid lines
                    tickformat="$,.0f",
                    title_font=dict(size=14, color=THEME["text_color"]),
                    tickfont=dict(size=12, color=THEME["text_color"]),
                    showline=True,
                    linecolor="rgba(255,255,255,0.5)"
                )
                
                fig.update_yaxes(
                    title_text="Award Actions",
                    secondary_y=True,
                    showgrid=False,
                    tickformat=",d",
                    title_font=dict(size=14, color=THEME["text_color"]),
                    tickfont=dict(size=12, color=THEME["text_color"]),
                    showline=True,
                    linecolor="rgba(255,255,255,0.5)"
                )
                
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("Insufficient data for trend analysis.")
        
        # Column 2: Capture Intensity visualization
        with col2:
            # Capture Intensity (renamed and using normalized data)
            st.subheader("Capture Intensity")
            
            agency_ratio = get_capture_intensity(df)
            
            if not agency_ratio.empty and len(agency_ratio) > 1:  # Need at least 2 points for a meaningful scatter plot
                # Create quadrant thresholds using normalized values
                median_count = agency_ratio["award_count_normalized"].median()
                median_obligation = agency_ratio["obligation_normalized"].median()
                
                # Create scatter plot with normalized values
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
                
                # Add quadrant lines
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
                
                # Add quadrant labels
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
                
                # Update layout
                fig.update_layout(
                    plot_bgcolor=THEME["sidebar_bg"],
                    paper_bgcolor=THEME["sidebar_bg"],
                    font=dict(color=THEME["text_color"]),
                    margin=dict(l=40, r=40, t=40, b=40),
                    showlegend=False,
                    title_font=dict(size=16, color=THEME["text_color"]),
                    hoverlabel=dict(
                        bgcolor="rgba(50, 50, 50, 0.9)",
                        font_size=14,
                        font_color="white"
                    )
                )
                
                # Make scatter points more visible
                fig.update_traces(
                    marker=dict(
                        line=dict(width=1, color="white")
                    ),
                    opacity=0.9  # Slightly increase opacity for better visibility
                )
                
                # Update tooltip to show original values
                fig.update_traces(
                    hovertemplate="<b>%{hovertext}</b><br>" +
                                 "Award Actions: %{customdata[0]:,.0f}<br>" +
                                 "Obligations: %{customdata[1]:$,.0f}<br>" +
                                 "Avg Award: %{customdata[2]:$,.0f}"
                )
                
                # Update axes
                fig.update_xaxes(
                    showgrid=True,
                    gridcolor=THEME["grid_color"],
                    title_text="Award Actions (log scale)"
                )
                
                fig.update_yaxes(
                    showgrid=True,
                    gridcolor=THEME["grid_color"],
                    title_text="Obligations (log scale)"
                )
                
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("Insufficient data for agency ratio analysis.")
        
        # Second row for additional visualizations
        col1, col2 = st.columns(2)
        
        with col1:
            # Contract Vehicle Distribution
            st.subheader("Contract Vehicle Distribution")
            
            vehicle_data = get_contract_vehicles(df)
            
            if not vehicle_data.empty:
                fig = px.pie(
                    vehicle_data,
                    values="count",
                    names="award_type",
                    title="Contract Vehicle Types",
                    hole=0.4,
                    color_discrete_sequence=px.colors.qualitative.Bold  # Using a bolder color sequence for visibility
                )
                
                # Update layout
                fig.update_layout(
                    plot_bgcolor=THEME["sidebar_bg"],
                    paper_bgcolor=THEME["sidebar_bg"],
                    font=dict(color=THEME["text_color"]),
                    margin=dict(l=40, r=40, t=40, b=40),
                    title_font=dict(size=16, color=THEME["text_color"])
                )
                
                # Update traces
                fig.update_traces(
                    textposition="inside",
                    textinfo="percent+label",
                    hoverinfo="label+percent+value",
                    textfont=dict(size=14, color="white", family="Arial"),
                    marker=dict(line=dict(color='rgba(0, 0, 0, 0.5)', width=1.5)),  # Add thin dark borders
                    insidetextorientation='radial'  # Orient text for better readability
                )
                
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("Insufficient data for contract vehicle analysis.")
        
        with col2:
            # Competitive Landscape
            st.subheader("Competitive Landscape")
            
            # Use the new specialized treemap data function instead of get_competitive_landscape()
            treemap_data = get_treemap_data(df)
            
            if not treemap_data.empty:
                # Use only top 10 competitors
                top_competitors = treemap_data.head(10)
                fig = px.treemap(
                    top_competitors,
                    path=["recipient_parent_name", "recipient_name", "funding_sub_agency_name", "transaction_description"],
                    values="federal_action_obligation",
                    color="win_rate",
                    color_continuous_scale="Viridis",
                    title="Top Competitors by Market Share",
                    hover_data=["award_count", "market_share"],
                    branchvalues="total",  # Show values as percentage of total
                )
                
                # Update layout
                fig.update_layout(
                    plot_bgcolor=THEME["sidebar_bg"],
                    paper_bgcolor=THEME["sidebar_bg"],
                    font=dict(color=THEME["text_color"]),
                    margin=dict(l=40, r=40, t=40, b=40),
                    title_font=dict(size=16, color=THEME["text_color"]),
                    coloraxis_colorbar=dict(
                        title="Win Rate",
                        titleside="top",
                        tickmode="array",
                        tickvals=[0, 0.25, 0.5, 0.75, 1],
                        ticktext=["0%", "25%", "50%", "75%", "100%"],
                        ticks="outside"
                    )
                )
                
                # Update traces for better readability with abbreviated values
                fig.update_traces(
                    hovertemplate="<b>%{label}</b><br>Obligations: " + 
                                 "$%{value:,.2f}<br>" +
                                 "Market Share: %{customdata[1]:.1f}%<br>" +
                                 "Award Count: %{customdata[0]}<extra></extra>",
                    texttemplate="%{label}<br>%{customdata[1]:.1f}%",
                    textfont=dict(size=12, color="#FFFFFF"),
                    marker=dict(
                        line=dict(width=1, color="rgba(0,0,0,0.3)")
                    ),
                    root_color="rgba(0,0,0,0.2)"  # Darken the root node for better contrast
                )
                
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("Insufficient data for competitive landscape analysis.")
        
        # Top Agencies Analysis
        st.subheader("Top Agencies Analysis")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Top Agencies by Award Actions
            top_agencies_count = get_top_agencies(df, metric="count", n=15)
            
            if not top_agencies_count.empty:
                fig = px.bar(
                    top_agencies_count,
                    x="award_count",
                    y="parent_award_agency_name",
                    title="Top Agencies by Award Actions",
                    orientation="h",
                    color="award_count",
                    color_continuous_scale="dense",  # More vibrant color scale
                    labels={
                        "award_count": "Award Actions",
                        "parent_award_agency_name": "Agency"
                    }
                )
                
                # Update layout
                fig.update_layout(
                    plot_bgcolor=THEME["sidebar_bg"],
                    paper_bgcolor=THEME["sidebar_bg"],
                    font=dict(color=THEME["text_color"]),
                    margin=dict(l=40, r=40, t=40, b=40),
                    coloraxis_showscale=False,
                    uniformtext_minsize=10,  # Ensure minimum text size
                    uniformtext_mode='hide',  # Hide labels that don't fit
                    title_font=dict(size=16, color=THEME["text_color"])
                )
                
                # Update axes
                fig.update_xaxes(
                    showgrid=True,
                    gridcolor="rgba(255,255,255,0.2)",  # Brighter grid lines
                    tickformat=",.0f",  # Format tick values with commas
                    title_font=dict(size=14, color=THEME["text_color"]),
                    tickfont=dict(size=12, color=THEME["text_color"]),
                    showline=True,
                    linecolor="rgba(255,255,255,0.5)"
                )
                
                fig.update_yaxes(
                    showgrid=False,
                    categoryorder="total ascending",
                    title=None,  # Remove y-axis title for cleaner look
                    tickfont=dict(size=12, color=THEME["text_color"]),
                    showline=True,
                    linecolor="rgba(255,255,255,0.5)"
                )
                
                # Add value annotations
                fig.update_traces(
                    texttemplate="%{x:,.0f}",  # Format with commas
                    textposition="outside",
                    cliponaxis=False
                )
                
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("Insufficient data for top agencies by award actions.")
        
        with col2:
            # Top Agencies by Obligation Amount
            top_agencies_dollars = get_top_agencies(df, metric="obligation", n=15)
            
            if not top_agencies_dollars.empty:
                fig = px.bar(
                    top_agencies_dollars,
                    x="federal_action_obligation",
                    y="parent_award_agency_name",
                    title="Top Agencies by Obligation Amount",
                    orientation="h",
                    color="federal_action_obligation",
                    color_continuous_scale="dense",  # More vibrant color scale
                    labels={
                        "federal_action_obligation": "Obligation Amount ($)",
                        "parent_award_agency_name": "Agency"
                    }
                )
                
                # Update layout
                fig.update_layout(
                    plot_bgcolor=THEME["sidebar_bg"],
                    paper_bgcolor=THEME["sidebar_bg"],
                    font=dict(color=THEME["text_color"]),
                    margin=dict(l=40, r=40, t=40, b=40),
                    coloraxis_showscale=False,
                    uniformtext_minsize=10,
                    uniformtext_mode='hide',
                    title_font=dict(size=16, color=THEME["text_color"])
                )
                
                # Update axes
                fig.update_xaxes(
                    showgrid=True,
                    gridcolor=THEME["grid_color"],
                    tickprefix="$",
                    tickformat=",.0f"  # Format numbers with commas
                )
                
                fig.update_yaxes(
                    showgrid=False,
                    categoryorder="total ascending",
                    title=None  # Remove y-axis title for cleaner look
                )
                
                # Add formatted value annotations
                # Use our format_value function to make readable labels
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
    else:
        st.error("No data available. Please check your filter settings or database connection.")

"""
Competitive Analysis tab for the Strategic Dashboard.

This module provides visualization functions for the Competitive Analysis tab content.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from src.frontend.styles.theme import THEME, COLOR_SCALES, CHART_DEFAULTS


def render_competitive_analysis(df):
    """
    Render the Competitive Analysis tab content.
    
    Args:
        df: DataFrame containing award data
    """
    if not df.empty:
        # Import necessary functions from strategic dashboard
        from src.frontend.pages.strategic_dashboard import (
            get_award_summary, format_value, get_treemap_data, 
            get_competitive_landscape, get_top_agencies
        )
        
        st.header("Competitive Analysis")
        st.subheader("Competitive Intelligence Overview")
        st.markdown("""
        This tab provides detailed analysis of the competitive landscape across federal contracts, 
        helping you understand competitor strengths, agency relationships, and market positioning.
        """)
        
        # Top Competitors Analysis
        competitors_data = get_competitive_landscape(df)
        
        if not competitors_data.empty:
            # Prepare data for visualization - get top 10 competitors
            top_competitors = competitors_data.nlargest(10, 'market_share')
            
            # First row of visualizations - Market Share and Win Rate
            col1, col2 = st.columns(2)
            
            with col1:
                # Competitor Market Share Analysis
                st.subheader("Market Share Analysis")
                
                fig = px.bar(
                    top_competitors,
                    x='market_share',
                    y='recipient_name',
                    orientation='h',
                    title="Top 10 Competitors by Market Share",
                    color='market_share',
                    color_continuous_scale="Blues",
                    labels={
                        'market_share': 'Market Share (%)',
                        'recipient_name': 'Competitor'
                    }
                )
                
                # Update layout
                fig.update_layout(
                    plot_bgcolor=THEME["sidebar_bg"],
                    paper_bgcolor=THEME["sidebar_bg"],
                    font=dict(color="#FFFFFF"),
                    title_font=dict(color="#FFFFFF", size=16),
                    margin=dict(l=10, r=10, t=40, b=10),
                    yaxis={'categoryorder': 'total ascending'},
                    coloraxis_showscale=False,
                    modebar=dict(
                        bgcolor="rgba(22, 45, 69, 0.8)",
                        color="#FFFFFF",
                        activecolor=THEME["primary_color"]
                    )
                )
                
                # Add value annotations
                fig.update_traces(
                    texttemplate='%{x:.1f}%',
                    textposition='outside',
                    hovertemplate='<b>%{y}</b><br>Market Share: %{x:.2f}%<extra></extra>'
                )
                
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # Competitor Win Rate Analysis
                st.subheader("Win Rate Analysis")
                
                fig = px.bar(
                    top_competitors,
                    x='win_rate',
                    y='recipient_name',
                    orientation='h',
                    title="Top 10 Competitors by Win Rate",
                    color='win_rate',
                    color_continuous_scale="Teal",
                    labels={
                        'win_rate': 'Win Rate (%)',
                        'recipient_name': 'Competitor'
                    }
                )
                
                # Update layout
                fig.update_layout(
                    plot_bgcolor=THEME["sidebar_bg"],
                    paper_bgcolor=THEME["sidebar_bg"],
                    font=dict(color="#FFFFFF"),
                    title_font=dict(color="#FFFFFF", size=16),
                    margin=dict(l=10, r=10, t=40, b=10),
                    yaxis={'categoryorder': 'total ascending'},
                    coloraxis_showscale=False,
                    modebar=dict(
                        bgcolor="rgba(22, 45, 69, 0.8)",
                        color="#FFFFFF",
                        activecolor=THEME["primary_color"]
                    )
                )
                
                # Add value annotations
                fig.update_traces(
                    texttemplate='%{x:.1f}%',
                    textposition='outside',
                    hovertemplate='<b>%{y}</b><br>Win Rate: %{x:.2f}%<extra></extra>'
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
            # Market Position Analysis - Scatter Plot
            st.subheader("Market Position Analysis")
            
            # Create scatter plot with win rate vs market share
            fig = px.scatter(
                top_competitors,
                x='market_share',
                y='win_rate',
                size='federal_action_obligation',
                color='recipient_name',
                hover_name='recipient_name',
                title="Competitive Positioning: Win Rate vs Market Share",
                labels={
                    'market_share': 'Market Share (%)',
                    'win_rate': 'Win Rate (%)',
                    'federal_action_obligation': 'Total Obligations ($)'
                },
                size_max=50
            )

            # Add quadrant lines at median values
            median_market_share = top_competitors['market_share'].median()
            median_win_rate = top_competitors['win_rate'].median()
            
            fig.add_shape(
                type="line",
                x0=median_market_share,
                y0=0,
                x1=median_market_share,
                y1=top_competitors['win_rate'].max() * 1.1,
                line=dict(color="White", width=1, dash="dash")
            )
            
            fig.add_shape(
                type="line",
                x0=0,
                y0=median_win_rate,
                x1=top_competitors['market_share'].max() * 1.1,
                y1=median_win_rate,
                line=dict(color="White", width=1, dash="dash")
            )
            
            # Add quadrant labels
            fig.add_annotation(
                x=median_market_share/2,
                y=top_competitors['win_rate'].max() * 0.8,
                text="High Win Rate, Low Market Share",
                showarrow=False,
                font=dict(color="#FFFFFF", size=14),
                bgcolor="rgba(22, 45, 69, 0.8)",
                bordercolor=THEME["highlight_color"],
                borderwidth=1,
                borderpad=4
            )
            
            fig.add_annotation(
                x=median_market_share*1.5,
                y=top_competitors['win_rate'].max() * 0.8,
                text="Market Leaders",
                showarrow=False,
                font=dict(color="#FFFFFF", size=14),
                bgcolor="rgba(22, 45, 69, 0.8)",
                bordercolor=THEME["highlight_color"],
                borderwidth=1,
                borderpad=4
            )
            
            fig.add_annotation(
                x=median_market_share/2,
                y=median_win_rate/2,
                text="Struggling Competitors",
                showarrow=False,
                font=dict(color="#FFFFFF", size=14),
                bgcolor="rgba(22, 45, 69, 0.8)",
                bordercolor=THEME["highlight_color"],
                borderwidth=1,
                borderpad=4
            )
            
            fig.add_annotation(
                x=median_market_share*1.5,
                y=median_win_rate/2,
                text="High Volume, Low Win Rate",
                showarrow=False,
                font=dict(color="#FFFFFF", size=14),
                bgcolor="rgba(22, 45, 69, 0.8)",
                bordercolor=THEME["highlight_color"],
                borderwidth=1,
                borderpad=4
            )
            
            # Update axes titles
            fig.update_xaxes(
                title="Market Share (%)"
            )
            
            fig.update_yaxes(
                title="Win Rate (%)"
            )
            
            # Update point appearance
            fig.update_traces(
                marker=dict(
                    opacity=0.8,
                    line=dict(width=2, color="DarkSlateGrey")
                ),
                selector=dict(mode="markers")
            )
            
            # Update layout
            fig.update_layout(
                plot_bgcolor=THEME["sidebar_bg"],
                paper_bgcolor=THEME["sidebar_bg"],
                font=dict(color="#FFFFFF"),
                title_font=dict(color="#FFFFFF", size=16),
                margin=dict(l=10, r=10, t=40, b=10),
                modebar=dict(
                    bgcolor="rgba(22, 45, 69, 0.8)",
                    color="#FFFFFF",
                    activecolor=THEME["primary_color"]
                )
            )
            
            # Update hover template
            fig.update_traces(
                hovertemplate="<b>%{hovertext}</b><br>" +
                              "Market Share: %{x:.2f}%<br>" +
                              "Win Rate: %{y:.2f}%<br>" +
                              "Total Obligations: $%{marker.size:,.0f}<extra></extra>"
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Competitive Strategy Insights
            st.subheader("Competitive Strategy Insights")
            
            # Create a container for the insights
            insights_container = st.container()
            
            with insights_container:
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("""
                    ### Market Positioning
                    
                    Based on the competitive analysis, consider these strategies:
                    
                    - **Focus on high win-rate, low market share quadrant** agencies where your company can efficiently compete
                    - **Identify partnering opportunities** with complementary contractors
                    - **Target contract vehicles** with lower competitive intensity
                    - **Develop specialized offerings** for agencies with diverse contractor bases
                    """)
                
                with col2:
                    st.markdown("""
                    ### Differentiation Opportunities
                    
                    Competitive analysis suggests these differentiation approaches:
                    
                    - **Pricing strategies** tailored to specific contract types
                    - **Agency-specific expertise** development where competitors are weaker
                    - **Contract vehicle specialization** in less congested segments
                    - **Past performance emphasis** in areas with strong incumbent presence
                    """)
        else:
            st.warning("Insufficient data for competitive analysis. Try expanding your filter criteria.")
    else:
        # Help the user understand why there's no data
        st.warning("No data available for Competitive Analysis.")
        st.info("Possible issues:")
        st.markdown("""
        1. **Database Connection**: Verify PostgreSQL is running and connection details are correct
        2. **Table Names**: The table 'usaprime_cleaned' may not exist (sidebar will show available tables)
        3. **Data Availability**: There may be no data for selected NAICS code in the database
        4. **Date Range**: Try expanding the date range to capture more data
        
        See the Diagnostics section in the sidebar for more details.
        """)
        
        # Show a sample of what the tab would look like with data
        st.subheader("Sample Competitive Analysis View")
        st.image("https://via.placeholder.com/800x500.png?text=Competitive+Analysis+Dashboard+(Sample)", 
                caption="Sample visualization of Competitive Analysis tab with data")

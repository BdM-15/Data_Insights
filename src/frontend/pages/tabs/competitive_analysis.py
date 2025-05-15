"""
Competitive Analysis tab for the strategic dashboard.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from src.backend.data.processors.competition import get_competitive_landscape
from src.frontend.styles.theme import THEME


def render_tab(df: pd.DataFrame):
    """
    Render the Competitive Analysis tab content.

    Args:
        df: Filtered DataFrame for the dashboard
    """
    st.header("Competitive Analysis")

    # Check if data is available
    if not df.empty:
        st.subheader("Competitive Intelligence Overview")
        st.markdown(
            """
            This tab provides detailed analysis of the competitive landscape across federal contracts, 
            helping you understand competitor strengths, agency relationships, and market positioning.
            """
        )

        competitors_data = get_competitive_landscape(df)

        if not competitors_data.empty:
            # Top 10 competitors by market share
            top_competitors = competitors_data.nlargest(10, 'market_share')

            # Market Share and Win Rate
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("Market Share Analysis")
                fig = px.bar(
                    top_competitors,
                    x='market_share',
                    y='recipient_name',
                    orientation='h',
                    title="Top 10 Competitors by Market Share",
                    color='market_share',
                    color_continuous_scale="Blues",
                    labels={'market_share': 'Market Share (%)', 'recipient_name': 'Competitor'}
                )
                fig.update_layout(
                    plot_bgcolor=THEME["bg_color"],
                    paper_bgcolor=THEME["bg_color"],
                    font=dict(color=THEME["text_color"]),
                    margin=dict(l=10, r=10, t=40, b=10),
                    yaxis={'categoryorder': 'total ascending'},
                    coloraxis_showscale=False
                )
                fig.update_traces(
                    texttemplate='%{x:.1f}%',
                    textposition='outside',
                    hovertemplate='<b>%{y}</b><br>Market Share: %{x:.2f}%<extra></extra>'
                )
                st.plotly_chart(fig, use_container_width=True)

            with col2:
                st.subheader("Win Rate Analysis")
                fig = px.bar(
                    top_competitors,
                    x='win_rate',
                    y='recipient_name',
                    orientation='h',
                    title="Top 10 Competitors by Win Rate",
                    color='win_rate',
                    color_continuous_scale="Teal",
                    labels={'win_rate': 'Win Rate (%)', 'recipient_name': 'Competitor'}
                )
                fig.update_layout(
                    plot_bgcolor=THEME["bg_color"],
                    paper_bgcolor=THEME["bg_color"],
                    font=dict(color=THEME["text_color"]),
                    margin=dict(l=10, r=10, t=40, b=10),
                    yaxis={'categoryorder': 'total ascending'},
                    coloraxis_showscale=False
                )
                fig.update_traces(
                    texttemplate='%{x:.1f}%',
                    textposition='outside',
                    hovertemplate='<b>%{y}</b><br>Win Rate: %{x:.2f}%<extra></extra>'
                )
                st.plotly_chart(fig, use_container_width=True)

            # Market Position Analysis
            st.subheader("Market Position Analysis")
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
            fig.add_annotation(
                x=median_market_share/2,
                y=top_competitors['win_rate'].max() * 0.8,
                text="High Win Rate, Low Market Share",
                showarrow=False,
                font=dict(color=THEME["highlight_color"])
            )
            fig.add_annotation(
                x=median_market_share*1.5,
                y=top_competitors['win_rate'].max() * 0.8,
                text="Market Leaders",
                showarrow=False,
                font=dict(color=THEME["highlight_color"])
            )
            fig.add_annotation(
                x=median_market_share/2,
                y=median_win_rate/2,
                text="Struggling Competitors",
                showarrow=False,
                font=dict(color=THEME["text_color"])
            )
            fig.add_annotation(
                x=median_market_share*1.5,
                y=median_win_rate/2,
                text="High Volume, Low Win Rate",
                showarrow=False,
                font=dict(color=THEME["text_color"])
            )
            fig.update_layout(
                plot_bgcolor=THEME["bg_color"],
                paper_bgcolor=THEME["bg_color"],
                font=dict(color=THEME["text_color"]),
                margin=dict(l=10, r=10, t=40, b=10)
            )
            fig.update_traces(
                hovertemplate="<b>%{hovertext}</b><br>Market Share: %{x:.2f}%<br>Win Rate: %{y:.2f}%<br>Total Obligations: $%{marker.size:,.0f}<extra></extra>"
            )
            st.plotly_chart(fig, use_container_width=True)

            # Competitor-Agency Relationships
            st.subheader("Competitor-Agency Relationships")
            if 'parent_award_agency_name' in df.columns and not df.empty:
                competitor_agency = df.groupby(['recipient_name', 'parent_award_agency_name'])['federal_action_obligation'].sum().reset_index()
                top_5_competitors = competitors_data.nlargest(5, 'market_share')['recipient_name'].tolist()
                competitor_agency = competitor_agency[competitor_agency['recipient_name'].isin(top_5_competitors)]
                competitor_top_agencies = {}
                for competitor in top_5_competitors:
                    competitor_data = competitor_agency[competitor_agency['recipient_name'] == competitor]
                    top_agencies = competitor_data.nlargest(3,'federal_action_obligation')
                    competitor_top_agencies[competitor] = top_agencies
                heatmap_data = []
                for competitor in top_5_competitors:
                    if competitor in competitor_top_agencies:
                        for _, row in competitor_top_agencies[competitor].iterrows():
                            heatmap_data.append({
                                'Competitor': competitor,
                                'Agency': row['parent_award_agency_name'],
                                'Obligation': row['federal_action_obligation']
                            })
                if heatmap_data:
                    heatmap_df = pd.DataFrame(heatmap_data)
                    pivot_df = heatmap_df.pivot_table(
                        values='Obligation',
                        index='Competitor',
                        columns='Agency',
                        aggfunc='sum',
                        fill_value=0
                    )
                    normalized_pivot = pivot_df.div(pivot_df.max(axis=1), axis=0)
                    fig = px.imshow(
                        normalized_pivot,
                        color_continuous_scale="Blues",
                        labels=dict(x="Agency", y="Competitor", color="Relationship Strength"),
                        title="Top Competitor-Agency Relationships"
                    )
                    fig.update_layout(
                        plot_bgcolor=THEME["bg_color"],
                        paper_bgcolor=THEME["bg_color"],
                        font=dict(color=THEME["text_color"]),
                        margin=dict(l=10, r=20, t=40, b=10),
                        xaxis={'side': 'top'}
                    )
                    fig.update_traces(
                        hovertemplate="<b>%{y}</b> - <b>%{x}</b><br>Relationship Strength: %{z:.2f}<br><extra></extra>"
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("Insufficient data to generate competitor-agency relationships.")
            else:
                st.info("Agency data not available to generate competitor-agency relationships.")

            # Contract Type Analysis
            st.subheader("Contract Type Analysis")
            if 'type_of_contract_pricing' in df.columns and not df.empty:
                contract_type_competition = df.groupby('type_of_contract_pricing')['recipient_name'].nunique().reset_index()
                contract_type_competition.columns = ['Contract Type', 'Number of Competitors']
                contract_type_competition = contract_type_competition.sort_values('Number of Competitors', ascending=False)
                top_contract_types = contract_type_competition.head(10)
                fig = px.bar(
                    top_contract_types,
                    x='Number of Competitors',
                    y='Contract Type',
                    orientation='h',
                    title="Competition Intensity by Contract Type",
                    color='Number of Competitors',
                    color_continuous_scale="Blues",
                    labels={
                        'Number of Competitors': 'Number of Unique Competitors',
                        'Contract Type': 'Contract Type'
                    }
                )
                fig.update_layout(
                    plot_bgcolor=THEME["bg_color"],
                    paper_bgcolor=THEME["bg_color"],
                    font=dict(color=THEME["text_color"]),
                    margin=dict(l=10, r=10, t=40, b=10),
                    yaxis={'categoryorder': 'total ascending'},
                    coloraxis_showscale=False
                )
                fig.update_traces(
                    texttemplate='%{x:.0f}',
                    textposition='outside',
                    hovertemplate='<b>%{y}</b><br>Competitors: %{x:.0f}<extra></extra>'
                )
                st.plotly_chart(fig, use_container_width=True)

                contract_type_value = df.groupby('type_of_contract_pricing')['federal_action_obligation'].sum().reset_index()
                contract_type_value.columns = ['Contract Type', 'Total Obligation']
                contract_type_analysis = pd.merge(contract_type_competition, contract_type_value, on='Contract Type')
                contract_type_analysis['Average Obligation'] = contract_type_analysis['Total Obligation'] / contract_type_analysis['Number of Competitors']
                top_value_types = contract_type_analysis.nlargest(10, 'Total Obligation')
                fig = make_subplots(specs=[[{"secondary_y": True}]])
                fig.add_trace(
                    go.Bar(
                        x=top_value_types['Contract Type'],
                        y=top_value_types['Total Obligation'],
                        name='Total Obligation',
                        marker_color=THEME["primary_color"]
                    ),
                    secondary_y=False
                )
                fig.add_trace(
                    go.Scatter(
                        x=top_value_types['Contract Type'],
                        y=top_value_types['Average Obligation'],
                        name='Avg Obligation per Competitor',
                        mode='lines+markers',
                        marker=dict(color=THEME["accent2_color"]),
                        line=dict(width=3)
                    ),
                    secondary_y=True
                )
                fig.update_layout(
                    title_text="Contract Type Value Analysis",
                    plot_bgcolor=THEME["bg_color"],
                    paper_bgcolor=THEME["bg_color"],
                    font=dict(color=THEME["text_color"]),
                    margin=dict(l=10, r=10, t=40, b=10),
                    legend=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=1.02,
                        xanchor="right",
                        x=1
                    )
                )
                fig.update_xaxes(title_text="Contract Type", tickangle=45)
                fig.update_yaxes(title_text="Total Obligation ($)", secondary_y=False, tickprefix="$", tickformat=",.")
                fig.update_yaxes(title_text="Avg Obligation per Competitor ($)", secondary_y=True, tickprefix="$", tickformat=",.")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Contract type data not available for analysis.")

            # Competitive Strategy Insights
            st.subheader("Competitive Strategy Insights")
            insights_container = st.container()
            with insights_container:
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(
                        """
                        ### Market Positioning
                        Based on the competitive analysis, consider these strategies:
                        - **Focus on high win-rate, low market share quadrant** agencies where your company can efficiently compete
                        - **Identify partnering opportunities** with complementary contractors
                        - **Target contract vehicles** with lower competitive intensity
                        - **Develop specialized offerings** for agencies with diverse contractor bases
                        """
                    )
                with col2:
                    st.markdown(
                        """
                        ### Differentiation Opportunities
                        Competitive analysis suggests these differentiation approaches:
                        - **Pricing strategies** tailored to specific contract types
                        - **Agency-specific expertise** development where competitors are weaker
                        - **Contract vehicle specialization** in less congested segments
                        - **Past performance emphasis** in areas with strong incumbent presence
                        """
                    )
        else:
            st.warning("Insufficient data for competitive analysis. Try expanding your filter criteria.")

    # If no data is available, show helpful warnings
    else:
        st.warning("No data available for Competitive Analysis.")
        st.info("Possible issues:")
        st.markdown(
            """
            1. **Database Connection**: Verify PostgreSQL is running and connection details are correct
            2. **Table Names**: The table 'usaprime_cleaned' may not exist (sidebar will show available tables)
            3. **Data Availability**: There may be no data for selected NAICS code in the database
            4. **Date Range**: Try expanding the date range to capture more data
            See the Diagnostics section in the sidebar for more details.
            """
        )

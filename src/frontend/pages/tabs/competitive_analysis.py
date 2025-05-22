"""
Competitive Analysis tab for the strategic dashboard.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import List

from src.backend.data.app_processors.competition import get_competitive_landscape
from src.backend.data.models.data_models import CompetitorPerformance
from src.frontend.styles.theme import THEME
from src.frontend.visualizations.charts.comparison_charts import plot_market_share_bar, plot_contract_type_competition_bar, plot_contract_type_value_analysis
from src.frontend.visualizations.charts.distribution_charts import plot_competitive_position_scatter, plot_competitor_agency_heatmap

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

        competitors_data: List[CompetitorPerformance] = get_competitive_landscape(df)

        if competitors_data:
            # Convert list of CompetitorPerformance models to DataFrame for visualization
            competitors_df = pd.DataFrame([c.dict() for c in competitors_data])
            # Top 10 competitors by market share
            top_competitors = competitors_df.nlargest(10, 'market_share')

            # Market Share and Win Rate
            col1, col2 = st.columns(2)
            with col1:
                fig = plot_market_share_bar(
                    top_competitors,
                    value_col='market_share',
                    label_col='recipient_name',
                    theme=THEME,
                    config={"title": "Top 10 Competitors by Market Share", "x_label": "Market Share (%)", "y_label": "Competitor", "color_scale": "Blues"}
                )
                st.plotly_chart(fig, use_container_width=True)
            with col2:
                fig = plot_market_share_bar(
                    top_competitors,
                    value_col='win_rate',
                    label_col='recipient_name',
                    theme=THEME,
                    config={"title": "Top 10 Competitors by Win Rate", "x_label": "Win Rate (%)", "y_label": "Competitor", "color_scale": "Teal"}
                )
                st.plotly_chart(fig, use_container_width=True)

            # Market Position Analysis and Competitor-Agency Relationships in two columns
            st.subheader("Market Position & Agency Relationships")
            col1, col2 = st.columns([1, 1])
            with col1:
                fig = plot_competitive_position_scatter(top_competitors, THEME)
                st.plotly_chart(fig, use_container_width=True)
            with col2:
                if 'parent_award_agency_name' in df.columns and not df.empty:
                    competitor_agency = df.groupby(['recipient_name', 'parent_award_agency_name'])['federal_action_obligation'].sum().reset_index()
                    top_5_competitors = competitors_df.nlargest(5, 'market_share')['recipient_name'].tolist()
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
                        fig = plot_competitor_agency_heatmap(normalized_pivot, THEME, config={"height": 600, "legend_font_size": 14, "title": None})
                        # Remove chart title from the Plotly figure (handles px.imshow bug)
                        fig.update_layout(title=None, title_text=None)
                        if hasattr(fig.layout, 'title'):
                            fig.layout.title.text = ''
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info("Insufficient data to generate competitor-agency relationships.")
                else:
                    st.info("Agency data not available to generate competitor-agency relationships.")

            # Contract Type Analysis in two columns
            st.subheader("Contract Type Analysis")
            col1, col2 = st.columns([1, 1])
            with col1:
                if 'type_of_contract_pricing' in df.columns and not df.empty:
                    contract_type_competition = df.groupby('type_of_contract_pricing')['recipient_name'].nunique().reset_index()
                    contract_type_competition.columns = ['Contract Type', 'Number of Competitors']
                    # Shorten long contract type names for display, add hover for full description
                    contract_type_competition['Contract Type Display'] = contract_type_competition['Contract Type'].apply(
                        lambda x: 'FIXED PRICE WITH EPA' if 'FIXED PRICE WITH ECONOMIC PRICE ADJUST' in x.upper() else x
                    )
                    contract_type_competition['Contract Type Display'] = contract_type_competition['Contract Type Display'].apply(
                        lambda x: 'ORDER DEPENDENT' if x.startswith('ORDER DEPENDENT') else x
                    )
                    contract_type_competition['Contract Type Hover'] = contract_type_competition['Contract Type'].apply(
                        lambda x: 'IDV ALLOWS PRICING ARRANGEMENT TO BE DETERMINED SEPARATELY FOR EACH ORDER' if x.startswith('ORDER DEPENDENT') else ''
                    )
                    top_contract_types = contract_type_competition.head(10)
                    fig = plot_contract_type_competition_bar(top_contract_types, THEME, config={"hover_col": "Contract Type Hover"})
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("Contract type data not available for analysis.")
            with col2:
                if 'type_of_contract_pricing' in df.columns and not df.empty:
                    contract_type_value = df.groupby('type_of_contract_pricing')['federal_action_obligation'].sum().reset_index()
                    contract_type_value.columns = ['Contract Type', 'Total Obligation']
                    contract_type_competition = df.groupby('type_of_contract_pricing')['recipient_name'].nunique().reset_index()
                    contract_type_competition.columns = ['Contract Type', 'Number of Competitors']
                    contract_type_analysis = pd.merge(contract_type_competition, contract_type_value, on='Contract Type')
                    contract_type_analysis['Average Obligation'] = contract_type_analysis['Total Obligation'] / contract_type_analysis['Number of Competitors']
                    # Shorten long contract type names for display, add hover for full description
                    contract_type_analysis['Contract Type Display'] = contract_type_analysis['Contract Type'].apply(
                        lambda x: 'FIXED PRICE WITH EPA' if 'FIXED PRICE WITH ECONOMIC PRICE ADJUST' in x.upper() else x
                    )
                    contract_type_analysis['Contract Type Display'] = contract_type_analysis['Contract Type Display'].apply(
                        lambda x: 'ORDER DEPENDENT' if x.startswith('ORDER DEPENDENT') else x
                    )
                    contract_type_analysis['Contract Type Hover'] = contract_type_analysis['Contract Type'].apply(
                        lambda x: 'IDV ALLOWS PRICING ARRANGEMENT TO BE DETERMINED SEPARATELY FOR EACH ORDER' if x.startswith('ORDER DEPENDENT') else ''
                    )
                    top_value_types = contract_type_analysis.nlargest(10, 'Total Obligation')
                    fig = plot_contract_type_value_analysis(top_value_types, THEME, config={"hover_col": "Contract Type Hover"})
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("Contract type data not available for analysis.")

            # Winning Strategy Suggestions (Restored original two-column layout)
            st.subheader("Winning Strategy Suggestions based on Competitive Analysis")
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(
                    """
                    **Market Positioning**
                    
                    - Target high-value, high-volume agencies for growth.
                    - Focus on agencies where your win rate is below average.
                    - Monitor expiring contracts for recompete opportunities.
                    - Diversify contract types to balance risk and opportunity.
                    """
                )
            with col2:
                st.markdown(
                    """
                    **Differentiation Opportunities**
                    
                    - Analyze top competitors to identify differentiators.
                    - Leverage teaming partners to fill capability gaps.
                    - Build relationships with key agency stakeholders.
                    - Invest in capabilities that align with agency priorities.
                    """
                )
            st.info(
                "_This section will provide AI-generated recommendations for improving win rates and market position based on the competitive landscape. In the future, this will be powered by an LLM/AI agent._"
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

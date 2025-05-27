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
from src.backend.data.app_processors.awards import get_competitor_agency_relationships, get_contract_type_analysis
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

            # Market Position Analysis and Competitor-Agency Relationships in two columns            st.subheader("Market Position & Agency Relationships")
            col1, col2 = st.columns([1, 1])
            with col1:
                fig = plot_competitive_position_scatter(top_competitors, THEME)
                st.plotly_chart(fig, use_container_width=True)
            with col2:
                # Use optimized SQL function for competitor-agency relationships
                
                # Get current filter context
                naics = df['naics_code'].iloc[0] if 'naics_code' in df.columns and len(df['naics_code'].unique()) == 1 else None
                start_date = df['action_date'].min().strftime('%Y-%m-%d') if 'action_date' in df.columns and not df.empty else None
                end_date = df['action_date'].max().strftime('%Y-%m-%d') if 'action_date' in df.columns and not df.empty else None
                agency = df['parent_award_agency_name'].iloc[0] if 'parent_award_agency_name' in df.columns and len(df['parent_award_agency_name'].unique()) == 1 else None
                
                competitor_agency_data = get_competitor_agency_relationships(
                    naics_code=naics,
                    start_date=start_date,
                    end_date=end_date,
                    agency=agency
                )
                
                if competitor_agency_data:
                    heatmap_df = pd.DataFrame(competitor_agency_data)
                    pivot_df = heatmap_df.pivot_table(
                        values='federal_action_obligation',
                        index='recipient_name',
                        columns='parent_award_agency_name',
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
            
            # Contract Type Analysis in two columns
            st.subheader("Contract Type Analysis")
            col1, col2 = st.columns([1, 1])
            with col1:
                # Use optimized SQL function for contract type analysis
                
                # Get current filter context
                naics = df['naics_code'].iloc[0] if 'naics_code' in df.columns and len(df['naics_code'].unique()) == 1 else None
                start_date = df['action_date'].min().strftime('%Y-%m-%d') if 'action_date' in df.columns and not df.empty else None
                end_date = df['action_date'].max().strftime('%Y-%m-%d') if 'action_date' in df.columns and not df.empty else None
                agency = df['parent_award_agency_name'].iloc[0] if 'parent_award_agency_name' in df.columns and len(df['parent_award_agency_name'].unique()) == 1 else None
                
                contract_type_data = get_contract_type_analysis(
                    naics_code=naics,
                    start_date=start_date,
                    end_date=end_date,
                    agency=agency
                )
                
                if contract_type_data.get('competition'):
                    contract_type_competition = pd.DataFrame(contract_type_data['competition'])
                    top_contract_types = contract_type_competition.head(10)
                    fig = plot_contract_type_competition_bar(top_contract_types, THEME, config={"hover_col": "Contract Type Hover"})
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("Contract type data not available for analysis.")
            with col2:
                if contract_type_data.get('value'):
                    contract_type_analysis = pd.DataFrame(contract_type_data['value'])
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

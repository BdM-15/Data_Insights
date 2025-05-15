"""
Geographic Analysis tab for the Strategic Dashboard.

This module provides visualization functions for the Geographic Analysis tab content.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from src.frontend.styles.theme import THEME
from src.backend.data.processors.awards import get_award_summary # Corrected import
from src.backend.data.models.data_models import AwardSummaryItem

def render_geographic_analysis(df: pd.DataFrame):
    """
    Render the Geographic Analysis tab content.
    
    Args:
        df: DataFrame containing award data filtered by NAICS code
    """
    st.header("Geographic Analysis")

    # For geographic analysis, we can use the award summary which might contain state information
    # or a dedicated geographic processor if one was created.
    # Let's assume get_award_summary_processor provides data that can be aggregated by state.
    award_summary_data = get_award_summary(df) # Corrected function call

    if not award_summary_data:
        st.info("No award data available for geographic analysis with the selected criteria.")
        return

    # Convert Pydantic models to a DataFrame
    geo_df = pd.DataFrame([model.model_dump() for model in award_summary_data])

    if 'place_of_performance_state_code' not in geo_df.columns or 'total_obligated_amount' not in geo_df.columns:
        st.warning("The necessary columns ('place_of_performance_state_code', 'total_obligated_amount') are not available in the processed data for geographic analysis.")
        # Display raw summary if columns are missing
        st.subheader("Award Summary Data (Lacks Geographic Columns)")
        st.dataframe(geo_df, use_container_width=True)
        st.markdown("---")
        st.info("Planned visualizations for regional spending, performance by location, and geographic concentration will be implemented once appropriate data fields are confirmed.")
        return

    # Ensure 'total_obligated_amount' is numeric
    geo_df['total_obligated_amount'] = pd.to_numeric(geo_df['total_obligated_amount'], errors='coerce').fillna(0)

    # --- Analysis by Place of Performance State ---
    st.subheader("Analysis by Place of Performance State")

    # Aggregate data by state
    state_performance = geo_df.groupby('place_of_performance_state_code').agg(
        total_obligation=('total_obligated_amount', 'sum'),
        award_count=('contract_award_unique_key', 'count') # Assuming 'contract_award_unique_key' is present for counting
    ).reset_index().sort_values(by='total_obligation', ascending=False)

    state_performance = state_performance[state_performance['place_of_performance_state_code'].notna()] # Remove entries where state is NaN

    if state_performance.empty:
        st.info("No data available for performance by state.")
    else:
        col1, col2 = st.columns(2)
        with col1:
            st.metric(label="Top State by Obligation", 
                      value=state_performance['place_of_performance_state_code'].iloc[0] if not state_performance.empty else "N/A",
                      delta=f"${state_performance['total_obligation'].iloc[0]:,.0f}" if not state_performance.empty else "")
        with col2:
            st.metric(label="Top State by Award Count",
                      value=state_performance.sort_values(by='award_count', ascending=False)['place_of_performance_state_code'].iloc[0] if not state_performance.empty else "N/A",
                      delta=f"{state_performance.sort_values(by='award_count', ascending=False)['award_count'].iloc[0]} awards" if not state_performance.empty else "")
        
        st.dataframe(state_performance.rename(columns={
            'place_of_performance_state_code': 'State Code',
            'total_obligation': 'Total Obligation ($)',
            'award_count': 'Number of Awards'
        }), use_container_width=True)

        # Bar chart for top N states by obligation
        top_n_states = 15
        fig_state_obligation = px.bar(
            state_performance.head(top_n_states),
            x='place_of_performance_state_code',
            y='total_obligation',
            title=f"Top {top_n_states} States by Total Obligation",
            labels={'place_of_performance_state_code': "State Code", 'total_obligation': "Total Obligation ($)"},
            color='place_of_performance_state_code'
        )
        fig_state_obligation.update_layout(**THEME)
        st.plotly_chart(fig_state_obligation, use_container_width=True)

        # Bar chart for top N states by award count
        fig_state_awards = px.bar(
            state_performance.sort_values(by='award_count', ascending=False).head(top_n_states),
            x='place_of_performance_state_code',
            y='award_count',
            title=f"Top {top_n_states} States by Number of Awards",
            labels={'place_of_performance_state_code': "State Code", 'award_count': "Number of Awards"},
            color='place_of_performance_state_code'
        )
        fig_state_awards.update_layout(**THEME)
        st.plotly_chart(fig_state_awards, use_container_width=True)
        
        # Note on Map Visualizations
        st.info("Choropleth map visualizations for US states can be added here if state FIPS codes or full state names are available and a suitable GeoJSON is used.")


    # Placeholder for other planned visualizations
    st.markdown("---")
    st.markdown("""
    Planned visualizations (requiring more specific data or processing):
    - Regional spending patterns (e.g., by US Census Region)
    - Performance by specific location (City/County - if data available)
    - Geographic concentration of awards (Heatmaps)
    """)

"""
Agency Intelligence tab for the strategic dashboard.
"""
import streamlit as st
import pandas as pd
import numpy as np
from src.backend.data.app_processors.agencies import get_top_agencies_by_award_count, get_top_agencies_by_obligation
from src.backend.data.app_processors.awards import get_expiring_contracts
from src.frontend.styles.theme import THEME
from src.frontend.visualizations.utils import apply_plotly_theme
from src.frontend.components.layouts.grid import section_divider, themed_aggrid, two_column_grid
import plotly.express as px
from st_aggrid import GridUpdateMode

def render_tab(df: pd.DataFrame):
    """
    Render the Agency Intelligence tab content.

    Args:
        df: Filtered DataFrame for the dashboard
    """
    st.header("Agency Intelligence")
    st.info("Explore detailed analytics for federal agencies, including spending trends, top NAICS/PSC, contractors, and expiring contracts.")

    # --- Context-aware Agency/Opportunity Selection ---
    selected_agency = None
    selected_naics = None
    selected_opp = st.session_state.get('selected_opportunity', None)
    if selected_opp:
        selected_agency = selected_opp.get('agency')
        selected_naics = selected_opp.get('naics_code')
        st.success(f"Context: Focusing on agency '{selected_agency}' and NAICS '{selected_naics}' from selected opportunity.")
    agencies = df['parent_award_agency_name'].dropna().unique()
    if selected_agency and selected_agency in agencies:
        agency_df = df[df['parent_award_agency_name'] == selected_agency].copy()
    else:
        selected_agency = st.selectbox("Select Agency", sorted(agencies))
        agency_df = df[df['parent_award_agency_name'] == selected_agency].copy()

    # --- Streamlit rerun note ---
    st.caption("Note: Changing the agency selection will refresh the entire dashboard tab due to Streamlit's rerun behavior.")

    # --- Agency Profile & Summary (Metrics in columns) ---
    section_divider(f"{selected_agency} Profile & Summary", icon="🏛️")
    total_obligation = agency_df['federal_action_obligation'].sum()
    award_count = (agency_df['modification_number'] == '0').sum()
    avg_award_value = total_obligation / award_count if award_count > 0 else 0
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Obligations", f"${total_obligation:,.0f}")
    with col2:
        st.metric("Award Actions", f"{award_count:,}")
    with col3:
        st.metric("Avg Award Value", f"${avg_award_value:,.0f}")

    # --- Spending Trends (Quarterly, dual-axis line chart) ---
    from src.backend.data.app_processors.awards import get_quarterly_trends
    from src.frontend.visualizations.charts.trend_charts import plot_quarterly_trends
    section_divider("Spending Trends (Quarterly)", icon="📈")
    # Use SQL-backed, filter-aware quarterly trends
    quarterly_data = get_quarterly_trends(
        agency=selected_agency,
        naics_code=selected_naics
        # Optionally add start_date/end_date if available in the UI context
    )
    if quarterly_data:
        qtr_df = pd.DataFrame([q.dict() for q in quarterly_data])
        fig = plot_quarterly_trends(qtr_df, THEME, config={"title": f"{selected_agency} Obligations & Award Actions by Quarter"})
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Insufficient data for quarterly trends visualization.")

    # --- Top NAICS/PSC Codes (always show tables if columns exist) ---
    section_divider("Top NAICS & PSC Codes", icon="🔢")
    naics_cols = [c for c in ['naics_code', 'naics_description'] if c in agency_df.columns]
    if len(naics_cols) == 2:
        top_naics = agency_df.groupby(naics_cols)['federal_action_obligation'].sum().reset_index().sort_values('federal_action_obligation', ascending=False).head(10)
        themed_aggrid(top_naics, columns=['naics_code', 'naics_description', 'federal_action_obligation'], height=220, update_mode=GridUpdateMode.NO_UPDATE)
    else:
        st.warning("NAICS description columns not found in data.")
    psc_cols = [c for c in ['product_or_service_code', 'product_or_service_code_description'] if c in agency_df.columns]
    if len(psc_cols) == 2:
        top_psc = agency_df.groupby(psc_cols)['federal_action_obligation'].sum().reset_index().sort_values('federal_action_obligation', ascending=False).head(10)
        themed_aggrid(top_psc, columns=['product_or_service_code', 'product_or_service_code_description', 'federal_action_obligation'], height=220, update_mode=GridUpdateMode.NO_UPDATE)
    else:
        st.warning("PSC description columns not found in data.")

    # --- Top Contractors ---
    section_divider("Top Contractors", icon="🏢")
    if 'recipient_name' in agency_df.columns:
        top_contractors = agency_df.groupby('recipient_name')['federal_action_obligation'].sum().reset_index().sort_values('federal_action_obligation', ascending=False).head(10)
        themed_aggrid(top_contractors, columns=['recipient_name', 'federal_action_obligation'], height=220, update_mode=GridUpdateMode.NO_UPDATE)
    else:
        st.warning("Contractor data not available for this agency.")

    # --- Expiring Contracts ---
    section_divider("Expiring Contracts (Next 24 Months)", icon="⏳")
    expiring_contracts = get_expiring_contracts(agency_df, months_ahead=24)
    if expiring_contracts:
        exp_df = pd.DataFrame([c.dict() for c in expiring_contracts])
        themed_aggrid(exp_df, columns=['contract_award_unique_key', 'recipient_name', 'period_of_performance_current_end_date', 'potential_total_value_of_award', 'days_to_expiration'], height=220, update_mode=GridUpdateMode.NO_UPDATE)
    else:
        st.info("No expiring contracts found for this agency in the next 24 months.")

    # --- Upcoming Opportunities (Stub/Planned) ---
    section_divider("Upcoming Opportunities (Planned)", icon="📋")
    st.info("Integration with SAM.gov and other sources for upcoming opportunities is planned.")

    # --- AI-Generated Insights (Stub) ---
    section_divider("AI-Generated Insights", icon="🤖")
    st.info("AI-generated narrative and recommendations for agency strategy will appear here.")

"""
Future Opportunities tab for the strategic dashboard.
"""
import streamlit as st
import pandas as pd
from src.backend.data.app_processors.future_opportunities import get_future_opportunities
from src.backend.data.models.data_models import FutureOpportunity
import plotly.express as px
from datetime import date
from src.frontend.styles.theme import THEME
from src.frontend.visualizations.utils import apply_plotly_theme
from st_aggrid import GridUpdateMode
from src.frontend.components.layouts.grid import two_column_grid, section_divider, themed_aggrid

def render_tab(df: pd.DataFrame = None):
    """
    Render the Future Opportunities tab content.

    Args:
        df: Filtered DataFrame for the dashboard (already filtered by main sidebar)
    """
    from src.backend.data.app_processors.awards import get_expiring_contracts
    import numpy as np

    st.header("Future Opportunities")
    st.info("This tab identifies upcoming opportunities by connecting historical contract data with active solicitations from SAM.gov and NATO NSPA.")

    # --- Fetch Data (use main dashboard filters) ---
    filtered_opps = get_future_opportunities(limit=100)

    # --- Expiring Contracts Section ---
    section_divider("Expiring Contracts (6-24 Months)", icon="⏳")
    expiring_contracts = get_expiring_contracts(df, months_ahead=24)
    if expiring_contracts:
        exp_df = pd.DataFrame([c.dict() for c in expiring_contracts])
        if 'recipient_name' not in exp_df:
            exp_df['recipient_name'] = 'IncumbentCo'
        if 'description' not in exp_df:
            exp_df['description'] = 'Contract description placeholder.'
        exp_df['suitability_score'] = np.random.randint(60, 95, size=len(exp_df))
        themed_aggrid(
            exp_df,
            columns=[
                'contract_award_unique_key', 'recipient_name', 'period_of_performance_current_end_date',
                'potential_total_value_of_award', 'description', 'suitability_score'
            ],
            selection_mode="multiple",
            use_checkbox=True,
            height=250,
            update_mode=GridUpdateMode.NO_UPDATE
        )
    else:
        st.info("No expiring contracts found in the next 6-24 months.")

    # --- Visual Insights Section ---
    section_divider("Visual Insights", icon="📊")

    def left_visual():
        # Bar chart: Opportunities by Agency
        if filtered_opps:
            df_opps = pd.DataFrame([o.dict() for o in filtered_opps])
            agency_counts = df_opps['agency'].value_counts().reset_index()
            agency_counts.columns = ['Agency', 'Count']
            fig = px.bar(agency_counts, x='Agency', y='Count', title='Opportunities by Agency')
            apply_plotly_theme(fig, THEME)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No data for agency visualization.")

    def right_visual():
        # Timeline: Response Due Dates
        if filtered_opps:
            df_opps = pd.DataFrame([o.dict() for o in filtered_opps])
            fig = px.timeline(
                df_opps,
                x_start="posted_date",
                x_end="response_due_date",
                y="title",
                color="agency",
                title="Response Due Dates for Opportunities"
            )
            apply_plotly_theme(fig, THEME)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No data for timeline visualization.")

    two_column_grid(left_visual, right_visual)

    # --- Table and Details Section ---
    section_divider("Upcoming Opportunities", icon="📋")
    if filtered_opps:
        df_opps = pd.DataFrame([o.dict() for o in filtered_opps])
        df_opps['suitability_score'] = np.random.randint(60, 95, size=len(df_opps))
        aggrid_response = themed_aggrid(
            df_opps,
            columns=[
                'opportunity_id', 'title', 'agency', 'naics_code', 'estimated_value',
                'posted_date', 'response_due_date', 'status', 'suitability_score'
            ],
            selection_mode="multiple",
            use_checkbox=True,
            height=350,
            update_mode=GridUpdateMode.NO_UPDATE
        )
        selected_rows = aggrid_response.selected_rows if aggrid_response and aggrid_response.selected_rows is not None else []
        show_details = st.button("Show Details for Selected Opportunities")
        # --- New: Store selected opportunity in session state for downstream tabs ---
        if len(selected_rows) == 1:
            # Only store if exactly one is selected (for downstream context)
            from src.backend.data.models.data_models import FutureOpportunity
            selected_opp = next((o for o in filtered_opps if o.opportunity_id == selected_rows[0]['opportunity_id']), None)
            if selected_opp:
                st.session_state['selected_opportunity'] = selected_opp.dict()
                st.info(f"Selected opportunity context set for downstream tabs: {selected_opp.title}")
        elif len(selected_rows) == 0:
            st.session_state.pop('selected_opportunity', None)
        if show_details and len(selected_rows) > 0:
            st.markdown("---")
            st.markdown("#### Opportunity Details")
            for row in selected_rows:
                opp = next((o for o in filtered_opps if o.opportunity_id == row['opportunity_id']), None)
                if opp:
                    st.markdown(f"**Title:** {opp.title}")
                    st.markdown(f"**Agency:** {opp.agency}")
                    st.markdown(f"**NAICS:** {opp.naics_code} - {opp.naics_description}")
                    st.markdown(f"**Estimated Value:** ${opp.estimated_value:,.0f}")
                    st.markdown(f"**Posted:** {opp.posted_date}")
                    st.markdown(f"**Response Due:** {opp.response_due_date}")
                    st.markdown(f"**Status:** {opp.status}")
                    st.markdown(f"**Suitability Score:** {row['suitability_score']}")
                    st.markdown(f"**Synopsis:** {opp.synopsis}")
                    st.markdown(f"[View Opportunity]({opp.url})")
                    st.button(f"Generate Capture Profile for {opp.title}", key=f"profile_{opp.opportunity_id}")
                    st.markdown("---")
    else:
        st.warning("No future opportunities found for the selected filters.")

    # --- Strategic Connections Section (Mock Logic) ---
    section_divider("Strategic Connections", icon="🔗")
    st.info("Links expiring contracts to similar open opportunities or historical wins. (Mocked for now)")
    if filtered_opps and expiring_contracts:
        # Mock: Link by NAICS code
        df_opps = pd.DataFrame([o.dict() for o in filtered_opps])
        exp_df = pd.DataFrame([c.dict() for c in expiring_contracts])
        connections = []
        for _, exp_row in exp_df.iterrows():
            matches = df_opps[df_opps['naics_code'] == exp_row.get('naics_code', None)]
            for _, opp_row in matches.iterrows():
                connections.append({
                    'Expiring Contract': exp_row.get('contract_award_unique_key', ''),
                    'Incumbent': exp_row.get('recipient_name', ''),
                    'Expiring End': exp_row.get('period_of_performance_current_end_date', ''),
                    'Opportunity': opp_row['title'],
                    'Agency': opp_row['agency'],
                    'Response Due': opp_row['response_due_date'],
                    'NAICS': opp_row['naics_code'],
                })
        if connections:
            st.dataframe(pd.DataFrame(connections), use_container_width=True)
        else:
            st.info("No strategic connections found (by NAICS code).")
    else:
        st.info("Not enough data to show strategic connections.")

"""
Capability Stance Page

Provides a comprehensive overview of KBR's company performance, teaming, and capabilities using prime awards, subawards received, and subawards issued.
All metrics, visuals, and tables are filter-driven and leverage deduplicated, precomputed tables for performance.
"""
import streamlit as st
from datetime import date, timedelta
from typing import List, Optional
import pandas as pd
from src.backend.data.models.data_models import CompanyPerformanceMetrics, TopEntitySummary
import os
import sys
from src.frontend.styles.theme import THEME
from src.frontend.styles.custom_css import generate_theme_css
from src.backend.core.database import execute_query
from src.frontend.utils.formatting import format_value

# --- Helper Functions (stubs, to be implemented with real queries) ---
def get_company_performance_metrics(filters: dict) -> CompanyPerformanceMetrics:
    """
    Query the database for KBR company performance metrics, using the 60-month toggle and date filters.
    """
    recent_months = filters.get("recent_activity_months", 0)
    use_60_months = recent_months == 60
    # Date filter logic
    if use_60_months:
        prime_date_filter = "action_date IS NULL OR action_date >= (CURRENT_DATE - INTERVAL '60 months')"
        sub_date_filter = "subaward_action_date IS NULL OR subaward_action_date >= (CURRENT_DATE - INTERVAL '60 months')"
        issued_date_filter = "subaward_action_date IS NULL OR subaward_action_date::date >= (CURRENT_DATE - INTERVAL '60 months')"
    else:
        prime_date_filter = "1=1"
        sub_date_filter = "1=1"
        issued_date_filter = "1=1"

    # Prime awards
    prime_awards = execute_query(f"SELECT COUNT(*) AS n FROM s3_processed.usaspending_prime_awards_kbr WHERE {prime_date_filter}")['n'][0]
    prime_obligation = execute_query(f"SELECT COALESCE(SUM(federal_action_obligation),0) AS s FROM s3_processed.usaspending_prime_awards_kbr WHERE {prime_date_filter}")['s'][0]
    unique_naics_prime = execute_query(f"SELECT COUNT(DISTINCT naics_code) AS n FROM s3_processed.usaspending_prime_awards_kbr WHERE {prime_date_filter} AND naics_code IS NOT NULL AND naics_code != ''")['n'][0]
    unique_psc_prime = execute_query(f"SELECT COUNT(DISTINCT product_or_service_code) AS n FROM s3_processed.usaspending_prime_awards_kbr WHERE {prime_date_filter} AND product_or_service_code IS NOT NULL AND product_or_service_code != ''")['n'][0]

    # Subawards received
    subawards_received = execute_query(f"SELECT COUNT(*) AS n FROM s3_processed.usaspending_subawards_kbr WHERE {sub_date_filter}")['n'][0]
    subawards_received_value = execute_query(f"SELECT COALESCE(SUM(subaward_amount),0) AS s FROM s3_processed.usaspending_subawards_kbr WHERE {sub_date_filter}")['s'][0]
    # No NAICS/PSC columns in subawards_kbr, so set to 0 or 1 as proxy
    unique_naics_sub = 1
    unique_psc_sub = 0

    # Subawards issued
    subawards_issued = execute_query(f"SELECT COUNT(*) AS n FROM s3_processed.usaspending_subawards_kbr_issued WHERE {issued_date_filter}")['n'][0]
    subawards_issued_value = execute_query(f"SELECT COALESCE(SUM(subaward_amount::numeric),0) AS s FROM s3_processed.usaspending_subawards_kbr_issued WHERE {issued_date_filter}")['s'][0]
    unique_naics_issued = execute_query(f"SELECT COUNT(DISTINCT naics_code) AS n FROM s3_processed.usaspending_subawards_kbr_issued WHERE {issued_date_filter} AND naics_code IS NOT NULL AND naics_code != ''")['n'][0]
    unique_psc_issued = execute_query(f"SELECT COUNT(DISTINCT product_or_service_code) AS n FROM s3_processed.usaspending_subawards_kbr_issued WHERE {issued_date_filter} AND product_or_service_code IS NOT NULL AND product_or_service_code != ''")['n'][0]

    # Top agencies/partners: stub for now (implement as needed)
    top_agencies_prime = []
    top_agencies_sub = []
    top_agencies_issued = []
    top_teaming_partners_prime = []
    top_teaming_partners_sub = []

    return CompanyPerformanceMetrics(
        total_prime_awards=prime_awards,
        total_prime_obligation=prime_obligation,
        total_subawards_received=subawards_received,
        total_subawards_received_value=subawards_received_value,
        total_subawards_issued=subawards_issued,
        total_subawards_issued_value=subawards_issued_value,
        unique_naics_prime=unique_naics_prime,
        unique_naics_sub=unique_naics_sub,
        unique_naics_issued=unique_naics_issued,
        unique_psc_prime=unique_psc_prime,
        unique_psc_sub=unique_psc_sub,
        unique_psc_issued=unique_psc_issued,
        top_agencies_prime=top_agencies_prime,
        top_agencies_sub=top_agencies_sub,
        top_agencies_issued=top_agencies_issued,
        top_teaming_partners_prime=top_teaming_partners_prime,
        top_teaming_partners_sub=top_teaming_partners_sub,
        recent_activity_months=recent_months
    )

# --- UI ---
def main():
    # Apply theme CSS
    st.markdown(generate_theme_css(THEME), unsafe_allow_html=True)

    # --- Sidebar Navigation & Filters ---
    with st.sidebar:
        st.header("Filters")
        default_start = date(2012, 10, 1)
        default_end = date(2025, 4, 30)
        start_date = st.date_input("Start Date", default_start)
        end_date = st.date_input("End Date", default_end)
        recent_activity = st.toggle("Show Only Last 60 Months", value=False)
        # If toggle is on, override start_date
        if recent_activity:
            end_date = date.today()
            start_date = end_date - timedelta(days=30*60)  # Approximate 60 months
        filters = {
            "start_date": start_date,
            "end_date": end_date,
            "recent_activity_months": 60 if recent_activity else 0
        }
        st.markdown("---")
        st.caption("Data_Insights v1.0 | Last updated: 2025-06-18")

    # --- Main Page Content ---
    st.title("🏆 Capability Stance Overview")
    st.markdown("""
    Analyze KBR's company performance, teaming, and capabilities using prime awards, subawards received, and subawards issued. All metrics and visuals update with your selected filters.
    """)

    # --- Metrics Cards ---
    metrics = get_company_performance_metrics(filters)
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    with col1:
        st.metric("Prime Awards", format_value(metrics.total_prime_awards))
    with col2:
        st.metric("Prime Obligation", format_value(metrics.total_prime_obligation, is_currency=True))
    with col3:
        st.metric("Subawards Received", format_value(metrics.total_subawards_received))
    with col4:
        st.metric("Subawards Received Value", format_value(metrics.total_subawards_received_value, is_currency=True))
    with col5:
        st.metric("Subawards Issued", format_value(metrics.total_subawards_issued))
    with col6:
        st.metric("Subawards Issued Value", format_value(metrics.total_subawards_issued_value, is_currency=True))

    # --- Capabilities Columns ---
    st.markdown("### Capabilities Overview")
    cap_col1, cap_col2, cap_col3, cap_col4 = st.columns(4)
    with cap_col1:
        st.metric("Unique NAICS (Prime)", format_value(metrics.unique_naics_prime))
    with cap_col2:
        st.metric("Unique PSC (Prime)", format_value(metrics.unique_psc_prime))
    with cap_col3:
        st.metric("Unique NAICS (Issued)", format_value(metrics.unique_naics_issued))
    with cap_col4:
        st.metric("Unique PSC (Issued)", format_value(metrics.unique_psc_issued))

    # --- Visuals: Top NAICS, PSC, Agencies, Teaming Partners (Prime & Issued) ---
    import plotly.express as px
    from src.backend.data.models.data_models import NAICSData, TopEntitySummary

    st.markdown("### Top Codes and Partners")
    vis_col1, vis_col2, vis_col3 = st.columns(3)

    # Top NAICS (Prime) by Award Actions (base awards only, mod_number = '0'), top 20, x-axis as categorical
    top_naics_awards_query = (
        f'''
        SELECT naics_code, naics_description, COUNT(*) AS award_count
        FROM s3_processed.usaspending_prime_awards_kbr
        WHERE modification_number = '0'
          AND naics_code IS NOT NULL AND naics_code != ''
          AND {('action_date IS NULL OR action_date >= (CURRENT_DATE - INTERVAL \'60 months\')') if filters['recent_activity_months'] == 60 else '1=1'}
        GROUP BY naics_code, naics_description
        ORDER BY award_count DESC, naics_code ASC
        LIMIT 20
        '''
    )
    top_naics_awards_df = execute_query(top_naics_awards_query)
    with vis_col1:
        st.markdown("**Top NAICS by Award Actions**")
        if not top_naics_awards_df.empty:
            top_naics_awards_df["naics_code"] = top_naics_awards_df["naics_code"].astype(str)
            num_naics_awards = len(top_naics_awards_df)
            fig_naics_awards = px.bar(
                top_naics_awards_df,
                x='naics_code',
                y='award_count',
                title=None,  # Remove native plotly title
                labels={'naics_code': 'NAICS Code', 'award_count': 'Number of Awards'},
                color='naics_code',
                color_discrete_sequence=px.colors.qualitative.Plotly
            )
            fig_naics_awards.update_layout(xaxis_tickangle=45, xaxis_type='category', showlegend=False, height=400)
            st.plotly_chart(fig_naics_awards, use_container_width=True)
        else:
            st.info("No data available.")

    # Top 20 NAICS by Obligations (Prime, base awards only, mod_number = '0'), x-axis as categorical
    top_naics_obligations_query = (
        f'''
        SELECT naics_code, naics_description, SUM(federal_action_obligation) AS total_obligation
        FROM s3_processed.usaspending_prime_awards_kbr
        WHERE modification_number = '0'
          AND naics_code IS NOT NULL AND naics_code != ''
          AND {('action_date IS NULL OR action_date >= (CURRENT_DATE - INTERVAL \'60 months\')') if filters['recent_activity_months'] == 60 else '1=1'}
        GROUP BY naics_code, naics_description
        ORDER BY total_obligation DESC, naics_code ASC
        LIMIT 20
        '''
    )
    top_naics_obligations_df = execute_query(top_naics_obligations_query)
    with vis_col2:
        st.markdown("**Top NAICS by Obligations**")
        if not top_naics_obligations_df.empty:
            top_naics_obligations_df["naics_code"] = top_naics_obligations_df["naics_code"].astype(str)
            num_naics_oblig = len(top_naics_obligations_df)
            fig_naics_oblig = px.bar(
                top_naics_obligations_df,
                x='naics_code',
                y='total_obligation',
                title=None,  # Remove native plotly title
                labels={'naics_code': 'NAICS Code', 'total_obligation': 'Total Obligations ($)'},
                color='naics_code',
                color_discrete_sequence=px.colors.qualitative.Plotly
            )
            fig_naics_oblig.update_layout(xaxis_tickangle=45, xaxis_type='category', showlegend=False, height=400)
            st.plotly_chart(fig_naics_oblig, use_container_width=True)
        else:
            st.info("No data available.")

    # Unique NAICS/PSC Combinations (Prime) table in third column
    naics_prime_query = (
        f"""
        SELECT naics_code AS "NAICS", naics_description AS "NAICS Description",
               product_or_service_code AS "PSC", product_or_service_code_description AS "PSC Description"
        FROM s3_processed.usaspending_prime_awards_kbr
        WHERE {('action_date IS NULL OR action_date >= (CURRENT_DATE - INTERVAL \'60 months\')') if filters['recent_activity_months'] == 60 else '1=1'}
          AND naics_code IS NOT NULL AND naics_code != ''
          AND product_or_service_code IS NOT NULL AND product_or_service_code != ''
        GROUP BY naics_code, naics_description, product_or_service_code, product_or_service_code_description
        ORDER BY naics_code ASC, product_or_service_code ASC
        """
    )
    naics_prime_df = execute_query(naics_prime_query)
    with vis_col3:
        st.markdown("**Unique NAICS/PSC Combinations (Prime)**")
        st.dataframe(naics_prime_df, use_container_width=True)

    # --- Restore all visuals and tables previously present, below the Top Codes and Partners section ---
    # --- Three column layout for Top Agencies and Prime Companies ---
    # Prepare data for three-column layout (move queries here so variables are in scope)
    top_agency_prime_query = (
        f"""
        SELECT parent_award_agency_name AS name, COUNT(*) AS count, 0.0 AS value
        FROM s3_processed.usaspending_prime_awards_kbr
        WHERE {('action_date IS NULL OR action_date >= (CURRENT_DATE - INTERVAL \'60 months\')') if filters['recent_activity_months'] == 60 else '1=1'}
          AND parent_award_agency_name IS NOT NULL AND parent_award_agency_name != ''
        GROUP BY parent_award_agency_name
        ORDER BY count DESC
        LIMIT 10
        """
    )
    top_agency_prime_df = execute_query(top_agency_prime_query)

    top_prime_kbr_query = (
        f"""
        SELECT recipient_name AS "Prime Company", recipient_uei, COUNT(*) AS count
        FROM s3_processed.usaspending_prime_awards_kbr
        WHERE recipient_uei IS NOT NULL AND recipient_uei != ''
        GROUP BY recipient_uei, recipient_name
        ORDER BY "Prime Company" ASC
        """
    )
    top_prime_kbr_df = execute_query(top_prime_kbr_query)
    all_prime_kbr_df = top_prime_kbr_df.drop_duplicates(subset=["recipient_uei"]).sort_values(by=["Prime Company"])

    st.markdown("### Top Agencies and Prime Companies")
    agency_col1, agency_col2, agency_col3 = st.columns(3)

    # First Column: Top Agencies (Prime) bar chart
    with agency_col1:
        st.markdown("**Top Agencies (Prime)**")
        if not top_agency_prime_df.empty:
            fig = px.bar(top_agency_prime_df, x="count", y="name", orientation="h", title=None, height=400)
            fig.update_layout(yaxis={'categoryorder':'total ascending'}, xaxis_title="Count", yaxis_title="Agency")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No data available.")

    # Second Column: Top Prime Companies Used bar chart
    with agency_col2:
        st.markdown("**Top Prime Companies Used**")
        if not top_prime_kbr_df.empty:
            fig = px.bar(top_prime_kbr_df, x="count", y="Prime Company", orientation="h", hover_data=["recipient_uei"], title=None, height=400)
            fig.update_layout(yaxis={'categoryorder':'total ascending'}, margin=dict(t=20))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No data available.")

    # Third Column: All Prime KBR Companies Used table
    with agency_col3:
        st.markdown("**All Prime KBR Companies**")
        sorted_prime_df = all_prime_kbr_df.sort_values(by=["Prime Company"]).reset_index(drop=True)
        st.dataframe(sorted_prime_df[["Prime Company", "recipient_uei"]], use_container_width=True)

    # --- Prepare data for Top Subcontracted Companies section ---
    top_sub_companies_query = (
        f'''
        SELECT subawardee_name AS "Subawardee Company", subawardee_uei AS "Subawardee UEI", COUNT(*) AS count
        FROM s3_processed.usaspending_subawards_kbr_issued
        WHERE subawardee_uei IS NOT NULL AND subawardee_uei != ''
        GROUP BY subawardee_name, subawardee_uei
        ORDER BY count DESC, "Subawardee Company" ASC
        LIMIT 25
        '''
    )
    top_sub_companies_df = execute_query(top_sub_companies_query)
    all_subaward_issued_simple_query = (
        f'''
        SELECT DISTINCT ON (subawardee_uei)
            subawardee_name AS "Subawardee Company",
            subawardee_uei AS "Subawardee UEI"
        FROM s3_processed.usaspending_subawards_kbr_issued
        WHERE subawardee_uei IS NOT NULL AND subawardee_uei != ''
        ORDER BY subawardee_uei, subawardee_name ASC
        '''
    )
    all_subaward_issued_simple_df = execute_query(all_subaward_issued_simple_query)
    naics_issued_query = (
        f"""
        SELECT naics_code AS "NAICS", naics_description AS "NAICS Description",
               product_or_service_code AS "PSC", product_or_service_code_description AS "PSC Description"
        FROM s3_processed.usaspending_subawards_kbr_issued
        WHERE {('subaward_action_date IS NULL OR subaward_action_date::date >= (CURRENT_DATE - INTERVAL \'60 months\')') if filters['recent_activity_months'] == 60 else '1=1'}
          AND naics_code IS NOT NULL AND naics_code != ''
          AND product_or_service_code IS NOT NULL AND product_or_service_code != ''
        GROUP BY naics_code, naics_description, product_or_service_code, product_or_service_code_description
        ORDER BY naics_code ASC, product_or_service_code ASC
        """
    )
    naics_issued_df = execute_query(naics_issued_query)

    # --- Three column layout for Top Subcontracted Companies ---
    st.markdown("### Top Subcontracted Companies")
    sub_col1, sub_col2, sub_col3 = st.columns(3)

    # 1st column: Top Sub Companies Used bar chart
    with sub_col1:
        st.markdown("**Top Sub Companies Used**")
        if not top_sub_companies_df.empty:
            fig = px.bar(top_sub_companies_df, x="count", y="Subawardee Company", orientation="h", hover_data=["Subawardee UEI"], title=None, height=400)
            fig.update_layout(yaxis={'categoryorder':'total ascending'}, margin=dict(t=20))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No data available.")

    # 2nd column: All Subcontracted Companies table
    with sub_col2:
        st.markdown("**All Subcontracted Companies**")
        sorted_sub_df = all_subaward_issued_simple_df.sort_values(by=["Subawardee Company"]).reset_index(drop=True)
        st.dataframe(sorted_sub_df[["Subawardee Company", "Subawardee UEI"]], use_container_width=True)

    # 3rd column: Unique NAICS/PSC Combinations (Issued) table
    with sub_col3:
        st.markdown("**Unique NAICS/PSC Combinations (Issued)**")
        st.dataframe(naics_issued_df, use_container_width=True)

    # --- Prepare data for Top Primes Used (KBR as sub) section ---
    top_prime_sub_query = (
        f"""
        SELECT subawardee_name AS "Prime Company", subawardee_uei AS "UEI", subawardee_parent_name AS "Parent Name", COUNT(*) AS count
        FROM s3_processed.usaspending_subawards_kbr
        WHERE {('subaward_action_date IS NULL OR subaward_action_date >= (CURRENT_DATE - INTERVAL \'60 months\')') if filters['recent_activity_months'] == 60 else '1=1'}
          AND subawardee_name IS NOT NULL AND subawardee_name != ''
        GROUP BY subawardee_name, subawardee_uei, subawardee_parent_name
        ORDER BY count DESC
        LIMIT 10
        """
    )
    top_prime_sub_df = execute_query(top_prime_sub_query)
    all_prime_sub_query = (
        f"""
        SELECT DISTINCT subawardee_name AS "Prime Company", subawardee_uei AS "UEI", subawardee_parent_name AS "Parent Name"
        FROM s3_processed.usaspending_subawards_kbr
        WHERE subawardee_name IS NOT NULL AND subawardee_name != ''
        ORDER BY "Prime Company"
        """
    )
    all_prime_sub_df = execute_query(all_prime_sub_query)

    # --- Two column layout for Top Primes Used (KBR as sub) ---
    st.markdown("### Top Primes Used (KBR as sub)")
    primesub_col1, primesub_col2 = st.columns(2)

    # 1st column: Top Prime Companies Used (KBR as Sub) bar chart
    with primesub_col1:
        st.markdown("**Top Prime Companies Used (KBR as Sub)**")
        if not top_prime_sub_df.empty:
            fig = px.bar(top_prime_sub_df, x="count", y="Prime Company", orientation="h", hover_data=["UEI", "Parent Name"], title=None, height=400)
            fig.update_layout(yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No data available.")

    # 2nd column: All Prime Companies Used (KBR as Sub) table
    with primesub_col2:
        st.markdown("**All Prime Companies Used (KBR as Sub)**")
        st.dataframe(all_prime_sub_df, use_container_width=True)

if __name__ == "__main__":
    main()

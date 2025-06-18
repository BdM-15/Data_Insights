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
    # TODO: Add visuals and tables step by step

if __name__ == "__main__":
    main()

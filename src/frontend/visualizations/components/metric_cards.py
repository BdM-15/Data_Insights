"""
metric_cards.py
Reusable KPI metric card components for the Data Insights dashboard.

Each function is modular, type-annotated, and documented for clarity.
"""

import streamlit as st
from typing import List, Dict, Any


def display_metric_cards(metrics: List[Dict[str, Any]], theme: Dict[str, Any]) -> None:
    """
    Display KPI metric cards in a row.

    Args:
        metrics: List of dicts with 'label', 'value', and optional 'delta'.
        theme: Theme dictionary for colors and styles.
    """
    # Reason: Use Streamlit columns for responsive metric display.
    cols = st.columns(len(metrics))
    for i, metric in enumerate(metrics):
        with cols[i]:
            st.metric(
                label=metric['label'],
                value=metric['value'],
                delta=metric.get('delta'),
                help=metric.get('help')
            )

def display_summary_metrics(summary: List[Any], expiring_contracts_count: int, theme: Dict[str, Any]) -> None:
    """
    Display executive summary metrics as Streamlit metric cards, styled for clarity and visual separation.

    Args:
        summary: List of AwardSummaryItem Pydantic models.
        expiring_contracts_count: Number of expiring contracts.
        theme: Theme dictionary for colors and styles.
    """
    from src.frontend.utils.formatting import format_value
    col1, col2, col3, col4, col5, col6, col7 = st.columns(7)
    summary_dict = {item.category: item for item in summary}
    with col1:
        st.metric(
            label="Total Obligations",
            value=format_value(summary_dict['total_obligations'].value, is_currency=True),
        )
    with col2:
        st.metric(
            label="Total Award Actions",
            value=format_value(summary_dict['total_award_actions'].value),
        )
    with col3:
        st.metric(
            label="Average Award Value",
            value=format_value(summary_dict['avg_award_value'].value, is_currency=True),
        )
    with col4:
        st.metric(
            label="Active Contracts",
            value=format_value(summary_dict['active_contracts'].value),
        )
    with col5:
        st.metric(
            label="Expiring Contracts",
            value=format_value(expiring_contracts_count),
            help="Number of contracts expiring in the next 6 to 24 months from today"
        )
    with col6:
        st.metric(
            label="Suitability",
            value="35%",
            help="The percentage of expiring contracts suitable for R&S based on comparing company capabilities to expiring contract descriptions"
        )
    with col7:
        st.metric(
            label="Synergy",
            value="55%",
            help="The percentage of expiring contracts suitable across MTS based on comparing company capabilities to expiring contract descriptions"
        )

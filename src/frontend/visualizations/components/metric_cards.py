"""
metric_cards.py
Reusable KPI metric card components for the Data Insights dashboard.

Each function is modular, type-annotated, and documented for clarity.
"""

import streamlit as st
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from src.frontend.styles.theme import THEME
from src.frontend.styles import custom_css

class MetricCard(BaseModel):
    """
    Pydantic model for a dashboard metric card.

    Attributes:
        label: The label/title for the metric (e.g., 'Expiring Contracts')
        value: The value to display (e.g., '9.2K', '$2.78M')
        help: Optional tooltip/help text for the label
        delta: Optional delta value for change indication
    """
    label: str
    value: str
    help: Optional[str] = None
    delta: Optional[str] = None

def display_metric_cards(metrics: List[MetricCard], theme: Dict[str, Any]) -> None:
    """
    Display KPI metric cards in a row.

    Args:
        metrics: List of MetricCard instances.
        theme: Theme dictionary for colors and styles.
    """
    # Reason: Use Streamlit columns for responsive metric display.
    cols = st.columns(len(metrics))
    for i, metric in enumerate(metrics):
        with cols[i]:
            metric_card(metric=metric)

def display_summary_metrics(summary: List[Any], expiring_contracts_count: int, theme: Dict[str, Any]) -> None:
    """
    Display executive summary metrics as Streamlit metric cards, styled for clarity and visual separation.

    Args:
        summary: List of AwardSummaryItem Pydantic models.
        expiring_contracts_count: Number of expiring contracts.
        theme: Theme dictionary for colors and styles.
    """
    from src.frontend.utils.formatting import format_value
    summary_dict = {item.category: item for item in summary}
    metrics = [
        MetricCard(
            label="Total Obligations",
            value=format_value(summary_dict['total_obligations'].value, is_currency=True)
        ),
        MetricCard(
            label="Total Award Actions",
            value=format_value(summary_dict['total_award_actions'].value)
        ),
        MetricCard(
            label="Average Award Value",
            value=format_value(summary_dict['avg_award_value'].value, is_currency=True)
        ),
        MetricCard(
            label="Active Contracts",
            value=format_value(summary_dict['active_contracts'].value)
        ),
        MetricCard(
            label="Expiring Contracts",
            value=format_value(expiring_contracts_count),
            help="Number of contracts expiring in the next 6 to 24 months from today"
        ),
        MetricCard(
            label="Suitability",
            value="35%",
            help="The percentage of expiring contracts suitable for R&S based on comparing company capabilities to expiring contract descriptions"
        ),
        MetricCard(
            label="Synergy",
            value="55%",
            help="The percentage of expiring contracts suitable across MTS based on comparing company capabilities to expiring contract descriptions"
        ),
    ]
    display_metric_cards(metrics, theme)

# Backward-compatible wrapper for legacy calls using keyword arguments
def metric_card(label: str = None, value: str = None, help_text: str = None, metric: 'MetricCard' = None):
    """
    Render a metric card with either legacy keyword arguments or a MetricCard Pydantic model.
    Args:
        label: The label/title for the metric (legacy usage)
        value: The value to display (legacy usage)
        help_text: Optional tooltip/help text for the label (legacy usage)
        metric: MetricCard instance (preferred usage)
    """
    if metric is not None:
        st.metric(label=metric.label, value=metric.value, help=metric.help, delta=metric.delta)
    else:
        st.metric(label=label, value=value, help=help_text)

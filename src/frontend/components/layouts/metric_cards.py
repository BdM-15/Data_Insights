"""
Metric card component for displaying KPIs in the dashboard.
Maintains the exact look and feel of the original cards (see dashboard screenshots).

Usage:
    from src.frontend.components.layouts.metric_cards import metric_card
    metric_card(label="Expiring Contracts", value="9.2K", help_text="Contracts expiring in the next 6-24 months")

All colors and styles are pulled from THEME and custom_css modules.
"""
import streamlit as st
from src.frontend.styles.theme import THEME
from src.frontend.styles import custom_css


def metric_card(label: str, value: str, help_text: str = None):
    """
    Render a metric card with a label, value, and optional help tooltip.
    Args:
        label: The label/title for the metric (e.g., 'Expiring Contracts')
        value: The value to display (e.g., '9.2K', '$2.78M')
        help_text: Optional tooltip/help text for the label
    """
    card_style = f"""
        background-color: {THEME['card_bg']};
        border-radius: 6px;
        border: 1.5px solid {THEME['primary']};
        padding: 0.5rem 0.5rem 0.2rem 0.5rem;
        margin-bottom: 0.5rem;
        min-width: 180px;
        max-width: 220px;
        text-align: left;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    """
    label_style = f"""
        color: {THEME['text_secondary']};
        font-size: 1rem;
        font-weight: 500;
        margin-bottom: 0.1rem;
        border-bottom: 2.5px solid {THEME['primary']};
        padding-bottom: 0.1rem;
        display: flex;
        align-items: center;
        justify-content: center;
        text-align: center;
        width: 100%;
    """
    value_style = f"""
        color: {THEME['primary']};
        font-size: 2.1rem;
        font-weight: 600;
        margin-top: 0.2rem;
        margin-bottom: 0.1rem;
        letter-spacing: 0.5px;
    """
    # Compose the label with optional help icon
    label_html = f"<span style='{label_style}'>{label}"
    if help_text:
        label_html += f" <span title='{help_text}' style='cursor:help;font-size:1rem;color:{THEME['primary']};'>&#9432;</span>"
    label_html += "</span>"
    # Render the card
    st.markdown(f"""
        <div style='{card_style}'>
            {label_html}
            <div style='{value_style}'>{value}</div>
        </div>
    """, unsafe_allow_html=True)

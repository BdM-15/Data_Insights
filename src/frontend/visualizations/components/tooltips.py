"""
tooltips.py
Reusable tooltip components for the Data Insights dashboard.

Each function is modular, type-annotated, and documented for clarity.
"""

import streamlit as st
from typing import Optional


def tooltip(text: str, help_text: Optional[str] = None) -> None:
    """
    Display a tooltip icon with optional help text.

    Args:
        text: The text to display next to the tooltip icon.
        help_text: The help text to show on hover.
    """
    # Reason: Use Streamlit's built-in help for simple tooltips.
    st.write(text, help=help_text)

"""
plotly_helpers.py
Common Plotly configuration and theme helpers for the Data Insights dashboard.

Each function is modular, type-annotated, and documented for clarity.
"""

import plotly.graph_objs as go
from typing import Dict


def apply_plotly_theme(fig: go.Figure, theme: Dict) -> None:
    """
    Apply theme settings to a Plotly figure.

    Args:
        fig: Plotly Figure object.
        theme: Theme dictionary.
    """
    # Reason: Centralize Plotly theming for consistency.
    fig.update_layout(
        font=dict(family=theme.get('font', 'sans-serif'), color=theme.get('font_color', '#FFFFFF')),
        plot_bgcolor=theme.get('plot_bgcolor', '#051B30'),
        paper_bgcolor=theme.get('paper_bgcolor', '#051B30')
    )


def format_currency_legend_label(base_label: str, value: float = None) -> str:
    """
    Format legend labels with currency values using comma separators.
    
    Args:
        base_label: Base legend label text
        value: Optional currency value to append with formatting
        
    Returns:
        Formatted legend label string
    """
    if value is not None:
        return f"{base_label} (${value:,.0f})"
    return base_label

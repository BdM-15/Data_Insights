"""
trend_charts.py
Reusable time-series and trend chart components for the Data Insights dashboard.

Each function is modular, type-annotated, and documented for clarity.
"""

import pandas as pd
import plotly.graph_objs as go
from typing import Dict, Any
from src.frontend.visualizations.utils.plotly_helpers import apply_plotly_theme


def plot_trend_chart(
    data: pd.DataFrame,
    config: Dict[str, Any],
    theme: Dict[str, Any]
) -> go.Figure:
    """
    Create a time-series trend chart.

    Args:
        data: DataFrame with 'date' and 'value' columns.
        config: Chart configuration (e.g., title, y-axis label).
        theme: Theme dictionary for colors and styles.

    Returns:
        Plotly Figure object.
    """
    # Reason: Use Plotly for interactive time-series visualization.
    fig = go.Figure()
    # Example implementation (replace with real logic):
    fig.add_trace(go.Scatter(
        x=data['date'],
        y=data['value'],
        mode='lines+markers',
        line=dict(color=theme.get('primaryColor', '#00C3FF')),
        name=config.get('series_name', 'Value')
    ))
    fig.update_layout(
        title=config.get('title', 'Trend Chart'),
        xaxis_title=config.get('xaxis_title', 'Date'),
        yaxis_title=config.get('yaxis_title', 'Value'),
        template=theme.get('plotly_template', 'plotly_dark')
    )
    return fig


def plot_quarterly_trends(
    qtr_df: pd.DataFrame,
    theme: Dict[str, Any],
    config: Dict[str, Any] = None
) -> go.Figure:
    """
    Create a dual-axis time-series chart for obligations and award actions by quarter.

    Args:
        qtr_df: DataFrame with 'quarter', 'total_obligation', 'award_count' columns.
        theme: Theme dictionary for colors and styles.
        config: Optional chart configuration (e.g., title).

    Returns:
        Plotly Figure object.
    """
    # Reason: Dual-axis for obligations and award actions trend.
    from plotly.subplots import make_subplots
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(
        go.Scatter(
            x=qtr_df["quarter"],
            y=qtr_df["total_obligation"],
            name="Obligations",
            line=dict(color=theme["primary_color"], width=3),
            mode="lines+markers",
            marker=dict(size=8, color=theme["primary_color"]),
            hovertemplate="<b>%{x}</b><br>Obligations: $%{y:,.0f}<extra></extra>"
        ),
        secondary_y=False
    )
    fig.add_trace(
        go.Scatter(
            x=qtr_df["quarter"],
            y=qtr_df["award_count"],
            name="Award Actions",
            line=dict(color=theme["accent2_color"], width=3),
            mode="lines+markers",
            marker=dict(size=8, color=theme["accent2_color"]),
            hovertemplate="<b>%{x}</b><br>Award Actions: %{y:,.0f}<extra></extra>"
        ),
        secondary_y=True
    )
    fig.update_layout(
        title=config.get("title", "Quarterly Trends") if config else "Quarterly Trends",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=40, r=40, t=40, b=40),
        plot_bgcolor=theme["bg_color"],
        paper_bgcolor=theme["bg_color"],
        font=dict(color=theme["text_color"]),
        # (Removed hovermode="x" to revert to previous behavior)
    )
    fig.update_xaxes(title_text="Fiscal Period", showgrid=True, gridcolor=theme["grid_color"], tickangle=45)
    fig.update_yaxes(title_text="Obligations ($)", secondary_y=False, showgrid=True, gridcolor=theme["grid_color"], tickprefix="$", tickformat=",.")
    fig.update_yaxes(title_text="Award Actions", secondary_y=True, showgrid=False)
    apply_plotly_theme(fig, theme)
    return fig

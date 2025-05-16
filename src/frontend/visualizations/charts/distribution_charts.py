"""
distribution_charts.py
Reusable distribution chart components (e.g., histogram, box plot) for the Data Insights dashboard.

Each function is modular, type-annotated, and documented for clarity.
"""

import pandas as pd
import plotly.graph_objs as go
import plotly.express as px
from typing import Dict, Any
from src.frontend.visualizations.utils.plotly_helpers import apply_plotly_theme


def plot_histogram(
    data: pd.DataFrame,
    config: Dict[str, Any],
    theme: Dict[str, Any]
) -> go.Figure:
    """
    Create a histogram for distribution analysis.

    Args:
        data: DataFrame with a 'value' column.
        config: Chart configuration (e.g., title, bins).
        theme: Theme dictionary for colors and styles.

    Returns:
        Plotly Figure object.
    """
    # Reason: Use Plotly for interactive distribution visualization.
    fig = go.Figure()
    fig.add_trace(go.Histogram(
        x=data['value'],
        nbinsx=config.get('bins', 20),
        marker_color=theme.get('primaryColor', '#00C3FF'),
        name=config.get('series_name', 'Value')
    ))
    fig.update_layout(
        title=config.get('title', 'Histogram'),
        xaxis_title=config.get('xaxis_title', 'Value'),
        yaxis_title=config.get('yaxis_title', 'Count'),
        template=theme.get('plotly_template', 'plotly_dark'),
        plot_bgcolor=theme.get('plot_bgcolor', '#051B30'),
        paper_bgcolor=theme.get('paper_bgcolor', '#051B30'),
        font=dict(color=theme.get('font_color', '#FFFFFF'))
    )
    return fig


def plot_capture_intensity_scatter(
    agency_df: pd.DataFrame,
    theme: Dict[str, Any],
    config: Dict[str, Any] = None
) -> go.Figure:
    """
    Create a scatter plot for capture intensity (award count vs. obligation, normalized).

    Args:
        agency_df: DataFrame with normalized award count and obligation columns.
        theme: Theme dictionary for colors and styles.
        config: Optional chart configuration (e.g., title).

    Returns:
        Plotly Figure object.
    """
    import numpy as np
    median_count = agency_df["award_count_normalized"].median()
    median_obligation = agency_df["obligation_normalized"].median()
    fig = px.scatter(
        agency_df,
        x="award_count_normalized",
        y="obligation_normalized",
        size="scatter_size",
        color="parent_award_agency_name",
        hover_name="parent_award_agency_name",
        hover_data={
            "award_count_normalized": False,
            "obligation_normalized": False,
            "award_count_original": ":.0f",
            "obligation_original": ":$.2s",
            "avg_award_value": ":$.2s"
        },
        size_max=50,
        title=config.get('title', 'Action-to-Obligation Ratio Analysis (Normalized Scale)') if config else 'Action-to-Obligation Ratio Analysis (Normalized Scale)',
        labels={
            "award_count_normalized": "Award Actions (log scale)",
            "obligation_normalized": "Obligations (log scale)",
            "avg_award_value": "Avg. Award Value"
        }
    )
    fig.add_shape(
        type="line",
        x0=median_count,
        y0=0,
        x1=median_count,
        y1=agency_df["obligation_normalized"].max() * 1.1,
        line=dict(color="White", width=1, dash="dash")
    )
    fig.add_shape(
        type="line",
        x0=0,
        y0=median_obligation,
        x1=agency_df["award_count_normalized"].max() * 1.1,
        y1=median_obligation,
        line=dict(color="White", width=1, dash="dash")
    )
    fig.add_annotation(
        x=median_count/2,
        y=median_obligation*1.5,
        text="High Value, Low Volume",
        showarrow=False,
        font=dict(color=theme["highlight_color"])
    )
    fig.add_annotation(
        x=median_count*1.5,
        y=median_obligation*1.5,
        text="High Value, High Volume",
        showarrow=False,
        font=dict(color=theme["highlight_color"])
    )
    fig.update_xaxes(showgrid=True, gridcolor=theme["grid_color"], title_text="Award Actions (log scale)")
    fig.update_yaxes(showgrid=True, gridcolor=theme["grid_color"], title_text="Obligations (log scale)")
    fig.update_layout(
        plot_bgcolor=theme["bg_color"],
        paper_bgcolor=theme["bg_color"],
        font=dict(color=theme["text_color"]),
        margin=dict(l=40, r=40, t=40, b=40),
        showlegend=False,
        title=config.get('title', 'Action-to-Obligation Ratio Analysis (Normalized Scale)') if config else 'Action-to-Obligation Ratio Analysis (Normalized Scale)'
    )
    from src.frontend.visualizations.utils.plotly_helpers import apply_plotly_theme
    apply_plotly_theme(fig, theme)
    return fig


def plot_treemap_competitive_landscape(
    treemap_df: pd.DataFrame,
    theme: Dict[str, Any],
    config: Dict[str, Any] = None
) -> go.Figure:
    """
    Create a treemap for top competitors by market share.

    Args:
        treemap_df: DataFrame with treemap data.
        theme: Theme dictionary for colors and styles.
        config: Optional chart configuration (e.g., title).

    Returns:
        Plotly Figure object.
    """
    import plotly.express as px
    fig = px.treemap(
        treemap_df,
        path=["recipient_parent_name", "recipient_name", "funding_sub_agency_name", "transaction_description"],
        values="federal_action_obligation",
        color="win_rate",
        color_continuous_scale="Viridis",
        title=config.get('title', 'Top Competitors by Market Share') if config else 'Top Competitors by Market Share',
        hover_data=["award_count", "market_share"],
    )
    fig.update_traces(
        hovertemplate="<b>%{label}</b><br>Obligations: $%{value:,.2f}<br>Market Share: %{customdata[1]:.1f}%<br>Award Count: %{customdata[0]}<extra></extra>",
        texttemplate="%{label}<br>%{customdata[1]:.1f}%",
        textfont=dict(size=11)
    )
    fig.update_layout(
        margin=dict(l=40, r=40, t=40, b=40),
        plot_bgcolor=theme.get('plot_bgcolor', '#051B30'),
        paper_bgcolor=theme.get('paper_bgcolor', '#051B30'),
        font=dict(color=theme.get('font_color', '#FFFFFF'))
    )
    apply_plotly_theme(fig, theme)
    return fig


def plot_competitive_position_scatter(
    df: pd.DataFrame,
    theme: Dict[str, Any],
    config: Dict[str, Any] = None
) -> go.Figure:
    """
    Create a scatter plot for competitive positioning (win rate vs. market share).

    Args:
        df: DataFrame with competitor data.
        theme: Theme dictionary for colors and styles.
        config: Optional chart configuration (e.g., title).

    Returns:
        Plotly Figure object.
    """
    import plotly.express as px
    median_market_share = df['market_share'].median()
    median_win_rate = df['win_rate'].median()
    fig = px.scatter(
        df,
        x='market_share',
        y='win_rate',
        size='federal_action_obligation',
        color='recipient_name',
        hover_name='recipient_name',
        title=config.get('title', 'Competitive Positioning: Win Rate vs Market Share') if config else 'Competitive Positioning: Win Rate vs Market Share',
        labels={
            'market_share': 'Market Share (%)',
            'win_rate': 'Win Rate (%)',
            'federal_action_obligation': 'Total Obligations ($)'
        },
        size_max=50
    )
    fig.add_shape(
        type="line",
        x0=median_market_share,
        y0=0,
        x1=median_market_share,
        y1=df['win_rate'].max() * 1.1,
        line=dict(color="White", width=1, dash="dash")
    )
    fig.add_shape(
        type="line",
        x0=0,
        y0=median_win_rate,
        x1=df['market_share'].max() * 1.1,
        y1=median_win_rate,
        line=dict(color="White", width=1, dash="dash")
    )
    fig.add_annotation(
        x=median_market_share/2,
        y=df['win_rate'].max() * 0.8,
        text="High Win Rate, Low Market Share",
        showarrow=False,
        font=dict(color=theme["highlight_color"])
    )
    fig.add_annotation(
        x=median_market_share*1.5,
        y=df['win_rate'].max() * 0.8,
        text="Market Leaders",
        showarrow=False,
        font=dict(color=theme["highlight_color"])
    )
    fig.add_annotation(
        x=median_market_share/2,
        y=median_win_rate/2,
        text="Struggling Competitors",
        showarrow=False,
        font=dict(color=theme["text_color"])
    )
    fig.add_annotation(
        x=median_market_share*1.5,
        y=median_win_rate/2,
        text="High Volume, Low Win Rate",
        showarrow=False,
        font=dict(color=theme["text_color"])
    )
    fig.update_traces(
        hovertemplate="<b>%{hovertext}</b><br>Market Share: %{x:.2f}%<br>Win Rate: %{y:.2f}%<br>Total Obligations: $%{marker.size:,.0f}<extra></extra>"
    )
    fig.update_layout(
        margin=dict(l=10, r=10, t=40, b=10),
        plot_bgcolor=theme.get('plot_bgcolor', '#051B30'),
        paper_bgcolor=theme.get('paper_bgcolor', '#051B30'),
        font=dict(color=theme.get('font_color', '#FFFFFF'))
    )
    apply_plotly_theme(fig, theme)
    return fig


def plot_competitor_agency_heatmap(
    normalized_pivot: pd.DataFrame,
    theme: Dict[str, Any],
    config: Dict[str, Any] = None
) -> go.Figure:
    """
    Create a heatmap for top competitor-agency relationships.

    Args:
        normalized_pivot: DataFrame (pivoted) with competitors as index and agencies as columns.
        theme: Theme dictionary for colors and styles.
        config: Optional chart configuration (e.g., title).

    Returns:
        Plotly Figure object.
    """
    import plotly.express as px
    fig = px.imshow(
        normalized_pivot,
        color_continuous_scale="Blues",
        labels=dict(x="Agency", y="Competitor", color="Relationship Strength"),
        title=config.get('title', 'Top Competitor-Agency Relationships') if config else 'Top Competitor-Agency Relationships'
    )
    fig.update_traces(
        hovertemplate="<b>%{y}</b> - <b>%{x}</b><br>Relationship Strength: %{z:.2f}<br><extra></extra>"
    )
    fig.update_layout(
        margin=dict(l=10, r=20, t=40, b=10),
        xaxis={'side': 'top'}
    )
    apply_plotly_theme(fig, theme)
    return fig

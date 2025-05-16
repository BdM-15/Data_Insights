"""
comparison_charts.py
Reusable comparison chart components (e.g., bar, stacked bar, pie) for the Data Insights dashboard.

Each function is modular, type-annotated, and documented for clarity.
"""

import pandas as pd
import plotly.graph_objs as go
import plotly.express as px
from typing import Dict, Any
from src.frontend.visualizations.utils.plotly_helpers import apply_plotly_theme


def plot_comparison_bar(
    data: pd.DataFrame,
    config: Dict[str, Any],
    theme: Dict[str, Any]
) -> go.Figure:
    """
    Create a comparison bar chart.

    Args:
        data: DataFrame with 'category' and 'value' columns.
        config: Chart configuration (e.g., title, orientation).
        theme: Theme dictionary for colors and styles.

    Returns:
        Plotly Figure object.
    """
    # Reason: Use Plotly for flexible bar chart visualizations.
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=data['category'],
        y=data['value'],
        marker_color=theme.get('primaryColor', '#00C3FF'),
        name=config.get('series_name', 'Value')
    ))
    fig.update_layout(
        title=config.get('title', 'Comparison Bar Chart'),
        xaxis_title=config.get('xaxis_title', 'Category'),
        yaxis_title=config.get('yaxis_title', 'Value'),
        template=theme.get('plotly_template', 'plotly_dark'),
        plot_bgcolor=theme.get('plot_bgcolor', '#051B30'),
        paper_bgcolor=theme.get('paper_bgcolor', '#051B30'),
        font=dict(color=theme.get('font_color', '#FFFFFF'))
    )
    return fig


def plot_top_agencies_bar(
    df: pd.DataFrame,
    value_col: str,
    label_col: str,
    theme: Dict[str, Any],
    config: Dict[str, Any] = None
) -> go.Figure:
    """
    Create a horizontal bar chart for top agencies by count or obligation, using a color scale for bars.

    Args:
        df: DataFrame with agency data.
        value_col: Column for bar values (e.g., 'award_count', 'federal_action_obligation').
        label_col: Column for agency names.
        theme: Theme dictionary for colors and styles.
        config: Optional chart configuration (e.g., title).

    Returns:
        Plotly Figure object.
    """
    import plotly.express as px
    # Use a color scale so bars get lighter as values decrease
    fig = px.bar(
        df,
        x=value_col,
        y=label_col,
        orientation="h",
        color=value_col,
        color_continuous_scale="Blues",
        labels={
            value_col: config.get('x_label', value_col.title()) if config else value_col.title(),
            label_col: config.get('y_label', label_col.title()) if config else label_col.title()
        },
        title=config.get('title', 'Top Agencies') if config else 'Top Agencies'
    )
    fig.update_layout(
        coloraxis_showscale=False,
        uniformtext_minsize=10,
        uniformtext_mode='hide',
        margin=dict(l=40, r=40, t=40, b=40),
        plot_bgcolor=theme.get('plot_bgcolor', '#051B30'),
        paper_bgcolor=theme.get('paper_bgcolor', '#051B30'),
        font=dict(color=theme.get('font_color', '#FFFFFF'))
    )
    fig.update_xaxes(showgrid=True, gridcolor=theme["grid_color"], tickformat=",.0f")
    fig.update_yaxes(showgrid=False, categoryorder="total ascending", title=None)
    fig.update_traces(texttemplate="%{x:,.0f}", textposition="outside", cliponaxis=False)
    apply_plotly_theme(fig, theme)
    return fig


def plot_top_agencies_obligation_bar(
    df: pd.DataFrame,
    theme: Dict[str, Any],
    config: Dict[str, Any] = None
) -> go.Figure:
    """
    Create a horizontal bar chart for top agencies by obligation amount, with value annotations and color scale.

    Args:
        df: DataFrame with agency data.
        theme: Theme dictionary for colors and styles.
        config: Optional chart configuration (e.g., title).

    Returns:
        Plotly Figure object.
    """
    import plotly.express as px
    from src.frontend.utils.formatting import format_value
    # Use a color scale so bars get lighter as values decrease
    fig = px.bar(
        df,
        x="federal_action_obligation",
        y="parent_award_agency_name",
        orientation="h",
        color="federal_action_obligation",
        color_continuous_scale="Blues",
        labels={
            "federal_action_obligation": "Obligation Amount ($)",
            "parent_award_agency_name": "Agency"
        },
        title=config.get('title', 'Top Agencies by Obligation Amount') if config else 'Top Agencies by Obligation Amount'
    )
    # Format value labels using format_value for currency
    formatted_labels = [format_value(val, is_currency=True) for val in df["federal_action_obligation"]]
    fig.update_traces(
        text=formatted_labels,
        texttemplate="%{text}",
        textposition="outside",
        cliponaxis=False
    )
    fig.update_layout(
        coloraxis_showscale=False,
        uniformtext_minsize=10,
        uniformtext_mode='hide',
        margin=dict(l=40, r=40, t=40, b=40),
        plot_bgcolor=theme.get('plot_bgcolor', '#051B30'),
        paper_bgcolor=theme.get('paper_bgcolor', '#051B30'),
        font=dict(color=theme.get('font_color', '#FFFFFF'))
    )
    fig.update_xaxes(showgrid=True, gridcolor=theme["grid_color"], tickprefix="$", tickformat=",.0f")
    fig.update_yaxes(showgrid=False, categoryorder="total ascending", title=None)
    apply_plotly_theme(fig, theme)
    return fig


def plot_contract_vehicle_pie(
    vehicle_df: pd.DataFrame,
    theme: Dict[str, Any],
    config: Dict[str, Any] = None
) -> go.Figure:
    """
    Create a pie chart for contract vehicle distribution.

    Args:
        vehicle_df: DataFrame with 'award_count' and 'contract_vehicle' columns.
        theme: Theme dictionary for colors and styles.
        config: Optional chart configuration (e.g., title).

    Returns:
        Plotly Figure object.
    """
    import plotly.express as px
    # Use a custom color sequence to match the original dashboard style
    color_sequence = theme.get('pie_colors', px.colors.sequential.Plasma)
    fig = px.pie(
        vehicle_df,
        values="award_count",
        names="contract_vehicle",
        title=config.get('title', 'Contract Vehicle Types') if config else 'Contract Vehicle Types',
        hole=0.4,
        color_discrete_sequence=color_sequence
    )
    fig.update_traces(
        textposition="inside",
        textinfo="percent+label",
        hoverinfo="label+percent+value"
    )
    fig.update_layout(
        margin=dict(l=40, r=40, t=40, b=40),
        plot_bgcolor=theme.get('plot_bgcolor', '#051B30'),
        paper_bgcolor=theme.get('paper_bgcolor', '#051B30'),
        font=dict(color=theme.get('font_color', '#FFFFFF'))
    )
    apply_plotly_theme(fig, theme)
    return fig


def plot_market_share_bar(
    df: pd.DataFrame,
    value_col: str,
    label_col: str,
    theme: Dict[str, Any],
    config: Dict[str, Any] = None
) -> go.Figure:
    """
    Create a horizontal bar chart for market share or win rate analysis.

    Args:
        df: DataFrame with competitor data.
        value_col: Column for bar values (e.g., 'market_share', 'win_rate').
        label_col: Column for competitor names.
        theme: Theme dictionary for colors and styles.
        config: Optional chart configuration (e.g., title, color scale).

    Returns:
        Plotly Figure object.
    """
    color_scale = config.get('color_scale', 'Blues') if config else 'Blues'
    fig = px.bar(
        df,
        x=value_col,
        y=label_col,
        orientation='h',
        color=value_col,
        color_continuous_scale=color_scale,
        labels={value_col: config.get('x_label', value_col.title()) if config else value_col.title(), label_col: config.get('y_label', label_col.title()) if config else label_col.title()},
        title=config.get('title', 'Market Share Analysis') if config else 'Market Share Analysis'
    )
    fig.update_layout(
        coloraxis_showscale=False,
        margin=dict(l=10, r=10, t=40, b=10),
        yaxis={'categoryorder': 'total ascending'},
        plot_bgcolor=theme.get('plot_bgcolor', '#051B30'),
        paper_bgcolor=theme.get('paper_bgcolor', '#051B30'),
        font=dict(color=theme.get('font_color', '#FFFFFF'))
    )
    fig.update_traces(
        texttemplate='%{x:.1f}%',
        textposition='outside',
        hovertemplate='<b>%{y}</b><br>%{x:.2f}%<extra></extra>'
    )
    apply_plotly_theme(fig, theme)
    return fig


def plot_contract_type_competition_bar(
    contract_type_competition: pd.DataFrame,
    theme: Dict[str, Any],
    config: Dict[str, Any] = None
) -> go.Figure:
    """
    Create a horizontal bar chart for competition intensity by contract type.

    Args:
        contract_type_competition: DataFrame with contract type and number of competitors.
        theme: Theme dictionary for colors and styles.
        config: Optional chart configuration (e.g., title).

    Returns:
        Plotly Figure object.
    """
    import plotly.express as px
    fig = px.bar(
        contract_type_competition,
        x='Number of Competitors',
        y='Contract Type',
        orientation='h',
        color='Number of Competitors',
        color_continuous_scale="Blues",
        labels={
            'Number of Competitors': 'Number of Unique Competitors',
            'Contract Type': 'Contract Type'
        },
        title=config.get('title', 'Competition Intensity by Contract Type') if config else 'Competition Intensity by Contract Type'
    )
    fig.update_layout(
        coloraxis_showscale=False,
        margin=dict(l=10, r=10, t=40, b=10),
        yaxis={'categoryorder': 'total ascending'},
        plot_bgcolor=theme.get('plot_bgcolor', '#051B30'),
        paper_bgcolor=theme.get('paper_bgcolor', '#051B30'),
        font=dict(color=theme.get('font_color', '#FFFFFF'))
    )
    fig.update_traces(
        texttemplate='%{x:.0f}',
        textposition='outside',
        hovertemplate='<b>%{y}</b><br>Competitors: %{x:.0f}<extra></extra>'
    )
    apply_plotly_theme(fig, theme)
    return fig


def plot_contract_type_value_analysis(
    top_value_types: pd.DataFrame,
    theme: Dict[str, Any],
    config: Dict[str, Any] = None
) -> go.Figure:
    """
    Create a dual-axis bar and line chart for contract type value analysis.

    Args:
        top_value_types: DataFrame with contract type, total obligation, and average obligation.
        theme: Theme dictionary for colors and styles.
        config: Optional chart configuration (e.g., title).

    Returns:
        Plotly Figure object.
    """
    from plotly.subplots import make_subplots
    import plotly.graph_objs as go
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(
        go.Bar(
            x=top_value_types['Contract Type'],
            y=top_value_types['Total Obligation'],
            name='Total Obligation',
            marker_color=theme["primary_color"]
        ),
        secondary_y=False
    )
    fig.add_trace(
        go.Scatter(
            x=top_value_types['Contract Type'],
            y=top_value_types['Average Obligation'],
            name='Avg Obligation per Competitor',
            mode='lines+markers',
            marker=dict(color=theme["accent2_color"]),
            line=dict(width=3)
        ),
        secondary_y=True
    )
    fig.update_layout(
        title_text=config.get('title', 'Contract Type Value Analysis') if config else 'Contract Type Value Analysis',
        margin=dict(l=10, r=10, t=40, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        plot_bgcolor=theme.get('plot_bgcolor', '#051B30'),
        paper_bgcolor=theme.get('paper_bgcolor', '#051B30'),
        font=dict(color=theme.get('font_color', '#FFFFFF'))
    )
    fig.update_xaxes(title_text="Contract Type", tickangle=45)
    fig.update_yaxes(title_text="Total Obligation ($)", secondary_y=False, tickprefix="$", tickformat=",.")
    fig.update_yaxes(title_text="Avg Obligation per Competitor ($)", secondary_y=True, tickprefix="$", tickformat=",.")
    apply_plotly_theme(fig, theme)
    return fig

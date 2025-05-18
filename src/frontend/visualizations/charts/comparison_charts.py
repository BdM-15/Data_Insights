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
    Create a horizontal bar chart for competition intensity by contract type, with hover for long names.

    Args:
        contract_type_competition: DataFrame with contract type and number of competitors.
        theme: Theme dictionary for colors and styles.
        config: Optional chart configuration (e.g., title, hover_col).

    Returns:
        Plotly Figure object.
    """
    import plotly.express as px
    hover_col = config.get('hover_col', None) if config else None
    y_col = 'Contract Type Display' if 'Contract Type Display' in contract_type_competition.columns else 'Contract Type'
    # Add COMBINATION logic for display and hover
    contract_type_competition = contract_type_competition.copy()
    contract_type_competition['Contract Type Display'] = contract_type_competition['Contract Type Display'].apply(
        lambda x: 'COMBINATION' if x.startswith('COMBINATION') else x
    ) if 'Contract Type Display' in contract_type_competition.columns else contract_type_competition['Contract Type']
    contract_type_competition['Contract Type Hover'] = contract_type_competition.apply(
        lambda row: row['Contract Type Hover'] if row['Contract Type Display'] == 'ORDER DEPENDENT' else (
            row['Contract Type'][row['Contract Type'].find('(')+1:row['Contract Type'].find(')')] if row['Contract Type'].startswith('COMBINATION') and '(' in row['Contract Type'] and ')' in row['Contract Type'] else ''
        ), axis=1
    )
    fig = px.bar(
        contract_type_competition,
        x='Number of Competitors',
        y='Contract Type Display',
        orientation='h',
        color='Number of Competitors',
        color_continuous_scale="Blues",
        labels={
            'Number of Competitors': 'Number of Unique Competitors',
            'Contract Type Display': 'Contract Type'
        },
        title=config.get('title', 'Competition Intensity by Contract Type') if config else 'Competition Intensity by Contract Type',
        hover_data=["Contract Type Hover"]
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
        hovertemplate='<b>%{y}</b><br>%{customdata[0]}<br>Competitors: %{x:.0f}<extra></extra>'
    )
    apply_plotly_theme(fig, theme)
    return fig


def plot_contract_type_value_analysis(
    top_value_types: pd.DataFrame,
    theme: Dict[str, Any],
    config: Dict[str, Any] = None
) -> go.Figure:
    """
    Create a dual-axis bar and line chart for contract type value analysis, with hover for long names and label replacement for EPA.

    Args:
        top_value_types: DataFrame with contract type, total obligation, and average obligation.
        theme: Theme dictionary for colors and styles.
        config: Optional chart configuration (e.g., title, hover_col).

    Returns:
        Plotly Figure object.
    """
    from plotly.subplots import make_subplots
    import plotly.graph_objs as go
    hover_col = config.get('hover_col', None) if config else None
    x_col = 'Contract Type Display' if 'Contract Type Display' in top_value_types.columns else 'Contract Type'
    # Always replace any variant of 'FIXED PRICE WITH ECONOMIC PRICE ADJUSMENT' or 'ADJUSTMENT' with 'FIXED PRICE WITH EPA'
    top_value_types = top_value_types.copy()
    top_value_types[x_col] = top_value_types[x_col].replace({
        'FIXED PRICE WITH ECONOMIC PRICE ADJUSTMENT': 'FIXED PRICE WITH EPA',
    })
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(
        go.Bar(
            x=top_value_types[x_col],
            y=top_value_types['Total Obligation'],
            name='Total Obligation',
            marker_color=theme["primary_color"],
            customdata=top_value_types[[hover_col]].values if hover_col else None,
            hovertemplate='<b>%{x}</b><br>%{customdata[0]}<br>Total Obligation: $%{y:,.0f}<extra></extra>' if hover_col else '<b>%{x}</b><br>Total Obligation: $%{y:,.0f}<extra></extra>'
        ),
        secondary_y=False
    )
    fig.add_trace(
        go.Scatter(
            x=top_value_types[x_col],
            y=top_value_types['Average Obligation'],
            name='Avg Obligation per Competitor',
            mode='lines+markers',
            marker=dict(color=theme["accent2_color"]),
            line=dict(width=3),
            customdata=top_value_types[[hover_col]].values if hover_col else None,
            hovertemplate='<b>%{x}</b><br>%{customdata[0]}<br>Avg Obligation: $%{y:,.0f}<extra></extra>' if hover_col else '<b>%{x}</b><br>Avg Obligation: $%{y:,.0f}<extra></extra>'
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
        config: Optional chart configuration (e.g., title, height, legend_font_size).

    Returns:
        Plotly Figure object.
    """
    import plotly.express as px
    height = config.get('height', 600) if config else 600
    legend_font_size = config.get('legend_font_size', 14) if config else 14
    fig = px.imshow(
        normalized_pivot,
        color_continuous_scale="Blues",
        labels=dict(x="Agency", y="Competitor", color="Relationship Strength"),
        aspect="auto",
        height=height
    )
    # Remove any layout title forcibly (handles px.imshow bug)
    fig.update_layout(title=None, title_text=None)
    if hasattr(fig.layout, 'title'):
        fig.layout.title.text = ''
    fig.update_traces(
        hovertemplate="<b>%{y}</b> - <b>%{x}</b><br>Relationship Strength: %{z:.2f}<br><extra></extra>"
    )
    fig.update_layout(
        margin=dict(l=10, r=20, t=40, b=10),
        xaxis={'side': 'top', 'tickangle': 45, 'automargin': True, 'tickfont': dict(size=14)},
        yaxis={'automargin': True, 'tickfont': dict(size=14)},
        autosize=True,
        width=None,  # Let Streamlit/Plotly handle responsive width
        coloraxis_colorbar=dict(
            title="Relationship Strength",
            orientation="v",
            x=1.02,
            y=0.5,
            len=0.8,
            thickness=20,
            tickfont=dict(size=legend_font_size),
            titlefont=dict(size=legend_font_size)
        ),
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
        hovertemplate=None  # Use default Plotly Express hover behavior
    )
    fig.update_layout(
        margin=dict(l=10, r=10, t=40, b=10),
        plot_bgcolor=theme.get('plot_bgcolor', '#051B30'),
        paper_bgcolor=theme.get('paper_bgcolor', '#051B30'),
        font=dict(color=theme.get('font_color', '#FFFFFF')),
    )
    from src.frontend.visualizations.utils.plotly_helpers import apply_plotly_theme
    apply_plotly_theme(fig, theme)
    # Restore default legend behavior (do not forcibly remove legend)
    return fig

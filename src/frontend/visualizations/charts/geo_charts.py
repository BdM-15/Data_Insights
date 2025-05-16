"""
geo_charts.py
Reusable geographic chart components (e.g., choropleth, scatter map) for the Data Insights dashboard.

Each function is modular, type-annotated, and documented for clarity.
"""

import pandas as pd
import plotly.graph_objs as go
from typing import Dict, Any


def plot_choropleth_map(
    data: pd.DataFrame,
    config: Dict[str, Any],
    theme: Dict[str, Any]
) -> go.Figure:
    """
    Create a choropleth map for geographic data visualization.

    Args:
        data: DataFrame with 'location' and 'value' columns.
        config: Chart configuration (e.g., title, geojson, locationmode).
        theme: Theme dictionary for colors and styles.

    Returns:
        Plotly Figure object.
    """
    # Reason: Use Plotly for interactive geographic visualization.
    fig = go.Figure(go.Choropleth(
        locations=data['location'],
        z=data['value'],
        locationmode=config.get('locationmode', 'USA-states'),
        colorscale=theme.get('colorscale', 'Blues'),
        colorbar_title=config.get('colorbar_title', 'Value')
    ))
    fig.update_layout(
        title=config.get('title', 'Choropleth Map'),
        geo_scope=config.get('geo_scope', 'usa'),
        template=theme.get('plotly_template', 'plotly_dark'),
        plot_bgcolor=theme.get('plot_bgcolor', '#051B30'),
        paper_bgcolor=theme.get('paper_bgcolor', '#051B30'),
        font=dict(color=theme.get('font_color', '#FFFFFF'))
    )
    return fig

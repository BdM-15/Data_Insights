"""
Plotly theme and color utilities for Data Insights dashboards.
Defines a vibrant, on-brand color palette and chart style settings for consistent visuals.
"""
from .theme import THEME

# Vibrant color palette for bar charts (distinct, accessible, and on-brand)
VIBRANT_BAR_COLORS = [
    THEME['primary'],
    THEME['highlight_color'],
    THEME['accent1_color'],
    THEME['accent2_color'],
    THEME['projection_obligations'],
    THEME['projection_awards'],
    THEME['projection_market'],
    '#FF5A36',  # Vivid red-orange
    '#A259F7',  # Purple
    '#43E97B',  # Green gradient
    '#F9CB40',  # Gold
    '#F97B22',  # Orange
    THEME['text_secondary'],
]

def get_vibrant_bar_colors(n: int):
    """
    Get a list of vibrant bar colors for Plotly charts, cycling if n > palette length.
    Args:
        n: Number of bars (categories)
    Returns:
        List of color hex codes
    """
    if n <= len(VIBRANT_BAR_COLORS):
        return VIBRANT_BAR_COLORS[:n]
    return [VIBRANT_BAR_COLORS[i % len(VIBRANT_BAR_COLORS)] for i in range(n)]

PLOTLY_CHART_STYLE = {
    'plot_bgcolor': THEME['bg_color'],
    'paper_bgcolor': THEME['bg_color'],
    'font_color': THEME['text_color'],
    'margin': dict(l=40, r=40, t=40, b=40)
}

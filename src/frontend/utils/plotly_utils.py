"""
Plotly chart utilities for Data Insights dashboards.
Provides color palettes and helper functions for consistent, vibrant visuals.
"""
from typing import List

# Vibrant color palette for bar charts (distinct, accessible, and on-brand)
VIBRANT_BAR_COLORS: List[str] = [
    "#00C3FF",  # Electric blue (primary)
    "#38ECFF",  # Bright cyan (highlight)
    "#5271FF",  # Electric indigo (accent1)
    "#FF2EDF",  # Electric pink/magenta (accent2)
    "#FFD700",  # Bright yellow
    "#FF8C00",  # Bright orange
    "#00FF7F",  # Vibrant green
    "#FF5A36",  # Vivid red-orange
    "#A259F7",  # Purple
    "#43E97B",  # Green gradient
    "#F9CB40",  # Gold
    "#F97B22",  # Orange
    "#B8D8F8",  # Light blue (secondary text)
]

def get_vibrant_bar_colors(n: int) -> List[str]:
    """
    Get a list of vibrant bar colors for Plotly charts, cycling if n > palette length.
    Args:
        n: Number of bars (categories)
    Returns:
        List of color hex codes
    """
    if n <= len(VIBRANT_BAR_COLORS):
        return VIBRANT_BAR_COLORS[:n]
    # Cycle colors if more bars than palette
    return [VIBRANT_BAR_COLORS[i % len(VIBRANT_BAR_COLORS)] for i in range(n)]

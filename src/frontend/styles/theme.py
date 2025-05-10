"""
Theme configuration for Data_Insights application.

This module provides centralized theme settings for consistent styling across the application.
"""

# Define theme colors
THEME = {
    'bg_color': '#051B30',         # Deep navy background
    'primary_color': '#00C3FF',    # Electric blue for primary elements
    'highlight_color': '#38ECFF',  # Bright cyan for highlights
    'accent1_color': '#5271FF',    # Electric indigo
    'accent2_color': '#FF2EDF',    # Electric pink/magenta
    'text_color': '#FFFFFF',       # White text
    'grid_color': 'rgba(0,195,255,0.15)' # Subtle electric blue grid lines
}

# Chart color palettes
COLOR_SCALES = {
    'blues': ['#00C3FF', '#5271FF', '#0057FF', '#003CB2', '#00205F'],
    'cyberpunk': ['#00C3FF', '#FF2EDF', '#38ECFF', '#5271FF', '#FF9E00'],
    'diverging': ['#00C3FF', '#38ECFF', '#FFFFFF', '#FF2EDF', '#FF9E00'],
}

# Chart defaults for consistent styling
CHART_DEFAULTS = {
    'plot_bgcolor': THEME['bg_color'],
    'paper_bgcolor': THEME['bg_color'],
    'font_color': THEME['text_color'],
    'grid_color': THEME['grid_color'],
    'margin': dict(l=40, r=40, t=40, b=40),
}

# Font settings
FONTS = {
    'title': dict(family="sans-serif", size=20, color=THEME['primary_color']),
    'subtitle': dict(family="sans-serif", size=16, color=THEME['highlight_color']),
    'body': dict(family="sans-serif", size=14, color=THEME['text_color']),
    'small': dict(family="sans-serif", size=12, color=THEME['text_color']),
}

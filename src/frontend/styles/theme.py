"""
Theme configuration for Data Insights Streamlit dashboards.

Defines color palette and style constants for consistent theming.
"""

THEME = {
    'bg_color': '#051B30',         # Deep navy background
    'primary': '#00C3FF',          # Electric blue for primary elements (for UI consistency)
    'primary_color': '#00C3FF',    # Electric blue for primary elements (legacy)
    'highlight_color': '#38ECFF',  # Bright cyan for highlights
    'accent1_color': '#5271FF',    # Electric indigo
    'accent2_color': '#FF2EDF',    # Electric pink/magenta
    'text_color': '#FFFFFF',       # White text
    'grid_color': 'rgba(0,195,255,0.15)', # Subtle electric blue grid lines
    'card_bg': '#0A223A',          # Card background (matches dashboard cards)
    'text_secondary': '#B8D8F8',   # Secondary text for card labels
    
    # Projection chart colors
    'projection_obligations': '#FFD700',  # Bright yellow for projected obligations
    'projection_awards': '#FF8C00',       # Bright orange for projected award actions
    'projection_market': '#00FF7F'        # Vibrant green for potential market share
}

# Chart settings for Plotly/Streamlit
CHART_SETTINGS = {
    'plot_bgcolor': THEME['bg_color'],
    'paper_bgcolor': THEME['bg_color'],
    'font_color': THEME['text_color'],
    'margin': dict(l=40, r=40, t=40, b=40)
}

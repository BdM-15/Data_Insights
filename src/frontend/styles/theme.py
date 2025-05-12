"""
Theme configuration for Data_Insights application.

This module provides centralized theme settings for consistent styling across the application.
"""

# Define theme colors
THEME = {
    # Primary Colors
    'bg_color': '#010A14',         # Extremely dark navy (almost black) for main background
    'primary_color': '#00C3FF',    # Electric blue for primary elements
    'highlight_color': '#38ECFF',  # Bright cyan for highlights
    'accent1_color': '#5271FF',    # Electric indigo
    'accent2_color': '#FF2EDF',    # Electric pink/magenta
    'text_color': '#FFFFFF',       # White text
    
    # Secondary/UI Colors
    'sidebar_bg': '#051B30',       # Dark navy for UI elements (slightly lighter than bg)
    'secondary_bg': '#051B30',     # Same dark navy for consistency
    'chart_bg': '#051B30',         # Match sidebar color for all UI elements
    'card_bg': '#051B30',          # Match sidebar color for all UI elements
    'tab_container_bg': '#010A14', # Match main background
    'grid_color': 'rgba(0,195,255,0.15)', # Subtle electric blue grid lines
    'separator': 'rgba(0,195,255,0.3)',   # Color for separators and borders (increased opacity for better visibility)
    'muted_text': 'rgba(255,255,255,0.7)', # Lower emphasis text
    
    # Status Colors
    'success': '#00E676',          # Green for success indicators
    'warning': '#FFAB00',          # Amber for warnings
    'danger': '#FF5252',           # Red for errors/important notices
    'info': '#00C3FF',             # Blue for information
}

# Chart color palettes
COLOR_SCALES = {
    'blues': ['#00C3FF', '#5271FF', '#0057FF', '#003CB2', '#00205F'],
    'cyberpunk': ['#00C3FF', '#FF2EDF', '#38ECFF', '#5271FF', '#FF9E00'],
    'diverging': ['#00C3FF', '#38ECFF', '#FFFFFF', '#FF2EDF', '#FF9E00'],
    
    # Chart-specific palettes
    'obligations': '#00C3FF',      # Blue for obligation values in trend charts
    'awards': '#FF2EDF',           # Pink for award actions in trend charts
}

# Chart defaults for consistent styling
CHART_DEFAULTS = {
    'plot_bgcolor': THEME['chart_bg'],
    'paper_bgcolor': THEME['chart_bg'],
    'font_color': THEME['text_color'],
    'grid_color': THEME['grid_color'],
    'margin': dict(l=40, r=40, t=40, b=40),
    'colorway': COLOR_SCALES['cyberpunk'],
    'xaxis': {
        'gridcolor': THEME['grid_color'],
        'zerolinecolor': THEME['separator'],
        'showgrid': True,
        'gridwidth': 1
    },
    'yaxis': {
        'gridcolor': THEME['grid_color'],
        'zerolinecolor': THEME['separator'],
        'showgrid': True,
        'gridwidth': 1
    }
}

# Chart-specific settings (to exactly match the screenshot)
CHART_TYPES = {
    'trend_line': {
        'line_width': 3,
        'marker_size': 8,
        'obligations_color': COLOR_SCALES['obligations'],
        'awards_color': COLOR_SCALES['awards'],
        'gridlines': {
            'x': True, 
            'y': True, 
            'color': THEME['grid_color'],
            'width': 1
        }
    },
    'scatter': {
        'marker_size': 15,
        'opacity': 0.7,
        'gridlines': {
            'x': True, 
            'y': True,
            'color': THEME['grid_color'],
            'width': 1
        }
    },
    'bar': {
        'bar_thickness': 0.5,  # 1 = full width, 0.5 = half width
        'gridlines': {
            'x': False, 
            'y': True,
            'color': THEME['grid_color'],
            'width': 1
        }
    }
}

# Font settings
FONTS = {
    'title': dict(family="sans-serif", size=20, color=THEME['primary_color']),
    'subtitle': dict(family="sans-serif", size=16, color=THEME['highlight_color']),
    'body': dict(family="sans-serif", size=14, color=THEME['text_color']),
    'small': dict(family="sans-serif", size=12, color=THEME['text_color']),
}

# Space/layout values for consistent spacing
SPACING = {
    'section_margin': '2rem 0',
    'card_padding': '1.5rem',
    'item_margin': '1rem',
    'border_radius': '8px',
}

# Element-specific styling that needs to be consistent
ELEMENTS = {
    'card': {
        'box_shadow': '0 4px 8px rgba(0, 0, 0, 0.2)',
        'border_radius': SPACING['border_radius'],
        'border': f"1px solid {THEME['separator']}",
    },
    'metric': {
        'border_left': f"4px solid {THEME['primary_color']}",
        'border_radius': SPACING['border_radius'],
    },
    'button': {
        'border_radius': '6px',
        'padding': '0.5rem 1rem',
        'bg_color': THEME['primary_color'],
        'text_color': THEME['bg_color'],
        'hover_bg': THEME['accent1_color'],
    }
}

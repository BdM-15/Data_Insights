"""
Reusable custom CSS functions for Data Insights Streamlit dashboards.

Provides utilities to inject theme-based CSS into Streamlit apps.
"""

def generate_theme_css(theme: dict) -> str:
    """
    Generate a CSS string for the Streamlit app based on the provided theme dict.

    Args:
        theme: Dictionary of theme color values
    Returns:
        CSS string
    """
    return f"""
    <style>
        .main .block-container {{
            padding-top: 1rem;
            padding-bottom: 1rem;
        }}
        h1, h2, h3, h4, h5, h6 {{
            color: {theme['primary_color']};
        }}
        .stTabs [data-baseweb="tab-list"] {{
            gap: 2px;
        }}
        .stTabs [data-baseweb="tab"] {{
            background-color: {theme['bg_color']};
            border-radius: 8px 8px 0px 0px;
            color: {theme['text_color']};
            padding: 15px 25px;
            font-size: 16px;
            min-width: 160px;
            text-align: center;
        }}
        .stTabs [aria-selected="true"] {{
            background-color: {theme['primary_color']};
            color: {theme['bg_color']};
            font-weight: bold;
        }}
        .stTabs [data-baseweb="tab"] {{
            box-shadow: 0 -3px 5px rgba(0, 0, 0, 0.1);
            transition: all 0.2s ease;
        }}
        .stTabs [data-baseweb="tab"]:hover:not([aria-selected="true"]) {{
            background-color: rgba(0, 195, 255, 0.1);
            transform: translateY(-2px);
        }}
        [data-testid="stMetricValue"] {{
            background-color: {theme['bg_color']};
            border-radius: 8px 8px 0px 0px;
            padding: 10px 5px 0px 5px;
            color: {theme['highlight_color']};
            width: 100%;
            text-align: center;
            font-size: 2rem;
        }}
        [data-testid="stMetricLabel"] {{
            background-color: {theme['bg_color']};
            border-radius: 0px 0px 8px 8px;
            padding: 0px 5px 10px 5px;
            color: {theme['text_color']};
            width: 100%;
            text-align: center;
            border-bottom: 4px solid {theme['primary_color']};
        }}
        [data-testid="metric-container"] {{
            background-color: {theme['bg_color']};
            box-shadow: 0px 4px 8px rgba(0, 0, 0, 0.4);
            border-radius: 8px;
            margin: 0px 3px;
            border-left: 4px solid {theme['primary_color']};
            border-right: 1px solid rgba(0, 195, 255, 0.2);
            border-top: 1px solid rgba(0, 195, 255, 0.2);
            border-bottom: 1px solid rgba(0, 195, 255, 0.2);
        }}
        div[data-testid="stMetricDelta"] {{
            text-align: center;
            width: 100%;
            background-color: {theme['bg_color']};
        }}
        [data-testid="stSidebar"] {{
            background-color: {theme['bg_color']};
            border-right: 1px solid rgba(0, 195, 255, 0.1);
        }}
        .sidebar-nav {{
            padding: 0.5rem 0;
            margin-bottom: 1rem;
        }}
        .sidebar-nav-item {{
            padding: 0.5rem 1rem;
            border-radius: 4px;
            margin-bottom: 0.25rem;
            display: block;
            color: {theme['text_color']};
            text-decoration: none;
            transition: background-color 0.2s;
        }}
        .sidebar-nav-item:hover {{
            background-color: rgba(0, 195, 255, 0.1);
        }}
        .sidebar-nav-item.active {{
            background-color: {theme['primary_color']};
            color: {theme['bg_color']};
        }}
        .user-section {{
            border-top: 1px solid rgba(0, 195, 255, 0.1);
            padding-top: 1rem;
            margin-top: 1rem;
        }}
    </style>
    """

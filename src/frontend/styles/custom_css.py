"""
Custom CSS functions for Data_Insights application.

This module provides reusable CSS generators for consistent styling across the application.
"""

from src.frontend.styles.theme import THEME

def get_base_css():
    """
    Returns the base CSS for the application.
    
    Returns:
        str: Base CSS styles
    """
    return f"""
    <style>
        .main .block-container {{
            padding-top: 1rem;
            padding-bottom: 1rem;
        }}
        h1, h2, h3, h4, h5, h6 {{
            color: {THEME['primary_color']};
        }}
    </style>
    """

def get_tabs_css():
    """
    Returns the CSS for styling tabs.
    
    Returns:
        str: CSS for tabs
    """
    return f"""
    <style>
        .stTabs [data-baseweb="tab-list"] {{
            gap: 2px;
        }}
        .stTabs [data-baseweb="tab"] {{
            background-color: {THEME['bg_color']};
            border-radius: 8px 8px 0px 0px;
            color: {THEME['text_color']};
            padding: 15px 25px;  /* Increased padding for larger tabs */
            font-size: 16px;     /* Larger font size */
            min-width: 160px;    /* Minimum width for each tab */
            text-align: center;
        }}
        .stTabs [aria-selected="true"] {{
            background-color: {THEME['primary_color']};
            color: {THEME['bg_color']};
            font-weight: bold;
        }}
        /* Make the tabs more prominent with a subtle box shadow */
        .stTabs [data-baseweb="tab"] {{
            box-shadow: 0 -3px 5px rgba(0, 0, 0, 0.1);
            transition: all 0.2s ease;
        }}
        /* Add a hover effect */
        .stTabs [data-baseweb="tab"]:hover:not([aria-selected="true"]) {{
            background-color: rgba(0, 195, 255, 0.1);
            transform: translateY(-2px);
        }}
    </style>
    """

def get_metric_css():
    """
    Returns the CSS for styling metric components.
    
    Returns:
        str: CSS for metric components
    """
    return f"""
    <style>
        /* Metric card styling with solid background */
        [data-testid="stMetricValue"] {{
            background-color: {THEME['bg_color']}; 
            border-radius: 8px 8px 0px 0px;
            padding: 10px 5px 0px 5px;
            color: {THEME['highlight_color']};
            width: 100%;
            text-align: center;
            font-size: 2rem;
        }}
        
        [data-testid="stMetricLabel"] {{
            background-color: {THEME['bg_color']};
            border-radius: 0px 0px 8px 8px;
            padding: 0px 5px 10px 5px;
            color: {THEME['text_color']};
            width: 100%;
            text-align: center;
            border-bottom: 4px solid {THEME['primary_color']};
        }}
        
        /* Add box shadow and border styling to the whole metric container */
        [data-testid="metric-container"] {{
            background-color: {THEME['bg_color']};
            box-shadow: 0px 4px 8px rgba(0, 0, 0, 0.4);
            border-radius: 8px;
            margin: 0px 3px;
            border-left: 4px solid {THEME['primary_color']};
            border-right: 1px solid rgba(0, 195, 255, 0.2);
            border-top: 1px solid rgba(0, 195, 255, 0.2);
            border-bottom: 1px solid rgba(0, 195, 255, 0.2);
        }}

        /* Handle delta values styling */
        div[data-testid="stMetricDelta"] {{
            text-align: center;
            width: 100%;
            background-color: {THEME['bg_color']};
        }}
    </style>
    """

def get_sidebar_css():
    """
    Returns the CSS for styling sidebar components.
    
    Returns:
        str: CSS for sidebar components
    """
    return f"""
    <style>
        /* Style the sidebar */
        [data-testid="stSidebar"] {{
            background-color: {THEME['bg_color']};
            border-right: 1px solid rgba(0, 195, 255, 0.1);
        }}
        /* Style sidebar navigation links */
        .sidebar-nav {{
            padding: 0.5rem 0;
            margin-bottom: 1rem;
        }}
        .sidebar-nav-item {{
            padding: 0.5rem 1rem;
            border-radius: 4px;
            margin-bottom: 0.25rem;
            display: block;
            color: {THEME['text_color']};
            text-decoration: none;
            transition: background-color 0.2s;
        }}
        .sidebar-nav-item:hover {{
            background-color: rgba(0, 195, 255, 0.1);
        }}
        .sidebar-nav-item.active {{
            background-color: {THEME['primary_color']};
            color: {THEME['bg_color']};
        }}
        /* User section */
        .user-section {{
            border-top: 1px solid rgba(0, 195, 255, 0.1);
            padding-top: 1rem;
            margin-top: 1rem;
        }}
    </style>
    """

def get_all_css():
    """
    Returns all CSS styles combined.
    
    Returns:
        str: All CSS styles
    """
    return get_base_css() + get_tabs_css() + get_metric_css() + get_sidebar_css()

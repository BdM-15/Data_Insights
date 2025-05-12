"""
Custom CSS functions for Data_Insights application.

This module provides reusable CSS generators for consistent styling across the application.
"""

from src.frontend.styles.theme import THEME, FONTS, SPACING, ELEMENTS

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
        
        /* Style dashboard cards and sections with clean separation */
        .stButton {{
            background-color: {THEME['card_bg']};
            border-radius: 6px;
            padding: 2px;
        }}
        
        /* Style Streamlit card elements - simple background */
        [data-testid="stCard"] {{
            background-color: {THEME['card_bg']} !important;
        }}        /* Chart container styling - match sidebar background */
        [data-testid="stMetric"], 
        .stPlotlyChart,
        div[data-testid*="stPlotly"] {{
            background-color: {THEME['sidebar_bg']} !important;
        }}
        
        /* Make sure overlay elements have proper contrast */
        .plotly-graph-div .bg,
        .plotly-graph-div .main-svg {{
            background-color: {THEME['sidebar_bg']} !important;
        }}
        
        /* Ensure legends and modebar have contrast */
        .plotly-graph-div .legend,
        .plotly-graph-div .modebar-container,
        .plotly-graph-div .modebar {{
            background-color: rgba(22, 45, 69, 0.8) !important;
        }}
        
        /* Make sure annotation texts are visible */
        .plotly-graph-div .annotation-text {{
            fill: #FFFFFF !important;
        }}
        
        /* Set padding and margins */
        .stPlotlyChart {{
            padding: 5px;
            margin-bottom: 1rem;
        }}
        
        /* Make select boxes stand out from background */
        div.stSelectbox > div[data-baseweb="select"] > div {{
            background-color: {THEME['secondary_bg']} !important;
            border-radius: 4px;
        }}
          /* Apply secondary background to other input elements */
        div.stDateInput > div[data-baseweb="input"] > div,
        div.stNumberInput > div[data-baseweb="input"] > div,
        div.stTextInput > div[data-baseweb="input"] > div {{
            background-color: {THEME['secondary_bg']} !important;
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
        /* Style the overall tabs container */
        .stTabs {{
            background-color: {THEME['bg_color']};
        }}
        
        .stTabs [data-baseweb="tab-list"] {{
            gap: 2px;
            background-color: {THEME['bg_color']};
        }}
        
        /* Force tab containers to use the main background color */
        div[class*="stTabContent"] {{
            background-color: {THEME['bg_color']} !important;
        }}
          .stTabs [data-baseweb="tab"] {{
            background-color: {THEME['sidebar_bg']};
            border-radius: 4px 4px 0px 0px;
            border: none;
            color: {THEME['text_color']};
            padding: 10px 20px;
            min-width: 140px;
            text-align: center;
        }}
        
        .stTabs [aria-selected="true"] {{
            background-color: {THEME['primary_color']};
            color: {THEME['bg_color']};
            font-weight: bold;
        }}
          /* Tab content container */
        .stTabs [data-baseweb="tab-panel"] {{
            background-color: {THEME['bg_color']};
            padding: 5px;
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
            background-color: {THEME['sidebar_bg']}; 
            border-radius: 8px 8px 0px 0px;
            padding: 10px 5px 0px 5px;
            color: {THEME['highlight_color']};
            width: 100%;
            text-align: center;
            font-size: 2rem;
        }}
        
        [data-testid="stMetricLabel"] {{
            background-color: {THEME['sidebar_bg']};
            border-radius: 0px 0px 8px 8px;
            padding: 0px 5px 10px 5px;
            color: {THEME['text_color']};
            width: 100%;
            text-align: center;
            border-bottom: 4px solid {THEME['primary_color']};
        }}
        
        /* Add box shadow and border styling to the whole metric container */
        [data-testid="metric-container"] {{
            background-color: {THEME['sidebar_bg']};
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
            background-color: {THEME['sidebar_bg']};
        }}
        
        /* Enhance visibility of delta values */
        div[data-testid="stMetricDelta"] > div {{
            background-color: {THEME['sidebar_bg']} !important;
            font-weight: bold;
        }}
        
        /* Style positive delta values */
        div[data-testid="stMetricDelta"] > div:has(svg[style*="green"]) {{
            color: {THEME['success']} !important;
            text-shadow: 0 0 5px rgba(0, 230, 118, 0.3);
        }}
        
        /* Style negative delta values */
        div[data-testid="stMetricDelta"] > div:has(svg[style*="red"]) {{
            color: {THEME['danger']} !important;
            text-shadow: 0 0 5px rgba(255, 82, 82, 0.3);
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
            background-color: {THEME['sidebar_bg']};
            border-right: 1px solid {THEME['separator']};
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

def get_chart_css():
    """
    Returns the CSS for styling chart containers.
    
    Returns:
        str: CSS for chart containers
    """
    return f"""
    <style>
        /* Clean chart containers matching sidebar/metrics color */
        .chart-container {{
            background-color: {THEME['sidebar_bg']};
            padding: 15px;
            margin-bottom: {SPACING['item_margin']};
        }}
          /* Clean chart title styling */
        .chart-title {{
            color: {THEME['primary_color']};
            font-size: {FONTS['title']['size']}px;
            font-weight: bold;
            margin-bottom: 10px;
        }}
        
        /* Clean Plotly chart elements */
        .js-plotly-plot .plotly {{
            background-color: {THEME['sidebar_bg']} !important;
        }}
          /* Style for filter containers - clean look */
        .filter-container {{
            background-color: {THEME['sidebar_bg']};
            padding: 15px;
            margin-bottom: 15px;
        }}
    </style>
    """

def get_all_css():
    """
    Returns all CSS styles combined.
    
    Returns:
        str: All CSS styles
    """
    return get_base_css() + get_tabs_css() + get_metric_css() + get_sidebar_css() + get_chart_css()

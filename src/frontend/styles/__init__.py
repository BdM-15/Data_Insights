"""
Styles module for Data_Insights application.

This module exports theme configuration and CSS for consistent styling across the application.
"""

from src.frontend.styles.theme import THEME, COLOR_SCALES, CHART_DEFAULTS, FONTS
from src.frontend.styles.custom_css import (
    get_base_css, 
    get_tabs_css, 
    get_metric_css, 
    get_sidebar_css,
    get_all_css
)

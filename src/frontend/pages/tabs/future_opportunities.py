"""
Future Opportunities tab for the Strategic Dashboard.

This module provides visualization functions for the Future Opportunities tab content.
"""

import streamlit as st
from src.frontend.styles.theme import THEME


def render_future_opportunities(df):
    """
    Render the Future Opportunities tab content.
    
    Args:
        df: DataFrame containing award data
    """
    st.header("Future Opportunities")
    st.info("This tab will identify upcoming opportunities by connecting historical contract data with active solicitations from SAM.gov and NATO NSPA.")
    
    # We'll implement the detailed visualizations in the next phase
    st.markdown("""
    Planned visualizations:
    - Expiring Contracts Timeline for next 6-24 months
    - Strategic Alignment Analysis (Suitability vs. Synergy quadrant chart)
    - Active SAM.gov Opportunities with capability match scoring
    - NATO NSPA Opportunities with capability match scoring  
    - Strategic Connections between historical performance and future opportunities
    """)

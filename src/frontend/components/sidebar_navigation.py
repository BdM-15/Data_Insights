"""
Custom sidebar navigation component for Data Insights application.

This module provides a custom navigation solution that allows for better control
over the layout and positioning of navigation elements in the sidebar.
"""

import streamlit as st
from typing import Dict, List, Callable, Optional
from datetime import datetime


def render_custom_navigation(
    pages: Dict[str, List[Dict]], 
    current_page: str,
    logo_path: Optional[str] = None
) -> str:
    """
    Render custom navigation in the sidebar with logo at top and navigation below.
    
    Args:
        pages: Dictionary of page sections and their pages
        current_page: Current active page identifier
        logo_path: Optional path to logo image
        
    Returns:
        str: Selected page identifier
    """
    
    # Display logo at the top if provided
    if logo_path:
        st.image(logo_path)
    
    # Add some spacing
    st.markdown("---")
    
    # No "Navigation" header - go straight to buttons
    
    selected_page = current_page
    
    # Render navigation sections
    for section_name, section_pages in pages.items():
        if not section_pages:  # Skip empty sections
            continue
            
        # Skip section titles entirely to remove "MAIN" text
        
        # Section pages
        for page_info in section_pages:
            page_id = page_info['id']
            title = page_info['title']
            icon = page_info['icon']
            
            # Determine if this is the active page
            is_active = page_id == current_page
            
            # Create clickable navigation item using button
            if st.button(
                f"{icon} {title}",
                key=f"nav_{page_id}",
                use_container_width=True,
                type="secondary"  # Use secondary for all navigation buttons
            ):
                selected_page = page_id
    
    # Return without adding the separator - let individual pages add their content
    return selected_page


def get_page_config():
    """
    Get the page configuration for the navigation system.
    
    Returns:
        Dict: Page configuration with sections and pages
    """
    return {
        "Main": [
            {
                "id": "dashboard",
                "title": "Strategic Dashboard",
                "icon": "📊",
                "function": None
            },
            {
                "id": "advanced-explorer",
                "title": "Advanced Opportunity Explorer",
                "icon": "🔍",
                "function": None
            },
            {
                "id": "capability-stance",
                "title": "Capability Stance",
                "icon": "🏆",
                "function": None
            },
            {
                "id": "ai-chat",
                "title": "AI Data Agent",
                "icon": "🤖",
                "function": None
            }
        ],
        "Tools": []
    }


def render_sidebar_footer():
    """Render the footer section of the sidebar."""
    st.markdown("---")
    st.markdown("""
    <div style="margin-top: 30px;">
        <h4 style="color: #00C3FF; font-size: 0.9rem;">About</h4>
        <p style="font-size: 0.8rem; color: #888;">
            Data Insights v1.0<br>
            Last updated: June 2025
        </p>
    </div>
    """, unsafe_allow_html=True)

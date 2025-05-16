"""
layouts.py
Reusable layout and container components for the Data Insights dashboard.

This module provides standardized layout patterns (grids, containers, expanders) for use across the Streamlit frontend.
All components are designed to be visually consistent with the dashboard's theme and easy to use in any page or tab module.

Future layout patterns can be added here as needed.
"""

import streamlit as st
from typing import Any, Callable, List, Optional
from src.frontend.styles.theme import THEME
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, AgGridTheme
import pandas as pd

# --- Grid Layouts ---
def two_column_grid(left_content: Callable[[], Any], right_content: Callable[[], Any], gap: str = "medium"):
    """
    Render a two-column grid layout.

    Args:
        left_content: Function to render content in the left column.
        right_content: Function to render content in the right column.
        gap: Spacing between columns ("small", "medium", or "large").
    """
    col1, col2 = st.columns(2, gap=gap)
    with col1:
        left_content()
    with col2:
        right_content()


def three_column_grid(
    left_content: Callable[[], Any],
    center_content: Callable[[], Any],
    right_content: Callable[[], Any],
    gap: str = "medium"
):
    """
    Render a three-column grid layout.

    Args:
        left_content: Function to render content in the left column.
        center_content: Function to render content in the center column.
        right_content: Function to render content in the right column.
        gap: Spacing between columns ("small", "medium", or "large").
    """
    col1, col2, col3 = st.columns(3, gap=gap)
    with col1:
        left_content()
    with col2:
        center_content()
    with col3:
        right_content()

# --- Container Layouts ---
def card_container(content: Callable[[], Any], title: Optional[str] = None, padding: int = 10, border: bool = True):
    """
    Render a card-like container with optional title, padding, and border.
    Args:
        content: Function to render the content inside the card.
        title: Optional card title.
        padding: Padding inside the card (px).
        border: Whether to show a border around the card.
    """
    style = f"padding: {padding}px; "
    if border:
        style += "border-radius: 8px; border: 1px solid #203040; background-color: #162030;"
    else:
        style += "background-color: #162030;"
    if title:
        st.markdown(f"<div style='{style}'><h5 style='margin-bottom: 0.5em;'>{title}</h5>", unsafe_allow_html=True)
    else:
        st.markdown(f"<div style='{style}'>", unsafe_allow_html=True)
    content()
    st.markdown("</div>", unsafe_allow_html=True)

# --- Expander Layouts ---
def expander_section(label: str, content: Callable[[], Any], expanded: bool = False):
    """
    Render a section inside a Streamlit expander.
    Args:
        label: Expander label.
        content: Function to render the content inside the expander.
        expanded: Whether the expander is open by default.
    """
    with st.expander(label, expanded=expanded):
        content()

# --- Card/Masonry Layouts ---
def card_grid(card_contents: List[Callable[[], Any]], cards_per_row: int = 3, gap: int = 2):
    """
    Render a responsive grid of card containers.
    Use case: Display multiple opportunity summaries, competitor profiles, or contract highlights in a dashboard grid.
    """
    rows = [card_contents[i:i+cards_per_row] for i in range(0, len(card_contents), cards_per_row)]
    for row in rows:
        cols = st.columns(len(row), gap=gap)
        for col, content in zip(cols, row):
            with col:
                content()

# --- Tabbed Card/Section ---
def tabbed_card(tab_labels: List[str], tab_contents: List[Callable[[], Any]], title: Optional[str] = None):
    """
    Render a card with tabs for switching between related content.
    Use case: Show different data slices (e.g., by agency, by NAICS, by time) or alternate between charts and tables for the same opportunity.
    """
    if title:
        st.markdown(f"<h5 style='margin-bottom: 0.5em;'>{title}</h5>", unsafe_allow_html=True)
    tab_objs = st.tabs(tab_labels)
    for tab, content in zip(tab_objs, tab_contents):
        with tab:
            content()

# --- Sidebar Layout ---
def sidebar_layout(sidebar_content: Callable[[], Any], main_content: Callable[[], Any]):
    """
    Render a sidebar for navigation, filters, or quick actions, with main content area.
    Use case: Persistent filters for agency, NAICS, or time; quick links to capture management tools.
    """
    with st.sidebar:
        sidebar_content()
    main_content()

# --- Section Divider / Title Bar ---
def section_divider(title: str, icon: Optional[str] = None):
    """
    Render a styled divider or title bar to separate dashboard sections.
    Use case: Visually group related analytics (e.g., "Market Position", "Capture Pipeline", "AI Insights").
    """
    icon_html = f"<span style='margin-right:8px'>{icon}</span>" if icon else ""
    st.markdown(f"<hr style='margin-top:2em;margin-bottom:0.5em;border:1px solid #203040'>", unsafe_allow_html=True)
    st.markdown(f"<h4 style='margin-bottom:0.5em'>{icon_html}{title}</h4>", unsafe_allow_html=True)

# --- Notification/Alert Banner ---
def alert_banner(message: str, alert_type: str = "info"):
    """
    Render a notification or alert banner.
    Use case: Show system status, data refresh, AI recommendations, or warnings (e.g., expiring contracts, missing data).
    """
    color = {"info": "#00C3FF", "warning": "#FFC300", "error": "#FF5733", "success": "#28A745"}.get(alert_type, "#00C3FF")
    st.markdown(f"<div style='background-color:{color};color:#fff;padding:0.75em 1em;border-radius:6px;margin-bottom:1em'>{message}</div>", unsafe_allow_html=True)

# --- Floating Action Button (FAB) ---
def floating_action_button(label: str, on_click: Callable[[], Any], icon: Optional[str] = None):
    """
    Render a floating action button for key actions.
    Use case: Quick access to "Add Filter", "Export", "Ask AI", or "Create Capture Profile".
    """
    btn_label = f"{icon} {label}" if icon else label
    st.button(btn_label, on_click=on_click, key=f"fab_{label}")

# --- Responsive Row/Column Layout ---
def responsive_row(contents: List[Callable[[], Any]], min_width: int = 300, gap: int = 2):
    """
    Render a row of columns that stacks on small screens.
    Use case: Ensure dashboard is mobile/tablet friendly for field capture teams or execs on the go.
    """
    cols = st.columns(len(contents), gap=gap)
    for col, content in zip(cols, contents):
        with col:
            content()

# --- Accordion/Stacked Expanders ---
def accordion(expanders: List[dict]):
    """
    Render multiple expanders with accordion behavior (only one open at a time).
    Use case: Step-by-step guides, FAQs, or multi-stage capture workflows (e.g., Shipley process steps).
    Each expander dict: {"label": str, "content": Callable, "expanded": bool}
    """
    expanded_idx = next((i for i, e in enumerate(expanders) if e.get("expanded", False)), 0)
    for i, exp in enumerate(expanders):
        with st.expander(exp["label"], expanded=(i == expanded_idx)):
            exp["content"]()

# --- Modal Dialog/Overlay (Stub) ---
def modal_dialog(content: Callable[[], Any], title: Optional[str] = None):
    """
    (Stub) Render a modal dialog overlay.
    Use case: Settings, detailed drill-downs, or AI chat. (Streamlit native support pending; can be emulated with popups or custom JS.)
    """
    st.warning("Modal dialogs are not natively supported in Streamlit yet. This is a placeholder for future implementation.")
    if title:
        st.markdown(f"### {title}")
    content()

# --- Progress/Stepper Bar (Stub) ---
def stepper_bar(steps: List[str], current_step: int):
    """
    (Stub) Render a progress/stepper bar for multi-step workflows.
    Use case: Capture profile generation, data import, or proposal creation.
    """
    st.markdown("<div style='margin:1em 0'>" +
        " ".join([
            f"<span style='padding:0.5em 1em;border-radius:20px;background-color:{'#00C3FF' if i==current_step else '#203040'};color:#fff;margin-right:8px'>{step}</span>"
            for i, step in enumerate(steps)
        ]) + "</div>", unsafe_allow_html=True)

# --- Themed AgGrid Table ---
def themed_aggrid(
    df: pd.DataFrame,
    selection_mode: str = "multiple",
    use_checkbox: bool = True,
    height: int = 350,
    update_mode=GridUpdateMode.NO_UPDATE,
    columns: list = None,
    fit_columns_on_grid_load: bool = True,
    key: str = None,
    **kwargs
):
    """
    Render an AgGrid table styled to match the dashboard theme.

    Args:
        df: DataFrame to display.
        selection_mode: 'single' or 'multiple' row selection.
        use_checkbox: Show checkboxes for selection.
        height: Table height in pixels.
        update_mode: When to trigger grid updates (default: NO_UPDATE).
        columns: Optional list of columns to display.
        fit_columns_on_grid_load: Auto-fit columns to grid width.
        key: Optional Streamlit key for the component.
        **kwargs: Additional AgGrid arguments.
    Returns:
        AgGrid response object (for selected rows, etc.)
    """
    import numpy as np
    if columns is not None:
        data = df[columns]
    else:
        data = df
    gb = GridOptionsBuilder.from_dataframe(data)
    gb.configure_selection(selection_mode=selection_mode, use_checkbox=use_checkbox)
    grid_options = gb.build()
    custom_css = {
        ".ag-root-wrapper": {"background-color": f"{THEME['bg_color']} !important"},
        ".ag-header, .ag-row, .ag-cell": {
            "background-color": f"{THEME['bg_color']} !important",
            "color": f"{THEME['text_color']} !important"
        },
        ".ag-header-cell-label": {"color": f"{THEME['text_color']} !important"},
        ".ag-row-selected": {"background-color": f"{THEME['primary']} !important"},
    }
    return AgGrid(
        data,
        gridOptions=grid_options,
        theme=AgGridTheme.STREAMLIT,
        update_mode=update_mode,
        allow_unsafe_jscode=False,
        enable_enterprise_modules=False,
        fit_columns_on_grid_load=fit_columns_on_grid_load,
        use_container_width=True,
        height=height,
        custom_css=custom_css,
        key=key,
        **kwargs
    )

# --- Future Layout Patterns ---
# Add more layouts as needed (e.g., tabbed containers, sidebar layouts, etc.)

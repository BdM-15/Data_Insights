"""
Contract Vehicle Analysis tab for the strategic dashboard.
"""
import streamlit as st
import pandas as pd
from src.frontend.styles.theme import THEME
from src.frontend.visualizations.charts.comparison_charts import (
    plot_contract_vehicle_pie,
)
from src.backend.data.app_processors.awards import get_contract_vehicles
from src.frontend.components.export import add_export_section

# Define a default color sequence for categorical charts
CATEGORY_COLORS = [
    THEME["primary"],
    THEME["accent1_color"],
    THEME["accent2_color"],
    "#FFD166",  # yellow
    "#06D6A0",  # green
    "#EF476F",  # red
    "#118AB2"   # blue
]

def render_tab(df: pd.DataFrame):
    """
    Render the Contract Vehicle Analysis tab content.

    Args:
        df: Filtered DataFrame for the dashboard
    """
    st.header("Contract Vehicle Analysis")
    st.markdown("""
    Analyze the distribution and trends of contract vehicles (FSS, GWAC, IDV, BPA, Stand Alone, etc.) across agencies and time. Use the filters in the sidebar to refine the analysis.
    """)

    # --- Contract Vehicle Distribution Pie Chart ---
    st.subheader("Contract Vehicle Distribution (Base Awards)")
    vehicle_data = get_contract_vehicles(df)
    if vehicle_data:
        vehicle_df = pd.DataFrame([v.dict() for v in vehicle_data])
        fig = plot_contract_vehicle_pie(vehicle_df, THEME)
        st.plotly_chart(fig, use_container_width=True, key="contract_vehicle_pie")
        add_export_section(vehicle_df, section_title="Export Contract Vehicle Data", file_prefix="contract_vehicles")
    else:
        st.info("No contract vehicle data available for the selected filters.")

    # --- Vehicle Preference by Agency (Stacked Bar Chart) ---
    st.subheader("Vehicle Preference by Agency")
    if not df.empty and 'parent_award_agency_name' in df.columns and 'award_type' in df.columns and 'federal_action_obligation' in df.columns:
        agency_vehicle = df[df['modification_number'] == '0'].groupby([
            'parent_award_agency_name', 'award_type']
        )['federal_action_obligation'].sum().reset_index()
        agency_pivot = agency_vehicle.pivot(index="parent_award_agency_name", columns="award_type", values="federal_action_obligation").fillna(0)
        import plotly.express as px
        fig_agency = px.bar(
            agency_pivot,
            x=agency_pivot.index,
            y=agency_pivot.columns,
            title="Contract Vehicle Preference by Agency",
            labels={"value": "Obligation ($)", "parent_award_agency_name": "Agency"},
            color_discrete_sequence=CATEGORY_COLORS
        )
        st.plotly_chart(fig_agency, use_container_width=True, key="vehicle_pref_agency")
        add_export_section(agency_vehicle, section_title="Export Agency-Vehicle Data", file_prefix="agency_vehicle_pref")
    else:
        st.info("No agency-vehicle data available.")

    # --- Single vs. Multiple Award Trends (Time Series Line Chart) ---
    st.subheader("Single vs. Multiple Award Trends Over Time")
    if vehicle_data and not vehicle_df.empty and 'award_type' in vehicle_df.columns and 'fiscal_year' in vehicle_df.columns:
        trend_df = vehicle_df.groupby(["fiscal_year", "award_type"])['obligation'].sum().reset_index()
        fig_trend = px.line(trend_df, x="fiscal_year", y="obligation", color="award_type",
                           markers=True, title="Single vs. Multiple Award Trends",
                           labels={"obligation": "Obligation ($)", "fiscal_year": "Fiscal Year", "award_type": "Award Type"},
                           color_discrete_sequence=CATEGORY_COLORS)
        st.plotly_chart(fig_trend, use_container_width=True, key="single_multi_trend")
        add_export_section(trend_df, section_title="Export Award Trends Data", file_prefix="award_trends")
    else:
        st.info("No award trend data available.")

    # --- Vehicle Success Rate (Obligation by Vehicle Type, Bar Chart) ---
    st.subheader("Vehicle Success Rate (Obligation by Vehicle Type)")
    if not df.empty and 'award_type' in df.columns and 'federal_action_obligation' in df.columns:
        vehicle_success = df[df['modification_number'] == '0'].groupby('award_type')['federal_action_obligation'].sum().reset_index()
        vehicle_success = vehicle_success.rename(columns={'award_type': 'contract_vehicle', 'federal_action_obligation': 'obligation'})
        fig_success = px.bar(vehicle_success, x="contract_vehicle", y="obligation",
                            title="Vehicle Success Rate (Total Obligation)",
                            labels={"obligation": "Obligation ($)", "contract_vehicle": "Vehicle Type"},
                            color="contract_vehicle",
                            color_discrete_sequence=CATEGORY_COLORS)
        st.plotly_chart(fig_success, use_container_width=True, key="vehicle_success_rate")
        add_export_section(vehicle_success, section_title="Export Vehicle Success Data", file_prefix="vehicle_success")
    else:
        st.info("No vehicle success data available.")

    # --- Interactive Filtering/Drill-down Placeholder ---
    st.markdown("""
    *Tip: Use the sidebar filters to drill down by agency, vehicle type, or fiscal year. More advanced interactivity coming soon.*
    """)

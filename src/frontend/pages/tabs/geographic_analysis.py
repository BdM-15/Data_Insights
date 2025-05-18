"""
Geographic Analysis tab for the strategic dashboard.
"""
import streamlit as st
import pandas as pd

def render_tab(df: pd.DataFrame):
    """
    Render the Geographic Analysis tab content.

    Args:
        df: Filtered DataFrame for the dashboard
    """
    st.header("Geographic Analysis")
    st.markdown("""
    Explore contract spending and award patterns by geography. Use the sidebar filters to refine by agency, NAICS, or date range.
    """)

    # --- Regional Spending Patterns (Choropleth Map) ---
    st.subheader("Regional Spending Patterns (by State)")
    if 'recipient_state_code' in df.columns:
        state_obligation = df.groupby('recipient_state_code')['federal_action_obligation'].sum().reset_index()
        state_obligation = state_obligation.rename(columns={'recipient_state_code': 'location', 'federal_action_obligation': 'value'})
        from src.frontend.visualizations.charts.geo_charts import plot_choropleth_map
        from src.frontend.styles.theme import THEME
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
        config = {
            'title': 'Obligations by State',
            'locationmode': 'USA-states',
            'colorbar_title': 'Obligation ($)',
            'geo_scope': 'usa'
        }
        fig_map = plot_choropleth_map(state_obligation, config, THEME)
        st.plotly_chart(fig_map, use_container_width=True, key="geo_choropleth")
        from src.frontend.components.export import add_export_section
        add_export_section(state_obligation, section_title="Export State Obligation Data", file_prefix="state_obligations")
    else:
        st.info("No state/location data available for geographic analysis.")

    # --- Performance by Location (Top States Bar Chart) ---
    st.subheader("Top States by Total Obligation")
    if 'recipient_state_code' in df.columns:
        top_states = state_obligation.sort_values('value', ascending=False).head(10)
        import plotly.express as px
        fig_bar = px.bar(top_states, x='location', y='value',
                        title='Top States by Total Obligation',
                        labels={'location': 'State', 'value': 'Obligation ($)'},
                        color='value', color_continuous_scale='Blues')
        st.plotly_chart(fig_bar, use_container_width=True, key="geo_top_states")
        add_export_section(top_states, section_title="Export Top States Data", file_prefix="top_states")
    else:
        st.info("No state/location data available for bar chart.")

    # --- Geographic Concentration of Awards (Scatter Map) ---
    st.subheader("Geographic Concentration of Awards")
    if 'recipient_longitude' in df.columns and 'recipient_latitude' in df.columns:
        awards_geo = df.dropna(subset=['recipient_longitude', 'recipient_latitude'])
        import plotly.express as px
        fig_scatter = px.scatter_geo(
            awards_geo,
            lon='recipient_longitude',
            lat='recipient_latitude',
            scope='usa',
            hover_name='recipient_name' if 'recipient_name' in awards_geo.columns else None,
            size='federal_action_obligation' if 'federal_action_obligation' in awards_geo.columns else None,
            color='federal_action_obligation' if 'federal_action_obligation' in awards_geo.columns else None,
            color_continuous_scale='Blues',
            title='Geographic Concentration of Awards',
            labels={'federal_action_obligation': 'Obligation ($)'}
        )
        fig_scatter.update_layout(geo=dict(bgcolor=THEME['bg_color']))
        st.plotly_chart(fig_scatter, use_container_width=True, key="geo_award_scatter")
        add_export_section(awards_geo[[
            'recipient_name', 'recipient_longitude', 'recipient_latitude', 'federal_action_obligation']].dropna(),
            section_title="Export Award Locations Data", file_prefix="award_locations")
    else:
        st.info("No recipient latitude/longitude data available for geographic concentration map.")

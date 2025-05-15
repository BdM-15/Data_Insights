"""
Competitive Analysis tab for the Strategic Dashboard.

This module provides visualization functions for the Competitive Analysis tab content.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go # Added import
from plotly.subplots import make_subplots # Added import

# Backend processors
from src.backend.data.processors.competition import get_competitive_landscape as get_competitive_landscape_processor, get_treemap_data # Added get_treemap_data

# Frontend styles
from src.frontend.styles.theme import THEME

def render_competitive_analysis(df: pd.DataFrame):
    """
    Render the Competitive Analysis tab content.
    
    Args:
        df: DataFrame containing award data (used by the processor)
    """
    if df.empty:
        # Help the user understand why there's no data
        st.warning("No data available for Competitive Analysis based on the current filters.")
        st.info("Possible issues:")
        st.markdown("""
        1. **Database Connection**: Verify PostgreSQL is running and connection details are correct.
        2. **Data Availability**: There may be no data for the selected NAICS code and date range in the database.
        3. **Filters**: The combination of NAICS code, date range, and agency filter might yield no results.
        
        Try adjusting the filters in the sidebar.
        """)
        return

    st.header("Competitive Analysis")
    st.subheader("Competitive Intelligence Overview")
    st.markdown("""
    This tab provides detailed analysis of the competitive landscape across federal contracts, 
    helping you understand competitor strengths, agency relationships, and market positioning.
    """)
    
    # Competitive Landscape Treemap
    st.subheader("Competitive Landscape Treemap")
    treemap_data_list = get_treemap_data(df)

    if treemap_data_list:
        treemap_df = pd.DataFrame([model.model_dump() for model in treemap_data_list])
        
        if not treemap_df.empty and all(col in treemap_df.columns for col in ['recipient_parent_name', 'recipient_name', 'funding_sub_agency_name', 'transaction_description', 'federal_action_obligation', 'market_share', 'win_rate']):
            
            path_columns = ['recipient_parent_name', 'recipient_name', 'funding_sub_agency_name', 'transaction_description']
            for col in path_columns:
                treemap_df[col] = treemap_df[col].fillna('Unknown').astype(str)
            
            treemap_df['federal_action_obligation'] = pd.to_numeric(treemap_df['federal_action_obligation'], errors='coerce').fillna(0)

            # Filter for positive obligations for the treemap values
            treemap_df_positive_values = treemap_df[treemap_df['federal_action_obligation'] > 0].copy() # Use .copy() to avoid SettingWithCopyWarning

            if not treemap_df_positive_values.empty: # Check if there's data after filtering
                fig_treemap = px.treemap(
                    treemap_df_positive_values, # Use filtered DataFrame
                    path=[px.Constant("All Contractors"), 'recipient_parent_name', 'recipient_name', 'funding_sub_agency_name', 'transaction_description'],
                    values='federal_action_obligation',
                    color='market_share', 
                    hover_data={
                        'federal_action_obligation': ':.2s', 
                        'market_share': ':.2f',
                        'win_rate': ':.2f'
                    },
                    color_continuous_scale='Blues',
                    title="Competitive Landscape by Obligations and Market Share"
                )
                
                fig_treemap.update_layout(
                    plot_bgcolor=THEME["sidebar_bg"], # Ensure plot_bgcolor is set
                    paper_bgcolor=THEME["sidebar_bg"], # Ensure paper_bgcolor is set
                    font=dict(color="#FFFFFF"),
                    title_font=dict(color="#FFFFFF", size=18),
                    margin=dict(t=50, l=10, r=10, b=10),
                    coloraxis_colorbar=dict(
                        title="Market Share (%)",
                        titlefont=dict(color="#FFFFFF"),
                        tickfont=dict(color="#FFFFFF")
                    ),
                    modebar=dict(
                        bgcolor="rgba(22, 45, 69, 0.8)",
                        color="#FFFFFF",
                        activecolor=THEME["primary_color"]
                    )
                )
                
                fig_treemap.update_traces(
                    textinfo="label+value",
                    # Customdata should also use the filtered DataFrame
                    customdata=treemap_df_positive_values[['market_share', 'win_rate']].values, 
                    hovertemplate=(
                        "<b>Path:</b> %{id}<br>"
                        "<b>Obligation:</b> %{value:$,.0f}<br>"
                        "<b>Market Share:</b> %{customdata[0]:.2f}%<br>"
                        "<b>Win Rate:</b> %{customdata[1]:.2f}%<br>"
                        "<extra></extra>"
                    )
                )
                
                st.plotly_chart(fig_treemap, use_container_width=True)
            else:
                st.warning("No positive obligation data available to generate the treemap after filtering.")
        else:
            st.warning("Insufficient or malformed data for treemap. Required columns might be missing or empty.")
            if not treemap_df.empty:
                st.write("Columns available in treemap_df:", treemap_df.columns.tolist())
            else:
                st.write("treemap_df is empty after processing.")

    else:
        st.warning("No data available to generate the treemap (get_treemap_data returned empty).")
            
    # Call backend processor for other charts
    competitors_data_list = get_competitive_landscape_processor(df) # Returns List[CompetitorPerformance]
    
    if competitors_data_list:
        competitors_df = pd.DataFrame([model.model_dump() for model in competitors_data_list])
        
        if not competitors_df.empty:
            # Prepare data for visualization - get top 10 competitors by market_share
            # The processor already sorts by market_share descending.
            top_competitors_df = competitors_df.head(10) 
            
            # First row of visualizations - Market Share and Win Rate
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Market Share Analysis")
                if not top_competitors_df.empty:
                    fig = px.bar(
                        top_competitors_df,
                        x='market_share',
                        y='recipient_name',
                        orientation='h',
                        title="Top 10 Competitors by Market Share",
                        color='market_share',
                        color_continuous_scale="Blues",
                        labels={
                            'market_share': 'Market Share (%)',
                            'recipient_name': 'Competitor'
                        }
                    )
                    fig.update_layout(
                        plot_bgcolor=THEME["sidebar_bg"],
                        paper_bgcolor=THEME["sidebar_bg"],
                        font=dict(color="#FFFFFF"),
                        title_font=dict(color="#FFFFFF", size=16),
                        margin=dict(l=10, r=10, t=40, b=10),
                        yaxis={'categoryorder': 'total ascending'},
                        coloraxis_showscale=False,
                        modebar=dict(
                            bgcolor="rgba(22, 45, 69, 0.8)",
                            color="#FFFFFF",
                            activecolor=THEME["primary_color"]
                        )
                    )
                    
                    # Add value annotations
                    fig.update_traces(
                        texttemplate='%{x:.1f}%',
                        textposition='outside',
                        hovertemplate='<b>%{y}</b><br>Market Share: %{x:.2f}%<extra></extra>'
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning("No competitor data to display for Market Share Analysis.")
            
            with col2:
                st.subheader("Win Rate Analysis")
                # For Win Rate, let's sort by win_rate to get top 10 by win_rate
                top_by_win_rate_df = competitors_df.nlargest(10, 'win_rate')
                if not top_by_win_rate_df.empty:
                    fig = px.bar(
                        top_by_win_rate_df, # Use DataFrame sorted by win_rate
                        x='win_rate',
                        y='recipient_name',
                        orientation='h',
                        title="Top 10 Competitors by Win Rate",
                        color='win_rate',
                        color_continuous_scale="Teal",
                        labels={
                            'win_rate': 'Win Rate (%)',
                            'recipient_name': 'Competitor'
                        }
                    )
                    fig.update_layout(
                        plot_bgcolor=THEME["sidebar_bg"],
                        paper_bgcolor=THEME["sidebar_bg"],
                        font=dict(color="#FFFFFF"),
                        title_font=dict(color="#FFFFFF", size=16),
                        margin=dict(l=10, r=10, t=40, b=10),
                        yaxis={'categoryorder': 'total ascending'},
                        coloraxis_showscale=False,
                        modebar=dict(
                            bgcolor="rgba(22, 45, 69, 0.8)",
                            color="#FFFFFF",
                            activecolor=THEME["primary_color"]
                        )
                    )
                    
                    # Add value annotations
                    fig.update_traces(
                        texttemplate='%{x:.1f}%',
                        textposition='outside',
                        hovertemplate='<b>%{y}</b><br>Win Rate: %{x:.2f}%<extra></extra>'
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning("No competitor data to display for Win Rate Analysis.")
                
            # Market Position Analysis - Scatter Plot
            # This plot uses the top_competitors_df (top 10 by market share)
            st.subheader("Market Position Analysis")
            if not top_competitors_df.empty:
                fig = px.scatter(
                    top_competitors_df, # Using top 10 by market share for consistency with original logic if it used 'top_competitors'
                    x='market_share',
                    y='win_rate',
                    size='federal_action_obligation', # This is the field name in CompetitorPerformance model
                    color='recipient_name',
                    hover_name='recipient_name',
                    title="Competitive Positioning: Win Rate vs Market Share",
                    labels={
                        'market_share': 'Market Share (%)',
                        'win_rate': 'Win Rate (%)',
                        'federal_action_obligation': 'Total Obligations ($)'
                    },
                    size_max=50
                )
                # Add quadrant lines at median values
                median_market_share = top_competitors_df['market_share'].median()
                median_win_rate = top_competitors_df['win_rate'].median()
                
                fig.add_shape(
                    type="line",
                    x0=median_market_share,
                    y0=0,
                    x1=median_market_share,
                    y1=top_competitors_df['win_rate'].max() * 1.1 if not top_competitors_df['win_rate'].empty else 1,
                    line=dict(color="White", width=1, dash="dash")
                )
                
                fig.add_shape(
                    type="line",
                    x0=0,
                    y0=median_win_rate,
                    x1=top_competitors_df['market_share'].max() * 1.1 if not top_competitors_df['market_share'].empty else 1,
                    y1=median_win_rate,
                    line=dict(color="White", width=1, dash="dash")
                )
                
                # Add quadrant labels
                # Ensure y_max_val is not NaN or too small for annotation placement
                y_max_val = top_competitors_df['win_rate'].max() if not top_competitors_df['win_rate'].empty else 1.0

                fig.add_annotation(
                    x=median_market_share/2,
                    y=y_max_val * 0.8,
                    text="High Win Rate, Low Market Share",
                    showarrow=False,
                    font=dict(color="#FFFFFF", size=14),
                    bgcolor="rgba(22, 45, 69, 0.8)",
                    bordercolor=THEME["highlight_color"],
                    borderwidth=1,
                    borderpad=4
                )
                
                fig.add_annotation(
                    x=median_market_share*1.5,
                    y=y_max_val * 0.8,
                    text="Market Leaders",
                    showarrow=False,
                    font=dict(color="#FFFFFF", size=14),
                    bgcolor="rgba(22, 45, 69, 0.8)",
                    bordercolor=THEME["highlight_color"],
                    borderwidth=1,
                    borderpad=4
                )
                
                fig.add_annotation(
                    x=median_market_share/2,
                    y=median_win_rate/2,
                    text="Struggling Competitors",
                    showarrow=False,
                    font=dict(color="#FFFFFF", size=14),
                    bgcolor="rgba(22, 45, 69, 0.8)",
                    bordercolor=THEME["highlight_color"],
                    borderwidth=1,
                    borderpad=4
                )
                
                fig.add_annotation(
                    x=median_market_share*1.5,
                    y=median_win_rate/2,
                    text="High Volume, Low Win Rate",
                    showarrow=False,
                    font=dict(color="#FFFFFF", size=14),
                    bgcolor="rgba(22, 45, 69, 0.8)",
                    bordercolor=THEME["highlight_color"],
                    borderwidth=1,
                    borderpad=4
                )
                
                # Update axes titles
                fig.update_xaxes(
                    title="Market Share (%)"
                )
                
                fig.update_yaxes(
                    title="Win Rate (%)"
                )
                
                # Update point appearance
                fig.update_traces(
                    marker=dict(
                        opacity=0.8,
                        line=dict(width=2, color="DarkSlateGrey")
                    ),
                    selector=dict(mode="markers")
                )
                
                # Update layout
                fig.update_layout(
                    plot_bgcolor=THEME["sidebar_bg"],
                    paper_bgcolor=THEME["sidebar_bg"],
                    font=dict(color="#FFFFFF"),
                    title_font=dict(color="#FFFFFF", size=16),
                    margin=dict(l=10, r=10, t=40, b=10),
                    modebar=dict(
                        bgcolor="rgba(22, 45, 69, 0.8)",
                        color="#FFFFFF",
                        activecolor=THEME["primary_color"]
                    )
                )
                
                # Update hover template
                fig.update_traces(
                    hovertemplate="<b>%{hovertext}</b><br>" +
                                  "Market Share: %{x:.2f}%<br>" +
                                  "Win Rate: %{y:.2f}%<br>" +
                                  "Total Obligations: $%{marker.size:,.0f}<extra></extra>"
                )
                
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("No competitor data for Market Position Analysis.")

            # Competitor-Agency Relationship Analysis
            st.subheader("Competitor-Agency Relationships")
            if 'parent_award_agency_name' in df.columns and not df.empty and not competitors_df.empty:
                # Use competitors_df for top competitors, df for agency details
                top_5_competitors_list = competitors_df.nlargest(5, 'market_share')['recipient_name'].tolist()
                
                competitor_agency_df = df[df['recipient_name'].isin(top_5_competitors_list)]
                
                if not competitor_agency_df.empty:
                    competitor_agency_obligations = competitor_agency_df.groupby(['recipient_name', 'parent_award_agency_name'])['federal_action_obligation'].sum().reset_index()

                    heatmap_data_list = []
                    for competitor_name in top_5_competitors_list:
                        competitor_specific_agency_data = competitor_agency_obligations[competitor_agency_obligations['recipient_name'] == competitor_name]
                        top_agencies_for_competitor = competitor_specific_agency_data.nlargest(3, 'federal_action_obligation')
                        for _, row in top_agencies_for_competitor.iterrows():
                            heatmap_data_list.append({
                                'Competitor': competitor_name,
                                'Agency': row['parent_award_agency_name'],
                                'Obligation': row['federal_action_obligation']
                            })
                    
                    if heatmap_data_list:
                        heatmap_df = pd.DataFrame(heatmap_data_list)
                        pivot_df = heatmap_df.pivot_table(
                            values='Obligation',
                            index='Competitor',
                            columns='Agency',
                            aggfunc='sum',
                            fill_value=0
                        )
                        
                        # Normalize for better visualization if desired, or use raw values
                        # For this example, let's use raw obligations for the heatmap color intensity
                        # normalized_pivot = pivot_df.div(pivot_df.sum(axis=1), axis=0) # Example normalization

                        fig_heatmap = px.imshow(
                            pivot_df, # Using pivot_df with raw obligations
                            color_continuous_scale="Blues",
                            labels=dict(x="Agency", y="Competitor", color="Total Obligation ($)"),
                            title="Top Competitor-Agency Relationships (by Obligation)"
                        )
                        
                        fig_heatmap.update_layout(
                            plot_bgcolor=THEME["sidebar_bg"],
                            paper_bgcolor=THEME["sidebar_bg"],
                            font=dict(color="#FFFFFF"),
                            title_font=dict(color="#FFFFFF", size=16),
                            margin=dict(l=10, r=20, t=50, b=10), # Adjusted top margin for title
                            xaxis={'side': 'top', 'tickangle': -45},
                            coloraxis_colorbar=dict(title="Obligation ($)")
                        )
                        
                        fig_heatmap.update_traces(
                            hovertemplate="<b>%{y}</b> - <b>%{x}</b><br>" +
                                          "Total Obligation: $%{z:,.0f}<br>" + # Show actual obligation
                                          "<extra></extra>"
                        )
                        st.plotly_chart(fig_heatmap, use_container_width=True)
                    else:
                        st.info("Insufficient data to generate competitor-agency relationships heatmap.")
                else:
                    st.info("No relevant agency data found for the top competitors.")
            else:
                missing_cols = []
                if 'parent_award_agency_name' not in df.columns:
                    missing_cols.append("'parent_award_agency_name'")
                if competitors_df.empty:
                     st.info("Competitor data is empty, cannot generate agency relationships.")
                elif df.empty:
                    st.info("Main dataframe is empty, cannot generate agency relationships.")
                else: # parent_award_agency_name is missing
                     st.info(f"Column {', '.join(missing_cols)} not available in the dataset to generate competitor-agency relationships.")


            # Competition Intensity by Contract Type
            st.subheader("Contract Type Analysis")
            if 'type_of_contract_pricing' in df.columns and 'federal_action_obligation' in df.columns and not df.empty:
                # Chart 1: Number of unique competitors by contract type
                contract_type_competition_df = df.groupby('type_of_contract_pricing')['recipient_name'].nunique().reset_index()
                contract_type_competition_df.columns = ['Contract Type', 'Number of Competitors']
                contract_type_competition_df = contract_type_competition_df.sort_values('Number of Competitors', ascending=False)
                top_contract_types_competition = contract_type_competition_df.head(10)

                fig_ct_bar = px.bar(
                    top_contract_types_competition,
                    x='Number of Competitors',
                    y='Contract Type',
                    orientation='h',
                    title="Competition Intensity by Contract Type (Top 10)",
                    color='Number of Competitors',
                    color_continuous_scale="Blues",
                    labels={
                        'Number of Competitors': 'Number of Unique Competitors',
                        'Contract Type': 'Contract Type'
                    }
                )
                fig_ct_bar.update_layout(
                    plot_bgcolor=THEME["sidebar_bg"],
                    paper_bgcolor=THEME["sidebar_bg"],
                    font=dict(color="#FFFFFF"),
                    title_font=dict(color="#FFFFFF", size=16),
                    margin=dict(l=10, r=10, t=40, b=10),
                    yaxis={'categoryorder': 'total ascending'},
                    coloraxis_showscale=False
                )
                fig_ct_bar.update_traces(
                    texttemplate='%{x:.0f}',
                    textposition='outside',
                    hovertemplate='<b>%{y}</b><br>Competitors: %{x:.0f}<extra></extra>'
                )
                st.plotly_chart(fig_ct_bar, use_container_width=True)

                # Chart 2: Dual-axis chart for Total Obligation and Avg Obligation per Competitor
                contract_type_value_df = df.groupby('type_of_contract_pricing')['federal_action_obligation'].sum().reset_index()
                contract_type_value_df.columns = ['Contract Type', 'Total Obligation']
                
                contract_type_analysis_df = pd.merge(contract_type_competition_df, contract_type_value_df, on='Contract Type')
                contract_type_analysis_df['Average Obligation'] = contract_type_analysis_df['Total Obligation'] / contract_type_analysis_df['Number of Competitors']
                contract_type_analysis_df['Average Obligation'] = contract_type_analysis_df['Average Obligation'].fillna(0) # Handle potential division by zero if a type has 0 competitors but somehow an obligation

                top_value_types_df = contract_type_analysis_df.nlargest(10, 'Total Obligation')

                fig_ct_dual = make_subplots(specs=[[{"secondary_y": True}]])
                fig_ct_dual.add_trace(
                    go.Bar(
                        x=top_value_types_df['Contract Type'],
                        y=top_value_types_df['Total Obligation'],
                        name='Total Obligation',
                        marker_color=THEME.get("primary_color", "#007bff") # Use theme color with fallback
                    ),
                    secondary_y=False
                )
                fig_ct_dual.add_trace(
                    go.Scatter(
                        x=top_value_types_df['Contract Type'],
                        y=top_value_types_df['Average Obligation'],
                        name='Avg Obligation per Competitor',
                        mode='lines+markers',
                        marker=dict(color=THEME.get("highlight_color", "#ffc107")), # Use theme color
                        line=dict(width=3)
                    ),
                    secondary_y=True
                )
                fig_ct_dual.update_layout(
                    title_text="Contract Type Value Analysis (Top 10 by Obligation)",
                    plot_bgcolor=THEME["sidebar_bg"],
                    paper_bgcolor=THEME["sidebar_bg"],
                    font=dict(color="#FFFFFF"),
                    title_font=dict(color="#FFFFFF", size=16),
                    margin=dict(l=10, r=10, t=50, b=10), # Adjusted top margin
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(color="#FFFFFF"), bgcolor=THEME["sidebar_bg"]),
                    xaxis=dict(tickangle=-45, title_font=dict(color="#FFFFFF"), tickfont=dict(color="#FFFFFF")),
                    yaxis=dict(title_text="Total Obligation ($)", secondary_y=False, tickprefix="$", tickformat=",.0f", title_font=dict(color="#FFFFFF"), tickfont=dict(color="#FFFFFF")),
                    yaxis2=dict(title_text="Avg Obligation per Competitor ($)", secondary_y=True, tickprefix="$", tickformat=",.0f", title_font=dict(color="#FFFFFF"), tickfont=dict(color="#FFFFFF"))
                )
                st.plotly_chart(fig_ct_dual, use_container_width=True)
            else:
                missing_cols_ct = []
                if 'type_of_contract_pricing' not in df.columns:
                    missing_cols_ct.append("'type_of_contract_pricing'")
                if 'federal_action_obligation' not in df.columns:
                    missing_cols_ct.append("'federal_action_obligation'")
                if df.empty:
                    st.info("Main dataframe is empty, cannot generate contract type analysis.")
                else:
                    st.info(f"Column(s) {', '.join(missing_cols_ct)} not available for Contract Type Analysis.")

            # Competitive Strategy Insights (static text, no changes needed)
            st.subheader("Competitive Strategy Insights")
            
            # Create a container for the insights
            insights_container = st.container()
            
            with insights_container:
                col1_insights, col2_insights = st.columns(2)
                
                with col1_insights:
                    st.markdown("""
                    ### Market Positioning
                    
                    Based on the competitive analysis, consider these strategies:
                    
                    - **Focus on high win-rate, low market share quadrant** agencies where your company can efficiently compete
                    - **Identify partnering opportunities** with complementary contractors
                    - **Target contract vehicles** with lower competitive intensity
                    - **Develop specialized offerings** for agencies with diverse contractor bases
                    """)
                
                with col2_insights:
                    st.markdown("""
                    ### Differentiation Opportunities
                    
                    Competitive analysis suggests these differentiation approaches:
                    
                    - **Pricing strategies** tailored to specific contract types
                    - **Agency-specific expertise** development where competitors are weaker
                    - **Contract vehicle specialization** in less congested segments
                    - **Past performance emphasis** in areas with strong incumbent presence
                    """)
        else:
            st.warning("Insufficient data for competitive analysis. Try expanding your filter criteria.")
    else:
        st.warning("No data available for Competitive Analysis based on the current filters.")
        st.info("Possible issues:")
        st.markdown("""
        1. **Database Connection**: Verify PostgreSQL is running and connection details are correct.
        2. **Data Availability**: There may be no data for the selected NAICS code and date range in the database.
        3. **Filters**: The combination of NAICS code, date range, and agency filter might yield no results.
        
        Try adjusting the filters in the sidebar.
        """)
        st.subheader("Sample Competitive Analysis View")
        st.image("https://via.placeholder.com/800x500.png?text=Competitive+Analysis+Dashboard+(Sample)", 
                caption="Sample visualization of Competitive Analysis tab with data")
    
    st.subheader("Competitive Landscape Treemap")
    treemap_data_list = get_treemap_data(df) # Use the dedicated processor

    if treemap_data_list:
        treemap_df = pd.DataFrame([model.model_dump() for model in treemap_data_list])
        
        if not treemap_df.empty and all(col in treemap_df.columns for col in ['recipient_parent_name', 'recipient_name', 'funding_sub_agency_name', 'transaction_description', 'federal_action_obligation', 'market_share', 'win_rate']):
            
            # Ensure path elements are not None or NaN, replace with a placeholder if necessary
            path_columns = ['recipient_parent_name', 'recipient_name', 'funding_sub_agency_name', 'transaction_description']
            for col in path_columns:
                treemap_df[col] = treemap_df[col].fillna('Unknown').astype(str)
            
            # Ensure 'federal_action_obligation' is numeric for the treemap values
            treemap_df['federal_action_obligation'] = pd.to_numeric(treemap_df['federal_action_obligation'], errors='coerce').fillna(0)

            fig_treemap = px.treemap(
                treemap_df,
                path=[px.Constant("All Contractors"), 'recipient_parent_name', 'recipient_name', 'funding_sub_agency_name', 'transaction_description'],
                values='federal_action_obligation',
                color='market_share', # Color by market_share
                hover_data={
                    'federal_action_obligation': ':.2s', 
                    'market_share': ':.2f',
                    'win_rate': ':.2f'
                },
                color_continuous_scale='Blues',
                title="Competitive Landscape by Obligations and Market Share"
            )
            
            fig_treemap.update_layout(
                plot_bgcolor=THEME["sidebar_bg"],
                paper_bgcolor=THEME["sidebar_bg"],
                font=dict(color="#FFFFFF"),
                title_font=dict(color="#FFFFFF", size=18), # Increased title font size
                margin=dict(t=50, l=10, r=10, b=10), # Adjusted margins
                coloraxis_colorbar=dict(
                    title="Market Share (%)",
                    titlefont=dict(color="#FFFFFF"), # Colorbar title font color
                    tickfont=dict(color="#FFFFFF")  # Colorbar tick font color
                ),
                modebar=dict(
                    bgcolor="rgba(22, 45, 69, 0.8)",
                    color="#FFFFFF",
                    activecolor=THEME["primary_color"]
                )
            )
            
            fig_treemap.update_traces(
                textinfo="label+value", # Show label and value
                hovertemplate=(
                    "<b>Path:</b> %{id}<br>"
                    "<b>Obligation:</b> %{value:$,.0f}<br>"
                    "<b>Market Share:</b> %{customdata[0]:.2f}%<br>" # Assuming market_share is first in hover_data
                    "<b>Win Rate:</b> %{customdata[1]:.2f}%<br>"     # Assuming win_rate is second
                    "<extra></extra>"
                )
            )
            
            st.plotly_chart(fig_treemap, use_container_width=True)
        else:
            st.warning("Insufficient or malformed data for treemap. Required columns might be missing or empty.")
            if not treemap_df.empty:
                st.write("Columns available in treemap_df:", treemap_df.columns.tolist())
            else:
                st.write("treemap_df is empty.")
    else:
        st.warning("No data available to generate the treemap.")

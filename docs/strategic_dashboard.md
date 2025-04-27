# Strategic Dashboard

## Overview

The Strategic Dashboard provides a high-level view of the government acquisition landscape with a focus on NAICS 561210 (Facilities Support Services). The dashboard visualizes key metrics including total obligations, award actions, top agencies, funding sub-agencies, and funding offices.

## UI Design - April 2025 Update

The dashboard user interface has been enhanced with:

- Centered metric card titles for improved readability and visual balance
- Redesigned sidebar structure based on project documentation
- Hierarchical navigation in the sidebar with clear section organization
- Properly structured filter controls with consistent styling
- About section in the sidebar footer with version information
- Removal of diagnostic panels for a cleaner interface
- Consistent electric theme styling throughout
- Replaced Unicode characters with ASCII-compatible alternatives for improved compatibility across environments

## Visual Theme

The dashboard uses an "electric energy" theme with:

- Vibrant electric blues and whites as primary colors
- Dark navy background (#1A1A2E) for contrast
- Bright complementary colors for different visualization types
- High contrast for readability and visual impact
- Centered metric titles with consistent styling across cards

## Dashboard Components

### Sidebar Structure

1. **Application Logo**
   - Placeholder logo at the top of the sidebar
2. **Navigation Section**

   - Strategic Dashboard (current page)
   - Data Explorer (placeholder)
   - Visualizations (placeholder)
   - Capture Profiles (placeholder)
   - AI Tools (placeholder)

3. **Filters Section**

   - NAICS Code selection (default: 561210)
   - Date Range with 5-year default span
   - Agency selection based on database values
   - Apply Filters button for deliberate filtering

4. **About Section**
   - Version information
   - Last updated date

### Main View

1. **Executive Summary Cards**

   - Total Obligations: Total dollar value of all obligations
   - Total Award Actions: Number of distinct award actions (base awards only, Modification No = '0')
   - Average Award Value: Average dollar value per award action
   - Active Contracts: Number of currently active contracts
   - Expiring Contracts (24mo): Number of contracts expiring within the next 6 to 24 months
   - Suitability: Percentage of expiring contracts suitable for R&S based on comparing company capabilities to expiring contract descriptions
   - Synergy: Percentage of expiring contracts suitable across MTS business units based on comparing company capabilities to expiring contract descriptions

2. **Combined Obligations and Award Actions Trend**

   - Dual-axis visualization showing relationship between spending and contract actions
   - Quarter-by-quarter view with fiscal year demarcations
   - Toggle capability between cumulative and quarterly views
- Line chart showing quarterly trends for both obligations and award actions

3. **Action-to-Obligation Ratio Analysis**

   - Scatter plot identifying agencies with high-value contracts but fewer award actions
   - Quadrant analysis for strategic targeting
   - Interactive tooltips with detailed agency metrics

4. **Contract Vehicle Distribution**

   - Pie chart showing distribution of contract vehicles (FSS, GWAC, IDV, BPA, Stand Alone...etc.)
   - Single vs. Multiple award analysis
   - Vehicle preferences by agency

5. **Competitive Landscape**

   - Treemap visualization of top competitors by market share
   - Win rates by competitor
   - Agency-competitor relationships

6. **Top Agencies Analysis**
   - Bar charts of top agencies by both award count and obligation amount
   - Hover details with additional agency metrics

### Tab Navigation

The dashboard uses a tabbed interface with six main tabs:

1. **Market Overview** (default tab)
   - Contains executive summary metrics and key visualizations described above
   - Top agencies, recipients, and NAICS code analysis
   - Interactive charts for obligations and award actions trends

2. **Future Opportunities**
   - Expiring Contracts Timeline for next 6-24 months
   - Strategic Alignment Analysis (Suitability vs. Synergy quadrant chart)
   - Active SAM.gov Opportunities with capability match scoring
   - NATO NSPA Opportunities with capability match scoring
- Incumbenet and recompete information
   - Strategic Connections between historical performance and future opportunities
 
   3. **Agency Intelligence**
   - Agency hierarchy analysis
   - Agency spending patterns
   - Set-aside utilization by agency
- Competitor-agency relationships

4. **Competitive Analysis**
   - Market Share Analysis - Horizontal bar chart of competitors by market share
   - Win Rate Analysis - Bar chart showing top competitors by win rate percentage
   - Market Position Analysis - Quadrant scatter plot showing win rate vs market share
   - Competitor-Agency Relationships - Heatmap visualization of relationships between top competitors and agencies
   - Contract Type Analysis - Competition intensity by contract type and dual-axis chart of contract value
   - Competitive Strategy Insights - Actionable recommendations based on analysis

5. **Contract Vehicle Analysis**
   - Vehicle preference by agency
   - Award type distributions
   - Success rates by contract type

6. **Geographic Analysis**
   - Regional spending patterns
   - Performance by location
   - Geographic concentration of awards

## Data Requirements

The dashboard requires the following base data from the usaspending_cleaned table:

- Award actions (where Modification No = '0')
- Federal action obligations
- Agency hierarchies (awarding and funding)
- Contract vehicle types
- Award dates and periods of performance
- Recipient information
- NAICS codes (filtered to 561210 by default)

## Filters

Users can filter the dashboard data by:

- NAICS Code: Default is 561210 (Facilities Support Services)
- Date Range: Start Date and End Date (Default is 5-year span)
- Agency: All agencies are available by default

The Clear Filters button resets all filters to their default values.

## Technical Approach

- Streamlit for frontend interface
- Plotly for interactive visualizations
- PostgreSQL for data queries with optimized indexes
- Caching of frequently accessed data for performance
- Responsive design for various screen sizes
- Session state management for filter persistence
- ASCII-compatible character usage for cross-environment compatibility

## Data Source

The dashboard pulls data from the PostgreSQL database table `usaprime_cleaned` with fallback options for other potential table names.

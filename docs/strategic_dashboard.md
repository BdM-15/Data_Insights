# Strategic Dashboard Implementation

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

   - Total Obligations in NAICS 561210
   - Total Award Actions (base awards only, Modification No = '0')
   - Average Award Value
   - Total Active Contracts
   - YoY Growth Rate

2. **Combined Obligations and Award Actions Trend**

   - Dual-axis visualization showing relationship between spending and contract actions
   - Quarter-by-quarter view with fiscal year demarcations
   - Toggle capability between cumulative and quarterly views

3. **Agency-to-Obligation Ratio Analysis**

   - Scatter plot identifying agencies with high-value contracts but fewer award actions
   - Quadrant analysis for strategic targeting
   - Interactive tooltips with detailed agency metrics

4. **Contract Vehicle Distribution**

   - Distribution of contract vehicles (FSS, GWAC, IDV, BPA, Stand Alone...etc.)
   - Single vs. Multiple award analysis
   - Vehicle preferences by agency

5. **Competitive Landscape**

   - Top competitors by market share
   - Win rates by competitor
   - Agency-competitor relationships

6. **Upcoming High-Value Opportunities**
   - Timeline of expiring high-value contracts
   - Incumbent and recompete information
   - Estimated contract values

### Tab Navigation

The dashboard now uses a tabbed interface with five main tabs:

1. **Market Overview** (default tab)
   - Contains executive summary metrics and key visualizations
2. **Agency Intelligence**

   - Agency hierarchy analysis
   - Agency spending patterns
   - Set-aside utilization by agency

3. **Competitive Analysis**

   - Competitor-Agency relationships
   - Contract type success rates
   - Win rate analysis by vehicle type

4. **Contract Vehicle Analysis**

   - Vehicle preference by agency
   - Award type distributions
   - Success rates by contract type

5. **Geographic Analysis**
   - Regional spending patterns
   - Performance by location
   - Geographic concentration of awards

## Implementation Tasks

- [x] Design dashboard layout and component structure
- [x] Create base queries for NAICS 561210 data filtering
- [x] Implement executive summary metrics calculation
- [x] Develop combined obligations/award actions visualization
- [x] Build agency-to-obligation ratio scatter plot
- [x] Create contract vehicle distribution chart
- [x] Implement competitive landscape visualization
- [x] Develop upcoming opportunities timeline
- [x] Add global filtering functionality
- [x] Implement tab navigation for secondary analyses
- [x] Redesign sidebar layout with logical structure
- [x] Center metric card titles for improved readability
- [x] Implement placeholder navigation system
- [x] Add About section to sidebar
- [ ] Add drill-down capabilities to all charts
- [ ] Optimize query performance for large datasets
- [ ] Implement export functionality for reports
- [ ] Add user preference saving for filter settings
- [ ] Create user documentation for dashboard features

## Data Requirements

The dashboard requires the following base data from the usaspending_cleaned table:

- Award actions (where Modification No = '0')
- Federal action obligations
- Agency hierarchies (awarding and funding)
- Contract vehicle types
- Award dates and periods of performance
- Recipient information
- NAICS codes (filtered to 561210 by default)

## Technical Approach

- Streamlit for frontend interface
- Plotly for interactive visualizations
- PostgreSQL for data queries with optimized indexes
- Caching of frequently accessed data for performance
- Responsive design for various screen sizes
- Session state management for filter persistence

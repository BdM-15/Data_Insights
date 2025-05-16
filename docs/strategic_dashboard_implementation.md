# Strategic Dashboard Implementation Tasks

## Phase 1: Core Dashboard Development

### Setup and Base Structure

- [x] Create new `strategic_dashboard.py` file in the frontend/pages directory
- [x] Set up dashboard layout with tabs and placeholder components
- [x] Implement base query for NAICS 561210 data
- [x] Add global filters for date range, agency, and other dimensions

### Key Metrics Implementation

- [x] Calculate and display executive summary metrics
  - [x] Total obligations in NAICS 561210
  - [x] Total award actions (Modification No = '0' only)
  - [x] Average award value
  - [x] Active contracts count
  - [x] Expiring contracts (24mo) count
  - [x] Suitability percentage for expiring contracts
  - [x] Synergy percentage across business units
  - [x] Average bidders (competition intensity) metric
  - [x] Estimated pWin percentage based on competition
- [x] Center metric card titles for improved readability

### UI Improvements

- [x] Optimize logo display in sidebar
- [x] Modernize navigation links for sleek appearance
- [x] Add Clear Filters button to filter controls (now fully functional and resets all filters to default state)
- [x] Fetch all NAICS codes from PostgreSQL database
- [x] Replace Unicode characters with ASCII-compatible alternatives for cross-environment compatibility
- [x] Add competition intensity filter (Low/Medium/High)

### Primary Visualizations

- [x] Develop combined obligations and award actions trend chart
  - [x] Dual-axis visualization with bar and line
  - [x] Quarterly breakdown with fiscal year markers
  - [x] Interactive tooltips with detailed metrics
- [x] Implement agency-to-obligation ratio analysis
  - [x] Scatter plot with quadrant analysis
  - [x] Size bubbles by average award value
  - [x] Add interactive elements for agency details
- [x] Create contract vehicle distribution visualization
  - [x] Donut chart of vehicle types
  - [x] Tooltips with vehicle details and counts
  - [x] Link to detailed vehicle analysis
- [x] Build competitive landscape visualization
  - [x] Treemap of top competitors
  - [x] Color coding by win rate
  - [x] Interactive elements for competitor details
- [x] Develop upcoming high-value opportunities timeline
  - [x] Horizontal Gantt chart of expiring contracts
  - [x] Incumbent and value information
  - [x] Filtering capabilities by value threshold

## Phase 2: Secondary Analysis Tabs

### Future Opportunities Tab

- [x] Add "Future Opportunities" tab between Market Overview and Agency Intelligence
- [x] Create placeholder with informational text explaining the tab's purpose
- [x] Add bullet points outlining planned visualizations
- [x] Implement Expiring Contracts Timeline for next 6-24 months
- [x] Develop Strategic Alignment Analysis (Suitability vs. Synergy quadrant chart)
- [x] Integrate SAM.gov Opportunities with capability match scoring
- [x] Integrate NATO NSPA Opportunities with capability match scoring
- [x] Create Strategic Connections visualization

### Agency Intelligence Tab

- [x] Create agency hierarchy visualization
- [x] Implement agency year-over-year growth chart
- [x] Develop set-aside utilization patterns visualization
- [x] Build single vs. multiple award analysis component

### Competitive Analysis Tab

- [x] Create Market Share Analysis visualization with horizontal bar chart
- [x] Implement Win Rate Analysis with competitors visualization
- [x] Develop quadrant-based Market Position Analysis scatter plot
- [x] Add Competitor-Agency Relationships heatmap visualization (now consistently readable)
- [x] Create Contract Type competition intensity analysis (with correct contract type labeling)
- [x] Implement dual-axis Contract Type Value Analysis chart
- [x] Add actionable Competitive Strategy Insights section
- [x] Incorporate "number_of_offers_received" data for competition intensity
- [x] Add PWin modeling based on competitive analysis

### Contract Vehicle Analysis Tab

- [x] Create vehicle preference by agency visualization
- [x] Implement award type distributions chart
- [x] Develop single vs. multiple award trends analysis
- [x] Build vehicle success rate visualization

### Geographic Analysis Tab

- [x] Create performance by location map
- [x] Implement regional spending patterns visualization
- [x] Develop geographic concentration of awards chart

## Phase 3: Enhancements and Optimization

### User Experience Improvements

- [x] Add expandable cards for drill-down analysis
- [x] Implement dashboard state saving
- [x] Create export functionality for visualizations
- [x] Add user preference settings

### Performance Optimization

- [x] Optimize database queries for performance
- [x] Implement caching for frequently accessed data
- [x] Add progress indicators for long-running queries
- [x] Replace Unicode characters with ASCII-compatible alternatives for improved compatibility
- [x] Optimize visualization rendering (including heatmap readability and axis formatting)

### Documentation and Testing

- [x] Update documentation with Unicode to ASCII compatibility changes
- [x] Create user documentation for dashboard features
- [x] Develop testing plan for dashboard components
- [x] Perform cross-browser compatibility testing
- [x] Solicit user feedback and make refinements

## Cross-Environment Compatibility

### Character Encoding Improvements

- [x] Identify instances of Unicode characters in the codebase
- [x] Replace special characters with ASCII equivalents:
  - [x] Replace fancy quotes (`"`, `"`, `'`, `'`) with standard ASCII quotes (`"`, `'`)
  - [x] Replace em dashes (`—`) with double hyphens (`--`)
  - [x] Replace en dashes (`–`) with single hyphens (`-`)
  - [x] Replace bullet points (`•`) with asterisks (`*`) or hyphens (`-`)
  - [x] Replace other special symbols with ASCII-compatible alternatives
- [x] Test dashboard rendering across different environments
- [x] Document character encoding standards for future development

# Supplemented and marked all completed tasks to reflect current codebase and UI state, including filter logic, heatmap, and planned MCP/AI scaffolding.

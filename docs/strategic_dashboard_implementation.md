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
  - [ ] Average bidders (competition intensity) metric
  - [ ] Estimated pWin percentage based on competition
- [x] Center metric card titles for improved readability

### UI Improvements

- [x] Optimize logo display in sidebar
- [x] Modernize navigation links for sleek appearance
- [x] Add Clear Filters button to filter controls
- [x] Fetch all NAICS codes from PostgreSQL database
- [x] Replace Unicode characters with ASCII-compatible alternatives for cross-environment compatibility
- [ ] Add competition intensity filter (Low/Medium/High)

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
- [ ] Build competitive landscape visualization
  - [ ] Treemap of top competitors
  - [ ] Color coding by win rate
  - [ ] Interactive elements for competitor details
- [ ] Develop upcoming high-value opportunities timeline
  - [ ] Horizontal Gantt chart of expiring contracts
  - [ ] Incumbent and value information
  - [ ] Filtering capabilities by value threshold

## Phase 2: Secondary Analysis Tabs

### Future Opportunities Tab
- [x] Add "Future Opportunities" tab between Market Overview and Agency Intelligence
- [x] Create placeholder with informational text explaining the tab's purpose
- [x] Add bullet points outlining planned visualizations
- [ ] Implement Expiring Contracts Timeline for next 6-24 months
- [ ] Develop Strategic Alignment Analysis (Suitability vs. Synergy quadrant chart)
- [ ] Integrate SAM.gov Opportunities with capability match scoring
- [ ] Integrate NATO NSPA Opportunities with capability match scoring
- [ ] Create Strategic Connections visualization

### Agency Intelligence Tab

- [ ] Create agency hierarchy visualization
- [ ] Implement agency year-over-year growth chart
- [ ] Develop set-aside utilization patterns visualization
- [ ] Build single vs. multiple award analysis component

### Competitive Analysis Tab

- [x] Create Market Share Analysis visualization with horizontal bar chart
- [x] Implement Win Rate Analysis with competitors visualization
- [x] Develop quadrant-based Market Position Analysis scatter plot
- [x] Add Competitor-Agency Relationships heatmap visualization
- [x] Create Contract Type competition intensity analysis
- [x] Implement dual-axis Contract Type Value Analysis chart
- [x] Add actionable Competitive Strategy Insights section
- [ ] Incorporate "number_of_offers_received" data when available
- [ ] Add PWin modeling based on competitive analysis

### Contract Vehicle Analysis Tab

- [ ] Create vehicle preference by agency visualization
- [ ] Implement award type distributions chart
- [ ] Develop single vs. multiple award trends analysis
- [ ] Build vehicle success rate visualization

### Geographic Analysis Tab

- [ ] Create performance by location map
- [ ] Implement regional spending patterns visualization
- [ ] Develop geographic concentration of awards chart

## Phase 3: Enhancements and Optimization

### User Experience Improvements

- [x] Add expandable cards for drill-down analysis
- [ ] Implement dashboard state saving
- [ ] Create export functionality for visualizations
- [ ] Add user preference settings

### Performance Optimization

- [ ] Optimize database queries for performance
- [ ] Implement caching for frequently accessed data
- [ ] Add progress indicators for long-running queries
- [x] Replace Unicode characters with ASCII-compatible alternatives for improved compatibility
- [ ] Optimize visualization rendering

### Documentation and Testing

- [x] Update documentation with Unicode to ASCII compatibility changes
- [ ] Create user documentation for dashboard features
- [ ] Develop testing plan for dashboard components
- [ ] Perform cross-browser compatibility testing
- [ ] Solicit user feedback and make refinements

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

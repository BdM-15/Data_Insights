# TASK.md

## Active Tasks
- **Fix type mismatch error in "Contracts Expiring in the Next 24 Months" section**:
  - Status: Fixed in the latest code snippet but not yet tested.
  - Sub-task: Test the updated code to ensure the section renders correctly.
- **Render remaining visualizations**:
  - "Top Recipients by Total Awards Made"
  - "Top Recipients by Total Contract Award Amount"
  - "Top NAICS by Award Actions"
  - "Top NAICS by Total Contract Award Amount"
  - Agency/Sub-Agency/Office visuals
  - Status: Implemented but not rendered due to the type mismatch error.

## Backlog
- **Implement "Generate Capture Profile" feature**:
  - Sub-tasks:
    - Add row selection in the "Query Results" DataFrame.
    - Integrate Ollama for local LLM inference on GTX 4060 with CUDA.
    - Use `python-docx` to generate a Word document with contract details, analysis, and AI-generated narratives.
    - Ensure all processing is local for privacy.
  - Status: Planned, waiting for user confirmation to proceed.
- **Add advanced filtering**:
  - Implement keyword search for contract descriptions.
  - Add multi-select filters for NAICS/PSC codes.
  - Status: Planned.
- **Enhance visualizations**:
  - Add interactive features (e.g., tooltips, drill-downs).
  - Add new visuals for contract type, extent competed, or set-aside type trends.
  - Status: Planned.
- **Optimize performance**:
  - Explore lazy loading or pagination for large datasets.
  - Review database indexes for further optimization.
  - Status: Planned.

## Milestones
- **Milestone 1: Core Functionality Complete**:
  - Query and filter data.
  - Display results in a DataFrame with CSV export.
  - Render all visualizations.
  - Status: In progress (pending fix for "Contracts Expiring in the Next 24 Months" and rendering of remaining visuals).
- **Milestone 2: Capture Profile Feature**:
  - Implement row selection and Word document generation with AI narratives.
  - Status: Planned.
- **Milestone 3: Advanced Features and Optimization**:
  - Add advanced filtering and enhanced visualizations.
  - Optimize performance for large datasets.
  - Status: Planned.
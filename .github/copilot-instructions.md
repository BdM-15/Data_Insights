# GitHub Copilot Instructions for Data_Insights Project

## Project Context

Business intelligence application for defense contractors focusing on logistics, operations, maintenance, and technology solutions. Provides visualization and insights for business development and capture management.

## Project Vision & Architecture

- **Data Exploration**: Enable filtering of contract data by dimensions (date range, agency, contractor, NAICS/PSC)
- **Visual Insights**: Provide visualizations for spending trends, top recipients/NAICS/agencies, expiring contracts
- **Capture Profile Generation**: Generate Word documents with details, analysis, and AI-generated narratives
- **Privacy**: All processing must remain local for security (no external API calls for AI)
- **Hardware Optimization**: Utilize 64GB RAM and NVIDIA GTX 4060 GPU with CUDA for local LLM inference

### Architecture Components

- **Frontend**: Streamlit for web interface (filters, DataFrames, visualizations)
- **Database**: PostgreSQL (migrated from SQLite) with optimized tables and indexes
- **AI Integration**: Ollama for local LLM inference with models like llama2/mistral
- **External Data**: Planned integrations with SAM.gov, SBA SubNet, GovWin IQ, Bloomberg Government
- **AI Agents**: Model Context Protocol (MCP) integration with specialized tools:
  - Web Intelligence Scraper for market research
  - Document Creator/Editor for multiple formats
  - Visualization Tool for interactive data insights
  - Analysis/Reasoning Tool for strategic assessment

## Development Rules

### Code Structure & Organization

- Keep files under 500 lines of code
- Organize by feature or responsibility
- Use relative imports within packages
- Maintain consistent file structure

### Coding Standards

- Python as primary language with PEP8 and black formatting
- Use type hints and pydantic for data validation
- Write Google-style docstrings
- Include "# Reason:" comments for complex logic

### Naming Conventions

- Use descriptive variable names reflecting purpose (e.g., `contract_count` instead of `x`)
- Include context in names (counter, index, total)
- Only use single-letter names for loop variables (i, j)

### Testing

- Create Pytest unit tests covering expected use, edge cases, and failures
- Place in /tests folder mirroring the app structure

### Technologies

- FastAPI for APIs
- SQLAlchemy/SQLModel for ORM
- Streamlit for dashboards
- Pandas/NumPy for data processing
- Matplotlib/Plotly/Altair for visualizations

### Performance & Architecture

- Optimize database queries and data processing
- Consider hardware acceleration where applicable
- Use modular code with clear separation of concerns
- Plan for scalability and future enhancements

### AI Integration

- Support local LLMs and Model Context Protocol
- Design for AI-augmented data analysis
- Enable AI-driven insights and recommendations
- Use Ollama for local inference on GTX 4060 with CUDA
- Implement specialized AI agents for web intelligence, document creation, visualization, and analysis

### Documentation

- Update README.md when adding features, changing dependencies, or modifying setup
- Maintain PLANNING.md when architecture changes or project vision evolves
- Comment non-obvious code
- Explain complex logic with inline "# Reason:" comments
- Document all functions and modules thoroughly

### Project Management

- Track completed tasks in TASK.md
- Add discovered sub-tasks under "Discovered During Work" section

### User Experience

- Prioritize intuitive navigation and clear visualizations
- Ensure responsive and accessible interface

### AI Behavior Rules

- Never assume missing context; ask questions if uncertain
- Use only known, verified Python packages
- Confirm file paths and module names exist before referencing
- Don't delete/overwrite existing code unless explicitly instructed or in TASK.md

## Code Patterns

### Function Pattern

```python
def process_award_data(award_df: pd.DataFrame, filters: dict = None) -> pd.DataFrame:
    """
    Process award data by applying filters and aggregations.

    Args:
        award_df: DataFrame containing award data
        filters: Dictionary of column:value pairs to filter on

    Returns:
        Processed DataFrame with relevant aggregations
    """
    # Implementation
```

### Class Pattern

```python
class DataProcessor:
    """Handles data processing operations for contract awards."""

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize with configuration.

        Args:
            config: Configuration dictionary with processing parameters
        """
        self.config = config

    def process(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Process the input data according to configuration.

        Args:
            data: Input DataFrame to process

        Returns:
            Processed DataFrame
        """
        # Implementation
```

## Planned Features

- **Capture Profile Generator**: AI-assisted document creation with contract details and win strategies
- **MCP Integration**: Local AI agents for web scraping, document creation, visualization, and analysis
- **External Data Integration**: SAM.gov, SBA SubNet, GovWin IQ, Bloomberg Government APIs
- **Capture Management Enhancements**: Pipeline building, opportunity qualification, teaming partner identification
- **Milestone Implementation**: Follow the milestone structure in TASKS.md for project progression

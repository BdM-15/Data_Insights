"""
Pydantic models for data validation in Data Insights.
Define all data schemas used in data processing modules here.
Each model includes a comment describing its purpose and where it is used in the application.
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import date, datetime

# ---------------- MCP Tool Input/Output Models ----------------

# Expanded MCP Tool Input/Output Models (grouped here for clarity)
class QueryDatabaseInput(BaseModel):
    """Input schema for the query_database MCP tool."""
    sql_query: str

class QueryDatabaseOutput(BaseModel):
    """Output schema for the query_database MCP tool."""
    results: List[Dict[str, Any]]

class ListTablesInput(BaseModel):
    """Input schema for the list_tables MCP tool (no parameters)."""
    pass

class ListTablesOutput(BaseModel):
    """Output schema for the list_tables MCP tool."""
    tables: List[Dict[str, Any]]

class DescribeTableInput(BaseModel):
    """Input schema for the describe_table MCP tool."""
    table_name: str
    schema_name: str = 'public'

class DescribeTableOutput(BaseModel):
    """Output schema for the describe_table MCP tool."""
    columns: List[Dict[str, Any]]

class GetTableSampleInput(BaseModel):
    """Input schema for the get_table_sample MCP tool."""
    table_name: str
    schema_name: str = 'public'
    limit: int = 10

class GetTableSampleOutput(BaseModel):
    """Output schema for the get_table_sample MCP tool."""
    sample: List[Dict[str, Any]]

class GetDatabaseSchemaInput(BaseModel):
    """Input schema for the get_database_schema MCP tool (no parameters)."""
    pass

class GetDatabaseSchemaOutput(BaseModel):
    """Output schema for the get_database_schema MCP tool."""
    schema: str

class GetDatabaseStatsInput(BaseModel):
    """
    Input schema for the get_database_stats MCP tool.
    (No parameters required for this tool, but defined for consistency and future extensibility.)
    Used by the agent in capture_intelligence_agent.py to validate tool input.
    """
    pass

class GetDatabaseStatsOutput(BaseModel):
    """
    Output schema for the get_database_stats MCP tool.
    Used by the agent in capture_intelligence_agent.py to validate tool output.
    """
    stats: List[Dict[str, str]] = Field(description="List of database statistics with metric and value fields")
    
    @classmethod
    def from_raw_list(cls, raw_stats: List[Dict[str, str]]) -> 'GetDatabaseStatsOutput':
        """Create from the raw list format returned by the MCP tool."""
        return cls(stats=raw_stats)

# ---------------- Agentic LLM Intent Model (for Tool Routing) ----------------

class AgenticIntent(BaseModel):
    """
    Unified intent schema for agentic LLM output.
    Used by the backend tool router to dispatch requests to the correct agent/tool.
    Can also be used as a generic input schema for agent tool calls, if the tool expects a flexible set of parameters.
    """
    intent: str  # e.g., 'data_query', 'visualization', 'note', 'document', 'analysis'
    tool: Optional[str] = None  # Optional: explicit tool/agent name if LLM specifies
    parameters: Dict[str, Any] = Field(default_factory=dict)  # All other parameters (filters, chart_type, etc.)
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    page: Optional[str] = None
    tab: Optional[str] = None
    # Reason: This model allows the LLM to flexibly specify any action/tool/parameters for dynamic routing and can be extended for tool input validation.

class FlexibleIntent(BaseModel):
    """
    Advanced intent schema for LLM-driven decision making and multi-step workflows.
    Replaces rigid routing with intelligent, context-aware orchestration.
    """
    intent: str  # Primary intent (e.g., 'analyze_contracts', 'generate_report', 'multi_step_analysis')
    approach: str  # LLM's chosen approach: 'conversational', 'single_tool', 'multi_step', 'workflow'
    reasoning: str  # LLM's explanation of its decision-making process
    confidence: float = Field(ge=0.0, le=1.0)  # LLM's confidence in its analysis (0.0 to 1.0)
    
    # Tool orchestration
    primary_tool: Optional[str] = None  # Main tool/capability to use
    secondary_tools: List[str] = Field(default_factory=list)  # Additional tools needed
    tool_sequence: List[Dict[str, Any]] = Field(default_factory=list)  # Ordered execution plan
    
    # Context and parameters
    parameters: Dict[str, Any] = Field(default_factory=dict)  # Tool-specific parameters
    context: Dict[str, Any] = Field(default_factory=dict)  # Additional context for execution
    
    # Session information
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    page: Optional[str] = None
    tab: Optional[str] = None
    
    # Execution metadata
    expected_output: Optional[str] = None  # What the LLM expects to produce
    fallback_strategy: Optional[str] = None  # What to do if primary approach fails
    requires_user_input: bool = False  # Whether additional user input is needed


# Models for data related to 'agencies.py' (used for agency summary and charting in dashboard)
class TopAgencyByCount(BaseModel):
    parent_award_agency_name: str
    award_count: int

class TopAgencyByObligation(BaseModel):
    parent_award_agency_name: str
    federal_action_obligation: float

class AgencyRatioMetrics(BaseModel):
    """Used for agency ratio metrics visualizations in dashboard (bubble/scatter charts)."""
    parent_award_agency_name: str  # Display/label
    award_count: int  # Data (Award Actions)
    federal_action_obligation: float  # Data (Obligations)
    avg_award_value: float  # Data (Avg Award Value)
    # --- Charting/Plotting only ---
    scatter_size: float  # Bubble size for chart
    award_count_normalized: float  # X axis (log scale)
    obligation_normalized: float  # Y axis (log scale)

# Model for data related to 'queries.py' (e.g., output of get_naics_data, used in NAICS summary tables)
class NAICSData(BaseModel):
    naics_code: str
    naics_description: Optional[str] = None # Description might be optional or not always present

# Models for data related to 'awards.py' (used for award summary and trends in dashboard)
class AwardSummaryItem(BaseModel):
    category: str
    value: float
    count: Optional[int] = None

class QuarterlyTrend(BaseModel):
    """Used for quarterly obligation/award trend charts in dashboard."""
    quarter: str # e.g., "Q1"
    year: int
    total_obligation: float
    award_count: int

class ProjectionTrend(BaseModel):
    """Used for projected trends and market forecasting visualizations."""
    quarter: str # e.g., "2026-Q1"
    year: int
    total_obligation: float
    award_count: int
    is_projection: bool = True  # Distinguishes from historical data
    suitability_obligation: Optional[float] = None  # Potential market share based on suitability percentage

class ContractVehicleSummary(BaseModel):
    """Used for contract vehicle breakdowns in dashboard visualizations."""
    contract_vehicle: str 
    award_count: int
    percentage: float # Added to reflect original script's functionality

class RecipientAwardCount(BaseModel):
    """Used for recipient award count summaries in dashboard tables/charts."""
    recipient_identifier: str 
    award_count: int

class RecipientObligation(BaseModel):
    """Used for recipient obligation summaries in dashboard tables/charts."""
    recipient_identifier: str
    total_obligation: float

class ExpiringContract(BaseModel):
    """Used for expiring contract tables and alerts in dashboard."""
    contract_award_unique_key: str 
    recipient_name: Optional[str] = None
    period_of_performance_current_end_date: date
    potential_total_value_of_award: Optional[float] = None 
    days_to_expiration: int

# Models for data related to 'competition.py' (used for competitive landscape visualizations)
class TreemapNode(BaseModel):
    """Used for treemap visualizations of competition in dashboard."""
    id: str
    parent: Optional[str] = None # Root nodes might not have a parent
    value: float
    name: str

class TreemapPathElement(BaseModel):
    """Used for treemap path details in competition visualizations."""
    recipient_parent_name: Optional[str] = None
    recipient_name: str
    funding_sub_agency_name: Optional[str] = None
    transaction_description: str
    federal_action_obligation: float
    award_count: Optional[int] = None
    market_share: Optional[float] = None
    win_rate: Optional[float] = None

class SunburstPathElement(BaseModel):
    """Data model for sunburst chart showing hierarchical competitive landscape."""
    recipient_parent_name: Optional[str] = None
    recipient_name: str
    funding_sub_agency_name: Optional[str] = None
    transaction_description: str
    federal_action_obligation: float
    award_count: Optional[int] = None
    market_share: Optional[float] = None
    win_rate: Optional[float] = None

class SankeyFlowElement(BaseModel):
    """Data model for sankey diagram showing flow from companies to agencies to contracts."""
    recipient_parent_name: Optional[str] = None
    recipient_name: str
    funding_sub_agency_name: Optional[str] = None
    transaction_description: str
    federal_action_obligation: float
    award_count: Optional[int] = None
    market_share: Optional[float] = None
    win_rate: Optional[float] = None

# Model for data related to competitor performance analysis in 'competition.py' (used for competitor tables)
class CompetitorPerformance(BaseModel):
    """Used for competitor performance tables in dashboard."""
    recipient_name: str
    market_share: float # Percentage
    win_rate: float # Percentage
    federal_action_obligation: float # Total obligations for this recipient

class FutureOpportunity(BaseModel):
    """Represents a future government contracting opportunity (e.g., from SAM.gov, NATO NSPA). Used in opportunity pipeline and enrichment."""
    opportunity_id: str
    title: str
    agency: str
    sub_agency: Optional[str] = None
    office: Optional[str] = None
    naics_code: Optional[str] = None
    naics_description: Optional[str] = None
    solicitation_number: Optional[str] = None
    type_of_set_aside: Optional[str] = None
    contract_type: Optional[str] = None
    estimated_value: Optional[float] = None
    posted_date: Optional[date] = None
    response_due_date: Optional[date] = None
    anticipated_award_date: Optional[date] = None
    status: Optional[str] = None
    synopsis: Optional[str] = None
    url: Optional[str] = None
    source: Optional[str] = None  # e.g., 'SAM.gov', 'NATO NSPA'
    # Add more fields as needed for future extensibility
    
# ---------------- Prime Award Data Models for Capability Gap Analysis ----------------

class PrimeCompetitorDetails(BaseModel):
    """Competitor details for a prime award record. Used in capability gap analysis and reporting."""
    recipient_name: Optional[str]
    recipient_uei: Optional[str]
    recipient_parent_name: Optional[str]
    recipient_parent_uei: Optional[str]

class PrimeContractAwardDetails(BaseModel):
    """Core award details for a prime contract record. Used in prime contract data processing and reporting."""
    embedding: Optional[List[float]] = None  # For semantic search/vector storage
    created_at: Optional[date] = None
    updated_at: Optional[date] = None
    source: Optional[str] = None  # Provenance tracking
    contract_transaction_unique_key: str  # Unique transaction key (primary key)
    contract_award_unique_key: Optional[str]  # Unique award key
    action_date_fiscal_year: Optional[str]
    action_date: Optional[date]
    parent_award_id_piid: Optional[str]
    award_id_piid: Optional[str]
    modification_number: Optional[str]
    federal_action_obligation: Optional[float]
    total_dollars_obligated: Optional[float]
    potential_total_value_of_award: Optional[float]
    total_outlayed_amount_for_overall_award: Optional[float]
    period_of_performance_start_date: Optional[date]
    period_of_performance_current_end_date: Optional[date]
    period_of_performance_potential_end_date: Optional[date]
    ordering_period_end_date: Optional[date]
    primary_place_of_performance_city_name: Optional[str]
    primary_place_of_performance_state_code: Optional[str]
    action_type: Optional[str]
    award_type: Optional[str]
    type_of_idc: Optional[str]
    idv_type: Optional[str]
    undefinitized_action: Optional[str]
    multi_year_contract: Optional[str]
    multiple_or_single_award_idv: Optional[str]
    usaspending_permalink: Optional[str]
    type_of_contract_pricing: Optional[str]

class PrimeContractRequirementDetails(BaseModel):
    """Requirement and classification details for a prime contract record. Used in requirement analysis and reporting."""
    prime_award_base_transaction_description: Optional[str]
    transaction_description: Optional[str]
    naics_code: Optional[str]
    naics_description: Optional[str]
    product_or_service_code: Optional[str]
    product_or_service_code_description: Optional[str]
    dod_acquisition_program_description: Optional[str]
    sam_gov_link: Optional[str]

class PrimeCustomerDetails(BaseModel):
    """Customer and agency details for a prime contract record. Used in customer/agency analysis."""
    parent_award_agency_name: Optional[str]
    awarding_sub_agency_name: Optional[str]
    awarding_office_name: Optional[str]
    funding_agency_name: Optional[str]
    funding_sub_agency_name: Optional[str]
    funding_office_name: Optional[str]

class PrimeSolicitationDetails(BaseModel):
    """Solicitation and competition details for a prime contract record. Used in competition analysis."""
    solicitation_date: Optional[date]
    solicitation_procedures: Optional[str]
    extent_competed: Optional[str]
    type_of_set_aside: Optional[str]
    fair_opportunity_limited_sources: Optional[str]
    other_than_full_and_open_competition: Optional[str]
    number_of_offers_received: Optional[int]
    subcontracting_plan: Optional[str]
    government_furnished_property: Optional[str]

# ---------------- Subaward Data Models for Capability Gap Analysis ----------------

class SubcontractAwardDetails(BaseModel):
    """Core award details for a subaward (subcontract) record. Used in subaward data processing and reporting."""
    embedding: Optional[List[float]] = None  # For semantic search/vector storage
    created_at: Optional[date] = None
    updated_at: Optional[date] = None
    source: Optional[str] = None  # Provenance tracking
    prime_award_unique_key: Optional[str]  # Join key to prime awards
    subaward_type: Optional[str]
    subaward_number: Optional[str]
    subaward_amount: Optional[float]
    subaward_action_date: Optional[date]
    subaward_action_date_fiscal_year: Optional[str]

class SubcontractCompetitorDetails(BaseModel):
    """Competitor (subawardee) information for a subaward record. Used in subaward competition analysis."""
    subawardee_uei: Optional[str]
    subawardee_name: Optional[str]
    subawardee_dba_name: Optional[str]
    subawardee_parent_uei: Optional[str]
    subawardee_parent_name: Optional[str]
    subawardee_country_code: Optional[str]
    subawardee_country_name: Optional[str]
    subawardee_city_name: Optional[str]
    subawardee_state_code: Optional[str]
    subawardee_business_types: Optional[str]

class SubcontractRequirementsDetails(BaseModel):
    """Requirement and place of performance details for a subaward record. Used in subaward requirement analysis."""
    metadata: Optional[dict] = None  # For unstructured or enriched data

# ---------------- Document Model for RAG/Web Enrichment ----------------
class Document(BaseModel):
    """Generic document/attachment model for RAG, web enrichment, and semantic search. Used in document enrichment and retrieval."""
    document_id: str
    related_contract_id: Optional[str] = None
    text: Optional[str] = None
    embedding: Optional[List[float]] = None
    source_url: Optional[str] = None
    document_type: Optional[str] = None
    created_at: Optional[date] = None
    updated_at: Optional[date] = None
    metadata: Optional[dict] = None
    subaward_primary_place_of_performance_city_name: Optional[str]
    subaward_primary_place_of_performance_state_code: Optional[str]
    subaward_description: Optional[str]

# ---------------- Company Performance Metrics for Capability Stance ----------------

class TopEntitySummary(BaseModel):
    """Used for top entity summaries in company performance metrics and dashboard tables."""
    name: str
    count: int
    value: float

class CompanyPerformanceMetrics(BaseModel):
    """Used for company performance metrics and capability stance analysis in dashboard."""
    total_prime_awards: int
    total_prime_obligation: float
    total_subawards_received: int
    total_subawards_received_value: float
    total_subawards_issued: int
    total_subawards_issued_value: float
    unique_naics_prime: int
    unique_naics_sub: int
    unique_naics_issued: int
    unique_psc_prime: int
    unique_psc_sub: int
    unique_psc_issued: int
    top_agencies_prime: Optional[List[TopEntitySummary]]
    top_agencies_sub: Optional[List[TopEntitySummary]]
    top_agencies_issued: Optional[List[TopEntitySummary]]
    top_teaming_partners_prime: Optional[List[TopEntitySummary]]
    top_teaming_partners_sub: Optional[List[TopEntitySummary]]
    recent_activity_months: int = 60

class ChatRequest(BaseModel):
    """Request model for chat endpoint (chat with the data). Used in MCP chat server and frontend chat UI."""
    user_prompt: str
    page: str
    tab: str
    session_id: Optional[str] = None
    prompt_structure: Optional[Dict[str, Any]] = None
    user_id: Optional[str] = None

class ChatResponse(BaseModel):
    """Response model for chat endpoint (chat with the data). Used in MCP chat server and frontend chat UI."""
    answer: str
    plotly_json: Optional[Dict[str, Any]] = None
    llm_generated_code: Optional[str] = None
    response_type: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class NoteRequest(BaseModel):
    """Request model for adding a user note via the /note endpoint. Used in MCP chat server and frontend chat UI."""
    note_text: str
    page: str
    tab: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None

class NoteDeleteRequest(BaseModel):
    """Request model for deleting a user note by ID via the /notes/delete endpoint."""
    id: int

class NoteUpdateRequest(BaseModel):
    """Request model for updating a user note by ID via the /notes/update endpoint."""
    id: int
    note_text: str

class ChatHistoryRequest(BaseModel):
    """Request model for retrieving chat history via the /chat/history endpoint."""
    page: str
    tab: str
    session_id: Optional[str] = None
    user_id: Optional[str] = None

class VisualizationRequest(BaseModel):
    """Request model for generating a custom visualization via the /visualization endpoint."""
    user_prompt: str  # Description of the chart/plot the user wants
    page: Optional[str] = None  # Optional: page context
    tab: Optional[str] = None   # Optional: tab context
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    data_filters: Optional[Dict[str, Any]] = None  # Optional: filters to apply to the data
    chart_type: Optional[str] = None  # Optional: e.g., 'bar', 'line', 'pie', etc.
    # Reason: Allows flexible, extensible chart requests

class VisualizationResponse(BaseModel):
    """Response model for returning a generated visualization (e.g., Plotly JSON) to the frontend."""
    answer: str  # LLM or system-generated explanation/caption
    plotly_json: Optional[Dict[str, Any]] = None  # Plotly figure as JSON
    llm_generated_code: Optional[str] = None  # Python code used to generate the chart (if any)
    response_type: str = "visualization"  # Always 'visualization' for this endpoint
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class ProfileGenerateRequest(BaseModel):
    """Request model for AI-assisted capture profile document creation via /profile/generate endpoint."""
    opportunity_id: Optional[str] = None  # Link to a specific opportunity/contract
    user_prompt: Optional[str] = None  # Custom instructions or focus areas
    page: Optional[str] = None
    tab: Optional[str] = None
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    milestone: Optional[str] = None  # e.g., 'ms0', 'ms1', etc. for Shipley reviews
    # Reason: Allows both general and milestone-specific profile generation

class ProfileGenerateResponse(BaseModel):
    """Response model for returning a generated capture profile document or milestone review."""
    summary: str  # Executive summary or main narrative
    document_text: str  # Full document (Word/Markdown/plaintext)
    ai_analysis: Optional[str] = None  # Optional: AI-generated analysis or recommendations
    milestone: Optional[str] = None  # If this is a milestone review
    response_type: str = "profile"  # Always 'profile' for this endpoint
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class DataSummaryResponse(BaseModel):
    """Response model for quick dashboard stats/summaries via /data/summary endpoint."""
    total_contracts: int
    total_obligation: float
    top_agency: Optional[str] = None
    top_contractor: Optional[str] = None
    expiring_contracts: int
    last_updated: datetime
    # Reason: Can be extended with more summary fields as needed

class ServiceDiscoveryResponse(BaseModel):
    """Response model for service discovery information."""
    servers: List[Dict[str, Any]]
    total_servers: int
    healthy_servers: int
    total_capabilities: int
    discovery_time: Optional[str] = None


class DynamicToolResponse(BaseModel):
    """Response model for dynamically discovered tools."""
    tools: List[Dict[str, Any]]
    total_tools: int
    server_count: int
    last_updated: str
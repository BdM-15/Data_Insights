"""
Pydantic models for data validation in Data Insights.
Define all data schemas used in data processing modules here.
"""
from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import date

# Models for data related to 'agencies.py'
class TopAgencyByCount(BaseModel):
    parent_award_agency_name: str
    award_count: int

class TopAgencyByObligation(BaseModel):
    parent_award_agency_name: str
    federal_action_obligation: float

class AgencyRatioMetrics(BaseModel):
    parent_award_agency_name: str  # Display/label
    award_count: int  # Data (Award Actions)
    federal_action_obligation: float  # Data (Obligations)
    avg_award_value: float  # Data (Avg Award Value)
    # --- Charting/Plotting only ---
    scatter_size: float  # Bubble size for chart
    award_count_normalized: float  # X axis (log scale)
    obligation_normalized: float  # Y axis (log scale)

# Model for data related to 'queries.py' (e.g., output of get_naics_data)
class NAICSData(BaseModel):
    naics_code: str
    naics_description: Optional[str] = None # Description might be optional or not always present

# Models for data related to 'awards.py'
class AwardSummaryItem(BaseModel):
    category: str
    value: float
    count: Optional[int] = None

class QuarterlyTrend(BaseModel):
    quarter: str # e.g., "Q1"
    year: int
    total_obligation: float
    award_count: int

class ProjectionTrend(BaseModel):
    quarter: str # e.g., "2026-Q1"
    year: int
    total_obligation: float
    award_count: int
    is_projection: bool = True  # Distinguishes from historical data
    suitability_obligation: Optional[float] = None  # Potential market share based on suitability percentage

class ContractVehicleSummary(BaseModel):
    # Example: 'contract_award_type_name' or similar for contract_vehicle
    contract_vehicle: str 
    award_count: int
    percentage: float # Added to reflect original script's functionality

class RecipientAwardCount(BaseModel):
    # Assumes 'recipient_duns', 'recipient_name', or similar is used for grouping
    recipient_identifier: str 
    award_count: int

class RecipientObligation(BaseModel):
    recipient_identifier: str
    total_obligation: float

class ExpiringContract(BaseModel):
    # Using common unique key for contracts
    contract_award_unique_key: str 
    recipient_name: Optional[str] = None
    period_of_performance_current_end_date: date
    # Using potential total value, could also be obligated amount
    potential_total_value_of_award: Optional[float] = None 
    days_to_expiration: int

# Models for data related to 'competition.py'
class TreemapNode(BaseModel):
    id: str
    parent: Optional[str] = None # Root nodes might not have a parent
    value: float
    name: str

class TreemapPathElement(BaseModel):
    recipient_parent_name: Optional[str] = None
    recipient_name: str
    funding_sub_agency_name: Optional[str] = None
    transaction_description: str
    federal_action_obligation: float
    award_count: Optional[int] = None
    market_share: Optional[float] = None
    win_rate: Optional[float] = None

class SunburstPathElement(BaseModel):
    """
    Data model for sunburst chart showing hierarchical competitive landscape.
    Path: Parent Company → Subsidiary → Agency → Contract
    """
    recipient_parent_name: Optional[str] = None
    recipient_name: str
    funding_sub_agency_name: Optional[str] = None
    transaction_description: str
    federal_action_obligation: float
    award_count: Optional[int] = None
    market_share: Optional[float] = None
    win_rate: Optional[float] = None

class SankeyFlowElement(BaseModel):
    """
    Data model for sankey diagram showing flow from companies to agencies to contracts.
    Represents the source-target-value relationship for Sankey nodes and links.
    """
    recipient_parent_name: Optional[str] = None
    recipient_name: str
    funding_sub_agency_name: Optional[str] = None
    transaction_description: str
    federal_action_obligation: float
    award_count: Optional[int] = None
    market_share: Optional[float] = None
    win_rate: Optional[float] = None

# Model for data related to competitor performance analysis in 'competition.py'
class CompetitorPerformance(BaseModel):
    recipient_name: str
    market_share: float # Percentage
    win_rate: float # Percentage
    federal_action_obligation: float # Total obligations for this recipient

class FutureOpportunity(BaseModel):
    """Represents a future government contracting opportunity (e.g., from SAM.gov, NATO NSPA)."""
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
    """
    Competitor details for a prime award record.
    """
    recipient_name: Optional[str]
    recipient_uei: Optional[str]
    recipient_parent_name: Optional[str]
    recipient_parent_uei: Optional[str]


class PrimeContractAwardDetails(BaseModel):
    embedding: Optional[List[float]] = None  # For semantic search/vector storage
    created_at: Optional[date] = None
    updated_at: Optional[date] = None
    source: Optional[str] = None  # Provenance tracking
    """
    Core award details for a prime contract record.
    """
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
    """
    Requirement and classification details for a prime contract record.
    """
    prime_award_base_transaction_description: Optional[str]
    transaction_description: Optional[str]
    naics_code: Optional[str]
    naics_description: Optional[str]
    product_or_service_code: Optional[str]
    product_or_service_code_description: Optional[str]
    dod_acquisition_program_description: Optional[str]
    sam_gov_link: Optional[str]


class PrimeCustomerDetails(BaseModel):
    """
    Customer and agency details for a prime contract record.
    """
    parent_award_agency_name: Optional[str]
    awarding_sub_agency_name: Optional[str]
    awarding_office_name: Optional[str]
    funding_agency_name: Optional[str]
    funding_sub_agency_name: Optional[str]
    funding_office_name: Optional[str]


class PrimeSolicitationDetails(BaseModel):
    """
    Solicitation and competition details for a prime contract record.
    """
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
    embedding: Optional[List[float]] = None  # For semantic search/vector storage
    created_at: Optional[date] = None
    updated_at: Optional[date] = None
    source: Optional[str] = None  # Provenance tracking
    """
    Core award details for a subaward (subcontract) record.

    Attributes:
        prime_award_unique_key: Unique key for joining to the prime award
        subaward_type: Type of subaward (e.g., procurement, grant)
        subaward_number: Subaward identifier/number
        subaward_amount: Dollar value of the subaward
        subaward_action_date: Date the subaward was made
        subaward_action_date_fiscal_year: Fiscal year of the subaward action
    """
    prime_award_unique_key: Optional[str]  # Join key to prime awards
    subaward_type: Optional[str]
    subaward_number: Optional[str]
    subaward_amount: Optional[float]
    subaward_action_date: Optional[date]
    subaward_action_date_fiscal_year: Optional[str]


class SubcontractCompetitorDetails(BaseModel):
    """
    Competitor (subawardee) information for a subaward record.

    Attributes:
        subawardee_uei: Unique Entity Identifier for the subawardee
        subawardee_name: Name of the subawardee
        subawardee_dba_name: Doing Business As name for the subawardee
        subawardee_parent_uei: Parent UEI for the subawardee
        subawardee_parent_name: Parent company name for the subawardee
        subawardee_country_code: Country code of the subawardee
        subawardee_country_name: Country name of the subawardee
        subawardee_city_name: City of the subawardee
        subawardee_state_code: State code of the subawardee
        subawardee_business_types: Business types/socioeconomic categories
    """
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
    metadata: Optional[dict] = None  # For unstructured or enriched data
# ---------------- Document Model for RAG/Web Enrichment ----------------
class Document(BaseModel):
    """
    Generic document/attachment model for RAG, web enrichment, and semantic search.
    """
    document_id: str
    related_contract_id: Optional[str] = None
    text: Optional[str] = None
    embedding: Optional[List[float]] = None
    source_url: Optional[str] = None
    document_type: Optional[str] = None
    created_at: Optional[date] = None
    updated_at: Optional[date] = None
    metadata: Optional[dict] = None
    """
    Requirement and place of performance details for a subaward record.

    Attributes:
        subaward_primary_place_of_performance_city_name: City where work is performed
        subaward_primary_place_of_performance_state_code: State where work is performed
        subaward_description: Description of the subcontracted work
    """
    subaward_primary_place_of_performance_city_name: Optional[str]
    subaward_primary_place_of_performance_state_code: Optional[str]
    subaward_description: Optional[str]

# ---------------- Company Performance Metrics for Capability Stance ----------------

class TopEntitySummary(BaseModel):
    name: str
    count: int
    value: float

class CompanyPerformanceMetrics(BaseModel):
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
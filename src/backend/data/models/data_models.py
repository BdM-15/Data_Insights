"""
Pydantic models for data validation in Data Insights.
Define all data schemas used in data processing modules here.
"""
from pydantic import BaseModel
from typing import Optional, List
from datetime import date

# Models for data related to 'agencies.py'
class TopAgencyByCount(BaseModel):
    parent_award_agency_name: str
    award_count: int

class TopAgencyByObligation(BaseModel):
    parent_award_agency_name: str
    federal_action_obligation: float

class AgencyRatioMetrics(BaseModel):
    parent_award_agency_name: str
    award_count: int
    federal_action_obligation: float
    avg_award_value: float
    scatter_size: float
    award_count_normalized: float
    obligation_normalized: float
    award_count_original: int
    obligation_original: float

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

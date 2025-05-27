"""
Processor for fetching and filtering future opportunities (SAM.gov, NATO NSPA, etc.).
"""
from typing import List, Optional
from datetime import date
from src.backend.data.models.data_models import FutureOpportunity
import pandas as pd

# For now, use mock/sample data. Replace with real DB/API integration later.
def get_future_opportunities(
    agency: Optional[str] = None,
    naics_code: Optional[str] = None,
    min_value: Optional[float] = None,
    max_value: Optional[float] = None,
    status: Optional[str] = None,
    posted_after: Optional[date] = None,
    posted_before: Optional[date] = None,
    limit: int = 100
) -> List[FutureOpportunity]:
    """
    Fetch and filter future opportunities from the database or external sources.
    For now, returns mock/sample data for UI development.

    Args:
        agency: Filter by agency name
        naics_code: Filter by NAICS code
        min_value: Minimum estimated value
        max_value: Maximum estimated value
        status: Filter by opportunity status
        posted_after: Only include opportunities posted after this date
        posted_before: Only include opportunities posted before this date
        limit: Max number of results
    Returns:
        List of FutureOpportunity models
    """
    # Sample/mock data for prototyping
    sample_data = [
        FutureOpportunity(
            opportunity_id="SAM-001",
            title="Base Operations Support Services",
            agency="Department of Defense",
            sub_agency="Army",
            office="Fort Bragg Contracting",
            naics_code="561210",
            naics_description="Facilities Support Services",
            solicitation_number="W9124-25-R-0001",
            type_of_set_aside="8(a)",
            contract_type="IDIQ",
            estimated_value=12000000.0,
            posted_date=date(2025, 5, 10),
            response_due_date=date(2025, 6, 15),
            anticipated_award_date=date(2025, 9, 1),
            status="Active",
            synopsis="Base operations support for Fort Bragg, NC.",
            url="https://sam.gov/opp/SAM-001",
            source="SAM.gov"
        ),
        FutureOpportunity(
            opportunity_id="SAM-002",
            title="IT Support Services",
            agency="Department of Homeland Security",
            sub_agency="FEMA",
            office="IT Acquisitions",
            naics_code="541512",
            naics_description="Computer Systems Design Services",
            solicitation_number="HSFE60-25-R-0022",
            type_of_set_aside="SDVOSB",
            contract_type="Firm Fixed Price",
            estimated_value=3500000.0,
            posted_date=date(2025, 5, 1),
            response_due_date=date(2025, 5, 30),
            anticipated_award_date=date(2025, 8, 15),
            status="Active",
            synopsis="IT support for FEMA regional offices.",
            url="https://sam.gov/opp/SAM-002",
            source="SAM.gov"
        ),
        FutureOpportunity(
            opportunity_id="NSPA-001",
            title="European Logistics Support",
            agency="NATO NSPA",
            sub_agency=None,
            office=None,
            naics_code="541614",
            naics_description="Process, Physical Distribution, and Logistics Consulting Services",
            solicitation_number="NSPA-25-LOG-001",
            type_of_set_aside=None,
            contract_type="Multiple Award",
            estimated_value=8000000.0,
            posted_date=date(2025, 4, 20),
            response_due_date=date(2025, 6, 1),
            anticipated_award_date=date(2025, 10, 1),
            status="Active",
            synopsis="Logistics support for NATO operations in Europe.",
            url="https://nspa.nato.int/opp/NSPA-001",
            source="NATO NSPA"
        ),
    ]
    # Filtering logic (expand as needed)
    results = sample_data
    if agency:
        results = [o for o in results if o.agency == agency]
    if naics_code:
        results = [o for o in results if o.naics_code == naics_code]
    if min_value:
        results = [o for o in results if o.estimated_value and o.estimated_value >= min_value]
    if max_value:
        results = [o for o in results if o.estimated_value and o.estimated_value <= max_value]
    if status:
        results = [o for o in results if o.status == status]
    if posted_after:
        results = [o for o in results if o.posted_date and o.posted_date > posted_after]
    if posted_before:
        results = [o for o in results if o.posted_date and o.posted_date < posted_before]
    return results[:limit]

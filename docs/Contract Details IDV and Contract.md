# Data & Display Differences: IDV Capture Profile vs. Definitive Contract Profile

## 1. IDV (Indefinite Delivery Vehicle) Capture Profile

### Data Displayed
- **IDV Base Contract Details** (same as Definitive Contract Profile)
  - Contract ID, Contractor, Parent Company, UEI, Awarding/Funding Agency, NAICS Code/Description, Competition, Set Aside, Start/End Date
  - Key Metrics: Total Actions, Modifications, Total Obligated, Potential Value
  - Contract Actions Timeline (Action Date, Mod #, Action Value, Description)
  - Subawards Table (Subaward #, Subawardee, Amount, Date)
- **PLUS: Orders Analysis**
  - Total Orders, Active Orders, Total Actions, Modifications, Recent Orders (12mo)
  - Financials: Total Action Value, Total Obligated, Total Potential Value (across all orders)
  - Top Ordering Agencies (by order count)
  - Top Contractors (by actions)
  - Active Orders Table (Order ID, Contractor, Total Obligated, End Date)
  - All Orders Table (Order ID, Contractor, Total Obligated, Start/End Date)
  - Date Range for Orders (Earliest Start, Latest End)

**Why:**  
IDVs are umbrella contracts that function as definitive contracts but also have many child orders. All definitive contract details are relevant, but additional order-level analysis is critical for understanding utilization, pipeline, and competitive landscape.

---

## 2. Definitive Contract Profile

### Data Displayed
- **Contract Overview**
  - Contract ID, Contractor, Parent Company, UEI, Awarding/Funding Agency, NAICS Code/Description, Competition, Set Aside, Start/End Date
- **Key Metrics**
  - Total Actions, Modifications, Total Obligated, Potential Value
- **Contract Actions Timeline**
  - Table of all actions/modifications (Action Date, Mod #, Action Value, Description)
- **Subawards**
  - Table of subawards (Subaward #, Subawardee, Amount, Date)

**Why:**  
Definitive contracts are single-award, so focus is on the contract’s lifecycle, modifications, and subaward activity. This supports risk assessment, compliance, and performance tracking.

---

## 3. Pydantic Model Recommendations & Example

**Yes, use Pydantic models** for both profile types.  
- The IDV model should inherit all fields from the Definitive Contract model and add orders/analysis fields.

### Example Pydantic Models

```python
from typing import List, Optional
from pydantic import BaseModel
from datetime import date

class SubawardSummary(BaseModel):
    subaward_number: str
    subawardee_name: str
    subaward_amount: float
    subaward_date: date

class ActionSummary(BaseModel):
    action_date: date
    modification_number: str
    federal_action_obligation: float
    transaction_description: Optional[str]

class ContractSummary(BaseModel):
    contract_id: str
    contractor: str
    parent_company: Optional[str]
    uei: Optional[str]
    awarding_agency: str
    funding_agency: Optional[str]
    naics_code: Optional[str]
    naics_description: Optional[str]
    competition: Optional[str]
    set_aside: Optional[str]
    start_date: date
    end_date: date
    total_actions: int
    modifications: int
    total_obligated: float
    potential_value: float
    actions: List[ActionSummary]
    subawards: List[SubawardSummary]

class OrderSummary(ContractSummary):
    pass  # Same structure as ContractSummary for each order

class OrdersAnalysisSummary(BaseModel):
    total_orders: int
    active_orders: int
    total_actions: int
    total_modifications: int
    total_value: float
    total_obligated: float
    total_potential_value: float
    ordering_agencies: List[str]
    contractors: List[str]
    recent_orders: int
    earliest_start: Optional[date]
    latest_end: Optional[date]
    active_orders_list: List[OrderSummary]
    all_orders_list: List[OrderSummary]

class DefinitiveContractProfile(BaseModel):
    contract: ContractSummary

class IDVCaptureProfile(DefinitiveContractProfile):
    orders: List[OrderSummary]
    orders_analysis: OrdersAnalysisSummary
# CAPTUREINTEL.md

> NOTE: This document now contains (1) high-level strategic context, (2) structured table schemas, and (3) a narrative element-by-element reference. Where definitions appear in both a schema table and the later narrative list, the schema table should be treated as the canonical concise form; the narrative list offers expanded prose. Future edits should modify both only when substantive meaning changes.

## Table of Contents

1. [Purpose](#purpose)
2. [High-Level Vision](#high-level-vision)
3. [Competitive Edge](#competitive-edge)
4. [How They Create Insights and Drive Decisions](#how-they-create-insights-and-drive-decisions)
5. [Call Plan Feature](#call-plan-feature)
6. [Subaward Data Integration](#subaward-data-integration)
7. [SBA Mentor-Protégé Agreements Integration](#sba-mentor-protégé-agreements-integration)
8. [Data Dictionary Overview](#data-dictionary)
9. [Prime Awards Deduplicated Table Schema](#table-s2_interimusaspending_prime_awards_dedup)
10. [Subawards Enriched Table Schema](#table-s2_interimusaspending_subawards_enriched)
11. [LLM Fine-Tuning Guidance](#llm-fine-tuning-guidance-prime--subaward-tables)
12. [Expanded Narrative Element Reference](#expanded-narrative-element-reference)
13. [Shipley Capture Milestone Mapping](#shipley-capture-milestone-mapping)
14. [Advanced Pricing Analysis Integration](#advanced-pricing-analysis-integration)
15. [Strategic Default Dashboard Specification](#strategic-default-dashboard-specification)
16. [Offers Received Data Integration](#offers-received-data-integration)
17. [External Data Sources Integration](#external-data-sources-integration)
18. [Company Capabilities & Competitor Research](#company-capabilities-foundation--competitor-research-2025-update)
19. [SAM.gov Solicitation Enrichment Pipeline](#samgov-solicitation-enrichment-pipeline-may-2025)

## Purpose

To maximize the value of the 297 data elements, this document outlines a structured approach tailored to the needs of business development (identifying opportunities and building customer relationships) and capture management (winning specific contracts). The ultimate goal is to create comprehensive, AI-powered Capture Profiles that synthesize intelligence from multiple sources to support strategic decision-making and proposal development.

## High-Level Vision

- **Data Filtering and Segmentation**:

  - **Description**: Filter contracts by awarding agency (e.g., DoD and its sub-agencies like Army, Navy, Air Force). Narrow the scope using NAICS (North American Industry Classification System) and PSC (Product Service Code) codes relevant to logistics, operations, and technology solutions.
  - **Impact**: Ensures focus on relevant opportunities aligned with core competencies.
  - **Utility**: Helps prioritize contracts that match the contractor’s expertise.

- **Trend Analysis**:

  - **Description**: Examine historical spending patterns to identify growth or decline in key areas. Assess shifts in competition levels and contracting strategies.
  - **Impact**: Provides insights into market dynamics and procurement trends.
  - **Utility**: Guides strategic planning and resource allocation.

- **Competitor Analysis**:

  - **Description**: Identify incumbent contractors, their contract wins, and market share. Analyze competitor strengths based on contract size, type, and geographic focus.
  - **Impact**: Highlights competitive positioning and potential gaps.
  - **Utility**: Informs differentiation strategies and teaming opportunities.

- **Opportunity Identification**:

  - **Description**: Pinpoint contracts nearing their end dates for recompete opportunities. Highlight sole-source or low-competition contracts that may open to broader bidding in the future.
  - **Impact**: Enables proactive capture planning.
  - **Utility**: Increases chances of winning recompetes and new opportunities.

- **Geographic and Socioeconomic Analysis**:

  - **Description**: Map contract performance locations to target high-activity regions. Evaluate set-aside contracts to identify niche opportunities or teaming possibilities.
  - **Impact**: Focuses efforts on high-value regions and socio-economic niches.
  - **Utility**: Enhances regional strategies and small business partnerships.

- **Technology and Innovation Focus**:
  - **Description**: Analyze data elements related to emerging technologies to align with DoD investment trends.
  - **Impact**: Positions offerings in line with future priorities.
  - **Utility**: Drives innovation and R&D alignment.

## Competitive Edge

These data elements give the contractor an edge by enabling:

- **Proactive Opportunity Pursuit**: Early identification of recompetes and low-competition contracts.
- **Data-Driven Proposals**: Tailored bids reflecting customer history and competitor weaknesses.
- **Strategic Resource Allocation**: Focused efforts on high-value customers and regions.
- **Market Differentiation**: Insights into trends (e.g., technology adoption) to outpace competitors.

## How They Create Insights and Drive Decisions

Using these elements, the contractor can:

- **Identify High-Value Opportunities**:

  - **Description**: Filter by NAICS/PSC codes and award amounts to target lucrative contracts in logistics or technology solutions.
  - **Example**: A $50M contract for base operations maintenance expiring in 2025 becomes a priority target.

- **Understand Customer Preferences**:

  - **Description**: Analyze awarding offices and contract types to tailor proposals to DoD preferences (e.g., fixed-price vs. cost-reimbursement).
  - **Example**: Navy contracting offices favoring IDIQs prompt a focus on vehicle-based strategies.

- **Anticipate Recompetes**:

  - **Description**: Track end dates to position early for renewals.
  - **Example**: A logistics contract ending in 18 months triggers capture planning now.

- **Analyze Competitors**:

  - **Description**: Use contractor names and win patterns to benchmark against rivals.
  - **Example**: Competitor X dominates maintenance contracts at Fort Bragg, signaling a need for differentiation.

- **Optimize Geography**:

  - **Description**: Map performance locations to concentrate efforts in high-activity areas.
  - **Example**: Heavy contract concentration in Virginia suggests a regional office expansion.

- **Leverage Technology Trends**:
  - **Description**: If keywords exist, align offerings with DoD tech priorities (e.g., cloud computing).
  - **Example**: Increased spending on cybersecurity contracts drives R&D investment in that area.

## Call Plan Feature

A separate and distinct "Call Plan" feature will be developed to complement the Capture Profile, providing capture managers with structured planning tools for customer engagement. This feature will:

### Purpose

To provide capture managers with comprehensive preparation materials before engaging with potential customers, ensuring productive and targeted discussions.

### Key Components

- **Stakeholder Identification**:

  - **Description**: Automatically extract key personnel from contracts, including contracting officers, technical representatives, and program managers.
  - **Impact**: Ensures outreach to decision-makers and influencers.
  - **Utility**: Creates a contact map for effective relationship management.

- **Agency/Office Intelligence**:

  - **Description**: Compile recent news, budget information, and strategic priorities for the target agency or office.
  - **Impact**: Provides context for conversations and demonstrates understanding of customer challenges.
  - **Utility**: Enables more informed and relevant discussions.

- **Pain Points Analysis**:

  - **Description**: Identify potential challenges based on contract history, modifications, and performance patterns.
  - **Impact**: Positions the contractor as a problem-solver rather than just a service provider.
  - **Utility**: Guides conversation toward value-added solutions.

- **Relationship History**:

  - **Description**: Document past interactions, contract performance, and relationship status with the agency.
  - **Impact**: Provides continuity in customer engagement.
  - **Utility**: Prevents repetitive conversations and builds on previous interactions.

- **Talking Points and Questions**:

  - **Description**: Suggest targeted discussion topics and questions based on contract history and agency priorities.
  - **Impact**: Ensures productive meetings with clear objectives.
  - **Utility**: Increases likelihood of gathering valuable information.

- **Competitive Intelligence**:

  - **Description**: Summarize incumbent and competitor relationships with the target agency.
  - **Impact**: Helps position against competitors.
  - **Utility**: Informs differentiation strategies.

- **Follow-up Actions**:
  - **Description**: Template for documenting agreed actions, new information, and next steps.
  - **Impact**: Ensures accountability and continuity.
  - **Utility**: Supports systematic relationship development.

### Integration with Data Sources

The Call Plan will leverage both USAspending.gov data and external sources:

- Contract data will provide factual information about procurement history and key stakeholders
- News APIs will gather recent agency developments and announcements
- Congressional budget information will offer insights into funding priorities
- Agency strategic plans will align conversations with customer objectives

### Implementation Approach

The Call Plan feature will be implemented as a separate workflow that can be initiated after a Capture Profile is generated, allowing capture managers to prepare for specific customer engagements with targeted intelligence.

## Subaward Data Integration

### Purpose

To enhance competitive intelligence and relationship mapping by incorporating subaward data from USAspending.gov, providing visibility into prime-sub relationships across the federal contracting landscape.

### Implementation Approach

- **Data Source**: Subaward data will be extracted from USAspending.gov's API or bulk download files
- **Data Integration**: Subaward records will be joined with prime award data using award IDs as the linking field
- **Database Design**: A new `subawards` table will be created and related to the existing awards data

### Key Benefits

- **Relationship Mapping**: Identify which primes frequently partner with which subcontractors
- **Capability Gap Analysis**: Detect potential capability gaps by analyzing subcontracted work
- **Teaming Opportunity Identification**: Discover potential teaming partners based on complementary capabilities
- **Competitive Intelligence**: Understand competitor relationships and partnership strategies
- **Small Business Compliance**: Track small business subcontracting patterns and compliance with goals

### Impact on Existing Features

The integration of subaward data will enhance several existing components:

- **Competitor Analysis**: Will now include subcontractor relationships
- **Opportunity Identification**: Will consider teaming potential based on subcontracting patterns
- **Market Differentiation**: Will leverage insights into how competitors structure their teams

## SBA Mentor-Protégé Agreements Integration

### Purpose

To enhance competitive intelligence, teaming opportunity identification, and capability gap analysis by incorporating SBA Mentor-Protégé Agreement data from SBA.gov (https://www.sba.gov/document/support-active-mentor-protege-agreements).

### Implementation Approach

- **Data Source**: Downloadable spreadsheet from SBA.gov containing active Mentor-Protégé relationships
- **Data Integration**: New database tables to store mentor-protégé relationship data with regular updates
- **Database Design**: Creation of `sba_mentor_protege` tables to track these strategic partnerships

### Key Benefits

- **Strategic Teaming Opportunities**: Identify potential small business partners with established capabilities and active federal contracts
- **Competitor Partnership Intelligence**: Track which large businesses are mentoring which small businesses to understand competitive teaming strategies
- **Industry Capability Mapping**: Gain insights into complementary capabilities between mentors and protégés
- **Gap Analysis Support**: Identify where competitors have filled capability gaps through mentor-protégé relationships
- **Bid Strategy Enhancement**: Develop more competitive teaming approaches informed by industry partnership trends

### Impact on Existing Features

This data source will directly support and enhance multiple aspects of the Data Insights platform:

- **Capture Profile Development**: Include mentor-protégé relationship data in competitor analysis sections of capture profiles
- **Competitor Analysis**: Provide comprehensive mapping of competitor's small business partnerships and potential teaming strategies
- **Capability Gap Identification**: Identify patterns in how competitors address capability gaps through strategic partnerships
- **Teaming Partner Identification**: Discover potential small business partners for set-aside opportunities
- **Market Intelligence**: Gain insights into emerging industry trends based on mentor-protégé focus areas

### Data Elements

The SBA Mentor-Protégé database includes valuable data elements such as:

- **Protégé Name and Location**: Small business partner information
- **Protégé Business Type(s)**: Socio-economic designations (8(a), SDVOSB, HUBZone, WOSB, etc.)
- **Mentor Name and Location**: Large business partner information
- **Agreement Approval Date**: When the partnership was officially established
- **Agreement Expiration Date**: When the partnership will conclude
- **Primary NAICS Code**: Core industry focus of the partnership
- **Agreement Benefits**: Specific areas of development within the partnership

### Integration with Shipley Process

This data source provides critical intelligence for multiple Shipley Capture milestones:

- **Milestone 0**: Identify potential small business partners for set-aside opportunities
- **Milestone 1**: Analyze competitor teaming strategies to inform capture approach
- **Milestone 2**: Evaluate potential teaming partners based on past performance with mentors
- **Milestone 3**: Fine-tune proposal teaming strategy based on competitive partnership intelligence

## Data Dictionary

The following data dictionary provides detailed information about key data elements used in the Data Insights platform. This comprehensive reference is designed to help both new and experienced users understand the data elements, their sources, typical values, and their strategic significance for business development and capture management.

## Data Elements for Business Intelligence and Why These Elements Are the Most Impactful

These data elements are the most impactful because they collectively provide a holistic view of the federal contracting landscape:

- **Customer Insights**: Agency and office codes reveal who is spending and where, enabling targeted outreach.
- **Market Dynamics**: Financial, competition, and timeline data uncover spending trends and opportunity timing.
- **Competitor Positioning**: Contractor details expose rival strengths and weaknesses.
- **Operational Relevance**: NAICS, PSC, and performance data ensure alignment with logistics, operations, maintenance, and technology expertise.
- **Strategic Flexibility**: Elements like set-asides and subcontracting requirements offer alternative entry points (e.g., partnering with primes).

Their historical nature amplifies their value, allowing trend analysis over time—e.g., rising DoD investments in cybersecurity or shifts toward competitive procurements.

---

## Table: s2_interim.usaspending_prime_awards_dedup

Cleaned & deduplicated prime award actions. Each row represents a unique business-significant contract action after compound-key deduplication. Flags & semantic fields support downstream analytics and retrieval augmentation.

> Human Readable Reference: The following subsections mirror the style of the Contract Identification Elements list (Definition / Why It Matters / Modeling Notes). The earlier markdown table has been replaced for readability. If a compact machine-readable table is re-required, generate from these entries.

### Identification & Keys

#### contract_transaction_unique_key (TEXT, PK)

- Definition: System-unique identifier for a specific transaction/action.
- Why It Matters: Golden key for joins back to raw tables & prevents duplicate analytics.
- Modeling Notes: Treat as opaque stable ID; no token splitting.

#### contract_award_unique_key (TEXT)

- Definition: Identifier grouping all actions under the same underlying award/vehicle.
- Why It Matters: Enables roll‑up (value, lifecycle) and recompete timing.
- Modeling Notes: Use as grouping feature / clustering handle.

#### parent_award_id_piid (TEXT)

- Definition: PIID of parent (IDIQ/BPA) when this is a task/delivery order.
- Why It Matters: Reveals strategic vehicle context & on‑ramp pathways.
- Modeling Notes: Link to aggregated vehicle narratives.

#### award_id_piid (TEXT)

- Definition: Procurement Instrument Identifier for the contract/order.
- Why It Matters: Industry-familiar external reference for research & validation.
- Modeling Notes: Preserve exact casing; high lexical salience.

#### modification_number (TEXT; '0' = base)

- Definition: Sequence identifier of modification vs base award.
- Why It Matters: Tracks contract churn, scope evolution, and lifecycle stage.
- Modeling Notes: Use sequence patterns in time‑series / narrative generation.

### Temporal Fields

#### action_date (DATE)

- Definition: Official action signature date.
- Why It Matters: Baseline for recency, velocity, and timeline analytics.
- Modeling Notes: Derive recency & intervals to solicitation_date.

#### action_date_fiscal_year (TEXT YYYY)

- Definition: Fiscal year derived from action_date.
- Why It Matters: Aligns with federal budget cycles & Q4 surge analysis.
- Modeling Notes: Treat as categorical year token.

#### action_date_fiscal_quarter (INTEGER 1–4)

- Definition: Fiscal quarter for the action.
- Why It Matters: Reveals intra‑year buying cadence.
- Modeling Notes: Discrete token (Q1..Q4) for seasonality features.

#### period_of_performance_start_date / current_end_date / potential_end_date (DATE)

- Definition: Lifecycle start, current scheduled completion, maximum potential completion.
- Why It Matters: Drives recompete forecasting & long‑tail revenue estimation.
- Modeling Notes: Generate duration, days_to_end, option_depth (potential - current).

#### ordering_period_end_date (DATE)

- Definition: Final ordering date for IDIQ/vehicle.
- Why It Matters: Urgency indicator for final task order pursuits.
- Modeling Notes: Derive days_remaining_ordering_period.

### Financial Fields

#### federal_action_obligation (NUMERIC)

- Definition: Dollars obligated by this specific action.
- Why It Matters: Measures incremental funding momentum.
- Modeling Notes: Log transform; pair with cumulative metrics.

#### total_dollars_obligated (NUMERIC)

- Definition: Cumulative obligations to date.
- Why It Matters: Execution progress vs ceiling.
- Modeling Notes: Compute utilization_ratio = total / potential_total_value_of_award.

#### potential_total_value_of_award (NUMERIC)

- Definition: Ceiling if all options executed.
- Why It Matters: Maximum strategic value sizing.
- Modeling Notes: Use with obligations for growth headroom features.

#### total_outlayed_amount_for_overall_award (NUMERIC)

- Definition: Dollars actually disbursed.
- Why It Matters: Execution fidelity; gap vs obligations signals slippage.
- Modeling Notes: Derived outlay_vs_obligation ratio.

### Performance & Scope Narratives

#### prime_award_base_transaction_description (TEXT)

- Definition: Base award scope narrative.
- Why It Matters: Context anchor for all downstream actions.
- Modeling Notes: Core segment in semantic_description.

#### transaction_description (TEXT)

- Definition: Action‑specific narrative.
- Why It Matters: Captures scope changes or refinements.
- Modeling Notes: Concatenate with base description for embeddings.

### Classification Codes

#### naics_code / naics_description

- Definition: Industry classification code + text label.
- Why It Matters: Aligns opportunity with corporate competencies & small business thresholds.
- Modeling Notes: Use both code and description tokens.

#### product_or_service_code / product_or_service_code_description

- Definition: PSC/FSC functional category + label.
- Why It Matters: Finer granularity for capability targeting.
- Modeling Notes: Pair with NAICS for richer vectors.

#### dod_acquisition_program_description (TEXT)

- Definition: DoD program name if present.
- Why It Matters: Ties contract to modernization / portfolio initiatives.
- Modeling Notes: Entity feature for knowledge graph.

### Organizational / Customer Fields

#### parent_award_agency_name; awarding_sub_agency_name; awarding_office_name

- Definition: Hierarchy of awarding entities.
- Why It Matters: Drives customer segmentation & relationship mapping.
- Modeling Notes: Maintain normalized casing; build org hierarchy embeddings.

#### funding_agency_name / funding_sub_agency_name / funding_office_name

- Definition: Budget source hierarchy.
- Why It Matters: Identifies true budget holders distinct from contracting office.
- Modeling Notes: Cross features with awarding for split-funding patterns.

### Contractor Identity Fields

#### recipient_name / recipient_uei

- Definition: Prime contractor name & UEI.
- Why It Matters: Incumbent & competitor identification.
- Modeling Notes: UEI as stable join key; name for surface narrative.

#### recipient_parent_name / recipient_parent_uei

- Definition: Ultimate parent entity & UEI.
- Why It Matters: Corporate roll‑up / consolidation analytics.
- Modeling Notes: Aggregation key for portfolio views.

### Competition & Procurement

#### solicitation_date / solicitation_procedures

- Definition: RFx issuance date & method.
- Why It Matters: Lead time & acquisition strategy insight.
- Modeling Notes: Derive cycle_time = action_date - solicitation_date.

#### extent_competed / type_of_set_aside

- Definition: Competition extent & socioeconomic reservation.
- Why It Matters: Determines market openness and eligibility pathways.
- Modeling Notes: Critical categorical features for competitive intensity modeling.

#### fair_opportunity_limited_sources / other_than_full_and_open_competition

- Definition: Justifications limiting competition.
- Why It Matters: Indicates constrained landscape & renewal likelihood.
- Modeling Notes: Narrative explanatory tokens.

#### number_of_offers_received (INTEGER)

- Definition: Count of offers.
- Why It Matters: Direct historical competitiveness signal.
- Modeling Notes: Use for intensity scores & pWin modeling.

#### subcontracting_plan (TEXT)

- Definition: Subcontracting plan indicator/type.
- Why It Matters: Signals mandated small business participation.
- Modeling Notes: Binary/enum for teaming recommendations.

### Pricing / Contract Structure

#### type_of_contract_pricing (TEXT)

- Definition: Pricing arrangement (FFP/CPFF/T&M/etc.).
- Why It Matters: Risk & margin strategy implications.
- Modeling Notes: Normalize to controlled vocabulary.

#### action_type / award_type

- Definition: Transaction nature & instrument category.
- Why It Matters: Distinguishes base vs mods and vehicle form.
- Modeling Notes: Sequence features for lifecycle modeling.

#### type_of_idc / idv_type

- Definition: IDC & Indefinite Delivery Vehicle classifications.
- Why It Matters: Vehicle strategy & competition mechanics.
- Modeling Notes: Low frequency; retain categorical encoding.

#### undefinitized_action (TEXT)

- Definition: Indicator of undefinitized award status.
- Why It Matters: Higher schedule urgency & future adjustment risk.
- Modeling Notes: Uncertainty signal.

#### multi_year_contract (TEXT)

- Definition: Multi‑year contract flag.
- Why It Matters: Long-term revenue stability.
- Modeling Notes: Convert to boolean.

#### multiple_or_single_award_idv (TEXT)

- Definition: Single vs multiple award structure.
- Why It Matters: Task order competition frequency & strategy.
- Modeling Notes: Key driver for opportunity generation prompts.

### Traceability & External Reference

#### usaspending_permalink (TEXT)

- Definition: Canonical public URL.
- Why It Matters: Analyst validation & drill‑down.
- Modeling Notes: Provide as citation link; not for embedding.

### KBR Role Flags

#### kbr_prime / kbr_as_sub / kbr_sub_issued (BOOLEAN)

- Definition: Role classification flags based on UEI list & subaward linkages.
- Why It Matters: Distinguishes internal footprint (prime vs sub) and teaming issuance behavior.
- Modeling Notes: Model as tri-state patterns for role narrative.

### Semantic Fields

#### semantic_description (TEXT)

- Definition: Concatenated descriptive fields for embedding.
- Why It Matters: Powers semantic search & similarity retrieval.
- Modeling Notes: Do not manually edit post-generation.

#### semantic_vector (DOUBLE PRECISION[])

- Definition: Dense embedding of semantic_description.
- Why It Matters: Enables vector similarity (RAG, clustering, nearest neighbor search).
- Modeling Notes: Use cosine similarity; dimension model-dependent.

### Prime Table Usage Patterns

- Recompete Targeting: Use period_of_performance_current_end_date within 6–18 month window + high potential_total_value_of_award utilization gaps.
- Competitive Intensity: Combine number_of_offers_received, extent_competed, type_of_set_aside.
- Strategic Vehicle Mapping: parent_award_id_piid + idv_type + multiple_or_single_award_idv.
- Incumbent Posture: recipient_name + modification_number sequence analysis.

---

## Table: s2_interim.usaspending_subawards_enriched

Enriched subaward events with joined prime award attributes and role flags. Each row is a deduplicated subaward instance.

### Core Identification

#### subaward_unique_key (BIGINT, PK)

- Definition: Surrogate unique key for subaward row.
- Why It Matters: Stable reference & batching anchor.
- Modeling Notes: Primary retrieval / vector ID.

#### subaward_number (TEXT)

- Definition: Subaward identifier when provided.
- Why It Matters: Differentiates multiple subs under same prime action.
- Modeling Notes: Sparse—retain but handle null.

#### prime_award_unique_key / contract_award_unique_key (TEXT)

- Definition: Linkage to prime award/contract.
- Why It Matters: Connects subcontract scope to vehicle and recompete context.
- Modeling Notes: Join path to prime features & narratives.

### Timing & Financials

#### subaward_action_date (DATE)

- Definition: Execution date of subaward.
- Why It Matters: Sequencing of partner onboarding.
- Modeling Notes: Lag vs prime_action_date.

#### subaward_amount (NUMERIC)

- Definition: Dollar amount allocated to this subcontract event.
- Why It Matters: Magnitude of dependency / capability outsourcing.
- Modeling Notes: Log transform; compute share vs prime obligations.

### Subcontract Scope & Parties

#### subaward_description (TEXT)

- Definition: Narrative of subcontracted work.
- Why It Matters: Reveals delegated functions & capability gaps.
- Modeling Notes: Included in semantic_description.

#### subawardee_name / subawardee_uei

- Definition: Subcontractor identity & unique entity ID.
- Why It Matters: Partner mapping & teaming strategy insights.
- Modeling Notes: UEI for disambiguation; name for narratives.

#### subawardee_parent_name / subawardee_parent_uei

- Definition: Parent corporation identifiers.
- Why It Matters: Corporate ecosystem concentration & influence.
- Modeling Notes: Hierarchical aggregation features.

### Geography & Business Profile

#### subawardee_city_name / subawardee_state_code / subawardee_country_code / subawardee_country_name

- Definition: Location fields of subcontractor.
- Why It Matters: Regional supply chain footprint & compliance considerations.
- Modeling Notes: Normalize state/country codes; geocluster features.

#### subawardee_business_types (TEXT)

- Definition: Socioeconomic and classification codes (delimited).
- Why It Matters: Set‑aside teaming qualification & diversity analysis.
- Modeling Notes: Multi‑label tokenization.

#### subaward_primary_place_of_performance_city_name / \_state_code

- Definition: Location of performance for the subcontract.
- Why It Matters: Operational footprint granularity beyond HQ.
- Modeling Notes: Co‑location analysis vs prime performance locale.

#### subaward_type (TEXT)

- Definition: Instrument/category of subcontract.
- Why It Matters: Indicates services vs supply & risk posture.
- Modeling Notes: Sparse categorical—retain label.

### Lineage & ETL Meta

#### created_at / updated_at / fetch_date

- Definition: Record creation, last update, ingestion dates.
- Why It Matters: Data freshness & change tracking.
- Modeling Notes: Features for staleness scoring; usually excluded from embeddings.

### KBR Role Flags

#### kbr_prime / kbr_as_sub / kbr_sub_issued

- Definition: Role classification relative to KBR UEI list.
- Why It Matters: Identifies leadership, partnership, and issuance behaviors in teaming structure.
- Modeling Notes: Use combined state vectors for role classification tasks.

### Joined Prime Context (All prefixed prime\_\*)

#### prime_contract_transaction_unique_key

- Definition: Prime action transaction key.
- Why It Matters: High‑resolution join to specific prime action semantics.
- Modeling Notes: Use for fine‑grained temporal alignment.

#### prime_action_date / prime_action_date_fiscal_year / prime_action_date_fiscal_quarter

- Definition: Prime action timing fields.
- Why It Matters: Anchor for lag analyses & seasonality of subcontracting.
- Modeling Notes: Derive sub_lag_days.

#### prime_modification_number

- Definition: Prime mod identifier.
- Why It Matters: Associates subcontract with modification events.
- Modeling Notes: Sequence modeling feature.

#### prime_federal_action_obligation / prime_total_dollars_obligated / prime_potential_total_value_of_award / prime_total_outlayed_amount_for_overall_award

- Definition: Prime financial metrics.
- Why It Matters: Context for subcontract scale & maturity stage.
- Modeling Notes: Compute sub_share_ratio & maturity indicators.

#### prime_period_of_performance_start_date / \_current_end_date / \_potential_end_date / prime_ordering_period_end_date

- Definition: Prime lifecycle & ordering window.
- Why It Matters: Remaining runway for sub performance & expansion.
- Modeling Notes: Duration & forecasting features.

#### prime_primary_place_of_performance_city_name / \_state_code

- Definition: Prime performance geography.
- Why It Matters: Geo proximity synergy or dispersion vs subcontract performance.
- Modeling Notes: Generate co_location flags.

#### prime_prime_award_base_transaction_description / prime_transaction_description

- Definition: Base award narrative & action narrative (prime).
- Why It Matters: Semantic context for subaward purpose alignment.
- Modeling Notes: Combined into embedding pipeline.

#### prime_naics_code / prime_naics_description / prime_product_or_service_code / prime_product_or_service_code_description

- Definition: Prime classification codes & descriptions.
- Why It Matters: Capability domain & overlap/mismatch analysis with sub scope.
- Modeling Notes: Comparative features to subaward_description tokens.

#### prime_dod_acquisition_program_description

- Definition: DoD program context.
- Why It Matters: Strategic alignment & modernization initiatives.
- Modeling Notes: Knowledge graph entity.

#### prime_parent_award_agency_name / prime_awarding_sub_agency_name / prime_awarding_office_name

- Definition: Prime awarding hierarchy.
- Why It Matters: Customer ecosystem mapping.
- Modeling Notes: Organizational embedding features.

#### prime_funding_agency_name / prime_funding_sub_agency_name / prime_funding_office_name

- Definition: Prime funding hierarchy.
- Why It Matters: Budget origin & influence channels.
- Modeling Notes: Cross with awarding for split patterns.

#### prime_recipient_name / prime_recipient_uei / prime_recipient_parent_name / prime_recipient_parent_uei

- Definition: Prime contractor identity & corporate parent.
- Why It Matters: Incumbent leverage & consolidation.
- Modeling Notes: Entity linking to prime awards table.

#### prime_solicitation_date / prime_solicitation_procedures / prime_extent_competed / prime_type_of_set_aside

- Definition: Prime procurement timing & competition attributes.
- Why It Matters: Predicts subcontract diversity & stability.
- Modeling Notes: Competitive intensity features.

#### prime_fair_opportunity_limited_sources / prime_other_than_full_and_open_competition

- Definition: Competition limitation justifications.
- Why It Matters: Indicates constrained subcontract landscape.
- Modeling Notes: Narrative explanation tokens.

#### prime_number_of_offers_received / prime_subcontracting_plan

- Definition: Prime competition count & subcontracting plan indicator.
- Why It Matters: Competitive pressure & mandated teaming commitments.
- Modeling Notes: Intensity & teaming propensity metrics.

#### prime_government_furnished_property

- Definition: GFP involvement at prime level.
- Why It Matters: Logistics complexity cascading to subs.
- Modeling Notes: Risk indicator.

#### prime_type_of_contract_pricing / prime_action_type / prime_award_type / prime_type_of_idc / prime_idv_type

- Definition: Prime pricing and vehicle structure fields.
- Why It Matters: Governs risk allocation & tasking mechanisms.
- Modeling Notes: Categorical encoding; some low frequency.

#### prime_undefinitized_action / prime_multi_year_contract / prime_multiple_or_single_award_idv

- Definition: Status & structural flags.
- Why It Matters: Scope fluidity, duration stability, competition structure.
- Modeling Notes: Boolean/enum normalization.

#### prime_usaspending_permalink

- Definition: Public reference URL for prime award.
- Why It Matters: Traceability & analyst drill‑down.
- Modeling Notes: Exclude from embeddings; surface for citations.

### Semantic Fields (Subawards)

#### semantic_description (TEXT)

- Definition: Concatenated sub + relevant prime descriptors.
- Why It Matters: Drives semantic retrieval & similarity search.
- Modeling Notes: Do not hand edit post generation.

#### semantic_vector (DOUBLE PRECISION[])

- Definition: Embedding of semantic_description.
- Why It Matters: Vector search for partner/requirement matching.
- Modeling Notes: Cosine similarity; dimension defined by embedding model.

### Subawards Usage Patterns

- Partner Identification: Rank subawardee_name frequency & diversity under target agencies.
- Incumbent Team Analysis: Compare prime_recipient_name vs repeated subawardee_name across vehicles.
- Capability Gap Mapping: Contrast prime_prime_award_base_transaction_description with subaward_description to infer outsourced functions.
- Recompete Strategy: Use nearing prime_period_of_performance_current_end_date + active subaward network breadth as incumbent defensibility indicator.

---

### LLM Fine-Tuning Guidance (Prime & Subaward Tables)

When creating training examples:

- Provide both raw categorical values (e.g., NAICS 541330) and human-readable description in the same context window for grounding.
- Construct contrastive pairs: (High competition: number_of_offers_received=15) vs (Low competition: number_of_offers_received=1) with explanation.
- Include temporal deltas (days_to_end, utilization_ratio) as derived narrative features rather than introducing new base columns.
- Emphasize role triplet states for KBR: (kbr_prime, kbr_as_sub, kbr_sub_issued) to teach role classification.
- Use semantic_description only as source text; avoid duplicating prime/sub fields verbatim unless clarifying.

---

### Expanded Narrative Element Reference

The following sections provide extended prose descriptions of individual data elements. They may repeat concise schema table definitions for readability and training material preparation.

#### Contract Identification Elements

- **Award ID (award_id_piid)**:

  - **Description**: Unique contract identifier assigned by the awarding agency.
  - **Impact**: Enables precise tracking of specific contracts across systems.
  - **Utility**: Serves as primary reference for connecting related contract documents and activities.

- **Parent Award ID (parent_award_id_piid)**:

  - **Description**: ID of the parent contract for task/delivery orders.
  - **Impact**: Reveals relationships between master contracts and task orders.
  - **Utility**: Identifies master contracts (IDIQs, BPAs) to understand broader procurement vehicles.

- **NAICS Code (naics_code)**:

  - **Description**: North American Industry Classification System code categorizing the industry.
  - **Impact**: Classifies contracts by industrial sector and business activity.
  - **Utility**: Filters opportunities by relevant industries aligned with core capabilities.

- **NAICS Description (naics_description)**:

  - **Description**: Text description of the NAICS code.
  - **Impact**: Provides clear understanding of the industrial categorization.
  - **Utility**: Helps understand the nature of work without having to look up NAICS codes.

- **PSC Code (product_or_service_code)**:

  - **Description**: Product or Service Code categorizing the contract.
  - **Impact**: Classifies contracts by specific products or services.
  - **Utility**: Narrows focus to specific types of services or products of interest.

- **PSC Description (product_or_service_code_description)**:

  - **Description**: Text description of the PSC code.
  - **Impact**: Clarifies the exact nature of contracted products/services.
  - **Utility**: Enables understanding of specific products/services without having to look up PSC codes.

- **Contract Description (transaction_description)**:

  - **Description**: Narrative description of the contracted work.
  - **Impact**: Provides insight into the specific work being performed.
  - **Utility**: Allows evaluation of relevance and scope of contracts for capture targeting.

- **Prime Award Description (prime_award_base_transaction_description)**:
  - **Description**: Description of the base award for task orders.
  - **Impact**: Contextualizes individual task orders within their parent vehicle.
  - **Utility**: Helps understand the broader scope of the parent vehicle.

#### Financial Information Elements

- **Obligation Amount (federal_action_obligation)**:

  - **Description**: Funds obligated by the specific action.
  - **Impact**: Shows immediate funding commitments for specific actions.
  - **Utility**: Helps assess the value of individual contract actions.

- **Total Obligated Amount (total_dollars_obligated)**:

  - **Description**: Cumulative funds obligated to date.
  - **Impact**: Reveals actual spending against potential contract value.
  - **Utility**: Allows evaluation of total spending on contracts to date.

- **Potential Value (potential_total_value_of_award)**:

  - **Description**: Maximum potential value including all options.
  - **Impact**: Indicates the full financial scope of an opportunity.
  - **Utility**: Helps understand total opportunity size including all option periods.

- **Total Disbursed (total_outlayed_amount_for_overall_award)**:
  - **Description**: Actual funds paid to contractor.
  - **Impact**: Shows execution rate of contracts.
  - **Utility**: Enables comparison of spending rate to obligations to identify slow-moving contracts.

#### Timeline Information Elements

- **Award Date (action_date)**:

  - **Description**: Date the contract action was signed.
  - **Impact**: Establishes the official start of contract obligations.
  - **Utility**: Helps track award timing patterns by agency.

- **Start Date (period_of_performance_start_date)**:

  - **Description**: Date work begins.
  - **Impact**: Marks the beginning of performance obligations.
  - **Utility**: Aids in planning resource allocation and tracking contract timelines.

- **End Date (period_of_performance_current_end_date)**:

  - **Description**: Current scheduled completion date.
  - **Impact**: Defines the current contractual end date.
  - **Utility**: Helps identify recompete opportunities and track contract durations.

- **Potential End Date (period_of_performance_potential_end_date)**:

  - **Description**: Final end date if all options exercised.
  - **Impact**: Shows the maximum possible contract duration.
  - **Utility**: Enables understanding of full potential duration of contracts.

- **Ordering End Date (ordering_period_end_date)**:

  - **Description**: Last date orders can be placed on IDIQs.
  - **Impact**: Defines the window of opportunity for task orders.
  - **Utility**: Helps track remaining ordering period on ID/IQ contracts.

- **Fiscal Year (action_date_fiscal_year)**:
  - **Description**: Federal fiscal year of the action.
  - **Impact**: Connects contract actions to budget cycles.
  - **Utility**: Allows alignment of analysis with government budget cycles.

#### Contracting Agency Elements

- **Awarding Agency (parent_award_agency_name)**:

  - **Description**: Top-level agency awarding the contract.
  - **Impact**: Identifies the primary customer organization.
  - **Utility**: Helps target business development efforts by agency.

- **Awarding Sub-Agency (awarding_sub_agency_name)**:

  - **Description**: Component of the awarding agency.
  - **Impact**: Provides greater specificity about the customer organization.
  - **Utility**: Enables focus of BD efforts on specific components with best fit.

- **Contracting Office (awarding_office_name)**:

  - **Description**: Office that executed the contract.
  - **Impact**: Pinpoints the specific buying office.
  - **Utility**: Facilitates building relationships with specific contracting offices.

- **Funding Agency (funding_agency_name)**:

  - **Description**: Agency providing the funds.
  - **Impact**: Reveals the source of budget authority.
  - **Utility**: Helps identify actual budget holders which may differ from awarding agency.

- **Funding Sub-Agency (funding_sub_agency_name)**:

  - **Description**: Component providing the funds.
  - **Impact**: Identifies specific budget-holding components.
  - **Utility**: Allows tracking of which components are spending on relevant services.

- **Funding Office (funding_office_name)**:
  - **Description**: Office controlling the budget.
  - **Impact**: Pinpoints program offices with spending authority.
  - **Utility**: Helps target relationship-building with program offices controlling budgets.

#### Contractor Information Elements

- **Awardee (recipient_name)**:

  - **Description**: Name of the contract recipient.
  - **Impact**: Identifies the primary contractor.
  - **Utility**: Helps identify competitors and potential partners.

- **Awardee UEI (recipient_uei)**:

  - **Description**: Unique Entity Identifier of awardee.
  - **Impact**: Provides consistent identification across contracts.
  - **Utility**: Enables tracking of contractor activity across contracts with consistent identifier.

- **Awardee Parent Name (recipient_parent_name)**:

  - **Description**: Ultimate parent company of awardee.
  - **Impact**: Reveals corporate ownership structures.
  - **Utility**: Helps understand corporate relationships and market consolidation.

- **Awardee Parent UEI (recipient_parent_uei)**:
  - **Description**: UEI of ultimate parent company.
  - **Impact**: Links subsidiaries to parent organizations.
  - **Utility**: Enables tracking of all subsidiaries of major competitors.

#### Competition and Procurement Elements

- **Solicitation Date (solicitation_date)**:

  - **Description**: Date RFP was issued.
  - **Impact**: Marks the start of the competitive process.
  - **Utility**: Helps analyze procurement timelines by agency.

- **Solicitation Procedures (solicitation_procedures)**:

  - **Description**: Method used to solicit offers.
  - **Impact**: Reveals contracting office's approach to competition.
  - **Utility**: Enables understanding of agency procurement preferences.

- **Extent Competed (extent_competed)**:

  - **Description**: Level of competition.
  - **Impact**: Indicates the competitive landscape.
  - **Utility**: Helps identify competitive landscape and sole-source opportunities.

- **Set-Aside Type (type_of_set_aside)**:

  - **Description**: Socioeconomic reservation.
  - **Impact**: Shows small business priorities.
  - **Utility**: Enables identification of set-aside opportunities and potential partners.

- **Fair Opportunity Limited Sources (fair_opportunity_limited_sources)**:

  - **Description**: Reason for limiting competition on IDIQs.
  - **Impact**: Explains exceptions to full competition.
  - **Utility**: Helps understand patterns in limited competition.

- **Other Than Full and Open Competition (other_than_full_and_open_competition)**:

  - **Description**: Reason for not competing fully.
  - **Impact**: Justifies sole-source or limited competition.
  - **Utility**: Enables identification of non-competitive award patterns.

- **Offers Received (number_of_offers_received)**:

  - **Description**: Number of bids received.
  - **Impact**: Quantifies competitive interest.
  - **Utility**: Helps gauge competitive interest and identify less contested opportunities.

- **Subcontracting Plan (subcontracting_plan)**:
  - **Description**: Type of subcontracting plan.
  - **Impact**: Indicates small business participation requirements.
  - **Utility**: Helps identify teaming opportunities and small business requirements.

#### Contract Terms and Types Elements

- **Contract Type (type_of_contract_pricing)**:

  - **Description**: Pricing structure of the contract.
  - **Impact**: Defines financial risk allocation.
  - **Utility**: Enables understanding of pricing preferences by agency and program.

- **Action Type (action_type)**:

  - **Description**: Nature of the transaction.
  - **Impact**: Distinguishes new awards from modifications.
  - **Utility**: Helps distinguish between new awards and modifications.

- **Award Type (award_type)**:

  - **Description**: Contract vehicle type.
  - **Impact**: Indicates preferred procurement methods.
  - **Utility**: Enables understanding of agency preferences for contract vehicles.

- **IDC Type (type_of_idc)**:

  - **Description**: Type of indefinite delivery contract.
  - **Impact**: Defines the structure of indefinite delivery contracts.
  - **Utility**: Helps identify patterns in IDIQ structures by agency.

- **IDV Type (idv_type)**:

  - **Description**: Type of indefinite delivery vehicle.
  - **Impact**: Categorizes contract vehicles.
  - **Utility**: Enables understanding of which contract vehicles agencies prefer.

- **Undefinitized Action (undefinitized_action)**:

  - **Description**: Whether action is undefinitized.
  - **Impact**: Indicates contracts with terms still being negotiated.
  - **Utility**: Helps identify UCAs which may indicate urgent requirements.

- **Multiple or Single Award (multiple_or_single_award_idv)**:

  - **Description**: Whether IDIQ is single or multiple award.
  - **Impact**: Defines competitive landscape for task orders.
  - **Utility**: Enables assessment of competitive landscape of IDIQ vehicles.

- **Multi-Year Contract (multi_year_contract)**:
  - **Description**: Whether contract spans multiple years.
  - **Impact**: Indicates long-term commitments.
  - **Utility**: Helps identify stable, long-term funding commitments.

#### Performance Information Elements

- **Place of Performance City (primary_place_of_performance_city_name)**:

  - **Description**: City where work is performed.
  - **Impact**: Locates contract activities geographically.
  - **Utility**: Helps identify geographic patterns and facility requirements.

- **Place of Performance State (primary_place_of_performance_state_code)**:

  - **Description**: State where work is performed.
  - **Impact**: Identifies regions with contract activity.
  - **Utility**: Enables focus of BD efforts in high-activity regions.

- **Government Furnished Property (government_furnished_property)**:

  - **Description**: Whether GFP/GFE is provided.
  - **Impact**: Indicates government resource contributions.
  - **Utility**: Helps understand resource requirements and constraints.

- **DoD Program Description (dod_acquisition_program_description)**:

  - **Description**: Associated DoD program.
  - **Impact**: Links contracts to major initiatives.
  - **Utility**: Enables linking of contracts to major programs for strategic targeting.

- **Program Acronym (program_acronym)**:
  - **Description**: Acronym of the program.
  - **Impact**: Provides shorthand reference for programs.
  - **Utility**: Helps quickly identify associated programs.

#### Reference Information Elements

- **Modification No (modification_number)**:

  - **Description**: Modification identifier.
  - **Impact**: Uniquely identifies contract changes.
  - **Utility**: Enables tracking of contract changes and history.

- **USAspending Permalink (usaspending_permalink)**:
  - **Description**: Direct link to award on USAspending.gov.
  - **Impact**: Provides access to official source data.
  - **Utility**: Enables access to full contract details for deeper research.

#### Subaward Elements (Planned Addition)

- **Subaward ID**:

  - **Description**: Unique identifier for the subaward.
  - **Impact**: Enables tracking of subcontracts.
  - **Utility**: Helps track specific subcontracts across contracts.

- **Subaward Amount**:

  - **Description**: Dollar value of the subaward.
  - **Impact**: Quantifies work allocation to subcontractors.
  - **Utility**: Enables assessment of size and scope of subcontracted work.

- **Subawardee Name**:

  - **Description**: Name of the subcontractor.
  - **Impact**: Identifies companies in supporting roles.
  - **Utility**: Helps identify potential teaming partners or competitors at sub level.

- **Subawardee UEI**:

  - **Description**: Unique Entity Identifier of subcontractor.
  - **Impact**: Provides consistent identification of subcontractors.
  - **Utility**: Enables tracking of subcontractor participation across multiple primes.

- **Subaward Description**:

  - **Description**: Description of subcontracted work.
  - **Impact**: Explains division of labor on contracts.
  - **Utility**: Helps understand work division between prime and subs.

- **Subaward Date**:

  - **Description**: Date subaward was issued.
  - **Impact**: Establishes timeline of team formation.
  - **Utility**: Enables tracking of timing of subcontract awards relative to prime award.

- **Principal Place of Performance**:

  - **Description**: Location where subcontracted work is performed.
  - **Impact**: Maps geographical distribution of contract work.
  - **Utility**: Helps map geographic distribution of work across team.

- **Subcontractor Size**:

  - **Description**: Business size of subcontractor.
  - **Impact**: Indicates small business utilization.
  - **Utility**: Enables analysis of small business utilization patterns.

- **Subcontractor Type**:
  - **Description**: Socioeconomic category of subcontractor.
  - **Impact**: Shows diversity in teaming arrangements.
  - **Utility**: Helps identify diversity in teaming arrangements.

## Shipley Capture Milestone Mapping

### Purpose

To integrate Shipley capture process methodology (milestones 0, 1, 2, 3) into the Data Insights platform, automating the collection and analysis of key data points required at each milestone to accelerate the decision-making process and improve win rates.

### Capture Milestone Framework

The Shipley process defines four key milestone decision points in the capture process:

- **Milestone 0 - Opportunity Identification**:

  - **Description**: Initial identification and qualification of potential opportunities.
  - **Decision Point**: Determine whether to invest resources in pursuing the opportunity.
  - **Data Automation Potential**: 70-80% of required information can be automated.

- **Milestone 1 - Opportunity Assessment/Validation**:

  - **Description**: Detailed opportunity analysis and initial capture strategy development.
  - **Decision Point**: Commit resources to pursue the opportunity.
  - **Data Automation Potential**: 50-60% of required information can be automated.

- **Milestone 2 - Bid/No-Bid Decision**:

  - **Description**: Comprehensive competitive assessment and capture plan execution.
  - **Decision Point**: Final decision to bid and allocate proposal resources.
  - **Data Automation Potential**: 30-40% of required information can be automated.

- **Milestone 3 - Proposal Strategy Validation**:
  - **Description**: Review of proposal strategy against capture intelligence.
  - **Decision Point**: Confirm alignment of proposal with capture strategy.
  - **Data Automation Potential**: 20-30% of required information can be automated.

### Key Data Points by Milestone

#### Milestone 0 (Opportunity Identification) Data Points

- **Automated Data Elements**:

  - Contract value range (estimated from historical data)
  - Agency and sub-agency identification
  - NAICS/PSC classification
  - Set-aside status
  - Incumbent identification (when available)
  - Anticipated competition level
  - Estimated release timeline
  - Historical spending patterns
  - Geographic requirements

- **Manual Assessment Elements**:
  - Strategic alignment with company goals
  - Initial resource availability assessment
  - Preliminary customer relationship status

#### Milestone 1 (Opportunity Assessment) Data Points

- **Automated Data Elements**:

  - Historical award values for similar contracts
  - Customer budget analysis
  - Incumbent performance metrics
  - Agency spending trends
  - Contract vehicle analysis
  - Competitive landscape assessment
  - Teaming partner suggestions based on historical partnerships
  - Price-to-win range analysis
  - Historical evaluation criteria analysis

- **Manual Assessment Elements**:
  - Solution approach feasibility
  - Customer relationship strength
  - Initial differentiation strategy
  - Risk assessment

#### Milestone 2 (Bid/No-Bid Decision) Data Points

- **Automated Data Elements**:

  - Detailed competitor analysis
  - Price-to-win refined model
  - Historical win patterns at target agency
  - Customer preference analysis (contract types, evaluation criteria)
  - Small business utilization patterns
  - Technical requirement categorization
  - Similar opportunity outcome analysis

- **Manual Assessment Elements**:
  - Solution differentiation finalization
  - Win strategy development
  - Competitive positioning
  - Teaming agreements status
  - Price-to-win strategy

#### Milestone 3 (Proposal Strategy Validation) Data Points

- **Automated Data Elements**:

  - Final price-to-win analysis
  - Latest competitive intelligence
  - Agency recent award patterns
  - Final compliance checklist
  - Evaluation criteria weighting analysis

- **Manual Assessment Elements**:
  - Solution approach final review
  - Theme and discriminator alignment
  - Proposal resource allocation
  - Senior management review inputs

### Advanced Pricing Analysis Integration

#### Purpose

To provide data-driven pricing intelligence that moves beyond simple historical price analysis to predictive modeling that supports strategic pricing decisions at each capture milestone.

#### Key Components

- **Historical Price Range Analysis**:

  - **Description**: Automated analysis of historical contract values for similar work (by NAICS, PSC, agency, and size).
  - **Implementation**: Statistical analysis of contract award values in target segments.
  - **Milestone Utility**: Provides baseline price ranges for Milestone 0 and 1 decisions.

- **Pricing Strategy Percentile Analysis**:

  - **Description**: Places potential contract pricing strategies on a percentile scale based on historical awards.
  - **Implementation**: Distribution analysis of contract values with percentile mapping.
  - **Milestone Utility**: Supports Milestone 1 and 2 pricing strategy development.

- **Agency-Specific Pricing Patterns**:

  - **Description**: Analyzes pricing trends specific to target agencies and contracting offices.
  - **Implementation**: Comparative analysis of award values across agencies for similar work.
  - **Milestone Utility**: Refines pricing strategy for Milestone 2 decisions.

- **Competitor Pricing Analysis**:

  - **Description**: Examines pricing patterns of specific competitors in target market segments.
  - **Implementation**: Competitor-focused historical price analysis.
  - **Milestone Utility**: Enhances competitive positioning for Milestone 2 and 3.

- **BLS OEWS Wage Data Integration**:

  - **Description**: Incorporates Bureau of Labor Statistics Occupational Employment and Wage Statistics for labor rate analysis.
  - **Implementation**: API-based retrieval of national, state, and metropolitan area wage data for 800+ occupations.
  - **Data Features**: Provides comprehensive percentile wage data (10th, 25th, median, 75th, 90th) by location and industry.
  - **Cross-Industry Analysis**: Enables comparison of wage rates across industries for the same occupation.
  - **Geographic Variance**: Shows wage differences based on location for distributed contract work.
  - **Milestone Utility**: Supports labor rate justification and pricing strategy development at Milestones 1, 2, and 3.

- **Labor Category Benchmarking**:

  - **Description**: Combines Data.gov Contract-Awarded Labor Category API data with BLS OEWS statistics.
  - **Implementation**: Cross-reference analysis between government contract rates and standard industry wages.
  - **Rate Justification**: Provides statistically valid support for proposed rates based on percentile positioning.
  - **Competitive Edge**: Enables strategic rate positioning based on experience levels relative to market standards.
  - **Milestone Utility**: Critical for price proposal development at Milestone 3.

- **Price-to-Win Predictive Model**:

  - **Description**: Combines multiple data factors to predict optimal pricing range.
  - **Implementation**: Machine learning model incorporating historical wins, competition levels, and agency preferences.
  - **Milestone Utility**: Provides sophisticated pricing guidance for Milestone 2 and 3.

- **Cost Structure Analysis**:

  - **Description**: Estimates likely cost structures based on contract requirements.
  - **Implementation**: Pattern recognition of cost elements across similar contracts.
  - **Milestone Utility**: Supports pricing strategy development at Milestone 2.

- **Best Value vs. LPTA Prediction**:
  - **Description**: Predicts agency's likely source selection approach based on historical patterns.
  - **Implementation**: Classification algorithm for source selection method prediction.
  - **Milestone Utility**: Guides pricing strategy for Milestone 1 and 2.

### Implementation Approach

The Shipley Capture Milestone Mapping will be implemented as a structured workflow within the Data Insights platform:

1. **Milestone Framework Definition**:

   - Configure system to recognize and track opportunities by Shipley milestone stage
   - Define data requirements for each milestone

2. **Data Integration and Automation**:

   - Map existing data elements to milestone decision requirements
   - Develop new data collection capabilities for milestone-specific needs
   - Create automated data acquisition pathways for each milestone

3. **Decision Support Dashboards**:

   - Design milestone-specific dashboards with relevant KPIs
   - Create visualization tools for critical decision factors
   - Develop comparison views for competitive assessment

4. **Pricing Intelligence Engine**:

   - Implement statistical models for pricing analysis
   - Develop machine learning algorithms for predictive pricing
   - Create visualization tools for pricing strategy development

5. **Milestone Progression Tracking**:
   - Develop capability to track opportunities through milestone progression
   - Create notification system for milestone review triggers
   - Implement milestone decision documentation tools

### Expected Impact on Win Rates

By implementing the Shipley Capture Milestone Mapping with advanced pricing intelligence:

- **Opportunity Qualification**: 20% reduction in pursuit of non-winnable opportunities
- **Decision Velocity**: 30% reduction in time required for milestone decisions
- **Pricing Optimization**: 15% improvement in pricing strategy effectiveness
- **Resource Allocation**: 25% more efficient allocation of capture and proposal resources
- **Win Rate Improvement**: 10-15% overall improvement in contract win rates

The system will enable a more data-driven, consistent approach to capture management while reducing the manual effort required to compile decision-making information at each milestone.

## Strategic Default Dashboard Specification

### Purpose

To provide users with immediate, actionable business intelligence upon application launch, presenting a comprehensive view of historical contract data and projected spending over the next 24-36 months without requiring manual query execution.

### Key Components

#### 1. Dashboard Layout and Organization

- **Multi-Tab Interface**:

  - Strategic Overview tab (loads by default)
  - Detailed Analysis tab (accessible after overview)
  - Expiring Contracts tab (focused on recompete opportunities)
  - Interactive Exploration tab (for custom visualization creation)

- **Dynamic Layout**:
  - Responsive design that adapts to screen size
  - Expandable/collapsible sections for each visualization group
  - Information hierarchy with most critical insights displayed prominently

#### 2. Historical Spending Analysis

- **Agency Hierarchy Visualizations**:

  - **Top Agencies by Award Actions and Obligations**:

    - Bar charts showing top 10-15 awarding agencies by both award count and total obligation amount
    - Year-over-year comparison option
    - Tooltips providing additional context (% change, average award size)

  - **Sub-Agency Breakdown**:

    - Hierarchical treemap displaying sub-agency spending within parent agencies
    - Color intensity indicating spending concentration
    - Click-through capability to drill down to individual sub-agencies

  - **Funding Office Analysis**:
    - Bar charts of top funding offices by award count and obligation amount
    - Office growth/decline indicators showing trend direction
    - Filtering capability by parent agency and sub-agency

- **NAICS and PSC Code Analysis**:

  - **Top NAICS Codes**:

    - Bar charts of top 20 NAICS codes by award actions and obligations
    - NAICS description inclusion for immediate understanding
    - Sparkline trend indicators showing spending trajectory

  - **NAICS Code Clustering**:

    - Group visualization of related NAICS codes to identify broader industry trends
    - Year-over-year growth indicators for industry segments
    - Filtering by first 2-3 digits for broader category analysis

  - **PSC Code Spending**:
    - Bar/pie charts showing product vs. service distribution
    - Top PSC categories by obligation
    - PSC trend analysis over selected timeframe

#### 3. Contract Vehicle Analysis

- **Vehicle Type Distribution**:

  - **Award Type Breakdown**:

    - Pie chart showing distribution of contract types (Definitive Contracts, Purchase Orders, IDVs, etc.)
    - Trend charts showing shifts in vehicle usage over time
    - Agency preference analysis for vehicle types

  - **IDV Analysis**:

    - Pie charts for single vs. multiple award IDVs
    - Bar charts of top IDVs by total obligations
    - Remaining ceiling visualization for active IDVs

  - **Contract Type Analysis**:
    - Distribution of pricing types (Firm-Fixed Price, Cost-Plus, T&M, etc.)
    - Agency preferences for contract types
    - Correlation between contract type and award size

#### 4. Competitive Landscape Analysis

- **Contractor Market Share**:

  - **Top Contractors**:

    - Bar charts of top 20 contractors by award actions and obligations
    - Market share pie chart with focus on top 10 contractors
    - Year-over-year change indicators

  - **Small Business Participation**:

    - Small vs. large business award distribution
    - Set-aside category breakdown (8(a), SDVOSB, HUBZone, etc.)
    - Small business participation trends over time

  - **Competitive Landscape by NAICS**:
    - Heatmap of contractor activity across top NAICS codes
    - Market concentration analysis by NAICS
    - Identification of dominant players in each NAICS segment

#### 5. Geographic Distribution Analysis

- **Performance Location Heatmap**:

  - **National Map**:

    - Heatmap of award actions and obligations by state
    - Color intensity reflecting concentration of contract activity
    - Tooltips showing state-specific metrics (total awards, obligations, top contractors)

  - **Regional Breakdown**:
    - Bar charts of top metropolitan areas by contract activity
    - Regional concentration analysis
    - Military installation overlay for defense contracts

#### 6. Future Opportunity Analysis

- **Expiring Contract Timeline**:

  - **6-24 Month Expiration View**:

    - Timeline visualization of contracts expiring in next 6-24 months
    - Size indicators reflecting contract value
    - Color coding by agency/NAICS
    - Filtering by minimum value threshold

  - **Recompete Opportunity Table**:

    - Sortable table of expiring high-value contracts
    - Incumbent information and performance history
    - Estimated recompete dates and projected values

  - **Incumbent Performance**:
    - Performance metrics for expiring contracts where available
    - Modification frequency analysis as performance indicator
    - Contract growth analysis (original vs. current value)

- **Projected Spending Forecast**:
  - **24-36 Month Projection**:
    - Line graph showing projected spending based on historical patterns
    - Agency-specific forecasts
    - NAICS-specific spending projections
    - Confidence intervals for projections

#### 7. SAM.gov Opportunity Insights

- **Current Opportunity Analysis**:

  - **Open Solicitations Overview**:

    - Real-time tracking of open solicitations, RFIs, and Sources Sought notices from SAM.gov
    - Agency-based distribution visualization using vibrant blue heatmaps
    - Timeline view of upcoming deadlines with urgency indicators

  - **Opportunity Trend Analysis**:

    - Bar charts showing procurement trends by agency and NAICS code
    - Growth indicators for emerging procurement categories
    - Seasonal patterns visualization with electric blue highlight for peak periods

  - **Capability Alignment Assessment**:

    - AI-powered matching of opportunity requirements with historical contract performance
    - Capability gap analysis showing strengths and improvement areas
    - Heat-scored visualization of capability alignment with color intensity indicating match level

  - **Competitive Positioning**:
    - Market analysis for targeted opportunities based on historical contract data
    - Identification of potential competitors for specific opportunities
    - Visualization of competitive landscape with blue-toned positioning map

- **Opportunity Pipeline**:

  - **Procurement Forecast Integration**:

    - Long-range view of anticipated solicitations from agency procurement forecasts
    - Timeline visualization with confidence scoring for likelihood and timing
    - Estimated value projections based on historical similar procurements

  - **Opportunity Qualification Dashboard**:
    - Automated scoring of opportunities against company capabilities
    - Probability of win assessment based on historical performance in similar contracts
    - Strategic fit indicators with vibrant blue highlighting for ideal matches

#### 8. Enhanced Visualizations

- **Heatmaps**:

  - Contract award density by month/year
  - Agency/NAICS code correlations
  - Competitive density across contract vehicles

- **Interactive Bubble Charts**:

  - Contract distribution by size, competition level, and agency
  - Multi-dimensional analysis of market segments
  - Dynamic filtering capabilities

- **Animated Time Series**:

  - Spending pattern evolution over multiple years
  - Market share shifts among top contractors
  - Agency priority changes visualized over time

- **Network Graphs**:
  - Prime-subcontractor relationship mapping
  - Agency-contractor network visualization
  - Contract vehicle relationship mapping

#### 9. Filter Integration and Dynamic Updates

- **Sidebar Filter Application**:

  - All dashboard visualizations should update dynamically based on sidebar filters
  - Filter state should persist across dashboard tabs
  - Quick filter presets for common scenarios (e.g., DoD Only, Civilian Only, IT Contracts)

- **Cross-Filtering**:
  - Enable filtering by clicking elements within visualizations
  - Synchronized filtering across all dashboard components
  - Clear indication of active filters with one-click reset option

#### 10. Advanced Analytics Integration

- **Trend Indicators**:

  - Growth/decline arrows on key metrics
  - Statistical significance indicators for trends
  - Anomaly highlighting for unusual patterns

- **Benchmark Comparisons**:

  - Agency spending vs. government-wide averages
  - Contract size comparisons to industry benchmarks
  - Competition level comparisons across segments

- **Predictive Insights**:
  - Opportunity forecast confidence levels
  - Market saturation analysis
  - Competitive intensity predictions

### Implementation Priorities

1. **Core Visualizations**: Agency hierarchy, NAICS analysis, expiring contracts
2. **Interactive Filtering**: Dynamic dashboard updates based on filter selection
3. **Timeline View**: Expiring contracts visualization
4. **Enhanced Visualizations**: Heatmaps, geographic distribution
5. **Advanced Analytics**: Projected spending, competitive landscape analysis
6. **Performance Optimization**: Precomputed aggregations, caching strategies

### User Experience Considerations

- **Initial Load Time**: Dashboard should load within 5 seconds on standard hardware
- **Interaction Response**: Filter changes should propagate in under 2 seconds
- **Visual Clarity**: Clean presentation with clear labels and minimal clutter
- **Information Hierarchy**: Most important insights prominently displayed
- **Guided Discovery**: Progressive disclosure of details through drill-downs
- **Export Capabilities**: All visualizations should be exportable as images/PDF
- **Mobile Responsiveness**: Dashboard should adapt to tablet/mobile displays

### Technical Implementation

- **Data Preparation**:

  - Pre-aggregated tables for common dashboard queries
  - Materialized views for complex calculations
  - Scheduled recalculation of projection models

- **Visualization Framework**:

  - Plotly for interactive charts
  - Streamlit components for layout management
  - Custom CSS for professional styling and branding

- **Performance Optimization**:
  - Client-side caching for static elements
  - Lazy loading for secondary visualizations
  - Asynchronous data loading for non-critical components

### Expected Impact

The Strategic Default Dashboard will dramatically enhance user experience by providing immediate value upon application launch. Users will gain strategic insights within seconds, rather than having to construct queries manually. The dashboard will serve as a "mission control" interface for business development and capture management activities, highlighting the most promising opportunities and market trends without requiring extensive data manipulation.

This feature directly supports the core business goals of identifying high-value opportunities, understanding customer preferences, analyzing competitors, optimizing geographic focus, and leveraging technology trends - all in an immediately accessible format that encourages regular use and data-driven decision making.

## Offers Received Data Integration

### Purpose

To enhance competitive intelligence, probability of win (pWin) calculations, and overall capture strategy by leveraging the "number_of_offers_received" data element from USAspending.gov, providing critical insights into competitive density across federal contracts.

### Implementation Approach

- **Data Source**: The "number_of_offers_received" field from USAspending.gov records
- **Data Integration**: Incorporated into competitive analysis workflows and pWin models
- **Database Usage**: Leveraged in queries for filtering opportunities by competition level

### Key Benefits

- **Competition Intensity Mapping**: Identify markets and agencies with varying levels of competitive density
- **pWin Model Enhancement**: Create more accurate probability of win calculations based on historical bidder counts
- **Strategic Opportunity Targeting**: Find "sweet spot" opportunities with favorable value-to-competition ratios
- **Pricing Strategy Refinement**: Analyze correlation between number of bidders and winning bid amounts
- **Competitive Landscape Visualization**: Graphically represent competitive density across contract types, agencies, and NAICS codes
- **Bid/No-Bid Decision Support**: Provide objective metrics on competitive environment for milestone decisions

### Impact on Existing Features

This data element will directly enhance multiple aspects of the Data Insights platform:

- **Capture Profile Development**: Include competitive density analysis in opportunity assessment sections
- **Competitive Analysis**: Calculate average number of bidders by agency, NAICS code, and contract type
- **Strategic Dashboard**: Add competition intensity metrics to executive view
- **pWin Calculation**: Implement mathematical model using number of bidders as a key factor
- **Opportunity Qualification**: Filter and prioritize opportunities by competition level

### Integration with Shipley Process

The "number of offers received" data provides critical intelligence for multiple Shipley Capture milestones:

- **Milestone 0**: Use historical bidder data to assess early opportunity attractiveness
- **Milestone 1**: Incorporate competitive density analysis into resource allocation decisions
- **Milestone 2**: Use competition level as a key factor in bid/no-bid decisions
- **Milestone 3**: Refine pricing strategy based on expected number of competitors

### Mathematical pWin Model

The integration enables a more sophisticated pWin calculation that accounts for:

1. Base probability (1/number of bidders)
2. Capability alignment factor
3. Incumbent advantage factor
4. Agency relationship factor
5. Pricing strategy effectiveness

The resulting model provides more realistic win probability estimates that inform resource allocation and pursuit decisions.

## External Data Sources Integration

### Purpose

To enhance capture intelligence and proposal development by integrating multiple authoritative data sources, providing a comprehensive view of the federal contracting landscape, labor rates, and emerging opportunities.

### Primary Data Sources

#### Contract and Opportunity Data Sources

- **USAspending.gov API and Bulk Download**:

  - **Description**: Primary source for historical federal contract award data
  - **Implementation**: Both API connections and bulk data processing pipelines
  - **Key Data**: Contract details, obligations, agency relationships, and historical trends
  - **Strategic Value**: Provides foundation for historical spending analysis and recompete identification

- **SAM.gov API**:

  - **Description**: Authoritative source for active and future federal opportunities
  - **Implementation**: API integration with rate limiting and backoff strategies
  - **Key Data**: Active solicitations, pre-solicitation notices, award notices
  - **Strategic Value**: Enables pipeline building with forecasted opportunity data

- **NATO NSPA XML Feed**:

  - **Description**: European procurement opportunities from NATO Support and Procurement Agency
  - **Implementation**: XML feed processing with schema detection
  - **Key Data**: International defense and security procurement opportunities
  - **Strategic Value**: Expands addressable market to European defense contracts

- **Federal Procurement Data System (FPDS)**:
  - **Description**: Additional contract data with detailed reporting
  - **Implementation**: API integration and report processing
  - **Key Data**: Specialized contract reporting data
  - **Strategic Value**: Provides supplementary details not available in USAspending.gov

#### Small Business and Teaming Intelligence

- **Small Business Administration (SBA) SubNet**:

  - **Description**: Repository of subcontracting opportunities
  - **Implementation**: Data scraping and API integration
  - **Key Data**: Prime contractor subcontracting opportunities
  - **Strategic Value**: Identifies teaming opportunities and prime-sub relationships

- **SBA Mentor-Protégé Agreements**:
  - **Description**: Database of active mentor-protégé relationships
  - **Implementation**: Regular updates from downloadable spreadsheets
  - **Key Data**: Relationships between large businesses and small business partners
  - **Strategic Value**: Provides competitive intelligence on teaming relationships

#### Commercial Intelligence Sources

- **GovWin IQ API**:

  - **Description**: Commercial source for pre-RFP intelligence and teaming information
  - **Implementation**: Secure API integration (requires paid subscription)
  - **Key Data**: Early opportunity intelligence, forecast data, and competitive analysis
  - **Strategic Value**: Provides pre-RFP intelligence for early capture positioning

- **Bloomberg Government API**:
  - **Description**: Financial insights and subcontractor intelligence
  - **Implementation**: Secure API integration (requires paid subscription)
  - **Key Data**: Agency spending trends, legislative tracking, and contractor relationships
  - **Strategic Value**: Offers unique financial and legislative context for opportunities

#### Labor Rate and Economic Data Sources

- **ILOSTAT Database API**:

  - **Description**: International Labour Organization's repository of global labor statistics
  - **Implementation**: API integration with secure credential management
  - **Key Data**: International wage rates, employment statistics, and labor market trends
  - **Strategic Value**: Supports pricing for international opportunities and cost comparisons

- **Data.gov Contract-Awarded Labor Category API (CALC)**:

  - **Description**: General Services Administration's database of awarded labor rates
  - **Implementation**: API integration with secure access management
  - **Key Data**: Actual awarded labor rates for various contract categories
  - **Strategic Value**: Enables competitive labor rate positioning based on historical awards

- **Bureau of Labor Statistics OEWS API**:
  - **Description**: Occupational Employment and Wage Statistics data
  - **Implementation**: API-based retrieval with data transformation
  - **Key Data**: Comprehensive wage data for 800+ occupations with percentile breakdowns
  - **Strategic Value**: Provides market-based labor rate benchmarks with statistical validity

### Integration Approach

Each data source will be integrated with the following considerations:

1. **Secure Credential Management**: API keys and access credentials securely stored in environment variables
2. **Scheduled Refresh Cycles**: Automated data refresh on appropriate schedules (daily, weekly, monthly)
3. **Data Transformation Pipeline**: Processing to normalize and standardize data formats
4. **Schema Evolution Handling**: Dynamic adaptation to changes in source data structures
5. **Cross-Source Relationship Mapping**: Creation of relationships between data from different sources
6. **Unified Query Interface**: Common interface for querying across multiple data sources

### Strategic Applications

#### Integrated Capture Intelligence

The combined data will enable comprehensive capture intelligence:

- **Opportunity Lifecycle Tracking**: Follow opportunities from forecast through award
- **Competitive Landscape Analysis**: Map competitors, relationships, and historical patterns
- **Price-to-Win Modeling**: Develop data-driven pricing strategies with labor rate benchmarking
- **Market Entry Analysis**: Identify optimal entry points into new market segments
- **International Expansion Strategy**: Support capture planning for international opportunities

#### Enhanced Proposal Development

The data sources will directly enhance proposal development:

- **Labor Rate Justification**: Statistical support for proposed labor rates
- **Past Performance Validation**: Verification of historical contract performance
- **Competitive Positioning**: Evidence-based differentiation from competitors
- **Teaming Strategy Optimization**: Data-driven selection of optimal partners
- **Pricing Strategy Development**: Competitive pricing based on market intelligence

### Implementation Priorities

1. **Core Historical Data**: USAspending.gov API and Bulk Download
2. **Opportunity Pipeline**: SAM.gov API
3. **Labor Rate Intelligence**: BLS OEWS API and CALC API
4. **Teaming Intelligence**: SBA SubNet and Mentor-Protégé data
5. **International Expansion**: ILOSTAT and NATO NSPA data
6. **Premium Intelligence**: GovWin IQ and Bloomberg Government (budget permitting)

## Company Capabilities Foundation & Competitor Research (2025 Update)

- The foundation for all capture intelligence and gap analysis is a structured, queryable JSON profile of your company (KBR and subsidiaries), stored in PostgreSQL.
- This profile is built from USAspending.gov data (prime/sub awards, UEIs), web crawls, social media, and BloombergGov API, orchestrated by the Prime AI Agent and MCP tools.
- The same pipeline and schema will be used for competitor research, enabling direct side-by-side analysis.
- All data is processed and enriched by AI agents to extract key capabilities, relationships, and news, supporting semantic search and advanced analytics.
- JSON is the preferred storage format for extensibility, queryability, and AI-driven enrichment; markdown/Word/PDF can be generated for reporting as needed.

### SAM.gov Solicitation Enrichment Pipeline (May 2025)

To maximize the value of opportunity and requirement data, the project ingests and enriches full-text SAM.gov solicitations as `Document` objects. This enables:

- Storing and searching the full text of active/inactive solicitations for richer context
- Linking solicitations to contracts/opportunities for capability/gap analysis
- Generating embeddings for semantic search and RAG workflows
- Using AI/LLM to extract requirements, keywords, and capability gaps from real solicitation language
  See `/src/backend/data_acquisition/sam_gov_enrichment_example.py` for a sample enrichment function and `/docs/PLANNING.md` for the full pipeline plan.

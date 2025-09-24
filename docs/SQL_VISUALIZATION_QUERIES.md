# SQL Visualization Queries Reference

Purpose: Central catalog of SQL queries powering frontend visualizations and analytical components. Each entry lists: (1) Visualization / Use Case, (2) Query (canonical form with parameter tokens), (3) Source Script & Function / Line Context, (4) Key Dimensions & Metrics, (5) Notes for LLM fine-tuning (what the query semantically represents).

Parameter Token Conventions:

- :naics_code, :start_date, :end_date, :agency, :contractor, :psc, :limit, :n, :top_n, :months_ahead, :suitability_percentage
- Where original code performs string interpolation for conditional clauses (e.g., 60‑month toggle), canonicalize to parameterized WHERE fragments shown below.

---

## 1. Capability Stance Page Metrics & Visuals (`src/frontend/pages/capability_stance.py`)

### 1.1 Prime Awards Count (Metric Card)

```sql
SELECT COUNT(*) AS total_prime_awards
FROM s3_processed.usaspending_prime_awards_kbr
WHERE /* dynamic date filter */ 1=1;
```

Dimensions: none (aggregate)
Metric: total_prime_awards
LLM Note: Measures volume of KBR prime award actions (base + mods) within window.

### 1.2 Prime Obligation Sum (Metric Card)

```sql
SELECT COALESCE(SUM(federal_action_obligation),0) AS total_prime_obligation
FROM s3_processed.usaspending_prime_awards_kbr
WHERE /* dynamic date filter */ 1=1;
```

Metric: total_prime_obligation
Semantic: Dollar flow captured as prime.

### 1.3 Unique NAICS (Prime)

```sql
SELECT COUNT(DISTINCT naics_code) AS unique_naics_prime
FROM s3_processed.usaspending_prime_awards_kbr
WHERE /* date */ 1=1
  AND naics_code IS NOT NULL AND naics_code <> '';
```

Metric: unique_naics_prime
Meaning: Breadth of industry classification coverage.

### 1.4 Unique PSC (Prime)

```sql
SELECT COUNT(DISTINCT product_or_service_code) AS unique_psc_prime
FROM s3_processed.usaspending_prime_awards_kbr
WHERE /* date */ 1=1
  AND product_or_service_code IS NOT NULL AND product_or_service_code <> '';
```

### 1.5 Subawards Received Count / Value

```sql
SELECT COUNT(*) AS subawards_received
FROM s3_processed.usaspending_subawards_kbr
WHERE /* subaward_action_date filter */ 1=1;
```

```sql
SELECT COALESCE(SUM(subaward_amount),0) AS subawards_received_value
FROM s3_processed.usaspending_subawards_kbr
WHERE /* subaward_action_date filter */ 1=1;
```

### 1.6 Subawards Issued Count / Value

```sql
SELECT COUNT(*) AS subawards_issued
FROM s3_processed.usaspending_subawards_kbr_issued
WHERE /* subaward_action_date filter */ 1=1;
```

```sql
SELECT COALESCE(SUM(subaward_amount::numeric),0) AS subawards_issued_value
FROM s3_processed.usaspending_subawards_kbr_issued
WHERE /* subaward_action_date filter */ 1=1;
```

### 1.7 Unique NAICS / PSC (Issued Subawards)

```sql
SELECT COUNT(DISTINCT naics_code) AS unique_naics_issued
FROM s3_processed.usaspending_subawards_kbr_issued
WHERE /* date */ 1=1
  AND naics_code IS NOT NULL AND naics_code <> '';
```

```sql
SELECT COUNT(DISTINCT product_or_service_code) AS unique_psc_issued
FROM s3_processed.usaspending_subawards_kbr_issued
WHERE /* date */ 1=1
  AND product_or_service_code IS NOT NULL AND product_or_service_code <> '';
```

### 1.8 Top NAICS by Award Actions (Prime, Base Awards Only)

```sql
SELECT naics_code, naics_description, COUNT(*) AS award_count
FROM s3_processed.usaspending_prime_awards_kbr
WHERE modification_number = '0'
  AND naics_code IS NOT NULL AND naics_code <> ''
  AND /* optional recent window */ 1=1
GROUP BY naics_code, naics_description
ORDER BY award_count DESC, naics_code ASC
LIMIT 20;
```

Dimensions: naics_code, naics_description
Metric: award_count
Visualization: Bar chart.

### 1.9 Top NAICS by Obligations (Prime, Base Awards Only)

```sql
SELECT naics_code, naics_description, SUM(federal_action_obligation) AS total_obligation
FROM s3_processed.usaspending_prime_awards_kbr
WHERE modification_number = '0'
  AND naics_code IS NOT NULL AND naics_code <> ''
  AND /* optional recent window */ 1=1
GROUP BY naics_code, naics_description
ORDER BY total_obligation DESC, naics_code ASC
LIMIT 20;
```

Metric: total_obligation

### 1.10 Unique NAICS/PSC Combinations (Prime)

```sql
SELECT naics_code AS "NAICS", naics_description AS "NAICS Description",
       product_or_service_code AS "PSC", product_or_service_code_description AS "PSC Description"
FROM s3_processed.usaspending_prime_awards_kbr
WHERE /* date */ 1=1
  AND naics_code IS NOT NULL AND naics_code <> ''
  AND product_or_service_code IS NOT NULL AND product_or_service_code <> ''
GROUP BY naics_code, naics_description, product_or_service_code, product_or_service_code_description
ORDER BY naics_code ASC, product_or_service_code ASC;
```

Use: Table visualization.

### 1.11 Top Agencies (Prime)

```sql
SELECT parent_award_agency_name AS name, COUNT(*) AS count
FROM s3_processed.usaspending_prime_awards_kbr
WHERE /* date */ 1=1
  AND parent_award_agency_name IS NOT NULL AND parent_award_agency_name <> ''
GROUP BY parent_award_agency_name
ORDER BY count DESC
LIMIT 10;
```

### 1.12 Prime Company Frequency (All Prime KBR Companies)

```sql
SELECT recipient_name AS "Prime Company", recipient_uei, COUNT(*) AS count
FROM s3_processed.usaspending_prime_awards_kbr
WHERE recipient_uei IS NOT NULL AND recipient_uei <> ''
GROUP BY recipient_uei, recipient_name
ORDER BY "Prime Company" ASC;
```

### 1.13 Top Subcontracted Companies (Issued)

```sql
SELECT subawardee_name AS "Subawardee Company", subawardee_uei AS "Subawardee UEI", COUNT(*) AS count
FROM s3_processed.usaspending_subawards_kbr_issued
WHERE subawardee_uei IS NOT NULL AND subawardee_uei <> ''
GROUP BY subawardee_name, subawardee_uei
ORDER BY count DESC, "Subawardee Company" ASC
LIMIT 25;
```

### 1.14 All Subcontracted Companies (Distinct UEI)

```sql
SELECT DISTINCT ON (subawardee_uei)
    subawardee_name AS "Subawardee Company",
    subawardee_uei AS "Subawardee UEI"
FROM s3_processed.usaspending_subawards_kbr_issued
WHERE subawardee_uei IS NOT NULL AND subawardee_uei <> ''
ORDER BY subawardee_uei, subawardee_name ASC;
```

### 1.15 Unique NAICS/PSC Combinations (Issued Subawards)

```sql
SELECT naics_code AS "NAICS", naics_description AS "NAICS Description",
       product_or_service_code AS "PSC", product_or_service_code_description AS "PSC Description"
FROM s3_processed.usaspending_subawards_kbr_issued
WHERE /* date */ 1=1
  AND naics_code IS NOT NULL AND naics_code <> ''
  AND product_or_service_code IS NOT NULL AND product_or_service_code <> ''
GROUP BY naics_code, naics_description, product_or_service_code, product_or_service_code_description
ORDER BY naics_code ASC, product_or_service_code ASC;
```

### 1.16 Top Primes (KBR as Sub)

```sql
SELECT subawardee_name AS "Prime Company", subawardee_uei AS "UEI", subawardee_parent_name AS "Parent Name", COUNT(*) AS count
FROM s3_processed.usaspending_subawards_kbr
WHERE /* date */ 1=1
  AND subawardee_name IS NOT NULL AND subawardee_name <> ''
GROUP BY subawardee_name, subawardee_uei, subawardee_parent_name
ORDER BY count DESC
LIMIT 10;
```

### 1.17 All Prime Companies (KBR as Sub)

```sql
SELECT DISTINCT subawardee_name AS "Prime Company", subawardee_uei AS "UEI", subawardee_parent_name AS "Parent Name"
FROM s3_processed.usaspending_subawards_kbr
WHERE subawardee_name IS NOT NULL AND subawardee_name <> ''
ORDER BY "Prime Company";
```

---

## 2. Strategic Dashboard & Tab-Backed Queries

Source modules: `src/backend/data/app_processors/awards.py`, `competition.py`, plus derived DataFrame operations for charts.

### 2.1 Award Summary Metrics

Function: `get_award_summary` / `get_award_summary_optimized`

```sql
SELECT
    SUM(federal_action_obligation) AS total_obligations,
    COUNT(*) FILTER (WHERE modification_number = '0') AS total_award_actions,
    CASE WHEN COUNT(*) FILTER (WHERE modification_number = '0') > 0
         THEN SUM(federal_action_obligation) / COUNT(*) FILTER (WHERE modification_number = '0')
         ELSE 0 END AS avg_award_value,
    COUNT(DISTINCT contract_award_unique_key) FILTER (WHERE modification_number = '0') AS active_contracts
FROM s3_processed.usaspending_prime_awards
WHERE 1=1
  /* AND naics_code = :naics_code */
  /* AND action_date >= :start_date */
  /* AND action_date <= :end_date */
  /* AND parent_award_agency_name = :agency */
  /* AND recipient_name = :contractor */
  /* AND product_or_service_code = :psc */
;
```

### 2.2 Top Agencies by Count

Function: `get_top_agencies(metric='count')`

```sql
SELECT parent_award_agency_name, COUNT(*) AS award_count
FROM s3_processed.usaspending_prime_awards
WHERE 1=1 /* filters */
  AND modification_number = '0'
GROUP BY parent_award_agency_name
ORDER BY award_count DESC
LIMIT :n;
```

### 2.3 Top Agencies by Obligation

```sql
SELECT parent_award_agency_name, SUM(federal_action_obligation) AS federal_action_obligation
FROM s3_processed.usaspending_prime_awards
WHERE 1=1 /* filters */
GROUP BY parent_award_agency_name
ORDER BY federal_action_obligation DESC
LIMIT :n;
```

### 2.4 Quarterly Trends (Fiscal Year Alignment)

Function: `get_quarterly_trends`

```sql
SELECT
    EXTRACT(YEAR FROM action_date + INTERVAL '3 months') AS fiscal_year,
    EXTRACT(QUARTER FROM action_date + INTERVAL '3 months') AS fiscal_quarter,
    CONCAT(EXTRACT(YEAR FROM action_date + INTERVAL '3 months'), '-Q', EXTRACT(QUARTER FROM action_date + INTERVAL '3 months')) AS fiscal_period,
    COUNT(*) FILTER (WHERE modification_number = '0') AS award_count,
    SUM(federal_action_obligation) AS total_obligation
FROM s3_processed.usaspending_prime_awards
WHERE 1=1 /* filters */
GROUP BY fiscal_year, fiscal_quarter, fiscal_period
ORDER BY fiscal_year, fiscal_quarter;
```

LLM Note: Aggregates by fiscal quarter (Oct roll-over) using +3 month shift.

### 2.5 Optimized NAICS Data Pull

Function: `get_naics_data_optimized`

```sql
SELECT
    action_date,
    modification_number,
    federal_action_obligation,
    parent_award_agency_name,
    funding_sub_agency_name,
    funding_office_name,
    recipient_name,
    recipient_parent_name,
    award_type,
    naics_code,
    type_of_contract_pricing,
    extent_competed,
    product_or_service_code,
    contract_award_unique_key
FROM s3_processed.usaspending_prime_awards
WHERE 1=1 /* filters */
ORDER BY federal_action_obligation DESC, action_date DESC
/* LIMIT :limit */;
```

Use: Base DataFrame powering multiple tabs (market overview, competition, vehicles, geography).

### 2.6 Agency Obligation Ratio (Scatter)

Function: `get_agency_obligation_ratio`

```sql
SELECT
    parent_award_agency_name,
    COUNT(*) FILTER (WHERE modification_number = '0') AS award_count,
    SUM(federal_action_obligation) AS federal_action_obligation
FROM s3_processed.usaspending_prime_awards
WHERE 1=1 /* filters */
GROUP BY parent_award_agency_name;
```

Post-SQL: avg_award_value = obligation / award_count; log normalization + size capping.

### 2.7 Geographic State Obligations

Function: `get_geographic_state_obligations`

```sql
SELECT
    recipient_state_code AS location,
    SUM(federal_action_obligation) AS value
FROM s3_processed.usaspending_prime_awards
WHERE 1=1 /* filters */
  AND recipient_state_code IS NOT NULL
GROUP BY recipient_state_code
ORDER BY value DESC;
```

Visualization: Choropleth / heatmap.

### 2.8 Contract Vehicle Distribution (Vehicle Preference per Agency)

Function: `get_contract_vehicle_agency_analysis`

```sql
SELECT
    parent_award_agency_name,
    award_type,
    SUM(federal_action_obligation) AS federal_action_obligation
FROM s3_processed.usaspending_prime_awards
WHERE 1=1 /* filters */
  AND modification_number = '0'
GROUP BY parent_award_agency_name, award_type
ORDER BY parent_award_agency_name, federal_action_obligation DESC;
```

### 2.9 Contract Vehicle Success Rates

Function: `get_contract_vehicle_success_rates`

```sql
SELECT
    award_type AS contract_vehicle,
    SUM(federal_action_obligation) AS obligation
FROM s3_processed.usaspending_prime_awards
WHERE 1=1 /* filters */
  AND modification_number = '0'
GROUP BY award_type
ORDER BY obligation DESC;
```

### 2.10 Contract Type Competition (Competitors by Pricing Type)

Function: `get_contract_type_analysis` (competition segment)

```sql
SELECT
    type_of_contract_pricing AS contract_type,
    COUNT(DISTINCT recipient_name) AS number_of_competitors
FROM s3_processed.usaspending_prime_awards
WHERE 1=1 /* filters */
  AND type_of_contract_pricing IS NOT NULL
GROUP BY type_of_contract_pricing
ORDER BY number_of_competitors DESC
LIMIT 10;
```

### 2.11 Contract Type Value (Obligation & Competitors)

```sql
SELECT
    type_of_contract_pricing AS contract_type,
    SUM(federal_action_obligation) AS total_obligation,
    COUNT(DISTINCT recipient_name) AS number_of_competitors
FROM s3_processed.usaspending_prime_awards
WHERE 1=1 /* filters */
  AND type_of_contract_pricing IS NOT NULL
GROUP BY type_of_contract_pricing
ORDER BY total_obligation DESC
LIMIT 10;
```

### 2.12 Agency-Specific Top NAICS / PSC / Contractors

Function: `get_agency_top_data`
Top NAICS:

```sql
SELECT
    naics_code,
    naics_description,
    SUM(federal_action_obligation) AS federal_action_obligation
FROM s3_processed.usaspending_prime_awards
WHERE parent_award_agency_name = :agency /* additional filters */
  AND naics_code IS NOT NULL
  AND naics_description IS NOT NULL
GROUP BY naics_code, naics_description
ORDER BY federal_action_obligation DESC
LIMIT 10;
```

Top PSC:

```sql
SELECT
    product_or_service_code,
    product_or_service_code_description,
    SUM(federal_action_obligation) AS federal_action_obligation
FROM s3_processed.usaspending_prime_awards
WHERE parent_award_agency_name = :agency /* additional filters */
  AND product_or_service_code IS NOT NULL
  AND product_or_service_code_description IS NOT NULL
GROUP BY product_or_service_code, product_or_service_code_description
ORDER BY federal_action_obligation DESC
LIMIT 10;
```

Top Contractors:

```sql
SELECT
    recipient_name,
    SUM(federal_action_obligation) AS federal_action_obligation
FROM s3_processed.usaspending_prime_awards
WHERE parent_award_agency_name = :agency /* additional filters */
  AND recipient_name IS NOT NULL
GROUP BY recipient_name
ORDER BY federal_action_obligation DESC
LIMIT 10;
```

### 2.13 Competitor-Agency Relationships Heatmap

Function: `get_competitor_agency_relationships`

```sql
WITH top_competitors AS (
    SELECT recipient_name
    FROM s3_processed.usaspending_prime_awards
    WHERE 1=1 /* filters */
    GROUP BY recipient_name
    ORDER BY SUM(federal_action_obligation) DESC
    LIMIT :top_n
),
competitor_agencies AS (
    SELECT
        recipient_name,
        parent_award_agency_name,
        SUM(federal_action_obligation) AS federal_action_obligation,
        ROW_NUMBER() OVER (PARTITION BY recipient_name ORDER BY SUM(federal_action_obligation) DESC) AS agency_rank
    FROM s3_processed.usaspending_prime_awards
    WHERE 1=1 /* filters */
      AND recipient_name IN (SELECT recipient_name FROM top_competitors)
    GROUP BY recipient_name, parent_award_agency_name
)
SELECT
    recipient_name,
    parent_award_agency_name,
    federal_action_obligation
FROM competitor_agencies
WHERE agency_rank <= 3
ORDER BY recipient_name, federal_action_obligation DESC;
```

Visualization: Heatmap / bipartite mapping.

### 2.14 Competitive Treemap

Function: `get_treemap_data`

```sql
SELECT
    recipient_parent_name,
    recipient_name,
    funding_sub_agency_name,
    MAX(CASE WHEN transaction_description IS NOT NULL AND transaction_description <> ''
             THEN transaction_description ELSE 'All Contracts' END) AS transaction_description,
    SUM(federal_action_obligation) AS federal_action_obligation,
    COUNT(*) FILTER (WHERE modification_number = '0') AS award_count
FROM s3_processed.usaspending_prime_awards
WHERE 1=1 /* filters */
GROUP BY recipient_parent_name, recipient_name, funding_sub_agency_name
ORDER BY SUM(federal_action_obligation) DESC
LIMIT :limit;
```

Hierarchy: Parent Company > Recipient > Funding Sub-Agency > (Representative) Contract Narrative.

### 2.15 Expiring Contracts (Optimized View)

Function: `get_expiring_contracts_optimized`

```sql
SELECT contract_award_unique_key, award_id_piid, recipient_name,
       parent_award_agency_name, funding_sub_agency_name,
       federal_action_obligation, potential_total_value_of_award,
       effective_end_date, days_to_expiration, expiration_timeframe,
       date_quality
FROM s3_processed.mv_expiring_contracts
WHERE 1=1 /* filters */
  AND days_to_expiration <= :months_ahead * 30
ORDER BY days_to_expiration, federal_action_obligation DESC
LIMIT :limit;
```

Visualization: Timeline / table of upcoming recompetes.

### 2.16 Five-Year Projection (Base Contract Selection)

Function: `get_five_year_projection` (initial contract set extraction)

```sql
WITH contract_totals AS (
    SELECT
        contract_award_unique_key,
        COALESCE(period_of_performance_current_end_date,
                 ordering_period_end_date,
                 action_date + INTERVAL '1 year') AS contract_end_date,
        SUM(federal_action_obligation) AS total_contract_obligation,
        GREATEST(
            EXTRACT(EPOCH FROM
                COALESCE(period_of_performance_current_end_date,
                        ordering_period_end_date,
                        action_date + INTERVAL '1 year') -
                COALESCE(period_of_performance_start_date, action_date)
            ) / (365.25 * 24 * 3600),
            1.0
        ) AS performance_period_years
    FROM s3_processed.usaspending_prime_awards
    WHERE 1=1 /* filters */
      AND COALESCE(period_of_performance_current_end_date,
                   ordering_period_end_date,
                   action_date + INTERVAL '1 year') >= CURRENT_DATE
      AND COALESCE(period_of_performance_current_end_date,
                   ordering_period_end_date,
                   action_date + INTERVAL '1 year') <= CURRENT_DATE + INTERVAL '5 years'
    GROUP BY contract_award_unique_key, contract_end_date,
             period_of_performance_start_date, action_date
)
SELECT contract_end_date, total_contract_obligation, performance_period_years
FROM contract_totals
WHERE total_contract_obligation > 0
ORDER BY contract_end_date;
```

Post-SQL: Python applies escalation, quarter bucketing, and suitability allocation.

---

## 3. Indexing / Embedding Support (For Contextual Retrieval)

Although not direct visualizations, these queries feed semantic features used by UI search / future vector search.

### 3.1 Embedding Source Rows (Prime)

File: `data_processing/4_vectorize_semantic_description.py`

```sql
SELECT contract_transaction_unique_key, semantic_description
FROM s3_processed.usaspending_prime_awards
WHERE semantic_description IS NOT NULL AND semantic_description <> ''
  AND semantic_vector IS NULL
ORDER BY contract_transaction_unique_key
LIMIT :batch_size;
```

### 3.2 Embedding Source Rows (Subawards)

```sql
SELECT subaward_unique_key, semantic_description
FROM s3_processed.usaspending_subawards
WHERE semantic_description IS NOT NULL AND semantic_description <> ''
  AND semantic_vector IS NULL
ORDER BY subaward_unique_key
LIMIT :batch_size;
```

---

## 4. Filter Metadata & System Introspection

Representative queries used for populating dropdown filters and validating objects.

### 4.1 Distinct NAICS Codes Fallback

```sql
SELECT DISTINCT naics_code
FROM s3_processed.usaspending_prime_awards
WHERE naics_code IS NOT NULL
ORDER BY naics_code;
```

### 4.2 Existence Checks (Example)

```sql
SELECT EXISTS(
  SELECT 1 FROM information_schema.tables
  WHERE table_schema = 's3_processed' AND table_name = 'usaspending_prime_awards'
);
```

---

## 5. Fine-Tuning Guidance Mapping

For each visualization query above, treat the primary GROUP BY dimensions as categorical context tokens and aggregate metrics (SUM / COUNT / AVG derived) as numeric factual anchors. Generation tasks can:

- Form comparative statements (e.g., Top NAICS vs others) using ordered results.
- Derive ratios (award_count share, market_share) not explicitly queried but computable.
- Combine time-series (quarterly trends) with projection outputs to explain growth trajectories.

---

## 6. Change Log

- Initial extraction (2025-08-15): Captured capability stance, strategic dashboard, competition, vehicle, geographic, projection, expiring contracts, and embedding feeder queries.

End of file.

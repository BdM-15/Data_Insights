# USAspending Data Architecture & Schema (May 2025)
## Schema & Table Naming Conventions

## Schema & Table Naming Conventions (May 2025 Update)

The Data_Insights project uses a strict three-stage schema approach for all USAspending data, but **all analytics, reporting, indexes, and precomputed tables are now created exclusively in the `s3_processed` schema** for maximum performance and clarity:

- **s1_raw**: As-ingested, unmodified data from USAspending.gov. Immutable, for audit and reprocessing only. No analytics or reporting is performed on these tables.
- **s2_interim**: Cleaned and standardized data, but not deduplicated or indexed for analytics. Used only for ETL processing. No analytics or reporting is performed on these tables.
- **s3_processed**: Deduplicated, analytics-ready data with all performance indexes, precomputed filter/aggregation tables, and (optionally) materialized views. **All dashboards, APIs, analytics, and AI agents use only this schema.**

**Key Practices (May 2025):**

- **All analytics, reporting, indexes, and precomputed tables (filter values, dependencies, quarterly_data, etc.) are created in the `s3_processed` schema only.**
- **Never run analytics or reporting on `s1_raw` or `s2_interim` tables.**
- **Only create performance indexes and materialized views in the `s3_processed` schema.**
- **All deduplication and business rules are applied in the move from `s2_interim` to `s3_processed`.**
- **Table names are always `usaspending_prime_awards` or `usaspending_subawards` (no suffixes for stage).**
- **All dashboard metrics, aggregations, and calculations are now performed via direct, filter-aware SQL queries (no Pandas-based aggregation in the backend).**
- **Materialized views in `s3_processed` are recommended for the most common, high-traffic queries (e.g., Top Competitors by Market Share) to provide instant dashboard performance. These should be refreshed after each ETL/transform run.**

**Deduplication Keys:**
- Prime awards: `contract_transaction_unique_key` (unique transaction key)
- Subawards: Composite key (`prime_award_unique_key`, `subaward_number`, `subaward_action_date`)

**Transformation & Indexing:**
- All index creation and filter/aggregation table generation is performed in the transformation stage, using only `s3_processed.usaspending_prime_awards` and `s3_processed.usaspending_subawards` as sources.
- All precomputed filter tables, dependencies, and quarterly aggregations are created in `s3_processed` (e.g., `s3_processed.filter_values_*`, `s3_processed.filter_dependencies`, `s3_processed.quarterly_data`).
- Composite and single-column indexes are created for all major filter/grouping columns (e.g., `recipient_parent_name, recipient_name, funding_sub_agency_name`, `federal_action_obligation`, `modification_number`, etc.)
- PostgreSQL-specific index optimizations (B-tree, GIN) are used for improved query performance.
- Filter value tables and dependent filter relationships are precomputed for fast UI filtering and analytics.
- Quarterly aggregation tables are created for timeline visualizations, with fiscal year/quarter computed dynamically.

**Summary:**
All analytics, reporting, and dashboard queries are now filter-aware, SQL-backed, and index-optimized, using only the `s3_processed` schema as the source. Materialized views are recommended for the most common, high-traffic queries to ensure instant dashboard performance.

**See also:** `src/backend/data/data_processing/transformation.py` for index/materialized view creation logic.

---

# USAspending Slim Table Architecture (May 2025, Updated)

## usaspending_prime_awards & usaspending_subawards (Table Structure)

### Overview

To support maintainable, normalized, and AI/LLM-friendly analytics, the Data_Insights project uses two slimmed tables at each stage:

- `usaspending_prime_awards`: Contains only the required columns for prime awards analytics and AI workflows.
- `usaspending_subawards`: Contains only the required columns for subawards analytics and AI workflows, including the join key (`prime_award_unique_key`).

These tables are designed for dynamic joins and smart querying by analytics code and AI/LLM agents. They are not denormalized; all joins are performed as needed for reporting or analysis. This approach supports future integration with Model Context Protocol (MCP) agents and local LLMs (Ollama, etc.).

**See the top of this document for schema and naming conventions.**

---

### usaspending_prime_awards_slim Schema

| Column Name                              | Type      | Description / Notes                         |
| ---------------------------------------- | --------- | ------------------------------------------- |
| contract_transaction_unique_key          | TEXT, PK  | Unique transaction key (primary key)        |
| contract_award_unique_key                | TEXT      | Unique award key                            |
| action_date_fiscal_year                  | TEXT      | Fiscal year of action date                  |
| action_date                              | TEXT      | Action date                                 |
| parent_award_id_piid                     | TEXT      | Parent award ID                             |
| award_id_piid                            | TEXT      | Award ID                                    |
| modification_number                      | TEXT      | Modification number                         |
| federal_action_obligation                | TEXT      | Federal action obligation amount            |
| total_dollars_obligated                  | TEXT      | Total dollars obligated                     |
| potential_total_value_of_award           | TEXT      | Potential total value of award              |
| total_outlayed_amount_for_overall_award  | TEXT      | Total outlayed amount for overall award     |
| period_of_performance_start_date         | TEXT      | Start date of period of performance         |
| period_of_performance_current_end_date   | TEXT      | Current end date of period of performance   |
| period_of_performance_potential_end_date | TEXT      | Potential end date of period of performance |
| ordering_period_end_date                 | TEXT      | Ordering period end date                    |
| primary_place_of_performance_city_name   | TEXT      | City of performance                         |
| primary_place_of_performance_state_code  | TEXT      | State code of performance                   |
| prime_award_base_transaction_description | TEXT      | Base transaction description                |
| transaction_description                  | TEXT      | Transaction description                     |
| naics_code                               | TEXT      | NAICS code                                  |
| naics_description                        | TEXT      | NAICS description                           |
| product_or_service_code                  | TEXT      | PSC code                                    |
| product_or_service_code_description      | TEXT      | PSC description                             |
| dod_acquisition_program_description      | TEXT      | DoD acquisition program description         |
| parent_award_agency_name                 | TEXT      | Parent award agency name                    |
| awarding_sub_agency_name                 | TEXT      | Awarding sub-agency name                    |
| awarding_office_name                     | TEXT      | Awarding office name                        |
| funding_agency_name                      | TEXT      | Funding agency name                         |
| funding_sub_agency_name                  | TEXT      | Funding sub-agency name                     |
| funding_office_name                      | TEXT      | Funding office name                         |
| recipient_name                           | TEXT      | Recipient name                              |
| recipient_uei                            | TEXT      | Recipient UEI                               |
| recipient_parent_name                    | TEXT      | Recipient parent name                       |
| recipient_parent_uei                     | TEXT      | Recipient parent UEI                        |
| solicitation_date                        | TEXT      | Solicitation date                           |
| solicitation_procedures                  | TEXT      | Solicitation procedures                     |
| extent_competed                          | TEXT      | Extent competed                             |
| type_of_set_aside                        | TEXT      | Type of set aside                           |
| fair_opportunity_limited_sources         | TEXT      | Fair opportunity limited sources            |
| other_than_full_and_open_competition     | TEXT      | Other than full and open competition        |
| number_of_offers_received                | TEXT      | Number of offers received                   |
| subcontracting_plan                      | TEXT      | Subcontracting plan                         |
| government_furnished_property            | TEXT      | Government furnished property               |
| type_of_contract_pricing                 | TEXT      | Type of contract pricing                    |
| action_type                              | TEXT      | Action type                                 |
| award_type                               | TEXT      | Award type                                  |
| type_of_idc                              | TEXT      | Type of IDC                                 |
| idv_type                                 | TEXT      | IDV type                                    |
| undefinitized_action                     | TEXT      | Undefinitized action                        |
| program_acronym                          | TEXT      | Program acronym                             |
| multi_year_contract                      | TEXT      | Multi-year contract                         |
| multiple_or_single_award_idv             | TEXT      | Multiple or single award IDV                |
| usaspending_permalink                    | TEXT      | USAspending permalink                       |
| created_at                               | TIMESTAMP | Record creation timestamp                   |
| updated_at                               | TIMESTAMP | Record update timestamp                     |
| fetch_date                               | DATE      | ETL fetch date                              |

---

### usaspending_subawards_slim Schema

| Column Name                                      | Type      | Description / Notes                 |
| ------------------------------------------------ | --------- | ----------------------------------- |
| id                                               | INTEGER   | Internal row ID                     |
| created_at                                       | TIMESTAMP | Record creation timestamp           |
| updated_at                                       | TIMESTAMP | Record update timestamp             |
| fetch_date                                       | DATE      | ETL fetch date                      |
| prime_award_unique_key                           | TEXT      | Join key to prime awards            |
| subaward_type                                    | TEXT      | Subaward type                       |
| subaward_number                                  | TEXT      | Subaward number                     |
| subaward_amount                                  | TEXT      | Subaward amount                     |
| subaward_action_date                             | TEXT      | Subaward action date                |
| subaward_action_date_fiscal_year                 | TEXT      | Fiscal year of subaward action date |
| subawardee_uei                                   | TEXT      | Subawardee UEI                      |
| subawardee_name                                  | TEXT      | Subawardee name                     |
| subawardee_dba_name                              | TEXT      | Subawardee DBA name                 |
| subawardee_parent_uei                            | TEXT      | Subawardee parent UEI               |
| subawardee_parent_name                           | TEXT      | Subawardee parent name              |
| subawardee_country_code                          | TEXT      | Subawardee country code             |
| subawardee_country_name                          | TEXT      | Subawardee country name             |
| subawardee_city_name                             | TEXT      | Subawardee city name                |
| subawardee_state_code                            | TEXT      | Subawardee state code               |
| subawardee_business_types                        | TEXT      | Subawardee business types           |
| subaward_primary_place_of_performance_city_name  | TEXT      | Place of performance city name      |
| subaward_primary_place_of_performance_state_code | TEXT      | Place of performance state code     |
| subaward_description                             | TEXT      | Subaward description                |

---

#### usaspending_subawards_slim Columns

The following columns are included in `usaspending_subawards_slim` (as of May 2025):

- `prime_award_unique_key` (join key to prime awards)
- `subaward_sam_report_id`
- `subaward_number`
- `subaward_amount`
- `subaward_action_date`
- `subaward_description`
- `subawardee_name`
- `subawardee_uei`
- `subawardee_parent_name`
- `subawardee_parent_uei`
- `subawardee_city_name`
- `subawardee_state_code`
- `subawardee_country_code`
- `subawardee_country_name`
- `subawardee_business_types`
- `subaward_primary_place_of_performance_city_name`
- `subaward_primary_place_of_performance_state_code`
- `subaward_type`

Additional metadata columns (e.g., `id`, `created_at`, `updated_at`, `fetch_date`) are included for auditing and ETL tracking.

#### Join Guidance (May 2025)

- Use `prime_award_unique_key` to join `s3_processed.usaspending_subawards` to `s3_processed.usaspending_prime_awards` for analytics and reporting.
- All joins should be performed dynamically in queries or by AI/LLM agents, not by denormalizing the tables.
- Materialized views or denormalized tables may be created for specific reporting needs if required, but are not the default.

#### Rationale

- This architecture supports maintainability, scalability, and future AI/LLM-driven analytics.
- Enables integration with Model Context Protocol (MCP) agents and local LLMs for advanced analytics, reasoning, and document generation.
- Robust deduplication and schema-aware transformation ensure high data quality for downstream AI, analytics, and RAG workflows.

# Filter/Aggregation Tables for Analytics & AI

The transformation pipeline precomputes filter value tables (e.g., `filter_values_parent_award_agency_name`, `filter_values_naics_code`) and dependent filter relationships (`filter_dependencies`) for fast UI filtering and analytics. Quarterly aggregation tables (e.g., `quarterly_data`) are also created for timeline visualizations. All are generated in `s3_processed` and are safe for repeated runs.

---

---

## Pydantic Model Alignment

The Pydantic models in `src/backend/data/models/data_models.py` are designed to mirror and validate the structure of the slimmed USAspending tables for robust data processing and API responses. The mapping is as follows:

### Prime Awards Table → Pydantic Models

- **PrimeContractAwardDetails**: Maps to core award fields (dates, values, IDs, performance period, contract types, etc.)
- **PrimeCompetitorDetails**: Maps to recipient and parent recipient fields (names, UEIs)
- **PrimeContractRequirementDetails**: Maps to requirement/classification fields (descriptions, NAICS, PSC, DoD program, etc.)
- **PrimeCustomerDetails**: Maps to agency and office fields (parent/awarding/funding agencies and offices)
- **PrimeSolicitationDetails**: Maps to solicitation and competition fields (solicitation date, procedures, extent competed, set-aside, etc.)

These models are used in combination to represent a full record from `usaspending_prime_awards_slim`.

### Subawards Table → Pydantic Models

- **SubcontractAwardDetails**: Maps to core subaward fields (join key, type, number, amount, action date, fiscal year)
- **SubcontractCompetitorDetails**: Maps to subawardee identity fields (UEI, name, DBA, parent info, country, city, state, business types)
- **SubcontractRequirementsDetails**: Maps to requirement and place of performance fields (performance city/state, description)

These models are used together to represent a full record from `usaspending_subawards_slim`.

> **Note:** Not all database columns are always present in a single Pydantic model. Instead, models are composed to reflect logical groupings for validation, API, and analytics use cases. See the model docstrings in `data_models.py` for details.

---

# USAspending Database Schema Documentation

This document provides a comprehensive overview of the schemas and tables within the USAspending database, organized to highlight the most relevant data for capture managers. The database is organized into four main schemas, each serving a specific purpose in the data processing pipeline.

## Data Flow and Transformations

The USAspending database follows a standard ETL (Extract, Transform, Load) process:

1. **Extract**: Data is extracted from USAspending.gov bulk downloads and loaded into the `raw` schema without modification.
2. **Transform**: Data is cleaned, normalized, and prepared in the `int` schema.
3. **Load**: Transformed data is loaded into optimized reporting tables in the `rpt` schema.

## Key Categories for Capture Managers

Capture managers should focus on these key categories of data when exploring the database:

## Common Transformations

The following transformations are generally applied when moving data from `raw` to `int` and then to `rpt` schemas:

1. **Data Cleansing**

   - Standardizing date formats
   - Trimming whitespace from text fields
   - Converting case (uppercase, lowercase) for consistency
   - Handling NULL values and empty strings

2. **Data Normalization**

   - Creating reference tables for repeated values
   - Establishing foreign key relationships
   - Splitting complex fields into atomic components

3. **Data Enrichment**

   - Calculating derived fields (fiscal_year from action_date)
   - Creating hierarchical structures (parent-child relationships)
   - Adding geospatial data

4. **Performance Optimization**
   - Creating indexes on commonly queried fields
   - Pre-aggregating values for reporting
   - Denormalizing data for query performance

## Sample Queries for Capture Managers

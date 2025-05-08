# USAspending Database Schema Documentation

This document provides a comprehensive overview of the schemas and tables within the USAspending database, organized to highlight the most relevant data for capture managers. The database is organized into four main schemas, each serving a specific purpose in the data processing pipeline.

## Schema Overview

### 1. `raw` Schema

Contains the original, unmodified data directly imported from USAspending.gov bulk downloads. This schema preserves the data in its original form without any transformations.

### 2. `int` (Intermediate) Schema

Contains normalized and cleaned data derived from the raw schema. This schema represents an intermediate step in the ETL process, where data has been transformed but not yet optimized for reporting.

### 3. `rpt` (Reporting) Schema

Contains denormalized tables specifically designed for efficient querying and reporting. These tables combine data from multiple sources and are optimized for analytics.

### 4. `public` Schema

Contains reference data, lookup tables, and administrative tables that support the application's functionality.

## Data Flow and Transformations

The USAspending database follows a standard ETL (Extract, Transform, Load) process:

1. **Extract**: Data is extracted from USAspending.gov bulk downloads and loaded into the `raw` schema without modification.
2. **Transform**: Data is cleaned, normalized, and prepared in the `int` schema.
3. **Load**: Transformed data is loaded into optimized reporting tables in the `rpt` schema.

## Key Categories for Capture Managers

Capture managers should focus on these key categories of data when exploring the database:

### 1. Contract Identification

Fields that uniquely identify contracts and awards:

- `piid` - Procurement Instrument Identifier
- `parent_award_id` - Parent award identifier for tracking IDVs
- `award_id` - Internal unique identifier
- `generated_unique_award_id` - System-generated unique award identifier
- `unique_award_key` - USAspending unique award key

### 2. Contract Details

Fields describing contract specifics:

- `award_description` - Description of the contract
- `type_of_contract_pricing` - Contract pricing type (FFP, T&M, CPFF, etc.)
- `contract_award_type` - Type of contract award
- `contract_award_type_desc` - Description of contract award type
- `base_and_all_options_value` - Total potential contract value
- `base_exercised_options_val` - Current exercised contract value
- `total_obligation` - Total funding obligated to date
- `potential_total_value_awar` - Maximum potential value of the award

### 3. Competitive Information

Fields related to competition and set-asides:

- `extent_competed` - Extent to which the contract was competed
- `type_set_aside` - Set-aside type (small business, 8(a), etc.)
- `number_of_offers_received` - Number of bids/proposals received
- `solicitation_procedures` - Procedures used for solicitation
- `fair_opportunity_limited_s` - Fair opportunity limited sources justification
- `other_than_full_and_open_c` - Other than full and open competition justification

### 4. Contract Timing

Fields related to contract timelines:

- `action_date` - Date of the action
- `period_of_performance_star` - Start date of performance
- `period_of_performance_curr` - Current end date of performance
- `ordering_period_end_date` - End date of ordering period
- `solicitation_date` - Date of solicitation

### 5. Agency Information

Fields identifying the contracting agencies:

- `awarding_agency_name` - Name of awarding agency
- `funding_agency_name` - Name of funding agency
- `awarding_office_name` - Name of contracting office
- `funding_office_name` - Name of funding office
- `awarding_sub_tier_agency_n` - Name of sub-tier agency awarding the contract

### 6. Classification Information

Fields classifying the contract's purpose:

- `product_or_service_code` - Product or Service Code
- `product_or_service_co_desc` - Description of PSC
- `naics` - NAICS code
- `naics_description` - Description of NAICS code
- `major_program` - Major program name

### 7. Competitor Information

Fields describing competitors and their capabilities:

**Prime Competitor Information**

- `awardee_or_recipient_legal` - Legal name of competitor
- `awardee_or_recipient_uniqu` - DUNS number
- `awardee_or_recipient_uei` - Unique Entity Identifier (UEI)
- `business_categories` - Array of business categories
- `ultimate_parent_legal_enti` - Ultimate parent company name
- `ultimate_parent_unique_ide` - Parent DUNS number
- `ultimate_parent_uei` - Parent UEI

**Subaward Information:** 

- `subaward_id` - Unique identifier for subawards
- `subaward_amount` - Dollar value of the subaward
- `subawardee_name` - Name of the subcontractor
- `subawardee_uei` - Unique Entity Identifier for subcontractor
- `subaward_description` - Description of subcontracted work
- `subaward_date` - Date subaward was issued
- `subaward_place_of_performance` - Location where subcontracted work is performed
- `subawardee_business_types` - Business size and socioeconomic categories of subcontractor

This subaward data helps identify capability gaps and competitive discriminators by revealing:
- Which capabilities competitors outsource vs. perform in-house
- Recurring partnership patterns between primes and subcontractors
- Division of work within competitor teams
- Geographic distribution of work across team members
- Small business utilization strategies

### 8. Small Business Designations

Boolean fields indicating contractor types:

- `small_business_competitive` - Small business competitiveness
- `emerging_small_business` - Emerging small business
- `c8a_program_participant` - 8(a) program participant
- `woman_owned_business` - Woman-owned business
- `women_owned_small_business` - Women-owned small business
- `service_disabled_veteran_o` - Service-disabled veteran-owned
- `veteran_owned_business` - Veteran-owned business
- `small_disadvantaged_busine` - Small disadvantaged business
- `historically_underutilized` - HUBZone business

### 9. Place of Performance

Fields describing where the work is performed:

- `place_of_perform_city_name` - City of performance
- `place_of_perform_state_nam` - State of performance
- `place_of_perform_country_n` - Country of performance
- `place_of_perform_zip_last4` - ZIP code of performance
- `place_of_performance_congr` - Congressional district of performance

## Schema Details

### `raw` Schema

#### `source_procurement_transaction`

This table contains the raw procurement (contract) data as downloaded from USAspending.gov.

**Key fields for capture managers by category:**

1. **Contract Identification**

   - `piid` - Procurement Instrument Identifier (contract number)
   - `parent_award_id` - Parent award ID for task/delivery orders
   - `award_or_idv_flag` - Indicates if record is an award or IDV
   - `unique_award_key` - Unique identifier for the award

2. **Contract Details**

   - `award_description` - Description of the contract
   - `contract_award_type` - Type of contract award
   - `contract_award_type_desc` - Description of contract award type
   - `type_of_contract_pricing` - Contract pricing type (FFP, T&M, CPFF, etc.)
   - `base_and_all_options_value` - Total potential contract value
   - `base_exercised_options_val` - Current exercised contract value
   - `potential_total_value_awar` - Maximum potential value of the award

3. **Competitive Information**

   - `extent_competed` - Extent to which the contract was competed
   - `extent_compete_description` - Description of competition extent
   - `type_set_aside` - Set-aside type (small business, 8(a), etc.)
   - `type_set_aside_description` - Description of set-aside type
   - `number_of_offers_received` - Number of bids/proposals received
   - `solicitation_procedures` - Procedures used for solicitation
   - `solicitation_procedur_desc` - Description of solicitation procedures
   - `fair_opportunity_limited_s` - Fair opportunity limited sources justification
   - `other_than_full_and_open_c` - Other than full and open competition justification

4. **Contract Timing**

   - `action_date` - Date of the action
   - `period_of_performance_star` - Start date of performance
   - `period_of_performance_curr` - Current end date of performance
   - `ordering_period_end_date` - End date of ordering period
   - `solicitation_date` - Date of solicitation
   - `period_of_perf_potential_e` - Potential end date including all options

5. **Agency Information**

   - `awarding_agency_code` - Code of awarding agency
   - `awarding_agency_name` - Name of awarding agency
   - `funding_agency_code` - Code of funding agency
   - `funding_agency_name` - Name of funding agency
   - `awarding_sub_tier_agency_c` - Code of awarding sub-tier agency
   - `awarding_sub_tier_agency_n` - Name of awarding sub-tier agency
   - `awarding_office_code` - Code of awarding office
   - `awarding_office_name` - Name of awarding office
   - `funding_office_name` - Name of funding office

6. **Classification Information**

   - `product_or_service_code` - Product or Service Code (PSC)
   - `product_or_service_co_desc` - Description of PSC
   - `naics` - NAICS code
   - `naics_description` - Description of NAICS code
   - `major_program` - Major program name
   - `program_system_or_equipmen` - Program system or equipment code
   - `program_system_or_equ_desc` - Description of program system/equipment
   - `dod_claimant_program_code` - DoD claimant program code
   - `program_acronym` - Program acronym

7. **Contractor Information**

   - `awardee_or_recipient_legal` - Legal name of contractor
   - `awardee_or_recipient_uniqu` - DUNS number
   - `awardee_or_recipient_uei` - Unique Entity Identifier (UEI)
   - `cage_code` - CAGE code
   - `ultimate_parent_legal_enti` - Ultimate parent company name
   - `ultimate_parent_unique_ide` - Parent DUNS number
   - `ultimate_parent_uei` - Parent UEI
   - `vendor_doing_as_business_n` - Doing business as name
   - `vendor_phone_number` - Vendor phone number

8. **Place of Performance**

   - `place_of_perform_city_name` - City of performance
   - `place_of_perform_state_nam` - State of performance
   - `place_of_perform_country_n` - Country of performance
   - `place_of_performance_zip5` - ZIP code of performance
   - `place_of_performance_congr` - Congressional district of performance
   - `place_of_performance_state` - State code of performance

9. **Contract Administration**
   - `contract_bundling` - Contract bundling status
   - `multi_year_contract` - Multi-year contract flag
   - `cost_or_pricing_data` - Cost or pricing data requirement
   - `subcontracting_plan` - Subcontracting plan requirement
   - `purchase_card_as_payment_m` - Purchase card as payment method
   - `consolidated_contract` - Consolidated contract flag
   - `type_of_idc` - Type of indefinite delivery contract
   - `performance_based_service` - Performance-based service acquisition
   - `contingency_humanitarian_o` - Contingency, humanitarian, or peacekeeping operation

**All columns:**

- `detached_award_procurement_id` - Integer, primary key, not null
- `detached_award_proc_unique` - Text, not null, unique constraint
- `a_76_fair_act_action` - Text
- `a_76_fair_act_action_desc` - Text
- `action_date` - Text
- `action_type` - Text
- `action_type_description` - Text
- `additional_reporting` - Text
- `agency_id` - Text
- `annual_revenue` - Text
- `award_description` - Text
- `award_modification_amendme` - Text
- `award_or_idv_flag` - Text
- `awardee_or_recipient_legal` - Text
- `awardee_or_recipient_uniqu` - Text (DUNS number)
- `awarding_agency_code` - Text
- `awarding_agency_name` - Text
- `awarding_office_code` - Text
- `awarding_office_name` - Text
- `awarding_sub_tier_agency_c` - Text
- `awarding_sub_tier_agency_n` - Text
- `base_and_all_options_value` - Text
- `base_exercised_options_val` - Text
- `business_categories` - Text array
- `cage_code` - Text
- `clinger_cohen_act_pla_desc` - Text
- `clinger_cohen_act_planning` - Text
- `commercial_item_acqui_desc` - Text
- `commercial_item_acquisitio` - Text
- `commercial_item_test_desc` - Text
- `commercial_item_test_progr` - Text
- `consolidated_contract` - Text
- `consolidated_contract_desc` - Text
- `construction_wage_rat_desc` - Text
- `construction_wage_rate_req` - Text
- `contingency_humanitar_desc` - Text
- `contingency_humanitarian_o` - Text
- `contract_award_type` - Text
- `contract_award_type_desc` - Text
- `contract_bundling` - Text
- `contract_bundling_descrip` - Text
- `contract_financing` - Text
- `contract_financing_descrip` - Text
- `contracting_officers_desc` - Text
- `contracting_officers_deter` - Text
- `cost_accounting_stand_desc` - Text
- `cost_accounting_standards` - Text
- `cost_or_pricing_data` - Text
- `cost_or_pricing_data_desc` - Text
- `country_of_product_or_desc` - Text
- `country_of_product_or_serv` - Text
- `created_at` - Timestamp without time zone
- `current_total_value_award` - Text
- `division_name` - Text
- `division_number_or_office` - Text
- `dod_claimant_prog_cod_desc` - Text
- `dod_claimant_program_code` - Text
- `domestic_or_foreign_e_desc` - Text
- `domestic_or_foreign_entity` - Text
- `epa_designated_produc_desc` - Text
- `epa_designated_product` - Text
- `evaluated_preference` - Text
- `evaluated_preference_desc` - Text
- `extent_compete_description` - Text
- `extent_competed` - Text
- `fair_opportunity_limi_desc` - Text
- `fair_opportunity_limited_s` - Text
- `fed_biz_opps` - Text
- `fed_biz_opps_description` - Text
- `federal_action_obligation` - Numeric
- `foreign_funding` - Text
- `foreign_funding_desc` - Text
- `funding_agency_code` - Text
- `funding_agency_name` - Text
- `funding_office_code` - Text
- `funding_office_name` - Text
- `funding_sub_tier_agency_co` - Text
- `funding_sub_tier_agency_na` - Text
- `government_furnished_desc` - Text
- `government_furnished_prope` - Text
- `high_comp_officer1_amount` - Text
- `high_comp_officer1_full_na` - Text
- `high_comp_officer2_amount` - Text
- `high_comp_officer2_full_na` - Text
- `high_comp_officer3_amount` - Text
- `high_comp_officer3_full_na` - Text
- `high_comp_officer4_amount` - Text
- `high_comp_officer4_full_na` - Text
- `high_comp_officer5_amount` - Text
- `high_comp_officer5_full_na` - Text
- `idv_type` - Text
- `idv_type_description` - Text
- `information_technolog_desc` - Text
- `information_technology_com` - Text
- `inherently_government_desc` - Text
- `inherently_government_func` - Text
- `initial_report_date` - Text
- `interagency_contract_desc` - Text
- `interagency_contracting_au` - Text
- `labor_standards` - Text
- `labor_standards_descrip` - Text
- `last_modified` - Text
- `legal_entity_address_line1` - Text
- `legal_entity_address_line2` - Text
- `legal_entity_address_line3` - Text
- `legal_entity_city_name` - Text
- `legal_entity_congressional` - Text
- `legal_entity_country_code` - Text
- `legal_entity_country_name` - Text
- `legal_entity_county_code` - Text
- `legal_entity_county_name` - Text
- `legal_entity_state_code` - Text
- `legal_entity_state_descrip` - Text
- `legal_entity_zip4` - Text
- `legal_entity_zip5` - Text
- `legal_entity_zip_last4` - Text
- `local_area_set_aside` - Text
- `local_area_set_aside_desc` - Text
- `major_program` - Text
- `materials_supplies_article` - Text
- `materials_supplies_descrip` - Text
- `multi_year_contract` - Text
- `multi_year_contract_desc` - Text
- `multiple_or_single_aw_desc` - Text
- `multiple_or_single_award_i` - Text
- `naics` - Text
- `naics_description` - Text
- `national_interest_action` - Text
- `national_interest_desc` - Text
- `number_of_actions` - Text
- `number_of_employees` - Text
- `number_of_offers_received` - Text
- `ordering_period_end_date` - Text
- `organizational_type` - Text
- `other_statutory_authority` - Text
- `other_than_full_and_o_desc` - Text
- `other_than_full_and_open_c` - Text
- `parent_award_id` - Text
- `performance_based_se_desc` - Text
- `performance_based_service` - Text
- `period_of_perf_potential_e` - Text
- `period_of_performance_curr` - Text
- `period_of_performance_star` - Text
- `piid` - Text
- `place_of_manufacture` - Text
- `place_of_manufacture_desc` - Text
- `place_of_perf_country_desc` - Text
- `place_of_perfor_state_desc` - Text
- `place_of_perform_city_name` - Text
- `place_of_perform_country_c` - Text
- `place_of_perform_country_n` - Text
- `place_of_perform_county_co` - Text
- `place_of_perform_county_na` - Text
- `place_of_perform_state_nam` - Text
- `place_of_perform_zip_last4` - Text
- `place_of_performance_congr` - Text
- `place_of_performance_locat` - Text
- `place_of_performance_state` - Text
- `place_of_performance_zip4a` - Text
- `place_of_performance_zip5` - Text
- `potential_total_value_awar` - Text
- `price_evaluation_adjustmen` - Text
- `product_or_service_co_desc` - Text
- `product_or_service_code` - Text
- `program_acronym` - Text
- `program_system_or_equ_desc` - Text
- `program_system_or_equipmen` - Text
- `pulled_from` - Text
- `purchase_card_as_paym_desc` - Text
- `purchase_card_as_payment_m` - Text
- `recovered_materials_s_desc` - Text
- `recovered_materials_sustai` - Text
- `referenced_idv_agency_desc` - Text
- `referenced_idv_agency_iden` - Text
- `referenced_idv_agency_name` - Text
- `referenced_idv_modificatio` - Text
- `referenced_idv_type` - Text
- `referenced_idv_type_desc` - Text
- `referenced_mult_or_si_desc` - Text
- `referenced_mult_or_single` - Text
- `research` - Text
- `research_description` - Text
- `sam_exception` - Text
- `sam_exception_description` - Text
- `sea_transportation` - Text
- `sea_transportation_desc` - Text
- `solicitation_date` - Text
- `solicitation_identifier` - Text
- `solicitation_procedur_desc` - Text
- `solicitation_procedures` - Text
- `subcontracting_plan` - Text
- `subcontracting_plan_desc` - Text
- `total_obligated_amount` - Text
- `transaction_number` - Text
- `type_of_contract_pric_desc` - Text
- `type_of_contract_pricing` - Text
- `type_of_idc` - Text
- `type_of_idc_description` - Text
- `type_set_aside` - Text
- `type_set_aside_description` - Text
- `ultimate_parent_legal_enti` - Text
- `ultimate_parent_unique_ide` - Text
- `undefinitized_action` - Text
- `undefinitized_action_desc` - Text
- `unique_award_key` - Text
- `updated_at` - Timestamp without time zone
- `vendor_alternate_name` - Text
- `vendor_alternate_site_code` - Text
- `vendor_doing_as_business_n` - Text
- `vendor_enabled` - Text
- `vendor_fax_number` - Text
- `vendor_legal_org_name` - Text
- `vendor_location_disabled_f` - Text
- `vendor_phone_number` - Text
- `vendor_site_code` - Text
- `awardee_or_recipient_uei` - Text
- `ultimate_parent_uei` - Text
- `small_business_competitive` - Boolean
- `city_local_government` - Boolean
- `county_local_government` - Boolean
- `inter_municipal_local_gove` - Boolean
- `local_government_owned` - Boolean
- `municipality_local_governm` - Boolean
- `school_district_local_gove` - Boolean
- `township_local_government` - Boolean
- `us_state_government` - Boolean
- `us_federal_government` - Boolean
- `federal_agency` - Boolean
- `federally_funded_research` - Boolean
- `us_tribal_government` - Boolean
- `foreign_government` - Boolean
- `community_developed_corpor` - Boolean
- `labor_surplus_area_firm` - Boolean
- `corporate_entity_not_tax_e` - Boolean
- `corporate_entity_tax_exemp` - Boolean
- `partnership_or_limited_lia` - Boolean
- `sole_proprietorship` - Boolean
- `small_agricultural_coopera` - Boolean
- `international_organization` - Boolean
- `us_government_entity` - Boolean
- `emerging_small_business` - Boolean
- `c8a_program_participant` - Boolean
- `sba_certified_8_a_joint_ve` - Boolean
- `dot_certified_disadvantage` - Boolean
- `self_certified_small_disad` - Boolean
- `historically_underutilized` - Boolean
- `small_disadvantaged_busine` - Boolean
- `the_ability_one_program` - Boolean
- `historically_black_college` - Boolean
- `c1862_land_grant_college` - Boolean
- `c1890_land_grant_college` - Boolean
- `c1994_land_grant_college` - Boolean
- `minority_institution` - Boolean
- `private_university_or_coll` - Boolean
- `school_of_forestry` - Boolean
- `state_controlled_instituti` - Boolean
- `tribal_college` - Boolean
- `veterinary_college` - Boolean
- `educational_institution` - Boolean
- `alaskan_native_servicing_i` - Boolean
- `community_development_corp` - Boolean
- `native_hawaiian_servicing` - Boolean
- `domestic_shelter` - Boolean
- `manufacturer_of_goods` - Boolean
- `hospital_flag` - Boolean
- `veterinary_hospital` - Boolean
- `hispanic_servicing_institu` - Boolean
- `foundation` - Boolean
- `woman_owned_business` - Boolean
- `minority_owned_business` - Boolean
- `women_owned_small_business` - Boolean
- `economically_disadvantaged` - Boolean
- `joint_venture_women_owned` - Boolean
- `joint_venture_economically` - Boolean
- `veteran_owned_business` - Boolean
- `service_disabled_veteran_o` - Boolean
- `contracts` - Boolean
- `grants` - Boolean
- `receives_contracts_and_gra` - Boolean
- `airport_authority` - Boolean
- `council_of_governments` - Boolean
- `housing_authorities_public` - Boolean
- `interstate_entity` - Boolean
- `planning_commission` - Boolean
- `port_authority` - Boolean
- `transit_authority` - Boolean
- `subchapter_s_corporation` - Boolean
- `limited_liability_corporat` - Boolean
- `foreign_owned_and_located` - Boolean
- `american_indian_owned_busi` - Boolean
- `alaskan_native_owned_corpo` - Boolean
- `indian_tribe_federally_rec` - Boolean
- `native_hawaiian_owned_busi` - Boolean
- `tribally_owned_business` - Boolean
- `asian_pacific_american_own` - Boolean
- `black_american_owned_busin` - Boolean
- `hispanic_american_owned_bu` - Boolean
- `native_american_owned_busi` - Boolean
- `subcontinent_asian_asian_i` - Boolean
- `other_minority_owned_busin` - Boolean
- `for_profit_organization` - Boolean
- `nonprofit_organization` - Boolean
- `other_not_for_profit_organ` - Boolean
- `us_local_government` - Boolean
- `entity_data_source` - Text

**Indexes**:

- Primary key on `detached_award_procurement_id`
- Unique constraint on `detached_award_proc_unique`
- Index on `created_at`
- Index on `updated_at`
- Index on `awardee_or_recipient_uniqu` (DUNS)
- Index on `ultimate_parent_unique_ide` (Parent DUNS)
- Index on `ultimate_parent_uei` (Parent UEI)
- Index on `awardee_or_recipient_uei` (UEI)

**Transformation notes**:

- Data in this table is raw and unmodified
- May contain duplicates and inconsistent formatting
- Original field names are preserved

#### `source_assistance_transaction`

This table contains the raw financial assistance (grants, loans, etc.) data as downloaded from USAspending.gov.

**Key fields for capture managers by category:**

1. **Assistance Identification**

   - `fain` - Federal Award Identification Number
   - `uri` - Uniform Resource Identifier
   - `afa_generated_unique` - Unique identifier for the assistance award
   - `unique_award_key` - USAspending unique award key

2. **Assistance Details**

   - `award_description` - Description of the assistance award
   - `action_type` - Type of action
   - `action_type_description` - Description of action type
   - `assistance_type` - Type of assistance
   - `assistance_type_desc` - Description of assistance type
   - `record_type` - Record type
   - `record_type_description` - Description of record type

3. **Financial Information**

   - `federal_action_obligation` - Federal obligation amount
   - `non_federal_funding_amount` - Non-federal funding amount
   - `face_value_loan_guarantee` - Face value of loan guarantee
   - `original_loan_subsidy_cost` - Original loan subsidy cost
   - `total_funding_amount` - Total funding amount

4. **Program Information**

   - `assistance_listing_number` - CFDA number
   - `assistance_listing_title` - CFDA program title
   - `funding_opportunity_number` - Funding opportunity number
   - `funding_opportunity_goals` - Funding opportunity goals
   - `sai_number` - State Application Identifier number

5. **Timing Information**

   - `action_date` - Date of the action
   - `period_of_performance_star` - Start date of performance
   - `period_of_performance_curr` - Current end date of performance
   - `initial_report_date` - Initial report date

6. **Agency Information**

   - `awarding_agency_code` - Code of awarding agency
   - `awarding_agency_name` - Name of awarding agency
   - `funding_agency_code` - Code of funding agency
   - `funding_agency_name` - Name of funding agency
   - `awarding_sub_tier_agency_c` - Code of awarding sub-tier agency
   - `awarding_sub_tier_agency_n` - Name of awarding sub-tier agency
   - `awarding_office_code` - Code of awarding office
   - `awarding_office_name` - Name of awarding office
   - `funding_office_name` - Name of funding office

7. **Recipient Information**

   - `awardee_or_recipient_legal` - Legal name of recipient
   - `awardee_or_recipient_uniqu` - DUNS number
   - `uei` - Unique Entity Identifier (UEI)
   - `business_types` - Business types
   - `business_types_desc` - Description of business types
   - `business_categories` - Array of business categories
   - `ultimate_parent_legal_enti` - Ultimate parent organization name
   - `ultimate_parent_unique_ide` - Parent DUNS number
   - `ultimate_parent_uei` - Parent UEI

8. **Place of Performance**
   - `place_of_performance_city` - City of performance
   - `place_of_perfor_state_desc` - State of performance description
   - `place_of_perform_country_n` - Country of performance
   - `place_of_performance_zip5` - ZIP code of performance
   - `place_of_performance_congr` - Congressional district of performance
   - `place_of_perform_country_c` - Country code of performance

**All columns:**

- `published_fabs_id` - Integer, primary key, not null
- `afa_generated_unique` - Text, not null, unique constraint
- `action_date` - Text
- `action_type` - Text
- `action_type_description` - Text
- `assistance_type` - Text
- `assistance_type_desc` - Text
- `award_description` - Text
- `award_modification_amendme` - Text
- `awardee_or_recipient_legal` - Text
- `awardee_or_recipient_uniqu` - Text (DUNS number)
- `awarding_agency_code` - Text
- `awarding_agency_name` - Text
- `awarding_office_code` - Text
- `awarding_office_name` - Text
- `awarding_sub_tier_agency_c` - Text
- `awarding_sub_tier_agency_n` - Text
- `business_categories` - Text array
- `business_funds_ind_desc` - Text
- `business_funds_indicator` - Text
- `business_types` - Text
- `business_types_desc` - Text
- `assistance_listing_number` - Text (CFDA number)
- `assistance_listing_title` - Text (CFDA program title)
- `correction_delete_ind_desc` - Text
- `correction_delete_indicatr` - Text
- `created_at` - Timestamp without time zone
- `face_value_loan_guarantee` - Numeric
- `fain` - Text (Federal Award Identification Number)
- `federal_action_obligation` - Numeric
- `fiscal_year_and_quarter_co` - Text
- `funding_agency_code` - Text
- `funding_agency_name` - Text
- `funding_office_code` - Text
- `funding_office_name` - Text
- `funding_sub_tier_agency_co` - Text
- `funding_sub_tier_agency_na` - Text
- `high_comp_officer1_amount` - Text
- `high_comp_officer1_full_na` - Text
- `high_comp_officer2_amount` - Text
- `high_comp_officer2_full_na` - Text
- `high_comp_officer3_amount` - Text
- `high_comp_officer3_full_na` - Text
- `high_comp_officer4_amount` - Text
- `high_comp_officer4_full_na` - Text
- `high_comp_officer5_amount` - Text
- `high_comp_officer5_full_na` - Text
- `is_active` - Boolean, not null, default false
- `is_historical` - Boolean
- `legal_entity_address_line1` - Text
- `legal_entity_address_line2` - Text
- `legal_entity_address_line3` - Text
- `legal_entity_city_code` - Text
- `legal_entity_city_name` - Text
- `legal_entity_congressional` - Text
- `legal_entity_country_code` - Text
- `legal_entity_country_name` - Text
- `legal_entity_county_code` - Text
- `legal_entity_county_name` - Text
- `legal_entity_foreign_city` - Text
- `legal_entity_foreign_descr` - Text
- `legal_entity_foreign_posta` - Text
- `legal_entity_foreign_provi` - Text
- `legal_entity_state_code` - Text
- `legal_entity_state_name` - Text
- `legal_entity_zip5` - Text
- `legal_entity_zip_last4` - Text
- `modified_at` - Timestamp without time zone
- `non_federal_funding_amount` - Numeric
- `original_loan_subsidy_cost` - Numeric
- `period_of_performance_curr` - Text
- `period_of_performance_star` - Text
- `place_of_perfor_state_code` - Text
- `place_of_perform_country_c` - Text
- `place_of_perform_country_n` - Text
- `place_of_perform_county_co` - Text
- `place_of_perform_county_na` - Text
- `place_of_perform_state_nam` - Text
- `place_of_perform_zip_last4` - Text
- `place_of_performance_city` - Text
- `place_of_performance_code` - Text
- `place_of_performance_congr` - Text
- `place_of_performance_forei` - Text
- `place_of_performance_zip4a` - Text
- `place_of_performance_zip5` - Text
- `place_of_performance_scope` - Text
- `record_type` - Integer
- `record_type_description` - Text
- `sai_number` - Text
- `submission_id` - Numeric
- `total_funding_amount` - Text
- `ultimate_parent_legal_enti` - Text
- `ultimate_parent_unique_ide` - Text (Parent DUNS number)
- `unique_award_key` - Text
- `updated_at` - Timestamp without time zone
- `uri` - Text (Uniform Resource Identifier)
- `uei` - Text (Unique Entity Identifier)
- `ultimate_parent_uei` - Text (Parent UEI)
- `funding_opportunity_goals` - Text
- `funding_opportunity_number` - Text
- `indirect_federal_sharing` - Numeric

**Indexes**:

- Primary key on `published_fabs_id`
- Unique constraint on `afa_generated_unique`
- Unique constraint on upper(`afa_generated_unique`)
- Index on `created_at`
- Index on `updated_at`
- Index on `fain`
- Index on `uri`
- Index on `unique_award_key`
- Index on `awardee_or_recipient_uniqu` (DUNS)
- Index on `ultimate_parent_unique_ide` (Parent DUNS)
- Index on `ultimate_parent_uei` (Parent UEI)
- Index on `uei` (UEI)

**Transformation notes**:

- Data in this table is raw and unmodified
- Contains all original fields from the FABS source data
- Field names match the USAspending.gov data dictionary

### `int` Schema

#### `duns`

This table contains normalized recipient DUNS numbers and associated information.

**Key fields for capture managers by category:**

1. **Identification**

   - `awardee_or_recipient_uniqu` - DUNS number
   - `uei` - Unique Entity Identifier
   - `broker_duns_id` - Primary key identifier

2. **Organization Information**

   - `legal_business_name` - Official business name
   - `dba_name` - "Doing Business As" name
   - `entity_structure` - Legal entity structure

3. **Parent Organization**

   - `ultimate_parent_unique_ide` - Parent DUNS number
   - `ultimate_parent_legal_enti` - Parent legal business name
   - `ultimate_parent_uei` - Parent UEI

4. **Location Information**

   - `address_line_1` - Primary address
   - `address_line_2` - Additional address information
   - `city` - City
   - `state` - State code
   - `zip` - ZIP code
   - `zip4` - ZIP+4 code
   - `country_code` - Country code
   - `congressional_district` - Congressional district

5. **Business Classification**
   - `business_types_codes` - Array of business type codes

**All columns:**

- `awardee_or_recipient_uniqu` - Text (DUNS number)
- `legal_business_name` - Text
- `ultimate_parent_unique_ide` - Text (Parent DUNS)
- `ultimate_parent_legal_enti` - Text
- `broker_duns_id` - Text, primary key, not null
- `update_date` - Date, not null
- `address_line_1` - Text
- `address_line_2` - Text
- `city` - Text
- `congressional_district` - Text
- `country_code` - Text
- `state` - Text
- `zip` - Text
- `zip4` - Text
- `business_types_codes` - Text array
- `dba_name` - Text ("Doing Business As" name)
- `entity_structure` - Text
- `uei` - Text (Unique Entity Identifier)
- `ultimate_parent_uei` - Text (Parent UEI)

**Indexes:**

- Primary key on `broker_duns_id`
- Unique constraint on `broker_duns_id`
- Unique partial index on `awardee_or_recipient_uniqu` where not null
- Unique partial index on `uei` where not null
- Index on `broker_duns_id` with text pattern operations

**Transformation notes:**

- Data has been cleaned and standardized from raw sources
- Duplicate DUNS entries have been consolidated
- Address information has been normalized
- UEI values have been linked to DUNS where available
- Business type codes have been converted to array format for easier querying

#### `transaction_delta`

This table tracks changes in transaction data for incremental updates.

**Key fields for capture managers:**

- `transaction_id` - Identifies transactions that have changed
- `created_at` - Timestamp when change was detected

**All columns:**

- `transaction_id` - Bigint, not null, primary key
- `created_at` - Timestamp with time zone, not null

**Indexes:**

- Primary key on `transaction_id`

**Transformation notes:**

- Created during differential loading processes
- Used to track changes between data loads
- Enables incremental updates rather than full reloads
- Stores only transaction IDs that have changed since last update
- Used to optimize ETL performance by processing only delta changes

### `rpt` Schema

#### `award_search`

This denormalized table combines award, transaction, and recipient data for efficient searching and reporting.

**Key fields for capture managers by category:**

1. **Contract Identification**

   - `generated_unique_award_id` - Unique identifier for the award
   - `display_award_id` - Human-readable award ID
   - `piid` - Procurement Instrument Identifier (contract number)
   - `parent_award_piid` - Parent contract number for task/delivery orders
   - `award_id` - Internal database identifier
   - `fain` - Federal Award Identification Number (for assistance)
   - `uri` - Uniform Resource Identifier (for assistance)

2. **Financial Information**

   - `total_obligation` - Total amount obligated to date
   - `base_and_all_options_value` - Total potential contract value including options
   - `base_exercised_options_val` - Current exercised contract value
   - `non_federal_funding_amount` - Non-federal funding amount
   - `total_funding_amount` - Total funding amount
   - `total_outlays` - Total outlays
   - `generated_pragmatic_obligation` - Calculated obligation value

3. **Contract Timeline**

   - `action_date` - Date of the most recent action
   - `fiscal_year` - Fiscal year of the action
   - `period_of_performance_start_date` - Start date of performance
   - `period_of_performance_current_end_date` - Current end date
   - `ordering_period_end_date` - End date of ordering period
   - `date_signed` - Date contract was signed
   - `last_modified_date` - Date of last modification
   - `certified_date` - Date award was certified

4. **Agency Information**

   - `awarding_agency_id` - ID of the awarding agency
   - `funding_agency_id` - ID of the funding agency
   - `awarding_toptier_agency_name` - Top-level awarding agency (department)
   - `awarding_toptier_agency_code` - Top-level awarding agency code
   - `awarding_subtier_agency_name` - Sub-tier awarding agency (bureau)
   - `awarding_subtier_agency_code` - Sub-tier awarding agency code
   - `funding_toptier_agency_name` - Top-level funding agency
   - `funding_toptier_agency_code` - Top-level funding agency code
   - `funding_subtier_agency_name` - Sub-tier funding agency
   - `funding_subtier_agency_code` - Sub-tier funding agency code
   - `fpds_agency_id` - FPDS agency identifier
   - `fpds_parent_agency_id` - FPDS parent agency identifier

5. **Contractor/Recipient Information**

   - `recipient_name` - Name of the contractor/recipient
   - `recipient_unique_id` - DUNS number
   - `uei` - Unique Entity Identifier
   - `recipient_hash` - Hash identifier for recipient
   - `parent_recipient_unique_id` - Parent DUNS
   - `parent_uei` - Parent UEI
   - `parent_recipient_name` - Name of parent organization
   - `business_categories` - Array of business category designations
   - `raw_recipient_name` - Unprocessed recipient name

6. **Contract Classification**

   - `type` - Type of award
   - `category` - Award category (contract, grant, loan, direct payment, etc.)
   - `type_description` - Description of award type
   - `type_of_contract_pricing` - Contract pricing type
   - `extent_competed` - Extent of competition
   - `type_set_aside` - Set-aside type
   - `product_or_service_code` - Product or Service Code (PSC)
   - `product_or_service_description` - Description of PSC
   - `naics_code` - NAICS code
   - `naics_description` - NAICS description
   - `cfda_number` - CFDA number (for assistance)
   - `cfda_program_title` - CFDA program title (for assistance)

7. **Place of Performance**

   - `pop_city_name` - City of performance
   - `pop_state_name` - State of performance
   - `pop_country_name` - Country of performance
   - `pop_zip5` - ZIP of performance
   - `pop_congressional_code` - Congressional district of performance
   - `pop_county_name` - County of performance
   - `pop_county_code` - County code of performance

8. **Recipient Location**

   - `recipient_location_city_name` - City of recipient
   - `recipient_location_state_name` - State of recipient
   - `recipient_location_country_name` - Country of recipient
   - `recipient_location_zip5` - ZIP of recipient
   - `recipient_location_congressional_code` - Congressional district of recipient
   - `recipient_location_county_name` - County of recipient
   - `recipient_location_county_code` - County code of recipient

9. **Executive Compensation**

   - `officer_1_name` - Name of highest compensated executive
   - `officer_1_amount` - Compensation amount for highest executive
   - `officer_2_name` - Name of second highest compensated executive
   - `officer_2_amount` - Compensation amount for second highest executive
   - `officer_3_name` - Name of third highest compensated executive
   - `officer_3_amount` - Compensation amount for third highest executive
   - `officer_4_name` - Name of fourth highest compensated executive
   - `officer_4_amount` - Compensation amount for fourth highest executive
   - `officer_5_name` - Name of fifth highest compensated executive
   - `officer_5_amount` - Compensation amount for fifth highest executive

10. **Funding Information**
    - `tas_paths` - Treasury Account Symbol paths
    - `tas_components` - TAS component identifiers
    - `federal_accounts` - Federal account data in JSON format
    - `disaster_emergency_fund_codes` - DEFC codes for emergency funding
    - `covid_spending_by_defc` - COVID-19 spending by DEFC code
    - `total_covid_obligation` - Total COVID-19 obligations
    - `iija_spending_by_defc` - Infrastructure Investment and Jobs Act spending
    - `total_iija_obligation` - Total IIJA obligations

**All columns:**

- `award_id` - Integer, primary key
- `generated_unique_award_id` - Text, unique identifier
- `display_award_id` - Text
- `type` - Text (award type)
- `category` - Text (award category)
- `type_description` - Text
- `piid` - Text (Procurement Instrument Identifier)
- `fain` - Text (Federal Award Identification Number)
- `uri` - Text (Uniform Resource Identifier)
- `total_obligation` - Numeric(23,2)
- `total_subsidy_cost` - Numeric(23,2)
- `total_loan_value` - Numeric(23,2)
- `update_date` - Timestamp with time zone
- `recipient_hash` - UUID
- `recipient_name` - Text
- `recipient_unique_id` - Text (DUNS)
- `uei` - Text (Unique Entity Identifier)
- `parent_recipient_unique_id` - Text (parent DUNS)
- `parent_uei` - Text (parent UEI)
- `business_categories` - Text array
- `action_date` - Date
- `fiscal_year` - Integer
- `last_modified_date` - Date
- `period_of_performance_start_date` - Date
- `period_of_performance_current_end_date` - Date
- `date_signed` - Date
- `ordering_period_end_date` - Date
- `original_loan_subsidy_cost` - Numeric(23,2)
- `face_value_loan_guarantee` - Numeric(23,2)
- `awarding_agency_id` - Integer
- `funding_agency_id` - Integer
- `funding_toptier_agency_id` - Integer
- `funding_subtier_agency_id` - Integer
- `awarding_toptier_agency_name` - Text
- `funding_toptier_agency_name` - Text
- `awarding_subtier_agency_name` - Text
- `funding_subtier_agency_name` - Text
- `awarding_toptier_agency_code` - Text
- `funding_toptier_agency_code` - Text
- `awarding_subtier_agency_code` - Text
- `funding_subtier_agency_code` - Text
- `recipient_location_country_code` - Text
- `recipient_location_country_name` - Text
- `recipient_location_state_code` - Text
- `recipient_location_county_code` - Text
- `recipient_location_county_name` - Text
- `recipient_location_zip5` - Text
- `recipient_location_congressional_code` - Text
- `recipient_location_city_name` - Text
- `recipient_location_state_name` - Text
- `recipient_location_state_fips` - Text
- `recipient_location_state_population` - Integer
- `recipient_location_county_population` - Integer
- `recipient_location_congressional_population` - Integer
- `pop_country_code` - Text (place of performance)
- `pop_country_name` - Text
- `pop_state_code` - Text
- `pop_county_code` - Text
- `pop_county_name` - Text
- `pop_city_code` - Text
- `pop_zip5` - Text
- `pop_congressional_code` - Text
- `pop_city_name` - Text
- `pop_state_name` - Text
- `pop_state_fips` - Text
- `pop_state_population` - Integer
- `pop_county_population` - Integer
- `pop_congressional_population` - Integer
- `cfda_program_title` - Text
- `cfda_number` - Text
- `cfdas` - Text array
- `sai_number` - Text
- `type_of_contract_pricing` - Text
- `extent_competed` - Text
- `type_set_aside` - Text
- `product_or_service_code` - Text
- `product_or_service_description` - Text
- `naics_code` - Text
- `naics_description` - Text
- `tas_paths` - Text array (Treasury Account Symbol)
- `tas_components` - Text array
- `disaster_emergency_fund_codes` - Text array
- `covid_spending_by_defc` - JSONB
- `total_covid_outlay` - Numeric(23,2)
- `total_covid_obligation` - Numeric(23,2)
- `base_and_all_options_value` - Numeric(23,2)
- `base_exercised_options_val` - Numeric(23,2)
- `certified_date` - Date
- `create_date` - Timestamp with time zone
- `fpds_agency_id` - Text
- `fpds_parent_agency_id` - Text
- `is_fpds` - Boolean, not null
- `non_federal_funding_amount` - Numeric(23,2)
- `officer_1_amount` - Numeric(23,2)
- `officer_1_name` - Text
- `officer_2_amount` - Numeric(23,2)
- `officer_2_name` - Text
- `officer_3_amount` - Numeric(23,2)
- `officer_3_name` - Text
- `officer_4_amount` - Numeric(23,2)
- `officer_4_name` - Text
- `officer_5_amount` - Numeric(23,2)
- `officer_5_name` - Text
- `parent_award_piid` - Text
- `raw_recipient_name` - Text
- `subaward_count` - Integer
- `total_funding_amount` - Numeric(23,2)
- `total_indirect_federal_sharing` - Numeric(23,2)
- `total_subaward_amount` - Numeric(23,2)
- `transaction_unique_id` - Text
- `awarding_subtier_agency_code_raw` - Text
- `awarding_subtier_agency_name_raw` - Text
- `awarding_toptier_agency_code_raw` - Text
- `awarding_toptier_agency_name_raw` - Text
- `funding_subtier_agency_code_raw` - Text
- `funding_subtier_agency_name_raw` - Text
- `funding_toptier_agency_code_raw` - Text
- `funding_toptier_agency_name_raw` - Text
- `data_source` - Text
- `earliest_transaction_id` - Bigint
- `latest_transaction_id` - Bigint
- `earliest_transaction_search_id` - Bigint
- `latest_transaction_search_id` - Bigint
- `iija_spending_by_defc` - JSONB
- `total_iija_obligation` - Numeric(23,2)
- `total_iija_outlay` - Numeric(23,2)
- `pop_congressional_code_current` - Text
- `recipient_location_congressional_code_current` - Text
- `total_outlays` - Numeric(23,2)
- `pop_county_fips` - Text
- `recipient_location_county_fips` - Text
- `type_description_raw` - Text
- `type_raw` - Text
- `parent_recipient_name` - Text
- `generated_pragmatic_obligation` - Numeric(23,2)
- `federal_accounts` - JSONB
- `program_activities` - JSONB

**Key Indexes:**

- Unique index on `award_id`
- Unique index on `generated_unique_award_id`
- Index on `action_date` (post 2007-10-01)
- Index on `action_date` (pre 2008-10-01)
- Index on upper(`fain`)
- Index on `funding_agency_id` (post 2007-10-01)
- Index on upper(`parent_award_piid`)
- Index on upper(`piid`)
- Index on `recipient_location_congressional_code` (post 2007-10-01)
- Index on `recipient_location_county_code` (post 2007-10-01)
- Index on `recipient_hash` (post 2007-10-01)
- Index on `recipient_location_state_code` (post 2007-10-01)
- Index on `recipient_unique_id` (post 2007-10-01, not null)
- Index on `update_date` (descending)
- Index on upper(`uri`)
- Index on `period_of_performance_current_end_date`
- Index on `category`
- Index on `total_obligation`
- Index on `total_outlays`

**Transformation notes:**

- Consolidated from multiple source tables for easy searching
- Monetary values converted to consistent numeric format
- Dates standardized and converted to proper date types
- Location data enriched with names and demographic info
- Agency hierarchy information included for better filtering
- Business categories derived from individual boolean flags

#### `transaction_search_fpds`

This denormalized table contains procurement (contract) transaction data optimized for searching.

**Key fields for capture managers by category:**

1. **Transaction Identification**

   - `transaction_id` - Unique identifier for the transaction
   - `award_id` - Associated award identifier
   - `modification_number` - Contract modification number
   - `detached_award_proc_unique` - Unique identifier for procurement actions
   - `transaction_unique_id` - Unique transaction identifier
   - `usaspending_unique_transaction_id` - USAspending unique transaction ID

2. **Contract Information**

   - `piid` - Procurement Instrument Identifier
   - `parent_award_id` - Parent award ID
   - `transaction_description` - Description of transaction
   - `award_category` - Category of award
   - `type` - Type of transaction
   - `type_description` - Description of type

3. **Financial Information**

   - `federal_action_obligation` - Federal obligation for transaction
   - `award_amount` - Total award amount
   - `base_and_all_options_value` - Base and all options value
   - `base_exercised_options_val` - Base exercised options value
   - `generated_pragmatic_obligation` - Calculated obligation amount
   - `current_total_value_award` - Current total value of award
   - `potential_total_value_awar` - Potential total value of award
   - `total_obligated_amount` - Total amount obligated

4. **Contract Timeline**

   - `action_date` - Date of the transaction
   - `fiscal_action_date` - Fiscal date of action
   - `fiscal_year` - Fiscal year of transaction
   - `award_date_signed` - Date contract was signed
   - `period_of_performance_start_date` - Start of performance period
   - `period_of_performance_current_end_date` - Current end date
   - `ordering_period_end_date` - End date for ordering
   - `last_modified_date` - Date of last modification
   - `initial_report_date` - Initial report date

5. **Procurement Classification**

   - `naics_code` - NAICS code
   - `naics_description` - NAICS description
   - `product_or_service_code` - PSC
   - `product_or_service_description` - PSC description
   - `type_of_contract_pricing` - Contract pricing type
   - `type_of_contract_pric_desc` - Contract pricing description
   - `contract_award_type` - Contract award type
   - `contract_award_type_desc` - Contract award type description

6. **Competition Information**

   - `extent_competed` - Extent of competition
   - `extent_compete_description` - Competition description
   - `solicitation_procedures` - Solicitation procedures
   - `solicitation_procedur_desc` - Solicitation procedures description
   - `type_set_aside` - Set-aside type
   - `type_set_aside_description` - Set-aside description
   - `fair_opportunity_limited_s` - Fair opportunity limited sources
   - `fair_opportunity_limi_desc` - Fair opportunity description
   - `number_of_offers_received` - Number of bids received
   - `other_than_full_and_open_c` - Other than full and open competition
   - `other_than_full_and_o_desc` - OTFOC description

7. **Agency Information**

   - `awarding_agency_id` - Awarding agency ID
   - `funding_agency_id` - Funding agency ID
   - `awarding_toptier_agency_name` - Top-tier awarding agency
   - `awarding_toptier_agency_abbreviation` - Top-tier agency abbreviation
   - `funding_toptier_agency_name` - Top-tier funding agency
   - `funding_toptier_agency_abbreviation` - Top-tier funding agency abbreviation
   - `awarding_subtier_agency_name` - Sub-tier awarding agency
   - `awarding_subtier_agency_abbreviation` - Sub-tier agency abbreviation
   - `funding_subtier_agency_name` - Sub-tier funding agency
   - `funding_subtier_agency_abbreviation` - Sub-tier funding agency abbreviation
   - `awarding_office_name` - Awarding office name
   - `awarding_office_code` - Awarding office code
   - `funding_office_name` - Funding office name
   - `funding_office_code` - Funding office code

8. **Contractor Information**

   - `recipient_hash` - Hash identifier for recipient
   - `recipient_name` - Name of contractor
   - `recipient_unique_id` - DUNS number
   - `recipient_uei` - Unique Entity Identifier
   - `parent_recipient_hash` - Hash for parent recipient
   - `parent_recipient_name` - Name of parent company
   - `parent_recipient_unique_id` - Parent DUNS
   - `parent_uei` - Parent UEI
   - `cage_code` - CAGE code
   - `vendor_doing_as_business_n` - Doing business as name
   - `vendor_phone_number` - Vendor phone number
   - `vendor_fax_number` - Vendor fax number

9. **Place of Performance**

   - `pop_city_name` - City of performance
   - `pop_state_name` - State of performance
   - `pop_country_name` - Country of performance
   - `pop_zip5` - ZIP code of performance
   - `pop_congressional_code` - Congressional district of performance
   - `pop_county_name` - County of performance
   - `pop_county_code` - County code of performance

10. **Specialized Contract Requirements**
    - `clinger_cohen_act_planning` - Clinger-Cohen Act planning
    - `construction_wage_rate_req` - Construction wage rate requirements
    - `consolidated_contract` - Consolidated contract flag
    - `contingency_humanitarian_o` - Contingency humanitarian operation
    - `contract_bundling` - Contract bundling
    - `contract_financing` - Contract financing
    - `cost_accounting_standards` - Cost accounting standards
    - `cost_or_pricing_data` - Cost or pricing data
    - `multi_year_contract` - Multi-year contract flag
    - `performance_based_service` - Performance based service acquisition
    - `research` - Research flag
    - `small_business_competitive` - Small business competitiveness
    - `subcontracting_plan` - Subcontracting plan

**All columns:**

- `transaction_id` - Bigint - Unique identifier for the transaction
- `award_id` - Bigint - Identifier for the associated award
- `modification_number` - Text - Contract modification number
- `detached_award_proc_unique` - Text - Unique identifier for the procurement
- `afa_generated_unique` - Text - Unique identifier for assistance awards
- `generated_unique_award_id` - Text - System-generated unique identifier
- `fain` - Text - Federal Award Identification Number
- `uri` - Text - Uniform Resource Identifier
- `piid` - Text - Procurement Instrument Identifier
- `action_date` - Date - Date the action was taken
- `fiscal_action_date` - Date - Fiscal date of the action
- `last_modified_date` - Date - Date of last modification
- `fiscal_year` - Integer - Fiscal year of the transaction
- `award_certified_date` - Date - Date award was certified
- `award_fiscal_year` - Integer - Fiscal year of the award
- `update_date` - Timestamp with time zone - Date of last update
- `award_update_date` - Timestamp with time zone - Date award was updated
- `etl_update_date` - Timestamp with time zone - Date ETL process updated
- `period_of_performance_start_date` - Date - Start of performance period
- `period_of_performance_current_end_date` - Date - Current end date of performance
- `type` - Text - Type of transaction
- `type_description` - Text - Description of transaction type
- `award_category` - Text - Category of award
- `transaction_description` - Text - Description of transaction
- `award_amount` - Numeric - Total award amount
- `generated_pragmatic_obligation` - Numeric - Calculated obligation amount
- `federal_action_obligation` - Numeric - Federal obligation amount
- `original_loan_subsidy_cost` - Numeric - Original subsidy cost for loans
- `face_value_loan_guarantee` - Numeric - Face value of loan or guarantee
- `business_categories` - Array - Business categories of recipient
- `naics_code` - Text - North American Industry Classification System code
- `naics_description` - Text - Description of NAICS code
- `product_or_service_code` - Text - Product or Service Code
- `product_or_service_description` - Text - Description of PSC
- `type_of_contract_pricing` - Text - Contract pricing type
- `type_set_aside` - Text - Set-aside type
- `extent_competed` - Text - Extent of competition
- `ordering_period_end_date` - Text - End date of ordering period
- `cfda_number` - Text - Catalog of Federal Domestic Assistance number
- `cfda_title` - Text - CFDA program title
- `cfda_id` - Integer - CFDA identifier
- `pop_country_name` - Text - Place of performance country name
- `pop_country_code` - Text - Place of performance country code
- `pop_state_name` - Text - Place of performance state name
- `pop_state_code` - Text - Place of performance state code
- `pop_county_code` - Text - Place of performance county code
- `pop_county_name` - Text - Place of performance county name
- `pop_zip5` - Text - Place of performance ZIP code
- `pop_congressional_code` - Text - Place of performance congressional district
- `pop_congressional_population` - Integer - Population of congressional district
- `pop_county_population` - Integer - Population of county
- `pop_state_fips` - Text - Place of performance state FIPS code
- `pop_state_population` - Integer - Population of state
- `pop_city_name` - Text - Place of performance city name
- `recipient_location_country_code` - Text - Recipient location country code
- `recipient_location_country_name` - Text - Recipient location country name
- `recipient_location_state_name` - Text - Recipient location state name
- `recipient_location_state_code` - Text - Recipient location state code
- `recipient_location_state_fips` - Text - Recipient location state FIPS code
- `recipient_location_state_population` - Integer - Population of recipient state
- `recipient_location_county_code` - Text - Recipient location county code
- `recipient_location_county_name` - Text - Recipient location county name
- `recipient_location_county_population` - Integer - Population of recipient county
- `recipient_location_congressional_code` - Text - Recipient congressional district
- `recipient_location_congressional_population` - Integer - Population of district
- `recipient_location_zip5` - Text - Recipient location ZIP code
- `recipient_location_city_name` - Text - Recipient location city name
- `recipient_hash` - UUID - Hash identifier for recipient
- `recipient_levels` - Array - Levels of recipient (parent, child)
- `recipient_name` - Text - Name of recipient
- `recipient_unique_id` - Text - DUNS number
- `parent_recipient_hash` - UUID - Hash for parent recipient
- `parent_recipient_name` - Text - Name of parent recipient
- `parent_recipient_unique_id` - Text - Parent DUNS
- `awarding_toptier_agency_id` - Integer - ID of top-tier awarding agency
- `funding_toptier_agency_id` - Integer - ID of top-tier funding agency
- `awarding_agency_id` - Integer - ID of awarding agency
- `funding_agency_id` - Integer - ID of funding agency
- `awarding_toptier_agency_name` - Text - Name of top-tier awarding agency
- `funding_toptier_agency_name` - Text - Name of top-tier funding agency
- `awarding_subtier_agency_name` - Text - Name of sub-tier awarding agency
- `funding_subtier_agency_name` - Text - Name of sub-tier funding agency
- `awarding_toptier_agency_abbreviation` - Text - Abbreviation of top-tier awarding agency
- `funding_toptier_agency_abbreviation` - Text - Abbreviation of top-tier funding agency
- `awarding_subtier_agency_abbreviation` - Text - Abbreviation of sub-tier awarding agency
- `funding_subtier_agency_abbreviation` - Text - Abbreviation of sub-tier funding agency
- `treasury_account_identifiers` - Array - Treasury account identifiers
- `tas_paths` - Array - Treasury Account Symbol paths
- `tas_components` - Array - TAS component identifiers
- `federal_accounts` - JSONB - Federal account data
- `disaster_emergency_fund_codes` - Array - DEFC codes for emergency funding
- `awarding_office_code` - Text - Code of awarding office
- `awarding_office_name` - Text - Name of awarding office
- `funding_office_code` - Text - Code of funding office
- `funding_office_name` - Text - Name of funding office
- `award_date_signed` - Date - Date award was signed
- `recipient_uei` - Text - Unique Entity Identifier
- `parent_uei` - Text - Parent Unique Entity Identifier
- `a_76_fair_act_action` - Text - A-76 Fair Act action
- `a_76_fair_act_action_desc` - Text - A-76 Fair Act action description
- `action_type` - Text - Type of action
- `action_type_description` - Text - Description of action type
- `agency_id` - Text - Agency identifier
- `airport_authority` - Boolean - Airport authority flag
- `alaskan_native_owned_corpo` - Boolean - Alaskan Native owned corporation
- `alaskan_native_servicing_i` - Boolean - Alaskan Native servicing institution
- `american_indian_owned_busi` - Boolean - American Indian owned business
- `asian_pacific_american_own` - Boolean - Asian Pacific American owned
- `awarding_agency_code` - Text - Code of awarding agency
- `awarding_sub_tier_agency_c` - Text - Code of awarding sub-tier agency
- `base_and_all_options_value` - Text - Base and all options value
- `base_exercised_options_val` - Text - Base exercised options value
- `black_american_owned_busin` - Boolean - Black American owned business
- `business_funds_ind_desc` - Text - Business funds indicator description
- `business_funds_indicator` - Text - Business funds indicator
- `business_types` - Text - Business types
- `business_types_desc` - Text - Business types description
- `c1862_land_grant_college` - Boolean - 1862 Land Grant College
- `c1890_land_grant_college` - Boolean - 1890 Land Grant College
- `c1994_land_grant_college` - Boolean - 1994 Land Grant College
- `c8a_program_participant` - Boolean - 8(a) Program participant
- `cage_code` - Text - Commercial and Government Entity code
- `city_local_government` - Boolean - City local government
- `clinger_cohen_act_pla_desc` - Text - Clinger-Cohen Act planning description
- `clinger_cohen_act_planning` - Text - Clinger-Cohen Act planning
- `commercial_item_acqui_desc` - Text - Commercial item acquisition description
- `commercial_item_acquisitio` - Text - Commercial item acquisition
- `commercial_item_test_desc` - Text - Commercial item test description
- `commercial_item_test_progr` - Text - Commercial item test program
- `community_developed_corpor` - Boolean - Community developed corporation
- `community_development_corp` - Boolean - Community development corporation
- `consolidated_contract` - Text - Consolidated contract
- `consolidated_contract_desc` - Text - Consolidated contract description
- `construction_wage_rat_desc` - Text - Construction wage rate description
- `construction_wage_rate_req` - Text - Construction wage rate requirements
- `contingency_humanitar_desc` - Text - Contingency humanitarian description
- `contingency_humanitarian_o` - Text - Contingency humanitarian operation
- `contract_award_type` - Text - Contract award type
- `contract_award_type_desc` - Text - Contract award type description
- `contract_bundling` - Text - Contract bundling
- `contract_bundling_descrip` - Text - Contract bundling description
- `contract_financing` - Text - Contract financing
- `contract_financing_descrip` - Text - Contract financing description
- `contracting_officers_desc` - Text - Contracting officers description
- `contracting_officers_deter` - Text - Contracting officers determination
- `contracts` - Boolean - Contracts flag
- `corporate_entity_not_tax_e` - Boolean - Corporate entity not tax exempt
- `corporate_entity_tax_exemp` - Boolean - Corporate entity tax exempt
- `correction_delete_ind_desc` - Text - Correction delete indicator description
- `correction_delete_indicatr` - Text - Correction delete indicator
- `cost_accounting_stand_desc` - Text - Cost accounting standards description
- `cost_accounting_standards` - Text - Cost accounting standards
- `cost_or_pricing_data` - Text - Cost or pricing data
- `cost_or_pricing_data_desc` - Text - Cost or pricing data description
- `council_of_governments` - Boolean - Council of governments
- `country_of_product_or_desc` - Text - Country of product origin description
- `country_of_product_or_serv` - Text - Country of product or service origin
- `county_local_government` - Boolean - County local government
- `create_date` - Timestamp with time zone - Creation date
- `current_total_value_award` - Text - Current total value of award
- `dod_claimant_prog_cod_desc` - Text - DoD claimant program code description
- `dod_claimant_program_code` - Text - DoD claimant program code
- `domestic_or_foreign_e_desc` - Text - Domestic or foreign entity description
- `domestic_or_foreign_entity` - Text - Domestic or foreign entity
- `domestic_shelter` - Boolean - Domestic shelter
- `dot_certified_disadvantage` - Boolean - DOT certified disadvantaged
- `economically_disadvantaged` - Boolean - Economically disadvantaged
- `educational_institution` - Boolean - Educational institution
- `emerging_small_business` - Boolean - Emerging small business
- `epa_designated_produc_desc` - Text - EPA designated product description
- `epa_designated_product` - Text - EPA designated product
- `evaluated_preference` - Text - Evaluated preference
- `evaluated_preference_desc` - Text - Evaluated preference description
- `extent_compete_description` - Text - Extent competed description
- `fair_opportunity_limi_desc` - Text - Fair opportunity limited description
- `fair_opportunity_limited_s` - Text - Fair opportunity limited sources
- `fed_biz_opps` - Text - Federal business opportunities
- `fed_biz_opps_description` - Text - Federal business opportunities description
- `federal_agency` - Boolean - Federal agency
- `federally_funded_research` - Boolean - Federally funded research
- `for_profit_organization` - Boolean - For profit organization
- `foreign_funding` - Text - Foreign funding
- `foreign_funding_desc` - Text - Foreign funding description
- `foreign_government` - Boolean - Foreign government
- `foreign_owned_and_located` - Boolean - Foreign owned and located
- `foundation` - Boolean - Foundation
- `funding_agency_code` - Text - Code of funding agency
- `funding_amount` - Numeric - Funding amount
- `funding_sub_tier_agency_co` - Text - Code of funding sub-tier agency
- `government_furnished_desc` - Text - Government furnished description
- `government_furnished_prope` - Text - Government furnished property
- `grants` - Boolean - Grants flag
- `hispanic_american_owned_bu` - Boolean - Hispanic American owned business
- `hispanic_servicing_institu` - Boolean - Hispanic servicing institution
- `historically_black_college` - Boolean - Historically black college or university
- `historically_underutilized` - Boolean - Historically underutilized business zone
- `hospital_flag` - Boolean - Hospital flag
- `housing_authorities_public` - Boolean - Housing authorities public
- `idv_type` - Text - Indefinite delivery vehicle type
- `idv_type_description` - Text - IDV type description
- `indian_tribe_federally_rec` - Boolean - Indian tribe federally recognized
- `information_technolog_desc` - Text - Information technology description
- `information_technology_com` - Text - Information technology commercial item
- `inherently_government_desc` - Text - Inherently governmental description
- `inherently_government_func` - Text - Inherently governmental function
- `inter_municipal_local_gove` - Boolean - Inter-municipal local government
- `interagency_contract_desc` - Text - Interagency contract description
- `interagency_contracting_au` - Text - Interagency contracting authority
- `international_organization` - Boolean - International organization
- `interstate_entity` - Boolean - Interstate entity
- `is_fpds` - Boolean - Is Federal Procurement Data System (required)
- `joint_venture_economically` - Boolean - Joint venture economically disadvantaged
- `joint_venture_women_owned` - Boolean - Joint venture women owned
- `labor_standards` - Text - Labor standards
- `labor_standards_descrip` - Text - Labor standards description
- `labor_surplus_area_firm` - Boolean - Labor surplus area firm
- `legal_entity_address_line1` - Text - Legal entity address line 1
- `legal_entity_address_line2` - Text - Legal entity address line 2
- `legal_entity_address_line3` - Text - Legal entity address line 3
- `legal_entity_city_code` - Text - Legal entity city code
- `legal_entity_foreign_city` - Text - Legal entity foreign city
- `legal_entity_foreign_descr` - Text - Legal entity foreign description
- `legal_entity_foreign_posta` - Text - Legal entity foreign postal code
- `legal_entity_foreign_provi` - Text - Legal entity foreign province
- `legal_entity_zip4` - Text - Legal entity ZIP+4
- `legal_entity_zip_last4` - Text - Legal entity ZIP last 4 digits
- `limited_liability_corporat` - Boolean - Limited liability corporation
- `local_area_set_aside` - Text - Local area set aside
- `local_area_set_aside_desc` - Text - Local area set aside description
- `local_government_owned` - Boolean - Local government owned
- `major_program` - Text - Major program
- `manufacturer_of_goods` - Boolean - Manufacturer of goods
- `materials_supplies_article` - Text - Materials supplies articles
- `materials_supplies_descrip` - Text - Materials supplies description
- `minority_institution` - Boolean - Minority institution
- `minority_owned_business` - Boolean - Minority owned business
- `multi_year_contract` - Text - Multi year contract
- `multi_year_contract_desc` - Text - Multi year contract description
- `multiple_or_single_aw_desc` - Text - Multiple or single award description
- `multiple_or_single_award_i` - Text - Multiple or single award IDV
- `municipality_local_governm` - Boolean - Municipality local government
- `national_interest_action` - Text - National interest action
- `national_interest_desc` - Text - National interest description
- `native_american_owned_busi` - Boolean - Native American owned business
- `native_hawaiian_owned_busi` - Boolean - Native Hawaiian owned business
- `native_hawaiian_servicing` - Boolean - Native Hawaiian servicing institution
- `non_federal_funding_amount` - Numeric - Non-federal funding amount
- `nonprofit_organization` - Boolean - Nonprofit organization
- `number_of_actions` - Text - Number of actions
- `number_of_offers_received` - Text - Number of offers received
- `officer_1_amount` - Numeric - Compensation amount for officer 1
- `officer_1_name` - Text - Name of officer 1
- `officer_2_amount` - Numeric - Compensation amount for officer 2
- `officer_2_name` - Text - Name of officer 2
- `officer_3_amount` - Numeric - Compensation amount for officer 3
- `officer_3_name` - Text - Name of officer 3
- `officer_4_amount` - Numeric - Compensation amount for officer 4
- `officer_4_name` - Text - Name of officer 4
- `officer_5_amount` - Numeric - Compensation amount for officer 5
- `officer_5_name` - Text - Name of officer 5
- `organizational_type` - Text - Organizational type
- `other_minority_owned_busin` - Boolean - Other minority owned business
- `other_not_for_profit_organ` - Boolean - Other not for profit organization
- `other_statutory_authority` - Text - Other statutory authority
- `other_than_full_and_o_desc` - Text - Other than full and open competition description
- `other_than_full_and_open_c` - Text - Other than full and open competition
- `parent_award_id` - Text - Parent award ID
- `parent_recipient_name_raw` - Text - Raw parent recipient name
- `partnership_or_limited_lia` - Boolean - Partnership or limited liability partnership
- `performance_based_se_desc` - Text - Performance based service description
- `performance_based_service` - Text - Performance based service acquisition
- `period_of_perf_potential_e` - Text - Period of performance potential end date
- `place_of_manufacture` - Text - Place of manufacture
- `place_of_manufacture_desc` - Text - Place of manufacture description
- `place_of_perform_zip_last4` - Text - Place of performance ZIP last 4
- `place_of_performance_code` - Text - Place of performance code
- `place_of_performance_forei` - Text - Place of performance foreign location
- `place_of_performance_scope` - Text - Place of performance scope
- `place_of_performance_zip4a` - Text - Place of performance ZIP4A
- `planning_commission` - Boolean - Planning commission
- `port_authority` - Boolean - Port authority
- `potential_total_value_awar` - Text - Potential total value of award
- `price_evaluation_adjustmen` - Text - Price evaluation adjustment
- `private_university_or_coll` - Boolean - Private university or college
- `program_acronym` - Text - Program acronym
- `program_system_or_equ_desc` - Text - Program system or equipment description
- `program_system_or_equipmen` - Text - Program system or equipment
- `pulled_from` - Text - Source system
- `purchase_card_as_paym_desc` - Text - Purchase card as payment description
- `purchase_card_as_payment_m` - Text - Purchase card as payment method
- `receives_contracts_and_gra` - Boolean - Receives contracts and grants
- `recipient_name_raw` - Text - Raw recipient name
- `record_type` - Integer - Record type
- `record_type_description` - Text - Record type description
- `recovered_materials_s_desc` - Text - Recovered materials sustainability description
- `recovered_materials_sustai` - Text - Recovered materials sustainability
- `referenced_idv_agency_desc` - Text - Referenced IDV agency description
- `referenced_idv_agency_iden` - Text - Referenced IDV agency identifier
- `referenced_idv_modificatio` - Text - Referenced IDV modification
- `referenced_idv_type` - Text - Referenced IDV type
- `referenced_idv_type_desc` - Text - Referenced IDV type description
- `referenced_mult_or_si_desc` - Text - Referenced multiple or single award description
- `referenced_mult_or_single` - Text - Referenced multiple or single award
- `research` - Text - Research flag
- `research_description` - Text - Research description
- `sai_number` - Text - State Application Identifier number
- `sam_exception` - Text - System for Award Management exception
- `sam_exception_description` - Text - SAM exception description
- `sba_certified_8_a_joint_ve` - Boolean - SBA certified 8(a) joint venture
- `school_district_local_gove` - Boolean - School district local government
- `school_of_forestry` - Boolean - School of forestry
- `sea_transportation` - Text - Sea transportation
- `sea_transportation_desc` - Text - Sea transportation description
- `self_certified_small_disad` - Boolean - Self-certified small disadvantaged business
- `service_disabled_veteran_o` - Boolean - Service disabled veteran owned business
- `small_agricultural_coopera` - Boolean - Small agricultural cooperative
- `small_business_competitive` - Boolean - Small business competitiveness demonstration
- `small_disadvantaged_busine` - Boolean - Small disadvantaged business
- `sole_proprietorship` - Boolean - Sole proprietorship
- `solicitation_date` - Date - Solicitation date
- `solicitation_identifier` - Text - Solicitation identifier
- `solicitation_procedur_desc` - Text - Solicitation procedures description
- `solicitation_procedures` - Text - Solicitation procedures
- `state_controlled_instituti` - Boolean - State controlled institution of higher learning
- `subchapter_s_corporation` - Boolean - Subchapter S corporation
- `subcontinent_asian_asian_i` - Boolean - Subcontinent Asian Asian Indian American owned
- `subcontracting_plan` - Text - Subcontracting plan
- `subcontracting_plan_desc` - Text - Subcontracting plan description
- `the_ability_one_program` - Boolean - AbilityOne program
- `total_funding_amount` - Numeric - Total funding amount
- `total_obligated_amount` - Text - Total obligated amount
- `township_local_government` - Boolean - Township local government
- `transaction_number` - Text - Transaction number
- `transaction_unique_id` - Text (required) - Unique transaction identifier
- `transit_authority` - Boolean - Transit authority
- `tribal_college` - Boolean - Tribal college
- `tribally_owned_business` - Boolean - Tribally owned business
- `type_of_contract_pric_desc` - Text - Type of contract pricing description
- `type_of_idc` - Text - Type of indefinite delivery contract
- `type_of_idc_description` - Text - Type of IDC description
- `type_set_aside_description` - Text - Type set aside description
- `undefinitized_action` - Text - Undefinitized action
- `undefinitized_action_desc` - Text - Undefinitized action description
- `us_federal_government` - Boolean - US federal government
- `us_government_entity` - Boolean - US government entity
- `us_local_government` - Boolean - US local government
- `us_state_government` - Boolean - US state government
- `us_tribal_government` - Boolean - US tribal government
- `usaspending_unique_transaction_id` - Text - USAspending unique transaction ID
- `vendor_doing_as_business_n` - Text - Vendor doing business as name
- `vendor_fax_number` - Text - Vendor fax number
- `vendor_phone_number` - Text - Vendor phone number
- `veteran_owned_business` - Boolean - Veteran owned business
- `veterinary_college` - Boolean - Veterinary college
- `veterinary_hospital` - Boolean - Veterinary hospital
- `woman_owned_business` - Boolean - Woman owned business
- `women_owned_small_business` - Boolean - Women owned small business
- `awarding_subtier_agency_name_raw` - Text - Raw awarding subtier agency name
- `awarding_toptier_agency_name_raw` - Text - Raw awarding toptier agency name
- `funding_subtier_agency_name_raw` - Text - Raw funding subtier agency name
- `funding_toptier_agency_name_raw` - Text - Raw funding toptier agency name
- `detached_award_procurement_id` - Integer - Detached award procurement ID
- `indirect_federal_sharing` - Numeric - Indirect federal sharing
- `published_fabs_id` - Integer - Published FABS ID
- `funding_opportunity_goals` - Text - Funding opportunity goals
- `funding_opportunity_number` - Text - Funding opportunity number
- `pop_congressional_code_current` - Text - Current place of performance congressional code
- `recipient_location_congressional_code_current` - Text - Current recipient location congressional code
- `pop_county_fips` - Text - Place of performance county FIPS code
- `recipient_location_county_fips` - Text - Recipient location county FIPS code
- `type_description_raw` - Text - Raw type description
- `type_raw` - Text - Raw type
- `initial_report_date` - Date - Initial report date
- `program_activities` - JSONB - Program activities data

**Key Indexes:**

- Index on `transaction_id`
- Index on `award_id`
- Index on `action_date`
- Index on `recipient_hash`
- Index on `awarding_agency_id`
- Index on `funding_agency_id`
- GIN index on `tas_paths`
- GIN index on `business_categories`
- GIN index on `disaster_emergency_fund_codes`
- Partial indexes for performance optimization

**Transformation notes:**

- Derived from `source_procurement_transaction` in the raw schema
- Date fields converted from text to proper date types
- Amount fields converted to numeric where appropriate
- Agency reference keys normalized
- Location data enhanced with demographic information
- Business categories derived from boolean flags
- Hierarchical relationships established (awards, recipients, agencies)
- Added program activity and federal account information
- Optimized for search and reporting performance

#### `transaction_search_fabs`

This denormalized table contains financial assistance transaction data (grants, loans, etc.) optimized for searching.

**Key fields for capture managers by category:**

1. **Transaction Identification**

   - `transaction_id` - Unique identifier for the transaction
   - `award_id` - Associated award identifier
   - `afa_generated_unique` - Generated unique identifier
   - `fain` - Federal Award Identification Number
   - `uri` - Uniform Resource Identifier
   - `transaction_unique_id` - Unique transaction identifier

2. **Assistance Information**

   - `type` - Type of assistance
   - `type_description` - Description of assistance type
   - `transaction_description` - Description of transaction
   - `award_category` - Category of award (grant, loan, etc.)
   - `assistance_type` - Type of assistance code
   - `assistance_type_desc` - Assistance type description
   - `record_type` - Record type code
   - `record_type_description` - Record type description
   - `correction_delete_indicatr` - Correction/deletion indicator
   - `correction_delete_ind_desc` - Correction/deletion description

3. **Financial Information**

   - `federal_action_obligation` - Federal obligation amount
   - `award_amount` - Total award amount
   - `non_federal_funding_amount` - Non-federal funding amount
   - `face_value_loan_guarantee` - Face value of loan guarantee
   - `original_loan_subsidy_cost` - Original loan subsidy cost
   - `total_funding_amount` - Total funding amount
   - `generated_pragmatic_obligation` - Calculated obligation value
   - `indirect_federal_sharing` - Indirect federal sharing amount

4. **Assistance Timeline**

   - `action_date` - Date of the transaction
   - `fiscal_action_date` - Fiscal date of action
   - `fiscal_year` - Fiscal year of transaction
   - `award_date_signed` - Date agreement was signed
   - `period_of_performance_start_date` - Start of performance period
   - `period_of_performance_current_end_date` - Current end date
   - `last_modified_date` - Date of last modification
   - `initial_report_date` - Initial report date

5. **Program Information**

   - `cfda_number` - CFDA number
   - `cfda_title` - CFDA program title
   - `cfda_id` - CFDA identifier
   - `funding_opportunity_number` - Funding opportunity announcement number
   - `funding_opportunity_goals` - Funding opportunity goals
   - `sai_number` - State Application Identifier number
   - `business_funds_indicator` - Business funds indicator
   - `business_funds_ind_desc` - Business funds indicator description

6. **Agency Information**

   - `awarding_agency_id` - Awarding agency ID
   - `funding_agency_id` - Funding agency ID
   - `awarding_toptier_agency_name` - Top-tier awarding agency
   - `awarding_toptier_agency_abbreviation` - Top-tier agency abbreviation
   - `funding_toptier_agency_name` - Top-tier funding agency
   - `funding_toptier_agency_abbreviation` - Top-tier funding agency abbreviation
   - `awarding_subtier_agency_name` - Sub-tier awarding agency
   - `awarding_subtier_agency_abbreviation` - Sub-tier agency abbreviation
   - `funding_subtier_agency_name` - Sub-tier funding agency
   - `funding_subtier_agency_abbreviation` - Sub-tier funding agency abbreviation
   - `awarding_office_name` - Awarding office name
   - `awarding_office_code` - Awarding office code
   - `funding_office_name` - Funding office name
   - `funding_office_code` - Funding office code

7. **Recipient Information**

   - `recipient_hash` - Hash identifier for recipient
   - `recipient_name` - Name of recipient
   - `recipient_unique_id` - DUNS number
   - `recipient_uei` - Unique Entity Identifier
   - `parent_recipient_hash` - Hash for parent recipient
   - `parent_recipient_name` - Name of parent organization
   - `parent_recipient_unique_id` - Parent DUNS
   - `parent_uei` - Parent UEI
   - `business_types` - Business types code
   - `business_types_desc` - Business types description
   - `business_categories` - Array of business categories

8. **Place of Performance**

   - `pop_city_name` - City of performance
   - `pop_state_name` - State of performance
   - `pop_country_name` - Country of performance
   - `pop_zip5` - ZIP code of performance
   - `pop_congressional_code` - Congressional district of performance
   - `pop_county_name` - County of performance
   - `pop_county_code` - County code of performance
   - `place_of_performance_scope` - Scope of performance

9. **Recipient Location**

   - `recipient_location_city_name` - City of recipient
   - `recipient_location_state_name` - State of recipient
   - `recipient_location_country_name` - Country of recipient
   - `recipient_location_zip5` - ZIP code of recipient
   - `recipient_location_congressional_code` - Congressional district of recipient
   - `recipient_location_county_name` - County of recipient
   - `recipient_location_county_code` - County code of recipient
   - `legal_entity_address_line1` - Address line 1 of recipient
   - `legal_entity_address_line2` - Address line 2 of recipient
   - `legal_entity_foreign_city` - Foreign city of recipient
   - `legal_entity_foreign_posta` - Foreign postal code of recipient

10. **Executive Compensation**
    - `officer_1_name` - Name of highest compensated executive
    - `officer_1_amount` - Compensation amount for highest executive
    - `officer_2_name` - Name of second highest compensated executive
    - `officer_2_amount` - Compensation amount for second highest executive
    - `officer_3_name` - Name of third highest compensated executive
    - `officer_3_amount` - Compensation amount for third highest executive
    - `officer_4_name` - Name of fourth highest compensated executive
    - `officer_4_amount` - Compensation amount for fourth highest executive
    - `officer_5_name` - Name of fifth highest compensated executive
    - `officer_5_amount` - Compensation amount for fifth highest executive

**All columns:**

- `transaction_id` - Bigint - Unique identifier for the transaction
- `award_id` - Bigint - Identifier for the associated award
- `modification_number` - Text - Modification number
- `detached_award_proc_unique` - Text - Unique identifier for procurement records
- `afa_generated_unique` - Text - Unique identifier for assistance awards
- `generated_unique_award_id` - Text - System-generated unique identifier
- `fain` - Text - Federal Award Identification Number
- `uri` - Text - Uniform Resource Identifier
- `piid` - Text - Procurement Instrument Identifier
- `action_date` - Date - Date the action was taken
- `fiscal_action_date` - Date - Fiscal date of the action
- `last_modified_date` - Date - Date of last modification
- `fiscal_year` - Integer - Fiscal year of the transaction
- `award_certified_date` - Date - Date award was certified
- `award_fiscal_year` - Integer - Fiscal year of the award
- `update_date` - Timestamp with time zone - Date of last update
- `award_update_date` - Timestamp with time zone - Date award was updated
- `etl_update_date` - Timestamp with time zone - Date ETL process updated
- `period_of_performance_start_date` - Date - Start of performance period
- `period_of_performance_current_end_date` - Date - Current end date of performance
- `type` - Text - Type of transaction
- `type_description` - Text - Description of transaction type
- `award_category` - Text - Category of award
- `transaction_description` - Text - Description of transaction
- `award_amount` - Numeric - Total award amount
- `generated_pragmatic_obligation` - Numeric - Calculated obligation amount
- `federal_action_obligation` - Numeric - Federal obligation amount
- `original_loan_subsidy_cost` - Numeric - Original subsidy cost for loans
- `face_value_loan_guarantee` - Numeric - Face value of loan or guarantee
- `business_categories` - Array - Business categories of recipient
- `naics_code` - Text - North American Industry Classification System code
- `naics_description` - Text - Description of NAICS code
- `product_or_service_code` - Text - Product or Service Code
- `product_or_service_description` - Text - Description of PSC
- `type_of_contract_pricing` - Text - Contract pricing type
- `type_set_aside` - Text - Set-aside type
- `extent_competed` - Text - Extent of competition
- `ordering_period_end_date` - Text - End date of ordering period
- `cfda_number` - Text - Catalog of Federal Domestic Assistance number
- `cfda_title` - Text - CFDA program title
- `cfda_id` - Integer - CFDA identifier
- `pop_country_name` - Text - Place of performance country name
- `pop_country_code` - Text - Place of performance country code
- `pop_state_name` - Text - Place of performance state name
- `pop_state_code` - Text - Place of performance state code
- `pop_county_code` - Text - Place of performance county code
- `pop_county_name` - Text - Place of performance county name
- `pop_zip5` - Text - Place of performance ZIP code
- `pop_congressional_code` - Text - Place of performance congressional district
- `pop_congressional_population` - Integer - Population of congressional district
- `pop_county_population` - Integer - Population of county
- `pop_state_fips` - Text - Place of performance state FIPS code
- `pop_state_population` - Integer - Population of state
- `pop_city_name` - Text - Place of performance city name
- `recipient_location_country_code` - Text - Recipient location country code
- `recipient_location_country_name` - Text - Recipient location country name
- `recipient_location_state_name` - Text - Recipient location state name
- `recipient_location_state_code` - Text - Recipient location state code
- `recipient_location_state_fips` - Text - Recipient location state FIPS code
- `recipient_location_state_population` - Integer - Population of recipient state
- `recipient_location_county_code` - Text - Recipient location county code
- `recipient_location_county_name` - Text - Recipient location county name
- `recipient_location_county_population` - Integer - Population of recipient county
- `recipient_location_congressional_code` - Text - Recipient congressional district
- `recipient_location_congressional_population` - Integer - Population of district
- `recipient_location_zip5` - Text - Recipient location ZIP code
- `recipient_location_city_name` - Text - Recipient location city name
- `recipient_hash` - UUID - Hash identifier for recipient
- `recipient_levels` - Array - Levels of recipient (parent, child)
- `recipient_name` - Text - Name of recipient
- `recipient_unique_id` - Text - DUNS number
- `parent_recipient_hash` - UUID - Hash for parent recipient
- `parent_recipient_name` - Text - Name of parent recipient
- `parent_recipient_unique_id` - Text - Parent DUNS
- `awarding_toptier_agency_id` - Integer - ID of top-tier awarding agency
- `funding_toptier_agency_id` - Integer - ID of top-tier funding agency
- `awarding_agency_id` - Integer - ID of awarding agency
- `funding_agency_id` - Integer - ID of funding agency
- `awarding_toptier_agency_name` - Text - Name of top-tier awarding agency
- `funding_toptier_agency_name` - Text - Name of top-tier funding agency
- `awarding_subtier_agency_name` - Text - Name of sub-tier awarding agency
- `funding_subtier_agency_name` - Text - Name of sub-tier funding agency
- `awarding_toptier_agency_abbreviation` - Text - Abbreviation of top-tier awarding agency
- `funding_toptier_agency_abbreviation` - Text - Abbreviation of top-tier funding agency
- `awarding_subtier_agency_abbreviation` - Text - Abbreviation of sub-tier awarding agency
- `funding_subtier_agency_abbreviation` - Text - Abbreviation of sub-tier funding agency
- `treasury_account_identifiers` - Array - Treasury account identifiers
- `tas_paths` - Array - Treasury Account Symbol paths
- `tas_components` - Array - TAS component identifiers
- `federal_accounts` - JSONB - Federal account data
- `disaster_emergency_fund_codes` - Array - DEFC codes for emergency funding
- `awarding_office_code` - Text - Code of awarding office
- `awarding_office_name` - Text - Name of awarding office
- `funding_office_code` - Text - Code of funding office
- `funding_office_name` - Text - Name of funding office
- `award_date_signed` - Date - Date award was signed
- `recipient_uei` - Text - Unique Entity Identifier
- `parent_uei` - Text - Parent Unique Entity Identifier

**Financial assistance specific fields:**

- `business_funds_indicator` - Text - Business funds indicator
- `business_funds_ind_desc` - Text - Business funds indicator description
- `business_types` - Text - Business types code
- `business_types_desc` - Text - Business types description
- `record_type` - Integer - Record type
- `record_type_description` - Text - Description of record type
- `correction_delete_indicatr` - Text - Correction or deletion indicator
- `correction_delete_ind_desc` - Text - Description of correction or deletion
- `funding_opportunity_number` - Text - Funding opportunity announcement number
- `funding_opportunity_goals` - Text - Funding opportunity goals
- `sai_number` - Text - State Application Identifier number
- `indirect_federal_sharing` - Numeric - Indirect federal sharing amount

**Additional organizational entity fields:**

- `airport_authority` - Boolean - Airport authority flag
- `alaskan_native_owned_corpo` - Boolean - Alaskan Native owned corporation
- `alaskan_native_servicing_i` - Boolean - Alaskan Native servicing institution
- `american_indian_owned_busi` - Boolean - American Indian owned business
- `asian_pacific_american_own` - Boolean - Asian Pacific American owned
- `black_american_owned_busin` - Boolean - Black American owned business
- `c1862_land_grant_college` - Boolean - 1862 Land Grant College
- `c1890_land_grant_college` - Boolean - 1890 Land Grant College
- `c1994_land_grant_college` - Boolean - 1994 Land Grant College
- `c8a_program_participant` - Boolean - 8(a) Program participant
- `city_local_government` - Boolean - City local government
- `community_developed_corpor` - Boolean - Community developed corporation
- `community_development_corp` - Boolean - Community development corporation
- `contracts` - Boolean - Contracts flag
- `corporate_entity_not_tax_e` - Boolean - Corporate entity not tax exempt
- `corporate_entity_tax_exemp` - Boolean - Corporate entity tax exempt
- `council_of_governments` - Boolean - Council of governments
- `county_local_government` - Boolean - County local government
- `domestic_shelter` - Boolean - Domestic shelter
- `dot_certified_disadvantage` - Boolean - DOT certified disadvantaged
- `economically_disadvantaged` - Boolean - Economically disadvantaged
- `educational_institution` - Boolean - Educational institution
- `emerging_small_business` - Boolean - Emerging small business
- `federal_agency` - Boolean - Federal agency
- `federally_funded_research` - Boolean - Federally funded research
- `for_profit_organization` - Boolean - For profit organization
- `foreign_government` - Boolean - Foreign government
- `foreign_owned_and_located` - Boolean - Foreign owned and located
- `foundation` - Boolean - Foundation
- `grants` - Boolean - Grants flag
- `hispanic_american_owned_bu` - Boolean - Hispanic American owned business
- `hispanic_servicing_institu` - Boolean - Hispanic servicing institution
- `historically_black_college` - Boolean - Historically black college or university
- `historically_underutilized` - Boolean - Historically underutilized business zone
- `hospital_flag` - Boolean - Hospital flag
- `housing_authorities_public` - Boolean - Housing authorities public
- `indian_tribe_federally_rec` - Boolean - Indian tribe federally recognized
- `inter_municipal_local_gove` - Boolean - Inter-municipal local government
- `international_organization` - Boolean - International organization
- `interstate_entity` - Boolean - Interstate entity
- `joint_venture_economically` - Boolean - Joint venture economically disadvantaged
- `joint_venture_women_owned` - Boolean - Joint venture women owned
- `labor_surplus_area_firm` - Boolean - Labor surplus area firm
- `limited_liability_corporat` - Boolean - Limited liability corporation
- `local_government_owned` - Boolean - Local government owned
- `manufacturer_of_goods` - Boolean - Manufacturer of goods
- `minority_institution` - Boolean - Minority institution
- `minority_owned_business` - Boolean - Minority owned business
- `municipality_local_governm` - Boolean - Municipality local government
- `native_american_owned_busi` - Boolean - Native American owned business
- `native_hawaiian_owned_busi` - Boolean - Native Hawaiian owned business
- `native_hawaiian_servicing` - Boolean - Native Hawaiian servicing institution
- `nonprofit_organization` - Boolean - Nonprofit organization
- `other_minority_owned_busin` - Boolean - Other minority owned business
- `other_not_for_profit_organ` - Boolean - Other not for profit organization
- `partnership_or_limited_lia` - Boolean - Partnership or limited liability partnership
- `planning_commission` - Boolean - Planning commission
- `port_authority` - Boolean - Port authority
- `private_university_or_coll` - Boolean - Private university or college
- `receives_contracts_and_gra` - Boolean - Receives contracts and grants
- `sba_certified_8_a_joint_ve` - Boolean - SBA certified 8(a) joint venture
- `school_district_local_gove` - Boolean - School district local government
- `school_of_forestry` - Boolean - School of forestry
- `self_certified_small_disad` - Boolean - Self-certified small disadvantaged business
- `service_disabled_veteran_o` - Boolean - Service disabled veteran owned business
- `small_agricultural_coopera` - Boolean - Small agricultural cooperative
- `small_business_competitive` - Boolean - Small business competitiveness demonstration
- `small_disadvantaged_busine` - Boolean - Small disadvantaged business
- `sole_proprietorship` - Boolean - Sole proprietorship
- `state_controlled_instituti` - Boolean - State controlled institution of higher learning
- `subchapter_s_corporation` - Boolean - Subchapter S corporation
- `subcontinent_asian_asian_i` - Boolean - Subcontinent Asian Asian Indian American owned
- `the_ability_one_program` - Boolean - AbilityOne program
- `township_local_government` - Boolean - Township local government
- `transit_authority` - Boolean - Transit authority
- `tribal_college` - Boolean - Tribal college
- `tribally_owned_business` - Boolean - Tribally owned business
- `us_federal_government` - Boolean - US federal government
- `us_government_entity` - Boolean - US government entity
- `us_local_government` - Boolean - US local government
- `us_state_government` - Boolean - US state government
- `us_tribal_government` - Boolean - US tribal government
- `veteran_owned_business` - Boolean - Veteran owned business
- `veterinary_college` - Boolean - Veterinary college
- `veterinary_hospital` - Boolean - Veterinary hospital
- `woman_owned_business` - Boolean - Woman owned business
- `women_owned_small_business` - Boolean - Women owned small business

**Place of performance fields:**

- `place_of_perform_zip_last4` - Text - Place of performance ZIP last 4
- `place_of_performance_code` - Text - Place of performance code
- `place_of_performance_forei` - Text - Place of performance foreign location
- `place_of_performance_scope` - Text - Place of performance scope
- `place_of_performance_zip4a` - Text - Place of performance ZIP4A
- `pop_congressional_code_current` - Text - Current place of performance congressional code
- `pop_county_fips` - Text - Place of performance county FIPS code

**Recipient location fields:**

- `legal_entity_address_line1` - Text - Legal entity address line 1
- `legal_entity_address_line2` - Text - Legal entity address line 2
- `legal_entity_address_line3` - Text - Legal entity address line 3
- `legal_entity_city_code` - Text - Legal entity city code
- `legal_entity_foreign_city` - Text - Legal entity foreign city
- `legal_entity_foreign_descr` - Text - Legal entity foreign description
- `legal_entity_foreign_posta` - Text - Legal entity foreign postal code
- `legal_entity_foreign_provi` - Text - Legal entity foreign province
- `legal_entity_zip4` - Text - Legal entity ZIP+4
- `legal_entity_zip_last4` - Text - Legal entity ZIP last 4 digits
- `recipient_location_congressional_code_current` - Text - Current recipient congressional code
- `recipient_location_county_fips` - Text - Recipient location county FIPS code

**System fields:**

- `is_fpds` - Boolean - Is Federal Procurement Data System (required, always false)
- `transaction_unique_id` - Text - Unique transaction identifier (required)
- `published_fabs_id` - Integer - Published FABS ID
- `detached_award_procurement_id` - Integer - Detached award procurement ID
- `usaspending_unique_transaction_id` - Text - USAspending unique transaction ID
- `awarding_subtier_agency_name_raw` - Text - Raw awarding subtier agency name
- `awarding_toptier_agency_name_raw` - Text - Raw awarding toptier agency name
- `funding_subtier_agency_name_raw` - Text - Raw funding subtier agency name
- `funding_toptier_agency_name_raw` - Text - Raw funding toptier agency name
- `create_date` - Timestamp with time zone - Creation date
- `initial_report_date` - Date - Initial report date
- `recipient_name_raw` - Text - Raw recipient name
- `parent_recipient_name_raw` - Text - Raw parent recipient name
- `pulled_from` - Text - Source system
- `type_description_raw` - Text - Raw type description
- `type_raw` - Text - Raw type
- `program_activities` - JSONB - Program activities data

**Key Indexes:**

- Index on `transaction_id`
- Index on `award_id`
- Index on `action_date`
- Index on `cfda_number`
- Index on `recipient_hash`
- Index on `awarding_agency_id`
- Index on `funding_agency_id`
- GIN index on `tas_paths`
- GIN index on `business_categories`
- GIN index on `disaster_emergency_fund_codes`
- Partial indexes for performance optimization

**Transformation notes:**

- Derived from `source_assistance_transaction` in the raw schema
- Date fields converted from text to proper date types
- Amount fields converted to numeric where appropriate
- Agency reference keys normalized
- Location data enhanced with demographic information
- Business categories derived from boolean flags
- Hierarchical relationships established (awards, recipients, agencies)
- Added program activity and federal account information
- Optimized for search and reporting performance

#### `recipient_lookup`

This table provides a normalized view of recipient information for efficient lookup.

**Key fields for capture managers by category:**

1. **Recipient Identification**

   - `recipient_hash` - Hash identifier for recipient lookup
   - `legal_business_name` - Official business name
   - `duns` - DUNS number
   - `uei` - Unique Entity Identifier

2. **Parent Company Information**

   - `parent_duns` - Parent DUNS number
   - `parent_legal_business_name` - Parent company name
   - `parent_uei` - Parent UEI

3. **Address Information**

   - `address_line_1` - Primary address
   - `address_line_2` - Secondary address
   - `city` - City
   - `state` - State code
   - `zip5` - 5-digit ZIP code
   - `zip4` - ZIP+4 code
   - `country_code` - Country code
   - `congressional_district` - Congressional district

4. **Business Information**
   - `business_types_codes` - Business type codes
   - `alternate_names` - Alternative business names
   - `source` - Source system of the data

**All columns:**

- `id` - Bigint, primary key, not null
- `recipient_hash` - UUID - Hash identifier for the recipient
- `legal_business_name` - Text - Name of the business
- `duns` - Text - DUNS number
- `address_line_1` - Text - First line of address
- `address_line_2` - Text - Second line of address
- `business_types_codes` - Array - Business types codes
- `city` - Text - City
- `congressional_district` - Text - Congressional district
- `country_code` - Text - Country code
- `parent_duns` - Text - Parent DUNS number
- `parent_legal_business_name` - Text - Parent business name
- `state` - Text - State code
- `zip4` - Text - ZIP+4 code
- `zip5` - Text - 5-digit ZIP code
- `alternate_names` - Array - Alternative business names
- `source` - Text, not null - Source system of the data
- `update_date` - Timestamp with time zone, not null - Last update date
- `uei` - Text - Unique Entity Identifier
- `parent_uei` - Text - Parent Unique Entity Identifier

**Indexes:**

- Primary key on `id`
- Index on `recipient_hash`
- Index on `duns`
- Index on `uei`
- Index on `parent_duns`
- Index on `parent_uei`
- Index on upper(`legal_business_name`)
- GIN index on `alternate_names`

**Transformation notes:**

- Consolidated recipient information from multiple sources
- Created standardized identifiers
- Established parent-child relationships between entities
- Enabled fast recipient lookups by multiple identifiers
- Maintains alternative names for fuzzy matching

#### `recipient_profile`

This table provides aggregated information about recipients for reporting and analytics.

**Key fields for capture managers by category:**

1. **Recipient Identification**

   - `recipient_hash` - Hash identifier for recipient
   - `recipient_unique_id` - DUNS number
   - `recipient_name` - Name of recipient
   - `uei` - Unique Entity Identifier
   - `recipient_level` - Level of recipient (P=Parent, C=Child, R=Recipient)

2. **Parent Organization**

   - `recipient_affiliations` - Related recipient identifiers
   - `parent_uei` - Parent UEI

3. **Contract Activity**

   - `last_12_months` - Total spending in last 12 months
   - `last_12_contracts` - Contract spending in last 12 months
   - `last_12_months_count` - Count of transactions in last 12 months
   - `award_types` - Types of awards received

4. **Grant Activity**
   - `last_12_grants` - Grant spending in last 12 months
   - `last_12_direct_payments` - Direct payment spending in last 12 months
   - `last_12_loans` - Loan spending in last 12 months
   - `last_12_other` - Other spending in last 12 months

**All columns:**

- `id` - Bigint, not null - Unique identifier
- `recipient_level` - Character varying, not null - Level of the recipient (P = Parent, C = Child, R = Recipient)
- `recipient_hash` - UUID - Hash identifier for the recipient
- `recipient_unique_id` - Text - DUNS number
- `recipient_name` - Text - Name of the recipient
- `recipient_affiliations` - Array, not null - Related recipient identifiers
- `last_12_months` - Numeric, not null - Total spending in last 12 months
- `last_12_contracts` - Numeric, not null - Contract spending in last 12 months
- `last_12_direct_payments` - Numeric, not null - Direct payment spending in last 12 months
- `last_12_grants` - Numeric, not null - Grant spending in last 12 months
- `last_12_loans` - Numeric, not null - Loan spending in last 12 months
- `last_12_months_count` - Integer, not null - Count of transactions in last 12 months
- `last_12_other` - Numeric, not null - Other spending in last 12 months
- `award_types` - Array, not null - Types of awards received
- `uei` - Text - Unique Entity Identifier
- `parent_uei` - Text - Parent Unique Entity Identifier

**Indexes:**

- Primary key on `id`
- Index on `recipient_hash`
- Index on `recipient_unique_id`
- Index on `uei`
- Index on `recipient_name` using gin_trgm_ops (for fuzzy searching)
- Index on `recipient_level`

**Transformation notes:**

- Pre-aggregated metrics for dashboard performance
- Created hierarchical structure for recipient relationships
- Generated summaries by award types
- Rolling 12-month calculations updated periodically
- Separate entries for parent, child, and individual recipient levels
- Enables quick lookups for recipient overview data

#### `parent_award`

This table contains information about parent awards for linking related awards.

**Key fields for capture managers by category:**

1. **Award Identification**

   - `award_id` - Unique identifier for the parent award
   - `generated_unique_award_id` - Generated identifier for the award
   - `parent_award_id` - Identifier for the parent of this award
   - `piid` - Procurement Instrument Identifier
   - `parent_piid` - Parent Procurement Instrument Identifier

2. **Award Information**

   - `type` - Type of award
   - `type_description` - Description of award type
   - `agency_id` - Agency identifier
   - `agency_name` - Agency name
   - `award_amount` - Award amount
   - `obligated_amount` - Obligated amount
   - `multiple_or_single_award_i` - Multiple or single award IDV
   - `idv_type` - Indefinite delivery vehicle type
   - `idv_type_description` - IDV type description

3. **Award Timeline**
   - `action_date` - Date of the action
   - `date_signed` - Date signed
   - `period_of_performance_start_date` - Start of performance period
   - `period_of_performance_current_end_date` - Current end date
   - `ordering_period_end_date` - End date of ordering period

**All columns:**

- `award_id` - Unique identifier for the parent award
- `generated_unique_award_id` - Generated identifier for the award
- `parent_award_id` - Identifier for the parent of this award

**Transformation notes:**

- Creates parent-child relationships between awards
- Establishes hierarchy for IDV contracts and related awards

### `public` Schema

This schema contains reference data, lookup tables, and administrative tables that support the application's functionality.

#### `agency`

This table contains information about federal agencies.

**Key fields for capture managers:**

1. **Agency Identification**
   - `id` - Unique identifier
   - `toptier_agency_id` - Reference to top-tier agency
   - `subtier_agency_id` - Reference to sub-tier agency
   - `toptier_flag` - Flag indicating if this is a top-tier agency record
   - `user_selectable` - Flag for UI filtering

**All columns:**

- `id` - Integer, primary key, not null - Unique identifier for the agency
- `create_date` - Timestamp with time zone, not null - Creation date
- `update_date` - Timestamp with time zone, not null - Last update date
- `toptier_agency_id` - Integer, not null - Foreign key reference to toptier_agency
- `subtier_agency_id` - Integer, not null - Foreign key reference to subtier_agency
- `toptier_flag` - Boolean, not null - Flag indicating if this is a top-tier agency record
- `user_selectable` - Boolean - Flag indicating if users can select this agency in UI filters

**Indexes:**

- Primary key on `id`
- Index on `toptier_agency_id`
- Index on `subtier_agency_id`
- Index on `toptier_flag` where true

**Transformation notes:**

- Establishes agency hierarchy relationships
- Links top-tier (departments) and sub-tier agencies
- Used for agency rollups in reporting

#### `toptier_agency`

This table contains information about top-tier federal agencies (departments).

**Key fields for capture managers:**


1. **Agency Identification**

   - `toptier_agency_id` - Unique identifier
   - `toptier_code` - CGAC code
   - `name` - Name of the agency (e.g., "Department of Defense")
   - `abbreviation` - Abbreviation for the agency (e.g., "DOD")

2. **Agency Information**
   - `mission` - Agency mission statement
   - `about_agency_data` - Information about agency data
   - `website` - Agency website URL
   - `justification` - Justification for existence
   - `congressional_justification_url` - URL for budget justification

**All columns:**

- `toptier_agency_id` - Integer, primary key, not null - Unique identifier
- `create_date` - Timestamp with time zone, not null - Creation date
- `update_date` - Timestamp with time zone, not null - Last update date
- `toptier_code` - Text, not null - CGAC (Common Government-wide Accounting Classification) code
- `name` - Text, not null - Name of the agency (e.g., "Department of Defense")
- `abbreviation` - Text - Abbreviation for the agency (e.g., "DOD")
- `mission` - Text - Agency mission statement
- `about_agency_data` - Text - Information about the agency's data
- `website` - Text - Agency website URL
- `justification` - Text - Justification for existence
- `icon_filename` - Text - Filename for agency icon
- `congressional_justification_url` - Text - URL for congressional budget justification
- `icon_filename_fy22` - Text - FY22 icon filename

**Indexes:**

- Primary key on `toptier_agency_id`
- Unique index on `toptier_code`
- Index on upper(`name`)
- Index on upper(`abbreviation`)

**Transformation notes:**

- Reference data for agency lookups
- Standardized agency names and codes
- Source of truth for top-tier agency information

#### `subtier_agency`

This table contains information about sub-tier federal agencies (bureaus).

**Key fields for capture managers:**


1. **Agency Identification**
   - `subtier_agency_id` - Unique identifier
   - `subtier_code` - Sub-tier agency code
   - `name` - Name of the sub-tier agency
   - `abbreviation` - Abbreviation for the sub-tier agency

**All columns:**

- `subtier_agency_id` - Integer, primary key, not null - Unique identifier
- `create_date` - Timestamp with time zone, not null - Creation date
- `update_date` - Timestamp with time zone, not null - Last update date
- `subtier_code` - Text, not null - Subtier agency code
- `name` - Text, not null - Name of the sub-tier agency
- `abbreviation` - Text - Abbreviation for the sub-tier agency

**Indexes:**

- Primary key on `subtier_agency_id`
- Unique index on `subtier_code`
- Index on upper(`name`)
- Index on upper(`abbreviation`)

**Transformation notes:**

- Reference data for agency lookups
- Standardized sub-tier agency names and codes
- Used for agency hierarchy mapping

#### `references_location`

This table contains geographic location information.

**Key fields for capture managers:**


1. **Location Identification**

   - `location_id` - Unique identifier for the location
   - `country_code` - ISO country code
   - `country_name` - Name of country
   - `state_code` - State or province code
   - `state_name` - State or province name
   - `county_code` - County code
   - `county_name` - County name
   - `city_name` - City name
   - `zip5` - 5-digit ZIP code

2. **Congressional Information**

   - `congressional_code` - Congressional district code
   - `congressional_code_current` - Current congressional district code
   - `congressional_population` - Congressional district population

3. **Demographics**
   - `state_population` - State population
   - `county_population` - County population

**All columns:**

- `location_id` - Integer, primary key, not null - Unique identifier
- `create_date` - Timestamp with time zone, not null - Creation date
- `update_date` - Timestamp with time zone, not null - Last update date
- `country_name` - Text - Name of country
- `country_code` - Text - ISO country code
- `state_code` - Text - State or province code
- `state_name` - Text - State or province name
- `state_fips` - Text - FIPS code for state
- `county_code` - Text - County code
- `county_name` - Text - County name
- `county_fips` - Text - County FIPS code
- `city_name` - Text - City name
- `city_code` - Text - City code
- `zip5` - Text - 5-digit ZIP code
- `zip4` - Text - ZIP+4 code
- `zip_last4` - Text - Last 4 digits of ZIP
- `congressional_code` - Text - Congressional district code
- `congressional_code_current` - Text - Current congressional district code (post-redistricting)
- `performance_code` - Text - Location performance code
- `location_country_code` - Text - Country code for location
- `location_country_name` - Text - Country name for location
- `foreign_city_name` - Text - Foreign city name
- `foreign_province` - Text - Foreign province name
- `foreign_postal_code` - Text - Foreign postal code
- `address_line1` - Text - First line of address
- `address_line2` - Text - Second line of address
- `address_line3` - Text - Third line of address
- `place_of_performance_scope` - Text - Scope of place of performance
- `foreign_location_description` - Text - Description of foreign location
- `state_population` - Integer - State population
- `county_population` - Integer - County population
- `congressional_population` - Integer - Congressional district population

**Indexes:**

- Primary key on `location_id`
- Indexes on location components (country_code, state_code, county_code, city_code, zip5)
- Index on congressional_code
- Indexes on population fields

**Transformation notes:**

- Combined information from multiple geographic sources
- Added population data from Census
- Standardized location codes and names
- Added support for congressional redistricting

#### `references_cfda`

This table contains information about CFDA (Catalog of Federal Domestic Assistance) programs.

**Key fields for capture managers:**


1. **Program Identification**

   - `program_number` - CFDA program number
   - `program_title` - Title of the CFDA program
   - `popular_name` - Popular name for the CFDA program

2. **Program Information**

   - `federal_agency` - Federal agency responsible for the program
   - `authorization` - Legal authorization for the program
   - `objectives` - Objectives of the program
   - `beneficiary_types` - Types of beneficiaries
   - `types_of_assistance` - Types of assistance provided
   - `uses_and_use_restrictions` - Uses and use restrictions

3. **Eligibility Information**
   - `applicant_eligibility` - Eligibility requirements for applicants
   - `credit_agency` - Indicates if it's a credit agency program
   - `loan_guarantee` - Indicates if program includes loan guarantees
   - `insurance` - Indicates if program includes insurance

**All columns:**

- `id` - Integer, primary key, not null - Unique identifier
- `create_date` - Timestamp with time zone, not null - Creation date
- `update_date` - Timestamp with time zone, not null - Last update date
- `program_number` - Text, not null - CFDA program number
- `program_title` - Text, not null - Title of the CFDA program
- `popular_name` - Text - Popular name for the CFDA program
- `federal_agency` - Text - Federal agency responsible for the program
- `authorization` - Text - Legal authorization for the program
- `objectives` - Text - Objectives of the program
- `beneficiary_types` - Text - Types of beneficiaries
- `types_of_assistance` - Text - Types of assistance provided
- `uses_and_use_restrictions` - Text - Uses and use restrictions
- `applicant_eligibility` - Text - Eligibility requirements for applicants
- `credit_agency` - Boolean - Indicates if it's a credit agency program
- `loan_guarantee` - Boolean - Indicates if program includes loan guarantees
- `insurance` - Boolean - Indicates if program includes insurance
- `archived_date` - Date - Date when program was archived

**Indexes:**

- Primary key on `id`
- Unique index on `program_number`
- Index on upper(`program_title`)
- Index on upper(`popular_name`)

**Transformation notes:**

- Reference data with minimal transformations
- Source of truth for CFDA information
- Updated periodically from Assistance Listings (formerly CFDA)

#### `naics`

This table contains information about NAICS (North American Industry Classification System) codes.

**Key fields for capture managers:**


1. **Code Information**
   - `code` - NAICS code
   - `description` - Description of the NAICS code
   - `year` - Year of the NAICS code version

**All columns:**

- `code` - Text, primary key, not null - NAICS code
- `description` - Text, not null - Description of the NAICS code
- `year` - Integer - Year of the NAICS code version

**Indexes:**

- Primary key on `code`
- Index on upper(`description`)
- Index on `year`

**Transformation notes:**

- Reference data with minimal transformations
- Source of truth for NAICS information
- Includes different NAICS code versions (2012, 2017, 2022)

#### `psc` (Product or Service Codes)

This table contains information about PSC (Product or Service Code) codes.

**Key fields for capture managers:**


1. **Code Information**

   - `code` - PSC code
   - `description` - Description of the PSC code
   - `full_name` - Full name of the product or service
   - `service_code` - Indicates if it's a service code

2. **Detailed Information**
   - `includes` - Items included in this category
   - `excludes` - Items excluded from this category
   - `notes` - Additional notes

**All columns:**

- `code` - Text, primary key, not null - PSC code
- `description` - Text - Description of the PSC code
- `full_name` - Text - Full name of the product or service
- `excludes` - Text - Items excluded from this category
- `notes` - Text - Additional notes
- `includes` - Text - Items included in this category
- `service_code` - Boolean - Indicates if it's a service code
- `updated_at` - Timestamp with time zone - Last update timestamp

**Indexes:**

- Primary key on `code`
- Index on upper(`description`)
- Index on `service_code`

**Transformation notes:**

- Reference data with minimal transformations
- Source of truth for PSC information
- Separates products from services

#### `ref_country_code`

This table contains country codes and names.

**Key fields for capture managers:**


1. **Country Information**
   - `country_code` - ISO country code
   - `country_name` - Country name
   - `valid_flag` - Indicates if the code is currently valid

**All columns:**

- `country_code` - Text, primary key, not null - ISO country code
- `country_name` - Text, not null - Country name
- `valid_begin_date` - Date - Date when code became valid
- `valid_end_date` - Date - Date when code became invalid
- `valid_flag` - Boolean - Indicates if the code is currently valid

**Indexes:**

- Primary key on `country_code`
- Index on upper(`country_name`)
- Index on `valid_flag` where true

**Transformation notes:**

- Reference data for country lookups
- Standardized country names and codes
- Includes historical country codes with validity periods

#### `disaster_emergency_fund_code`

This table contains Disaster Emergency Fund Codes (DEFCs) for tracking emergency spending.

**Key fields for capture managers:**


1. **Code Information**

   - `code` - DEFC code
   - `public_law` - Associated public law
   - `title` - Title of the emergency funding
   - `group_name` - Group name for the DEFC

2. **Status Information**
   - `start_date` - Start date of the emergency funding
   - `end_date` - End date (if applicable)
   - `is_emergency` - Indicates if it's emergency spending
   - `is_active` - Indicates if the code is currently active

**All columns:**

- `code` - Text, primary key, not null - DEFC code
- `public_law` - Text - Associated public law
- `title` - Text - Title of the emergency funding
- `urls` - Text array - Relevant URLs
- `group_name` - Text - Group name for the DEFC
- `start_date` - Date - Start date of the emergency funding
- `end_date` - Date - End date (if applicable)
- `is_emergency` - Boolean - Indicates if it's emergency spending
- `is_active` - Boolean - Indicates if the code is currently active

**Indexes:**

- Primary key on `code`
- Index on `public_law`
- Index on `is_emergency`
- Index on `is_active`

**Transformation notes:**

- Reference data for emergency funding tracking
- Used for COVID-19 and Infrastructure investments reporting
- Enables tracking of special appropriations across agencies

#### `usaspending_subawards`

This table contains subaward (subcontract and subgrant) data as reported by prime awardees to USAspending.gov.

**Key fields for capture managers by category:**

1. **Subaward Identification**

   - `subaward_id` - Unique identifier for the subaward
   - `subaward_number` - Number assigned to the subaward by the prime recipient
   - `award_id` - ID of the prime award this subaward is under
   - `award_type` - Type of the prime award (procurement or assistance)

2. **Subaward Details**

   - `subaward_amount` - Dollar value of the subaward
   - `subaward_description` - Description of the work or purpose
   - `subaward_action_date` - Date the subaward was made
   - `subaward_report_year` - Fiscal year of the subaward report
   - `subaward_report_month` - Month of the subaward report

3. **Prime Award Information**

   - `prime_award_piid` - Procurement Instrument Identifier for prime contract
   - `prime_award_parent_piid` - Parent PIID for prime contract
   - `prime_award_fain` - Federal Award Identification Number for prime assistance award
   - `prime_award_amount` - Amount of the prime award

4. **Prime Recipient Information**

   - `prime_awardee_name` - Name of the prime awardee
   - `prime_awardee_duns` - DUNS number of the prime recipient
   - `prime_awardee_uei` - Unique Entity Identifier of the prime recipient
   - `prime_awardee_parent_duns` - Parent DUNS of the prime recipient
   - `prime_awardee_parent_uei` - Parent UEI of the prime recipient

5. **Subawardee Information**

   - `subawardee_name` - Name of the subcontractor or subgrantee
   - `subawardee_duns` - DUNS number of the subawardee
   - `subawardee_uei` - Unique Entity Identifier of the subawardee
   - `subawardee_parent_duns` - Parent DUNS of the subawardee
   - `subawardee_parent_uei` - Parent UEI of the subawardee
   - `subawardee_business_types` - Business size and socioeconomic categories of subawardee

6. **Location Information**

   - `subaward_primary_place_of_performance_city` - City where subaward work is performed
   - `subaward_primary_place_of_performance_state` - State where subaward work is performed
   - `subaward_primary_place_of_performance_country` - Country where subaward work is performed
   - `subaward_primary_place_of_performance_zip_4` - ZIP code where subaward work is performed
   - `subaward_primary_place_of_performance_congressional_district` - Congressional district of performance

7. **Federal Oversight Information**

   - `funding_agency_name` - Name of the funding agency
   - `funding_agency_id` - ID of the funding agency
   - `awarding_agency_name` - Name of the awarding agency
   - `awarding_agency_id` - ID of the awarding agency

8. **Classification Information**

   - `cfda_number` - Assistance Listings (CFDA) number for grants
   - `cfda_title` - Title of the CFDA program
   - `product_or_service_code` - Product or Service Code for contracts
   - `product_or_service_description` - Description of the PSC

**All columns:**

- `id` - Integer, primary key, not null - Auto-incrementing unique identifier
- `created_at` - Timestamp with time zone - Creation timestamp of the record
- `updated_at` - Timestamp with time zone - Last update timestamp of the record
- `fetch_date` - Date - Date the record was fetched from USAspending.gov
- `subaward_id` - Text - Unique identifier for the subaward from USAspending.gov
- `subaward_number` - Text - Number assigned to the subaward by the prime recipient
- `award_id` - Text - ID of the prime award this subaward is under
- `award_type` - Text - Type of the prime award (procurement or assistance)
- `subaward_amount` - Text - Dollar value of the subaward
- `subaward_action_date` - Text - Date the subaward was made
- `subaward_report_year` - Text - Fiscal year of the subaward report
- `subaward_report_month` - Text - Month of the subaward report
- `subaward_description` - Text - Description of the work or purpose
- `subaward_fsrs_report_id` - Text - FSRS (Federal Subaward Reporting System) report ID
- `subawardee_name` - Text - Name of the subcontractor or subgrantee
- `subawardee_duns` - Text - DUNS number of the subawardee
- `subawardee_uei` - Text - Unique Entity Identifier of the subawardee
- `subawardee_parent_duns` - Text - Parent DUNS of the subawardee
- `subawardee_parent_uei` - Text - Parent UEI of the subawardee
- `subawardee_address_line_1` - Text - First line of subawardee address
- `subawardee_address_line_2` - Text - Second line of subawardee address
- `subawardee_address_line_3` - Text - Third line of subawardee address
- `subawardee_city_name` - Text - Subawardee city name
- `subawardee_state_code` - Text - Subawardee state code
- `subawardee_state_name` - Text - Subawardee state name
- `subawardee_zip_4` - Text - Subawardee ZIP+4 code
- `subawardee_zip_code` - Text - Subawardee ZIP code
- `subawardee_congressional_district` - Text - Subawardee congressional district
- `subawardee_country_code` - Text - Subawardee country code
- `subawardee_country_name` - Text - Subawardee country name
- `subawardee_foreign_postal_code` - Text - Subawardee foreign postal code
- `subawardee_business_types` - Text - Business size and socioeconomic categories of subawardee
- `top_paid_fulltime_officers` - Text - Information about top paid officers in the subawardee organization
- `subaward_primary_place_of_performance_address_line_1` - Text - First line of subaward performance address
- `subaward_primary_place_of_performance_address_line_2` - Text - Second line of subaward performance address
- `subaward_primary_place_of_performance_address_line_3` - Text - Third line of subaward performance address
- `subaward_primary_place_of_performance_city` - Text - City where subaward work is performed
- `subaward_primary_place_of_performance_state` - Text - State where subaward work is performed
- `subaward_primary_place_of_performance_country` - Text - Country where subaward work is performed
- `subaward_primary_place_of_performance_zip_4` - Text - ZIP+4 code where subaward work is performed
- `subaward_primary_place_of_performance_congressional_district` - Text - Congressional district of performance
- `subaward_primary_place_of_performance_foreign_location` - Text - Foreign location description if applicable
- `prime_award_id` - Text - ID of the prime award in USAspending.gov
- `prime_award_piid` - Text - Procurement Instrument Identifier for prime contract
- `prime_award_parent_piid` - Text - Parent PIID for prime contract
- `prime_award_fain` - Text - Federal Award Identification Number for prime assistance award
- `prime_award_uri` - Text - Uniform Resource Identifier for prime assistance award
- `prime_award_type` - Text - Type of the prime award
- `prime_award_amount` - Text - Total amount of the prime award
- `prime_award_base_and_all_options_value` - Text - Base and all options value of prime contract
- `prime_award_base_exercised_options_val` - Text - Base exercised options value of prime contract
- `prime_award_description` - Text - Description of the prime award
- `prime_award_action_date` - Text - Date of the prime award action
- `prime_award_action_type` - Text - Type of action for the prime award
- `prime_award_action_type_description` - Text - Description of the prime award action type
- `prime_award_modification_number` - Text - Modification number of the prime award
- `prime_award_period_of_performance_start_date` - Text - Start date of prime award performance period
- `prime_award_period_of_performance_current_end_date` - Text - Current end date of prime award performance period
- `prime_awardee_name` - Text - Name of the prime awardee
- `prime_awardee_duns` - Text - DUNS number of the prime recipient
- `prime_awardee_uei` - Text - Unique Entity Identifier of the prime recipient
- `prime_awardee_parent_duns` - Text - Parent DUNS of the prime recipient
- `prime_awardee_parent_uei` - Text - Parent UEI of the prime recipient
- `prime_awardee_address_line_1` - Text - First line of prime awardee address
- `prime_awardee_address_line_2` - Text - Second line of prime awardee address
- `prime_awardee_address_line_3` - Text - Third line of prime awardee address
- `prime_awardee_city_name` - Text - Prime awardee city name
- `prime_awardee_state_code` - Text - Prime awardee state code
- `prime_awardee_state_name` - Text - Prime awardee state name
- `prime_awardee_zip_4` - Text - Prime awardee ZIP+4 code
- `prime_awardee_zip_code` - Text - Prime awardee ZIP code
- `prime_awardee_congressional_district` - Text - Prime awardee congressional district
- `prime_awardee_country_code` - Text - Prime awardee country code
- `prime_awardee_country_name` - Text - Prime awardee country name
- `prime_awardee_business_types` - Text - Business types of prime awardee
- `prime_award_primary_place_of_performance_city` - Text - City of prime award performance
- `prime_award_primary_place_of_performance_state` - Text - State of prime award performance
- `prime_award_primary_place_of_performance_country` - Text - Country of prime award performance
- `prime_award_primary_place_of_performance_zip_4` - Text - ZIP+4 code of prime award performance
- `prime_award_primary_place_of_performance_congressional_district` - Text - Congressional district of prime award performance
- `awarding_agency_id` - Text - ID of the awarding agency
- `awarding_agency_name` - Text - Name of the awarding agency
- `awarding_sub_tier_agency_id` - Text - ID of the awarding sub-tier agency
- `awarding_sub_tier_agency_name` - Text - Name of the awarding sub-tier agency
- `awarding_office_id` - Text - ID of the awarding office
- `awarding_office_name` - Text - Name of the awarding office
- `funding_agency_id` - Text - ID of the funding agency
- `funding_agency_name` - Text - Name of the funding agency
- `funding_sub_tier_agency_id` - Text - ID of the funding sub-tier agency
- `funding_sub_tier_agency_name` - Text - Name of the funding sub-tier agency
- `funding_office_id` - Text - ID of the funding office
- `funding_office_name` - Text - Name of the funding office
- `product_or_service_code` - Text - Product or Service Code for contracts
- `product_or_service_description` - Text - Description of the PSC
- `naics_code` - Text - North American Industry Classification System code
- `naics_description` - Text - Description of the NAICS code
- `cfda_number` - Text - Assistance Listings (CFDA) number for grants
- `cfda_title` - Text - Title of the CFDA program
- `high_comp_officer1_full_name` - Text - Full name of 1st highest compensated officer
- `high_comp_officer1_amount` - Text - Compensation amount for 1st highest officer
- `high_comp_officer2_full_name` - Text - Full name of 2nd highest compensated officer
- `high_comp_officer2_amount` - Text - Compensation amount for 2nd highest officer
- `high_comp_officer3_full_name` - Text - Full name of 3rd highest compensated officer
- `high_comp_officer3_amount` - Text - Compensation amount for 3rd highest officer
- `high_comp_officer4_full_name` - Text - Full name of 4th highest compensated officer
- `high_comp_officer4_amount` - Text - Compensation amount for 4th highest officer
- `high_comp_officer5_full_name` - Text - Full name of 5th highest compensated officer
- `high_comp_officer5_amount` - Text - Compensation amount for 5th highest officer
- `unique_award_key` - Text - Unique identifier for the award across USAspending.gov
- `broker_subaward_id` - Text - ID of the subaward in the broker system
- `last_modified_date` - Text - Date the record was last modified in source system

**Indexes:**

- Primary key on `id`
- Index on `subaward_id`
- Index on `award_id`
- Index on `subawardee_duns`
- Index on `subawardee_uei`
- Index on `prime_awardee_duns`
- Index on `prime_awardee_uei`
- Index on `subaward_action_date`

**Transformation notes:**

- Data is loaded directly from the USAspending.gov bulk download API
- Both subcontracts and subgrants are included in this table
- Monetary amounts are stored as text and may need conversion for calculations
- Foreign keys to related tables like awards and recipients enable relational queries
- Contains subaward data reported by prime recipients as required by FFATA
- Regular updates capture new subawards as they are reported

This subaward data helps identify capability gaps and competitive discriminators by revealing:
- Which capabilities competitors outsource vs. perform in-house
- Recurring partnership patterns between primes and subcontractors
- Division of work within competitor teams
- Geographic distribution of work across team members
- Small business utilization strategies

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

### 1. Finding Expiring Contracts by Agency and NAICS Code

```sql
SELECT
    a.award_id,
    a.piid,
    a.recipient_name,
    a.awarding_toptier_agency_name AS department,
    a.awarding_subtier_agency_name AS agency,
    a.period_of_performance_current_end_date AS end_date,
    a.total_obligation AS current_value,
    a.base_and_all_options_value AS potential_value,
    a.naics_code,
    a.naics_description,
    a.type_of_contract_pricing
FROM
    rpt.award_search a
WHERE
    a.naics_code = '541330'  -- Engineering Services
    AND a.awarding_toptier_agency_name = 'Department of Defense'
    AND a.period_of_performance_current_end_date BETWEEN CURRENT_DATE AND (CURRENT_DATE + INTERVAL '6 months')
ORDER BY
    a.period_of_performance_current_end_date;
```

### 2. Analyzing Competition History by Office

```sql
SELECT
    a.awarding_office_name,
    t.extent_competed,
    COUNT(*) AS award_count,
    SUM(a.total_obligation) AS total_value
FROM
    rpt.award_search a
    JOIN rpt.transaction_search_fpds t ON a.latest_transaction_id = t.transaction_id
WHERE
    a.awarding_subtier_agency_name = 'Naval Sea Systems Command'
    AND a.action_date >= '2022-10-01'
    AND a.action_date <= '2023-09-30'
GROUP BY
    a.awarding_office_name,
    t.extent_competed
ORDER BY
    a.awarding_office_name,
    total_value DESC;
```

### 3. Finding Incumbent Contractors by Agency and PSC

```sql
SELECT
    a.recipient_name,
    a.piid,
    a.product_or_service_code,
    a.product_or_service_description,
    a.period_of_performance_start_date,
    a.period_of_performance_current_end_date,
    a.total_obligation,
    a.awarding_office_name
FROM
    rpt.award_search a
WHERE
    a.product_or_service_code LIKE 'D3%'  -- IT and Telecom services
    AND a.awarding_toptier_agency_name = 'Department of Homeland Security'
    AND a.period_of_performance_current_end_date > CURRENT_DATE
ORDER BY
    a.total_obligation DESC;
```

### 4. Identifying Set-Aside Opportunities by Department

```sql
SELECT
    a.awarding_toptier_agency_name,
    t.type_set_aside,
    COUNT(*) AS award_count,
    SUM(a.total_obligation) AS total_obligated,
    AVG(a.total_obligation) AS average_award_size
FROM
    rpt.award_search a
    JOIN rpt.transaction_search_fpds t ON a.award_id = t.award_id
WHERE
    a.action_date >= '2022-10-01'
    AND t.type_set_aside IS NOT NULL
    AND t.type_set_aside != ''
GROUP BY
    a.awarding_toptier_agency_name,
    t.type_set_aside
ORDER BY
    total_obligated DESC;
```

### 5. Contract Recompete Timeline Analysis

```sql
SELECT
    a.piid,
    a.award_description,
    a.recipient_name,
    a.awarding_subtier_agency_name,
    a.period_of_performance_start_date,
    a.period_of_performance_current_end_date,
    a.total_obligation,
    a.product_or_service_code,
    a.product_or_service_description,
    a.naics_code,
    a.naics_description
FROM
    rpt.award_search a
WHERE
    a.period_of_performance_current_end_date BETWEEN
        (CURRENT_DATE + INTERVAL '6 months') AND
        (CURRENT_DATE + INTERVAL '12 months')
    AND a.total_obligation > 1000000
    AND a.category = 'contract'
ORDER BY
    a.period_of_performance_current_end_date;
```

## Schema Integration with Data_Insights Application

To integrate data from the USAspending database with the Data_Insights application, you can use the following approach:

1. **Extract relevant data** from the `rpt` schema (for most queries)
2. **Transform** the data to match your application's schema
3. **Load** the transformed data into your application's database

Example of a data integration query:

```sql
-- Extract from USAspending database (port 5433)
WITH award_data AS (
    SELECT
        a.award_id,
        a.piid,
        a.fain,
        a.recipient_name,
        a.total_obligation,
        a.action_date,
        a.period_of_performance_start_date,
        a.period_of_performance_current_end_date,
        ta.name AS awarding_agency,
        t.naics
    FROM
        rpt.award_search a
        JOIN rpt.transaction_search_fpds t ON a.award_id = t.award_id
        JOIN public.agency ag ON a.awarding_agency_id = ag.id
        JOIN public.toptier_agency ta ON ag.toptier_agency_id = ta.toptier_agency_id
    WHERE
        t.naics = '561210'
        AND a.fiscal_year = 2024
)
SELECT * FROM award_data;

-- Then insert into Data_Insights database (port 5432)
-- INSERT INTO capture_insights.contract_data (...)
-- SELECT ... FROM award_data;
```

# Database Setup

## Database Configuration

The application uses two separate PostgreSQL databases:

1. **Main Application Database** (Port 5432)

   - Used for the core application functionality
   - Contains cleaned and transformed data from various sources
   - Stores user preferences and application state

2. **USAspending Full Database** (Port 5433)
   - Complete USAspending.gov database restored from bulk download
   - Provides direct access to all USAspending.gov database tables
   - Runs on a separate PostgreSQL instance to ensure performance isolation

## Database Connection Information

### Main PostgreSQL Database

- **Host**: localhost
- **Port**: 5432
- **Database**: capture_insights
- **Username**: postgres
- **Password**: admin

### USAspending PostgreSQL Database

- **Host**: localhost
- **Port**: 5433
- **Database**: usaspending_full_db_download
- **Username**: root
- **Password**: password

## Environment Configuration

Both database connections are configured in the `.env` file:

```
# PostgreSQL Database Configuration
PG_USER=postgres
PG_PASSWORD=admin
PG_HOST=localhost
PG_PORT=5432
PG_DBNAME=capture_insights

# USAspending PostgreSQL Database
USASPENDING_PG_USER=root
USASPENDING_PG_PASSWORD=password
USASPENDING_PG_HOST=localhost
USASPENDING_PG_PORT=5433
USASPENDING_PG_DBNAME=usaspending_full_db_download
```

## USAspending Database Restoration

The USAspending database is restored from the official USAspending.gov bulk download. The restoration process:

1. Initializes a separate PostgreSQL instance on port 5433
2. Configures the instance with optimized performance settings
3. Restores the database in three phases:
   - Schema creation (pre-data)
   - Data loading
   - Index creation (post-data)

### USAspending Fetch Adjustment

To improve data retrieval reliability and accommodate API rate limits, we implemented the following fetch adjustments:

1. **Optimized Batch Processing**:
   - Implemented chunking of large data requests into smaller batches
   - Added configurable batch size parameters to prevent timeouts
   - Created resume capability to restart failed fetches from the last successful point

2. **Enhanced Error Handling**:
   - Added exponential backoff retry mechanism for API failures
   - Implemented comprehensive error classification and recovery strategies
   - Added detailed logging with timestamps for troubleshooting

3. **Rate Limiting Compliance**:
   - Implemented dynamic request throttling to respect API rate limits
   - Added automatic pausing when approaching rate limits
   - Created daily request quota tracking to prevent API cutoffs

4. **Performance Optimizations**:
   - Implemented parallel fetching for independent data segments
   - Added progress tracking and ETA calculations for large fetches
   - Created caching mechanism to prevent redundant requests

5. **Data Integrity Safeguards**:
   - Added checksum validation for downloaded files
   - Implemented transaction-based loading to prevent partial updates
   - Created automated data validation checks post-fetch

These adjustments significantly improved the reliability and efficiency of data acquisition from USAspending.gov, enabling us to process the full 1.1TB of federal spending data while maintaining compliance with API limitations.

### Starting and Managing the USAspending PostgreSQL Instance

The USAspending database runs on a separate PostgreSQL instance (port 5433) for performance isolation. This instance needs to be running for the application to connect to the USAspending database.

#### Manual Start/Stop

To manually start the PostgreSQL instance on port 5433:

```bash
cd "C:\Program Files\PostgreSQL\17\bin"
pg_ctl -D "E:\PostgreSQL17\data" -l "E:\PostgreSQL17\postgres.log" start
```

To stop the instance:

```bash
cd "C:\Program Files\PostgreSQL\17\bin"
pg_ctl -D "E:\PostgreSQL17\data" stop -m fast
```

#### Setting Up Automatic Start (Requires Admin Rights)

To make the USAspending PostgreSQL instance start automatically when Windows boots:

1. Open Command Prompt as Administrator
2. Run the following command:
   ```
   cd "C:\Program Files\PostgreSQL\17\bin"
   pg_ctl register -N "postgresql-usaspending" -D "E:\PostgreSQL17\data" -o "-p 5433"
   ```
3. Open Windows Services (services.msc)
4. Find the "postgresql-usaspending" service
5. Right-click and select "Properties"
6. Set "Startup type" to "Automatic"
7. Click "Apply" and "OK"

##### Troubleshooting Service Start Issues

If the service starts and then immediately stops:

1. Check the PostgreSQL log file for specific errors:

   ```
   type E:\PostgreSQL17\postgres.log
   ```

2. Common issues that may prevent the service from starting:

   a. **Port Conflict**: Another application might be using port 5433

   ```
   netstat -ano | findstr :5433
   ```

   b. **Service Account Permissions**: Ensure the service has proper permissions to access the E: drive

   - In Services, right-click the postgresql-usaspending service
   - Select "Properties" → "Log On" tab
   - Change to "Local System account" and check "Allow service to interact with desktop"
   - Make sure the E: drive is accessible before Windows attempts to start the service

   c. **Configuration Issues**: Try adjusting the service registration with different parameters

   ```
   pg_ctl unregister -N "postgresql-usaspending"
   pg_ctl register -N "postgresql-usaspending" -D "E:\PostgreSQL17\data" -w -o "-p 5433"
   ```

   d. **Start Parameters**: Edit the service and add start parameters:

   - In Services, right-click the postgresql-usaspending service
   - Select "Properties" → "General" tab
   - In "Start parameters" field, add: `-p 5433 -D "E:\PostgreSQL17\data"`

3. If you need to manually start the service instead of using automatic startup:

   ```
   net start postgresql-usaspending
   ```

   Or use the manual start command if service startup continues to fail:

   ```
   cd "C:\Program Files\PostgreSQL\17\bin"
   pg_ctl -D "E:\PostgreSQL17\data" -l "E:\PostgreSQL17\postgres.log" start
   ```

4. If the E: drive is removable or not always connected at startup, you may need to set the service to "Manual" startup type and start it only after confirming the E: drive is available.

#### Troubleshooting Connection Issues

If you encounter connection issues with the USAspending database:

1. **Check if the PostgreSQL service is running on port 5433:**

   ```
   netstat -ano | findstr LISTEN | findstr :5433
   ```

   If no output appears, the service is not running.

2. **Check PostgreSQL logs for errors:**

   ```
   type E:\PostgreSQL17\postgres.log
   ```

3. **Start the PostgreSQL instance if it's not running:**

   ```
   cd "C:\Program Files\PostgreSQL\17\bin"
   pg_ctl -D "E:\PostgreSQL17\data" -l "E:\PostgreSQL17\postgres.log" start
   ```

4. **Verify the connection is working:**
   ```
   psql -h localhost -p 5433 -U root -d usaspending_full_db_download
   ```

### Recent Restoration Completion

**✅ Database Restoration Successfully Completed on May 1, 2025**

The USAspending database restoration was successfully completed after processing approximately 1.1TB of federal spending data. The restoration process completed the following phases:

1. **Phase 1**: Schema Creation - All database schemas, tables, and structure created
2. **Phase 2**: Data Loading - All data loaded into tables across schemas including:
   - `public` schema: Core administrative and reference tables
   - `raw` schema: Source procurement and assistance transaction data
   - `int` schema: Intermediate processing tables
   - `rpt` schema: Reporting and analytics tables
3. **Phase 3**: Index Creation - Completed at 00:38:49 on May 1, 2025
   - Created hundreds of specialized indexes across all schemas
   - Established primary key constraints
   - Created foreign key relationships between tables
   - Built text search and specialized GIN indexes for performance
4. **Final Phase**: Database Statistics - ANALYZE operation completed

The database is now fully operational and can be accessed using the connection information below.

### Performance Optimizations

The USAspending PostgreSQL instance is configured with optimized settings:

- `shared_buffers = 4GB`
- `work_mem = 512MB`
- `maintenance_work_mem = 2000MB`
- `max_parallel_workers_per_gather = 8`
- `max_parallel_workers = 16`
- `synchronous_commit = off`
- `checkpoint_timeout = 60min`
- `max_wal_size = 10GB`
- Other performance settings

### Accessing the USAspending Database

You can access the USAspending database using pgAdmin 4:

1. Register a new server in pgAdmin
2. Configure the connection with:
   - Host: localhost
   - Port: 5433
   - Database: usaspending_full_db_download
   - Username: root
   - Password: password

You can also access the database using the psql command line:

```bash
psql -h localhost -p 5433 -U root usaspending_full_db_download
```

### Database Size

The full USAspending database is approximately 1.1TB in size and contains complete federal contract award data.

## Database Utilities

The project includes several database utilities to manage the USAspending database:

- `usaspening_restore_improved.py`: Python script for restoring the USAspending database with optimized settings
- `usaspending_restore_improved.bat`: Batch script alternative for database restoration
- `install_postgres_on_edrive.bat`: Script to install PostgreSQL on the E: drive

## USAspending Database Schema

The USAspending database is organized into four main schemas, each serving a specific purpose in the data processing pipeline. Below is a detailed overview of each schema and the transformations applied to the data throughout the ETL process.

### Schema Overview

1. **`raw` Schema** - Contains the original, unmodified data directly imported from USAspending.gov bulk downloads
2. **`int` (Intermediate) Schema** - Contains normalized and cleaned data derived from the raw schema
3. **`rpt` (Reporting) Schema** - Contains denormalized tables optimized for efficient querying and reporting
4. **`public` Schema** - Contains reference data, lookup tables, and administrative tables

### Data Flow and ETL Process

The USAspending database implements a standard ETL (Extract, Transform, Load) process:

1. **Extract**: Raw data is extracted from USAspending.gov bulk downloads and loaded into the `raw` schema without modification
2. **Transform**: Data is cleaned, normalized, and prepared in the `int` schema
3. **Load**: Transformed data is loaded into optimized reporting tables in the `rpt` schema

### Schema Details

#### `raw` Schema Tables

This schema contains unmodified data directly from USAspending.gov:

1. **`source_procurement_transaction`**

   - **Purpose**: Stores raw procurement (contract) data
   - **Columns**:
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

   **Transformation notes:**

   - Data in this table is raw and unmodified
   - May contain duplicates and inconsistent formatting
   - Original field names are preserved

2. **`source_assistance_transaction`**

   - **Purpose**: Stores raw financial assistance data (grants, loans)
   - **Columns**:
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

   **Transformation notes:**

   - Data in this table is raw and unmodified
   - Contains all original fields from the FABS source data
   - Field names match the USAspending.gov data dictionary

#### `int` Schema Tables

This schema contains normalized and cleaned data:

1. **`duns`**

   - **Purpose**: Normalized recipient identification information
   - **Columns**:
     - `awardee_or_recipient_uniqu` - Text (DUNS number)
     - `legal_business_name` - Text
     - `ultimate_parent_unique_ide` - Text (Parent DUNS)
     - `ultimate_parent_legal_enti` - Text
     - `broker_duns_id` - Text, not null, primary key
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

   **Indexes**:

   - Primary key on `broker_duns_id`
   - Unique constraint on `broker_duns_id`
   - Unique partial index on `awardee_or_recipient_uniqu` where not null
   - Unique partial index on `uei` where not null
   - Index on `broker_duns_id` with text pattern operations

   **Transformations Applied**:

   - Data cleansing and standardization
   - Duplicate DUNS consolidation
   - Address normalization
   - UEI-to-DUNS linking

2. **`transaction_delta`**

   - **Purpose**: Tracks changes in transaction data for incremental updates
   - **Columns**:
     - `transaction_id` - Bigint, not null, primary key
     - `created_at` - Timestamp with time zone, not null

   **Indexes**:

   - Primary key on `transaction_id`

   **Transformations Applied**:

   - Created during differential loading processes
   - Enables incremental updates rather than full reloads

#### `rpt` Schema Tables

This schema contains denormalized tables optimized for analytics:

1. **`award_search`**

   - **Purpose**: Denormalized table combining award, transaction, and recipient data
   - **Columns**:
     - `award_id` - Integer (primary key)
     - `generated_unique_award_id` - Text (unique identifier)
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

   **Indexes**:

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
   - Index on `awarding_agency_id`
   - Index on `category`
   - Index on `earliest_transaction_id`
   - Index on `earliest_transaction_search_id`
   - Index on `fain`
   - Index on `funding_agency_id`
   - Index on `latest_transaction_id`
   - Index on `latest_transaction_search_id`
   - Index on `parent_award_piid`
   - Index on `period_of_performance_start_date`
   - Index on `piid`
   - Index on `total_obligation`
   - Index on `total_outlays`
   - Index on `type`
   - Index on `type_raw`
   - Index on `uri`

   **Transformations Applied**:

   - Multi-source data combination from raw and int schemas
   - Extensive data cleaning and standardization
   - Derived fields like business categories from boolean flags
   - Pre-calculated fields for performance (totals, counts)
   - Added demographic data (populations)
   - COVID and Infrastructure spending tracking
   - Added treasury account data
   - Optimized for analytics with denormalized structure

2. **`transaction_search_fpds`**

   - **Purpose**: Optimized procurement transaction data for searching and reporting
   - **Columns**: (374 total columns)
     - `transaction_id` - Bigint - Transaction identifier
     - `award_id` - Bigint - Award identifier
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
     - Demographic data (population statistics)
     - Business classification flags (small business, minority owned, etc.)
     - Detailed award and contract information
     - Agency hierarchies
     - Funding details
     - Entity information
     - Treasury account information
     - Additional identifiers and cross-reference data
     - Timestamps for various stages of the award process
     - Boolean flags for various business types and classifications \*/

   **Key Indexes**:

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

   **Transformations Applied**:

   - Date standardization from text to date format
   - Agency reference normalization
   - Location data standardized and enhanced with demographic data
   - Business categories extracted from individual boolean flags
   - Amount fields converted to consistent numeric format
   - Hierarchical data structures established (recipient, agency, award)
   - Taxonomy codes standardized (NAICS, PSC)
   - Treasury account data normalized

3. **`transaction_search_fabs`**

   - **Purpose**: Optimized financial assistance data for searching
   - **Key Columns**:
     - `transaction_id`, `award_id`, `fain`, `uri`
     - `action_date`, `type`, `federal_action_obligation`
     - `cfda_number`
     - `awarding_agency_id`, `funding_agency_id`
     - `recipient_hash`
   - **Transformations Applied**:
     - Date format standardization
     - Reference key addition
     - Search optimization

4. **`recipient_lookup`**

   - **Purpose**: Normalized recipient information for efficient lookups
   - **Key Columns**:
     - `recipient_hash`, `legal_business_name`
     - `recipient_unique_id`, `uei`
     - `parent_duns`, `parent_uei`
   - **Transformations Applied**:
     - Recipient information consolidation
     - Standardized identifier creation
     - Parent-child relationship establishment

5. **`recipient_profile`**

   - **Purpose**: Aggregated recipient information
   - **Key Columns**:
     - `recipient_hash`, `recipient_level` (P=Parent, C=Child, R=Recipient)
     - `recipient_name`, `recipient_unique_id`, `uei`
     - `last_12_months` (JSON data with aggregated metrics)
   - **Transformations Applied**:
     - Metrics pre-aggregation for dashboard performance
     - Hierarchical recipient structure creation
     - Denormalized JSON data for quick access

6. **`parent_award`**
   - **Purpose**: Parent-child award relationship information
   - **Key Columns**:
     - `award_id`
     - `generated_unique_award_id`
     - `parent_award_id`
   - **Transformations Applied**:
     - Parent-child relationship establishment for awards
     - Hierarchy creation for IDV contracts

#### `public` Schema Tables

This schema contains reference and lookup tables:

1. **`agency`**

   - **Purpose**: Agency information and hierarchy
   - **Key Columns**:
     - `id`, `toptier_agency_id`, `subtier_agency_id`
     - `office_agency_id`, `toptier_flag`
   - **Transformations Applied**:
     - Agency hierarchy relationship establishment
     - Top-tier and sub-tier agency linking

2. **`toptier_agency`**

   - **Purpose**: Top-tier federal agency details
   - **Key Columns**:
     - `toptier_agency_id`, `cgac_code`
     - `name`, `abbreviation`, `toptier_code`
   - **Transformations Applied**:
     - Agency name and code standardization
     - Reference data preparation

3. **`subtier_agency`**

   - **Purpose**: Sub-tier agency information
   - **Key Columns**:
     - `subtier_agency_id`
     - `name`, `abbreviation`, `subtier_code`
   - **Transformations Applied**:
     - Sub-tier agency name and code standardization

4. **`references_cfda`**

   - **Purpose**: CFDA program information
   - **Key Columns**:
     - `id`, `program_number`, `program_title`
     - `popular_name`, `federal_agency`, `objectives`
   - **Transformations Applied**:
     - Minimal transformations as reference data

5. **`naics`**

   - **Purpose**: NAICS code information
   - **Key Columns**:
     - `code`, `description`, `year`
   - **Transformations Applied**:
     - Minimal transformations as reference data

6. **`psc`**
   - **Purpose**: Product or Service Code information
   - **Key Columns**:
     - `code`, `description`
   - **Transformations Applied**:
     - Minimal transformations as reference data

### Key Transformations and Data Cleansing Processes

Throughout the ETL pipeline, the following transformation categories are applied:

#### 1. Data Cleansing

- **Date Standardization**: Converting various date formats to ISO format
- **Text Field Cleaning**: Trimming whitespace, handling special characters
- **Case Normalization**: Converting to upper/lower case for consistency
- **NULL Handling**: Proper handling of NULL values and empty strings

#### 2. Data Normalization

- **Reference Table Creation**: Establishing lookup tables for repeated values
- **Foreign Key Relationships**: Creating proper database relationships
- **Atomic Field Creation**: Splitting complex fields into atomic components

#### 3. Data Enrichment

- **Derived Field Calculation**: Creating fields like fiscal_year from action_date
- **Hierarchical Structure Creation**: Establishing parent-child relationships
- **Geospatial Enrichment**: Adding location-based data where applicable

#### 4. Performance Optimization

- **Index Creation**: Adding indexes on commonly queried fields
- **Pre-aggregation**: Creating pre-calculated fields and aggregated values
- **Denormalization**: Strategic denormalization to enhance query performance

### Sample Queries for Data Access

Below are example queries demonstrating how to access data from the USAspending database:

```sql
-- Basic contract search by NAICS code and fiscal year
SELECT
    a.award_id,
    a.piid,
    a.recipient_name,
    a.total_obligation,
    a.period_of_performance_start_date,
    a.period_of_performance_current_end_date
FROM
    rpt.award_search a
    JOIN rpt.transaction_search_fpds t ON a.award_id = t.award_id
WHERE
    t.naics = '561210'  -- Facilities Support Services
    AND a.fiscal_year = 2024;

-- Agency spending by recipient
SELECT
    r.recipient_name,
    ta.name AS agency_name,
    SUM(a.total_obligation) AS total_obligation
FROM
    rpt.award_search a
    JOIN rpt.recipient_lookup r ON a.recipient_hash = r.recipient_hash
    JOIN public.agency ag ON a.awarding_agency_id = ag.id
    JOIN public.toptier_agency ta ON ag.toptier_agency_id = ta.toptier_agency_id
WHERE
    a.action_date >= '2023-10-01'
    AND a.action_date <= '2024-09-30'
GROUP BY
    r.recipient_name,
    ta.name
ORDER BY
    total_obligation DESC
LIMIT 20;

-- Contracts expiring in the next 24 months
SELECT
    a.award_id,
    a.piid,
    a.recipient_name,
    a.period_of_performance_current_end_date,
    a.total_obligation,
    ta.name AS awarding_agency,
    n.description AS naics_description
FROM
    rpt.award_search a
    JOIN rpt.transaction_search_fpds t ON a.award_id = t.award_id
    JOIN public.agency ag ON a.awarding_agency_id = ag.id
    JOIN public.toptier_agency ta ON ag.toptier_agency_id = ta.toptier_agency_id
    LEFT JOIN public.naics n ON t.naics = n.code
WHERE
    a.period_of_performance_current_end_date >= CURRENT_DATE
    AND a.period_of_performance_current_end_date <= (CURRENT_DATE + INTERVAL '24 months')
ORDER BY
    a.period_of_performance_current_end_date;
```

### Integration with Data_Insights Application

To integrate data from the USAspending database with the main Data_Insights application database:

1. Extract data from the USAspending database (port 5433)
2. Transform as needed for application requirements
3. Load into the main application database (port 5432)

Example cross-database query pattern:

```sql
-- Extract from USAspending database (port 5433)
WITH award_data AS (
    SELECT
        a.award_id,
        a.piid,
        a.recipient_name,
        a.total_obligation,
        ta.name AS awarding_agency,
        t.naics,
        n.description AS naics_description
    FROM
        rpt.award_search a
        JOIN rpt.transaction_search_fpds t ON a.award_id = t.award_id
        JOIN public.agency ag ON a.awarding_agency_id = ag.id
        JOIN public.toptier_agency ta ON ag.toptier_agency_id = ta.toptier_agency_id
        LEFT JOIN public.naics n ON t.naics = n.code
    WHERE
        t.naics = '561210'
        AND a.fiscal_year = 2024
)
SELECT * FROM award_data;

-- Then in application code, insert into Data_Insights database (port 5432)
-- INSERT INTO capture_insights.contract_data (...)
-- SELECT ... FROM award_data;
```

For more detailed information on specific schema structures, transformations, and sample queries, refer to the comprehensive documentation in `docs/DATABASE_SCHEMA.md`.

from sqlalchemy import create_engine, text

# Connect to the SQLite database
db_path = r'sqlite:///C:\GitHub\Opp_Sem_Search\backend\data\usaspending_historical.db'
engine = create_engine(db_path)

# Create the awards_slim table
# This table is a slimmed down version of the awards table, containing only the columns needed for the analysis.
with engine.connect() as connection:
    connection.execute(text("""
        CREATE TABLE awards_slim AS
        SELECT action_date, action_date_fiscal_year, action_type, award_id_piid, total_outlayed_amount_for_overall_award, award_type, awarding_agency_name, awarding_office_name,
               awarding_sub_agency_name, base_and_all_options_value, base_and_exercised_options_value,
               contract_award_unique_key, contract_transaction_unique_key, current_total_value_of_award,
               dod_acquisition_program_description, extent_competed, fair_opportunity_limited_sources,
               federal_action_obligation, funding_agency_name, funding_office_name, funding_sub_agency_name,
               government_furnished_property, idv_type, multi_year_contract, multiple_or_single_award_idv,
               naics_code, naics_description, number_of_actions, number_of_offers_received,
               ordering_period_end_date, other_than_full_and_open_competition, parent_award_agency_name,
               period_of_performance_current_end_date, period_of_performance_potential_end_date,
               period_of_performance_start_date, potential_total_value_of_award,
               primary_place_of_performance_city_name, primary_place_of_performance_state_code, prime_award_base_transaction_description, transaction_description,
               product_or_service_code, product_or_service_code_description, program_acronym, recipient_doing_business_as_name,
               recipient_name, recipient_uei, recipient_parent_name, recipient_parent_name_raw,
               recipient_parent_uei, solicitation_date, solicitation_procedures,
               subcontracting_plan, total_dollars_obligated, type_of_contract_pricing, type_of_idc, type_of_set_aside,
               undefinitized_action, usaspending_permalink
        FROM awards;
    """))
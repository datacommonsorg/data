#!/bin/bash
set -e

SCRIPT_PATH=$(realpath "$(dirname "$0")")

python3 $SCRIPT_PATH/../../tools/statvar_importer/stat_var_processor.py --input_data=$SCRIPT_PATH/input_files/births.csv --pv_map=$SCRIPT_PATH/irl_birth_pvmap.csv --config_file=$SCRIPT_PATH/irl_metadata.csv --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf --output_path=$SCRIPT_PATH/output_files/irl_birth_output  || { echo "Error: Processing births.csv failed!"; exit 1; }

python3 $SCRIPT_PATH/../../tools/statvar_importer/stat_var_processor.py --input_data=$SCRIPT_PATH/input_files/deaths.csv --pv_map=$SCRIPT_PATH/irl_deaths_pvmap.csv --config_file=$SCRIPT_PATH/irl_metadata.csv --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf --output_path=$SCRIPT_PATH/output_files/irl_death_output  || { echo "Error: Processing deaths.csv failed!"; exit 1; }

python3 $SCRIPT_PATH/../../tools/statvar_importer/stat_var_processor.py --input_data=$SCRIPT_PATH/input_files/deaths_from_external_causes.csv --pv_map=$SCRIPT_PATH/irl_causeofdeath_pvmap.csv --config_file=$SCRIPT_PATH/irl_metadata.csv --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf --places_resolved_csv=$SCRIPT_PATH/places_resolver.csv --output_path=$SCRIPT_PATH/output_files/irl_external_cause_of_death_output  || { echo "Error: Processing external_cause_of_death.csv failed!"; exit 1; }

python3 $SCRIPT_PATH/../../tools/statvar_importer/stat_var_processor.py --input_data=$SCRIPT_PATH/input_files/life_expectancy.csv --pv_map=$SCRIPT_PATH/irl_lifeexpectancy_pvmap.csv --config_file=$SCRIPT_PATH/irl_metadata.csv --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf --output_path=$SCRIPT_PATH/output_files/irl_life_expectancy_output  || { echo "Error: Processing life_expectancy.csv failed!"; exit 1; }

python3 $SCRIPT_PATH/../../tools/statvar_importer/stat_var_processor.py --input_data=$SCRIPT_PATH/input_files/suicides.csv --pv_map=$SCRIPT_PATH/irl_suicide_pvmap.csv --config_file=$SCRIPT_PATH/irl_metadata.csv --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf --output_path=$SCRIPT_PATH/output_files/irl_suicide_output || { echo "Error: Processing suicides.csv failed!"; exit 1; }

python3 $SCRIPT_PATH/../../tools/statvar_importer/stat_var_processor.py --input_data=$SCRIPT_PATH/input_files/suicides_with_aa1_aa2.csv --pv_map=$SCRIPT_PATH/irl_aa1_aa2_suicide_pvmap.csv --config_file=$SCRIPT_PATH/irl_metadata.csv --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf --places_resolved_csv=$SCRIPT_PATH/places_resolver.csv --output_path=$SCRIPT_PATH/output_files/irl_aa1_aa2_suicide_output || { echo "Error: Processing aa1_aa2_suicide.csv failed!"; exit 1; }

python3 $SCRIPT_PATH/../../tools/statvar_importer/stat_var_processor.py --input_data=$SCRIPT_PATH/input_files/population_by_age_gender.csv --pv_map=$SCRIPT_PATH/irl_population_by_age_gender_pvmap.csv --config_file=$SCRIPT_PATH/irl_metadata.csv --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf --output_path=$SCRIPT_PATH/output_files/irl_population_by_age_gender_output || { echo "Error: Processing population_by_age_gender.csv failed!"; exit 1; }

python3 $SCRIPT_PATH/../../tools/statvar_importer/stat_var_processor.py --input_data=$SCRIPT_PATH/input_files/population_by_religion.csv --pv_map=$SCRIPT_PATH/irl_population_by_religion_pvmap.csv --config_file=$SCRIPT_PATH/irl_metadata.csv --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf --places_resolved_csv=$SCRIPT_PATH/places_resolver_religion.csv --output_path=$SCRIPT_PATH/output_files/irl_population_by_religion_output || { echo "Error: Processing population_by_religion.csv failed!"; exit 1; }

python3 $SCRIPT_PATH/../../tools/statvar_importer/stat_var_processor.py --input_data=$SCRIPT_PATH/input_files/population_at_each_census.csv --pv_map=$SCRIPT_PATH/irl_population_at_each_census_pvmap.csv --config_file=$SCRIPT_PATH/irl_metadata.csv --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf --places_resolved_csv=$SCRIPT_PATH/places_resolver_each_census.csv --output_path=$SCRIPT_PATH/output_files/irl_population_at_each_census_output || { echo "Error: Processing population_at_each_census.csv failed!"; exit 1; }

python3 $SCRIPT_PATH/../../tools/statvar_importer/stat_var_processor.py --input_data=$SCRIPT_PATH/input_files/population_by_gender.csv --pv_map=$SCRIPT_PATH/irl_population_by_gender_pvmap.csv --config_file=$SCRIPT_PATH/irl_metadata.csv --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf --places_resolved_csv=$SCRIPT_PATH/places_resolver_gender.csv --output_path=$SCRIPT_PATH/output_files/irl_population_by_gender_output || { echo "Error: Processing popuplation_by_gender.csv failed!"; exit 1; }

python3 $SCRIPT_PATH/../../tools/statvar_importer/stat_var_processor.py --input_data=$SCRIPT_PATH/input_files/population_by_employment.csv --pv_map=$SCRIPT_PATH/irl_aa1_aa2_employment_pvmap.csv --config_file=$SCRIPT_PATH/irl_metadata.csv --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf --places_resolved_csv=$SCRIPT_PATH/places_resolver.csv --output_path=$SCRIPT_PATH/output_files/irl_aa1_aa2_employment_output || { echo "Error: Processing employment.csv failed!"; exit 1; }

echo "All processing steps completed successfully."
exit 0
#!/bin/bash
set -e

# Get the absolute path to the directory where this script is located
SCRIPT_PATH=$(realpath "$(dirname "$0")")

# --- Process Commands ---

echo "Starting processing..."

python3 $SCRIPT_PATH/../../tools/statvar_importer/stat_var_processor.py \
    --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf \
    --input_data=$SCRIPT_PATH/input_files/activity_employment_unemployment_by_sex.csv \
    --pv_map=$SCRIPT_PATH/employment_unemployment_pvmap.csv \
    --config_file=$SCRIPT_PATH/employment_unemployment_metadata.csv \
    --output_path=$SCRIPT_PATH/output/employment_unemployment_output \
    --log_level=-2 \
    --log_every_n=1000 \
    || { echo "Error: Processing activity_employment_unemployment_by_sex.csv failed!"; exit 1; }

python3 $SCRIPT_PATH/../../tools/statvar_importer/stat_var_processor.py \
    --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf \
    --input_data=$SCRIPT_PATH/input_files/Education_Field_of_study.csv \
    --pv_map=$SCRIPT_PATH/education_field_of_study_pvmap.csv \
    --config_file=$SCRIPT_PATH/education_field_of_study_metadata.csv \
    --output_path=$SCRIPT_PATH/output/education_field_of_study_output \
    --log_level=-2 \
    --log_every_n=1000 \
    || { echo "Error: Processing Education_Field_of_study.csv failed!"; exit 1; }

python3 $SCRIPT_PATH/../../tools/statvar_importer/stat_var_processor.py \
    --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf \
    --input_data=$SCRIPT_PATH/input_files/Gross_Birth_Rate_by_province.csv \
    --pv_map=$SCRIPT_PATH/gross_birth_rate_by_province_pvmap.csv \
    --places_resolved_csv=$SCRIPT_PATH/places_resolved.csv \
    --config_file=$SCRIPT_PATH/gross_birth_rate_by_province_metadata.csv \
    --output_path=$SCRIPT_PATH/output/gross_birth_rate_by_province_output \
    --log_level=-2 \
    --log_every_n=1000 \
    || { echo "Error: Processing Gross_Birth_Rate_by_province.csv failed!"; exit 1; }

python3 $SCRIPT_PATH/../../tools/statvar_importer/stat_var_processor.py \
    --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf \
    --input_data=$SCRIPT_PATH/input_files/Gross_Birth_Rate_national.csv \
    --pv_map=$SCRIPT_PATH/gross_birth_rate_national_pvmap.csv \
    --config_file=$SCRIPT_PATH/gross_birth_rate_national_metadata.csv \
    --output_path=$SCRIPT_PATH/output/gross_birth_rate_national_output \
    --log_level=-2 \
    --log_every_n=1000 \
    || { echo "Error: Processing Gross_Birth_Rate_national.csv failed!"; exit 1; }

python3 $SCRIPT_PATH/../../tools/statvar_importer/stat_var_processor.py \
    --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf \
    --input_data=$SCRIPT_PATH/input_files/Gross_Birth_Rate_per_municipality.csv \
    --pv_map=$SCRIPT_PATH/gross_birth_rate_per_municipality_pvmap.csv \
    --places_resolved_csv=$SCRIPT_PATH/places_resolved.csv \
    --config_file=$SCRIPT_PATH/gross_birth_rate_per_municipality_metadata.csv \
    --output_path=$SCRIPT_PATH/output/gross_birth_rate_per_municipality_output \
    --log_level=-2 \
    --log_every_n=1000 \
    || { echo "Error: Processing Gross_Birth_Rate_per_municipality.csv failed!"; exit 1; }

python3 $SCRIPT_PATH/../../tools/statvar_importer/stat_var_processor.py \
    --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf \
    --input_data=$SCRIPT_PATH/input_files/Male_rate_at_birth_by_province.csv \
    --pv_map=$SCRIPT_PATH/male_rate_at_birth_by_province_pvmap.csv \
    --places_resolved_csv=$SCRIPT_PATH/places_resolved.csv \
    --config_file=$SCRIPT_PATH/male_rate_at_birth_by_province_metadata.csv \
    --output_path=$SCRIPT_PATH/output/male_rate_at_birth_by_province_output \
    --log_level=-2 \
    --log_every_n=1000 \
    || { echo "Error: Processing Male_rate_at_birth_by_province.csv failed!"; exit 1; }

python3 $SCRIPT_PATH/../../tools/statvar_importer/stat_var_processor.py \
    --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf \
    --input_data=$SCRIPT_PATH/input_files/Levels_of_education_gender.csv \
    --pv_map=$SCRIPT_PATH/education_sex_levels_of_education_pvmap.csv \
    --config_file=$SCRIPT_PATH/education_sex_levels_of_education_metadata.csv \
    --output_path=$SCRIPT_PATH/output/levels_of_education_gender_output \
    --log_level=-2 \
    --log_every_n=1000 \
    || { echo "Error: Processing Levels_of_education_gender.csv failed!"; exit 1; }

python3 $SCRIPT_PATH/../../tools/statvar_importer/stat_var_processor.py \
    --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf \
    --input_data=$SCRIPT_PATH/input_files/Population_by_municipality_and_gender.csv \
    --pv_map=$SCRIPT_PATH/population_by_municipality_and_gender_pvmap.csv \
    --places_resolved_csv=$SCRIPT_PATH/places_resolved.csv \
    --config_file=$SCRIPT_PATH/population_by_municipality_and_gender_metadata.csv \
    --output_path=$SCRIPT_PATH/output/population_by_municipality_and_gender_output \
    --log_level=-2 \
    --log_every_n=1000 \
    || { echo "Error: Processing Population_by_municipality_and_gender.csv failed!"; exit 1; }

python3 $SCRIPT_PATH/../../tools/statvar_importer/stat_var_processor.py \
    --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf \
    --input_data=$SCRIPT_PATH/input_files/Population_by_province_capitals_and_gender.csv \
    --pv_map=$SCRIPT_PATH/population_by_province_capitals_and_gender_pvmap.csv \
    --places_resolved_csv=$SCRIPT_PATH/places_resolved.csv \
    --config_file=$SCRIPT_PATH/population_by_province_capitals_and_gender_metadata.csv \
    --output_path=$SCRIPT_PATH/output/population_by_province_capitals_and_gender_output \
    --log_level=-2 \
    --log_every_n=1000 \
    || { echo "Error: Processing Population_by_province_capitals_and_gender.csv failed!"; exit 1; }

python3 $SCRIPT_PATH/../../tools/statvar_importer/stat_var_processor.py \
    --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf \
    --input_data=$SCRIPT_PATH/input_files/Population_by_sex_and_age_group.csv \
    --pv_map=$SCRIPT_PATH/population_by_sex_and_age_group_pvmap.csv \
    --config_file=$SCRIPT_PATH/population_by_sex_and_age_group_metadata.csv \
    --output_path=$SCRIPT_PATH/output/population_by_sex_and_age_group_output \
    --log_level=-2 \
    --log_every_n=1000 \
    || { echo "Error: Processing Population_by_sex_and_age_group.csv failed!"; exit 1; }

# --- Completion ---
echo "All processing steps completed successfully."
exit 0

#!/bin/bash
set -e

SCRIPT_PATH=$(realpath "$(dirname "$0")")

python3 "$SCRIPT_PATH/../../../tools/statvar_importer/stat_var_processor.py" --input_data="$SCRIPT_PATH/input_files/Educational_Attainment_by_Age_Range_and_Gender/*.csv" --pv_map="$SCRIPT_PATH/Educational_Attainment_by_Age_Range_and_Gender_pvmap.csv" --config_file="$SCRIPT_PATH/common_metadata.csv" --output_path="$SCRIPT_PATH/output_files/Educational_Attainment_by_Age_Range_and_Gender_output" --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf --statvar_dcid_remap_csv="$SCRIPT_PATH/statvar_remap.csv" || { echo "Error: Processing Educational_Attainment_by_Age_Range_and_Gender failed!"; exit 1; }

python3 "$SCRIPT_PATH/../../../tools/statvar_importer/stat_var_processor.py" --input_data="$SCRIPT_PATH/input_files/Post_Secondary_Completions_Total_Awards_Degrees/*.csv" --pv_map="$SCRIPT_PATH/Post_Secondary_Completions_Total_Awards_Degrees_pvmap.csv" --config_file="$SCRIPT_PATH/common_metadata.csv" --output_path="$SCRIPT_PATH/output_files/Post_Secondary_Completions_Total_Awards_Degrees_output" --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf --places_resolved_csv="$SCRIPT_PATH/places_resolver.csv" --statvar_dcid_remap_csv="$SCRIPT_PATH/statvar_remap.csv" || { echo "Error: Processing Post_Secondary_Completions_Total_Awards_Degrees failed!"; exit 1; }

python3 "$SCRIPT_PATH/../../../tools/statvar_importer/stat_var_processor.py" --input_data="$SCRIPT_PATH/input_files/Public_School_Enrollment_by_County_Grade_and_Race/*.csv" --pv_map="$SCRIPT_PATH/Public_School_Enrollment_by_County_Grade_and_Race_pvmap.csv" --config_file="$SCRIPT_PATH/common_metadata.csv" --output_path="$SCRIPT_PATH/output_files/Public_School_Enrollment_by_County_Grade_and_Race_output" --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf --places_resolved_csv="$SCRIPT_PATH/places_resolver.csv" --statvar_dcid_remap_csv="$SCRIPT_PATH/statvar_remap.csv" || { echo "Error: Processing Public_School_Enrollment_by_County_Grade_and_Race failed!"; exit 1; }

python3 "$SCRIPT_PATH/../../../tools/statvar_importer/stat_var_processor.py" --input_data="$SCRIPT_PATH/input_files/Undergraduate_STEM_Enrollment_at_Publicly_Supported_Institutions/*.csv" --pv_map="$SCRIPT_PATH/Undergraduate_STEM_Enrollment_at_Publicly_Supported_Institutions_pvmap.csv" --config_file="$SCRIPT_PATH/common_metadata.csv" --output_path="$SCRIPT_PATH/output_files/Undergraduate_STEM_Enrollment_at_Publicly_Supported_Institutions_output" --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf --places_resolved_csv="$SCRIPT_PATH/places_resolver.csv" --statvar_dcid_remap_csv="$SCRIPT_PATH/statvar_remap.csv" || { echo "Error: Processing Undergraduate_STEM_Enrollment_at_Publicly_Supported_Institutions failed!"; exit 1; }

echo "All processing steps completed successfully."
exit 0   

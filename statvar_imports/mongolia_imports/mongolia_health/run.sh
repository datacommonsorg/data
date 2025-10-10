#!/bin/bash

set -e

SCRIPT_PATH=$(realpath "$(dirname "$0")")

python3 $SCRIPT_PATH/../../../tools/statvar_importer/stat_var_processor.py --input_data=$SCRIPT_PATH/input_files/deaths_by_month_and_region.csv --pv_map=$SCRIPT_PATH/deaths_by_month_and_region_pvmap.csv --config_file=$SCRIPT_PATH/mongolia_metadata.csv --output_path=$SCRIPT_PATH/output_files/deaths_by_month_and_region_output --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf --places_resolved_csv=$SCRIPT_PATH/mongolia_place_resolver.csv || { echo "Error: Processing deaths_by_month_and_region failed!"; exit 1; }

python3 $SCRIPT_PATH/../../../tools/statvar_importer/stat_var_processor.py --input_data=$SCRIPT_PATH/input_files/infant_mortality_per_1000_live_births_by_month_region.csv --pv_map=$SCRIPT_PATH/infant_mortality_per_1000_live_births_by_month_region_pvmap.csv --config_file=$SCRIPT_PATH/mongolia_metadata.csv --output_path=$SCRIPT_PATH/output_files/infant_mortality_per_1000_live_births_by_month_region_output --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf --places_resolved_csv=$SCRIPT_PATH/mongolia_place_resolver.csv || { echo "Error: Processing infant_mortality_per_1000_live_births_by_month_region failed!"; exit 1; }

python3 $SCRIPT_PATH/../../../tools/statvar_importer/stat_var_processor.py --input_data=$SCRIPT_PATH/input_files/live_births_by_month_region.csv --pv_map=$SCRIPT_PATH/live_births_by_month_region_pvmap.csv --config_file=$SCRIPT_PATH/mongolia_metadata.csv --output_path=$SCRIPT_PATH/output_files/live_births_by_month_region_output --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf --places_resolved_csv=$SCRIPT_PATH/mongolia_place_resolver.csv || { echo "Error: Processing live_births_by_month_region failed!"; exit 1; }

python3 $SCRIPT_PATH/../../../tools/statvar_importer/stat_var_processor.py --input_data=$SCRIPT_PATH/input_files/number_of_abortions_by_region.csv --pv_map=$SCRIPT_PATH/number_of_abortions_by_region_pvmap.csv --config_file=$SCRIPT_PATH/mongolia_metadata.csv --output_path=$SCRIPT_PATH/output_files/number_of_abortions_by_region_output --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf --places_resolved_csv=$SCRIPT_PATH/mongolia_place_resolver.csv  || { echo "Error: Processing number_of_abortions_by_region failed!"; exit 1; }

python3 $SCRIPT_PATH/../../../tools/statvar_importer/stat_var_processor.py --input_data=$SCRIPT_PATH/input_files/number_of_hospital_beds_by_type.csv --pv_map=$SCRIPT_PATH/number_of_hospital_beds_by_type_pvmap.csv --config_file=$SCRIPT_PATH/mongolia_metadata.csv --output_path=$SCRIPT_PATH/output_files/number_of_hospital_beds_by_type_output --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf || { echo "Error: Processing number_of_hospital_beds_by_type failed!"; exit 1; }

python3 $SCRIPT_PATH/../../../tools/statvar_importer/stat_var_processor.py --input_data=$SCRIPT_PATH/input_files/number_of_mothers_delivered_child_by_month_region.csv --pv_map=$SCRIPT_PATH/number_of_mothers_delivered_child_by_month_region_pvmap.csv --config_file=$SCRIPT_PATH/mongolia_metadata.csv --output_path=$SCRIPT_PATH/output_files/number_of_mothers_delivered_child_by_month_region_output --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf --places_resolved_csv=$SCRIPT_PATH/mongolia_place_resolver.csv || { echo "Error: Processing number_of_mothers_delivered_child_by_month_region failed!"; exit 1; }

echo "All processing steps completed successfully."
exit 0

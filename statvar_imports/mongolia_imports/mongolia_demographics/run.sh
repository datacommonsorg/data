#!/bin/bash
set -e

SCRIPT_PATH=$(realpath "$(dirname "$0")")

python3 $SCRIPT_PATH/../../../tools/statvar_importer/stat_var_processor.py --input_data=$SCRIPT_PATH/input_files/mid_year_total_population_by_region.xlsx --pv_map=$SCRIPT_PATH/mid_year_total_population_by_region_pvmap.csv --config_file=$SCRIPT_PATH/mongolia_metadata.csv --output_path=$SCRIPT_PATH/output_files/mid_year_total_population_by_region_output --places_resolved_csv=$SCRIPT_PATH/mongolia_place_resolver.csv 

python3 $SCRIPT_PATH/../../../tools/statvar_importer/stat_var_processor.py --input_data=$SCRIPT_PATH/input_files/number_of_households_by_region_and_urban_rural.xlsx --pv_map=$SCRIPT_PATH/number_of_households_by_region_and_urban_rural_pvmap.csv --config_file=$SCRIPT_PATH/mongolia_metadata.csv --output_path=$SCRIPT_PATH/output_files/number_of_households_by_region_and_urban_rural_output --places_resolved_csv=$SCRIPT_PATH/mongolia_place_resolver.csv 

python3 $SCRIPT_PATH/../../../tools/statvar_importer/stat_var_processor.py --input_data=$SCRIPT_PATH/input_files/number_of_households_by_region.xlsx --pv_map=$SCRIPT_PATH/number_of_households_by_region_pvmap.csv --config_file=$SCRIPT_PATH/mongolia_metadata.csv --output_path=$SCRIPT_PATH/output_files/number_of_households_by_region_output --places_resolved_csv=$SCRIPT_PATH/mongolia_place_resolver.csv 

python3 $SCRIPT_PATH/../../../tools/statvar_importer/stat_var_processor.py --input_data=$SCRIPT_PATH/input_files/resident_population_by_agegroup_15_and_over_and_maritalstatus.xlsx --pv_map=$SCRIPT_PATH/resident_population_by_agegroup_15_and_over_and_maritalstatus_pvmap.csv --config_file=$SCRIPT_PATH/mongolia_metadata.csv --output_path=$SCRIPT_PATH/output_files/resident_population_by_agegroup_15_and_over_and_maritalstatus_output 

python3 $SCRIPT_PATH/../../../tools/statvar_importer/stat_var_processor.py --input_data=$SCRIPT_PATH/input_files/total_population_by_age_group_and_sex.xlsx --pv_map=$SCRIPT_PATH/total_population_by_age_group_and_sex_pvmap.csv --config_file=$SCRIPT_PATH/mongolia_metadata.csv --output_path=$SCRIPT_PATH/output_files/total_population_by_age_group_and_sex_output 

python3 $SCRIPT_PATH/../../../tools/statvar_importer/stat_var_processor.py --input_data=$SCRIPT_PATH/input_files/total_population_by_region_and_urban_rural.xlsx --pv_map=$SCRIPT_PATH/total_population_by_region_and_urban_rural_pvmap.csv --config_file=$SCRIPT_PATH/mongolia_metadata.csv --output_path=$SCRIPT_PATH/output_files/total_population_by_region_and_urban_rural_output --places_resolved_csv=$SCRIPT_PATH/mongolia_place_resolver.csv 

python3 $SCRIPT_PATH/../../../tools/statvar_importer/stat_var_processor.py --input_data=$SCRIPT_PATH/input_files/total_population_by_sex_and_urban_rural.xlsx --pv_map=$SCRIPT_PATH/total_population_by_sex_and_urban_rural_pvmap.csv --config_file=$SCRIPT_PATH/mongolia_metadata.csv --output_path=$SCRIPT_PATH/output_files/total_population_by_sex_and_urban_rural_output 

echo "All processing steps completed successfully."
exit 0

#!/bin/bash
set -e

SCRIPT_PATH=$(realpath "$(dirname "$0")")

COVID_CSV_FILES="$SCRIPT_PATH/input_files/2021_COVID_Directional_Indicators.csv,$SCRIPT_PATH/input_files/2022_COVID_Directional_Indicators.csv"

# Process column SCH_DIND_INSTRUCTIONTYPE
python3 $SCRIPT_PATH/../../../tools/statvar_importer/stat_var_processor.py \
--input_data=$COVID_CSV_FILES \
--pv_map=$SCRIPT_PATH/covid_directional_indicators_pv_map1.csv \
--config_file=$SCRIPT_PATH/covid_directional_indicators_metadata.csv \
--places_resolved_csv=$SCRIPT_PATH/place_resolved.csv \
--existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf \
--output_path=$SCRIPT_PATH/output_files/covid_directional_indicators_output1 || \
{ echo "Error: Processing SCH_DIND_INSTRUCTIONTYPE!"; exit 1; }

# Process column SCH_DIND_REMOTETYPE
python3 $SCRIPT_PATH/../../../tools/statvar_importer/stat_var_processor.py \
--input_data=$COVID_CSV_FILES \
--pv_map=$SCRIPT_PATH/covid_directional_indicators_pv_map2.csv \
--config_file=$SCRIPT_PATH/covid_directional_indicators_metadata.csv \
--places_resolved_csv=$SCRIPT_PATH/place_resolved.csv \
--existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf \
--output_path=$SCRIPT_PATH/output_files/covid_directional_indicators_output2 || \
{ echo "Error: Processing SCH_DIND_REMOTETYPE!"; exit 1; }

# Process column SCH_DIND_REMOTEAMOUNT
python3 $SCRIPT_PATH/../../../tools/statvar_importer/stat_var_processor.py \
--input_data=$COVID_CSV_FILES \
--pv_map=$SCRIPT_PATH/covid_directional_indicators_pv_map3.csv \
--config_file=$SCRIPT_PATH/covid_directional_indicators_metadata.csv \
--places_resolved_csv=$SCRIPT_PATH/place_resolved.csv \
--existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf \
--output_path=$SCRIPT_PATH/output_files/covid_directional_indicators_output3 || \
{ echo "Error: Processing SCH_DIND_REMOTEAMOUNT!"; exit 1; }

# Process column SCH_DIND_REMOTEPERCT
python3 $SCRIPT_PATH/../../../tools/statvar_importer/stat_var_processor.py \
--input_data=$COVID_CSV_FILES \
--pv_map=$SCRIPT_PATH/covid_directional_indicators_pv_map4.csv \
--config_file=$SCRIPT_PATH/covid_directional_indicators_metadata.csv \
--places_resolved_csv=$SCRIPT_PATH/place_resolved.csv \
--existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf \
--output_path=$SCRIPT_PATH/output_files/covid_directional_indicators_output4 || \
{ echo "Error: Processing SCH_DIND_REMOTEPERCT!"; exit 1; }

echo "All processing steps completed successfully."
exit 0



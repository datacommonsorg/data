#!/bin/bash
SCRIPT_PATH=$(realpath "$(dirname "$0")")
INPUT_DIR="$SCRIPT_PATH/input_files"
OUTPUT_DIR="$SCRIPT_PATH/output_files"
PROCESSOR_SCRIPT="$SCRIPT_PATH/../data/tools/statvar_importer/stat_var_processor.py"
PV_MAP="$SCRIPT_PATH/pv_map.py"
PLACES_RESOLVED_CSV="$SCRIPT_PATH/place_mapping.csv"
CONFIG_FILE="$SCRIPT_PATH/bea_metadata.py"
STATVAR_REMAP_CSV="$SCRIPT_PATH/bea_statvar_remap.csv"
EXISTING_STATVAR_MCF="gs://unresolved_mcf/scripts/statvar/stat_vars.mcf"

# Create output directory if it doesn't exist
mkdir -p "$OUTPUT_DIR"

# Loop through all files in the input directory that start with 'bea_gdp_input_'
for input_file in "$INPUT_DIR"/bea_gdp_input_*.csv; do
  if [[ -f "$input_file" ]]; then
    # Extract the base filename and create the output filename
    base_filename=$(basename "$input_file")
    output_filename="${base_filename%.*}" # Remove the .csv extension
    output_path="$OUTPUT_DIR/${output_filename}"

    # Construct the python command
    python3 "$PROCESSOR_SCRIPT" \
      --input_data="$input_file" \
      --pv_map="$PV_MAP" \
      --places_resolved_csv="$PLACES_RESOLVED_CSV" \
      --config_file="$CONFIG_FILE" \
      --statvar_dcid_remap_csv="$STATVAR_REMAP_CSV" \
      --existing_statvar_mcf="$EXISTING_STATVAR_MCF" \
      --output_path="$output_path"

    echo "Processed: $input_file -> $output_path"
  fi
done

echo "Finished processing all bea_gdp_input_*.csv files."
#!/bin/bash

# Ensure all target directories exist inside the container
mkdir -p final_output input_files

# Step 1: Data Download (Downloads directly into this local folder)
curl -L --retry 3 "https://ec.europa.eu/eurostat/api/dissemination/sdmx/2.1/data/DEMO_NDIVIND/?format=SDMX-CSV&compressed=false" -o ./input_files/Divorce_indicators_data_raw.csv

# Step 2: Data Processing
# Pointing directly to the downloaded CSV to avoid wildcard expansion errors
python3 ../../../tools/statvar_importer/stat_var_processor.py \
  "--input_data=./input_files/Divorce_indicators_data_raw.csv" \
  "--pv_map=./Divorce_indicators_pvmap.csv" \
  "--config_file=./Divorce_indicators_metadata.csv" \
  "--generate_statvar_name=True" \
  "--skip_constant_csv_columns=False" \
  "--output_columns=observationDate,observationAbout,variableMeasured,value,observationPeriod,measurementMethod,unit,scalingFactor" \
  "--output_path=./final_output/Divorce_indicators_output" \
  "--places_resolved_csv=./places_resolved.csv" \
  "--existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf"
  
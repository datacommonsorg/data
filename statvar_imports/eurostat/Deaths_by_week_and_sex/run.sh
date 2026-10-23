#!/bin/bash

# Ensure all target directories exist inside the container
mkdir -p final_output input_files

# Step 1: Data Download (Downloads directly into this local folder) & Run the Script
curl -L --retry 3 "https://ec.europa.eu/eurostat/api/dissemination/sdmx/2.1/data/DEMO_R_MWK_TS/?format=SDMX-CSV&compressed=false" -o Deaths_by_week_and_sex_data_raw.csv
python3 convert_week_to_date.py
mv Deaths_by_week_and_sex_data_raw_processed.csv input_files/

# Step 2: Data Processing
# Pointing directly to the generated CSV to avoid wildcard errors
python3 ../../../tools/statvar_importer/stat_var_processor.py \
  "--input_data=./input_files/Deaths_by_week_and_sex_data_raw_processed.csv" \
  "--pv_map=./Deaths_by_week_and_sex_pvmap.csv" \
  "--config_file=./Deaths_by_week_and_sex_metadata.csv" \
  "--generate_statvar_name=True" \
  "--skip_constant_csv_columns=False" \
  "--output_columns=observationDate,observationAbout,variableMeasured,value,observationPeriod,measurementMethod,unit,scalingFactor" \
  "--output_path=./final_output/Deaths_by_week_and_sex_output" \
  "--places_resolved_csv=./places_resolved.csv" \
  "--existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf"
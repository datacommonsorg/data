#!/bin/bash

# Step 1: Data Download (Downloads directly into this local folder)
mkdir -p input_files
mkdir -p final_output
curl -L --retry 3 "https://ec.europa.eu/eurostat/api/dissemination/sdmx/2.1/data/une_rt_m/?format=SDMX-CSV&compressed=false" -o input_files/unemployment_by_sex_and_age_monthly_data_data_raw.csv

# Step 2: Data Processing
python3 ../../../tools/statvar_importer/stat_var_processor.py \
  "--input_data=./input_files/*.csv" \
  "--pv_map=./unemployment_by_sex_and_age_monthly_data_pvmap.csv" \
  "--config_file=./unemployment_by_sex_and_age_monthly_data_metadata.csv" \
  "--generate_statvar_name=True" \
  "--skip_constant_csv_columns=False" \
  "--output_columns=observationDate,observationAbout,variableMeasured,value,observationPeriod,unit,scalingFactor" \
  "--output_path=./final_output/unemployment_by_sex_and_age_monthly_data_output" \
  "--places_resolved_csv=./places_resolved.csv" \
  "--existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf" 
  
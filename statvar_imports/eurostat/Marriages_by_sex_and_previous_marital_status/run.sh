#!/bin/bash

mkdir -p input_files
mkdir -p final_output

# Step 1: Data Download (Downloads directly into this local folder)
curl -L --retry 3 "https://ec.europa.eu/eurostat/api/dissemination/sdmx/2.1/data/DEMO_NMSTA/?format=SDMX-CSV&compressed=false" -o ./input_files/Marriages_by_sex_and_previous_marital_status_data_raw.csv

# Step 2: Data Processing
python3 ../../../tools/statvar_importer/stat_var_processor.py \
  "--input_data=./input_files/*.csv" \
  "--pv_map=./Marriages_by_sex_and_previous_marital_status_pvmap.csv" \
  "--config_file=./Marriages_by_sex_and_previous_marital_status_metadata.csv" \
  "--generate_statvar_name=True" \
  "--skip_constant_csv_columns=False" \
  "--output_columns=observationDate,observationAbout,variableMeasured,value,observationPeriod,measurementMethod,unit,scalingFactor" \
  "--output_path=./Marriages_by_sex_and_previous_marital_status_output" \
  "--places_resolved_csv=./places_resolved.csv" \
  "--existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf" 

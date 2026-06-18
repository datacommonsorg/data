#!/bin/bash

# Step 1: Data Download
mkdir -p input_files
mkdir -p output_files
curl -L --retry 3 "https://ec.europa.eu/eurostat/api/dissemination/sdmx/2.1/data/DEMO_FMONTH/?format=SDMX-CSV&compressed=false" -o ./input_files/live_births_total_by_month_data_input.csv

# Step 2: Data Processing

python3 ../../../tools/statvar_importer/stat_var_processor.py \
  "--input_data=./input_files/*.csv" \
  "--pv_map=./live_births_total_by_month_pvmap.csv" \
  "--config_file=./live_births_total_by_month_metadata.csv" \
  "--generate_statvar_name=True" \
  "--skip_constant_csv_columns=False" \
  "--output_columns=observationDate,observationAbout,variableMeasured,value,observationPeriod,unit" \
  "--output_path=output_files/live_births_total_by_month_output" \
  "--places_resolved_csv=./places_resolved.csv" \
  "--existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf"
  
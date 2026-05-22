#!/bin/bash
# Updated commands for existing folder structure

# Step 1: Data Download
mkdir -p input_files
curl -L --retry 3 "https://ec.europa.eu/eurostat/api/dissemination/sdmx/2.1/data/DEMO_FMONTH/?format=SDMX-CSV&compressed=false" -o ./input_files/Live_births_total_by_month_data_raw.csv

# Step 2: Full Data Processing

python3 ../../../tools/statvar_importer/stat_var_processor.py \
  "--input_data=./input_files/Live_births_total_by_month_data_raw.csv" \
  "--pv_map=./Live_births_total_by_month_pvmap.csv" \
  "--config_file=./Live_births_total_by_month_metadata.csv" \
  "--generate_statvar_name=True" \
  "--skip_constant_csv_columns=False" \
  "--output_columns=observationDate,observationAbout,variableMeasured,value,observationPeriod" \
  "--output_path=./output" \
  "--places_resolved_csv=./places_resolved.csv" \
  "--existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf"
  
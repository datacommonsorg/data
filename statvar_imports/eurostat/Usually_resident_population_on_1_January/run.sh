#!/bin/bash

# Step 1: Data Download
mkdir -p source_files
curl -L --retry 3 "https://ec.europa.eu/eurostat/api/dissemination/sdmx/2.1/data/DEMO_URESPOP/?format=SDMX-CSV&compressed=false" -o ./source_files/Usually_resident_population_on_1_January_input.csv

# Step 2: Data Processing
python3 ../../../tools/statvar_importer/stat_var_processor.py \
  "--input_data=./source_files/*.csv" \
  "--pv_map=./Usually_resident_population_on_1_January_pvmap.csv" \
  "--config_file=./Usually_resident_population_on_1_January_metadata.csv" \
  "--generate_statvar_name=True" \
  "--skip_constant_csv_columns=False" \
  "--output_columns=observationDate,observationAbout,variableMeasured,value,observationPeriod,unit" \
  "--output_path=./Usually_resident_population_on_1_January" \
  "--places_resolved_csv=./places_resolved_runtime.csv" \
  "--existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf"

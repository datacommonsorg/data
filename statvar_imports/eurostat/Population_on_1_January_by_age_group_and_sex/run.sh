#!/bin/bash

# Step 1: Data Download
mkdir -p source_files
curl -L --retry 3 "https://ec.europa.eu/eurostat/api/dissemination/sdmx/2.1/data/DEMO_PJANGROUP/?format=SDMX-CSV&compressed=false" -o ./source_files/Population_on_1_January_by_age_group_and_sex_data_input.csv

# Step 2: Data Processing
python3 ../../../tools/statvar_importer/stat_var_processor.py \
  "--input_data=./source_files/*.csv" \
  "--pv_map=./Population_on_1_January_by_age_group_and_sex_pvmap.csv" \
  "--config_file=./Population_on_1_January_by_age_group_and_sex_metadata.csv" \
  "--generate_statvar_name=True" \
  "--skip_constant_csv_columns=False" \
  "--output_columns=observationDate,observationAbout,variableMeasured,value,observationPeriod,unit" \
  "--output_path=./Population_on_1_January_by_age_group_and_sex_output" \
  "--places_resolved_csv=./places_resolved_runtime.csv" \
  "--existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf"

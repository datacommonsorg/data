#!/bin/bash

# Step 1: Data Download
mkdir -p input_files
curl -L --retry 3 "https://ec.europa.eu/eurostat/api/dissemination/sdmx/2.1/data/DEMO_PJANEDU/?format=SDMX-CSV&compressed=false" -o ./input_files/pop_age_sex_edu_attainment_level_input.csv

# Step 2: Full Data Processing
python3 ../../../tools/statvar_importer/stat_var_processor.py \
  "--input_data=./input_files/*.csv" \
  "--pv_map=./pop_age_sex_edu_attainment_level_pvmap.csv" \
  "--config_file=./pop_age_sex_edu_attainment_level_metadata.csv" \
  "--generate_statvar_name=True" \
  "--skip_constant_csv_columns=False" \
  "--output_columns=observationDate,observationAbout,variableMeasured,value,observationPeriod,unit" \
  "--output_path=./pop_age_sex_edu_attainment_level_output" \
  "--places_resolved_csv=./places_resolved.csv" \
  "--existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf"

#!/bin/bash

# Step 1: Data Download
mkdir -p input_files
curl -L --retry 3 "https://ec.europa.eu/eurostat/api/dissemination/sdmx/2.1/data/DEMO_NDIVIND/?format=SDMX-CSV&compressed=false" -o sdmx/Divorce_indicators/divorce_indicators_data_raw.csv

# Step 2: Data Processing
python3 ../../../tools/statvar_importer/stat_var_processor.py \
  "--input_data=./input_files/*.csv" \
  "--pv_map=./divorce_indicators_pvmap.csv" \
  "--config_file=./divorce_indicators_metadata.csv" \
  "--generate_statvar_name=True" \
  "--skip_constant_csv_columns=False" \
  "--output_columns=observationDate,observationAbout,variableMeasured,value,observationPeriod,unit" \
  "--output_path=./divorce_indicators_output" \
  "--places_resolved_csv=./places_resolved.csv" \
  "--existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf" \

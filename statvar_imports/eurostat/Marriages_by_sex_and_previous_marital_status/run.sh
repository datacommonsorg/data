#!/bin/bash

# Ensure all target directories exist inside the container
mkdir -p final_output

# Step 1: Data Download (Downloads directly into this local folder)
curl -L --retry 3 "https://ec.europa.eu/eurostat/api/dissemination/sdmx/2.1/data/DEMO_NMSTA/?format=SDMX-CSV&compressed=false" -o Marriages_by_sex_and_previous_marital_status_data_raw.csv

# Step 2: Navigate up 3 levels to the 'data/' repository root
# This makes all the "statvar_imports/..." parameter paths perfectly resolve.
cd ../../../

# Step 3: Data Processing
python3 tools/statvar_importer/stat_var_processor.py \
  "--input_data=statvar_imports/eurostat/Marriages_by_sex_and_previous_marital_status/Marriages_by_sex_and_previous_marital_status_data_raw.csv" \
  "--pv_map=statvar_imports/eurostat/Marriages_by_sex_and_previous_marital_status/output_pvmap_cleaned.csv" \
  "--config_file=statvar_imports/eurostat/Marriages_by_sex_and_previous_marital_status/output_metadata.csv" \
  "--generate_statvar_name=True" \
  "--skip_constant_csv_columns=False" \
  "--output_columns=observationDate,observationAbout,variableMeasured,value,observationPeriod,measurementMethod,unit,scalingFactor" \
  "--output_path=statvar_imports/eurostat/Marriages_by_sex_and_previous_marital_status/final_output/output" \
  "--places_resolved_csv=statvar_imports/eurostat/Marriages_by_sex_and_previous_marital_status/places_resolved_runtime.csv" \
  "--existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf"

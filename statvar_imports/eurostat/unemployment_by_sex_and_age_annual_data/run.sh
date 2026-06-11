#!/bin/bash

# Ensure all target directories exist inside the container
mkdir -p final_output

# Step 1: Data Download (Downloads directly into this local folder)
curl -L --retry 3 "https://ec.europa.eu/eurostat/api/dissemination/sdmx/2.1/data/une_rt_a/?format=SDMX-CSV&compressed=false" -o unemployment_by_sex_and_age_annual_data_data_raw.csv

# Step 2: Navigate up 3 levels to the 'data/' repository root
# This makes all the "statvar_imports/..." parameter paths perfectly resolve.
cd ../../../

# Step 3: Data Processing
python3 tools/statvar_importer/stat_var_processor.py \
  "--input_data=statvar_imports/eurostat/unemployment_by_sex_and_age_annual_data/unemployment_by_sex_and_age_annual_data_data_raw.csv" \
  "--pv_map=statvar_imports/eurostat/unemployment_by_sex_and_age_annual_data/unemployment_by_sex_and_age_annual_data_pvmap.csv" \
  "--config_file=statvar_imports/eurostat/unemployment_by_sex_and_age_annual_data/unemployment_by_sex_and_age_annual_data_metadata.csv" \
  "--generate_statvar_name=True" \
  "--skip_constant_csv_columns=False" \
  "--output_columns=observationDate,observationAbout,variableMeasured,value,observationPeriod,unit,scalingFactor" \
  "--output_path=statvar_imports/eurostat/unemployment_by_sex_and_age_annual_data/final_output/unemployment_by_sex_and_age_annual_data_output" \
  "--places_resolved_csv=statvar_imports/eurostat/unemployment_by_sex_and_age_annual_data/places_resolved.csv" \
  "--existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf"

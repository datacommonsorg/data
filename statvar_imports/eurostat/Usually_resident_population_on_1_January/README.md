# Eurostat Usually Resident Population On January 1 Import

## Overview

This dataset contains annual data reporting the usually resident population on January 1st at the national level, sourced from Eurostat. The data tracks the official total population counts across various European countries to support EU legislative, budgeting, and institutional voting procedures.

type of place: Country
years: Historical data to present (2014-2025)
place_resolution: Resolved to DCIDs (e.g., dcid:country/FRA, dcid:country/DEU)

## Data Source
**Source URL:**
https://ec.europa.eu/eurostat/databrowser/product/view/demo_urespop?lang=en

**Provenance Description:**
This dataset is produced by **Eurostat** using harmonized population data provided by European national statistical institutes. It tracks the usually resident population across European countries on January 1st to support official EU policy, budgeting, and voting procedures.

## Processing
To process the  Eurostat Usually Resident Population On January 1 data and generate statistical variables, use the following commands from your current import data directory:

# Download input file

```bash
mkdir -p input_files
curl -L --retry 3 "https://ec.europa.eu/eurostat/api/dissemination/sdmx/2.1/data/DEMO_URESPOP/?format=SDMX-CSV&compressed=false" -o ./source_files/Usually_resident_population_on_1_January_input.csv

## For Test Data Run

python3 tools/statvar_importer/stat_var_processor.py \
  "--input_data=./testdata/Usually_resident_population_on_1_January_input.csv" \
  "--pv_map=./Usually_resident_population_on_1_January_pvmap.csv" \
  "--output_path=./testdata/Usually_resident_population_on_1_January_output" \
  "--config_file=./Usually_resident_population_on_1_January_metadata.csv" \
  "--existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf" 

## For Main data run

python3 ../../../tools/statvar_importer/stat_var_processor.py \
  "--input_data=./source_files/*.csv" \
  "--pv_map=./Usually_resident_population_on_1_January_pvmap.csv" \
  "--config_file=./Usually_resident_population_on_1_January_metadata.csv" \
  "--generate_statvar_name=True" \
  "--skip_constant_csv_columns=False" \
  "--output_columns=observationDate,observationAbout,variableMeasured,value,observationPeriod,unit" \
  "--output_path=./Usually_resident_population_on_1_January_output" \
  "--places_resolved_csv=./places_resolved_runtime.csv" \
  "--existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf"
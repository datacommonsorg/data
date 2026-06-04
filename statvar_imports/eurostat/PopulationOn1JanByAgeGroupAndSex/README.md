# Eurostat Population By Age Group And Sex On January 1 Import

## Overview

This dataset contains annual population stock data broken down by age groups and sex at the national level, sourced from Eurostat. The data tracks demographic distributions on January 1st across various European countries to support long-term social, economic, and institutional planning.

type of place: Country
years: Historical data to present (1960-2025)
place_resolution: Resolved to DCIDs (e.g., dcid:country/FRA, dcid:country/DEU)

## Data Source
**Source URL:**
https://ec.europa.eu/eurostat/databrowser/view/demo_pjangroup/default/table

**Provenance Description:**
This dataset is produced and harmonized by Eurostat using demographic data provided by national statistical institutes across European countries. It breaks down the annual population stock on January 1st by specific age groups and sex to support EU socioeconomic policy and long-term planning.

### Script Details:
- **Download**: Uses `curl` to fetch the latest SDMX-CSV data from Eurostat's dissemination API.
- **Processing**: Uses `stat_var_processor.py` to map raw data to Data Commons StatVarObservations using the PV map and metadata configuration.

## Processing
To process the Eurostat Population By Age Group And Sex On January 1 data and generate statistical variables, use the following commands from your current import data directory:

# Download input file

```bash
mkdir -p input_files
curl -L --retry 3 "https://ec.europa.eu/eurostat/api/dissemination/sdmx/2.1/data/DEMO_PJANGROUP/?format=SDMX-CSV&compressed=false" -o ./source_files/Population_on_1_January_by_age_group_and_sex_data_input.csv

## For Test Data Run

python3 tools/statvar_importer/stat_var_processor.py \
  --input_data=statvar_imports/eurostat/Population_on_1_January_by_age_group_and_sex/testdata/Population_on_1_January_by_age_group_and_sex_data_input.csv \
  --pv_map=statvar_imports/eurostat/Population_on_1_January_by_age_group_and_sex/Population_on_1_January_by_age_group_and_sex_pvmap.csv \
  --output_path=statvar_imports/eurostat/Population_on_1_January_by_age_group_and_sex/testdata/Population_on_1_January_by_age_group_and_sex_output \
  --config_file=statvar_imports/eurostat/Population_on_1_January_by_age_group_and_sex/Population_on_1_January_by_age_group_and_sex_metadata.csv \
  --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf 

## For Main data run

python3 tools/statvar_importer/stat_var_processor.py \
  --input_data=statvar_imports/eurostat/Population_on_1_January_by_age_group_and_sex/source_files/Population_on_1_January_by_age_group_and_sex_data_input.csv \
  --pv_map=statvar_imports/eurostat/Population_on_1_January_by_age_group_and_sex/Population_on_1_January_by_age_group_and_sex_pvmap.csv \
  --output_path=statvar_imports/eurostat/Population_on_1_January_by_age_group_and_sex/Population_on_1_January_by_age_group_and_sex_output \
  --config_file=statvar_imports/eurostat/Population_on_1_January_by_age_group_and_sex/Population_on_1_January_by_age_group_and_sex_metadata.csv\
  --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf
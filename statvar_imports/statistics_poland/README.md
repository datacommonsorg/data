# Poland Demographics Dataset
## Overview
This dataset contains demographic information from Poland sourced directly from poland datasets for foundational demographic and socio-economic statistics for Poland.

## Data Source

**Source URL:** 
https://stat.gov.pl/en/databases/


The data comes from Poland's official statistical authority and includes comprehensive demographic variables such as population counts, age distributions, and other census-related metrics.
Processing Instructions

## how to download data
Download script (download_script.py). To download the data, you'll need to use the provided download script,download_script.py. This script will automatically create an "poland_input" folder where you should place the file to be processed. The script also requires a poland_data_sample/poland_raw.xlsx to be present to identify file structure.

type of place: State.

statvars: Demographics

years: 2003 to 2024.

## Processing Instructions
To process the Poland Census data and generate statistical variables, use the following command from the "data" directory:

Example Download : python3 statistics_poland/download_script.py

## For Test Data Run:
python3 tools/statvar_importer/stat_var_processor.py \
  --input_data=statvar_imports/statistics_poland/test/StatisticsPoland_input.csv \
  --pv_map=statvar_imports/statistics_poland/StatisticsPoland_pvmap.csv \
  --output_path=statvar_imports/statistics_poland/test/StatisticsPoland_output \
  --config_file=statvar_imports/statistics_poland/Statistics_Poland_metadata.csv \
  --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf \
  2>&1 | tee statvar_imports/statistics_poland/log.txt

## For Main data run
python3 tools/statvar_importer/stat_var_processor.py \
  --input_data=statvar_imports/statistics_poland/poland_input/StatisticsPoland_input.csv \
  --pv_map=statvar_imports/statistics_poland/StatisticsPoland_pvmap.csv \
  --output_path=statvar_imports/statistics_poland/poland_output/StatisticsPoland_output \
  --config_file=statvar_imports/statistics_poland/Statistics_Poland_metadata.csv \
  --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf

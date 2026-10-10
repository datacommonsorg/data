# Poland Demographics Dataset
## Overview
This dataset contains demographic information from Poland sourced directly from poland datasets for foundational demographic and socio-economic statistics for Poland.

## Data Source

**Source URL:** 
https://stat.gov.pl/en/databases/


The data comes from Poland's official statistical authority and includes comprehensive demographic variables such as population counts, age distributions, and other census-related metrics.
Processing Instructions

## Processing Instructions
To process the Poland Census data and generate statistical variables, use the following command from the "data" directory:

python3 tools/statvar_importer/stat_var_processor.py \
  --input_data=statvar_imports/statistics_poland/test/StatisticsPoland_input.csv \
  --pv_map=statvar_imports/statistics_poland/StatisticsPoland_pvmap.csv \
  --output_path=statvar_imports/statistics_poland/test/StatisticsPoland_output \
  --config_file=statvar_imports/statistics_poland/Statistics_Poland_metadata.csv
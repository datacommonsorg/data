# Bulgaria Demographics Dataset

## Overview

This dataset contains demographic information from Bulgaria sourced directly from the National Statistical Institute (NSI) datasets for foundational demographic and socio-economic statistics for Bulgaria.
, 
## Data Source

**Source URL:** 
 https://www.nsi.bg/en/statistical-data/206/649

The data comes from Bulgaria's official statistical authority and includes comprehensive demographic variables such as population counts, age distributions, and other census-related metrics.

## Processing Instructions

To process the Bulgaria Census data and generate statistical variables, use the following command from the "data" directory:

 python3 tools/statvar_importer/stat_var_processor.py \
  --input_data=statvar_imports/BulgariaNSI_Demographics/populationbyyear/test_data/BulgariaNSI_Demographics_Year_input.csv \
  --pv_map=statvar_imports/BulgariaNSI_Demographics/populationbyyear/BulgariaNSI_Demographics_Year_pvmap.csv \
  --output_path=statvar_imports/BulgariaNSI_Demographics/populationbyyear/test_data/BulgariaNSI_Demographics_Year_output \
  --config_file=statvar_imports/BulgariaNSI_Demographics/populationbyyear/BulgariaNSI_Demographics_metadata.csv



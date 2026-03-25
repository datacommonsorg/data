# Poland Demographics Dataset
## Overview
This dataset provides foundational demographic and socio-economic statistics for Poland, sourced directly from official national datasets.

## Data Source

**Source URL:**
https://stat.gov.pl/en/databases/


The data comes from Poland's official statistical authority and includes comprehensive demographic variables such as population counts, age distributions, and other census-related metrics.

## How To Download Input Data
To download the data, you'll need to use the provided download script download_input_data.py. This script processes the StatisticsPoland_input.csv file available in Bucket with path datcom-prod-imports/statvar_imports/statistics_poland/poland_data_sample to generate StatisticsPoland_input_*.csv inside a new "source_files" folder.

type of place: State.

statvars: Demographics

years: 2003 to 2024.

## Processing Instructions
To process the Poland Census data and generate statistical variables, use the following command from the "data" directory:

**Download input file**
 ```bash
 python3 statvar_imports/statistics_poland/download_input_data.py
```
**For Test Data Run**
```bash
python3 tools/statvar_importer/stat_var_processor.py \
  --input_data=statvar_imports/statistics_poland/test/StatisticsPoland_input.csv \
  --pv_map=statvar_imports/statistics_poland/StatisticsPoland_pvmap.csv \
  --output_path=statvar_imports/statistics_poland/test/StatisticsPoland_output \
  --config_file=statvar_imports/statistics_poland/StatisticsPoland_metadata.csv \
  --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf
```
**For Main data run**
```bash
python3 tools/statvar_importer/stat_var_processor.py \
  --input_data='statvar_imports/statistics_poland/source_files/*.csv' \
  --pv_map=statvar_imports/statistics_poland/StatisticsPoland_pvmap.csv \
  --output_path=statvar_imports/statistics_poland/StatisticsPoland_output \
  --config_file=statvar_imports/statistics_poland/StatisticsPoland_metadata.csv \
  --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf
```

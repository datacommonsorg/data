# Norway Demographics Dataset
## Overview
This dataset provides foundational demographic and socio-economic statistics for Norway, sourced directly from official national datasets.

## Data Source

**Source URL:**
https://www.ssb.no/en/statbank/table/07459/

The data comes from Statistics Norway (SSB) and includes comprehensive demographic variables such as population counts, age distributions, and other census-related metrics.

## How To Download Input Data
To download the data, you'll need to use the provided download script data_download.py. This script fetches live data from the SSB API to generate Norway_input.csv which is our input data.

type of place: AdministrativeArea1.

statvars: Demographics

years: 1986 to 2040.

## Processing Instructions
To process the Norway Census data and generate statistical variables, use the following command from the "data" directory:

**Download Input File**
 ```bash
 python3 statvar_imports/norway_census/data_download.py
```
**For Test Data Run**
```bash
python3 tools/statvar_importer/stat_var_processor.py \
  --input_data=statvar_imports/norway_census/test/Norway_input.csv \
  --pv_map=statvar_imports/norway_census/Norway_pvmap.csv \
  --output_path=statvar_imports/norway_census/test/Norway_output \
  --config_file=statvar_imports/norway_census/Norway_metadata.csv \
  --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf
```
**For Main data run**
```bash
python3 tools/statvar_importer/stat_var_processor.py \
  --input_data=statvar_imports/norway_census/Norway_input.csv \
  --pv_map=statvar_imports/norway_census/Norway_pvmap.csv \
  --output_path=statvar_imports/norway_census/Norway_output \
  --config_file=statvar_imports/norway_census/Norway_metadata.csv \
  --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf
```

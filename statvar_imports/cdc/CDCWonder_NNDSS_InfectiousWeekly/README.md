# CDCWonder_NNDSS_Infectious_Weekly

## Overview
Notifiable Infectious Diseases Data: Weekly tables from CDC WONDER which has the incident counts of different infectious diseases per week that are reported by the 50 states, New York City, the District of Columbia, and the U.S. territories.

## Data Source
**Source URL:**
`https://data.cdc.gov/api/views/x9gk-5huc/rows.csv?accessType=DOWNLOAD&api_foundry=true`

## How To Download Input Data
To download and process the data, you'll need to run the provided preprocess script, `preprocess.py`. This script will automatically create an "input_files" folder where you should place the file to be processed.By using this script, we are creating one more columns in the input files such as 'observationDate'. 

statvars: Demographics

## Download the data: 
For download and preprocess the source data, run:
```python3 preprocess.py```

## Processing Instructions
To process  data and generate statistical variables, use the following command from the "data" directory:

**For Test Data Run**
```
python3 tools/statvar_importer/stat_var_processor.py \
  --input_data=statvar_imports/cdc/CDCWonder_NNDSS_InfectiousWeekly/testdata/NNDSS_Weekly_Data.csv \
  --pv_map=statvar_imports/cdc/CDCWonder_NNDSS_InfectiousWeekly/nndss_weekly_pvmap.csv \
  --config_file=statvar_imports/cdc/CDCWonder_NNDSS_InfectiousWeekly/nndss_weekly_metadata.csv \
  --output_path=statvar_imports/cdc/CDCWonder_NNDSS_InfectiousWeekly/testdata/nndss_weekly_output 
```

**For Main data run**
```bash
python3 tools/statvar_importer/stat_var_processor.py \
  --input_data=statvar_imports/cdc/CDCWonder_NNDSS_InfectiousWeekly/input_files/NNDSS_Weekly_Data.csv \
  --pv_map=statvar_imports/cdc/CDCWonder_NNDSS_InfectiousWeekly/nndss_weekly_pvmap.csv \
  --config_file=statvar_imports/cdc/CDCWonder_NNDSS_InfectiousWeekly/nndss_weekly_metadata.csv \
  --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf \
  --output_path=statvar_imports/cdc/CDCWonder_NNDSS_InfectiousWeekly/output/nndss_weekly_output
```

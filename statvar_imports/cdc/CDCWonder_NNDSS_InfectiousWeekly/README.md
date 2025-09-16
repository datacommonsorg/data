# Commerce_NTIA

- source:  `https://data.cdc.gov/api/views/x9gk-5huc/rows.csv?accessType=DOWNLOAD&api_foundry=true`

- Notifiable Infectious Diseases Data: Weekly tables from CDC WONDER which has the incident counts of different infectious diseases per week that are reported by the 50 states, New York City, the District of Columbia, and the U.S. territories.

- how to download data: 
    To download and process the data, you'll need to run the provided preprocess script, `preprocess.py`. This script will automatically create an "input_files" folder where you should place the file to be processed.
    By using this script, we are creating one more columns in the input files such as 'observationDate'. 


- statvars: Demographics

### How to run:

```
python3 stat_var_processor.py 
--input_data='../../statvar_imports/cdc/CDCWonder_NNDSS_InfectiousWeekly/<input_file.csv>' 
--pv_map='../../statvar_imports/cdc/CDCWonder_NNDSS_InfectiousWeekly/<filename of metadata.csv>' --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf 
--output_path='../../statvar_imports/cdc/CDCWonder_NNDSS_InfectiousWeekly/<output_folder_name>/<filename>'
```

#### Download the data: 

For download and preprocess the source data, run:
`python3 preprocess.py`

Notes: 
Files will be downloaded inside "input_files" folder (input_files/raw.csv).


#### Process the data:

Execute the script inside the folder `/data/tools/statvar_importer/`

```
python3 stat_var_processor.py 
--input_data=../../statvar_imports/cdc/CDCWonder_NNDSS_InfectiousWeekly/input_files/rows.csv 
--pv_map=../../statvar_imports/cdc/CDCWonder_NNDSS_InfectiousWeekly/nndss_weekly_pvmap.csv 
--config_file=../../statvar_imports/cdc/CDCWonder_NNDSS_InfectiousWeekly/nndss_weekly_metadata.csv --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf 
--output_path=../../statvar_imports/cdc/CDCWonder_NNDSS_InfectiousWeekly/nndss_weekly/output
```

```
python3 stat_var_processor.py 
--input_data=../../statvar_imports/cdc/CDCWonder_NNDSS_InfectiousWeekly/input_files/rows.csv 
--pv_map=../../statvar_imports/cdc/CDCWonder_NNDSS_InfectiousWeekly/nndss_weekly_pvmap.csv 
--config_file=../../statvar_imports/cdc/CDCWonder_NNDSS_InfectiousWeekly/nndss_weekly_metadata.csv --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf 
--output_path=../../statvar_imports/dc/CDCWonder_NNDSS_InfectiousWeekly/nndss_weekly/output
```
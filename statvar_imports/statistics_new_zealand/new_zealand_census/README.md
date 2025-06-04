# New_Zealand_Census

- source: https://www.stats.govt.nz/large-datasets/csv-files-for-download/ 

- how to download data: Download script (download_script.py).
    To download the data, you'll need to use the provided download script, download_script.py. This script will automatically create an "input_files" folder where you should place the file to be processed. The script also requires a configuration file (config.py) to function correctly. Future urls can be added in the same config.py file.

- type of place: Country, district and city level.

- statvars: Demographics and Subnational

- years: 1991 to 2023.

- place_resolution: Places resolved to wikidataId in place_resolver sheet separately.

### How to run:

`python3 stat_var_processor.py --existing_statvar_mcf=stat_vars.mcf --input_data='<input_file>.csv' --pv_map='data/statvar_imports/statistics_new_zealand/new_zealand_census/<filename of pvmap.csv> --places_resolved_csv='data/statvar_imports/statistics_new_zealand/new_zealand_census/<filename of places_resolved_csv.csv>' --config_file='data/statvar_imports/statistics_new_zealand/new_zealand_census/<filename of metadata.csv>' --output_path='data/statvar_imports/statistics_new_zealand/new_zealand_census/<output_folder_name>/<filename>`

#### Example
#### Download : 
`python3 download_script.py`
Notes: Files will be downloaded inside "input_files" folder.
#### Processing
National:
`python3 stat_var_processor.py --existing_statvar_mcf=stat_vars.mcf --input_data='data/statvar_imports/statistics_new_zealand/new_zealand_census/input_files/Summary-figures-for-the-NZ-population-1991-2023.xlsx' --pv_map='data/statvar_imports/statistics_new_zealand/new_zealand_census/national_pvmap.csv' --config_file='data/statvar_imports/statistics_new_zealand/new_zealand_census/national_metadata.csv' --output_path='data/statvar_imports/statistics_new_zealand/new_zealand_census/output_files/nzl_national_output`
Subnational:
`python3 stat_var_processor.py --existing_statvar_mcf=stat_vars.mcf --input_data='data/statvar_imports/statistics_new_zealand/new_zealand_census/input_files/snpe-at30june21-population-table.csv' --pv_map='data/statvar_imports/statistics_new_zealand/new_zealand_census/subnational_pvmap.csv' --config_file='data/statvar_imports/statistics_new_zealand/new_zealand_census/subnational_metadata.csv' --places_resolved_csv='data/statvar_imports/statistics_new_zealand/new_zealand_census/subnational_places_resolved_csv.csv' --output_path='data/statvar_imports/statistics_new_zealand/new_zealand_census/output_files/nzl_subnational_output`

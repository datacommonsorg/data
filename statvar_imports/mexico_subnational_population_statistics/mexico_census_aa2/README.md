# MexicoCensus_AA2

- source: https://data.humdata.org/dataset/cod-ps-mex/ 

- how to download data: Download script (mexico_download.py).
    To download the data, you'll need to use the provided download script, mexico_download.py. This script will automatically create an "input_files" folder where you should place the file to be processed. The script also requires a configuration file (config.py) to function correctly. Future urls can be added in the same config.py file.

- type of place: Country (Administrative Area 0), Administrative Area 1, and Administrative Area 2 levels.

- statvars: Demographics and Subnational.

- years: 2021 to 2024.

- place_resolution: Places resolved to wikidataId in place_resolver sheet separately.

### How to run:

`python3 stat_var_processor.py --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf --input_data='<input_file>.csv' --pv_map='data/statvar_imports/mexico_subnational_population_statistics/mexico_census_aa2/<filename of pvmap.csv>' --places_resolved_csv='data/statvar_imports/mexico_subnational_population_statistics/mexico_census_aa2/<filename of places_resolved_csv.csv>' --config_file='data/statvar_imports/mexico_subnational_population_statistics/mexico_census_aa2/<filename of metadata.csv>' --output_path='data/statvar_imports/mexico_subnational_population_statistics/mexico_census_aa2/<output_folder_name>/<filename>' --output_counters='data/statvar_imports/mexico_subnational_population_statistics/mexico_census_aa2/counters/<filename of counters.csv>'`


#### Example
#### Download : 
`python3 mexico_download.py`
Notes: Files will be downloaded inside "input_files" folder.
#### Processing
For Administrative Area 0 (AA0):
`python3 stat_var_processor.py --input_data=/data/statvar_imports/mexico_subnational_population_statistics/mexico_census_aa2/input_files/mex_admpop_adm0_*.csv --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf --pv_map=/data/statvar_imports/mexico_subnational_population_statistics/mexico_census_aa2/mexico_pvmap_adm0.csv --config_file=/data/statvar_imports/mexico_subnational_population_statistics/mexico_census_aa2/mexico_metadata.csv --places_resolved_csv=/data/statvar_imports/mexico_subnational_population_statistics/mexico_census_aa2/mexico_places.csv --output_path='/data/statvar_imports/mexico_subnational_population_statistics/mexico_census_aa2/output_files/mexico_output_aa0' --output_counters=/data/statvar_imports/mexico_subnational_population_statistics/mexico_census_aa2/counters/mexico_census_data_counters_0.csv`

For Administrative Area 1 (AA1):
`python3 stat_var_processor.py --input_data=/data/statvar_imports/mexico_subnational_population_statistics/mexico_census_aa2/input_files/mex_admpop_adm1_*.csv --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf --pv_map=/data/statvar_imports/mexico_subnational_population_statistics/mexico_census_aa2/mexico_pvmap_aa1.csv --config_file=/data/statvar_imports/mexico_subnational_population_statistics/mexico_census_aa2/mexico_metadata.csv --places_resolved_csv=/data/statvar_imports/mexico_subnational_population_statistics/mexico_census_aa2/mexico_places.csv --output_path='/data/statvar_imports/mexico_subnational_population_statistics/mexico_census_aa2/output_files/mexico_output_aa1' --output_counters=/data/statvar_imports/mexico_subnational_population_statistics/mexico_census_aa2/counters/mexico_census_data_counters_1.csv`

For Administrative Area 2 (AA2):
`python3 stat_var_processor.py --input_data=/data/statvar_imports/mexico_subnational_population_statistics/mexico_census_aa2/input_files/mex_admpop_adm2_*.csv --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf --pv_map=/data/statvar_imports/mexico_subnational_population_statistics/mexico_census_aa2/mexico_pvmap_aa2.csv --config_file=/data/statvar_imports/mexico_subnational_population_statistics/mexico_census_aa2/mexico_metadata.csv --places_resolved_csv=/data/statvar_imports/mexico_subnational_population_statistics/mexico_census_aa2/mexico_places.csv --output_path='/data/statvar_imports/mexico_subnational_population_statistics/mexico_census_aa2/output_files/mexico_output_aa2' --output_counters=/data/statvar_imports/mexico_subnational_population_statistics/mexico_census_aa2/counters/mexico_census_data_counters_2.csv`


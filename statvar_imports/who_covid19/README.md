# covid_Covid_19 Dataset

- source: https://data.who.int/dashboards/covid19/cases?n=c
    
- type of place: Country Data

- statvars: Health

- years: 2021 to 2025

- place_resolution: manually.

### Release Frequency: P1Y

### How to run:

- To download the input file

   `bash download.sh`

- StatVar Script

`python3 ../../tools/statvar_importer/stat_var_processor.py --input_data=input_files/COV_VAC_UPTAKE_2021_2023.csv --pv_map=pvmap/COV_VAC_UPTAKE_2021_2023_pvmap.csv --existing_statvar_mcf=stat_vars.mcf  --config_file=common_metadata.csv  --output_path=output/COV_VAC_UPTAKE_2021_2023 `
    
#### Refresh type :Fully Autorefresh 


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

`python3 ../../tools/statvar_importer/stat_var_processor.py --input_data=input_files/COV_VAC_UPTAKE_2021_2023.csv --pv_map=pvmap/COV_VAC_UPTAKE_2021_2023_pvmap.csv --existing_statvar_mcf=stat_vars.mcf  --config_file=common_metadata.csv  --output_path=output/COV_VAC_UPTAKE_2021_2023`

`python3 ../../tools/statvar_importer/stat_var_processor.py --input_data=input_files/COV_VAC_UPTAKE_2024.csv --pv_map=pvmap/COV_VAC_UPTAKE_2024_pvmap.csv --existing_statvar_mcf=stat_vars.mcf --config_file=common_metadata.csv  --output_path=output/COV_VAC_UPTAKE_2024`

`python3 ../../tools/statvar_importer/stat_var_processor.py --input_data=input_files/WHO-COVID-19-global-monthly-death-by-age-data.csv --pv_map=pvmap/WHO-COVID-19-global-monthly-death-by-age-data_pvmap.csv  --config_file=common_metadata.csv --statvar_dcid_remap_csv=remap/WHO-COVID-19-global-monthly-death-by-age-data_remap.csv --output_path=output/death_by_age`

`python3 ../../tools/statvar_importer/stat_var_processor.py --input_data=input_files/WHO-COVID-19-global-daily-data.csv --pv_map=pvmap/WHO-COVID-19-global-daily-data_pvmap.csv --existing_statvar_mcf=stat_vars.mcf --places_resolved_csv=place_resolver.csv --config_file=common_metadata.csv  --output_path=output/global_daily_data`

`python3 ../../tools/statvar_importer/stat_var_processor.py --input_data=input_files/WHO-COVID-19-global-hosp-icu-data.csv --pv_map=pvmap/WHO-COVID-19-global-hosp-icu-data_pvmap.csv --existing_statvar_mcf=stat_vars.mcf --config_file=common_metadata.csv --statvar_dcid_remap_csv=remap/WHO-COVID-19-global-hosp-icu-data_remap.csv --output_path=output/global_hosp_icu_data`
    
#### Refresh type: Fully Autorefresh 


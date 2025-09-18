# Urban Florida Education

- source: https://www.flbog.edu/resources/data-analytics/dashboards/

- how to download data: Download script (download_script.py)
    
    The data is downloaded based on urls and it is processed to drop the institution and aggregate the data on course level.

- type of place: Country

- statvars: Demographics,Education

- years: 2019 to 2024

- place_resolution:Place is directly assigned in pv_map.


### How to run:

- To download the input file

    `python3 download_script.py`

- StatVar Script

    `python3 ../../tools/statvar_importer/stat_var_processor.py  --input_data=input_files/DeathByCause.csv --pv_map=configs/deathbycause_pvmap.csv --config_file=configs/common_metadata.csv --output_path=output_path/DeathByCause --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf`
    
    
#### Fully Autorefresh: 

Trigger `data/import-automation/executor/run_import.sh` manually for test/prod ingestion

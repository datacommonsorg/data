# Singapore Census Autorefresh

- source: https://tablebuilder.singstat.gov.sg/

- how to download data: Download script (download_and_process.py)
    
    The data is downloaded based on urls and it is processed to give header to the data according to the source.
    This script will automatically create an "input" folder where you should place the file to be processed.

- type of place: Country

- statvars: Demographics, Health

- years: 1969 to 2025

- place_resolution:Place is directly assigned in pv_map.


### How to run:

- To download the input file

    `python3 download_and_process.py`

- StatVar Script

    `python3 "../../tools/statvar_importer/stat_var_processor.py  --input_data=input_files/DeathByCause_T3.csv --pv_map=configs/deathbycause_pvmap.csv --config_file=configs/deathbycause_metadata.csv --output_path=output_path/DeathByCause --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf"`

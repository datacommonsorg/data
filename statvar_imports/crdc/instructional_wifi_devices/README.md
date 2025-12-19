# crdc_instructional_wifi_devices Dataset

- source: https://civilrightsdata.ed.gov/data
    
- type of place: School Data

- statvars: Education

- years: 2021 to 2022

- place_resolution: manually.

### Release Frequency: P1Y

### How to run:

- To download the input file

   `python3 download.py`

- StatVar Script

`python3 ../../../tools/statvar_importer/stat_var_processor.py --input_data=input_files/*.csv --pv_map=common_pvmap.csv --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf --config_file=common_metadata.csv  --output_path=output/instructional_wifi_devices`

#### Refresh type: Fully Autorefresh 


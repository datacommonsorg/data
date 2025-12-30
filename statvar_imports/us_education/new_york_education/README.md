# Urban NewYork Education

- source: https://data.cityofnewyork.us/browse?category=Education

- how to download data: Download script (download.py)
    
    The data is downloaded based on urls mentioned in config.json

- type of place: City

- statvars: Demographics,Education

- years: 2006 to 2023

- place_resolution: manually.

### Release Frequency: P1Y

### How to run:

- To download the input file

    `python3 download.py`

- StatVar Script

    `python3 ../../../tools/statvar_importer/stat_var_processor.py --input_data=input_files/english/*.csv --pv_map=NY_common_pvmap_english.csv --existing_statvar_mcf=stat_vars.mcf --config_file=NY_common_metadata.csv --places_resolved_csv=Urban_NY_Place_resolver.csv --output_path=output/english`
    
    
#### Refresh type :Semi Autorefresh 

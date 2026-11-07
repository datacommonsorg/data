# Nigeria Census Data from Opendata

- source: https://nigeria.opendataforafrica.org/data/#menu=topic 

- how to download data: Manual download from source based on filter - `Topics`.

- type of place: Country and AdministrativeArea1.

- statvars: Demographics, Health, Crime and Economy

- years: 1991 to 2018

- place_resolution: State places are resolved based on place name.

### How to run:


`python3 stat_var_processor.py --existing_statvar_mcf=stat_vars.mcf --input_data=<input_file>.csv --pv_map=statvar_imports/opendata/cpi/Nigeria_CPI_pvmap.csv --config=statvar_imports/opendata/cpi/Nigeria_CPI_metadata.csv --output_path=--output_path=<filepath/filename>`


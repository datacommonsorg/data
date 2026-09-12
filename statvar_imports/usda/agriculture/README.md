# USDA PSD data

- source: https://apps.fas.usda.gov/psdonline/app/index.html#/app/downloadshttps://apps.fas.usda.gov/psdonline/app/index.html#/app/downloads 

- how to download data: Manual download from source.

- type of place: Countries.

- statvars: Agriculture

- years: 1960 to 2023

- place_resolution: Places are resolved based on place name.

### How to run:


`python3 stat_var_processor.py --existing_statvar_mcf=stat_vars.mcf --input_data=<input_file>.csv --pv_map=statvar_imports/opendata/cpi/Nigeria_CPI_pvmap.csv --config=statvar_imports/opendata/cpi/Nigeria_CPI_metadata.csv --output_path=--output_path=<filepath/filename>`

# New Jersey - US Education Data

- source: https://rc.doe.state.nj.us/download 

- how to download data: Manual download from source based on filter - `School Year`.

- type of place: Country and AdministrativeArea1.

- statvars: Education

- years: 2017 to 2023

- place_resolution: State places are resolved based on name.

### How to run:

`python3 stat_var_processor.py --existing_statvar_mcf=stat_vars.mcf --input_data=<input_file>.csv --pv_map=statvar_imports/brazil_VISDATA/FoodBasketDistribution/pv_map/<filename>_pvmap.csv --places_resolved_csv=statvar_imports/brazil_visdata/Brazil_Places_Resolved.csv --config=statvar_imports/brazil_VISDATA/FoodBasketDistribution/common_metadata.csv --output_path=--output_path=<filepath/filename>`

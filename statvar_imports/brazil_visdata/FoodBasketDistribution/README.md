# Brazil - Food Distribution Program

- source: https://aplicacoes.cidadania.gov.br/vis/data3/data-explorer.php, 

- how to download data: Manual download from source based on filter - `Food Distribution Action to Specific Population Groups`.

- type of place: Country and AdministrativeArea1.

- statvars: Demographics, Household

- years: 2021 to 2023

- place_resolution: State places are resolved based on name.

### How to run:

`python3 stat_var_processor.py --existing_statvar_mcf=stat_vars.mcf --input_data=<input_file>.csv --pv_map=statvar_imports/brazil_VISDATA/FoodBasketDistribution/pv_map/<filename>_pvmap.csv --places_resolved_csv=statvar_imports/brazil_visdata/Brazil_Places_Resolved.csv --config=statvar_imports/brazil_VISDATA/FoodBasketDistribution/common_metadata.csv --output_path=--output_path=<filepath/filename>`

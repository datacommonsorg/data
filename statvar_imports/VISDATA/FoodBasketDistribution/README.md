# Brazil - Food Distribution Program

- source: https://aplicacoes.cidadania.gov.br/vis/data3/data-explorer.php, 

- how to download data: Manual download from source based on filter - `Food Distribution Action to Specific Population Groups`.

- type of place: Country and AdministrativeArea1.

- statvars: Demographics, Household

- years: 2021 to 2023

- place_resolution: State places are resolved based on name.

### How to run:

`python3 stat_var_processor.py --existing_statvar_mcf=stat_vars.mcf --input_data=data/statvar_imports/VISDATA/FoodBasketDistribution/test_data/sample_input/MunicipalFoodBasket_RecycledMaterialCollectorFamily_data.csv --pv_map=data/statvar_imports/VISDATA/FoodBasketDistribution/test_data/sample_input/MunicipalFoodBasket_RecycledMaterialCollectorFamily_pvmap.csv --config=data/statvar_imports/VISDATA/FoodBasketDistribution/test_data/sample_input/MunicipalFoodBasket_RecycledMaterialCollectorFamily_metadata.csv --output_path=data/statvar_imports/VISDATA/FoodBasketDistribution/test_data/sample_output/MunicipalFoodBasket_RecycledMaterialCollectorFamily`

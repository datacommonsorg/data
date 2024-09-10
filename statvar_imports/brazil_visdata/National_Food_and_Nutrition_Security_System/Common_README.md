###  National_Food_and_Nutrition_Security_System

- import_name: "National_Food_and_Nutrition_Security_System"

- source: https://aplicacoes.cidadania.gov.br/vis/data3/data-explorer.php
          https://dados.gov.br/dados/conjuntos-dados/sistema-de-vigilancia-alimentar-e-nutricional---sisvan

- how to download data: Manual download from source based on filter - `Municipalities that joined the National Food Security System (SISAN) - Accumulated` and                                                                   `Municipalities that have a Food and Nutritional Security Plan - Accumulated`

- place_resolution: Municipality codes of Brazil. 

- statvars: Municipality
  
- years: 2013 to 2021

- type of place: AA ,AA1, AA2, City, Country.

### How to run:

`python3 stat_var_processor.py --existing_statvar_mcf=stat_vars.mcf --input_data=<input_file>.csv --pv_map=statvar_imports/brazil_visdata/<filepath>/pv_map.csv --places_resolved_csv=statvar_imports/brazil_visdata/National_Food_and_Nutrition_Security_System/Brazil_MunicipalityCodes_Places_Resolved.csv --config=<filepath/filename>.csv --output_path=<filepath/filename>`


   


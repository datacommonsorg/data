###  National_Food_and_Nutrition_Security_System

- import_name: "National_Food_and_Nutrition_Security_System"

- source: https://aplicacoes.cidadania.gov.br/vis/data3/data-explorer.php
          https://dados.gov.br/dados/conjuntos-dados/sistema-de-vigilancia-alimentar-e-nutricional

- how to download data: Manual download from source based on filter - `Municipalities that joined the National Food Security System (SISAN) - Accumulated` and  `Municipalities that have a Food and Nutritional Security Plan - Accumulated`

- place_resolution: Municipality codes of Brazil. 

- statvars: Municipality
  
- years: 2013 to 2021

- type of place: AA ,AA1, AA2, City, Country.

### How to run:
`python3 stat_var_processor.py --existing_statvar_mcf=stat_vars.mcf --input_data=<input_file>.csv --pv_map=statvar_imports/brazil_visdata/<filepath>/pv_map.csv --places_resolved_csv=statvar_imports/brazil_visdata/National_Food_and_Nutrition_Security_System/Brazil_MunicipalityCodes_Places_Resolved.csv --config=<filepath/filename>.csv --output_path=<filepath/filename>`

#### Example
`python3 stat_var_processor.py --input_data=statvar_imports/brazil_visdata/National_Food_and_Nutrition_Security_System/Food_and_Nutritional_Security/test_data/sample_input/Food_and_Nutritional_Security_test_data.csv --pv_map=statvar_imports/brazil_visdata/National_Food_and_Nutrition_Security_System/Food_and_Nutritional_Security/pv_map.csv --places_resolved_csv=statvar_imports/brazil_visdata/National_Food_and_Nutrition_Security_System/Brazil_MunicipalityCodes_Places_Resolved.csv --config=statvar_imports/brazil_visdata/National_Food_and_Nutrition_Security_System/Food_and_Nutritional_Security/metadata.csv --output_path=statvar_imports/brazil_visdata/National_Food_and_Nutrition_Security_System/Food_and_Nutritional_Security/test_data/sample_output/Food_and_Nutritional_Security_test_data`


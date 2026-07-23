# Brazil - Food Acquisition Program

- source: https://aplicacoes.cidadania.gov.br/vis/data3/data-explorer.php, 

- how to download data: Manual download from source based on filter - `Brazil Food Acquisition Program Action to Specific Population Groups`.

- type of place: Country and Municipality level.

- statvars: Demographics, Household

- years: 2011 to 2023

- place_resolution: Places resolved based on municipalty code.
- License: 

### How to run:

`python3 stat_var_processor.py --existing_statvar_mcf=stat_vars.mcf --input_data=data/statvar_imports/brazil_visdata/FoodAcquisitionProgram/test_data/sample_input/<input_file>.csv --pv_map=/data/statvar_imports/brazil_visdata/FoodAcquisitionProgram/pv_map/<filename>_pvmap.csv --config=data/statvar_imports/brazil_visdata/FoodAcquisitionProgram/pv_map/<metadata-file-name>.csv --output_path=data/statvar_imports/brazil_visdata/FoodAcquisitionProgram/test_data/sample_output/<Filename>


for example:
=============

python3 stat_var_processor.py --existing_statvar_mcf=stat_vars.mcf --input_data='data/statvar_imports/brazil_visdata/FoodAcquisitionProgram/test_data/sample_input/Programa_de_Aquisicao_de_Alimentos_PAA_Execucao_Geral_(quantidade_de_agricultores_e_recursos_pagos_ano_a_ano) - data.csv'   --pv_map='data/statvar_imports/brazil_visdata/FoodAcquisitionProgram/pv_map/Programa_de_Aquisicao_de_Alimentos_PAA_Execucao_Geral_(quantidade_de_agricultores_e_recursos_pagos_ano_a_ano) - pvmap.csv'    --config='data/statvar_imports/brazil_visdata/FoodAcquisitionProgram/pv_map/Programa_de_Aquisicao_de_Alimentos_PAA_Execucao_Geral_(quantidade_de_agricultores_e_recursos_pagos_ano_a_ano) - metadata.csv'   --output_path='data/statvar_imports/brazil_visdata/FoodAcquisitionProgram/test_data/sample_output/'

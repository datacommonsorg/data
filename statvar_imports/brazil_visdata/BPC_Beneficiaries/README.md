# Brazil - BPC beneficiaries in the Single Registry

- source: https://aplicacoes.cidadania.gov.br/vis/data3/data-explorer.php, 

- how to download data: Manual download from source based on filter - `BPC beneficiaries in the Single Registry`.

- type of place: Country and AdministrativeArea1.

- statvars: Demographics, Household

- years: 2019 to 2023

- place_resolution: State places are resolved based on name.

### How to run:

`python3 stat_var_processor.py --input_data=<input_file>.csv --pv_map=statvar_imports/brazil_visdata/BPC_Beneficiaries/pv_map/<filename>_pvmap.csv --places_resolved_csv=statvar_imports/brazil_visdata/BPC_Beneficiaries/Municipality_Beneficiarios_do BPC_no_Cadastro_Unico - resolved_places.csv --config=statvar_imports/brazil_visdata/BPC_Beneficiaries/config_metadata/Municipality_Beneficio_de_Prestacao_Continuada_BPC_por_municipio_pagador_3 - metadata.csv --output_path=<filepath/filename>`

#### Example
python3 tools/statvar_importer/stat_var_processor.py --input_data='/usr/local/google/home/shamimansari/Brazil_BPC_Beneficiaries16062025/data/statvar_imports/brazil_visdata/BPC_Beneficiaries/test_data/sample_input/Municipality_Renda_Mensal_Vitalícia_RMV_por_município_pagador_4 - data.csv'    --pv_map='/usr/local/google/home/shamimansari/Brazil_BPC_Beneficiaries16062025/data/statvar_imports/brazil_visdata/BPC_Beneficiaries/pv_map/Municipality_Renda_Mensal_Vitalícia_RMV_por_município_pagador_1 - pvmap.csv'     --config_file='/usr/local/google/home/shamimansari/Brazil_BPC_Beneficiaries16062025/data/statvar_imports/brazil_visdata/BPC_Beneficiaries/config_metadata/Municipality_Beneficio_de_Prestacao_Continuada_BPC_por_municipio_pagador_3 - metadata.csv' --places_resolved_csv='/usr/local/google/home/shamimansari/Brazil_BPC_Beneficiaries16062025/data/statvar_imports/brazil_visdata/BPC_Beneficiaries/Municipality_Beneficiarios_do BPC_no_Cadastro_Unico - resolved_places.csv'     --output_path='/usr/local/google/home/shamimansari/Brazil_BPC_Beneficiaries16062025/data/statvar_imports/brazil_visdata/BPC_Beneficiaries/test_data/sample_output/Municipality_Renda_Mensal_Vitalícia_RMV_por_município_pagador_4'  --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf

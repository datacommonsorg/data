# Brazil - Unified Social Assistance System

- source: https://aplicacoes.cidadania.gov.br/vis/data3/data-explorer.php, 

- how to download data: Manual download from source based on filter - `Unified Social Assistance System`

- type of place: Country and AdministrativeArea2/City

- statvars: Demographics, Household

- years: 2005 to 2024

- place_resolution: State places are resolved based on name and Municipality places are resolved based on `brazilianMunicipalityCode`

### How to run:
`python3 statvar_processory.py --input_data=<input_file>.csv --pv_map=statvar_imports/brazil_visdata/suas/<filename>_pvmap.csv --places_resolved_csv=statvar_imports/brazil_visdata/Brazil_Places_Resolved.csv --config=statvar_imports/brazil_visdata/suas/CommunityServices_Commonpvmap_metadata.csv --output_path=<filepath/filename>`

#### Example
1. Country Data

`python3 stat_var_processor.py --input_data='statvar_imports/brazil_visdata/suas/test_data/sample_input/Centros_de_Referência_em_Assistência_Social_CRAS_com_cofinanciamento_do_Ministério_da_Cidadania_Acumulado_data.csv'  --pv_map='statvar_imports/brazil_visdata/suas/CommunityServices_Commonpvmap_pvmap.csv'  --config='statvar_imports/brazil_visdata/suas/CommunityServices_Commonpvmap_metadata.csv'  --output_path=statvar_imports/brazil_visdata/suas/test_data/sample_output/CRAS`

2. Municipal Data

`python3 stat_var_processor.py --input_data='statvar_imports/brazil_visdata/suas/test_data/sample_input/Municipal Centros de Referência em Assistência Social CRAS com cofinanciamento do Ministério da Cidadania Acumulado_data.csv' --pv_map='statvar_imports/brazil_visdata/suas/Municipal_CommunityServices_Commonpvmap_pvmap.csv'  --places_resolved_csv='statvar_imports/brazil_visdata/Brazil_Places_Resolved.csv'   --config='statvar_imports/brazil_visdata/suas/CommunityServices_Commonpvmap_metadata.csv'  --output_path=statvar_imports/brazil_visdata/suas/test_data/sample_output/Municipal_CRAS`

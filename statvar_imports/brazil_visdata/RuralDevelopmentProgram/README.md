# Brazil - Rural Development Program

- source: https://aplicacoes.cidadania.gov.br/vis/data3/data-explorer.php, 

- how to download data: Manual download from source based on filter - `Rural Productive Activities Promotion Program`.

- type of place: Country, AdministrativeArea1 and AdministrativeArea2/City

- statvars: Demographics, Household

- years: 2012 to 2023

- place_resolution: State places are resolved based on name and Municipality places are resolved based on `brazilianMunicipalityCode`


### How to run:
`python3 statvar_processory.py --existing_statvar_mcf=stat_vars.mcf --input_data=<input_file>.csv --pv_map=/usr/local/google/home/chharish/VISDATA/data/statvar_imports/brazil_VISDATA/RuralDevelopmentProgram/pv_map/<filename>_pvmap.csv  --config=/usr/local/google/home/chharish/VISDATA/data/statvar_imports/brazil_VISDATA/RuralDevelopmentProgram/common_metdata.csv --output_path=<filepath/filename>`
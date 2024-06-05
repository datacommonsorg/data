# Brazil - Rural Development Program

- source: https://aplicacoes.cidadania.gov.br/vis/data3/data-explorer.php, 

- how to download data: Manual download from source based on filter - `Rural Productive Activities Promotion Program`.

- type of place: Country, AdministrativeArea1 and AdministrativeArea2/City

- statvars: Demographics, Household

- years: 2012 to 2023

- place_resolution: State places are resolved based on name and Municipality places are resolved based on `brazilianMunicipalityCode`


### How to run:
`python statvar_processory.py --input_data=statvar_imports/VISDATA/RuralDevelopmentProgram/test_data/sample_input/FinancialResources_Beneficiary_RuralDevelopmentProgram_data.csv --pv_map=statvar_imports/VISDATA/RuralDevelopmentProgram/test_data/sample_input/FinancialResources_Beneficiary_RuralDevelopmentProgram_pvmap.csv --config=statvar_imports/VISDATA/RuralDevelopmentProgram/test_data/sample_input/FinancialResources_Beneficiary_RuralDevelopmentProgram_metadata.csv`
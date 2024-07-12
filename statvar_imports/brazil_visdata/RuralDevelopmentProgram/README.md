# Brazil - Rural Development Program

- source: https://aplicacoes.cidadania.gov.br/vis/data3/data-explorer.php, 

- how to download data: Manual download from source based on filter - `Rural Productive Activities Promotion Program`.

- type of place: Country, AdministrativeArea1 and AdministrativeArea2/City

- statvars: Demographics, Household

- years: 2012 to 2023

- place_resolution: State places are resolved based on name and Municipality places are resolved based on `brazilianMunicipalityCode`


### How to run:
`python3 statvar_processory.py --input_data=<input_file>.csv --pv_map=statvar_imports/brazil_VISDATA/RuralDevelopmentProgram/pv_map/<filename>_pvmap.csv --places_resolved_csv=statvar_imports/brazil_visdata/Brazil_Places_Resolved.csv --config=statvar_imports/brazil_VISDATA/RuralDevelopmentProgram/common_metdata.csv --output_path=<filepath/filename>`

#### Example
`python3 stat_var_processor.py --input_data=/statvar_imports/brazil_visdata/RuralDevelopmentProgram/test_data/sample_input/FinancialResources_Beneficiary_RuralDevelopmentProgram_data.csv --pv_map=/statvar_imports/brazil_visdata/RuralDevelopmentProgram/pv_map/FinancialResources_Beneficiary_RuralDevelopmentProgram_pvmap.csv --places_resolved_csv=/statvar_imports/brazil_visdata/Brazil_Places_Resolved.csv --config=/statvar_imports/brazil_visdata/RuralDevelopmentProgram/common_metadata.csv --output_path=/statvar_imports/brazil_visdata/RuralDevelopmentProgram/test_data/sample_output/FinancialResources_Beneficiary_RuralDevelopmentProgram`

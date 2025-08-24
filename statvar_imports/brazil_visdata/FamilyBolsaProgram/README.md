# Brazil - Family Bolsa Program

- source: https://dados.gov.br/dados/conjuntos-dados/bolsa-familia---beneficios-basicos-e-variaveis


- how to download data: Manual download from source based on filter 

- type of place: Country and AdministrativeArea1.

- statvars: Demographics

- years: 2004 to 2024

- place_resolution: State places are resolved based on name.

### How to run:

`python3 stat_var_processor.py --input_data=<input_file>.csv --pv_map=statvar_imports/brazil_VISDATA/FamilyBolsaProgram/pvmap/<filename>.csv --places_resolved_csv=statvar_imports/brazil_visdata/Brazil_Places_Resolved.csv --config=statvar_imports/brazil_VISDATA/FamilyBolsaProgram/metadata.csv --output_path=--output_path=<filepath/filename>`

#### Example
`python3 stat_var_processor.py --input_data=/statvar_imports/brazil_visdata/FamilyBolsaProgram/test_data/sample_input/municipality_BolsaFamíliaProgram_Number_of_Benefitsbytypefrom2023.csv --pv_map=/statvar_imports/brazil_visdata/FamilyBolsaProgram/pvmap/municipality_BolsaFamíliaProgram_Number_of_Benefitsbytypefrom2023 - pvmap.csv --places_resolved_csv=/statvar_imports/brazil_visdata/Brazil_Places_Resolved.csv --config=/statvar_imports/brazil_visdata/FamilyBolsaProgram/metadata.csv --output_path=/statvar_imports/brazil_visdata/FamilyBolsaProgram/test_data/sample_output/municipality_BolsaFamíliaProgram_Number_of_Benefitsbytypefrom2023`

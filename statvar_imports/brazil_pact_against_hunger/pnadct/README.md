# Brazil - Brazil Pact Against Hunger PNADCT


- source: https://sidra.ibge.gov.br/home/pnadct/brasil 

- how to download data: Manual download from source based on filter 

- type of place: Country and AdministrativeArea1.

- statvars: Economy

- years: 2012 to 2024

- place_resolution: State places are resolved based on name.

### How to run:

`python3 stat_var_processor.py --input_data=<filepath/filename> --pv_map=statvar_imports/brazil_pact_against_hunger/pnadct/pv_map.csv --places_resolved_csv=statvar_imports/brazil_pact_against_hunger/pnadct/Brazil_Places_Resolved.csv --config=statvar_imports/brazil_pact_against_hunger/pnadct/metadata.csv --output_path=<filepath/filename> --existing_statvar_mcf=stat_vars.mcf`

#### Example
`python3 stat_var_processor.py --input_data=/statvar_imports/brazil_pact_against_hunger/pnadct/test_data/sample_input/tabela5434.xlsx --pv_map=/statvar_imports/brazil_pact_against_hunger/pnadct/pv_map.csv --places_resolved_csv=/statvar_imports/brazil_pact_against_hunger/pnadct/Brazil_Places_Resolved.csv --config=/statvar_imports/brazil_pact_against_hunger/pnadct/metadata.csv --output_path=statvar_imports/brazil_pact_against_hunger/pnadct/test_data/sample_output/5434 --existing_statvar_mcf=stat_vars.mcf`


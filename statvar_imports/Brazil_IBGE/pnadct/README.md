# Brazilian Institute of Geography and Statistics (IBGE) : PNADCT


- source: https://sidra.ibge.gov.br/home/pnadct/brasil 

- how to download data: Manual download from source based on filter 

- type of place: Country and AdministrativeArea1.

- statvars: Economy

- years: 2012 to 2024

- place_resolution: State places are resolved based on name.

### How to run:

`python3 stat_var_processor.py --input_data=<filepath/filename> --pv_map=statvar_imports/Brazil_IBGE/pnadct/pvmap/<filename>.csv --places_resolved_csv=statvar_imports/Brazil_IBGE/pnadct/Brazil_Places_Resolved.csv --config=statvar_imports/Brazil_IBGE/pnadct/metadata.csv --output_path=<filepath/filename> --existing_statvar_mcf=stat_vars.mcf`

#### Example
`python3 stat_var_processor.py --input_data=/statvar_imports/Brazil_IBGE/pnadct/test_data/sample_input/tabela5434.xlsx --pv_map=/statvar_imports/Brazil_IBGE/pnadct/pvmap/tabela5434.csv --places_resolved_csv=/statvar_imports/Brazil_IBGE/pnadct/Brazil_Places_Resolved.csv --config=/statvar_imports/Brazil_IBGE/pnadct/metadata.csv --output_path=statvar_imports/Brazil_IBGE/pnadct/test_data/sample_output/5434 --existing_statvar_mcf=stat_vars.mcf`


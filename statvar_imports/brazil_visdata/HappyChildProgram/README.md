# Brazil - Single Registry

- source: https://aplicacoes.cidadania.gov.br/vis/data3/data-explorer.php, 

- how to download data: Manual download from source based on filter - `Happy Child Program`.

- type of place: Country, AA2.

- statvars: Demographics, Household

- years: 2018 to 2022

- place_resolution: State places are resolved based on name and Municipality places are resolved based on `brazilianMunicipalityCode`.

### How to run:

`python3 stat_var_processor.py --input_data=<input_file>.csv --config=statvar_imports/brazil_visdata/HappyChildProgram/common_metadata.csv --places_resolved_csv=statvar_imports/brazil_visdata/Brazil_Places_Resolved.csv --output_path=<filepath/filename>`

#### Example
`python3 stat_var_processor.py --input_data=statvar_imports/brazil_visdata/HappyChildProgram/test_data/sample_input/Brazil_Count_Individuals_HappyChildProgram_data.csv --config=statvar_imports/brazil_visdata/HappyChildProgram/common_metadata.csv --places_resolved_csv=/Users/sanikap/crash_pr/data/statvar_imports/brazil_visdata/HappyChildProgram/test_data/sample_output/Brazil_Count_Individuals_HappyChildProgram`
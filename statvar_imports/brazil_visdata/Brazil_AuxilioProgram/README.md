# Brazil - Auxílio Brasil Program (PAB)

- source: https://aplicacoes.cidadania.gov.br/vis/data3/data-explorer.php, 

- how to download data: Manual download from source based on filter - `Auxílio Brasil Program (PAB).

- type of place: Municipality and AdministrativeArea1.

- statvars: Demographics, Household

- years: 2021 to 2024

- place_resolution: State places are resolved based on name.

### How to run:

`python3 stat_var_processor.py --input_data=<input_file>.csv --pv_map=statvar_imports/brazil_VISDATA/Brazil_AuxilioProgram/pv_map/<filename>_pvmap.csv --places_resolved_csv=statvar_imports/brazil_visdata/Brazil_AuxilioProgram/Brazil_place_resolve_municipality - place_resolver.csv --config=statvar_imports/brazil_VISDATA/Brazil_AuxilioProgram/<filename>_metadata.csv --output_path=--output_path=<filepath/filename>`

#### Example
`python3 stat_var_processor.py --input_data='/statvar_imports/brazil_visdata/Brazil_AuxilioProgram/test_data/sample_input/Acompanhamento_Educacao_do_Programa_Auxilio_Brasil_(PAB)_-_Beneficiarios_de_4_a_5_anos_-_(Bimestral) - data.csv'  --pv_map='/statvar_imports/brazil_visdata/Brazil_AuxilioProgram/pv_map/Acompanhamento_Educacao_do_Programa_Auxilio_Brasil_(PAB)_-_Beneficiarios_de_4_a_5_anos_-_(Bimestral) - pvmap.csv'  --places_resolved_csv='statvar_imports/brazil_visdata/Brazil_AuxilioProgram/Brazil_place_resolve_municipality - place_resolver.csv'  --config='/statvar_imports/brazil_visdata/Brazil_AuxilioProgram/config_metadata/Acompanhamento_Educacao_do_Programa_Auxilio_Brasil_(PAB)_-_Beneficiarios_de_4_a_5_anos_-_(Bimestral) - metadata.csv'  --output_path='/statvar_imports/brazil_visdata/Brazil_AuxilioProgram/test_data/sample_output/<filename>.csv'`



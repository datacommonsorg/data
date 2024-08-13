# Brazil - Brazil Auxilio Program

- source: https://aplicacoes.cidadania.gov.br/vis/data3/data-explorer.php, 

- how to download data: Manual download from source based on filter - `Brazil Auxilio Program Action to Specific Population Groups`.

- type of place: Country and Municipality level.

- statvars: Demographics, Household

- years: 2021 to 2023

- place_resolution: Place resolution done by municipality code
   /data/statvar_imports/brazil_visdata/AuxilioProgram/Brazil_place_resolve_municipality - place_resolver.csv
- License: 

### How to run:

python3 stat_var_processor.py --existing_statvar_mcf=stat_vars.mcf --input_data=statvar_imports/brazil_visdata/AuxilioProgram/test_data/sample_input/<input_file>.csv --pv_map=statvar_imports/brazil_visdata/AuxilioProgram/pv_map/<filename>_pvmap.csv --config=statvar_imports/brazil_visdata/AuxilioProgram/pv_map/<metadata-file-name>.csv --output_path=statvar_imports/brazil_visdata/AuxilioProgram/test_data/sample_output/<Filename>


# Brazil - Gas Aid Program

- source: https://aplicacoes.cidadania.gov.br/vis/data3/data-explorer.php, 

- how to download data: Manual download from source based on filter - `Brazil Gas Aid Program Action to Specific Population Groups`.

- type of place: Country and Municipality level.

- statvars: Demographics, Household

- years: 2021 to 2024

- place_resolution: N/A
- License: 

### How to run:

python3 stat_var_processor.py --existing_statvar_mcf=stat_vars.mcf --input_data=statvar_imports/brazil_visdata/GasAidProgram/test_data/sample_input/<input_file>.csv --pv_map=statvar_imports/brazil_visdata/GasAidProgram/pv_map/<filename>_pvmap.csv --config=statvar_imports/brazil_visdata/GasAidProgram/pv_map/<metadata-file-name>.csv --output_path=statvar_imports/brazil_visdata/GasAidProgram/test_data/sample_output/<Filename>

### for example:

python3 stat_var_processor.py --existing_statvar_mcf=stat_vars.mcf --input_data='/statvar_imports/brazil_visdata/GasAidProgram/test_data/sample_input/Percentage_of_Single_Person_Families_served_by_the_Brazilian_Gas_Aid_Program - data.csv' --pv_map='/statvar_imports/brazil_visdata/GasAidProgram/pv_map/Percentage_of_Single_Person_Families_served_by_the_Brazilian_Gas_Aid_Program - pvmap.csv' --config='/statvar_imports/brazil_visdata/GasAidProgram/pv_map/Percentage_of_Single_Person_Families_served_by_the_Brazilian_Gas_Aid_Program - metadata.csv' --output_path=/test_data/sample_output/Percentage_of_Single_Person_Families_served_by_the_Brazilian_Gas_Aid_Program

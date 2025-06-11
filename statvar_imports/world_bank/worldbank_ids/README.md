# WorldBank - International Debt Statistics

## Download Script for World Bank - International Debt Statistics

url - `https://databank.worldbank.org/source/international-debt-statistics`

- The download script uses a package called `bblocks`.
- Install the package in a virtual environment `pip3 install -r scripts/world_bank/worldbank_ids/requirements.txt`
- Run the following command to download the input files `python3 scripts/world_bank/worldbank_ids/download.py`
- The year range and indicator list can be modified in the script

- source: `https://databank.worldbank.org/source/international-debt-statistics`, 

- how to download data: The files can be downloaded using `python3 scripts/world_bank/worldbank_ids/download.py`.

- type of place: Country.

- statvars: Economy

- years: 1970 to 2031

- place_resolution: Places are resolved based on name.

### How to run:

`python3 donwload.py`

`python3 ../../../tools/statvar_importer/stat_var_processor.py --input_data=input_files/currency_input.csv --pv_map=configs/currency_pvmap.csv,country:observationAbout.csv,counterpart_area:InputlendingEntity.csv --output_path=output/currency/currency --existing_schema_mcf=Schema_entity.mcf --config_file=common_metadata.csv`

`python3 ../../../tools/statvar_importer/stat_var_processor.py --input_data=input_files/interest_input.csv --pv_map=configs/interest_pvmap.csv,country:observationAbout.csv,counterpart_area:InputlendingEntity.csv --output_path=output/interest/interest_output --existing_schema_mcf=Schema_entity.mcf --config_file=common_metadata.csv`

`python3 ../../../tools/statvar_importer/stat_var_processor.py --input_data=input_files/disbursed_input.csv --pv_map=configs/disbursed_pvmap.csv,country:observationAbout.csv,counterpart_area:InputlendingEntity.csv --output_path=output/disbursed/disbursed_output --existing_schema_mcf=Schema_entity.mcf --config_file=common_metadata.csv`

`python3 ../../../tools/statvar_importer/stat_var_processor.py --input_data=input_files/principal_input.csv --pv_map=configs/principal_pvmap.csv,country:observationAbout.csv,counterpart_area:InputlendingEntity.csv --output_path=output/principal/principal_output --existing_schema_mcf=Schema_entity.mcf --config_file=common_metadata.csv`

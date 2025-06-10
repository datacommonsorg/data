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

`python3 statvar/stat_var_processor.py --input_data=statvar_imports/worldbank_ids/test_data/sample_input/<input_file> --pv_map='statvar_imports/worldbank_ids/test_data/sample_input/<input_pvmap>.csv,country:statvar_imports/worldbank_ids/observationAbout.csv,counterpart_area:statvar_imports/worldbank_ids/InputlendingEntity.csv' --output_path=statvar_imports/worldbank_ids/test_data/sample_output/<output_filename> --existing_schema_mcf=statvar_imports/worldbank_ids/Schema_entity.mcf --config=statvar_imports/worldbank_ids/common_metadata.csv`


#### Example
`python3 statvar/stat_var_processor.py --input_data=statvar_imports/worldbank_ids/test_data/sample_input/disbursed_input.csv --pv_map='statvar_imports/worldbank_ids/test_data/sample_input/disbursed_input.csv,country:statvar_imports/worldbank_ids/observationAbout.csv,counterpart_area:statvar_imports/worldbank_ids/InputlendingEntity.csv' --output_path=statvar_imports/worldbank_ids/test_data/sample_output/Disbursed_Outstanding --existing_schema_mcf=statvar_imports/worldbank_ids/Schema_entity.mcf --config=statvar_imports/worldbank_ids/common_metadata.csv`

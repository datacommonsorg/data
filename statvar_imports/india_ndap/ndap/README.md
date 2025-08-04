# NDAP - India Life Expectancy

- source: `https://ndap.niti.gov.in/dataset/7375`, 

- how to download data: The files can be downloaded using `python3 scripts/world_bank/worldbank_ids/download.py`.
                        The config is stored in GCS bucket as the source URL is an API with key.
                        This approach enhances safety by preventing sensitive information from being directly exposed 

- type of place: State.

- statvars: Health

- years: 1997 to 2020

- place_resolution: Places are resolved based on name.

### How to run:

`python3 donwload_script.py`

`python3 stat_var_processor.py --input_data=../../statvar_imports/india_ndap/ndap/input_files/India_LifeExpectancy_input.csv --pv_map=../../statvar_imports/india_ndap/ndap/India_LifeExpectancy_pvmap.csv --config_file=../../statvar_imports/india_ndap/ndap/India_LifeExpectancy_metadata.csv  --output_path=../../statvar_imports/india_ndap/ndap/output/Life_expectancy`

# OECD Land Cover (city and country) - OECD Data

- source: https://www.oecd-ilibrary.org/environment/data/oecd-environment-statistics_env-data-en

- how to download data: Manual download from source by selecting 'Land Cover' and 'Land Cover in metropolitan cities' and then click the button - 'Export' in the redirected page.

- type of place: Country, City.

- statvars: Environment

- years: 1992 to 2019
- place_resolution: Country and City places are resolved based on name.

### How to run:

Prerequisite: The below command must be run from a folder that contains stat_var_processor.py script file.

python3 stat_var_processor.py --existing_statvar_mcf=stat_vars.mcf --input_data='/data/statvar_imports/oecd_data/landcover/testdata/sample_input/oced_landcover_data.csv' --pv_map='/data/statvar_imports/oecd_data/landcover/testdata/sample_input/oced_landcover_pvmap.csv' --config='/data/statvar_imports/oecd_data/landcover/oced_landcover_metadata.csv' --output_path="/data/statvar_imports/oecd_data/landcover/testdata/sample_output/oecd_landcover"



 


# Land Buitups - OECD Data

- source: https://data-explorer.oecd.org/vis?df[ds]=DisseminateFinalDMZ&df[id]=DSD_LAND@DF_LAND_COVER&df[ag]=OECD.ENV.EPI

- how to download data: Manual download from source by clicking the button - `Export`.

- type of place: Country, City.

- statvars: Environment

- years: 1975 to 2014
- place_resolution: Country and City places are resolved based on name.

### How to run:

Prerequisite: The below command must be run from a folder that contains stat_var_processor.py script file.

python3 stat_var_processor.py --existing_statvar_mcf=stat_vars.mcf --input_data='/data/statvars_import/testdata/sample_input/OECD_LandBuiltups_data.csv' --pv_map='/data/statvars_import/testdata/sample_input/OECD_LandBuiltups_pvmap.csv' --places_resolved_csv='/data/statvars_import/testdata/sample_input/OECD_LandBuiltups_places_resolved.csv' --config='/data/statvars_import/testdata/sample_input/OECD_LandBuiltups_metadata.csv'  --output_path="/data/statvars_import/testdata/sample_output/OECD_LandBuiltups"

 


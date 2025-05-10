# Ireland_Census

- source urls: 
`https://data.cso.ie/table/FY002`, `https://data.cso.ie/table/VSD30`, `https://data.cso.ie/table/VSD31`, `https://data.cso.ie/table/VSA30`, `https://data.cso.ie/table/VSA09`, `https://data.cso.ie/table/VSD24`, `https://data.cso.ie/table/VSA03`, `https://data.cso.ie/table/FY003B`, `https://data.cso.ie/table/FY001`, `https://data.cso.ie/table/FY031`, `https://data.cso.ie/table/CNA22`

- how to download data: Download script (download_script.py).
    To download the data, you'll need to use the provided download script, download_script.py. This script will automatically create an "input_files" folder where you should place the file to be processed. The script also requires a configuration file (config.py) to function correctly. 

- type of place: Demographics, Administrative Area 1 and Administrative area 2 level.

- statvars: Demographics and Subnational.

- place_resolution: Places resolved to wikidataId in place_resolver sheet separately.

### How to run:

`python3 stat_var_processor.py --existing_statvar_mcf=stat_vars.mcf --input_data='<input_file>.csv' --pv_map='data/statvar_imports/ireland_census/<filename of pvmap.csv> --places_resolved_csv='data/statvar_imports/ireland_census/<filename of places_resolved_csv.csv>' --config_file='data/statvar_imports/ireland_census/<filename of metadata.csv>' --output_path='data/statvar_imports/ireland_census/<output_folder_name>/<filename>`

#### To Download the files, run: 

`python3 download_script.py`

Notes: Files will be downloaded inside "input_files" folder.

#### To Process the files, run:

`sh run.sh`

or

`python3 stat_var_processor.py --input_data=/data/statvar_imports/ireland_census/input_files/births.csv --pv_map=/data/statvar_imports/ireland_census/irl_birth_pvmap.csv --config_file=/data/statvar_imports/ireland_census/irl_birth_metadata.csv --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf --output_path=/data/statvar_imports/ireland_census/output_files/irl_birth_output`

`python3 stat_var_processor.py --input_data=/data/statvar_imports/ireland_census/input_files/deaths.csv --pv_map=/data/statvar_imports/ireland_census/irl_deaths_pvmap.csv --config_file=/data/statvar_imports/ireland_census/irl_deaths_metadata.csv --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf --output_path=/data/statvar_imports/ireland_census/output_files/irl_death_output`

`python3 stat_var_processor.py --input_data=/data/statvar_imports/ireland_census/input_files/deaths_from_external_causes.csv --pv_map=/data/statvar_imports/ireland_census/irl_causeofdeath_pvmap.csv --config_file=/data/statvar_imports/ireland_census/irl_causeofdeath_metadata.csv --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf --places_resolved_csv=/data/statvar_imports/ireland_census/places_resolver.csv --output_path=/data/statvar_imports/ireland_census/output_files/irl_external_cause_of_death_output`

`python3 stat_var_processor.py --input_data=/data/statvar_imports/ireland_census/input_files/life_expectancy.csv --pv_map=/data/statvar_imports/ireland_census/irl_lifeexpectancy_pvmap.csv --config_file=/data/statvar_imports/ireland_census/irl_lifeexpectancy_metadata.csv --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf --output_path=/data/statvar_imports/ireland_census/output_files/irl_life_expectancy_output`

`python3 stat_var_processor.py --input_data=/data/statvar_imports/ireland_census/input_files/suicides.csv --pv_map=/data/statvar_imports/ireland_census/irl_suicide_pvmap.csv --config_file=/data/statvar_imports/ireland_census/irl_suicide_metadata.csv --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf --output_path=/data/statvar_imports/ireland_census/output_files/irl_suicide_output`

`python3 stat_var_processor.py --input_data=/data/statvar_imports/ireland_census/input_files/suicides_with_aa1_aa2.csv --pv_map=/data/statvar_imports/ireland_census/irl_aa1_aa2_suicide_pvmap.csv --config_file=/data/statvar_imports/ireland_census/irl_aa1_aa2_suicide_metadata.csv --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf --places_resolved_csv=/data/statvar_imports/ireland_census/places_resolver.csv --output_path=/data/statvar_imports/ireland_census/output_files/irl_aa1_aa2_suicide_output`

`python3 stat_var_processor.py --input_data=/data/statvar_imports/ireland_census/input_files/population_by_age_gender.csv --pv_map=/data/statvar_imports/ireland_census/irl_population_by_age_gender_pvmap.csv --config_file=/data/statvar_imports/ireland_census/irl_population_by_age_gender_metadata.csv --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf --output_path=/data/statvar_imports/ireland_census/output_files/irl_population_by_age_gender_output`

`python3 stat_var_processor.py --input_data=/data/statvar_imports/ireland_census/input_files/population_by_religion.csv --pv_map=/data/statvar_imports/ireland_census/irl_population_by_religion_pvmap.csv --config_file=/data/statvar_imports/ireland_census/irl_population_by_religion_metadata.csv --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf --places_resolved_csv=/data/statvar_imports/ireland_census/places_resolver_religion.csv --output_path=/data/statvar_imports/ireland_census/output_files/irl_population_by_religion_output`

`python3 stat_var_processor.py --input_data=/data/statvar_imports/ireland_census/input_files/population_at_each_census.csv --pv_map=/data/statvar_imports/ireland_census/irl_population_at_each_census_pvmap.csv --config_file=/data/statvar_imports/ireland_census/irl_population_at_each_census_metadata.csv --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf --places_resolved_csv=/data/statvar_imports/ireland_census/places_resolver_each_census.csv --output_path=/data/statvar_imports/ireland_census/output_files/irl_population_at_each_census_output`

`python3 stat_var_processor.py --input_data=/data/statvar_imports/ireland_census/input_files/population_by_gender.csv --pv_map=/data/statvar_imports/ireland_census/irl_population_by_gender_pvmap.csv --config_file=/data/statvar_imports/ireland_census/irl_population_by_gender_metadata.csv --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf --places_resolved_csv=/data/statvar_imports/ireland_census/places_resolver_gender.csv --output_path=/data/statvar_imports/ireland_census/output_files/irl_population_by_gender_output`

`python3 stat_var_processor.py --input_data=/data/statvar_imports/ireland_census/input_files/population_by_employment.csv --pv_map=/data/statvar_imports/ireland_census/irl_aa1_aa2_employment_pvmap.csv --config_file=/data/statvar_imports/ireland_census/irl_aa1_aa2_employment_metadata.csv --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf --places_resolved_csv=/data/statvar_imports/ireland_census/places_resolver.csv --output_path=/data/statvar_imports/ireland_census/output_files/irl_aa1_aa2_employment_output`
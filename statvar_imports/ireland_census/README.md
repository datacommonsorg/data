# Ireland_Census
This import includes Ireland Demographics, Health and Economy data from Central Statistics Office(CSO) by country, county and city levels.

- source urls: 
    - `https://data.cso.ie/table/FY002`
    - `https://data.cso.ie/table/VSD30` 
    - `https://data.cso.ie/table/VSD31` 
    - `https://data.cso.ie/table/VSA30` 
    - `https://data.cso.ie/table/VSA09`
    - `https://data.cso.ie/table/VSD24` 
    - `https://data.cso.ie/table/VSA03` 
    - `https://data.cso.ie/table/FY003B` 
    - `https://data.cso.ie/table/FY001` 
    - `https://data.cso.ie/table/FY031` 
    - `https://data.cso.ie/table/CNA22`

- how to download data: Download script (`download_script.py`).
    To download the data, you'll need to use the provided download script, `download_script.py`. This script will automatically create an "input_files" folder where you should place the file to be processed. 
    The script also requires a configuration file (`config.py`) to function correctly. We should run `preprocess.py` script for removing duplicates data related suicides files. In `suicides.csv` input file contains state level data between the year 1950 and 2021 and the another input file `suicides_with_aa1_aa2.csv` is having data from the year 2008 to latest which is creating duplicates. 
    By executing the `preprocess.py` , we are removing the data from 2008 to 2021 and keeping the data from 2022 to the latest in the `suicides_with_aa1_aa2.csv` and also keeping the `suicides.csv` file as it is after downloading for avoiding the conflicts.

- type of place: Demographics, Administrative Area 1 and Administrative area 2 level.

- statvars: Demographics and Subnational.

- place_resolution: Places resolved to wikidataId in place_resolver sheet separately.

#### To Download the files, run: 

`python3 download_script.py`

Notes: Files will be downloaded inside "input_files" folder.

`python3 preprocess.py`

#### To Process the files, run:

`sh run.sh`

or

Execute the script inside the folder "data/statvar_importer/ireland_census/"

```
python3 ../../tools/statvar_importer/stat_var_processor.py 
--input_data=input_files/births.csv 
--pv_map=irl_birth_pvmap.csv
--config_file=irl_birth_metadata.csv
--existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf 
--output_path=output_files/irl_birth_output
```

```
python3 ../../tools/statvar_importer/stat_var_processor.py 
--input_data=input_files/deaths.csv 
--pv_map=irl_deaths_pvmap.csv 
--config_file=irl_deaths_metadata.csv 
--existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf 
--output_path=output_files/irl_death_output
```

```
python3 ../../tools/statvar_importer/stat_var_processor.py 
--input_data=input_files/deaths_from_external_causes.csv 
--pv_map=irl_causeofdeath_pvmap.csv 
--config_file=irl_causeofdeath_metadata.csv 
--existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf 
--places_resolved_csv=places_resolver.csv 
--output_path=output_files/irl_external_cause_of_death_output
```

```
python3 ../../tools/statvar_importer/stat_var_processor.py 
--input_data=input_files/life_expectancy.csv 
--pv_map=irl_lifeexpectancy_pvmap.csv 
--config_file=irl_lifeexpectancy_metadata.csv 
--existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf -
-output_path=output_files/irl_life_expectancy_output
```

```
python3 ../../tools/statvar_importer/stat_var_processor.py 
--input_data=input_files/suicides.csv 
--pv_map=irl_suicide_pvmap.csv 
--config_file=irl_suicide_metadata.csv 
--existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf 
--output_path=output_files/irl_suicide_output
```

```
python3 ../../tools/statvar_importer/stat_var_processor.py 
--input_data=input_files/suicides_with_aa1_aa2.csv 
--pv_map=irl_aa1_aa2_suicide_pvmap.csv 
--config_file=irl_aa1_aa2_suicide_metadata.csv 
--existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf 
--places_resolved_csv=places_resolver.csv 
--output_path=output_files/irl_aa1_aa2_suicide_output
```

```
python3 ../../tools/statvar_importer/stat_var_processor.py 
--input_data=input_files/population_by_age_gender.csv 
--pv_map=irl_population_by_age_gender_pvmap.csv 
--config_file=irl_population_by_age_gender_metadata.csv 
--existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf 
--output_path=output_files/irl_population_by_age_gender_output
```

```
python3 ../../tools/statvar_importer/stat_var_processor.py
 --input_data=input_files/population_by_religion.csv 
 --pv_map=irl_population_by_religion_pvmap.csv 
--config_file=irl_population_by_religion_metadata.csv 
--existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf --places_resolved_csv=places_resolver_religion.csv 
--output_path=output_files/irl_population_by_religion_output
```

```
python3 ../../tools/statvar_importer/stat_var_processor.py 
--input_data=input_files/population_at_each_census.csv 
--pv_map=irl_population_at_each_census_pvmap.csv 
--config_file=irl_population_at_each_census_metadata.csv 
--existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf --places_resolved_csv=places_resolver_each_census.csv 
--output_path=output_files/irl_population_at_each_census_output
```

```
python3 ../../tools/statvar_importer/stat_var_processor.py 
--input_data=input_files/population_by_gender.csv 
--pv_map=irl_population_by_gender_pvmap.csv 
--config_file=irl_population_by_gender_metadata.csv 
--existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf --places_resolved_csv=places_resolver_gender.csv 
--output_path=output_files/irl_population_by_gender_output
```

```
python3 ../../tools/statvar_importer/stat_var_processor.py 
--input_data=input_files/population_by_employment.csv 
--pv_map=irl_aa1_aa2_employment_pvmap.csv 
--config_file=irl_aa1_aa2_employment_metadata.csv 
--existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf 
--places_resolved_csv=places_resolver.csv 
--output_path=output_files/irl_aa1_aa2_employment_output
```

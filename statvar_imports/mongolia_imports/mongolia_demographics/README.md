### Copyright 2025 Google LLC
###
### Licensed under the Apache License, Version 2.0 (the "License");
### you may not use this file except in compliance with the License.
### You may obtain a copy of the License at
###
###       http://www.apache.org/licenses/LICENSE-2.0
###
### Unless required by applicable law or agreed to in writing, software
### distributed under the License is distributed on an "AS IS" BASIS,
### WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
### See the License for the specific language governing permissions and
### limitations under the License.


## Mongolia_Demographics Import

This import contains statistical data related to Mongolia's populations and households at the country level.

-----

### ⚙️ How to Use

The workflow for this data import involves two main steps: downloading the necessary files and then processing them.

#### Step 1: Download the Data

- **Source:** [Mongolia population and household data](https://www.1212.mn/en/statcate)
- **Description:** The provided URL links to the official website of the National Statistical Office (NSO) of Mongolia. This specific page presents official statistics and data related to the country's population and households.

To get the necessary data files, you'll need to run download script `common_download_script.py`.

All downloaded files will be located into the `mongolia_demographics/input_files` folder.

This import will be fully refreshed in an automated manner.

-----

#### Step 2: Process the Files

After downloading the files, you can process them to generate the final output. There are two ways to do this:

**Option A: Use the `run.sh` script**

The `run.sh` script automates the processing of all the downloaded files.

**Run the following command:**

```bash
sh run.sh
```

**Option B: Manually Execute the Processing Script**

You can also run the `stat_var_processor.py` script individually for each file. This script is located in the `data/tools/statvar_importer/` directory.

Here are the specific commands for each file:

```bash
python3 stat_var_processor.py
--input_data=../../statvar_imports/mongolia_imports/mongolia_demographics/input_files/mid_year_total_population_by_region.csv
--pv_map=../../statvar_imports/mongolia_imports/mongolia_demographics/mid_year_total_population_by_region_pvmap.csv
--config_file=../../statvar_imports/mongolia_imports/mongolia_demographics/mongolia_metadata.csv
--output_path=../../statvar_imports/mongolia_imports/mongolia_demographics/output_files/mid_year_total_population_by_region_output
--places_resolved_csv=../../statvar_imports/mongolia_imports/mongolia_demographics/mongolia_place_resolver.csv 
--existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf
```

```bash
python3 stat_var_processor.py
--input_data=../../statvar_imports/mongolia_imports/mongolia_demographics/input_files/number_of_households_by_region_and_urban_rural.csv
--pv_map=../../statvar_imports/mongolia_imports/mongolia_demographics/number_of_households_by_region_and_urban_rural_pvmap.csv
--config_file=../../statvar_imports/mongolia_imports/mongolia_demographics/mongolia_metadata.csv
--output_path=../../statvar_imports/mongolia_imports/mongolia_demographics/output_files/number_of_households_by_region_and_urban_rural_output
--places_resolved_csv=../../statvar_imports/mongolia_imports/mongolia_demographics/mongolia_place_resolver.csv 
--existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf
```

```bash
python3 stat_var_processor.py
--input_data=../../statvar_imports/mongolia_imports/mongolia_demographics/input_files/number_of_households_by_region.csv
--pv_map=../../statvar_imports/mongolia_imports/mongolia_demographics/number_of_households_by_region_pvmap.csv
--config_file=../../statvar_imports/mongolia_imports/mongolia_demographics/mongolia_metadata.csv
--output_path=../../statvar_imports/mongolia_imports/mongolia_demographics/output_files/number_of_households_by_region_output
--places_resolved_csv=../../statvar_imports/mongolia_imports/mongolia_demographics/mongolia_place_resolver.csv 
--existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf
```

```bash
python3 stat_var_processor.py
--input_data=../../statvar_imports/mongolia_imports/mongolia_demographics/input_files/resident_population_by_agegroup_15_and_over_and_maritalstatus.csv
--pv_map=../../statvar_imports/mongolia_imports/mongolia_demographics/resident_population_by_agegroup_15_and_over_and_maritalstatus_pvmap.csv
--config_file=../../statvar_imports/mongolia_imports/mongolia_demographics/mongolia_metadata.csv
--output_path=../../statvar_imports/mongolia_imports/mongolia_demographics/output_files/resident_population_by_agegroup_15_and_over_and_maritalstatus_output
--existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf
```

```bash
python3 stat_var_processor.py
--input_data=../../statvar_imports/mongolia_imports/mongolia_demographics/input_files/total_population_by_age_group_and_sex.csv
--pv_map=../../statvar_imports/mongolia_imports/mongolia_demographics/total_population_by_age_group_and_sex_pvmap.csv
--config_file=../../statvar_imports/mongolia_imports/mongolia_demographics/mongolia_metadata.csv
--output_path=../../statvar_imports/mongolia_imports/mongolia_demographics/output_files/total_population_by_age_group_and_sex_output 
--existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf
```

```bash
python3 stat_var_processor.py
--input_data=../../statvar_imports/mongolia_imports/mongolia_demographics/input_files/total_population_by_region_and_urban_rural.csv
--pv_map=../../statvar_imports/mongolia_imports/mongolia_demographics/total_population_by_region_and_urban_rural_pvmap.csv
--config_file=../../statvar_imports/mongolia_imports/mongolia_demographics/mongolia_metadata.csv
--output_path=../../statvar_imports/mongolia_imports/mongolia_demographics/output_files/total_population_by_region_and_urban_rural_output
--places_resolved_csv=../../statvar_imports/mongolia_imports/mongolia_demographics/mongolia_place_resolver.csv 
--existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf
```

```bash
python3 stat_var_processor.py
--input_data=../../statvar_imports/mongolia_imports/mongolia_demographics/input_files/total_population_by_sex_and_urban_rural.csv
--pv_map=../../statvar_imports/mongolia_imports/mongolia_demographics/total_population_by_sex_and_urban_rural_pvmap.csv
--config_file=../../statvar_imports/mongolia_imports/mongolia_demographics/total_population_by_sex_and_urban_rural_metadata.csv
--output_path=../../statvar_imports/mongolia_imports/mongolia_demographics/output_files/total_population_by_sex_and_urban_rural_output 
--existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf
```


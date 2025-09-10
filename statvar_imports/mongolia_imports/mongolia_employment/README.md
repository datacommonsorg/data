#### Copyright 2025 Google LLC
####
#### Licensed under the Apache License, Version 2.0 (the "License");
#### you may not use this file except in compliance with the License.
#### You may obtain a copy of the License at
####
####       http://www.apache.org/licenses/LICENSE-2.0
####
#### Unless required by applicable law or agreed to in writing, software
#### distributed under the License is distributed on an "AS IS" BASIS,
#### WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#### See the License for the specific language governing permissions and
#### limitations under the License.


## Mongolia_Employment Import

This import contains statistical data related to Mongolia's labour and business at the country level.

-----

### ⚙️ How to Use

The workflow for this data import involves two main steps: Manually downloading the necessary files and then processing them.

#### Step 1: Download the Data

- **Source:** [Mongolia labour and business data](https://www.1212.mn/en/statcate)
- **Description:** The provided URL links to the official website of the National Statistical Office (NSO) of Mongolia. This specific page presents official statistics and data related to the country's labour and business statistics.

To get the necessary data files, you'll need to manually download source files.
<https://www.1212.mn/en/statcate/table/Labour%2C%20business/Labour>

All downloaded files will be located into the gcs path `unresolved_mcf/country/mongolia/mongolia_employment/latest/input_files` and can be directly read from it while processing.

This import will be refreshed in a semi-automated manner.

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
--input_data=gs://unresolved_mcf/country/mongolia/mongolia_employment/latest/input_files/employment_by_classification_of_economic_activities_region_gender_and_agegroup.csv
--pv_map=../../statvar_imports/mongolia_imports/mongolia_employment/employment_by_classification_of_economic_activities_region_gender_and_agegroup_pvmap.csv
--config_file=../../statvar_imports/mongolia_imports/mongolia_employment/metadata.csv
--output_path=../../statvar_imports/mongolia_imports/mongolia_employment/output_files/employment_by_classification_of_economic_activities_region_gender_and_agegroup_output
--places_resolved_csv=../../statvar_imports/mongolia_imports/mongolia_employment/places_resolved.csv 
--existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf
```

```bash
python3 stat_var_processor.py
--input_data=gs://unresolved_mcf/country/mongolia/mongolia_employment/latest/input_files/employment_by_occupation_by_region_gender_and_agegroup.csv
--pv_map=../../statvar_imports/mongolia_imports/mongolia_employment/employment_by_occupation_by_region_gender_and_agegroup_pvmap.csv
--config_file=../../statvar_imports/mongolia_imports/mongolia_employment/employment_by_occupation_by_region_gender_and_agegroup_metadata.csv
--output_path=../../statvar_imports/mongolia_imports/mongolia_employment/output_files/employment_by_occupation_by_region_gender_and_agegroup_output
--places_resolved_csv=../../statvar_imports/mongolia_imports/mongolia_employment/places_resolved.csv 
--existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf
```

```bash
python3 stat_var_processor.py
--input_data=gs://unresolved_mcf/country/mongolia/mongolia_employment/latest/input_files/employment_to_population_ratio_by_region_gender_and_agegroup.csv
--pv_map=../../statvar_imports/mongolia_imports/mongolia_employment/employment_to_population_ratio_by_region_gender_and_agegroup_pvmap.csv
--config_file=../../statvar_imports/mongolia_imports/mongolia_employment/employment_to_population_ratio_by_region_gender_and_agegroup_metadata.csv
--output_path=../../statvar_imports/mongolia_imports/mongolia_employment/output_files/employment_to_population_ratio_by_region_gender_and_agegroup_output
--places_resolved_csv=../../statvar_imports/mongolia_imports/mongolia_employment/places_resolved.csv 
--existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf
```

```bash
python3 stat_var_processor.py
--input_data=gs://unresolved_mcf/country/mongolia/mongolia_employment/latest/input_files/labour_force_by_region_gender_and_agegroup.csv
--pv_map=../../statvar_imports/mongolia_imports/mongolia_employment/labour_force_by_region_gender_and_agegroup_pvmap.csv
--config_file=../../statvar_imports/mongolia_imports/mongolia_employment/metadata.csv
--output_path=../../statvar_imports/mongolia_imports/mongolia_employment/output_files/labour_force_by_region_gender_and_agegroup_output
--places_resolved_csv=../../statvar_imports/mongolia_imports/mongolia_employment/places_resolved.csv 
--existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf
```

```bash
python3 stat_var_processor.py
--input_data=gs://unresolved_mcf/country/mongolia/mongolia_employment/latest/input_files/labour_underutilization_by_region_gender_and_agegroup.csv
--pv_map=../../statvar_imports/mongolia_imports/mongolia_employment/labour_underutilization_by_region_gender_and_agegroup_pvmap.csv
--config_file=../../statvar_imports/mongolia_imports/mongolia_employment/metadata.csv
--output_path=../../statvar_imports/mongolia_imports/mongolia_employment/output_files/labour_underutilization_by_region_gender_and_agegroup_output 
--places_resolved_csv=../../statvar_imports/mongolia_imports/mongolia_employment/places_resolved.csv 
--existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf
```

```bash
python3 stat_var_processor.py
--input_data=gs://unresolved_mcf/country/mongolia/mongolia_employment/latest/input_files/registered_unemployed_by_education_level_region_gender_month.csv
--pv_map=../../statvar_imports/mongolia_imports/mongolia_employment/registered_unemployed_by_education_level_region_gender_month_pvmap.csv
--config_file=../../statvar_imports/mongolia_imports/mongolia_employment/metadata.csv
--output_path=../../statvar_imports/mongolia_imports/mongolia_employment/output_files/registered_unemployed_by_education_level_region_gender_month_output
--places_resolved_csv=../../statvar_imports/mongolia_imports/mongolia_employment/places_resolved.csv 
--existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf
```



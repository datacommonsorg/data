#### Copyright 2025 Google LLC
####
#### Licensed under the Apache License, Version 2.0 (the "License");
#### you may not use this file except in compliance with the License.
####
####       http://www.apache.org/licenses/LICENSE-2.0
####
#### Unless required by applicable law or agreed to in writing, software
#### distributed under the License is distributed on an "AS IS" BASIS,
#### WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#### See the License for the specific language governing permissions and
#### limitations under the License.
-----


## NCHS_BRFSS_Asthma Import

This import contains US statistical data mainly focused on Adult and child Self-Reported Lifetime Asthma Prevalence.

-----

### ⚙️ How to Use

The workflow for this data import involves two main steps: downloading the necessary files and then processing them.

#### Step 1: Download the Data

- **Source:** [NCHS BRFSS Asthma data](https://www.cdc.gov/asthma/brfss/default.htm)
- **Description:** The provided URL links to the Asthma and the Behavioral Risk Factor Surveillance System (BRFSS) data. The BRFSS is a large-scale, ongoing telephone survey conducted by the Centers for Disease Control and Prevention (CDC) that gathers data on health-related risk behaviors and chronic health conditions of adults and child in the U.S.

To get the necessary data files, you'll need to run download script `download_script.py`.

All downloaded files will be located in the `input_files` folder. Within this folder, there are six sub-folders, each containing categorized data for both adults and children:

    - by_age_and_state

    - by_education_and_state

    - by_income_and_state

    - by_race_ethnicity_and_state

    - by_sex_and_state

    - overall_by_state

### Auto refresh Type

This import will be refreshed in a fully automated manner.

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
--input_data=../../statvar_imports/brfss_nchs_asthma_prevalence/nchs_brfss_asthma/input_files/by_age_and_state/*.csv"
--pv_map=../../statvar_imports/brfss_nchs_asthma_prevalence/nchs_brfss_asthma/brfss_asthma_by_age_and_state_pvmap.csv"
--config_file=../../statvar_imports/brfss_nchs_asthma_prevalence/nchs_brfss_asthma/common_metadata.csv"
--output_path=../../statvar_imports/brfss_nchs_asthma_prevalence/nchs_brfss_asthma/output_files/brfss_asthma_by_age_and_state_output"
--existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf
--places_resolved_csv=../../statvar_imports/brfss_nchs_asthma_prevalence/nchs_brfss_asthma/places_resolver.csv"
--statvar_dcid_remap_csv=../../statvar_imports/brfss_nchs_asthma_prevalence/nchs_brfss_asthma/statvar_remap.csv"
```

```bash
python3 stat_var_processor.py
--input_data=../../statvar_imports/brfss_nchs_asthma_prevalence/nchs_brfss_asthma/input_files/by_education_and_state/*.csv"
--pv_map=../../statvar_imports/brfss_nchs_asthma_prevalence/nchs_brfss_asthma/brfss_asthma_by_education_and_state_pvmap.csv"
--config_file=../../statvar_imports/brfss_nchs_asthma_prevalence/nchs_brfss_asthma/common_metadata.csv"
--output_path=../../statvar_imports/brfss_nchs_asthma_prevalence/nchs_brfss_asthma/output_files/brfss_asthma_by_education_and_state_output"
--existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf
--places_resolved_csv=../../statvar_imports/brfss_nchs_asthma_prevalence/nchs_brfss_asthma/places_resolver.csv"
--statvar_dcid_remap_csv=../../statvar_imports/brfss_nchs_asthma_prevalence/nchs_brfss_asthma/statvar_remap.csv"
``` 

```bash
python3 stat_var_processor.py
--input_data=../../statvar_imports/brfss_nchs_asthma_prevalence/nchs_brfss_asthma/input_files/by_income_and_state/*.csv"
--pv_map=../../statvar_imports/brfss_nchs_asthma_prevalence/nchs_brfss_asthma/brfss_asthma_by_income_and_state_pvmap.csv"
--config_file=../../statvar_imports/brfss_nchs_asthma_prevalence/nchs_brfss_asthma/common_metadata.csv"
--output_path=../../statvar_imports/brfss_nchs_asthma_prevalence/nchs_brfss_asthma/output_files/brfss_asthma_by_income_and_state_output"
--existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf
--places_resolved_csv=../../statvar_imports/brfss_nchs_asthma_prevalence/nchs_brfss_asthma/places_resolver.csv"
--statvar_dcid_remap_csv=../../statvar_imports/brfss_nchs_asthma_prevalence/nchs_brfss_asthma/statvar_remap.csv"
``` 

```bash
python3 stat_var_processor.py
--input_data=../../statvar_imports/brfss_nchs_asthma_prevalence/nchs_brfss_asthma/input_files/by_race_ethnicity_and_state/*.csv"
--pv_map=../../statvar_imports/brfss_nchs_asthma_prevalence/nchs_brfss_asthma/brfss_asthma_by_race_and_ethnicity_state_pvmap.csv"
--config_file=../../statvar_imports/brfss_nchs_asthma_prevalence/nchs_brfss_asthma/common_metadata.csv"
--output_path=../../statvar_imports/brfss_nchs_asthma_prevalence/nchs_brfss_asthma/output_files/brfss_asthma_by_race_and_ethnicity_state_output"
--existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf
--places_resolved_csv=../../statvar_imports/brfss_nchs_asthma_prevalence/nchs_brfss_asthma/places_resolver.csv"
--statvar_dcid_remap_csv=../../statvar_imports/brfss_nchs_asthma_prevalence/nchs_brfss_asthma/statvar_remap.csv"
``` 

```bash
python3 stat_var_processor.py
--input_data=../../statvar_imports/brfss_nchs_asthma_prevalence/nchs_brfss_asthma/input_files/by_sex_and_state/*.csv"
--pv_map=../../statvar_imports/brfss_nchs_asthma_prevalence/nchs_brfss_asthma/brfss_asthma_by_sex_and_state_pvmap.csv"
--config_file=../../statvar_imports/brfss_nchs_asthma_prevalence/nchs_brfss_asthma/metadata_by_sex_and_state.csv"
--output_path=../../statvar_imports/brfss_nchs_asthma_prevalence/nchs_brfss_asthma/output_files/brfss_asthma_by_sex_and_state_output"
--existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf
--places_resolved_csv=../../statvar_imports/brfss_nchs_asthma_prevalence/nchs_brfss_asthma/places_resolver.csv"
--statvar_dcid_remap_csv=../../statvar_imports/brfss_nchs_asthma_prevalence/nchs_brfss_asthma/statvar_remap.csv"
``` 

```bash
python3 stat_var_processor.py
--input_data=../../statvar_imports/brfss_nchs_asthma_prevalence/nchs_brfss_asthma/input_files/overall_by_state/*.csv"
--pv_map=../../statvar_imports/brfss_nchs_asthma_prevalence/nchs_brfss_asthma/brfss_asthma_by_state_pvmap.csv"
--config_file=../../statvar_imports/brfss_nchs_asthma_prevalence/nchs_brfss_asthma/metadata_by_sex_and_state.csv"
--output_path=../../statvar_imports/brfss_nchs_asthma_prevalence/nchs_brfss_asthma/output_files/brfss_asthma_by_state_output"
--existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf
--places_resolved_csv=../../statvar_imports/brfss_nchs_asthma_prevalence/nchs_brfss_asthma/places_resolver.csv"
--statvar_dcid_remap_csv=../../statvar_imports/brfss_nchs_asthma_prevalence/nchs_brfss_asthma/statvar_remap.csv"
``` 

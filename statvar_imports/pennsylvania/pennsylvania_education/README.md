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


## Pennsylvania_education Import

Dataset related to Pennsylvania's Education at county level.
-----

**Provenance Description:**
Data assets within this catalog are authored and maintained by individual Commonwealth agencies, which serve as the authoritative sources for their respective domains. The portal, managed by the Office of Administration, provides a transparent audit trail by documenting original publication dates, metadata update frequencies, and the specific departmental "stewards" responsible for the data's accuracy and integrity.

### How to Use

The workflow for this data import involves two main steps: downloading the necessary files and then processing them.

#### Step 1: Download the Data

- **Source:** [Pennsylvania_Education](https://data.pa.gov/browse?sortBy=relevance&page=1&pageSize=20)
- **Description:** The provided URL links to the Education data category within the Commonwealth of Pennsylvania’s open data repository. This portal serves as a centralized clearinghouse for public records, statistics, and geospatial data managed by the Pennsylvania Department of Education (PDE) and related agencies.

To fetch the necessary data files, you'll need to run download script `download_script.py`.

The download_script will download below mentioned files in the `input_files` folder. Within this folder, there are four sub-folders, each containing categorized data for both adults and children:

    - educational_attainment_by_age_range_and_gender

    - post_secondary_completions_total_awards_degrees

    - public_school_enrollment_by_county_grade_and_race

    - undergraduate_stem_enrollment


### Auto refresh Type

This import will be refreshed in a fully automated manner.

-----

#### Step 2: Process the Files

After downloading the files, you can process them to generate the final output. To do this:

**Option A: Use the `run_processing.sh` script**

The `run_processing.sh` script automates the processing of all the downloaded files.

**Run the following command:**

```bash
sh run.sh
```

**Option B: Manually Execute the Processing Script**

You can also run the `stat_var_processor.py` script individually for each file. This script is located in the `data/tools/statvar_importer/` directory.

Here are the specific commands for each file:

```bash
python3 stat_var_processor.py
--input_data=../../statvar_imports/pennsylvania/pennsylvania_education/input_files/educational_attainment_by_age_range_and_gender/*.csv"
--pv_map=../../statvar_imports/pennsylvania/pennsylvania_education/educational_attainment_by_age_range_and_gender_pvmap.csv"
--config_file=../../statvar_imports/pennsylvania/pennsylvania_education/common_metadata.csv"
--output_path=../../statvar_imports/pennsylvania/pennsylvania_education/output_files/educational_attainment_by_age_range_and_gender_output"
--existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf
--places_resolved_csv=../../statvar_imports/pennsylvania/pennsylvania_education/educational_attainment_by_age_range_and_gender_places_resolver.csv"
```

```bash
python3 stat_var_processor.py
--input_data=../../statvar_imports/pennsylvania/pennsylvania_education/input_files/post_secondary_completions_total_awards_degrees/*.csv"
--pv_map=../../statvar_imports/pennsylvania/pennsylvania_education/post_secondary_completions_total_awards_degrees_pvmap.csv"
--config_file=../../statvar_imports/pennsylvania/pennsylvania_education/common_metadata.csv"
--output_path=../../statvar_imports/pennsylvania/pennsylvania_education/output_files/post_secondary_completions_total_awards_degrees_output"
--existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf
--places_resolved_csv=../../statvar_imports/pennsylvania/pennsylvania_education/post_secondary_completions_total_awards_degrees_places_resolver.csv"
``` 

```bash
python3 stat_var_processor.py
--input_data=../../statvar_imports/pennsylvania/pennsylvania_education/input_files/public_school_enrollment_by_county_grade_and_race/*.csv"
--pv_map=../../statvar_imports/pennsylvania/pennsylvania_education/public_school_enrollment_by_county_grade_and_race_pvmap.csv"
--config_file=../../statvar_imports/pennsylvania/pennsylvania_education/common_metadata.csv"
--output_path=../../statvar_imports/pennsylvania/pennsylvania_education/output_files/public_school_enrollment_by_county_grade_and_race_output"
--existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf
--places_resolved_csv=../../statvar_imports/pennsylvania/pennsylvania_education/public_school_enrollment_by_county_grade_and_race_places_resolver.csv"
``` 

```bash
python3 stat_var_processor.py
--input_data=../../statvar_imports/pennsylvania/pennsylvania_education/input_files/undergraduate_stem_enrollment/*.csv"
--pv_map=../../statvar_imports/pennsylvania/pennsylvania_education/undergraduate_stem_enrollment_pvmap.csv"
--config_file=../../statvar_imports/pennsylvania/pennsylvania_education/common_metadata.csv"
--output_path=../../statvar_imports/pennsylvania/pennsylvania_education/output_files/undergraduate_stem_enrollment_output"
--existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf
--places_resolved_csv=../../statvar_imports/pennsylvania/pennsylvania_education/undergraduate_stem_enrollment_places_resolver.csv"
``` 


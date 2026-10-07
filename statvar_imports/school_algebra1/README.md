#### Copyright 2025 Google LLC
####
#### Licensed under the Apache License, Version 2.0 (the "License");
#### you may not use this file except in compliance with the License.
#### You may obtain a copy of the License at
####
####    https://www.apache.org/licenses/LICENSE-2.0
####
#### Unless required by applicable law or agreed to in writing, software
#### distributed under the License is distributed on an "AS IS" BASIS,
#### WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#### See the License for the specific language governing permissions and
#### limitations under the License.

-----

## US_UrbanSchool_Algebra1 Import

This import focuses on urban school Algebra1. This dataset contains information about enrollment and passed data of students in Algebra1 and also at different grade level.

-----
- source: https://civilrightsdata.ed.gov/data

- type of place: School (NCES School ID)

- statvars: Education

- years: 2009 to 2024

### ⚙️ Workflow

The workflow for this data import involves three main steps: downloading the raw data, preprocessing and filtering, and generating the final StatVars.

#### Step 1: Download the Source Data

To acquire the raw CRDC data files, execute the download script `download_script.py`:
```bash
    python3 download_script.py
```
All downloaded raw files will be stored in `input_files/`.

#### Step 2: Preprocess and Filter the Data

Run `preprocess_data.py` to convert `.xlsx` workbooks to `.csv`, compute standard `ncesid` and `YEAR` identifiers, and dynamically filter columns against `Algebra1_pvmap.csv`:
```bash
    python3 preprocess_data.py
```
All preprocessed files will be stored in `processed_files/`.

#### Step 3: Process the Data with StatVar Processor

Once the data is preprocessed, run `stat_var_processor.py` to generate the final artifacts (CSV, TMCF, MCF):
```bash
    python3 ../../tools/statvar_importer/stat_var_processor.py --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf --input_data=processed_files/*.csv --pv_map=Algebra1_pvmap.csv --config_file=Algebra1_metadata.csv --output_path=output/algebra1_output --output_counters=counters/algebra1_counters.csv --log_level=-2 --log_every_n=1000
```

### Validation & Testing

Run the unit tests for preprocessing:
```bash
    python3 -m unittest preprocess_data_test.py
```

### Autorefresh type

This import uses a fully automated refresh process.

-----


### Automation

This import pipeline is configured to run automatically on a monthly schedule.

- Cron Expression: 30 08 25 * *

Schedule: The script runs at 8:30 AM on the 25th day of every month.

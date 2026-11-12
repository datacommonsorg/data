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

## US_UrbanSchool_Retention Import

This data provides an overview of student retention counts and indicators, categorized by gender, race/ethnicity, disability status, and language fluency, for Kindergarten and School Grades 1 to 12.

-----
- source: https://civilrightsdata.ed.gov/data

- type of place: School

- statvars: Education

- years: 2010 - 2024

### ⚙️ Workflow

The workflow for this data import involves two main steps: downloading/preprocessing the source files and then running the StatVar processor.

#### Step 1: Download and Preprocess the Source Data

Execute `download_script.py` from the `statvar_imports/school_retention/` directory:
```bash
python3 download_script.py
```

This script performs the following:
- Downloads the CRDC archive files for published survey years and extracts matching school-level retention files into `raw_input_files/`.
- Standardizes 12-character `NCESID` values (`LEAID` + `SCHID` or `COMBOKEY`), normalizes the juvenile justice indicator (`JJ` / `SCH_JUST`), filters out unmapped columns and negative CRDC reserve codes, and writes clean `.csv` files into `input_files/transformed_*.csv`.

#### Step 2: Process the Data

Run `stat_var_processor.py` to generate the final output artifacts (`output/retention_output.csv`, `output/retention_output.tmcf`, and `output/retention_output_stat_vars.mcf`):
```bash
python3 ../../tools/statvar_importer/stat_var_processor.py \
  --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf \
  --input_data=input_files/*.csv \
  --pv_map=retention_pvmap.csv \
  --config_file=retention_metadata.csv \
  --output_path=output/retention_output \
  --output_counters=counters/retention_counters.csv \
  --recon_property=variableMeasured \
  --log_level=-2 \
  --log_every_n=1000
```

#### Step 3: Run Unit Tests

From the `data/` repository root:
```bash
./run_tests.sh -p statvar_imports/school_retention
```

### Autorefresh type

This import uses a fully automated refresh process.

-----

### Automation

This import pipeline is configured to run automatically on a weekly schedule.

- Cron Expression: `30 9 * * 2`

Schedule: Weekly on Tuesday at 09:30 UTC.


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

# US_State_SAT_ACT_Participation Import

This dataset contains state-level participation in the Scholastic Assessment Test (SAT) or American College Testing (ACT) based on various demographics.

-----

## ⚙️ Workflow

The workflow for this data import involves two main steps: downloading the necessary files and then processing them.

### Autorefresh type

This import uses a fully automated refresh process.

-----

### Single execution

To download the data, run the following script:

```bash
sh run_download_process.sh
```

**Note:** If `run_download_process.sh` exists, ensure it calls `download_statelevel.py` and saves files to `/input_files_state`.

### Individual Execution

To execute the command file by file, here are the following steps

#### Step 1: Download the Source Data

To acquire the necessary data files, execute the download script `download_statelevel.py`.

```bash
python3 download_statelevel.py --data_type=sat_act
```

All downloaded files will be stored in the directory `/input_files_state`.

#### Step 2: Run the files individually
Example
```bash
python3 statvar_processor.py --input_data=../../../statvar_imports/us_urban_school/sat_act_participation/input_files_school/2022_SAT_ACT_Participation.csv  --pv_map=../../../statvar_imports/us_urban_school/sat_act_participation/config/SATorACT_Participation_pvmap.csv --config_file=../../../statvar_imports/us_urban_school/sat_act_participation/config/SATorACT_Participation_metadata.csv --output_path=../../../statvar_imports/us_urban_school/sat_act_participation/output_files/output_2022  --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf 
```
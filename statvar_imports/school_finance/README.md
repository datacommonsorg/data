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

## US_UrbanSchool_Finances Import

This import focuses on urban school finance. This dataset contains financial and identifying information for educational institutions, including details on salaries and expenditures of teachers.

-----
- source: https://ocrdata.ed.gov/data

- type of place: Country

- statvars: Education

- years: 2010 and 2012

### ⚙️ Workflow

The workflow for this data import involves two main steps: downloading the necessary files and then processing them.

#### Step 1: Download the Source Data

To acquire the necessary data files, execute the download script `download_script.py`.

All downloaded files will be stored in the directory `input_files`.

#### Step 2: Process the Data

Once the data is downloaded run the `stat_var_processor.py` script to process the files and generate the final output artifacts (CSV, TMCF, MCF).

The script is located in the `data/tools/statvar_importer/` directory. Run the following command
    ```bash
    python3 stat_var_processor.py --input_data=../../statvar_imports/school_finance/input_files/*.xlsx --pv_map=../../statvar_imports/school_finance/school_finance_pvmap.csv --config_file=../../statvar_imports/school_finance/school_finance_metadata.csv --output_path=../../statvar_imports/school_finance/output/school_finance_output
    ```

### Autorefresh type

This import uses a fully automated refresh process.

-----


### Automation

This import pipeline is configured to run automatically on a monthly schedule.

- Cron Expression: 30 08 25 * *

Schedule: The script runs at 8:30 AM on the 25th day of every month.

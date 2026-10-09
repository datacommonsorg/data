#### Copyright 2026 Google LLC
####
#### Licensed under the Apache License, Version 2.0 (the "License");
#### you may not use this file except in compliance with the License.
#### You may obtain a copy of the License at
####
####     https://www.apache.org/licenses/LICENSE-2.0
####
#### Unless required by applicable law or agreed to in writing, software
#### distributed under the License is distributed on an "AS IS" BASIS,
#### WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#### See the License for the specific language governing permissions and
#### limitations under the License.

## SouthKorea_Employment Import

This import contains statistical data related to employment, unemployment rates, and employment status in South Korea, including breakdowns by province, gender, age, and education level.

-----

### ⚙️ How to Use

The workflow for this data import involves two main steps: downloading the source files from KOSIS and staging them in GCS, then processing them using the StatVar processor.

#### Step 1: Download the Data

- **Source:** [Korean Statistical Information Service (KOSIS)](https://kosis.kr/eng/statisticsList/statisticsListIndex.do)
- **Description:** KOSIS provides official statistical data about South Korea. This import covers 4 annual (`P1Y`) employment tables:

1. **Employment Status** (Table `DT_1DA7010S`): Saved as `source_files/employmentstatus_data.csv`  
   <https://kosis.kr/statHtml/statHtml.do?sso=ok&returnurl=https%3A%2F%2Fkosis.kr%3A443%2FstatHtml%2FstatHtml.do%3Flist_id%3DB17%26obj_var_id%3D%26seqNo%3D%26tblId%3DDT_1DA7010S%26vw_cd%3DMT_ETITLE%26language%3Den%26orgId%3D101%26path%3D%252Feng%252FstatisticsList%252FstatisticsListIndex.do%26conn_path%3DMT_ETITLE%26itm_id%3D%26lang_mode%3Den%26scrId%3D%26>

2. **Unemployment Status by Gender and Educational Attainment** (Table `DT_1DA7087S`): Saved as `source_files/sexandeducationalattainment_unemploymentstatus_data.csv`  
   <https://kosis.kr/statHtml/statHtml.do?sso=ok&returnurl=https%3A%2F%2Fkosis.kr%3A443%2FstatHtml%2FstatHtml.do%3Flist_id%3DB16%26obj_var_id%3D%26seqNo%3D%26tblId%3DDT_1DA7087S%26vw_cd%3DMT_ETITLE%26language%3Den%26orgId%3D101%26path%3D%252Feng%252FstatisticsList%252FstatisticsListIndex.do%26conn_path%3DMT_ETITLE%26itm_id%3D%26lang_mode%3Den%26scrId%3D%26>

3. **Unemployment Rate by Gender and Age** (Table `DT_1DA7102S`): Saved as `source_files/unemploymentrate_by_gender_age_data.csv`  
   <https://kosis.kr/statHtml/statHtml.do?sso=ok&returnurl=https%3A%2F%2Fkosis.kr%3A443%2FstatHtml%2FstatHtml.do%3Flist_id%3DB15%26obj_var_id%3D%26seqNo%3D%26tblId%3DDT_1DA7102S%26vw_cd%3DMT_ETITLE%26language%3Den%26orgId%3D101%26path%3D%252Feng%252FstatisticsList%252FstatisticsListIndex.do%26conn_path%3DMT_ETITLE%26itm_id%3D%26lang_mode%3Den%26scrId%3D%26>

4. **Unemployment Status by Province and Gender** (Table `DT_1DA7088S`): Saved as `source_files/unemploymentstatus_data.csv`  
   <https://kosis.kr/statHtml/statHtml.do?sso=ok&returnurl=https%3A%2F%2Fkosis.kr%3A443%2FstatHtml%2FstatHtml.do%3Flist_id%3DB16%26obj_var_id%3D%26seqNo%3D%26tblId%3DDT_1DA7088S%26vw_cd%3DMT_ETITLE%26language%3Den%26orgId%3D101%26path%3D%252Feng%252FstatisticsList%252FstatisticsListIndex.do%26conn_path%3DMT_ETITLE%26itm_id%3D%26lang_mode%3Den%26scrId%3D%26>

All downloaded files are staged into the GCS path `gs://unresolved_mcf/country/southkorea/employment/source_files/`.

#### Autorefresh Type:

This import is refreshed in a semi-automated manner on an annual cadence (`P1Y`).

-----
### Step 1: Download the files:

To download the files, run:

```bash
../run.sh gs://unresolved_mcf/country/southkorea/employment/source_files/
```

#### Step 2: Process the Files

After downloading the files, you can process them to generate the final output. 

**Manually Execute the Processing Script**

You can also run the `stat_var_processor.py` script individually for each file. This script is located in the `data/tools/statvar_importer/` directory.

Here are the specific commands for each file:

```bash
python3 ../../../tools/statvar_importer/stat_var_processor.py --input_data=source_files/employmentstatus_data.csv --pv_map=employmentstatus_pvmap.csv --config_file=employmentstatus_metadata.csv --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf --output_path=output/employmentstatus --output_counters=counters/employmentstatus_counters.csv

python3 ../../../tools/statvar_importer/stat_var_processor.py --input_data=source_files/sexandeducationalattainment_unemploymentstatus_data.csv --pv_map=sexandeducationalattainment_unemploymentstatus_pvmap.csv --config_file=sexandeducationalattainment_unemploymentstatus_metadata.csv --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf --output_path=output/sexandeducationalattainment_unemploymentstatus --output_counters=counters/sexandeducationalattainment_unemploymentstatus_counters.csv

python3 ../../../tools/statvar_importer/stat_var_processor.py --input_data=source_files/unemploymentrate_by_gender_age_data.csv --pv_map=unemploymentrate_by_gender_age_pvmap.csv --config_file=unemploymentrate_by_gender_age_metadata.csv --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf --output_path=output/unemploymentrate_by_gender_age --output_counters=counters/unemploymentrate_by_gender_age_counters.csv

python3 ../../../tools/statvar_importer/stat_var_processor.py --input_data=source_files/unemploymentstatus_data.csv --pv_map=unemploymentstatus_pvmap.csv --config_file=unemploymentstatus_metadata.csv --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf --output_path=output/unemploymentstatus --output_counters=counters/unemploymentstatus_counters.csv
```
#### Copyright 2025 Google LLC
####
#### Licensed under the Apache License, Version 2.0 (the "License");
#### you may not use this file except in compliance with the License.
#### You may obtain a copy of the License at
####
####        [http://www.apache.org/licenses/LICENSE-2.0](http://www.apache.org/licenses/LICENSE-2.0)
####
#### Unless required by applicable law or agreed to in writing, software
#### distributed under the License is distributed on an "AS IS" BASIS,
#### WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#### See the License for the specific language governing permissions and
#### limitations under the License.

## SouthKorea_Employment Import

This import contains statistical data related to employment, unemployment rates, and employment status in South Korea, including breakdowns by gender, age, and education level.

-----

### ⚙️ How to Use

The workflow for this data import involves two main steps: Manually downloading the necessary files and then processing them.

#### Step 1: Download the Data

- **Source:** [South Korea Statistics Agency (KOSA)](https://kosis.kr/eng/statisticsList/statisticsListIndex.do)
- **Description:** The website provides a wide range of statistical data about South Korea, including population, economy, and social indicators. It serves as a comprehensive resource for information about the country's employment statistics.

To get the necessary data files, you'll need to manually download source files related to employment from the KOSA website.

**Employment Status**: <https://kosis.kr/statHtml/statHtml.do?sso=ok&returnurl=https%3A%2F%2Fkosis.kr%3A443%2FstatHtml%2FstatHtml.do%3Flist_id%3DB17%26obj_var_id%3D%26seqNo%3D%26tblId%3DDT_1DA7010S%26vw_cd%3DMT_ETITLE%26language%3Den%26orgId%3D101%26path%3D%252Feng%252FstatisticsList%252FstatisticsListIndex.do%26conn_path%3DMT_ETITLE%26itm_id%3D%26lang_mode%3Den%26scrId%3D%26>

**Unemployment status by gender and age**:<https://kosis.kr/statHtml/statHtml.do?sso=ok&returnurl=https%3A%2F%2Fkosis.kr%3A443%2FstatHtml%2FstatHtml.do%3Flist_id%3DB16%26obj_var_id%3D%26seqNo%3D%26tblId%3DDT_1DA7087S%26vw_cd%3DMT_ETITLE%26language%3Den%26orgId%3D101%26path%3D%252Feng%252FstatisticsList%252FstatisticsListIndex.do%26conn_path%3DMT_ETITLE%26itm_id%3D%26lang_mode%3Den%26scrId%3D%26>

**Unemploymentrate**: <https://kosis.kr/statHtml/statHtml.do?sso=ok&returnurl=https%3A%2F%2Fkosis.kr%3A443%2FstatHtml%2FstatHtml.do%3Flist_id%3DB15%26obj_var_id%3D%26seqNo%3D%26tblId%3DDT_1DA7102S%26vw_cd%3DMT_ETITLE%26language%3Den%26orgId%3D101%26path%3D%252Feng%252FstatisticsList%252FstatisticsListIndex.do%26conn_path%3DMT_ETITLE%26itm_id%3D%26lang_mode%3Den%26scrId%3D%26>

**Unemployment status**: <https://kosis.kr/statHtml/statHtml.do?sso=ok&returnurl=https%3A%2F%2Fkosis.kr%3A443%2FstatHtml%2FstatHtml.do%3Flist_id%3DB16%26obj_var_id%3D%26seqNo%3D%26tblId%3DDT_1DA7088S%26vw_cd%3DMT_ETITLE%26language%3Den%26orgId%3D101%26path%3D%252Feng%252FstatisticsList%252FstatisticsListIndex.do%26conn_path%3DMT_ETITLE%26itm_id%3D%26lang_mode%3Den%26scrId%3D%26>

All downloaded files will be located into the gcs path `unresolved_mcf/country/southkorea/employment/source_files` and can be directly read from it while processing.

#### Autorefresh Type:

This import will be refreshed in a semi-automated manner.

-----

#### Step 2: Process the Files

After downloading the files, you can process them to generate the final output. There are two ways to do this:

**Option B: Manually Execute the Processing Script**

You can also run the `stat_var_processor.py` script individually for each file. This script is located in the `data/tools/statvar_importer/` directory.

Here are the specific commands for each file:

```bash
python3 ../../../tools/statvar_importer/stat_var_processor.py --input_data=gs://unresolved_mcf/country/southkorea/employment/source_files/employmentstatus_data.csv --pv_map=employmentstatus_pvmap.csv --config_file=employmentstatus_metadata.csv --places_resolved_csv=employmentstatus_places_resolved.csv --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf --output_path=output/employmentstatus


python3 ../../../tools/statvar_importer/stat_var_processor.py --input_data=gs://unresolved_mcf/country/southkorea/employment/source_files/sexandeducationalattainment_unemploymentstatus_data.csv --pv_map=sexandeducationalattainment_unemploymentstatus_pvmap.csv --config_file=sexandeducationalattainment_unemploymentstatus_metadata.csv --places_resolved_csv=sexandeducationalattainment_unemploymentstatus_places_resolved.csv --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf --output_path=output/sexandeducationalattainment_unemploymentstatus

python3 ../../../tools/statvar_importer/stat_var_processor.py --input_data=gs://unresolved_mcf/country/southkorea/employment/source_files/unemploymentrate_by_gender_age_data.csv --pv_map=unemploymentrate_by_gender_age_pvmap.csv --config_file=unemploymentrate_by_gender_age_metadata.csv --places_resolved_csv=unemploymentrate_by_gender_age_places_resolved.csv --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf --output_path=output/unemploymentrate_by_gender_age

python3 ../../../tools/statvar_importer/stat_var_processor.py --input_data=gs://unresolved_mcf/country/southkorea/employment/source_files/unemploymentstatus_data.csv --pv_map=unemploymentstatus_pvmap.csv --config_file=unemploymentstatus_metadata.csv --places_resolved_csv=unemploymentstatus_places_resolved.csv --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf --output_path=output/unemploymentstatus
```

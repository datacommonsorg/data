#### Copyright 2025 Google LLC
####
#### Licensed under the Apache License, Version 2.0 (the "License");
#### you may not use this file except in compliance with the License.
#### You may obtain a copy of the License at
####
####        http://www.apache.org/licenses/LICENSE-2.0
####
#### Unless required by applicable law or agreed to in writing, software
#### distributed under the License is distributed on an "AS IS" BASIS,
#### WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#### See the License for the specific language governing permissions and
#### limitations under the License.

## SouthKorea_Education Import

This import contains statistical data related to educational institutions in South Korea, including elementary, middle, and high schools, as well as kindergarten and junior colleges.

-----

### ⚙️ How to Use

The workflow for this data import involves two main steps: Manually downloading the necessary files and then processing them.

#### Step 1: Download the Data

- **Source:** [South Korea Statistics Agency (KOSA)](https://kosis.kr/eng/statisticsList/statisticsListIndex.do)
- **Description:** The website provides a wide range of statistical data about South Korea, including population, economy, and social indicators. It serves as a comprehensive resource for information about the country's educational statistics.

To get the necessary data files, you'll need to manually download source files related to education from the KOSA website.

**Middle School** : https://kosis.kr/statHtml/statHtml.do?sso=ok&returnurl=https%3A%2F%2Fkosis.kr%3A443%2FstatHtml%2FstatHtml.do%3Flist_id%3DH1_2%26obj_var_id%3D%26seqNo%3D%26tblId%3DDT_1963003_003%26vw_cd%3DMT_ETITLE%26language%3Den%26orgId%3D334%26path%3D%252Feng%252FstatisticsList%252FstatisticsListIndex.do%26conn_path%3DMT_ETITLE%26itm_id%3D%26lang_mode%3Den%26scrId%3D%26

**Kindergarten** :  https://kosis.kr/statHtml/statHtml.do?sso=ok&returnurl=https%3A%2F%2Fkosis.kr%3A443%2FstatHtml%2FstatHtml.do%3Flist_id%3DH1_2%26obj_var_id%3D%26seqNo%3D%26tblId%3DDT_1963003_001%26vw_cd%3DMT_ETITLE%26language%3Den%26orgId%3D334%26path%3D%252Feng%252FstatisticsList%252FstatisticsListIndex.do%26conn_path%3DMT_ETITLE%26itm_id%3D%26lang_mode%3Den%26scrId%3D%26

**Junior College** : https://kosis.kr/statHtml/statHtml.do?sso=ok&returnurl=https%3A%2F%2Fkosis.kr%3A443%2FstatHtml%2FstatHtml.do%3Flist_id%3DH1_2%26obj_var_id%3D%26seqNo%3D%26tblId%3DDT_1963003_011%26vw_cd%3DMT_ETITLE%26language%3Den%26orgId%3D334%26path%3D%252Feng%252FstatisticsList%252FstatisticsListIndex.do%26conn_path%3DMT_ETITLE%26itm_id%3D%26lang_mode%3Den%26scrId%3D%26

**High School** : https://kosis.kr/statHtml/statHtml.do?sso=ok&returnurl=https%3A%2F%2Fkosis.kr%3A443%2FstatHtml%2FstatHtml.do%3Flist_id%3DH1_2%26obj_var_id%3D%26seqNo%3D%26tblId%3DDT_1963003_004%26vw_cd%3DMT_ETITLE%26language%3Den%26orgId%3D334%26path%3D%252Feng%252FstatisticsList%252FstatisticsListIndex.do%26conn_path%3DMT_ETITLE%26itm_id%3D%26lang_mode%3Den%26scrId%3D%26

**Elementary School** : https://kosis.kr/statHtml/statHtml.do?sso=ok&returnurl=https%3A%2F%2Fkosis.kr%3A443%2FstatHtml%2FstatHtml.do%3Flist_id%3DH1_2%26obj_var_id%3D%26seqNo%3D%26tblId%3DDT_1963003_002%26vw_cd%3DMT_ETITLE%26language%3Den%26orgId%3D334%26path%3D%252Feng%252FstatisticsList%252FstatisticsListIndex.do%26conn_path%3DMT_ETITLE%26itm_id%3D%26lang_mode%3Den%26scrId%3D%26


All downloaded files will be located into the gcs path `unresolved_mcf/country/southkorea/education/source_files` and can be directly read from it while processing.

#### Autorefresh Type:

This import will be refreshed in a semi-automated manner.

-----

#### Step 2: Process the Files

After downloading the files, you can process them to generate the final output. There are two ways to do this:

**Option B: Manually Execute the Processing Script**

You can also run the `stat_var_processor.py` script individually for each file. This script is located in the `data/tools/statvar_importer/` directory.

Here are the specific commands for each file:

```bash
python3 ../../../tools/statvar_importer/stat_var_processor.py --input_data=gs://unresolved_mcf/country/southkorea/education/source_files/elementary_school_data.csv --pv_map=elementary_school_pvmap.csv --config_file=elementary_school_metadata.csv --places_resolved_csv=elementary_school_places_resolved.csv --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf --output_path=output/elementary_school

python3 ../../../tools/statvar_importer/stat_var_processor.py --input_data=gs://unresolved_mcf/country/southkorea/education/source_files/junior_college_data.csv --pv_map=junior_college_pvmap.csv --config_file=junior_college_metadata.csv --places_resolved_csv=junior_college_places_resolved.csv --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf --output_path=output/junior_college

python3 ../../../tools/statvar_importer/stat_var_processor.py --input_data=gs://unresolved_mcf/country/southkorea/education/source_files/junior_college_data.csv --pv_map=junior_college_pvmap.csv --config_file=junior_college_metadata.csv --places_resolved_csv=junior_college_places_resolved.csv --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf --output_path=output/junior_college

python3 ../../../tools/statvar_importer/stat_var_processor.py --input_data=gs://unresolved_mcf/country/southkorea/education/source_files/kindergarten_data.csv --pv_map=kindergarten_pvmap.csv --config_file=kindergarten_metadata.csv --places_resolved_csv=kindergarten_places_resolved.csv --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf --output_path=output/kindergarten

python3 ../../../tools/statvar_importer/stat_var_processor.py --input_data=gs://unresolved_mcf/country/southkorea/education/source_files/middle_school_data.csv --pv_map=middle_school_pvmap.csv --config_file=middle_school_metadata.csv --places_resolved_csv=middle_school_places_resolved.csv --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf --output_path=output/middle_school

```
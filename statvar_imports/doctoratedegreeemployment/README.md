
/*
 * Copyright 2023 Google LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */


NCSES_DoctorateDegreeEmployment
source: https://ncses.nsf.gov/pubs/nsf19304/assets/data/tables/wmpd19-sr-tab09-026.xlsx

how to download data: Download script (download_util_script.py). To download the data, you'll need to use the provided download script,download_util_script.py. This script will automatically create an input_files folder. where you should place the file to be processed. 

type of place: State.

statvars: Demographics

years: 2017

place_resolution: Places resolved to wikidataId in metadata sheet itself.


Command to download using the download util.

python3 add_years.py  --output_folder="source_files" --unzip=False


#### Processing the data:


How to run:
python3 stat_var_processor.py  --input_data='../../statvar_imports/doctoratedegreeemployment/test_data/<filename>.xlsx' --pv_map='../../statvar_imports/doctoratedegreeemployment/<filename>.csv' --config='../../statvar_imports/doctoratedegreeemployment/<filename>.csv' --output_path='../../statvar_imports/doctoratedegreeemployment/test_data /<filename>'


Example

Processing
python3 stat_var_processor.py --input_data='../../statvar_imports/doctoratedegreeemployment/test_data/sample_input.csv' --pv_map='../../statvar_imports/doctoratedegreeemployment/pv_map.csv' --config='../../statvar_imports/doctoratedegreeemployment/metadata.csv' --output_path='../../statvar_imports/doctoratedegreeemployment/test_data/sample_output'



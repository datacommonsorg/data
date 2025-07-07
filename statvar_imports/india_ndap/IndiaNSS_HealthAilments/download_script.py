#Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 20 ('License');
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#           https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an 'AS IS' BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# How to run the script to download the files:
# python3 download_script.py
import json
import os
import pandas as pd
import sys
from absl import app
from absl import flags
from absl import logging
from google.cloud import storage
flags.DEFINE_string(
        'config_file_path',
        'gs://datcom-import-test/statvar_imports/india_ndap/IndiaNSS_HealthAilments/IndiaNSS_HealthAilments/download_config.json',
        'Input directory where config files downloaded.')

_SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(_SCRIPT_PATH, '../../../util/')) 
from download_util_script import _retry_method


def main(_):
    all_data = []
    _FLAGS = flags.FLAGS 
    config_file_path = _FLAGS.config_file_path
    storage_client = storage.Client()
    bucket_name =  config_file_path.split('/')[2]
    bucket = storage_client.bucket(bucket_name)
    blob_name = '/'.join(config_file_path.split('/')[3:])
    blob = bucket.blob(blob_name)
    file_contents = blob.download_as_text()
    try:
        file_config = json.loads(file_contents)
        url = file_config.get('url')
        input_files = file_config.get('input_files') 
    except json.JSONDecodeError:
        logging.fatal("Cannot extract url and input files path.")
    page_num = 1 
    while True: 
        api_url = f"{url}&pageno={page_num}"
        response = _retry_method(api_url, None, 3, 5, 2)
        response_data = response.json()
        if response_data and 'Data' in response_data and len(response_data['Data']) > 0:
            keys = response_data['Data']
            try:
                if not isinstance(keys, list):
                    logging.fatal(f"Value for key 'Data' is not a list.")
            except KeyError as e:
                logging.fatal(f"Missing expected key '{e}' in the API response.")
                break 
            # Considering the table id I7375_4 which is specific to the import.
            for i in keys:
                a = (i['StateName'], i['TRU'],i['D7300_3'],i['D7300_4'],i['D7300_5'],i['I7300_6']['TotalPopulationWeight'],i['I7300_7']['avg'],i['I7300_8']['avg'],i['Year'].split(",")[-1].strip(), str(int(i['Year'].split(",")[-1].strip()) + 1),i['Year'].split(",")[-1].strip(), i['Year'])
                all_data.append(a)
            page_num += 1 
        else:
            logging.error(f"failed to retrieve data from page {page_num}")
            break
    if all_data:
        df = pd.DataFrame(all_data, columns=['srcStateName','TRU','GENDER', 'Broad ailment category','Age group','Ailments reported for each Broad caliment category per 100000 persons during last 15 days by different age groups','Estimated number of ailments under broad ailment category', 'Sample number of ailments under broad ailment category', 'srcYear', 'future year','YearCode', 'Year'])
        os.makedirs(input_files, exist_ok=True)
        input_filename = os.path.join('IndiaNSS_HealthAilments.csv')
        df.to_csv(input_filename, index=False)
        logging.info("Data saved to ndiaNSS_HealthAilments.csv")
    else:
        logging.info("No data was retrieved from the API.")

if __name__=="__main__":
    app.run(main)
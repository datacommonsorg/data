# Copyright 2025 Google LLC
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
import numpy as np
import sys
from absl import app
from absl import flags
from absl import logging
from google.cloud import storage
flags.DEFINE_string(
        'download_config_path',
        'gs://unresolved_mcf/india_ndap/ndap/download_config.json',
        'Input directory where config files downloaded.')

_SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(_SCRIPT_PATH, '../../../util/')) 
from download_util_script import _retry_method


def main(_):
    all_data = []
    _FLAGS = flags.FLAGS 
    download_config_path = _FLAGS.download_config_path
    storage_client = storage.Client()
    bucket_name =  download_config_path.split('/')[2]
    bucket = storage_client.bucket(bucket_name)
    blob_name = '/'.join(download_config_path.split('/')[3:])
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
            
            for i in keys:
                a = a=i['Country'],i['StateName'],i['Year'],i['D7375_3'],i['D7375_4'],i['I7375_5']['TotalPopulationWeight']
                all_data.append(a)
            page_num += 1 
        else:
            logging.error(f"failed to retrieve data from page {page_num}")
            break
    if all_data:
       
        df = pd.DataFrame(all_data, columns=['Country', 'State/UT', 'Year', 'Time period', 'Gender', 'Life expectancy in years'])
        os.makedirs(input_files, exist_ok=True)
        df["Temp_year"] = df["Time period"].str[5:].astype(int)
        input_filename = os.path.join(input_files, 'India_LifeExpectancy_input.csv')
        df["OBS_Year"] = np.where(df["Temp_year"]>90,
                                  1900+df["Temp_year"],
                                  2000+df["Temp_year"])
        df.drop(columns="Temp_year",inplace=True)
        df=df[['Country', 'State/UT', 'Year', 'Time period', 'OBS_Year', 'Gender', 'Life expectancy in years']]
        df.to_csv(input_filename, index=False)
        logging.info("Data saved to India_LifeExpectancy_input.csv")
    else:
        logging.info("No data was retrieved from the API.")

if __name__=="__main__":
    app.run(main)
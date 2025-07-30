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
import os
import sys
from absl import app
from absl import logging
import csv
_SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(_SCRIPT_PATH, '../../../util/')) 
from download_util_script import _retry_method


def main(_):

    url = "https://api.census.gov/data/timeseries/healthins/sahie?get=NIC_PT,NAME,NUI_PT,YEAR&for=county:*&in=state:01&AGECAT=0&SEXCAT=0&IPRCAT=0"

    api_url = f"{url}"
    try:
        response = _retry_method(api_url, None, 3, 5, 2)
        response_data = response.json()

        if response_data and isinstance(response_data, list) and len(response_data) > 1:
            headers = response_data[0]
            # data start from row 2
            data_rows = response_data[1:]
            # Processing each data row into a dictionary
            structured_data = []
            for row in data_rows:
                if len(row) == len(headers):
                    row_dict = dict(zip(headers, row))
                    structured_data.append(row_dict)
                else:
                    logging.warning(f"Skipping malformed row: {row}. Length mismatch with headers.")

            # csv creation logic
            if structured_data: 
                csv_filepath = "census_sahie_data.csv"
                with open(csv_filepath, 'w', newline='', encoding='utf-8') as csvfile:
                    fieldnames = headers 
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writeheader() 
                    writer.writerows(structured_data) 

                logging.info(f"Successfully wrote data to {csv_filepath}")
            else:
                logging.info("No structured data to write to CSV.")

        else:
            logging.info("No data or malformed data was retrieved from the API.")

    except Exception as e:
        logging.error(f"An error occurred during API call or data processing: {e}")


if __name__ == "__main__":
    app.run(main)
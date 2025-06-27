# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#How to run the script python3 download_script.py

import csv
import json
import os
import sys
from absl import app
from absl import flags
from absl import logging
from google.cloud import storage
flags.DEFINE_string(
        'config_file_path',
        'gs://datcom-import-test/statvar_imports/singapore_census/download_config.json',
        'Input directory where config files downloaded.')

_SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(_SCRIPT_PATH, '../../util/')) 
from download_util_script import _retry_method


def data_extraction(json_string):
    """
    Extracts data from the JSON string and structures it horizontally.
    Each row in the output will represent a series, with 'Series Name' as the
    first column, and subsequent columns for each year, containing the corresponding value.

    Args:
        json_string: A string containing the JSON data.

    Returns:
        A tuple:
        - A list of dictionaries, where each dictionary represents a row for the CSV.
          Keys are 'Series Name' and the years (e.g., '1960', '1961').
        - A list of all unique years found in the data, sorted in ascending order.
    """
    data = json.loads(json_string)
    
    horizontal_rows = []
    all_unique_years = set()

    # getting 'row' array within the 'Data' object
    if "Data" in data and "row" in data["Data"]:
        for series_obj in data["Data"]["row"]:
            row_text = series_obj.get("rowText") 
            current_row_data = {"Series Name": row_text}
        
            # Process the 'columns' array which contains year-value pairs
            if "columns" in series_obj:
                for col in series_obj["columns"]:
                    year = col.get("key")  
                    value = col.get("value") 
                    if year is not None and value is not None:
                        current_row_data[year] = value # Add year and value to the current row
                        all_unique_years.add(year)     # Keeping the  track of all unique years encountered
            
            horizontal_rows.append(current_row_data)

    # Sorted  the unique years numerically for consistent column order in the CSV
    sorted_years = sorted(list(all_unique_years), key=int) 
    
    # filling missing values with an empty string for consistent CSV output.
    processed_rows = []
    for row in horizontal_rows:
        new_row = {"Data Series": row.get("Series Name", "")}
        for year in sorted_years:
            # Get the value for the year, or an empty string if not present in this series' data
            new_row[year] = row.get(year, '') 
        processed_rows.append(new_row)

    return processed_rows, sorted_years

def main(argv):
    try:
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
            
        hdr = {'User-Agent': 'Mozilla/5.0', "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,/;q=0.8"}
        response=_retry_method(url, hdr, 3, 5, 2)
        data_from_url = response.content
        json_data_string = data_from_url.decode('utf-8')
        logging.info("Successfully fetched data from URL.")
        horizontal_rows_data, all_years_columns = data_extraction(json_data_string)
        if horizontal_rows_data:
            logging.info("cleaned data is successfully created")
        else:
            logging.info("No data rows processed.")
            
        os.makedirs(input_files, exist_ok=True)  
        csv_filename = os.path.join(input_files, "singapore_census_data.csv")
        if horizontal_rows_data:
            #adding the 1st columns observationAbout with the constant value 'country/SGP'
            for row in horizontal_rows_data:
                row['observationAbout'] = 'country/SGP'
            fieldnames = ["observationAbout", "Data Series"] + all_years_columns
            with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    
                writer.writeheader() 
                writer.writerows(horizontal_rows_data) 
                
            logging.info(f"\nData successfully saved to {csv_filename}")
        else:
            logging.info("\nNo data rows found to save to CSV.")

    except Exception as e:
        logging.fatal(f"An unexpected error occurred while fetching or processing data: {e}")

if __name__ == "__main__":
    app.run(main)
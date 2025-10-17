# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the 'License');
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#             https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an 'AS IS' BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json
import os
import sys
import csv
import shutil
from absl import app
from absl import logging
import pandas as pd
from urllib.parse import urlparse

_SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(_SCRIPT_PATH, '../../util/'))

from download_util_script import download_file

_CONFIG_PATH = os.path.join(_SCRIPT_PATH, 'import_config.json')
_OUTPUT_DIRECTORY = os.path.join(_SCRIPT_PATH, 'input_files')



def rename_total(filepath):
   
    df = pd.read_csv(filepath, sep=',')
    df.columns = df.columns.str.strip() 
   
    if 'Total' in df.columns:
        df = df.rename(columns={'Total': 'value'})
    df.to_csv(filepath, index=False)

def clean_and_rename_total(filepath):
    try:
        rename_total(filepath)
        df = pd.read_csv(filepath)
        df.columns = df.columns.str.strip()
        try:
            df['value'] = df['value'].astype(str)
            df['value'] = df['value'].str.replace('.', '', regex=False)
            df['value'] = df['value'].str.replace(',', '.', regex=False)
            df['value'] = pd.to_numeric(df['value'], errors='coerce')

        except Exception as e:
            logging.fatal(f"An error occurred while cleaning the 'value' column: {e}")
        df.to_csv(filepath, index=False)
        

    except pd.errors.ParserError as e:
        logging.fatal(f"Error parsing the CSV file: {e}. Please check the file format.")
    except Exception as e:
        logging.fatal(f"An unexpected error occurred: {e}")

def convert_tsv_to_csv(file_path):
    """
    Converts a tab-separated file to a comma-separated file in-place.
    """
    temp_file_path = file_path + ".tmp"
    try:
        with open(file_path, 'r', encoding='utf-8') as infile, open(
                temp_file_path, 'w', encoding='utf-8', newline='') as outfile:
            reader = csv.reader(infile, delimiter='\t')
            writer = csv.writer(outfile, delimiter=',')
            for row in reader:
                writer.writerow(row)

        shutil.move(temp_file_path, file_path)
        logging.info(
            f"Successfully converted {os.path.basename(file_path)} to CSV.")
    except Exception as e:
        logging.error(f"Error converting file {file_path}: {e}")
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        raise


def main(_):
    os.makedirs(_OUTPUT_DIRECTORY, exist_ok=True)
    logging.info(
        f"Base output directory '{_OUTPUT_DIRECTORY}' ensured to exist.")

    with open(_CONFIG_PATH, 'r') as f:
        config = json.load(f)

    for item in config.get('imports', []):
        url, filename = item.get('url'), item.get('filename')
        if not url or not filename:
            logging.warning(f"Skipping invalid entry in config: {item}")
            continue

        # download_file needs to be able to resolve to the final location
        if not download_file(url, _OUTPUT_DIRECTORY, False):
            logging.error(f"Failed to download {filename} from {url}.")
            continue

        original_filename = os.path.basename(urlparse(url).path)
        original_filepath = os.path.join(_OUTPUT_DIRECTORY, original_filename)
        csv_filename = os.path.splitext(filename)[0] + '.csv'
        output_path = os.path.join(_OUTPUT_DIRECTORY, csv_filename)

        if os.path.exists(original_filepath):
            os.rename(original_filepath, output_path)
            logging.info(f"Downloaded and renamed to {csv_filename}.")
            try:
                convert_tsv_to_csv(output_path)
            except Exception as e:
                logging.error(f"Failed to convert {csv_filename}: {e}")
        else:
            logging.error(
                f"Downloaded file not found at {original_filepath}")
    activity_file = os.path.join(_OUTPUT_DIRECTORY, "activity_employment_unemployment_by_sex.csv")
    education_file = os.path.join(_OUTPUT_DIRECTORY, "Levels_of_education_gender.csv")
    population_file = os.path.join(_OUTPUT_DIRECTORY,"Population_by_sex_and_age_group.csv")
    rename_total(activity_file)
    rename_total(education_file)
    clean_and_rename_total(population_file)


if __name__ == '__main__':
    app.run(main)
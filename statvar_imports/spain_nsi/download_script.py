# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the 'License');
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#         https://www.apache.org/licenses/LICENSE-2.0
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


def clean_and_rename_total(filepath):
    """
    Efficiently processes a specific CSV file by combining renaming, cleaning,
    and dropping 'Percentage: 100' rows.
    """
    try:
        # Read the file once
        df = pd.read_csv(filepath)
        df.columns = df.columns.str.strip()

        # Perform the logic from rename_total in memory
        if 'Total' in df.columns:
            df = df.rename(columns={'Total': 'value'})

        # Clean the 'value' column
        if 'value' in df.columns:
            # First, clean the value to prepare it for numeric conversion
            value_col_cleaned = df['value'].astype(str).str.replace('.', '',
                                                                    regex=False)
            value_col_cleaned = value_col_cleaned.str.replace(',', '.',
                                                              regex=False)
            numeric_values = pd.to_numeric(value_col_cleaned, errors='coerce')
            
            # Now, assign the cleaned numeric values back to the 'value' column
            df['value'] = numeric_values
        
        # --- LOGIC TO DROP PERCENTAGE=100 ROWS ---
        if 'Unit' in df.columns and 'value' in df.columns:
            
            # --- MODIFIED LINE ---
            # Made the 'Unit' check case-insensitive (.str.lower())
            condition_to_drop = (df['Unit'].str.strip().str.lower() == 'percentage') & \
                                (df['value'] == 100)
            # --- END OF MODIFICATION ---

            rows_to_drop = condition_to_drop.sum()
            if rows_to_drop > 0:
                logging.info(f"Dropping {rows_to_drop} 'Percentage: 100' rows from {os.path.basename(filepath)}.")
                # Keep only the rows that DO NOT meet the drop condition
                df = df[~condition_to_drop]
        # --- END OF DROP LOGIC ---

        # Write the file once
        df.to_csv(filepath, index=False)

    except pd.errors.ParserError as e:
        logging.error(
            f"Error parsing the CSV file: {e}. Please check the file format.")
    except Exception as e:
        logging.error(f"An unexpected error occurred in {filepath}: {e}")


def convert_tsv_to_csv(file_path):
    """
    Converts a tab-separated file to CSV. Skips if the file does not appear
    to be a TSV.
    """
    temp_file_path = file_path + ".tmp"
    try:
        with open(file_path, 'r', encoding='utf-8') as infile:
            first_line = infile.readline()
            # Check for tabs in the header to guess if it's a TSV
            if '\t' not in first_line:
                logging.info(
                    f"Skipping conversion for {os.path.basename(file_path)} as it doesn't appear to be a TSV."
                )
                return
            # Reset file pointer to the beginning to read the whole file
            infile.seek(0)

            with open(temp_file_path, 'w', encoding='utf-8',
                      newline='') as outfile:
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

    # --- ALL FILE PATHS ---
    activity_file = os.path.join(_OUTPUT_DIRECTORY,
                                 "activity_employment_unemployment_by_sex.csv")
    education_file = os.path.join(_OUTPUT_DIRECTORY,
                                  "Levels_of_education_gender.csv")
    population_file = os.path.join(_OUTPUT_DIRECTORY,
                                   "Population_by_sex_and_age_group.csv")
    education_field_file = os.path.join(_OUTPUT_DIRECTORY,
                                      "Education_Field_of_study.csv")
    
    # --- CALLING THE CLEAN FUNCTION FOR ALL FILES ---
    # This will now apply the drop logic to every file
    
    if os.path.exists(activity_file):
        clean_and_rename_total(activity_file)
    else:
        logging.warning(f"File not found, skipping: {activity_file}")
        
    if os.path.exists(education_file):
        clean_and_rename_total(education_file)
    else:
        logging.warning(f"File not found, skipping: {education_file}")
        
    if os.path.exists(population_file):
        clean_and_rename_total(population_file)
    else:
        logging.warning(f"File not found, skipping: {population_file}")
        
    if os.path.exists(education_field_file):
        clean_and_rename_total(education_field_file)
    else:
        logging.warning(f"File not found, skipping: {education_field_file}")


if __name__ == '__main__':
    app.run(main)
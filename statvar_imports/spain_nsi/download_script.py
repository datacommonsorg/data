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


def clean_and_rename_total(filepath, decimal_style='.'):
    """
    Efficiently processes a specific CSV file by combining renaming, cleaning,
    and dropping 'Percentage: 100' rows.

    Args:
        filepath: Path to the CSV file.
        decimal_style: The character used as a decimal separator (',' or '.').
    """
    try:
        # --- Set pandas read_csv parameters based on the style ---
        thousands_char = None
        decimal_char = '.'
        
        if decimal_style == ',':
            # European-style: "1.234,56"
            thousands_char = '.'
            decimal_char = ','
            logging.debug(f"Reading {os.path.basename(filepath)} with decimal=',' and thousands='.'")
        
        elif decimal_style == '.':
            # American-style: "1,234.56"
            thousands_char = ','
            decimal_char = '.'
            logging.debug(f"Reading {os.path.basename(filepath)} with decimal='.' and thousands=','")
        
        # --- Optimistic Read ---
        # Try to read the file, letting pandas handle number formats
        df = pd.read_csv(filepath, 
                         thousands=thousands_char, 
                         decimal=decimal_char, 
                         low_memory=False)

        df.columns = df.columns.str.strip()

        # Perform the logic from rename_total in memory
        if 'Total' in df.columns:
            df = df.rename(columns={'Total': 'value'})

        # Clean the 'value' column
        if 'value' in df.columns:
            
            # If read_csv failed to parse (e.g., mixed types), 
            # the column will be 'object'. We must manually clean.
            if df['value'].dtype == 'object':
                logging.debug(f"'value' column in {os.path.basename(filepath)} is 'object', applying manual cleaning...")
                
                # Convert to string to be safe
                value_col_str = df['value'].astype(str)
                value_col_cleaned = None
                
                if decimal_style == ',':
                    # European-style: "8,9" -> 8.9 | "1.234" -> 1234
                    # 1. Remove thousand separators ('.')
                    value_col_cleaned = value_col_str.str.replace('.', '', regex=False)
                    # 2. Replace the comma decimal separator with a period ('.')
                    value_col_cleaned = value_col_cleaned.str.replace(',', '.', regex=False)
                
                elif decimal_style == '.':
                    # American-style: "8.9" -> 8.9 | "1,234" -> 1234
                    # 1. Remove thousand separators (',')
                    value_col_cleaned = value_col_str.str.replace(',', '', regex=False)
                
                else:
                    value_col_cleaned = value_col_str # Should not happen

                # Now, convert the fully cleaned string to numeric
                df['value'] = pd.to_numeric(value_col_cleaned, errors='coerce')
            
        # Logic to drop 'Percentage: 100' rows
        if 'Unit' in df.columns and 'value' in df.columns:
            
            condition_to_drop = (df['Unit'].str.strip().str.lower() == 'percentage') & \
                                (df['value'] == 100)

            rows_to_drop = condition_to_drop.sum()
            if rows_to_drop > 0:
                logging.info(f"Dropping {rows_to_drop} 'Percentage: 100' rows from {os.path.basename(filepath)}.")
                df = df[~condition_to_drop]

        # Write the file, formatting floats to 3 decimal places
        df.to_csv(filepath, index=False, float_format='%.3f')

    except pd.errors.ParserError as e:
        logging.error(
            f"Error parsing the CSV file: {e}. Please check the file format.")
        raise RuntimeError(f"Failed to parse CSV file: {filepath}") from e
    except Exception as e:
        logging.error(f"An unexpected error occurred in {filepath}: {e}")
        raise RuntimeError(f"Unexpected error processing file: {filepath}") from e


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

    # This list will store files to be cleaned after download
    # It will be a list of tuples: (full_filepath, decimal_style)
    files_to_process = []

    # --- Primary Download and Conversion Loop ---
    for item in config.get('imports', []):
        url = item.get('url')
        filename = item.get('filename') # This is the .tsv filename from config
        
        # Get the new decimal_style from the config.
        # It defaults to '.' if you forget to add it.
        decimal_style = item.get('decimal_style', '.') 
        
        if not url or not filename:
            logging.warning(f"Skipping invalid entry in config: {item}")
            continue

        if not download_file(url, _OUTPUT_DIRECTORY, False):
            logging.error(f"Failed to download {filename} from {url}.")
            continue

        original_filename = os.path.basename(urlparse(url).path)
        original_filepath = os.path.join(_OUTPUT_DIRECTORY, original_filename)
        
        # This is the final name, e.g., "activity_employment_unemployment_by_sex.csv"
        csv_filename = os.path.splitext(filename)[0] + '.csv'
        # This is the full path to that file
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

        # Add the successfully downloaded/converted file to our list
        # for processing.
        if os.path.exists(output_path):
            files_to_process.append( (output_path, decimal_style) )

    # --- Post-Processing and Cleaning Loop ---
    logging.info("Starting post-download cleaning...")

    for file_path, style in files_to_process:
        # A final check to ensure the file exists
        if os.path.exists(file_path):
            try:
                # Call the cleaning function, passing the correct style
                # for this specific file.
                clean_and_rename_total(file_path, decimal_style=style)
            except Exception as e:
                # Log errors but continue processing other files
                logging.error(f"Failed to clean {os.path.basename(file_path)}: {e}")
        else:
            logging.warning(f"File not found, skipping: {file_path}")


if __name__ == '__main__':
    app.run(main)
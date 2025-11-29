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

import os
import sys
from absl import app
from absl import logging
import datetime
import glob
import shutil
import pandas as pd
import re

_SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))

sys.path.append(os.path.join(_SCRIPT_PATH, '../../util/'))

from download_util_script import download_file

logging.set_verbosity(logging.INFO)

_BASE_URL = "https://civilrightsdata.ed.gov/assets/ocr/docs/{year_range}-crdc-data.zip"
_OUTPUT_DIRECTORY = "input_files"
_START_YEAR = 2009
_CURRENT_YEAR = datetime.datetime.now().year


def add_year_column(filepath: str, year: int):
    """Adds a 'year' column as the first column to the given CSV or XLSX file."""
    try:
        # Determine file type and read the DataFrame
        if filepath.endswith('.csv'):
            df = pd.read_csv(filepath, encoding='utf-8', low_memory=False, dtype=str)
        elif filepath.endswith('.xlsx'):
            df = pd.read_excel(filepath, dtype=str)
        else:
            logging.warning(f"Unsupported file type for year column addition: {filepath}")
            return

        # Added the 'year' column
        df['year'] = year

        # Reordered the columns to put 'year' first
        cols = list(df.columns)
        if 'year' in cols:
            cols.remove('year')
            new_cols = ['year'] + cols
            df = df[new_cols]
        else:
            logging.warning(f"'year' column not found for reordering in {filepath}.")

        if filepath.endswith('.csv'):
            df.to_csv(filepath, index=False)
        elif filepath.endswith('.xlsx'):
            with pd.ExcelWriter(filepath) as writer:
                df.to_excel(writer, index=False, sheet_name='Sheet1')
            
        logging.info(
            f"Added 'year' column with value {year} as the FIRST column to {os.path.basename(filepath)}"
        )
    except Exception as e:
        # Log the error so you see the filename
        logging.error(f"Could not add year column to {filepath}: {e}")
        # Kill the script immediately so you don't get bad data
        raise RuntimeError(e)
        



def main(_):
    os.makedirs(_OUTPUT_DIRECTORY, exist_ok=True)
    logging.info(f"Base output directory '{_OUTPUT_DIRECTORY}' ensured to exist.")

    # CRDC data typically follows an odd-year reporting schedule (e.g., 2009-10, 2011-12)
    years_to_try = list(range(_START_YEAR, 2018, 2)) + list(
        range(2020, _CURRENT_YEAR + 1, 2))

    for year in years_to_try:
        year_range = f"{year}-{str(year+1)[-2:]}"
        url = _BASE_URL.format(year_range=year_range)

        # Download to a temporary sub-folder
        temp_output_dir = os.path.join(_OUTPUT_DIRECTORY, f"{year_range}")
        os.makedirs(temp_output_dir, exist_ok=True)

        success = download_file(url=url,
                                output_folder=temp_output_dir,
                                unzip=True)

        if not success:
            logging.warning(
                f"Failed to download or process data for year {year}. Skipping cleanup and continuing."
            )
            shutil.rmtree(temp_output_dir, ignore_errors=True)
            continue

        logging.info(f"Successfully downloaded and extracted data for {year_range}.")

        # Find, rename, and move the files we want to keep
        search_pattern = os.path.join(temp_output_dir, '**', '*')
        
        # Define the target category
        category_name = "school finance"
        category_dir = _OUTPUT_DIRECTORY

        for item_path in glob.glob(search_pattern, recursive=True):
            if not os.path.isfile(item_path):
                continue

            filename = os.path.basename(item_path)
            base, extension = os.path.splitext(filename)
            extension = extension.lower()
            
            # Use a cleaner check for the required files
            if (extension in ['.csv', '.xlsx'] and 
                category_name in base.lower()):
                if 'lea' in base.lower() and extension == '.xlsx':
                    logging.info(f"Skipping and removing Excel file: '{filename}' because it contains 'LEA'.")
                    os.remove(item_path)
                    continue
            
                clean_base = re.sub(r'[^a-zA-Z0-9]+', '_', base).lower()

                new_filename = f"crdc_{year_range}_{clean_base}{extension}"
                new_filepath = os.path.join(category_dir, new_filename)

                logging.info(f"Moving '{item_path}' to '{new_filepath}'")
                shutil.move(item_path, new_filepath)

                # Add the year column (using the end year of the range)
                end_year = int(f"20{year_range.split('-')[1]}")
                add_year_column(new_filepath, end_year)

        # Clean up the temporary directory for the year
        logging.info(f"Removing temporary directory: {temp_output_dir}")
        shutil.rmtree(temp_output_dir, ignore_errors=True)

    logging.info("Script finished.")


if __name__ == '__main__':
    app.run(main)
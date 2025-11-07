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

"""
This script downloads SAIPE School District Estimates for 2003 to current year.
URL: https://www.census.gov/programs-surveys/saipe/data/datasets.html
"""
import os
import sys
import datetime
from absl import app
from absl import logging
import pandas as pd

# Allows the following module imports to work when running as a script
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(_SCRIPT_DIR, '../../../util/'))
from download_util_script import download_file

URL_TEMPLATE = "https://www2.census.gov/programs-surveys/saipe/datasets/{year}/{year}-school-districts/ussd{yy}.xls"
_OUTPUT_DIR = os.path.join(_SCRIPT_DIR, "input_files")


def _process_xls(filepath, year):
    """
    This helper function processes the downloaded xls file, removes the
    description and keeps the data with headers.
    """
    # Read the excel file without headers
    df = pd.read_excel(filepath, header=None)
    # Find the header row. We assume header contains 'State FIPS Code'.
    header_row_index = -1
    # Search for the header row which contains 'State FIPS Code'
    for i, row in df.iterrows():
        if 'State FIPS Code' in row.astype(str).values:
            header_row_index = i
            break

    if header_row_index != -1:
        # Set the found row as header
        df.columns = df.iloc[header_row_index]
        # Get all the data from next row onwards
        df = df[header_row_index + 1:]
        # Add the Year column
        df['Year'] = year
        # Save the processed data back to the same file, but as .xlsx
        # Pandas will automatically use 'openpyxl' for .xlsx files
        new_filepath = filepath.replace(".xls", ".xlsx")
        df.to_excel(new_filepath, index=False)
        # Remove the original .xls file
        os.remove(filepath)
        logging.info(f"Processed file: {filepath} and saved as {new_filepath}")
        logging.info(f"Processed file: {filepath}")
    else:
        logging.warning(f"Header not found in file: {filepath}")


def main(_):
    """Main function to download and process data for all years."""
    os.makedirs(_OUTPUT_DIR, exist_ok=True)

    current_year = datetime.datetime.now().year
    for year in range(2003, current_year + 1):
        yy = str(year)[2:]
        url = URL_TEMPLATE.format(year=year, yy=yy)
        logging.info(f"Downloading data for year {year} from {url}")

        success = download_file(url=url,
                                output_folder=_OUTPUT_DIR,
                                unzip=False)

        if success:
            file_path = os.path.join(_OUTPUT_DIR, f"ussd{yy}.xls")
            _process_xls(file_path, year)
            # Update file_path to the new .xlsx extension for subsequent operations if any
            file_path = file_path.replace(".xls", ".xlsx")
        else:
            logging.warning(
                f"Failed to download data for year {year}. Stopping.")
            break

    logging.info("Script processing completed.")


if __name__ == "__main__":
    app.run(main)

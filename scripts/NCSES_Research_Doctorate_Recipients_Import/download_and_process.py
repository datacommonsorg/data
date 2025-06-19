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

# How to run the script to process  the files:
# python3 download_and_process.py
import os
import sys
import pandas as pd
from absl import app
from absl import logging

_CODEDIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(1, _CODEDIR)
sys.path.insert(1, os.path.join(_CODEDIR, '../../util/'))

from download_util_script import download_file

logging.set_verbosity(logging.INFO)

download_configs = [{
    "url":
        "https://ncses.nsf.gov/pubs/nsf23300/assets/data-tables/tables/nsf23300-tab001-009.xlsx",
    "output_csv_name":
        "ncses_employed_male.csv"
}, {
    "url":
        "https://ncses.nsf.gov/pubs/nsf23300/assets/data-tables/tables/nsf23300-tab001-010.xlsx",
    "output_csv_name":
        "ncses_employed_female.csv"
}]

# data cleaning function


def process_and_modify_data_cascading(file_path):
    """
    Reads a file, modifies the first column by prepending the last encountered
    top-level header to subsequent non-header rows, and then removes the
    'Not Hispanic or Latino' row.

    Args:
        file_path (str): The path to the Excel or CSV file.

    Returns:
        pandas.DataFrame: The DataFrame with the first column modified and
                          the 'Not Hispanic or Latino' row removed.
                          Returns an empty DataFrame if an error occurs.
    """
    # list of top-level header keywords
    header_keywords = [
        'Male doctorate recipients', 'Female doctorate recipients',
        'Hispanic or Latino', 'Not Hispanic or Latino',
        'American Indian or Alaska Native', 'Asian',
        'Black or African American', 'White', 'More than one race',
        'Other race or race not reported', 'Ethnicity not reported'
    ]

    df = pd.DataFrame()
    try:
        if file_path.endswith('.csv'):
            df = pd.read_csv(file_path, header=None)
            logging.info(f"Successfully loaded CSV file: {file_path}")
        elif file_path.endswith('.xlsx') or file_path.endswith('.xls'):
            df = pd.read_excel(file_path, header=None)
            logging.info(f"Successfully loaded Excel file: {file_path}")
        else:
            logging.error(
                f"Error: Unsupported file type for '{file_path}'. Please use .csv, .xlsx, or .xls."
            )
            return df

    except FileNotFoundError:
        logging.fatal(f"Error: The file '{file_path}' was not found")
        return df
    except Exception as e:
        logging.fatal(f"An error occurred while reading the file: {e}")

        return df

    # variable to keep track of the last encountered top-level header
    last_known_header = None

    # Apply cascading logic
    for i in range(len(df)):
        current_cell_value = str(df.iloc[i, 0]).strip()

        # Check if the current cell value is one of the defined top-level headers
        if current_cell_value in header_keywords:
            # If it is a top-level header, updatating  'last_known_header'
            last_known_header = current_cell_value
        else:
            # If it's not a top-level header, and we have a last known header
            if last_known_header is not None:
                df.iloc[i, 0] = f"{last_known_header}:{current_cell_value}"
    row_to_remove = "Not Hispanic or Latino"
    original_rows_count = len(df)
    df_filtered = df[df.iloc[:, 0].astype(str).str.strip() != row_to_remove]
    removed_rows_count = original_rows_count - len(df_filtered)

    if removed_rows_count > 0:
        logging.info(
            f"Successfully removed {removed_rows_count} row(s) matching '{row_to_remove}'."
        )
    else:
        logging.info(
            f"No rows matching '{row_to_remove}' found to remove in this file.")

    return df_filtered


def main(argv):
    processed_files = []
    for config in download_configs:
        url = config["url"]
        desired_output_csv_name = config["output_csv_name"]

        logging.info(f"Attempting to download: {url}")

        file_name_from_url = url.split('/')[-1]
        downloaded_file_path = os.path.join("temp_downloads",
                                            file_name_from_url)
        try:

            download_successful = download_file(url=url,
                                                output_folder="temp_downloads",
                                                unzip=False,
                                                headers=None,
                                                tries=3,
                                                delay=5,
                                                backoff=2)

            if download_successful:
                logging.info(f"Download of '{file_name_from_url}' completed.")
            else:
                logging.error(
                    f"Download or processing of '{file_name_from_url}' failed")

            output_full_path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                desired_output_csv_name)

            modified_df = process_and_modify_data_cascading(
                downloaded_file_path)

            if not modified_df.empty:
                try:
                    modified_df.to_csv(output_full_path, index=False)
                    logging.info(
                        f"Successfully created new CSV file: {output_full_path}"
                    )
                    processed_files.append(desired_output_csv_name)
                except Exception as e:
                    logging.error(
                        f"An error occurred while creating the output CSV file for {file_name_from_url}: {e}"
                    )
            else:
                logging.error(
                    f"No data processed or loaded for {file_name_from_url}. Output CSV not created."
                )
        except FileNotFoundError:
            logging.fatal(
                f"Error: Python interpreter or download script not found. Check your paths."
            )
        except Exception as e:
            logging.fatal(
                f"An unexpected error occurred during the download/processing loop: {e}"
            )

    if processed_files:
        logging.info("All requested files processed")
    else:
        logging.error("No files were successfully processed. ---")


if __name__ == '__main__':
    app.run(main)

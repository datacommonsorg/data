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
"""Downloads files for illinois_education import."""

import json
import os
import re
import sys

import pandas as pd
from absl import app
from absl import logging

# Add the project root to the Python path.
_SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(_SCRIPT_PATH, '../../../', 'util'))

import download_util

_OUTPUT_DIRECTORY = "input_files"


def _convert_xlsx_to_csv(output_dir):
    """Converts all .xlsx files in the output directory to .csv files."""
    for filename in os.listdir(output_dir):
        if filename.endswith(".xlsx"):
            xlsx_path = os.path.join(output_dir, filename)
            try:
                xls = pd.ExcelFile(xlsx_path)
                for sheet_name in xls.sheet_names:
                    df = pd.read_excel(xls, sheet_name)
                    base_filename = os.path.splitext(filename)[0]
                    sanitized_base = re.sub(r'[\W_]+', '_', base_filename)
                    sanitized_sheet = re.sub(r'[\W_]+', '_', sheet_name)
                    csv_filename = f'{sanitized_base}_{sanitized_sheet}_data.csv'
                    csv_path = os.path.join(output_dir, csv_filename)
                    # Write the DataFrame to a CSV file without the index.
                    df.to_csv(csv_path, index=False)
                    logging.info(
                        f"Successfully converted '{sheet_name}' to '{csv_path}'"
                    )
                # Remove the original .xlsx file.
                os.remove(xlsx_path)
                logging.info(f"Successfully removed {xlsx_path}")
            except Exception as e:
                logging.error(f"Error processing {xlsx_path}: {e}")
                raise RuntimeError(f"Error processing {xlsx_path}: {e}")


def main(_):
    # Get the directory of the current script.
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Create the output directory.
    output_dir = os.path.join(script_dir, _OUTPUT_DIRECTORY)
    os.makedirs(output_dir, exist_ok=True)

    # Construct the path to the import config file.
    config_path = os.path.join(script_dir, 'import_config.json')

    # Read the import configuration.
    with open(config_path, 'r') as f:
        config = json.load(f)

    # Get the list of files to download.
    files_to_download = config.get('imports', {}).get('illinois_education', [])

    # Download each file.
    for file_info in files_to_download:
        url = file_info.get('url')
        filename = file_info.get('filename')
        if url and filename:
            output_path = os.path.join(output_dir, filename)
            logging.info(f"Downloading {url} to {output_path}...")
            if download_util.download_file_from_url(url,
                                                  output_file=output_path,
                                                  timeout=300):
                logging.info(f"Successfully downloaded {filename}.")
            else:
                logging.error(f"Failed to download {filename}.")
                raise RuntimeError(f"Failed to download {filename}.")
        else:
            logging.warning(f"Skipping invalid file info: {file_info}")

    # Convert all .xlsx files to .csv files.
    _convert_xlsx_to_csv(output_dir)


if __name__ == '__main__':
    app.run(main)

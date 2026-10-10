# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the 'License');
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#          https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an 'AS IS' BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json
import os
import sys
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
    Efficiently processes a specific CSV or TSV file by reading as text to handle
    number formatting safely, renaming columns, and dropping 'Percentage: 100' rows.

    Args:
        filepath: Path to the file.
        decimal_style: The character used as a decimal separator (',' or '.').
    """
    try:
        logging.debug(f"Processing {os.path.basename(filepath)} with decimal_style='{decimal_style}'")

        # Read as String (dtype=str) with Auto-Detected Separator (sep=None)
        # This prevents pandas from misinterpreting "76,3" as 763 before we can fix it.
        df = pd.read_csv(filepath, 
                         sep=None, 
                         engine='python', 
                         dtype=str)

        df.columns = df.columns.str.strip()

        # Rename Total -> value
        if 'Total' in df.columns:
            df = df.rename(columns={'Total': 'value'})

        # Manual Number Cleaning
        if 'value' in df.columns:
            value_col = df['value'].str.strip()
            
            if decimal_style == ',':
                # European: Remove thousands dot, replace decimal comma
                value_col = value_col.str.replace('.', '', regex=False)
                value_col = value_col.str.replace(',', '.', regex=False)
            
            elif decimal_style == '.':
                # American: Remove thousands comma
                value_col = value_col.str.replace(',', '', regex=False)

            # Convert to numeric now that the string is clean
            df['value'] = pd.to_numeric(value_col, errors='coerce')

        # Drop 'Percentage: 100' rows
        if 'Unit' in df.columns and 'value' in df.columns:
            condition_to_drop = (df['Unit'].str.strip().str.lower() == 'percentage') & \
                                (df['value'] == 100)

            rows_to_drop = condition_to_drop.sum()
            if rows_to_drop > 0:
                logging.info(f"Dropping {rows_to_drop} 'Percentage: 100' rows from {os.path.basename(filepath)}.")
                df = df[~condition_to_drop]

        # Write output as standard CSV
        df.to_csv(filepath, index=False, sep=',', float_format='%.3f')

    except Exception as e:
        logging.error(f"Error processing {filepath}: {e}")
        raise RuntimeError(f"Error processing {filepath}") from e


def main(_):
    os.makedirs(_OUTPUT_DIRECTORY, exist_ok=True)
    logging.info(
        f"Base output directory '{_OUTPUT_DIRECTORY}' ensured to exist.")

    with open(_CONFIG_PATH, 'r') as f:
        config = json.load(f)

    files_to_process = []

    # --- Primary Download Loop ---
    for item in config.get('imports', []):
        url = item.get('url')
        filename = item.get('filename')
        decimal_style = item.get('decimal_style', '.') 
        
        if not url or not filename:
            logging.warning(f"Skipping invalid entry in config: {item}")
            continue

        if not download_file(url, _OUTPUT_DIRECTORY, False):
            logging.error(f"Failed to download {filename} from {url}.")
            raise RuntimeError(f"Failed to download {filename} from {url}.")

        original_download_name = os.path.basename(urlparse(url).path)
        downloaded_filepath = os.path.join(_OUTPUT_DIRECTORY, original_download_name)
        final_filepath = os.path.join(_OUTPUT_DIRECTORY, filename)

        if os.path.exists(downloaded_filepath):
            os.rename(downloaded_filepath, final_filepath)
            logging.info(f"Downloaded and renamed to {filename}.")
        else:
            logging.error(f"Downloaded file not found at {downloaded_filepath}")
            raise RuntimeError(f"Downloaded file not found at {downloaded_filepath}")

        if os.path.exists(final_filepath):
            files_to_process.append((final_filepath, decimal_style))

    # --- Post-Processing and Cleaning Loop ---
    logging.info("Starting post-download cleaning...")

    for file_path, style in files_to_process:
        if os.path.exists(file_path):
            try:
                clean_and_rename_total(file_path, decimal_style=style)
            except Exception as e:
                logging.error(f"Failed to clean {os.path.basename(file_path)}: {e}")
                raise RuntimeError(f"Failed to clean {os.path.basename(file_path)}") from e
        else:
            logging.warning(f"File not found, skipping: {file_path}")


if __name__ == '__main__':
    app.run(main)

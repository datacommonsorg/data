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

import pandas as pd
import os
import sys
from decimal import Decimal, InvalidOperation
from absl import logging
from absl import app 

# --- GCS Configuration ---
GCS_BUCKET_NAME = "unresolved_mcf"
GCS_INPUT_PREFIX = "us_eda/latest/input_files"

# Get the directory of the current script
_MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
# Define the local working directory for both input and output files
LOCAL_WORKING_DIR = os.path.join(_MODULE_DIR, 'gcs_output')

PROJECT_ROOT = os.path.abspath(os.path.join(_MODULE_DIR, '..', '..', '..'))
sys.path.insert(0, PROJECT_ROOT)

# Add the 'data/util' directory to sys.path.
# This is crucial because file_util.py expects to find aggregation_util.py
# as a direct module import ('from aggregation_util import ...'),
# and both are located within 'data/util/'.
sys.path.insert(0, os.path.join(PROJECT_ROOT, 'data', 'util'))


# Now, directly import file_util.
# This assumes file_util.py is located at data/util/file_util.py relative to PROJECT_ROOT.
try:
    from data.util import file_util
except ImportError as e:
    logging.fatal(f"Failed to import file_util: {e}. Please ensure data/util/file_util.py exists and is accessible, and that the project root and data/util are correctly set in sys.path.", exc_info=True)
  


us_states = {
    "Alabama", "Alaska", "American Samoa", "Arizona", "Arkansas", "California",
    "Colorado", "Connecticut", "Delaware", "District of Columbia",
    "Federated States of Micronesia", "Florida", "Georgia", "Guam", "Hawaii",
    "Idaho", "Illinois", "Indiana", "Iowa", "Kansas", "Kentucky", "Louisiana",
    "Maine", "Maryland", "Massachusetts", "Michigan", "Minnesota", "Mississippi",
    "Missouri", "Montana", "Nebraska", "Nevada", "New Hampshire", "New Jersey",
    "New Mexico", "New York", "North Carolina", "North Dakota",
    "Northern Mariana Islands", "Ohio", "Oklahoma", "Oregon", "Pennsylvania",
    "Puerto Rico", "Rhode Island", "South Carolina", "South Dakota", "Tennessee",
    "Texas", "Utah", "Vermont", "Virginia", "Washington", "West Virginia",
    "Wisconsin", "Wyoming", "U.S. Virgin Islands"
}

def setup_local_directories(directory_path: str):
    """Ensures that the specified local directory exists."""
    try:
        os.makedirs(directory_path, exist_ok=True)
        logging.info(f"Created/Ensured local working directory: {directory_path}")
    except OSError as e:
        logging.error(f"Error creating directory {directory_path}: {e}")
        raise

def download_files_via_file_util(
    files_to_download: list,
    gcs_bucket: str,
    gcs_prefix: str,
    local_target_dir: str
):
    """
    Downloads specified files from GCS to a local directory by directly calling
    methods from the imported file_util module.
    """
    logging.info("--- Starting GCS File Transfers using file_util module ---")
    for file_name in files_to_download:
        gcs_source_path = f"gs://{gcs_bucket}/{gcs_prefix}/{file_name}"
        local_destination_path = os.path.join(local_target_dir, file_name)
        
        try:
            file_util.file_copy(gcs_source_path, local_destination_path)
            logging.info(f"Copied '{gcs_source_path}' to '{local_destination_path}' using file_util module")
        except Exception as e:
            # Catch any exception that file_util.file_copy might raise
            logging.error(f"Error copying '{gcs_source_path}' to '{local_destination_path}': {e}")
            raise # Re-raise to be caught by the main function's try-except
    logging.info("--- GCS File Transfers Complete ---\n")

def process_investment_csv(input_csv_filepath: str, output_csv_filepath: str, states_set: set):
    """
    Processes the Investment CSV file, transforming data and handling numeric precision.
    """
    try:
        df = pd.read_csv(input_csv_filepath, header=None, skiprows=1, dtype=str)
    except FileNotFoundError:
        logging.fatal(f"Error: Input file not found at {input_csv_filepath}. Please ensure it was transferred successfully.")
        raise
    except pd.errors.EmptyDataError:
        logging.error(f"Error: Input file {input_csv_filepath} is empty.")
        raise
    except Exception as e:
        logging.error(f"Error reading CSV file {input_csv_filepath}: {e}")
        raise

    output_data = []
    current_state = None

    logging.info("--- Starting CSV Data Processing ---")
    for index, row in df.iterrows():
        original_col_a = str(row[0]).strip() if pd.notna(row[0]) else ""

        if original_col_a in states_set:
            current_state = original_col_a
            new_col_a = current_state
            new_col_b = "Total"
        else:
            new_col_a = current_state
            new_col_b = original_col_a

        if index == 0:
            new_col_a = "Place"

        output_row = [new_col_a, new_col_b]

        for col_idx in range(1, len(row)):
            val = row[col_idx]
            if pd.isna(val) or (isinstance(val, str) and val.lower() == "nan"):
                output_row.append(None)
            else:
                val_str = str(val).strip()
                
                if isinstance(val_str, str):
                    if ',' in val_str:
                        val_str = val_str.replace(",", "")
                    if '$' in val_str:
                        val_str = val_str.replace("$", "")

                val_to_append = val_str
                try:
                    decimal_val = Decimal(val_str)
                    if decimal_val == decimal_val.to_integral_value():
                        val_to_append = str(int(decimal_val))
                    else:
                        val_to_append = str(decimal_val)
                except InvalidOperation:
                    # If the string cannot be converted to a Decimal (e.g., it's plain text),
                    # assign its original string value to val_to_append.
                    val_to_append = val_str
                except Exception as e:
                    # This catches any other unexpected error during Decimal conversion.
                    # In case of an unexpected error, the value is appended as its original string.
                    val_to_append = val_str

                output_row.append(val_to_append)
                
        output_data.append(output_row)
    logging.info("--- CSV Data Processing Complete ---\n")

    output_column_names = ["State", "Category"] + [f"Original_Col_{i}" for i in range(1, df.shape[1])]
    output_df = pd.DataFrame(output_data, columns=output_column_names)
    output_df = output_df.applymap(lambda x: None if x is None or (isinstance(x, str) and x.lower() == "nan") else x)

    try:
        output_df.to_csv(output_csv_filepath, index=False, header=False, float_format='%.0f')
        logging.info(f"✅ Successfully processed '{input_csv_filepath}' and saved to '{output_csv_filepath}' (empty cells preserved, commas and dollar signs removed, numeric precision maintained).")
    except Exception as e:
        logging.error(f"Error saving processed CSV to {output_csv_filepath}: {e}")
        raise

def main(argv): # main function accepts argv as required by absl.app.run
    """Main function to orchestrate the data processing workflow."""
    del argv # Unused argument, required by absl.app.run
    try:
        setup_local_directories(LOCAL_WORKING_DIR)

        files_to_download = ["EstimatedOutcome.csv", "Poverty.csv", "Investment.csv"]
        download_files_via_file_util(
            files_to_download,
            GCS_BUCKET_NAME,
            GCS_INPUT_PREFIX,
            LOCAL_WORKING_DIR
        )

        input_filepath = os.path.join(LOCAL_WORKING_DIR, "Investment.csv")
        output_filepath = os.path.join(LOCAL_WORKING_DIR, "Investment1.csv")

        process_investment_csv(input_filepath, output_filepath, us_states)

        logging.info(f"All specified input files have been transferred to and processed from the '{LOCAL_WORKING_DIR}' directory.")
    except Exception as main_e:
        logging.fatal(f"An unrecoverable error occurred during execution: {main_e}", exc_info=True)
       

if __name__ == "__main__":
    
    app.run(main) # Use absl.app.run

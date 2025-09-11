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

import sys
import time
from absl import logging
from absl import flags
from absl import app
import os
import re
import pandas as pd
import shutil
import subprocess

FLAGS = flags.FLAGS
flags.DEFINE_string('output_folder', 'download_folder', 'download folder name')

# --- GCS Configuration ---
GCS_BUCKET_NAME = "unresolved_mcf"
GCS_INPUT_PREFIX = "fbi/city/latest/input_files"

# --- Path and Import Configuration ---
_MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(_MODULE_DIR, '..', '..', '..', '..', '..'))
sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, os.path.join(PROJECT_ROOT, 'data', 'util'))

try:
    from data.util import file_util
except ImportError as e:
    logging.fatal(f"Failed to import file_util: {e}.")

STATE_COLUMN = 0
CITY_COLUMN = 1
COLUMN_VALUES = ['State','City']

def copy_and_process_files_from_gcs(gcs_bucket, gcs_prefix, local_base_dir):
    """
    Copies .xlsx files from GCS, then processes them directly.
    """
    logging.info("--- Starting GCS File Transfers ---")
    
    local_input_dir = os.path.join(local_base_dir, 'input_files')
    os.makedirs(local_input_dir, exist_ok=True)

    gcs_source_path_wildcard = f"gs://{gcs_bucket}/{gcs_prefix}/*.xlsx"
    logging.info(f"Listing files from: {gcs_source_path_wildcard}")
    
    try:
        result = subprocess.run(['gsutil', 'ls', gcs_source_path_wildcard], capture_output=True, text=True, check=True)
        gcs_files = result.stdout.strip().split('\n')
        if not gcs_files or gcs_files == ['']:
            logging.fatal(f"No .xlsx files found at '{gcs_source_path_wildcard}'")
            return
    except subprocess.CalledProcessError as e:
        logging.fatal(f"Error listing files from GCS with gsutil: {e.stderr}")
        return
    except FileNotFoundError:
        logging.fatal("gsutil command not found. Please ensure the Google Cloud SDK is installed and in your PATH.")
        return

    logging.info(f"Found {len(gcs_files)} xlsx files to copy and process.")

    for gcs_source_path in gcs_files:
        file_name = os.path.basename(gcs_source_path)
        local_file_path = os.path.join(local_input_dir, file_name)
        
        try:
            file_util.file_copy(gcs_source_path, local_file_path)
            logging.info(f"Successfully copied '{gcs_source_path}' to '{local_file_path}'")
            
            # --- Directly process the copied file ---
            logging.info(f"Processing file: {local_file_path}")
            clean_headers(local_file_path)
            clean_state_column(local_file_path)
            
        except Exception as e:
            logging.fatal(f"Error copying or processing '{gcs_source_path}': {e}")
            
    logging.info("--- GCS File Transfers and Processing Complete ---\n")

def clean_headers(file_to_access):
  try:
    df = pd.read_excel(file_to_access,header=None)
    header_value = "Population"
    cleaned_headers = []
    for i in range(10):
      all_headers = df.iloc[i].tolist()
      if header_value in all_headers:
        logging.info(f"{header_value},{all_headers}")
        cleaned_headers = [header[:-1] if header and header[-1].isdigit() else header for header in all_headers]
        df.iloc[i] = cleaned_headers
    df.to_excel(file_to_access,index=False,header=False)
  except FileNotFoundError:
        logging.fatal(f"Error: File '{file_to_access}' not found.")
  except ValueError as e:
        logging.fatal(f"Error: {e}")
  except IndexError:
        logging.fatal("Error: headers not found or file is empty.")
  except Exception as e:
        logging.fatal(f"An unexpected error occurred: {e}")


def clean_state_column(file_path):
  try:
    df = pd.read_excel(file_path,header=None)
    state_row_index = df[df.iloc[:,STATE_COLUMN] == 'State'].index.values[0] if 'State' in df.iloc[:,STATE_COLUMN].values else None
    city_row_index = df[df.iloc[:,CITY_COLUMN] == 'City'].index.values[0] if 'City' in df.iloc[:,CITY_COLUMN].values else None
    if state_row_index is None:
      raise ValueError("No 'State' header found in the first column")
    if city_row_index is None:
       raise ValueError("No 'City' header found in the 2nd column")
    for column in COLUMN_VALUES:
      if column == 'State': 
        for i in range(state_row_index+1,len(df)):
            value =  str(df.iloc[i,0])
            if value and value[-1].isdigit():
              df.iloc[i,STATE_COLUMN] = value[:-1]
            if not pd.isna(df.iloc[i, STATE_COLUMN]):  # Check for NaN
                df.iloc[i, STATE_COLUMN] = str(df.iloc[i, STATE_COLUMN]) + " State"  
              
      elif column == 'City':
        for i in range(city_row_index+1,len(df)):
          value =  str(df.iloc[i,CITY_COLUMN])
          if value and value[-1].isdigit():
            cleaned_value = re.sub(r'[^a-zA-Z\s]+$', '', value)  # Remove non-alphanumeric from end
            df.iloc[i, CITY_COLUMN] = cleaned_value

    df.iloc[city_row_index,CITY_COLUMN] = 'City_Name' 
    df_new = df.copy()
    df_below_header = df_new[city_row_index:]
    df_below_header = df_below_header.dropna(subset=[1])
    df_below_header[1] = df_below_header[1].str.replace(',','',regex=False)
    df_new = pd.concat([df_new.iloc[:city_row_index+1], df_below_header.iloc[1:]], ignore_index=True)
    df_new.to_excel(file_path,index=False,header=False)    
  except FileNotFoundError:
        logging.fatal(f"Error: File '{file_path}' not found.")
  except ValueError as e:
        logging.fatal(f"Error: {e}")
  except IndexError:
        logging.fatal("Error: 'State' or 'City' header not found or file is empty.")
  except Exception as e:
        logging.fatal(f"An unexpected error occurred: {e}")

def main(unused_argv):
    _SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))
    DOWNLOAD_DIRECTORY = (os.path.join(_SCRIPT_PATH, FLAGS.output_folder))
    
    # Clear the local directory before starting
    if os.path.exists(DOWNLOAD_DIRECTORY):
        shutil.rmtree(DOWNLOAD_DIRECTORY)
    os.makedirs(DOWNLOAD_DIRECTORY)

    copy_and_process_files_from_gcs(GCS_BUCKET_NAME, GCS_INPUT_PREFIX, DOWNLOAD_DIRECTORY)


if __name__ == '__main__':
    app.run(main)

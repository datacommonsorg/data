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
import sys
import os
from absl import logging

# Set up module path to access the utility script
_MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
parent_of_parent_dir = os.path.join(_MODULE_DIR, '..', '..','..')
sys.path.append(parent_of_parent_dir)

from util.download_util_script import download_file


# URLs for the data
HEADCOUNT_URL = "https://www.flbog.edu/wp-content/uploads/2024/09/HEADCOUNT_ENROLLMENT_BY_STUDENT_TYPE_EXPORT_2024-09-13.xlsx"
DEGREES_URL = "https://www.flbog.edu/wp-content/uploads/2025/02/DEGREES_AWARDED_BY_STUDENT_DEMO_EXPORT_2025-02-19.xlsx"

# Directory names for downloaded and processed files
_SOURCE_FOLDER = 'source_files'
_INPUT_FOLDER = 'input_files'

def process_headcount_data(input_file, output_file):
    """
    Processes a student headcount Excel file.
    
    Args:
        input_file (str): The path to the input Excel file.
        output_file (str): The path to save the headcount summary CSV.
    """
    logging.info("Processing student headcount data...")
    try:
        df = pd.read_excel(input_file)
        
        # Add 'Place' column with value 'Florida'
        df.insert(0, 'Place', 'Florida')
        logging.info("Added 'Place' column to headcount data.")
        
        if 'Institution' in df.columns:
            df = df.drop(columns=['Institution'])
            logging.info("Dropped 'Institution' column.")

        if 'Fall Term' in df.columns:
            df['Fall Term'] = df['Fall Term'].astype(str).str.extract(r'(\d{4})')
            logging.info("Extracted year from 'Fall Term' for headcount data.")
        else:
            logging.error("'Fall Term' column not found.")
            raise ValueError("'Fall Term' column not found.")
        
        if 'FTIC Status' in df.columns:
            df['FTIC Status'] = df['FTIC Status'].fillna('NA')
            logging.info("Filled missing 'FTIC Status' values with 'NA'.")
        else:
            logging.warning("'FTIC Status' column not found. Skipping fillna.")
        
        grouping_cols = ['Place', 'Fall Term', 'Student Level', 'Student Type', 'FTIC Status']
        value_column = df.columns[-1]
        
        df_aggregated = df.groupby(grouping_cols, as_index=False)[value_column].sum()
        
        df_aggregated.rename(columns={value_column: 'Sum of Headcount (#)'}, inplace=True)
        
        df_aggregated.to_csv(output_file, index=False)
        logging.info("Successfully processed headcount data and saved to '%s'.", output_file)
    except Exception as e:
        logging.error("An error occurred during headcount processing: %s", e, exc_info=True)
        raise

def process_degrees_data(input_file, output_file):
    """
    Processes a degrees awarded Excel file.
    
    Args:
        input_file (str): The path to the input Excel file.
        output_file (str): The path to save the degrees awarded summary CSV.
    """
    logging.info("Processing degrees awarded data...")
    try:
        df = pd.read_excel(input_file)
        
        # Add 'Place' column with value 'Florida'
        df.insert(0, 'Place', 'Florida')
        logging.info("Added 'Place' column to degrees awarded data.")
        
        if 'Institution' in df.columns:
            df = df.drop(columns=['Institution'])
            logging.info("Dropped 'Institution' column.")

        if 'Year' in df.columns:
            df['Year'] = df['Year'].astype(str).str.extract(r'-(\d{4})').astype(int)
            logging.info("Extracted end year from 'Year' column for degrees data.")
        else:
            logging.error("'Year' column not found.")
            raise ValueError("'Year' column not found.")
        
        grouping_cols = ['Place', 'Degree Group', 'Degree Level', 'Race/Ethnicity', 'Gender', 'Year']
        value_column = df.columns[-1]
        
        df.rename(columns={value_column: 'Degrees Awarded'}, inplace=True)
        df_aggregated = df.groupby(grouping_cols, as_index=False)['Degrees Awarded'].sum()

        df_aggregated.to_csv(output_file, index=False)
        logging.info("Successfully processed degrees data and saved to '%s'.", output_file)
    except Exception as e:
        logging.error("An error occurred during degrees processing: %s", e, exc_info=True)
        raise

if __name__ == "__main__":
    logging.use_absl_handler()
    logging.set_verbosity(logging.INFO)

    # Create the source and input directories if they don't exist
    os.makedirs(_SOURCE_FOLDER, exist_ok=True)
    os.makedirs(_INPUT_FOLDER, exist_ok=True)
    logging.info("Ensured 'source_files' and 'input_files' directories exist.")

    headcount_filename = 'HEADCOUNT_ENROLLMENT_BY_STUDENT_TYPE_EXPORT_2024-09-13.xlsx'
    degrees_filename = 'DEGREES_AWARDED_BY_STUDENT_DEMO_EXPORT_2025-02-19.xlsx'

    # Download the headcount file to the source folder
    download_success_headcount = download_file(
        url=HEADCOUNT_URL,
        output_folder=_SOURCE_FOLDER,
        unzip=False,
        tries=3,
        delay=5,
        backoff=2
    )

    # Download the degrees awarded file to the source folder
    download_success_degrees = download_file(
        url=DEGREES_URL,
        output_folder=_SOURCE_FOLDER,
        unzip=False,
        tries=3,
        delay=5,
        backoff=2
    )

    # Check if downloads were successful
    if download_success_headcount and download_success_degrees:
        logging.info("All required files downloaded successfully. Proceeding with data processing.")
        
        headcount_input_path = os.path.join(_SOURCE_FOLDER, headcount_filename)
        degrees_input_path = os.path.join(_SOURCE_FOLDER, degrees_filename)
        
        headcount_output_path = os.path.join(_INPUT_FOLDER, 'enrollment_summary.csv')
        degrees_output_path = os.path.join(_INPUT_FOLDER, 'degrees_summary.csv')
        
        try:
            # Process each file separately
            process_headcount_data(headcount_input_path, headcount_output_path)
            process_degrees_data(degrees_input_path, degrees_output_path)
        except Exception as e:
            logging.fatal("Processing failed due to an error: %s", e)
            raise RuntimeError('Processing failed.')
            
    else:
        logging.fatal("Critical Error: One or more files failed to download. Terminating script.")
        raise RuntimeError('One or more files failed to download.')

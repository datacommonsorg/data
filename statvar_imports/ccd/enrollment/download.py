# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import sys
import pandas as pd

# Add the project root to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from util.download_util import download_file_from_url

_SV_INDEX_URL = "https://nces.ed.gov/programs/digest/d24/tables/xls/tabn203.65.xlsx"
_SV_INDEX_FILE_NAME = "tabn203.65.xlsx"
_SV_INDEX_CSV_FILE_NAME = "ccd_input.csv"

def download_data(output_dir: str):
    """Downloads the Enrollment in public elementary and secondary schools, by level, grade, and race/ethnicity data and processes it."""
    
    # Create the output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # Download the Excel file
    excel_file_path = os.path.join(output_dir, _SV_INDEX_FILE_NAME)
    download_file_from_url(_SV_INDEX_URL, output_file=excel_file_path)

    # Read the Excel file, skipping the first two rows
    df = pd.read_excel(excel_file_path, skiprows=2)

    df.drop(columns=["Unnamed: 2","Unnamed: 4","Prekindergarten through grade 8.2"], inplace=True)

    # Replace specified strings in the DataFrame
    df.replace(to_replace=r'Ungraded\\1\\', value='Ungraded_1', regex=True, inplace=True)
    df.replace(to_replace=r'Ungraded\\1,2\\', value='Ungraded1_2', regex=True, inplace=True)

    # Save the processed data to a CSV file
    csv_file_path = os.path.join(output_dir, _SV_INDEX_CSV_FILE_NAME)
    df.to_csv(csv_file_path, index=False)
    print(f"Downloaded and processed data saved to: {csv_file_path}")

if __name__ == "__main__":
    script_dir = os.path.dirname(__file__)
    download_output_dir = os.path.join(script_dir, "input_files")
    download_data(download_output_dir)        
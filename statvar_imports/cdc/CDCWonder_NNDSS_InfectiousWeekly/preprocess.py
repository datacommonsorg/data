# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os, sys
import pandas as pd
from absl import app, logging
from pathlib import Path
import datetime

script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(script_dir, '../../../util'))
from download_util_script import download_file
INPUT_DIR = os.path.join(script_dir, "input_files")
Path(INPUT_DIR).mkdir(parents=True, exist_ok=True)
INPUT_FILE = os.path.join(INPUT_DIR, "rows.csv")



def _start_date_of_year(year: int) -> datetime.date:
    """
    Return start date of the year using MMWR week rules.
    
    A year's first MMWR week is the first full calendar week (Sunday-Saturday)
    that contains at least four days of the new year. This means the start
    date of the first MMWR week can be in the previous calendar year.
    """
    jan_one = datetime.date(year, 1, 1)
    
    # Calculate the day difference to get to the first Sunday of the year.
    # The condition jan_one.isoweekday() > 3 accounts for the rule that
    # Jan 1 must be in the first week if it falls on a Mon, Tue, Wed, or Thu.
    diff = 7 * (jan_one.isoweekday() > 3) - jan_one.isoweekday()
    
    return jan_one + datetime.timedelta(days=diff)

def get_mmwr_week_end_date(year, week) -> datetime.date:
    """
    Return the start date of an MMWR week (starts at Sunday).
    The provided code originally had 'end_date' in the name but calculated
    the start date. To maintain the original logic, this returns the start date.
    """
    day_one = _start_date_of_year(year)
    diff = 7 * (week - 1)
    
    # The original function had a print statement, keeping it for consistency.
    # In a production environment, this should be removed.

    return day_one + datetime.timedelta(days=diff)

def preprocess_data(filepath: str):
    """
    Reads a CSV file, adds a new column 'observationDate' by calculating
    the MMWR week start date, and saves the changes back to the same file.
    The new column is placed immediately after the 'MMWR WEEK' column.
    
    Args:
        filepath (str): The path to the CSV file to read and update.
    """
    try:
        # Read the CSV file into a pandas DataFrame
        df = pd.read_csv(filepath)

        # Define the required column names.
        required_cols = ['Current MMWR Year', 'MMWR WEEK']

        # Check for the required columns. A KeyError will be raised if they don't exist.
        if not all(col in df.columns for col in required_cols):
            # This check is good practice, although the KeyError below would also catch it.
            raise KeyError(f"The file must contain the columns: {required_cols}.")

        # Use a vectorized operation with .apply() for better performance.
        # This applies the get_mmwr_week_end_date function to each row.
        df['observationDate'] = df.apply(
            lambda row: get_mmwr_week_end_date(row['Current MMWR Year'], row['MMWR WEEK']),
            axis=1
        )

        # Reorder the columns to place 'observationDate' after 'MMWR WEEK'
        cols = list(df.columns)
        mmwr_week_index = cols.index('MMWR WEEK')
        
        # Insert the new column at the desired position
        cols.insert(mmwr_week_index + 1, 'observationDate')
        
        # Reassign the DataFrame with the new column order
        df = df[cols]

        # Save the updated DataFrame back to the same CSV file
        df.to_csv(filepath, index=False)
        logging.info(f"Success: File '{filepath}' has been updated and saved.")
        
    except FileNotFoundError:
        logging.fatal(f"Error: The file '{filepath}' was not found.")
    except KeyError as e:
        logging.fatal(f"Error: Missing a required column. Details: {e}")
    except Exception as e:
        logging.fatal(f"An unexpected error occurred: {e}")

def main(argv):
    try:
        download_file(url="https://data.cdc.gov/api/views/x9gk-5huc/rows.csv?accessType=DOWNLOAD&api_foundry=true",
                  output_folder=INPUT_DIR,
                  unzip=False,
                  headers= None,
                  tries= 3,
                  delay= 5,
                  backoff= 2)
    except Exception as e:
        logging.fatal(f"Failed to download NNDSS weekly data file,{e}")
    preprocess_data(INPUT_FILE)

if __name__ == "__main__":
    app.run(main)

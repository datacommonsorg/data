# Copyright 2026 Google LLC
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

"""
This script extracts population data by sex, age, and year from the Statistics 
Denmark API using the BULK format. It performs dynamic sorting on demographic 
categories (ensuring 'Total' values appear first) and pivots the data to a 
wide-format time series before saving to CSV.
"""

import requests
import pandas as pd
import os
from io import StringIO
import re
from absl import logging

# Set logging verbosity
logging.set_verbosity(logging.INFO)

# --- CONFIGURATION ---
url = "https://api.statbank.dk/v1/data"
output_dir = "./input_files/"
table_id = "BEFOLK2"

def get_age_rank(age_str):
    """
    Assigns a numerical rank to age strings to facilitate correct sorting.
    
    'Total' or 'Age, total' is assigned the highest priority (-1), while 
    numeric age groups (e.g., '0-4', '5-9') are ranked by their starting integer.
    
    Args:
        age_str (str): The label for the age category.
        
    Returns:
        int: A ranking value used for sorting.
    """
    age_str = str(age_str).lower()
    if 'total' in age_str:
        return -1
    nums = re.findall(r'\d+', age_str)
    return int(nums[0]) if nums else 999

def main():
    """
    Main orchestration function to fetch, sort, pivot, and save the population data.
    
    The function handles:
    1. Directory initialization.
    2. API POST request for bulk data.
    3. Dynamic sorting of Sex (Total first).
    4. Regex-based sorting of Age groups and Years.
    5. Transformation from long to wide format (time series).
    """
    logging.info("--- Starting Statistics Denmark BEFOLK2 data extraction ---")

    # Ensure the target directory exists
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        logging.info(f"Created output directory: {output_dir}")

    # --- FETCH DATA ---
    # Define the variables for the API request
    payload = {
       "table": table_id,
       "format": "BULK",
       "lang": "en",
       "variables": [
          {"code": "KØN", "values": ["*"]},
          {"code": "ALDER", "values": ["*"]},
          {"code": "Tid", "values": ["*"]}
       ]
    }

    try:
        logging.info(f"Requesting bulk data for table: {table_id}")
        response = requests.post(url, json=payload)
        response.raise_for_status()

        if response.status_code == 200:
            # Process the semicolon-separated bulk response
            df = pd.read_csv(StringIO(response.text), sep=';')
            sex_col, age_col, time_col, val_col = df.columns
            logging.info(f"Data received. Processing {len(df)} rows.")

            # 1. DYNAMIC SEX SORTING (Total -> Men -> Women)
            # Identify 'Total' dynamically to ensure it stays at the top of the dataset.
            sex_order = sorted(df[sex_col].unique(), key=lambda x: 0 if 'total' in str(x).lower() else 1)
            df[sex_col] = pd.Categorical(df[sex_col], categories=sex_order, ordered=True)

            # 2. DYNAMIC AGE SORTING (Age, total -> 0-4 -> 5-9...)
            # Apply the ranking function to create a temporary sort key.
            df['age_sort'] = df[age_col].apply(get_age_rank)

            # 3. DYNAMIC YEAR SORTING
            # Extract digits from time labels to ensure chronological ordering.
            df[time_col] = df[time_col].apply(lambda x: int(re.search(r'\d+', str(x)).group()))

            # Sort the dataframe by the defined demographic hierarchy.
            df = df.sort_values([sex_col, 'age_sort', time_col])

            # 4. PIVOT
            # Transform the data so that years become individual columns. 
            # sort=False is used to preserve the manual demographic sorting performed above.
            df_pivot = df.pivot_table(
                index=[sex_col, age_col],
                columns=time_col,
                values=val_col,
                aggfunc='first',
                sort=False 
            ).reset_index()
            
            # Map column names to descriptive English titles
            df_pivot = df_pivot.rename(columns={'ALDER': 'Age', 'KØN': 'Sex'})

            # --- SAVE ---
            filename = "population_sex_age_time_input.csv"
            save_path = os.path.join(output_dir, filename)
            
            # Save using utf-8-sig to ensure compatibility with Excel and special characters.
            df_pivot.to_csv(save_path, index=False, encoding='utf-8-sig')
            logging.info(f"File saved successfully: {save_path}")

        else:
            logging.error(f"Request failed with status code: {response.status_code}")

    except requests.exceptions.RequestException as e:
        logging.fatal(f"Network error while fetching data: {e}")
    except Exception as e:
        logging.fatal(f"An unexpected error occurred during processing: {e}")

    logging.info("--- Script execution finished ---")

if __name__ == "__main__":
    main()

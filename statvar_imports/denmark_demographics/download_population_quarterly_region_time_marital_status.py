# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the 'License');
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#         https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an 'AS IS' BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
This script downloads quarterly population data from the Statistics Denmark API (Statbank).
It fetches demographic data including region, sex, age, and marital status, 
processes the JSON-STAT response into a flat structure, and saves it as a CSV.
"""

import requests
import pandas as pd
import itertools
import os
from absl import logging

# Set logging verbosity
logging.set_verbosity(logging.INFO)

# --- CONFIGURATION ---
# url: The endpoint for the Statistics Denmark API.
# output_dir: Local directory where the resulting CSV will be saved.
# table_id: The specific dataset ID (Population at the first day of the quarter).
url = "https://api.statbank.dk/v1/data"
output_dir = "./input_files/"
table_id = "FOLK1A"

def find_key_recursive(source_dict: dict, target_key: str):
    """
    Recursively searches for a key within a nested dictionary.
    
    Args:
        source_dict (dict): The dictionary to search.
        target_key (str): The key to find.
        
    Returns:
        The value associated with the target_key, or None if not found.
    """
    if target_key in source_dict: 
        return source_dict[target_key]
    for _, value in source_dict.items():
        if isinstance(value, dict):
            found = find_key_recursive(value, target_key)
            if found is not None: 
                return found
    return None

def main():
    """
    Orchestrates the data extraction, transformation, and loading (ETL) process.
    
    1. Prepares the local environment.
    2. Sends a POST request with a specific JSON payload to the Statbank API.
    3. Parses the complex JSON-STAT response into a flat list of dimensions.
    4. Uses a Cartesian product to align dimension labels with their corresponding values.
    5. Cleans and standardizes the resulting DataFrame.
    6. Saves the output to a CSV file.
    """
    logging.info("--- Starting Statistics Denmark data extraction ---")

    # Ensure output directory exists
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        logging.info(f"Created output directory: {output_dir}")

    # Define the API query payload
    # The '*' values indicate that we are requesting all available categories for that variable.
    payload = {
        "table": table_id,
        "format": "JSONSTAT",
        "lang": "en",
        "variables": [
            {"code": "OMRÅDE", "values": ["000"]},  # All of Denmark
            {"code": "KØN", "values": ["*"]},
            {"code": "ALDER", "values": ["*"]},
            {"code": "CIVILSTAND", "values": ["*"]},
            {"code": "Tid", "values": ["*"]}  
        ]
    }

    try:
        logging.info(f"Requesting data for table: {table_id}")
        response = requests.post(url, json=payload)
        response.raise_for_status()
        
        full_data = response.json()
        dims = find_key_recursive(full_data, 'dimension')
        vals = find_key_recursive(full_data, 'value')

        if dims and vals:
            logging.info("Successfully retrieved dimensions and values. Processing...")
            
            ids = find_key_recursive(full_data, 'id') or list(dims.keys())
            role = find_key_recursive(full_data, 'role') or {}
            metric_ids = role.get('metric', [])
            
            dim_list = []
            col_names = []

            # Extract labels for each dimension to build the Cartesian product
            for d_id in ids:
                if d_id in metric_ids or d_id.lower() in ['indhold', 'contents']: 
                    continue
                labels = dims[d_id]['category']['label']
                dim_list.append(list(labels.values()))
                col_names.append(d_id)

            # Build the DataFrame using the product of all dimension levels
            df = pd.DataFrame(list(itertools.product(*dim_list)), columns=col_names)
            df['Value'] = vals

            # Renaming and Data Cleanup for standardization
            df = df.rename(columns={
                'OMRÅDE': 'Region', 
                'ALDER': 'Age', 
                'CIVILSTAND': 'Marital_Status', 
                'Tid': 'Quarter', 
                'KØN': 'Sex'
            })
            
            # Clean up 'Total' labels to avoid confusion with specific categories
            df.loc[df['Sex'] == 'Total', 'Sex'] = 'Gender_Total'
            df.loc[df['Marital_Status'] == 'Total', 'Marital_Status'] = 'Marital_Total'

            filename = 'population_quarterly_region_time_marital_status_input.csv'
            save_path = os.path.join(output_dir, filename)
            
            df.to_csv(save_path, index=False)
            logging.info(f"Execution successful! Saved {len(df)} rows to {save_path}")
            
        else:
            logging.error("Failed to parse dimensions or values from the API response.")

    except requests.exceptions.RequestException as e:
        logging.fatal(f"Network error or bad HTTP response: {e}")
    except Exception as e:
        logging.fatal(f"An unexpected error occurred: {e}")

    logging.info("--- Script execution finished ---")

if __name__ == "__main__":
    main()

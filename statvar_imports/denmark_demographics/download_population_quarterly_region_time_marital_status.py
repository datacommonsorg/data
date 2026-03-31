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

import pandas as pd
import itertools
import os
from absl import logging
from statbank_utils import find_key_recursive, fetch_statbank_api

logging.set_verbosity(logging.INFO)

# --- CONFIGURATION ---
# url: API endpoint for Statistics Denmark.
# output_dir: Local path for the generated CSV.
# table_id: FOLK1A (Population at the first day of the quarter).
url = "https://api.statbank.dk/v1/data"
output_dir = "./input_files/"
table_id = "FOLK1A"

def main():
    """
    Orchestrates the data extraction, transformation, and loading (ETL) process.
    
    1. Fetches data via a POST request using fetch_statbank_api.
    2. Parses the nested JSON-STAT structure into dimensions and values.
    3. Reconstructs the dataset using a Cartesian product of labels.
    4. Cleanses and standardizes labels for downstream use.
    """
    logging.info("--- Starting Statistics Denmark data extraction ---")

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        logging.info(f"Created output directory: {output_dir}")
    
    # Define the API query payload
    # '*' is a wildcard requesting all sub-categories for the given variable.
    payload = {
        "table": table_id,
        "format": "JSONSTAT",
        "lang": "en",
        "variables": [
            {"code": "OMRÅDE", "values": ["000"]},
            {"code": "KØN", "values": ["*"]},
            {"code": "ALDER", "values": ["*"]},
            {"code": "CIVILSTAND", "values": ["*"]},
            {"code": "Tid", "values": ["*"]}  
        ]
    }

    try:
        response = fetch_statbank_api(url, table_id, payload)
        full_data = response.json()
        
        dims = find_key_recursive(full_data, 'dimension')
        vals = find_key_recursive(full_data, 'value')

        if dims and vals:
            logging.info("Successfully retrieved dimensions and values. Processing...")
            ids = find_key_recursive(full_data, 'id') or list(dims.keys())
            role = find_key_recursive(full_data, 'role') or {}
            metric_ids = role.get('metric', [])
            
            # Extract readable labels for each dimension to prepare for product calculation
            dim_list, col_names = [], []
            for d_id in ids:
                if d_id in metric_ids or d_id.lower() in ['indhold', 'contents']: 
                    continue
                labels = dims[d_id]['category']['label']
                dim_list.append(list(labels.values()))
                col_names.append(d_id)
            
            # JSON-STAT values are flat; we align them by creating a Cartesian product 
            # of all dimension labels.
            df = pd.DataFrame(list(itertools.product(*dim_list)), columns=col_names)
            df['Value'] = vals

            # Standardize Danish column names to English
            df = df.rename(columns={
                'OMRÅDE': 'Region', 'ALDER': 'Age', 
                'CIVILSTAND': 'Marital_Status', 'Tid': 'Quarter', 'KØN': 'Sex'
            })
            
            df.loc[df['Sex'] == 'Total', 'Sex'] = 'Gender_Total'
            df.loc[df['Marital_Status'] == 'Total', 'Marital_Status'] = 'Marital_Total'

            filename = 'population_quarterly_region_time_marital_status_input.csv'
            save_path = os.path.join(output_dir, filename)
            df.to_csv(save_path, index=False)
            logging.info(f"Execution successful! Saved {len(df)} rows to {save_path}")
    except Exception as e:
        logging.fatal(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()

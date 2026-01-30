import requests
import pandas as pd
from pyjstat import pyjstat
import os
import logging
import sys

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# --- DYNAMIC CONFIGURATION ---
# Sets path relative to where this script is saved
BASE_PATH = os.path.dirname(os.path.abspath(__file__))
POST_URL = "https://data.ssb.no/api/pxwebapi/v2/tables/07459/data?lang=en&outputFormat=json-stat2"
OUTPUT_FILE = os.path.join(BASE_PATH, "Norway_input.csv")

# Regions to exclude
EXCLUDE_REGIONS = [
    "Svalbard", 
    "Jan Mayen", 
    "Continental shelf", 
    "Unknown region", 
    "Uoppgitt bostedskommune"
]

QUERY = {
  "selection": [
    {"variableCode": "ContentsCode", "valueCodes": ["*"]},
    {"variableCode": "Tid", "valueCodes": ["*"]},
    {"variableCode": "Region", "valueCodes": ["*"], "codelist": "agg_KommFylker"},
    {"variableCode": "Alder", "valueCodes": ["*"], "codelist": "agg_TiAarigGruppering"},
    {"variableCode": "Kjonn", "valueCodes": ["*"]}
  ],
  "response": { "format": "json-stat2" }
}

def download_ssb_data():
    logging.info(f"Requesting data from SSB: {POST_URL}")
    
    try:
        # 1. Fetch data from SSB API
        response = requests.post(POST_URL, json=QUERY)
        response.raise_for_status()

        # 2. Parse JSON-stat2 into DataFrame
        dataset = pyjstat.Dataset.read(response.text)
        df = dataset.write('dataframe')

        # 3. Rename columns to match your Data Commons mapping
        df.columns = ['Region', 'Sex', 'Age', 'Contents', 'Year', 'Value']
        
        initial_count = len(df)

        # 4. Filter by Region (Exclude non-mainland/unknown regions)
        df = df[~df['Region'].isin(EXCLUDE_REGIONS)]
        df = df[~df['Region'].str.contains('shelf|Unknown|Svalbard', case=False, na=False)]
        
        final_count = len(df)
        
        # 6. Save result to the directory where the script lives
        df.to_csv(OUTPUT_FILE, index=False, encoding='utf-8')
        
        logging.info(f"Filtered out {initial_count - final_count} rows.")
        logging.info(f"SUCCESS: {final_count} rows saved to {OUTPUT_FILE}")

    except Exception as e:
        logging.error(f"An error occurred during processing: {e}")
        sys.exit(1)

if __name__ == "__main__":
    download_ssb_data()
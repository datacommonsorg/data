import requests
import pandas as pd
from pyjstat import pyjstat
import os
import logging
import sys

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# --- DYNAMIC CONFIGURATION ---
BASE_PATH = os.path.dirname(os.path.abspath(__file__))
POST_URL = "https://data.ssb.no/api/pxwebapi/v2/tables/07459/data?lang=en&outputFormat=json-stat2"
OUTPUT_FILE = os.path.join(BASE_PATH, "Norway_input.csv")

EXCLUDE_REGIONS = ["Svalbard", "Jan Mayen", "Continental shelf", "Unknown region", "Uoppgitt bostedskommune"]

def get_query(region_code, codelist=None):
    """Generates the body for the SSB API request."""
    # FUTURE PROOFING: Changed specific years to "*" to get all available years
    selection = [
        {"variableCode": "ContentsCode", "valueCodes": ["*"]},
        {"variableCode": "Tid", "valueCodes": ["*"]}, 
        {"variableCode": "Alder", "valueCodes": ["*"], "codelist": "agg_TiAarigGruppering"},
        {"variableCode": "Kjonn", "valueCodes": ["*"]},
        {"variableCode": "Region", "valueCodes": [region_code]}
    ]
    if codelist:
        selection[-1]["codelist"] = codelist
    
    return {"selection": selection, "response": {"format": "json-stat2"}}

def fetch_norway_data():
    logging.info("Starting combined data fetch (National + Regional)...")
    
    try:
        # 1. Fetch National Data (Code 0)
        logging.info("Fetching National data...")
        res_nat = requests.post(POST_URL, json=get_query("0"))
        res_nat.raise_for_status()
        df_nat = pyjstat.Dataset.read(res_nat.text).write('dataframe')

        # 2. Fetch Regional Data (Codelist agg_KommFylker)
        logging.info("Fetching Regional data...")
        res_reg = requests.post(POST_URL, json=get_query("*", "agg_KommFylker"))
        res_reg.raise_for_status()
        df_reg = pyjstat.Dataset.read(res_reg.text).write('dataframe')

        # 3. Combine DataFrames
        df = pd.concat([df_nat, df_reg], ignore_index=True)

        # 4. Standardize Columns safely
        # SSB lowercase names are: region, contents, tid, alder, kjonn, value
        rename_map = {
            'region': 'Region',
            'contents': 'Contents',
            'tid': 'Year',
            'alder': 'Age',
            'kjonn': 'Sex',
            'value': 'Value'
        }
        df.rename(columns=rename_map, inplace=True)
        
        # 5. Filter Regions
        df = df[~df['Region'].isin(EXCLUDE_REGIONS)]
        df = df[~df['Region'].str.contains('shelf|Unknown|Svalbard', case=False, na=False)]

        # 6. Year Cleaning and Future Filtering
        # This keeps the script working for 2026, 2027, etc.
        if 'Year' in df.columns:
            df['Year'] = df['Year'].astype(str).str.extract('(\d{4})')[0].astype(int)
            # Filter to keep data from 2023 onwards (includes future years)
            df = df[df['Year'] >= 2023]
        
        # 7. Save result
        df.to_csv(OUTPUT_FILE, index=False, encoding='utf-8')
        
        logging.info(f"SUCCESS: Combined data ({len(df)} rows) saved to {OUTPUT_FILE}")

    except Exception as e:
        logging.error(f"An error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    fetch_norway_data()
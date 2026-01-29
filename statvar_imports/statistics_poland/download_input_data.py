import pandas as pd
import os
import logging
import sys
import subprocess
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# --- CONFIGURATION ---
BASE_PATH = os.path.dirname(os.path.abspath(__file__))
# Local temporary path for the downloaded Excel
LOCAL_EXCEL = os.path.join(BASE_PATH, "poland_raw.xlsx") 
# Source GCS path
GCS_EXCEL_PATH = "gs://datcom-prod-imports/statvar_imports/statistics_poland/poland_data_sample/poland_raw.xlsx"
# Final CSV in the root directory for the processor
OUTPUT_FILE = os.path.join(BASE_PATH, "StatisticsPoland_input.csv")

TARGET_AGES = [
    "0-2", "3-6", "7-12", "13-15", "16-19", "20-24", 
    "25-34", "35-44", "45-54", "55-64", "65 i więcej"
]

def download_from_gcs():
    """Downloads the raw excel file from GCS using gsutil."""
    try:
        logging.info(f"Downloading source from {GCS_EXCEL_PATH}...")
        subprocess.check_call(['gsutil', 'cp', GCS_EXCEL_PATH, LOCAL_EXCEL])
    except Exception as e:
        logging.error(f"Failed to download from GCS: {e}")
        # Note: If running locally and file exists, you might want to skip exit
        if not os.path.exists(LOCAL_EXCEL):
            sys.exit(1)

def process_poland_pivot():
    # 1. Fetch data from cloud
    download_from_gcs()

    logging.info(f"Processing data from local copy: {LOCAL_EXCEL}")

    try:
        # 2. Load the 'DANE' sheet
        df = pd.read_excel(LOCAL_EXCEL, sheet_name='DANE')
        df.columns = ['Code', 'Name', 'Age', 'Sex', 'Location', 'Year', 'Value', 'Unit', 'Attr']

        # 3. Filtering and Year Logic
        df = df[df['Age'].isin(TARGET_AGES)]
        current_year = datetime.now().year
        available_years = sorted([y for y in df['Year'].unique() if y <= current_year])
        df = df[df['Year'].isin(available_years)]

        # 4. Translation Logic
        translations = {
            'mężczyźni': 'males',
            'kobiety': 'females',
            'ogółem': 'total',
            'w miastach': 'in urban areas',
            'na wsi': 'in rural areas',
            'POLSKA': 'POLAND',
            '65 i więcej': '65 and more'
        }
        for col in ['Sex', 'Location', 'Name', 'Age']:
            df[col] = df[col].replace(translations)

        # 5. Create Pivot Table
        pivot_df = df.pivot_table(
            index=['Code', 'Name'], 
            columns=['Age', 'Sex', 'Location', 'Year'], 
            values='Value'
        )

        # 6. Format Geographic Codes (7-digit padding)
        pivot_df.index = pivot_df.index.set_levels(
            pivot_df.index.levels[0].astype(str).str.zfill(7), level=0
        )

        # 7. Save result to root for the Cloud executor
        pivot_df.to_csv(OUTPUT_FILE, encoding='utf-8')
        
        logging.info(f"SUCCESS: {OUTPUT_FILE} created in root directory.")
        # Cleanup temporary Excel to keep the environment clean
        if os.path.exists(LOCAL_EXCEL):
            os.remove(LOCAL_EXCEL)

    except Exception as e:
        logging.error(f"Processing Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    process_poland_pivot()
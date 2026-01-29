import pandas as pd
import os
import logging
import sys
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(levelname)s: %(message)s'
)

# --- FLATTENED PATH LOGIC ---
# Get the directory where THIS script is actually saved
BASE_PATH = os.path.dirname(os.path.abspath(__file__))

# Input remains in the sample subfolder
INPUT_FILE = os.path.join(BASE_PATH, "poland_data_sample/poland_raw.xlsx")

# Output is now saved directly in BASE_PATH (the root of the import folder)
# This ensures stat_var_processor.py can find it in the Cloud environment
OUTPUT_FILE = os.path.join(BASE_PATH, "StatisticsPoland_input.csv")

TARGET_AGES = [
    "0-2", "3-6", "7-12", "13-15", "16-19", "20-24", 
    "25-34", "35-44", "45-54", "55-64", "65 i więcej"
]

def process_poland_pivot():
    # Verify input exists
    if not os.path.exists(INPUT_FILE):
        logging.error(f"CRITICAL ERROR: {INPUT_FILE} not found.")
        # Tells the automation executor to STOP here
        sys.exit(1)

    logging.info(f"Processing data from: {INPUT_FILE}")

    try:
        # 1. Load the 'DANE' sheet
        df = pd.read_excel(INPUT_FILE, sheet_name='DANE')
        df.columns = ['Code', 'Name', 'Age', 'Sex', 'Location', 'Year', 'Value', 'Unit', 'Attr']

        # 2. Generic Filtering
        df = df[df['Age'].isin(TARGET_AGES)]
        
        current_year = datetime.now().year
        available_years = sorted([y for y in df['Year'].unique() if y <= current_year])
        df = df[df['Year'].isin(available_years)]

        # 3. Translation Logic
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

        # 4. Create the Pivot Table
        pivot_df = df.pivot_table(
            index=['Code', 'Name'], 
            columns=['Age', 'Sex', 'Location', 'Year'], 
            values='Value'
        )

        # 5. Format Geographic Codes
        pivot_df.index = pivot_df.index.set_levels(
            pivot_df.index.levels[0].astype(str).str.zfill(7), level=0
        )

        # 6. Save result directly to BASE_PATH
        # encoding='utf-8' is crucial for Polish characters
        pivot_df.to_csv(OUTPUT_FILE, encoding='utf-8')
        
        logging.info(f"SUCCESS: {OUTPUT_FILE} created in the root directory.")
        logging.info(f"Years Included: {available_years}")

    except Exception as e:
        logging.error(f"Processing Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    process_poland_pivot()
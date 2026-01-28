import pandas as pd
import os
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)

# Configuration
INPUT_FILE = "statvar_imports/statistics_poland/poland_data_sample/poland_raw.xlsx"
OUTPUT_DIR = "statvar_imports/statistics_poland/poland_input"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "StatisticsPoland_input.csv")

# Target functional age groups
TARGET_AGES = [
    "0-2", "3-6", "7-12", "13-15", "16-19", "20-24", 
    "25-34", "35-44", "45-54", "55-64", "65 i więcej"
]

def process_poland_pivot():
    if not os.path.exists(INPUT_FILE):
        logging.error(f"{INPUT_FILE} not found.")
        return

    logging.info(f"Starting generic processing. Saving to: {OUTPUT_FILE}")

    try:
        # 1. Load the 'DANE' sheet
        df = pd.read_excel(INPUT_FILE, sheet_name='DANE')
        df.columns = ['Code', 'Name', 'Age', 'Sex', 'Location', 'Year', 'Value', 'Unit', 'Attr']

        # 2. Generic Filtering
        df = df[df['Age'].isin(TARGET_AGES)]
        
        # DYNAMIC YEAR LOGIC
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
        
        # Refactored repetitive replace calls into a loop
        for col in ['Sex', 'Location', 'Name', 'Age']:
            df[col] = df[col].replace(translations)

        # 4. Create the Pivot Table
        pivot_df = df.pivot_table(
            index=['Code', 'Name'], 
            columns=['Age', 'Sex', 'Location', 'Year'], 
            values='Value'
        )

        # 5. Format Geographic Codes (ensuring 7-digit padding)
        pivot_df.index = pivot_df.index.set_levels(
            pivot_df.index.levels[0].astype(str).str.zfill(7), level=0
        )

        # 6. Save result
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        pivot_df.to_csv(OUTPUT_FILE, encoding='utf-8-sig')
        
        logging.info(f"SUCCESS: {OUTPUT_FILE} has been updated.")
        logging.info(f"Years Included: {available_years}")
        logging.info(f"Total Geographies Processed: {pivot_df.shape[0]}")

    except Exception as e:
        logging.error(f"Processing Error: {e}")

if __name__ == "__main__":
    process_poland_pivot()

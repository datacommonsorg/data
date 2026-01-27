import pandas as pd
import os
from datetime import datetime

# Configuration
INPUT_FILE = "statvar_imports/statistics_poland/poland_data_sample/poland_raw.xlsx"
# Final path for Data Commons import
OUTPUT_DIR = "statvar_imports/statistics_poland/poland_input"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "StatisticsPoland_input.csv")

# Target functional age groups
TARGET_AGES = [
    "0-2", "3-6", "7-12", "13-15", "16-19", "20-24", 
    "25-34", "35-44", "45-54", "55-64", "65 i więcej"
]

def process_poland_pivot():
    if not os.path.exists(INPUT_FILE):
        print(f"ERROR: {INPUT_FILE} not found.")
        return

    print(f"Starting generic processing. Saving to: {OUTPUT_FILE}")

    try:
        # 1. Load the 'DANE' sheet
        df = pd.read_excel(INPUT_FILE, sheet_name='DANE')
        df.columns = ['Code', 'Name', 'Age', 'Sex', 'Location', 'Year', 'Value', 'Unit', 'Attr']

        # 2. Generic Filtering
        # Keep only specified age groups
        df = df[df['Age'].isin(TARGET_AGES)]
        
        # DYNAMIC YEAR LOGIC:
        # Detects all years in the file and filters out any accidental future projections
        current_year = datetime.now().year
        available_years = sorted([y for y in df['Year'].unique() if y <= current_year])
        df = df[df['Year'].isin(available_years)]

        # 3. Translation Dictionary
        translations = {
            'mężczyźni': 'males',
            'kobiety': 'females',
            'ogółem': 'total',
            'w miastach': 'in urban areas',
            'na wsi': 'in rural areas',
            'POLSKA': 'POLAND',
            '65 i więcej': '65 and more'
        }
        
        df['Sex'] = df['Sex'].replace(translations)
        df['Location'] = df['Location'].replace(translations)
        df['Name'] = df['Name'].replace(translations)
        df['Age'] = df['Age'].replace(translations)

        # 4. Create the Pivot Table
        # Stacks categories into a multi-level header: Age > Sex > Location > Year
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
        # utf-8-sig ensures Polish special characters in 'Name' stay readable
        pivot_df.to_csv(OUTPUT_FILE, encoding='utf-8-sig')
        
        print(f"SUCCESS: {OUTPUT_FILE} has been updated.")
        print(f"Years Included: {available_years}")
        print(f"Total Geographies Processed: {pivot_df.shape[0]}")

    except Exception as e:
        print(f"Processing Error: {e}")

if __name__ == "__main__":
    process_poland_pivot()
import requests
import zipfile
import pandas as pd
import os
import io
import tempfile
from pathlib import Path
import time
import datetime
import logging
import sys

# --- 1. Constants (Configuration Only) ---
# It is okay to keep static configuration at the top level.
BASE_URL = "https://civilrightsdata.ed.gov/assets/ocr/docs/"
TARGET_CSV_NAME = "Internet Access and Devices"
OUTPUT_DIR = Path("input_files")

# --- 2. Function Definitions ---

def generate_year_strings(start_year=2020):
    """
    Generates academic year strings (e.g., '2020-21') from the start_year
    up to the current academic cycle, starting with the newest year.
    """
    current_date = datetime.datetime.now()
    current_year = current_date.year
    current_month = current_date.month
    
    if current_month >= 8:
        max_start_year = current_year
    else:
        max_start_year = current_year - 1

    year_strings = []
    for y in range(start_year, max_start_year + 1):
        end_year_two_digits = str(y + 1)[2:]
        year_string = f"{y}-{end_year_two_digits}"
        year_strings.append(year_string)
    
    return list(reversed(year_strings))

def get_full_year(year_string):
    """Derives the full year (e.g., 2024 from '2023-24') for the YEAR column."""
    try:
        two_digit_year = year_string.split('-')[1]
        return int(f"20{two_digit_year}")
    except IndexError:
        logging.error(f"Could not parse year from string '{year_string}'. Using 0.")
        return 0

def process_crdc_data(year_string):
    """Downloads, extracts, finds, processes, and saves the target CSV."""
    zip_filename = f"{year_string}-crdc-data.zip"
    full_url = f"{BASE_URL}{zip_filename}"
    target_year = get_full_year(year_string)

    logging.info(f"\n--- Starting processing for academic year {year_string} (Column YEAR={target_year}) ---")

    try:
        response = requests.get(full_url, stream=True)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logging.error(f"Error downloading {zip_filename}: {e}")
        return

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        try:
            with zipfile.ZipFile(io.BytesIO(response.content)) as zf:
                zf.extractall(temp_path)
        except zipfile.BadZipFile:
            logging.error(f"The downloaded file for {year_string} is not a valid ZIP file.")
            return

        found_csv_path = None
        for file_path in temp_path.rglob('*.csv'):
            if TARGET_CSV_NAME.lower() in file_path.stem.lower():
                found_csv_path = file_path
                break

        if not found_csv_path:
            logging.error(f"Could not find a CSV matching '{TARGET_CSV_NAME}' for year {year_string}.")
            return

        try:
            df = pd.read_csv(found_csv_path, encoding='latin-1', low_memory=False)
            df['YEAR'] = target_year
            output_filename = OUTPUT_DIR / f"{TARGET_CSV_NAME.replace(' ', '_')}_{target_year}.csv"
            df.to_csv(output_filename, index=False, encoding='utf-8')
            logging.info(f"Successfully saved data to: {output_filename.resolve()}")
        except Exception as e:
            logging.error(f"An error occurred during CSV processing for {year_string}: {e}")

# --- 3. Main Execution Block ---

def main():
    # A. Configure Logging (Moved inside main)
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler()]
    )

    # B. Directory Creation Logic (Moved inside main)
    try:
        OUTPUT_DIR.mkdir(exist_ok=True)
        logging.info(f"Output directory verified: {OUTPUT_DIR.resolve()}")
    except Exception as e:
        logging.fatal(f"FATAL: Could not create output directory {OUTPUT_DIR.resolve()}. Error: {e}")
        sys.exit(1)

    # C. Dynamic Data Generation (Moved inside main)
    year_strings = generate_year_strings()

    # D. Processing Loop
    for year in year_strings:
        process_crdc_data(year)
        # Small delay to be polite to the server
        time.sleep(2)

    logging.info("\nAll tasks complete.")

if __name__ == "__main__":
    main()
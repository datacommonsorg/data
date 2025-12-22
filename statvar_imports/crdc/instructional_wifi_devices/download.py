import requests
import zipfile
import pandas as pd
import os
import io
import tempfile
from pathlib import Path
import time
import datetime
import logging # Import the logging module
import sys
# --- NEW: Simplified Logging Configuration ---
# Configure logging to output ONLY to the console (StreamHandler)
# and set the log format.
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)


OUTPUT_DIR = Path("input_files")

# Create the output directory if it doesn't exist
try:
    OUTPUT_DIR.mkdir(exist_ok=True)
    logging.info(f"Output directory created/verified: {OUTPUT_DIR.resolve()}")
except Exception as e:
    logging.fatal(f"FATAL: Could not create output directory {OUTPUT_DIR.resolve()}. Exiting. Error: {e}")
    sys.exit(1)


# --- Configuration ---
BASE_URL = "https://civilrightsdata.ed.gov/assets/ocr/docs/"
# The file names we are looking for inside the zip files
TARGET_CSV_NAME = "Internet Access and Devices"

# --- Dynamic Year String Generation ---
def generate_year_strings(start_year=2020):
    """
    Generates academic year strings (e.g., '2020-21') from the start_year
    up to the current academic cycle, starting with the newest year.
    """
    current_date = datetime.datetime.now()
    current_year = current_date.year
    current_month = current_date.month
    
    # Determine the start year of the most recent academic cycle.
    if current_month >= 8:
        max_start_year = current_year
    else:
        max_start_year = current_year - 1

    year_strings = []
    # Loop from the earliest year to the latest possible start year
    for y in range(start_year, max_start_year + 1):
        end_year_two_digits = str(y + 1)[2:]
        year_string = f"{y}-{end_year_two_digits}"
        year_strings.append(year_string)
    
    # Reverse the list so the script attempts to download the newest data first.
    return list(reversed(year_strings))

YEAR_STRINGS = generate_year_strings()

def get_full_year(year_string):
    """
    Derives the full year (e.g., 2024 from '2023-24') for the YEAR column.
    """
    try:
        # Extract the second two-digit part ('24', '22', or '21')
        two_digit_year = year_string.split('-')[1]
        return int(f"20{two_digit_year}")
    except IndexError:
        logging.error(f"Could not parse year from string '{year_string}'. Using 0.")
        return 0

def process_crdc_data(year_string):
    """
    Downloads, extracts, finds, processes, and saves the target CSV for a given year.
    """
    zip_filename = f"{year_string}-crdc-data.zip"
    full_url = f"{BASE_URL}{zip_filename}"
    target_year = get_full_year(year_string)

    logging.info(f"\n--- Starting processing for academic year {year_string} (Column YEAR={target_year}) ---")
    logging.info(f"Attempting to download from: {full_url}")

    # 1. Download the ZIP file
    try:
        response = requests.get(full_url, stream=True)
        response.raise_for_status() # Raise an exception for bad status codes
        logging.info(f"Successfully downloaded ZIP file content for {year_string}.")
    except requests.exceptions.RequestException as e:
        # 404 errors or other connection issues are handled here
        logging.error(f"Error downloading {zip_filename}. File might not be released yet or connection failed: {e}")
        return

    # Use a temporary directory for extraction
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        logging.info(f"Extracting contents to temporary directory: {temp_dir}")

        # Unzip the file from memory
        try:
            # We use io.BytesIO to treat the response content as a file in memory
            with zipfile.ZipFile(io.BytesIO(response.content)) as zf:
                # Extract all contents into the temporary directory
                zf.extractall(temp_path)
            logging.info("Extraction complete.")
        except zipfile.BadZipFile:
            logging.error(f"The downloaded file for {year_string} is not a valid ZIP file.")
            return

        # 2. Recursively search for the target CSV file
        found_csv_path = None
        # Use Path.rglob() for recursive search
        for file_path in temp_path.rglob('*.csv'):
            # Check if the file name contains the target phrase (case-insensitive)
            if TARGET_CSV_NAME.lower() in file_path.stem.lower():
                found_csv_path = file_path
                break

        if not found_csv_path:
            logging.error(f"Could not find a CSV file matching '{TARGET_CSV_NAME}' for year {year_string}.")
            return

        logging.info(f"Found target CSV: {found_csv_path.name} in subdirectory {found_csv_path.parent.name}")

        # 3. Load, process, and save the CSV
        try:
            # Use 'latin-1' encoding as CRDC files often contain special characters
            df = pd.read_csv(found_csv_path, encoding='latin-1', low_memory=False)
            logging.info(f"Loaded DataFrame with {len(df)} rows and {len(df.columns)} columns.")

            # 4. Append the YEAR column
            df['YEAR'] = target_year

            # 5. Save the modified DataFrame to the output folder
            output_filename = OUTPUT_DIR / f"{TARGET_CSV_NAME.replace(' ', '_')}_{target_year}.csv"
            df.to_csv(output_filename, index=False, encoding='utf-8')

            logging.info(f"Successfully processed and saved data to: {output_filename.resolve()}")

        except Exception as e:
            # Catch exceptions during file operations or Pandas processing
            logging.error(f"An error occurred during CSV processing for {year_string}: {e}")

# --- Main execution loop ---
for year in YEAR_STRINGS:
    process_crdc_data(year)
    # Be polite to the server by adding a small delay between large downloads
    time.sleep(2)
logging.info("\nAll tasks complete.")
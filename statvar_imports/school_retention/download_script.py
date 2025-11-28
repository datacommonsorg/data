# Copyright 2025 Google LLC
# Licensed under the Apache License, Version 2.0

"""
CRDC Data Downloader & Processor (Merged)
-----------------------------------------
1. Downloads CRDC data (2010-Present) with parallel processing.
2. Extracts only specific files based on keywords.
3. Process Data:
   - Adds 'YEAR' and 'NCESID' columns to the START.
   - Converts 'Yes' -> 1 and 'No' -> 0 (Excluding 'JJ').
   - Converts numeric strings to actual numbers.
"""

import os
import re
import shutil
import zipfile
import requests
import pandas as pd
import tempfile
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from absl import logging, app
from pathlib import Path
from retry import retry

# ==========================================
# Configuration
# ==========================================
MAX_WORKERS = 5
SCRIPT_DIR = Path(os.path.dirname(os.path.abspath(__file__)))
SAVE_FOLDER = os.path.join(SCRIPT_DIR, "input_files")

# Regex Patterns to identify required files
KEYWORDS = [
    r'.*09-2 Retention.*',
    r'Retention of Students.*grade (0[1-9]|1[0-2])\.xlsx$',
    r'Retention of Students.*kindergarten\.xlsx$',
    r'Retention\.csv$',
    r'Retention\.xlsx$',
    r'School Data\.csv$'
]

# Columns to SKIP during Yes/No conversion
EXCLUDE_COLS = ['JJ', 'LEA_STATE', 'LEA_STATE_NAME', 'LEA_NAME', 'SCH_NAME']

# Replacement Map
REPLACEMENT_MAP = {
    "Yes": 1, "No": 0,
    "yes": 1, "no": 0,
    "YES": 1, "NO": 0
}

# ==========================================
# Helper Functions
# ==========================================

def matches_keywords(filename: str) -> bool:
    return any(re.search(pattern, filename, re.IGNORECASE) for pattern in KEYWORDS)

def get_urls_for_year(start_year, end_year):
    short_end = str(end_year)[-2:]
    return [
        f"https://civilrightsdata.ed.gov/assets/ocr/docs/{start_year}-{short_end}-crdc-data.zip",
        f"https://civilrightsdata.ed.gov/assets/ocr/docs/CRDC{start_year}_{short_end}_CSV.zip",
        f"https://civilrightsdata.ed.gov/assets/ocr/docs/CRDC{start_year}_{short_end}_data.zip",
        f"https://civilrightsdata.ed.gov/assets/ocr/docs/{start_year}-{short_end}-crdc-csv.zip"
    ]

def transform_crdc_data(df: pd.DataFrame, year: int, filename: str) -> pd.DataFrame:
    """
    Applies common transformations: Adds YEAR, generates NCESID, 
    cleans Yes/No values, and reorders columns.
    """
    # --- 1. ADD YEAR & NCESID ---
    df["YEAR"] = year
    df.columns = [x.upper() for x in df.columns]

    if "LEAID" in df.columns and "SCHID" in df.columns:
        df["NCESID"] = (
            df["LEAID"].astype(str).str.zfill(7) +
            df["SCHID"].astype(str).str.zfill(5))
    elif "COMBOKEY" in df.columns:
        df["NCESID"] = df["COMBOKEY"].astype(str).str.replace("'", "")
    else:
        logging.warning(f"Missing LEAID/SCHID in {filename}")

    # --- 2. CLEAN YES/NO (Excluding JJ) ---
    exclude_upper = [c.upper() for c in EXCLUDE_COLS]
    target_cols = [col for col in df.columns if col not in exclude_upper]
    
    # Map Yes/No to 1/0
    df[target_cols] = df[target_cols].replace(REPLACEMENT_MAP)

    # Convert numeric columns efficiently (Vectorized)
    # Using errors='coerce' turns bad data into NaN instead of crashing or ignoring
    df[target_cols] = df[target_cols].apply(pd.to_numeric, errors='coerce')

    # --- 3. REORDER COLUMNS ---
    priority_cols = ['YEAR', 'NCESID']
    existing_priority = [c for c in priority_cols if c in df.columns]
    other_cols = [c for c in df.columns if c not in existing_priority]
    
    return df[existing_priority + other_cols]

def process_dataframe(file_path: str, year: int):
    """
    Loads, Cleans (Yes/No), Adds Columns, and Saves the file.
    Handles multi-sheet Excel files by processing only the first sheet.
    """
    try:
        filename = os.path.basename(file_path)

        # --- CSV HANDLING ---
        if file_path.lower().endswith(".csv"):
            try:
                # Try reading with Latin1 first
                df = pd.read_csv(file_path, dtype=str, low_memory=False, encoding='latin1')
            except UnicodeDecodeError:
                # Fallback to default (usually UTF-8) if Latin1 fails
                df = pd.read_csv(file_path, dtype=str, low_memory=False)

            df = transform_crdc_data(df, year, filename)
            df.to_csv(file_path, index=False)

        # --- XLSX HANDLING ---
        elif file_path.lower().endswith(".xlsx"):
            # Read ALL sheets into a dictionary
            all_sheets = pd.read_excel(file_path,
                                       dtype=str,
                                       engine='openpyxl',
                                       sheet_name=None)

            # Get the name of the first sheet (the "Data" sheet)
            data_sheet_name = list(all_sheets.keys())[0]
            df = all_sheets[data_sheet_name]

            df = transform_crdc_data(df, year, filename)

            # Save all sheets back
            with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                for sheet_name, original_sheet_df in all_sheets.items():
                    if sheet_name == data_sheet_name:
                        # Write the *processed* data frame
                        df.to_excel(writer, sheet_name=sheet_name, index=False)
                    else:
                        # Write the *original, untouched* definitions/other frames
                        original_sheet_df.to_excel(writer, sheet_name=sheet_name, index=False)

        else:
            return

        logging.info(f"Processed & Cleaned: {filename}")

    except Exception as e:
        logging.error(f"Failed to process DataFrame {file_path}: {e}")
        raise RuntimeError(f"Failed to process DataFrame {file_path}") from e

@retry(tries=2, delay=2)
def try_download_url(url, temp_file):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    try:
        with requests.get(url, headers=headers, stream=True, timeout=120) as r:
            if r.status_code == 200:
                # Security Check: Ensure we didn't just download an HTML error page
                content_type = r.headers.get('Content-Type', '').lower()
                if 'html' in content_type:
                    logging.warning(f"URL {url} returned HTML instead of ZIP. Skipping.")
                    return False
                
                shutil.copyfileobj(r.raw, temp_file)
                return True
            else:
                logging.warning(f"URL {url} returned status {r.status_code}")
    except Exception as e:
        logging.warning(f"Failed to download {url}: {e}")
    return False

# ==========================================
# Main Logic
# ==========================================

def process_year_data(start_year: int, end_year: int):
    possible_urls = get_urls_for_year(start_year, end_year)
    zip_label = f"{start_year}-{str(end_year)[-2:]}"
    
    logging.info(f"Processing {zip_label}...")

    with tempfile.NamedTemporaryFile(delete=True) as tmp_zip:
        downloaded = False
        
        for url in possible_urls:
            tmp_zip.seek(0)
            tmp_zip.truncate()
            if try_download_url(url, tmp_zip):
                downloaded = True
                break
        
        if not downloaded:
            logging.warning(f"Skipped {zip_label}: All URL variations failed.")
            return

        tmp_zip.flush()
        
        try:
            with zipfile.ZipFile(tmp_zip.name) as z:
                matched_files = [f for f in z.namelist() if matches_keywords(f)]
                
                if not matched_files:
                    logging.info(f"Downloaded {zip_label}, but no files matched keywords.")
                    return

                for file_name in matched_files:
                    output_filename = f"{end_year}_{os.path.basename(file_name)}"
                    output_path = os.path.join(SAVE_FOLDER, output_filename)

                    with z.open(file_name) as source, open(output_path, "wb") as target:
                        shutil.copyfileobj(source, target)

                    process_dataframe(output_path, end_year)

        except zipfile.BadZipFile:
            logging.error(f"File downloaded for {zip_label} was not a valid zip.")
            raise RuntimeError(f"File {zip_label} was not a valid zip") from None
        except Exception as e:
            logging.error(f"Error extracting {zip_label}: {e}")
            raise RuntimeError(f"Error extracting {zip_label}") from e

def main(_):
    start_year = 2010
    current_year = datetime.now().year
    
    os.makedirs(SAVE_FOLDER, exist_ok=True)
    year_pairs = [(y - 1, y) for y in range(start_year, current_year)]

    logging.info(f"Starting processing with {MAX_WORKERS} workers...")
    
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(process_year_data, sy, ey): ey for sy, ey in year_pairs}
        for future in as_completed(futures):
            try:
                future.result()
            except Exception as exc:
                logging.error(f"Worker failed: {exc}")
                raise RuntimeError(f"Worker failed: {exc}") from exc

if __name__ == '__main__':
    app.run(main)
# Copyright 2025 Google LLC
# Licensed under the Apache License, Version 2.0

"""
CRDC Data Downloader & Processor (Clean All IDs)
------------------------------------------------
1. Downloads CRDC data.
2. Fixes IDs: Cleans LEAID (7 digits) and SCHID (5 digits).
3. Generates NCESID by combining LEAID + SCHID (Total 12 digits).
4. Saves only the data sheet.
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

KEYWORDS = [
    r'.*09-2 Retention.*',
    r'Retention of Students.*grade (0[1-9]|1[0-2])\.xlsx$',
    r'Retention of Students.*kindergarten\.xlsx$',
    r'Retention\.csv$',
    r'Retention\.xlsx$',
    r'School Data\.csv$'
]

# ID columns excluded from numeric conversion
EXCLUDE_COLS = [
    'JJ', 'LEA_STATE', 'LEA_STATE_NAME', 'LEA_NAME', 'SCH_NAME',
    'NCESID', 'LEAID', 'SCHID', 'COMBOKEY', 'observationDate'
]

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

def clean_id_column(series):
    """
    Helper to clean any ID column: removes non-digits, strips spaces.
    """
    return (series.astype(str)
            .str.replace(r'\D', '', regex=True) # Delete quotes, dots, letters
            .str.strip())

def transform_crdc_data(df: pd.DataFrame, year: int, filename: str) -> pd.DataFrame:
    """
    Applies transformations: Adds observationDate, cleans IDs, 
    and generates NCESID by strictly combining LEAID + SCHID.
    """
    # Uppercase columns first
    df.columns = [x.upper() for x in df.columns]

    # Add Date
    df["observationDate"] = year

    # --- 1. CLEAN & PAD SOURCE COLUMNS ---
    # We must ensure LEAID is 7 chars and SCHID is 5 chars to build a valid 12-char NCESID.
    
    if "LEAID" in df.columns:
        # Remove non-digits, then pad to 7 (e.g., "100005" -> "0100005")
        df["LEAID"] = clean_id_column(df["LEAID"]).str.zfill(7)
    
    if "SCHID" in df.columns:
        # Remove non-digits, then pad to 5 (e.g., "879" -> "00879")
        df["SCHID"] = clean_id_column(df["SCHID"]).str.zfill(5)
        
    if "COMBOKEY" in df.columns:
        df["COMBOKEY"] = clean_id_column(df["COMBOKEY"])

    # --- 2. GENERATE NCESID (STRICT LOGIC) ---
    # Logic: Ignore the source COMBOKEY because it is often corrupt (missing zeros).
    # Instead, construct it: NCESID = LEAID (7) + SCHID (5)
    
    if "LEAID" in df.columns and "SCHID" in df.columns:
        df["NCESID"] = df["LEAID"] + df["SCHID"]
    elif "COMBOKEY" in df.columns:
        # Fallback ONLY if LEAID or SCHID is missing
        logging.warning(f"Using raw COMBOKEY fallback for {filename}")
        df["NCESID"] = df["COMBOKEY"].str.zfill(12)
    else:
        logging.warning(f"Missing LEAID/SCHID or COMBOKEY in {filename}")
        df["NCESID"] = ""

    # --- 3. CLEAN YES/NO ---
    exclude_upper = [c.upper() for c in EXCLUDE_COLS]
    # target columns are those NOT in the exclude list and NOT observationDate
    target_cols = [col for col in df.columns if col not in exclude_upper and col != 'observationDate']
    
    # Replace Yes/No with 1/0
    df[target_cols] = df[target_cols].replace(REPLACEMENT_MAP)
    
    # Convert numeric columns, turning errors into NaN (blank)
    df[target_cols] = df[target_cols].apply(pd.to_numeric, errors='coerce')

    # --- 4. REORDER COLUMNS ---
    priority_cols = ['observationDate', 'NCESID']
    existing_priority = [c for c in priority_cols if c in df.columns]
    other_cols = [c for c in df.columns if c not in existing_priority]
    
    return df[existing_priority + other_cols]

def process_dataframe(file_path: str, year: int):
    """
    Loads, cleans, and saves ONLY the data sheet.
    """
    try:
        filename = os.path.basename(file_path)

        # --- CSV HANDLING ---
        if file_path.lower().endswith(".csv"):
            try:
                df = pd.read_csv(file_path, dtype=str, low_memory=False, encoding='latin1')
            except UnicodeDecodeError:
                df = pd.read_csv(file_path, dtype=str, low_memory=False)

            df = transform_crdc_data(df, year, filename)
            df.to_csv(file_path, index=False)

        # --- XLSX HANDLING ---
        elif file_path.lower().endswith(".xlsx"):
            all_sheets = pd.read_excel(file_path, dtype=str, sheet_name=None)
            
            # Identify the Data Sheet (usually the first one)
            data_sheet_name = list(all_sheets.keys())[0]
            df = all_sheets[data_sheet_name]

            df = transform_crdc_data(df, year, filename)

            # Save only the DATA sheet
            with pd.ExcelWriter(file_path) as writer:
                df.to_excel(writer, sheet_name=data_sheet_name, index=False)
                
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
                # Security Check: Prevent downloading HTML error pages as Zips
                content_type = r.headers.get('Content-Type', '').lower()
                if 'html' in content_type:
                    logging.warning(f"URL {url} returned HTML instead of ZIP. Skipping.")
                    return False
                
                shutil.copyfileobj(r.raw, temp_file)
                return True
    except Exception:
        pass
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

# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

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
from google.cloud import storage

# ==========================================
# Configuration
# ==========================================
MAX_WORKERS = 5
SCRIPT_DIR = Path(os.path.dirname(os.path.abspath(__file__)))

# New Folder Structure
RAW_SAVE_FOLDER = os.path.join(SCRIPT_DIR, "raw_input_files")
TRANSFORMED_SAVE_FOLDER = os.path.join(SCRIPT_DIR, "input_files")

GCS_BUCKET_NAME = "unresolved_mcf"
GCS_BASE_PATH = "country/us_education/us_urbaneducation_school/school_retention/latest/input_files/"

KEYWORDS = [
    r'.*09-2 Retention.*',
    r'Retention of Students.*grade (0[1-9]|1[0-2])\.xlsx$',
    r'Retention of Students.*kindergarten\.xlsx$',
    r'Retention\.csv$',
    r'Retention\.xlsx$',
    r'School Data\.csv$'
]

EXCLUDE_COLS = [
    'JJ', 'LEA_STATE', 'LEA_STATE_NAME', 'LEA_NAME', 'SCH_NAME',
    'NCESID', 'LEAID', 'SCHID', 'COMBOKEY', 'observationDate'
]

REPLACEMENT_MAP = {
    "Yes": 1, "No": 0, "yes": 1, "no": 0, "YES": 1, "NO": 0
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
    return (series.astype(str)
            .str.replace(r'\D', '', regex=True)
            .str.strip())

def transform_crdc_data(df: pd.DataFrame, year: int, filename: str) -> pd.DataFrame:
    df.columns = [x.upper() for x in df.columns]
    df["observationDate"] = year

    if "LEAID" in df.columns:
        df["LEAID"] = clean_id_column(df["LEAID"]).str.zfill(7)
    if "SCHID" in df.columns:
        df["SCHID"] = clean_id_column(df["SCHID"]).str.zfill(5)
    if "COMBOKEY" in df.columns:
        df["COMBOKEY"] = clean_id_column(df["COMBOKEY"])

    if "LEAID" in df.columns and "SCHID" in df.columns:
        df["NCESID"] = df["LEAID"] + df["SCHID"]
    elif "COMBOKEY" in df.columns:
        df["NCESID"] = df["COMBOKEY"].str.zfill(12)
    else:
        df["NCESID"] = ""

    target_cols = [col for col in df.columns if col not in [c.upper() for c in EXCLUDE_COLS]]
    df[target_cols] = df[target_cols].replace(REPLACEMENT_MAP)
    df[target_cols] = df[target_cols].apply(pd.to_numeric, errors='coerce')

    priority_cols = ['observationDate', 'NCESID']
    existing_priority = [c for c in priority_cols if c in df.columns]
    other_cols = [c for c in df.columns if c not in existing_priority]
    return df[existing_priority + other_cols]

# ==========================================
# Core Processing & GCS Logic
# ==========================================

def process_dataframe(raw_file_path: str, year: int):
    try:
        filename = os.path.basename(raw_file_path)
        # Save transformed file with 'transformed_' prefix into 'input_files' folder
        transformed_filename = f"transformed_{filename}"
        transformed_path = os.path.join(TRANSFORMED_SAVE_FOLDER, transformed_filename)

        # 1. Load Data from 'raw_input_files'
        if raw_file_path.lower().endswith(".csv"):
            try:
                df = pd.read_csv(raw_file_path, dtype=str, low_memory=False, encoding='latin1')
            except UnicodeDecodeError:
                df = pd.read_csv(raw_file_path, dtype=str, low_memory=False)
        elif raw_file_path.lower().endswith(".xlsx"):
            all_sheets = pd.read_excel(raw_file_path, dtype=str, sheet_name=None)
            data_sheet_name = list(all_sheets.keys())[0]
            df = all_sheets[data_sheet_name]
        else:
            return

        # 2. Transform
        df_transformed = transform_crdc_data(df, year, filename)

        # 3. Save Transformed to 'input_files'
        if raw_file_path.lower().endswith(".csv"):
            df_transformed.to_csv(transformed_path, index=False)
        else:
            with pd.ExcelWriter(transformed_path) as writer:
                df_transformed.to_excel(writer, sheet_name=data_sheet_name, index=False)

        # 4. Upload Transformed to GCS
        client = storage.Client()
        bucket = client.bucket(GCS_BUCKET_NAME)
        gcs_blob_path = os.path.join(GCS_BASE_PATH, transformed_filename)
        blob = bucket.blob(gcs_blob_path)
        blob.upload_from_filename(transformed_path)

        logging.info(f"Original: {raw_file_path} | Uploaded: gs://{GCS_BUCKET_NAME}/{gcs_blob_path}")

    except Exception as e:
        logging.error(f"Failed to process {raw_file_path}: {e}")

@retry(tries=2, delay=2)
def try_download_url(url, temp_file):
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        with requests.get(url, headers=headers, stream=True, timeout=120) as r:
            if r.status_code == 200 and 'html' not in r.headers.get('Content-Type', '').lower():
                shutil.copyfileobj(r.raw, temp_file)
                return True
    except Exception:
        pass
    return False

def process_year_data(start_year: int, end_year: int):
    possible_urls = get_urls_for_year(start_year, end_year)
    zip_label = f"{start_year}-{str(end_year)[-2:]}"

    # TODO: Preserve the downloaded zip file and not keep it as a tmp file.
    with tempfile.NamedTemporaryFile(delete=True) as tmp_zip:
        downloaded = False
        for url in possible_urls:
            tmp_zip.seek(0)
            tmp_zip.truncate()
            if try_download_url(url, tmp_zip):
                downloaded = True
                break
        
        if not downloaded: return

        tmp_zip.flush()
        try:
            with zipfile.ZipFile(tmp_zip.name) as z:
                matched_files = [f for f in z.namelist() if matches_keywords(f)]
                for file_name in matched_files:
                    output_filename = f"{end_year}_{os.path.basename(file_name)}"
                    # Extract original to 'raw_input_files'
                    raw_output_path = os.path.join(RAW_SAVE_FOLDER, output_filename)
                    with z.open(file_name) as source, open(raw_output_path, "wb") as target:
                        shutil.copyfileobj(source, target)
                    
                    process_dataframe(raw_output_path, end_year)
        except Exception as e:
            logging.error(f"Error extracting {zip_label}: {e}")

def main(_):
    start_year = 2010
    current_year = datetime.now().year
    
    # Ensure both local folders exist
    os.makedirs(RAW_SAVE_FOLDER, exist_ok=True)
    os.makedirs(TRANSFORMED_SAVE_FOLDER, exist_ok=True)
    
    year_pairs = [(y - 1, y) for y in range(start_year, current_year)]
    
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(process_year_data, sy, ey): ey for sy, ey in year_pairs}
        for future in as_completed(futures):
            try:
                future.result()
            except Exception as exc:
                logging.error(f"Worker failed: {exc}")

if __name__ == '__main__':
    app.run(main)

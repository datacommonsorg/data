# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import re
import io
import zipfile
import requests
import pandas as pd
from datetime import datetime
from absl import logging, app
from pathlib import Path
from retry import retry

# Base URL template
BASE_URL_TEMPLATE = "https://civilrightsdata.ed.gov/assets/ocr/docs/{}-{}-crdc-data.zip"

SCRIPT_DIR = Path(os.path.dirname(os.path.abspath(__file__)))
SAVE_FOLDER = os.path.join(SCRIPT_DIR, "input_files")

# Keyword patterns
KEYWORDS = [
    r'Advanced Mathematics\.(csv|xlsx)$',
    r'Physics\.(csv|xlsx)$',
    r'Calculus\.(csv|xlsx)$',
    r'School Data\.csv$',
    r'Geometry\.(csv|xlsx)$',
    r'Chemistry\.(csv|xlsx)$',
    r'Biology\.(csv|xlsx)$',
    r'Algebra II\.(csv|xlsx)$'
]

def matches_keywords(filename: str) -> bool:
    """Return True if filename matches any of the target patterns."""
    return any(re.search(pattern, filename, re.IGNORECASE) for pattern in KEYWORDS)

def add_year_ncesid_column(file_path: str, year: int):
    """Open CSV/XLSX, add YEAR column, and overwrite."""
    try:
        if file_path.lower().endswith(".csv"):
            df = pd.read_csv(file_path, dtype=str, low_memory=False, encoding='latin1')
        elif file_path.lower().endswith(".xlsx"):
            df = pd.read_excel(file_path, dtype=str, engine='openpyxl')
        else:
            logging.warning(f"Skipping non-tabular file: {file_path}")
            return

        df["YEAR"] = year
        if all(col in df.columns for col in ["LEAID", "SCHID"]):
            df["LEAID"] = df["LEAID"].astype(str).str.zfill(7)
            df["SCHID"] = df["SCHID"].astype(str).str.zfill(5)
            df["ncesid"] = df["LEAID"] + df["SCHID"]
        else:
            logging.warning(f"Warning: Missing LEAID or SCHID columns for NCESID creation in {os.path.basename(file_path)}")

        df.to_csv(file_path, index=False) if file_path.lower().endswith(".csv") else df.to_excel(file_path, index=False)
        logging.info(f"YEAR column added ({year}) → {os.path.basename(file_path)}")

    except Exception as e:
        raise RuntimeError(f"Failed to add YEAR and nces id columns to {file_path}: {e}")

@retry(tries=3, delay=5, backoff=2)
def download_url_with_retry(zip_url):
    """Handles downloading the ZIP content with retries and status checks."""
    try:
        head_response = requests.head(zip_url, allow_redirects=True, timeout=10)
        head_response.raise_for_status() 
        response = requests.get(zip_url, stream=True, timeout=180)
        response.raise_for_status() 
        return response
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            raise FileNotFoundError(f"URL returned 404: {zip_url}") from e
        raise

def download_and_extract_zip(start_year: int, end_year: int):
    """Download and extract matching files for a year range ZIP."""
    zip_name = f"{start_year}-{str(end_year)[-2:]}-crdc-data.zip"
    url = BASE_URL_TEMPLATE.format(start_year, str(end_year)[-2:])
    logging.info(f"\nDownloading {zip_name} ...")

    try:
        response = download_url_with_retry(url)
        if response.status_code != 200:
            logging.warning(f"Skipped {zip_name} (HTTP {response.status_code})")
            return

        with zipfile.ZipFile(io.BytesIO(response.content)) as z:
            matched_files = [f for f in z.namelist() if matches_keywords(f)]

            if not matched_files:
                logging.warning(f"No matching files found in {zip_name}")
                return

            os.makedirs(SAVE_FOLDER, exist_ok=True)

            for file_name in matched_files:
                output_filename = f"{end_year}_{os.path.basename(file_name)}"
                output_path = os.path.join(SAVE_FOLDER, output_filename)

                with z.open(file_name) as source, open(output_path, "wb") as target:
                    target.write(source.read())

                logging.info(f"Extracted: {output_filename}")
                add_year_ncesid_column(output_path, end_year)
        logging.info("Downloading completed...!")

    except Exception as e:
        logging.error(f"Error downloading {zip_name}: {e}")
        return None

def main(_):
    start_year = 2010
    current_year = datetime.now().year

    for year in range(start_year, current_year):
        download_and_extract_zip(year - 1, year)

if __name__ == '__main__':
    app.run(main)


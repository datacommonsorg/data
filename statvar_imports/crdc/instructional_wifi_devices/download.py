# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Downloads and extracts CRDC Instructional WiFi Devices data."""

import datetime
import logging
from pathlib import Path
import re
import shutil
import sys
import tempfile
import time
import zipfile

import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# --- 1. Constants ---
BASE_URL = "https://civilrightsdata.ed.gov/assets/ocr/docs/"
TARGET_CSV_NAME = "Internet Access and Devices"
SCRIPT_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = SCRIPT_DIR / "input_files"
REQUEST_TIMEOUT = 60  # seconds


# --- 2. Helper Functions ---

def create_session() -> requests.Session:
    """Creates a requests.Session configured with exponential backoff retries."""
    session = requests.Session()
    session.headers.update({
        "User-Agent": (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    })
    retries = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retries)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


def generate_year_strings(start_year: int = 2020) -> list[str]:
    """Generates academic year strings (e.g. '2020-21') in chronological order."""
    current_date = datetime.datetime.now()
    current_year = current_date.year
    current_month = current_date.month

    max_start_year = current_year if current_month >= 8 else current_year - 1

    year_strings = []
    for y in range(start_year, max_start_year + 1):
        end_year_two_digits = str(y + 1)[2:]
        year_strings.append(f"{y}-{end_year_two_digits}")

    return year_strings


def get_full_year(year_string: str) -> int:
    """Derives full calendar year (e.g., 2024 from '2023-24') for the YEAR column."""
    match = re.match(r"^(\d{4})-(\d{2})$", year_string.strip())
    if not match:
        raise ValueError(
            f"Invalid academic year format '{year_string}'. Expected format: 'YYYY-YY'"
        )
    century = match.group(1)[:2]
    return int(f"{century}{match.group(2)}")


def process_crdc_data(session: requests.Session, year_string: str) -> bool:
    """Downloads, extracts, processes, and atomically saves the target CSV.

    Returns True if successfully downloaded and processed, False otherwise.
    """
    zip_filename = f"{year_string}-crdc-data.zip"
    full_url = f"{BASE_URL}{zip_filename}"
    target_year = get_full_year(year_string)

    logging.info(
        "Starting download for academic year %s (Target YEAR=%d)",
        year_string,
        target_year,
    )

    try:
        response = session.get(full_url, stream=True, timeout=REQUEST_TIMEOUT)
        if response.status_code == 404:
            logging.info(
                "Dataset for year %s not found (HTTP 404). Skipping.",
                year_string,
            )
            return False
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logging.error("Failed to download %s: %s", full_url, e)
        raise

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        temp_zip_file = temp_path / zip_filename

        with open(temp_zip_file, "wb") as f:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    f.write(chunk)

        try:
            with zipfile.ZipFile(temp_zip_file, "r") as zf:
                target_member = None
                for member in zf.infolist():
                    if member.is_dir():
                        continue
                    member_name = Path(member.filename).name
                    if (
                        TARGET_CSV_NAME.lower() in member_name.lower()
                        and member_name.lower().endswith(".csv")
                    ):
                        target_member = member
                        break

                if not target_member:
                    logging.warning(
                        "Could not find CSV matching '%s' in %s",
                        TARGET_CSV_NAME,
                        zip_filename,
                    )
                    return False

                # Extract single target CSV safely (prevent path traversal / Zip Slip)
                safe_filename = Path(target_member.filename).name
                extracted_csv_path = temp_path / safe_filename
                with zf.open(target_member) as src, open(
                    extracted_csv_path, "wb"
                ) as dst:
                    shutil.copyfileobj(src, dst)

        except zipfile.BadZipFile:
            logging.error(
                "Downloaded file for %s is not a valid ZIP file.", year_string
            )
            return False

        try:
            # Preserve leading zeros in school codes (COMBOKEY, LEAID, SCHID)
            df = pd.read_csv(
                extracted_csv_path,
                dtype=str,
                encoding="latin-1",
                low_memory=False,
            )
            df["YEAR"] = str(target_year)

            output_filename = (
                OUTPUT_DIR
                / f"{TARGET_CSV_NAME.replace(' ', '_')}_{target_year}.csv"
            )
            temp_output = output_filename.with_suffix(".csv.tmp")

            # Write atomically
            df.to_csv(temp_output, index=False, encoding="utf-8")
            if temp_output.stat().st_size == 0 or len(df) == 0:
                raise IOError(f"Output CSV {temp_output} is empty.")

            temp_output.replace(output_filename)
            logging.info(
                "Successfully saved %d rows to: %s",
                len(df),
                output_filename.resolve(),
            )
            return True

        except Exception as e:
            logging.error(
                "Error processing CSV for year %s: %s", year_string, e
            )
            raise


# --- 3. Main Execution Block ---

def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )

    try:
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        logging.info("Output directory verified: %s", OUTPUT_DIR.resolve())
    except Exception as e:
        logging.fatal(
            "FATAL: Could not create output directory %s. Error: %s",
            OUTPUT_DIR.resolve(),
            e,
        )
        sys.exit(1)

    year_strings = generate_year_strings()
    session = create_session()

    success_count = 0

    for year in year_strings:
        try:
            downloaded = process_crdc_data(session, year)
            if downloaded:
                success_count += 1
        except Exception as e:
            logging.error("Failed processing year %s: %s", year, e)

        time.sleep(1)

    if success_count == 0:
        logging.fatal("FATAL: No CRDC datasets were successfully downloaded.")
        sys.exit(1)

    logging.info(
        "Download complete. Successfully processed %d dataset(s).",
        success_count,
    )


if __name__ == "__main__":
    main()
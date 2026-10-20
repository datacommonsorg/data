#!/usr/bin/env python3
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
"""Standalone downloader for NCES Private School Survey (PSS) public data."""

import csv
import io
import os
import re
import shutil
import time
import urllib.parse
import zipfile

from absl import app
from absl import logging
from bs4 import BeautifulSoup
import requests

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PSS_DATA_PAGE_URL = "https://nces.ed.gov/surveys/pss/pssdata.asp"
PSS_BASE_URL = "https://nces.ed.gov/surveys/pss/"
MAX_RETRIES = 5
RETRY_SLEEP_SECS = 3
PERMANENT_CLIENT_ERRORS = {400, 401, 403, 404}


def retry_call(func, *args, **kwargs):
    """Executes func with exponential backoff on transient failure."""
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            return func(*args, **kwargs)
        except requests.exceptions.HTTPError as exc:
            # Fail fast on permanent client errors per code_criteria.md
            status_code = getattr(exc.response, "status_code", None)
            if status_code in PERMANENT_CLIENT_ERRORS:
                logging.error(
                    "Permanent client error %d for %s; aborting retry.",
                    status_code,
                    args,
                )
                raise
            if attempt == MAX_RETRIES:
                logging.error("Failed after %d attempts: %s", attempt, exc)
                raise
            sleep_time = RETRY_SLEEP_SECS * (2**(attempt - 1))
            logging.warning(
                "Attempt %d/%d failed with %s; sleeping %ds before retry...",
                attempt,
                MAX_RETRIES,
                exc,
                sleep_time,
            )
            time.sleep(sleep_time)
        except Exception as exc:
            if attempt == MAX_RETRIES:
                logging.error("Failed after %d attempts: %s", attempt, exc)
                raise
            sleep_time = RETRY_SLEEP_SECS * (2**(attempt - 1))
            logging.warning(
                "Attempt %d/%d failed with %s; sleeping %ds before retry...",
                attempt,
                MAX_RETRIES,
                exc,
                sleep_time,
            )
            time.sleep(sleep_time)


def _download_and_extract_pss_zip(session: requests.Session, zip_url: str,
                                  extract_dir: str) -> None:
    """Downloads PSS public ZIP archive and extracts CSV/TXT data as CSV."""
    res = session.get(zip_url, timeout=(10, 120))
    res.raise_for_status()

    os.makedirs(extract_dir, exist_ok=True)

    # Clean out any stale legacy ELSI exports seeded from previous production runs.
    for existing_file in os.listdir(extract_dir):
        if existing_file.lower().startswith("elsi_"):
            try:
                os.remove(os.path.join(extract_dir, existing_file))
                logging.info("Removed stale legacy export: %s", existing_file)
            except OSError as e:
                logging.warning("Could not remove %s: %s", existing_file, e)

    extracted_files = []
    with zipfile.ZipFile(io.BytesIO(res.content)) as zf:
        for member in zf.namelist():
            filename = os.path.basename(member)
            if not filename:
                continue
            lower_name = filename.lower()
            if lower_name.endswith(".csv"):
                target_path = os.path.join(extract_dir, filename)
                temp_path = target_path + ".tmp"
                with zf.open(member) as src, open(temp_path, "wb") as dst:
                    shutil.copyfileobj(src, dst)
                os.replace(temp_path, target_path)
                if os.path.getsize(target_path) > 0:
                    extracted_files.append(target_path)
                logging.info("Extracted PSS CSV to: %s", target_path)
            elif lower_name.endswith(".txt"):
                stem = os.path.splitext(filename)[0]
                target_path = os.path.join(extract_dir, f"{stem}.csv")
                temp_path = target_path + ".tmp"
                with zf.open(member) as raw_src:
                    text_stream = io.TextIOWrapper(raw_src,
                                                   encoding="ISO-8859-1")
                    reader = csv.reader(text_stream, delimiter="\t")
                    with open(temp_path, "w", newline="",
                              encoding="utf-8") as dst:
                        writer = csv.writer(dst)
                        writer.writerows(reader)
                os.replace(temp_path, target_path)
                if os.path.getsize(target_path) > 0:
                    extracted_files.append(target_path)
                logging.info("Converted tab-delimited PSS TXT to CSV: %s",
                             target_path)

    if not extracted_files:
        raise RuntimeError(
            f"No valid non-empty CSV/TXT files were extracted from {zip_url} into {extract_dir}"
        )


def download_pss_private_school_files() -> None:
    """Downloads PSS public-use data files from official portal."""
    logging.info("Fetching PSS data page: %s", PSS_DATA_PAGE_URL)
    with requests.Session() as session:

        def _fetch_page(url: str) -> requests.Response:
            resp = session.get(url, timeout=(10, 60))
            resp.raise_for_status()
            return resp

        response = retry_call(_fetch_page, PSS_DATA_PAGE_URL)

        soup = BeautifulSoup(response.text, "html.parser")

        # Map start_year -> full_zip_url
        year_to_url = {}
        zip_patterns = [
            re.compile(r"zip/pss(\d{2})(\d{2})_pu_(?:csv|txt)\.zip$",
                       re.IGNORECASE),
            re.compile(r"zip/TXT_PSS(\d{2})(\d{2})\.zip$", re.IGNORECASE),
        ]
        for a_tag in soup.find_all("a", href=True):
            href = a_tag["href"].strip()
            for pat in zip_patterns:
                match = pat.search(href)
                if match:
                    yy1 = match.group(1)
                    century = "19" if int(yy1) >= 80 else "20"
                    start_year = f"{century}{yy1}"
                    full_url = urllib.parse.urljoin(PSS_BASE_URL, href)
                    year_to_url[start_year] = full_url
                    break

        target_years = sorted([y for y in year_to_url.keys() if int(y) >= 1997])

        if not target_years:
            raise RuntimeError(
                f"Failed to find any PSS survey ZIP links on {PSS_DATA_PAGE_URL}. "
                "The page structure or link URLs may have changed.")

        for start_year in target_years:
            zip_url = year_to_url[start_year]
            extract_dir = os.path.join(_SCRIPT_DIR, "gcs_folder", "input_files",
                                       start_year)
            logging.info("Downloading PSS data for year %s from %s", start_year,
                         zip_url)
            retry_call(_download_and_extract_pss_zip, session, zip_url,
                       extract_dir)


def main(argv):
    del argv  # Unused
    logging.set_verbosity(logging.INFO)
    logging.info("Starting PSS Private School Data Download...")
    download_pss_private_school_files()
    logging.info("PSS Private School Data Download Completed.")


if __name__ == "__main__":
    app.run(main)

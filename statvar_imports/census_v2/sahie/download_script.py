# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the 'License');
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#             https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an 'AS IS' BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# How to run the script to download the files:
# python3 download_script.py

import datetime
import glob
import os
import shutil
import sys
from absl import app
from absl import logging
import requests
from retry import retry

_SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(_SCRIPT_PATH, '../../../util/'))
from download_util_script import download_file

_DEFAULT_HEADERS = {
    'User-Agent': 'DataCommons-Import-Automation/1.0 (support@datacommons.org)'
}


class _TransientHTTPError(requests.exceptions.HTTPError):
    """Exception raised for retryable HTTP status codes (429 and 5xx)."""


def _is_year_url_available(url: str,
                           session: requests.Session,
                           headers: dict = None,
                           tries: int = 3,
                           delay: int = 5,
                           backoff: int = 2) -> bool:
    """Checks whether a SAHIE release archive URL exists on the Census server.

    Returns False immediately on HTTP 404 (unpublished year) without retrying.
    Retries transient network errors (ConnectionError, Timeout) and retryable
    HTTP status codes (429, 5xx), and raises RuntimeError if availability cannot
    be verified.
    """

    @retry(tries=tries,
           delay=delay,
           backoff=backoff,
           exceptions=(requests.exceptions.ConnectionError,
                       requests.exceptions.Timeout, _TransientHTTPError))
    def _probe() -> bool:
        logging.info(f"Checking availability via HEAD request: {url}")
        req_lib = session if session is not None else requests
        response = req_lib.head(url,
                                headers=headers,
                                allow_redirects=True,
                                timeout=10)
        if response.status_code == 405:
            response = req_lib.get(url,
                                   headers=headers,
                                   stream=True,
                                   timeout=10)
            response.close()

        if response.status_code == 404:
            return False
        if response.status_code == 429 or response.status_code >= 500:
            raise _TransientHTTPError(
                f"Transient HTTP {response.status_code} for {url}",
                response=response)
        response.raise_for_status()
        return True

    try:
        return _probe()
    except requests.exceptions.RequestException as e:
        logging.error(f"Error checking availability for {url}: {e}")
        raise RuntimeError(f"Failed availability check for {url}") from e


def clean_csv_file(file_path: str, output_path: str = None) -> None:
    """
    Cleans a single CSV file by removing the header description.
    Reads from file_path with UTF-8 (with fallback to Latin-1 for accented
    county names or preamble characters) and writes the cleaned CSV to
    output_path (or in-place to file_path if output_path is None) using UTF-8.
    """
    # List of required header columns to identify the start of the CSV data.
    header_parts = ['year', 'version', 'statefips', 'countyfips', 'geocat']
    target_path = output_path if output_path is not None else file_path
    temp_file_path = target_path + ".tmp"
    try:
        content = None
        for encoding in ('utf-8-sig', 'latin-1'):
            try:
                logging.info(
                    f"Reading {os.path.basename(file_path)} with {encoding} encoding."
                )
                with open(file_path, 'r', encoding=encoding) as infile:
                    content = infile.readlines()
                break
            except UnicodeDecodeError:
                logging.warning(
                    f"Failed to decode {os.path.basename(file_path)} with {encoding}, trying fallback encoding."
                )

        if content is None:
            raise RuntimeError(
                f"Failed to decode file {file_path} with supported encodings.")

        found_header = False
        os.makedirs(os.path.dirname(os.path.abspath(target_path)),
                    exist_ok=True)
        with open(temp_file_path, 'w', encoding='utf-8') as outfile:
            for line in content:
                # The actual CSV data starts with the comma-separated header row.
                if not found_header:
                    columns = [col.strip().lower() for col in line.split(',')]
                    if columns[:len(header_parts)] == header_parts:
                        found_header = True

                if found_header:
                    outfile.write(line)

        if not found_header:
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
            raise RuntimeError(
                f"CSV header {header_parts} not found in {file_path}.")

        shutil.move(temp_file_path, target_path)
        logging.info(
            f"Successfully cleaned file: {os.path.basename(target_path)}")

    except Exception as e:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        logging.error(f"Error processing file {file_path}: {e}")
        raise RuntimeError(f"Failed to process file {file_path}") from e


_BASE_URL = "https://www2.census.gov/programs-surveys/sahie/datasets/time-series/estimates-acs/sahie-{year}-csv.zip"
_RAW_DIRECTORY = os.path.join(_SCRIPT_PATH, "raw_files")
_OUTPUT_DIRECTORY = os.path.join(_SCRIPT_PATH, "input_files")
_START_YEAR = 2018
# US Census SAHIE has a ~2-year publication lag (released late in the year, so
# up to 3 years lag in early calendar months). Historical years up to
# (current_year - _MAX_PUBLICATION_LAG_YEARS) must exist; newer candidate years
# are probed for HTTP 404 before downloading.
_MAX_PUBLICATION_LAG_YEARS = 3


def main(_):
    logging.set_verbosity(logging.INFO)
    os.makedirs(_RAW_DIRECTORY, exist_ok=True)
    os.makedirs(_OUTPUT_DIRECTORY, exist_ok=True)
    logging.info(
        f"Directories '{_RAW_DIRECTORY}' and '{_OUTPUT_DIRECTORY}' ensured to exist."
    )

    current_year = datetime.datetime.now().year
    latest_required_year = max(_START_YEAR,
                               current_year - _MAX_PUBLICATION_LAG_YEARS)
    processing_succeeded = False

    try:
        with requests.Session() as session:
            for year in range(_START_YEAR, current_year + 1):
                year_url = _BASE_URL.format(year=year)
                if year > latest_required_year:
                    if not _is_year_url_available(url=year_url,
                                                  session=session,
                                                  headers=_DEFAULT_HEADERS):
                        logging.warning(
                            f"Data for recent year {year} is not yet available at {year_url}. Stopping further downloads."
                        )
                        break

                success = download_file(url=year_url,
                                        output_folder=_RAW_DIRECTORY,
                                        unzip=True,
                                        headers=_DEFAULT_HEADERS,
                                        session=session,
                                        tries=5,
                                        delay=10)

                if not success:
                    logging.error(
                        f"Failed to download SAHIE data for year {year} from {year_url}."
                    )
                    raise RuntimeError(
                        f"Failed to download SAHIE data for year {year} from {year_url}."
                    )

                logging.info(f"Successfully downloaded data for year {year}.")

        raw_csv_files = sorted(glob.glob(os.path.join(_RAW_DIRECTORY, "*.csv")))
        if not raw_csv_files:
            raise RuntimeError(
                f"No CSV files were downloaded into '{_RAW_DIRECTORY}'.")

        # Write cleaned CSV files to _OUTPUT_DIRECTORY while preserving raw files
        for raw_csv_file in raw_csv_files:
            cleaned_csv_path = os.path.join(_OUTPUT_DIRECTORY,
                                            os.path.basename(raw_csv_file))
            clean_csv_file(raw_csv_file, cleaned_csv_path)

        processing_succeeded = True

    finally:
        if os.path.exists(_OUTPUT_DIRECTORY):
            for item in os.listdir(_OUTPUT_DIRECTORY):
                item_path = os.path.join(_OUTPUT_DIRECTORY, item)
                if item.endswith(".tmp") or item.endswith(".zip"):
                    os.remove(item_path)
                    logging.info(f"Removed temporary/archive file: {item_path}")
                elif not processing_succeeded and item.endswith(".csv"):
                    os.remove(item_path)
                    logging.info(
                        f"Removed incomplete CSV file after failure: {item_path}"
                    )

        logging.info("Final cleanup complete")


if __name__ == '__main__':
    app.run(main)

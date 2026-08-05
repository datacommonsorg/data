# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#           https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import sys
import re
from urllib.parse import urlparse
from absl import app
from absl import logging
import openpyxl
import requests

# Add data/util to sys.path so we can import the shared wrapper functions
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, '../../..'))
UTIL_DIR = os.path.join(PROJECT_ROOT, 'util')
if UTIL_DIR not in sys.path:
    sys.path.insert(0, UTIL_DIR)

try:
    from download_util_script import download_file, _retry_method
except ImportError:
    logging.fatal(
        "Could not import download_file from 'util/download_util_script.py'."
    )
    sys.exit(1)

LANDING_PAGE_URL = "https://ncses.nsf.gov/surveys/national-survey-college-graduates"
FILE_PATTERN = r'/pubs/[^/]+/assets/data-tables/tables/[^/]*tab006-002\.(?:xlsx|csv)'
OUTPUT_FOLDER = os.path.join(SCRIPT_DIR, "source_files")
YEAR_HEADER_PATTERN = re.compile(r'^\s*(\d{4})[a-zA-Z*#]+\s*$')


def resolve_url(landing_url=LANDING_PAGE_URL,
                file_pattern=FILE_PATTERN,
                headers=None,
                tries=3,
                delay=5,
                backoff=2):
    """
    Scrapes landing page HTML to dynamically find matching table URL.

    Args:
        landing_url: URL of the webpage containing table links.
        file_pattern: Regex pattern to match the target link.
        headers: Optional dictionary of HTTP headers to send with the request.
        tries: Number of retry attempts.
        delay: Initial delay for retries.
        backoff: Backoff factor for retries.

    Returns:
        str: Absolute URL of the target file, or None if not found.
    """
    logging.info(f"Attempting to resolve target URL from landing page: {landing_url}")

    try:
        response = _retry_method(landing_url, headers, tries, delay, backoff)
        response.raise_for_status()
    except (requests.exceptions.RequestException, ValueError, OSError) as e:
        logging.error(f"Failed to fetch landing page '{landing_url}': {e}")
        return None
    except Exception as e:
        logging.fatal(
            f"An unexpected error occurred while fetching landing page '{landing_url}': {e}"
        )
        return None

    matches = re.findall(file_pattern, response.text)
    if not matches:
        logging.error(
            f"No link matching pattern '{file_pattern}' found on '{landing_url}'."
        )
        return None

    resolved_path = matches[0]
    parsed_landing = urlparse(landing_url)
    base_domain = f"{parsed_landing.scheme}://{parsed_landing.netloc}"
    resolved_url = f"{base_domain}{resolved_path}"
    logging.info(f"Dynamically resolved download URL: {resolved_url}")
    return resolved_url


def clean_year_headers(folder_path, max_header_row=4):
    """
    Cleans year headers in downloaded Excel files by removing footnote suffixes
    (e.g., '2023a' -> '2023') strictly in the top header rows (rows 1-4).
    Leaves all data rows (row 5+) completely untouched.

    Args:
        folder_path: Path to the directory containing downloaded Excel files.
        max_header_row: Maximum row index to inspect for header columns.

    Returns:
        bool: True if header cleaning succeeded, False if an error occurred.
    """
    if not folder_path or not os.path.exists(folder_path):
        return True

    for filename in os.listdir(folder_path):
        if not filename.endswith('.xlsx'):
            continue

        file_path = os.path.join(folder_path, filename)
        wb = None
        try:
            wb = openpyxl.load_workbook(file_path)
            sheet = wb.active
            modified = False
            for row in sheet.iter_rows(max_row=max_header_row):
                for cell in row:
                    if isinstance(cell.value, str):
                        new_val = YEAR_HEADER_PATTERN.sub(r'\1', cell.value)
                        if new_val != cell.value:
                            cell.value = new_val
                            modified = True
            if modified:
                wb.save(file_path)
                logging.info(f"Successfully cleaned year headers in '{file_path}'")
        except (ValueError, OSError) as e:
            logging.error(f"Error cleaning headers in file '{file_path}': {e}")
            return False
        except Exception as e:
            logging.fatal(
                f"An unexpected error occurred while cleaning headers in '{file_path}': {e}"
            )
            return False
        finally:
            if wb is not None:
                wb.close()

    return True


def main(_):
    logging.set_verbosity(logging.INFO)
    logging.info("Script execution started...")

    resolved_url = resolve_url(LANDING_PAGE_URL, FILE_PATTERN, None)
    if not resolved_url:
        logging.error("Failed to resolve URL from landing page.")
        sys.exit(1)

    if not download_file(resolved_url, OUTPUT_FOLDER, False, None):
        logging.error(
            "File download or processing failed. Check logs for details.")
        sys.exit(1)

    if not clean_year_headers(OUTPUT_FOLDER):
        logging.error("Year header cleaning failed. Check logs for details.")
        sys.exit(1)

    logging.info("Script processing completed successfully.")


if __name__ == '__main__':
    app.run(main)

#!/usr/bin/env python3
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
"""Download and preprocess NSCG employed college graduates tables.

This script scrapes the NCSES National Survey of College Graduates (NSCG)
landing page to discover the latest publication table (Table 6-2), downloads
the raw Excel file into source_files/, and creates an atomically written
cleaned copy (cleaned_<filename>.xlsx) where year headers with survey
methodology footnote suffixes (e.g. '2023a' -> '2023') are normalized strictly
within header rows 1-4.
"""

import os
import re
import sys
from typing import Optional
from urllib.parse import urlparse
from absl import app
from absl import logging
import openpyxl

# Add data/util to sys.path so we can import shared wrapper functions
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.abspath(os.path.join(_SCRIPT_DIR, '../../..'))
_UTIL_DIR = os.path.join(_PROJECT_ROOT, 'util')
if _UTIL_DIR not in sys.path:
    sys.path.insert(0, _UTIL_DIR)

try:
    from download_util import request_url
    from download_util_script import download_file
except ImportError:
    logging.fatal("Could not import download utilities from 'util/'.")

LANDING_PAGE_URL = (
    "https://ncses.nsf.gov/surveys/national-survey-college-graduates")
FILE_PATTERN = (
    r'/pubs/[^/]+/assets/data-tables/tables/[^/]*tab006-002\.(?:xlsx|csv)')
OUTPUT_FOLDER = os.path.join(_SCRIPT_DIR, "source_files")

# Pattern to strip footnote markers (e.g. '2023a' -> '2023').
# Note: In Table 6-2 (NSF 25-322), footnote 'a' on '2023a' denotes a survey
# question change: "The 2023 estimates by sex were based on responses to the
# question, 'What sex were you assigned at birth, on your original birth
# certificate? 1. Male, 2. Female,' which was a change from prior survey cycles."
YEAR_HEADER_PATTERN = re.compile(r'^\s*(\d{4})([a-zA-Z*#].*|\s+.*)?$',
                                 re.DOTALL)


def resolve_url(landing_url: str = LANDING_PAGE_URL,
                file_pattern: str = FILE_PATTERN,
                headers: Optional[dict] = None,
                tries: int = 3,
                delay: int = 5) -> Optional[str]:
    """Scrapes landing page HTML to dynamically find matching table URL.

    Args:
        landing_url: URL of the webpage containing table links.
        file_pattern: Regex pattern to match the target link.
        headers: Optional dictionary of HTTP headers to send with the request.
        tries: Number of retry attempts.
        delay: Initial delay for retries in seconds.

    Returns:
        Absolute URL of the target file, or None if not found or on error.
    """
    logging.info("Attempting to resolve target URL from landing page: %s",
                 landing_url)

    try:
        content = request_url(landing_url,
                              headers=headers or {},
                              output='text',
                              retries=tries,
                              retry_secs=delay)
    except Exception as e:
        logging.error("Failed to fetch landing page '%s': %s", landing_url, e)
        return None

    if not content:
        logging.error("Failed to fetch landing page '%s': empty response.",
                      landing_url)
        return None

    matches = re.findall(file_pattern, content)
    if not matches:
        logging.error("No link matching pattern '%s' found on '%s'.",
                      file_pattern, landing_url)
        return None

    resolved_path = matches[0]
    parsed_landing = urlparse(landing_url)
    base_domain = f"{parsed_landing.scheme}://{parsed_landing.netloc}"
    resolved_url = f"{base_domain}{resolved_path}"
    logging.info("Dynamically resolved download URL: %s", resolved_url)
    return resolved_url


def clean_year_headers(folder_path: str, max_header_row: int = 4) -> bool:
    """Cleans year headers in downloaded Excel files by removing footnote suffixes.

    Normalizes footnote suffixes (e.g., '2023a' -> '2023') strictly in the top
    header rows (rows 1-4). Leaves all data rows (row 5+) completely untouched.
    Writes the output to a separate 'cleaned_<filename>' file atomically using a
    temporary file and rename, preserving raw data provenance and original file
    modification timestamps.

    Args:
        folder_path: Path to directory containing downloaded Excel files.
        max_header_row: Maximum row index to inspect for header columns.

    Returns:
        True if header cleaning succeeded, False if an error occurred.
    """
    if not folder_path or not os.path.exists(folder_path):
        return True

    for filename in os.listdir(folder_path):
        if not filename.endswith('.xlsx') or filename.startswith('cleaned_'):
            continue

        file_path = os.path.join(folder_path, filename)
        cleaned_file_path = os.path.join(folder_path, f"cleaned_{filename}")
        temp_cleaned_path = f"{cleaned_file_path}.tmp"
        wb = None
        try:
            wb = openpyxl.load_workbook(file_path)
            sheet = wb.active
            for row in sheet.iter_rows(max_row=max_header_row):
                for cell in row:
                    if isinstance(cell.value, str):
                        new_val = YEAR_HEADER_PATTERN.sub(r'\1', cell.value)
                        if new_val != cell.value:
                            cell.value = new_val
            # Atomic write: save to temporary file, then atomic rename
            wb.save(temp_cleaned_path)
            os.replace(temp_cleaned_path, cleaned_file_path)
            logging.info("Successfully wrote cleaned file to '%s'",
                         cleaned_file_path)
        except (ValueError, OSError) as e:
            logging.error("Error cleaning headers in file '%s': %s", file_path,
                          e)
            if os.path.exists(temp_cleaned_path):
                try:
                    os.remove(temp_cleaned_path)
                except OSError:
                    pass
            return False
        except Exception as e:
            logging.error(
                "An unexpected error occurred while cleaning headers in '%s': %s",
                file_path, e)
            if os.path.exists(temp_cleaned_path):
                try:
                    os.remove(temp_cleaned_path)
                except OSError:
                    pass
            return False
        finally:
            if wb is not None:
                wb.close()

    return True


def main(_):
    logging.set_verbosity(logging.INFO)
    logging.info("Script execution started...")

    # Ensure output directory exists idempotently
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)

    resolved_url = resolve_url(LANDING_PAGE_URL, FILE_PATTERN, None)
    if not resolved_url:
        logging.fatal("Failed to resolve URL from landing page.")

    if not download_file(resolved_url, OUTPUT_FOLDER, False, None):
        logging.fatal(
            "File download or processing failed. Check logs for details.")

    if not clean_year_headers(OUTPUT_FOLDER):
        logging.fatal("Year header cleaning failed. Check logs for details.")

    logging.info("Script processing completed successfully.")


if __name__ == '__main__':
    app.run(main)

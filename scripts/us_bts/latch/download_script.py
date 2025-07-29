# Copyright 2022 Google LLC
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
"""This script downloads files from a JSON configuration,
handling various file types including paginated API data and compressed archives,
leveraging a separate utility for general downloads."""

# Standard library imports
import gzip
import json
import os
import subprocess
import sys  # <-- sys is needed for path modification
import time
from typing import List, Dict
from urllib.parse import urlparse

# Third-party imports
import requests
from absl import app, flags, logging

# --- Start of Path Modification for Relative Import ---
# This block allows the script to be run from its current directory (latch/)
# and still find 'util/download_util_script.py'
current_script_dir = os.path.dirname(os.path.abspath(__file__))

# Navigate back from 'latch' -> 'us_bts' -> 'scripts' -> 'data'
# So, from 'latch' (current_script_dir) go up 4 levels to get to the project root.
# (latch/ -> us_bts/ -> scripts/ -> data/ -> USBTS_Tract_Household_Transportation/)
# Then from the project root, go into 'data/util/'
# OR, from 'latch' go up to 'data' directory.
# data/scripts/us_bts/latch/
# data/scripts/us_bts/    <- one up
# data/scripts/          <- two up
# data/                  <- three up. This is the directory that *contains* 'util'
data_parent_dir = os.path.abspath(os.path.join(current_script_dir, '../../..'))

# Now, add the path to the 'data' directory to sys.path
# This makes 'data.util' (or just 'util' if it's treated as a top-level package) discoverable.
if data_parent_dir not in sys.path:
    sys.path.insert(0, data_parent_dir)  # Add to the beginning to prioritize

# --- End of Path Modification ---

# Local application/library specific imports
# Now, with 'data_parent_dir' added to sys.path, 'util' should be discoverable
# If 'util' itself is a package (i.e., has an __init__.py file directly inside it),
# the import will be `from util.download_util_script`.
# If 'util' is just a directory and download_util_script.py is treated as a module directly
# under the added path, you *might* need to adjust the import, but
# `from util.download_util_script` is the standard way if `util` also has an `__init__.py`.
# Assuming you've already added __init__.py to util/ as per previous suggestion:
from util.download_util_script import download_file as robust_download_file

FLAGS = flags.FLAGS
flags.DEFINE_string('output_dir', os.path.dirname(os.path.abspath(__file__)),
                    'Output directory to download files to.')

_GCS_URLS_CONFIG_FILE = 'gs://unresolved_mcf/us_bts/latch/latest/import_configs.json'
_GCS_OUTPUT_PATH = 'gs://unresolved_mcf/us_bts/latch/latest/gcs_output/input_files/'
_SOCRATA_PAGINATION_LIMIT = 50000


def _upload_to_gcs(file_path: str):
    """Uploads a file to the GCS output path."""
    try:
        subprocess.run(['gsutil', 'cp', file_path, _GCS_OUTPUT_PATH],
                       check=True,
                       capture_output=True,
                       text=True)
        logging.info(f"Successfully uploaded {file_path} to {_GCS_OUTPUT_PATH}")
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        logging.error(f"Failed to upload {file_path} to GCS: {e}")


def _perform_request_with_retry(url: str,
                                headers: Dict = None,
                                stream: bool = False,
                                timeout: int = 60) -> requests.Response:
    """Helper to perform a GET request with retry logic for internal functions.
    Raises requests.exceptions.RequestException on final failure."""
    tries = FLAGS.retry_tries
    delay = FLAGS.retry_delay
    backoff = FLAGS.retry_backoff

    for i in range(tries):
        try:
            response = requests.get(url,
                                    stream=stream,
                                    headers=headers,
                                    timeout=timeout)
            response.raise_for_status(
            )  # Raise HTTPError for bad responses (4xx or 5xx)
            return response
        except requests.exceptions.RequestException as e:
            logging.warning(f"Attempt {i + 1}/{tries} failed for {url}: {e}")
            if i < tries - 1:
                time.sleep(delay)
                delay *= backoff
            else:
                logging.error(
                    f"All {tries} attempts failed. Giving up on {url}.")
                raise  # Re-raise the last exception if all retries fail


def _download_and_decompress_gz(url: str, output_path: str) -> bool:
    """Downloads and decompresses a GZ file using internal retry helper."""
    # logging.info(f"Downloading and decompressing GZ from: {url}")
    try:
        response = _perform_request_with_retry(url, stream=True, timeout=60)
        # gzip.GzipFile can work directly with response.raw, which is a file-like object
        with gzip.GzipFile(fileobj=response.raw) as uncompressed:
            # Determine output file name without .gz extension
            base_name, _ = os.path.splitext(os.path.basename(output_path))
            final_output_path = os.path.join(os.path.dirname(output_path),
                                             base_name)

            with open(final_output_path, 'wb') as f:
                for chunk in uncompressed:
                    f.write(chunk)
        # logging.info(f"GZ decompressed to: {final_output_path}")
        return True
    except (requests.exceptions.RequestException, gzip.BadGzipFile) as e:
        # RequestException caught by _perform_request_with_retry and re-raised on final failure
        logging.error(
            f"Failed to decompress GZ from {url} to {output_path}: {e}")
        return False
    except Exception as e:
        logging.error(
            f"An unexpected error occurred during GZ download/decompress for {url}: {e}",
            exc_info=True)
        return False


def _download_paginated_socrata_file(
        url: str,
        output_path: str,
        pagination_limit: int = _SOCRATA_PAGINATION_LIMIT) -> bool:
    """Downloads a file with Socrata API pagination logic using internal retry helper."""
    # logging.info(f"Downloading paginated Socrata data from: {url}")
    offset = 0
    is_header_written = False

    try:
        # Clear the file before starting
        with open(output_path, 'w', encoding='utf-8') as f:
            pass
    except IOError as e:
        logging.error(f"Could not open/clear output file {output_path}: {e}")
        return False

    try:
        while True:
            separator = '&' if '?' in url else '?'
            paginated_url = f"{url}{separator}$limit={pagination_limit}&$offset={offset}"
            response = _perform_request_with_retry(paginated_url,
                                                   stream=True,
                                                   timeout=120)

            if response.content.strip() == b'[]':
                # logging.info(f"No more data from Socrata API for {url}, pagination complete.")
                break

            lines = response.content.splitlines(
                True)  # Keep line endings for 'ab' mode

            with open(output_path, 'ab') as f:  # Open in append binary mode
                if not is_header_written:
                    f.writelines(lines)
                    is_header_written = True
                else:
                    f.writelines(
                        lines[1:])  # Skip header on subsequent requests

            num_lines_received = len(lines)
            if is_header_written and offset > 0:  # If it's a subsequent page, subtract header
                num_lines_received -= 1

            if num_lines_received < pagination_limit:
                # logging.info(f"Less than limit ({pagination_limit}) lines received ({num_lines_received}), pagination complete for {url}.")
                break

            offset += pagination_limit
            # logging.info(f"Downloaded {num_lines_received} lines from {url}. Next offset: {offset}")

        # logging.info(f"Paginated download for {url} finished.")
        return True
    except requests.exceptions.RequestException as e:  # Catch exceptions re-raised by _perform_request_with_retry
        logging.error(
            f"Failed during Socrata pagination for {url} after retries: {e}")
        return False
    except Exception as e:
        logging.error(
            f"An unexpected error occurred during Socrata pagination for {url}: {e}",
            exc_info=True)
        return False


def create_download_configs() -> List[Dict]:
    """Reads the URL config JSON from GCS and generates the download configurations."""
    try:
        result = subprocess.run(['gsutil', 'cat', _GCS_URLS_CONFIG_FILE],
                                capture_output=True,
                                text=True,
                                check=True,
                                encoding='UTF-8')
        urls_config = json.loads(result.stdout)
        logging.info(
            f"Successfully loaded download configurations from {_GCS_URLS_CONFIG_FILE}"
        )
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        logging.error(
            f"Failed to read GCS config file '{_GCS_URLS_CONFIG_FILE}': {e}. Ensure 'gsutil' is in your PATH and the file exists."
        )
        return []
    except json.JSONDecodeError as e:
        logging.error(
            f"Failed to parse JSON from GCS config file '{_GCS_URLS_CONFIG_FILE}': {e}"
        )
        return []
    except Exception as e:
        logging.error(
            f"An unexpected error occurred while creating download configs: {e}"
        )
        return []

    return [
        file for item in urls_config for file in item.get('files', [])
        if file.get('url') and file.get('input_file_name')
    ]


def download_all_files_from_config(download_dir: str) -> None:
    """
    Downloads files into the specified directory based on configurations,
    dispatching to appropriate download functions.
    """
    os.makedirs(download_dir, exist_ok=True)
    # logging.info(f"Ensured output directory exists: {download_dir}")

    download_configs = create_download_configs()

    if not download_configs:
        logging.warning(
            "No download configurations found. Exiting download process.")
        return

    for config in download_configs:
        url = config.get('url')
        # file_name from config will be used to determine the output_path for
        # internal GZ and Socrata functions.
        # For robust_download_file, it will derive the name from the URL directly
        # as the original download_util_script.py does not take a file_name parameter.
        file_name = config.get('input_file_name')

        if not url or not file_name:
            logging.error(f"Skipping malformed config entry: {config}")
            continue

        output_path = os.path.join(download_dir, file_name)
        # logging.info(f"Processing URL: {url} (expected output: {output_path})")

        success = False
        try:
            file_name_lower = file_name.lower()
            parsed_url = urlparse(url)

            if file_name_lower.endswith('.gz'):
                success = _download_and_decompress_gz(url=url,
                                                      output_path=output_path)
            elif file_name_lower.endswith('.zip'):
                # robust_download_file from util already handles unzipping if unzip=True and it's a .zip file.
                # It determines the output file path internally based on output_folder and URL's base name.
                # The 'file_name' from config is NOT passed here as per 'no modification to download_util_script.py' constraint.
                success = robust_download_file(
                    url=url,
                    output_folder=download_dir,
                    unzip=True,  # Instruct util to unzip
                )
            # Heuristic for Socrata API pagination: check if URL contains $limit or $offset,
            # or if it's a common Socrata resource path (e.g., /resource/ABCD-EFGH.json)
            # This heuristic might need adjustment based on specific URL patterns.
            elif '$limit=' in url or '$offset=' in url or '/resource/' in parsed_url.path or not '.' in os.path.basename(
                    parsed_url.path):
                success = _download_paginated_socrata_file(
                    url=url, output_path=output_path)
            else:
                # For all other direct file downloads, use the robust utility.
                # The 'file_name' from config is NOT passed here as per 'no modification to download_util_script.py' constraint.
                success = robust_download_file(
                    url=url,
                    output_folder=download_dir,
                    unzip=False,
                )

            if success:
                _upload_to_gcs(output_path)
                # logging.info(f"Successfully processed {url}")
            else:
                logging.error(
                    f"Failed to process {url} after all retries or due to an error."
                )

        except Exception as e:
            logging.error(
                f"An unhandled error occurred while processing {url}: {e}",
                exc_info=True)


def main(_) -> None:
    """Entry point for the script."""
    logging.set_verbosity(logging.INFO)
    # logging.info("Starting consolidated file download script...")

    if not FLAGS.output_dir:
        logging.fatal("--output_dir is required. Exiting.")
        sys.exit(1)

    download_all_files_from_config(FLAGS.output_dir)
    logging.info("Download script completed.")


if __name__ == '__main__':
    app.run(main)

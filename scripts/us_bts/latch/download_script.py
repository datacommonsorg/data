# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""This script downloads files from a JSON configuration,
handling various file types including paginated API data and compressed archives,
leveraging a separate utility for general downloads."""

import gzip
import json
import os
import subprocess
import sys
from typing import List, Dict
from urllib.parse import urlparse
from absl import app, flags, logging

logging.set_verbosity(logging.INFO)

_SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(_SCRIPT_PATH, '../../../util/'))
_GCS_OUTPUT_DIR = os.path.join(_SCRIPT_PATH, 'gcs_output')

from download_util_script import _retry_method, download_file

FLAGS = flags.FLAGS
flags.DEFINE_string('output_dir', os.path.join(_GCS_OUTPUT_DIR, "input_files"),
                    'Output directory to download files to.')
_GCS_URLS_CONFIG_FILE = 'gs://unresolved_mcf/us_bts/latch/latest/import_configs.json'
_SOCRATA_PAGINATION_LIMIT = 50000


def _download_and_decompress_gz(url: str, output_path: str) -> bool:
    """Downloads and decompresses a GZ file using internal retry helper."""
    try:
        print(url)
        response = _retry_method(url, None, 3, 5, 2)

        with gzip.GzipFile(fileobj=response.raw) as uncompressed:
            # Determine output file name without .gz extension
            base_name, _ = os.path.splitext(os.path.basename(output_path))
            final_output_path = os.path.join(os.path.dirname(output_path),
                                             base_name)

            with open(final_output_path, 'wb') as f:
                for chunk in uncompressed:
                    f.write(chunk)
        return True

    except Exception as e:
        logging.fatal(
            f"An unexpected error occurred during GZ download/decompress for {url}: {e}",
            exc_info=True)
        return False


def _download_paginated_socrata_file(
        url: str,
        output_path: str,
        pagination_limit: int = _SOCRATA_PAGINATION_LIMIT) -> bool:
    """Downloads a file with Socrata API pagination logic using internal retry helper."""

    offset = 0
    is_header_written = False

    try:
        # Clear the file before starting
        with open(output_path, 'w', encoding='utf-8') as f:
            pass
    except IOError as e:
        logging.fatal(f"Could not open/clear output file {output_path}: {e}")
        return False

    try:
        while True:
            separator = '&' if '?' in url else '?'
            paginated_url = f"{url}{separator}$limit={pagination_limit}&$offset={offset}"
            response = _retry_method(paginated_url, None, 3, 5, 2)

            if response.content.strip() == b'[]':
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

    except Exception as e:
        logging.fatal(
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
        logging.fatal(
            f"Failed to read GCS config file '{_GCS_URLS_CONFIG_FILE}': {e}. Ensure 'gsutil' is in your PATH and the file exists."
        )
        return []
    except json.JSONDecodeError as e:
        logging.fatal(
            f"Failed to parse JSON from GCS config file '{_GCS_URLS_CONFIG_FILE}': {e}"
        )
        return []
    except Exception as e:
        logging.fatal(
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
    # UNCOMMENTED: Ensure the output directory exists before attempting to write files.
    os.makedirs(download_dir, exist_ok=True)
    # logging.info(f"Ensured output directory exists: {download_dir}")

    download_configs = create_download_configs()

    if not download_configs:
        logging.warning(
            "No download configurations found. Exiting download process.")
        return

    for config in download_configs:
        url = config.get('url')
        file_name = config.get('input_file_name')
        if not url or not file_name:
            logging.fatal(f"Skipping malformed config entry: {config}")
            continue

        output_path = os.path.join(download_dir, file_name)
        # logging.info(f"Processing URL: {url} (expected output: {output_path})")

        success = False
        try:
            file_name_lower = file_name.lower()
            parsed_url = urlparse(url)

            if file_name_lower.endswith('.gz'):
                success = _download_and_decompress_gz(url=parsed_url,
                                                      output_path=output_path)

            elif file_name_lower.endswith('.zip'):
                success = download_file(
                    url,
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
                success = download_file(
                    url=url,
                    output_folder=download_dir,
                    unzip=False,
                )

        except Exception as e:
            logging.fatal(
                f"An unhandled error occurred while processing {url}: {e}",
                exc_info=True)


def main(_) -> None:
    """Entry point for the script."""

    if not FLAGS.output_dir:
        logging.fatal("--output_dir is required. Exiting.")
        sys.exit(1)

    download_all_files_from_config(FLAGS.output_dir)
    logging.info("Download script completed.")


if __name__ == '__main__':
    app.run(main)

# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import errno
import os
import sys
import shutil
import time
import requests
from typing import Optional
from absl import logging
from absl import app

script_dir = os.path.dirname(os.path.abspath(__file__))
data_dir = os.path.dirname(os.path.dirname(os.path.dirname(script_dir)))
if data_dir not in sys.path:
    sys.path.insert(0, data_dir)

from util.download_util_script import download_file
from absl import flags

flags.DEFINE_string('api_url',
                    'https://www.fema.gov/api/open/v2/FimaNfipClaims',
                    'The base URL of the API endpoint to download data from.')
flags.DEFINE_string(
    'bulk_url',
    'https://www.fema.gov/about/reports-and-data/openfema/FimaNfipClaims.csv',
    'The direct bulk download URL for the full dataset.')
flags.DEFINE_string('temp_dir', os.path.join(script_dir, 'temp_fema_data'),
                    'The temporary directory to store downloaded chunks.')
flags.DEFINE_string(
    'output_dir', os.path.join(script_dir, 'input_file'),
    'The output directory to store the downloaded claims data.')
_FLAGS = flags.FLAGS

# Define the page size for each API request.
PAGE_SIZE = 1000


def _is_valid_bulk_file(filepath: str,
                        min_size: int = 10 * 1024 * 1024,
                        required_header: str = 'dateOfLoss',
                        expected_records: Optional[int] = None,
                        tolerance_ratio: float = 0.98) -> bool:
    """Validates that a bulk downloaded file meets size, header, and record count requirements."""
    if not os.path.exists(filepath):
        return False
    size = os.path.getsize(filepath)
    if size < min_size:
        logging.warning(
            "Bulk file size (%s bytes) is below minimum threshold (%s bytes).",
            size, min_size)
        return False
    try:
        with open(filepath, 'rb') as f:
            first_line = f.readline().decode('utf-8', errors='ignore')
            if required_header not in first_line:
                logging.warning(
                    "Bulk file missing required header '%s'. First line: %s",
                    required_header, first_line[:200])
                return False
            if expected_records is not None and expected_records > 0:
                row_count = sum(1 for line in f if line.strip())
                # OpenFEMA bulk export CSV is updated periodically while the live API
                # counter increments in real time. Allow a small tolerance (default 2%)
                # to prevent minor lag from triggering an expensive pagination fallback.
                min_expected = expected_records * tolerance_ratio
                if row_count < min_expected:
                    logging.warning(
                        "Bulk file record count (%s) is below tolerance threshold (%s, expected: ~%s). Truncated download.",
                        row_count, int(min_expected), expected_records)
                    return False
    except Exception as e:
        logging.warning("Error inspecting bulk file header: %s", e)
        return False
    return True


def _publish_file_atomically(source_path: str, destination_path: str) -> None:
    """Atomically replaces destination_path with source_path, handling cross-device links."""
    try:
        os.replace(source_path, destination_path)
    except OSError as e:
        if e.errno == errno.EXDEV:
            temp_dest = f"{destination_path}.tmp.{os.getpid()}"
            shutil.copy2(source_path, temp_dest)
            os.replace(temp_dest, destination_path)
            if os.path.exists(source_path):
                os.remove(source_path)
        else:
            raise


def get_total_records(api_url):
    """
    Makes a preliminary API call to get the total number of records.

    This is necessary because the main download utility and pagination logic
    are not guaranteed to be robust for all API behaviors (e.g., an empty
    final page).

    Args:
        api_url (str): The base URL of the API endpoint.

    Returns:
        int: The total number of records, or None if the request fails.
    """
    count_url = f"{api_url}?$count=true"
    logging.info("Getting total record count from: %s", count_url)
    try:
        # Use requests for this simple JSON query, as the download_file
        # utility is for large file downloads and may not be suitable.
        response = requests.get(count_url, timeout=30)
        response.raise_for_status()
        data = response.json()
        total_count = int(data.get('metadata', {}).get('count'))
        if total_count <= 0:
            logging.error("API returned non-positive total record count: %s",
                          total_count)
            raise RuntimeError(
                f"Invalid total record count from API: {total_count}")
        logging.info("Found a total of %s records.", total_count)
        return total_count
    except requests.exceptions.RequestException as e:
        logging.error("Failed to get total record count: %s", e)
        raise RuntimeError('Failed to get total record count.')
    except (ValueError, KeyError, TypeError) as e:
        logging.error(
            "Failed to parse the total record count from the response: %s", e)
        raise RuntimeError(
            'Failed to parse the total record count from the response.')


def download_data(api_url: str,
                  temp_dir: str,
                  bulk_url: str = None,
                  output_dir: str = None,
                  min_bulk_size: int = 10 * 1024 * 1024):
    """
    Downloads data from the FEMA API, handling pagination and file merging.

    Args:
        api_url (str): The base URL of the API endpoint.
        temp_dir (str): The path to the temporary directory for downloaded chunks.
        bulk_url (str): The direct bulk CSV download URL.
        output_dir (str): The output directory for the final dataset.
        min_bulk_size (int): Minimum byte threshold for bulk CSV validation.
    """
    if output_dir is None:
        output_dir = os.path.join(script_dir, "input_file")
    if not os.path.isabs(output_dir):
        output_dir = os.path.join(script_dir, output_dir)
    if not os.path.isabs(temp_dir):
        temp_dir = os.path.join(script_dir, temp_dir)

    os.makedirs(output_dir, exist_ok=True)
    final_filepath = os.path.join(output_dir, "fema_nfip_claims.csv")

    logging.set_verbosity(logging.INFO)

    total_records = None

    # 1. Try direct bulk download first (~8 seconds vs ~2.5 hours for pagination)
    if bulk_url:
        logging.info("Attempting direct bulk download from: %s", bulk_url)
        try:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
            os.makedirs(temp_dir, exist_ok=True)

            if download_file(url=bulk_url, output_folder=temp_dir,
                             unzip=False):
                downloaded = [
                    os.path.join(temp_dir, f) for f in os.listdir(temp_dir)
                    if os.path.isfile(os.path.join(temp_dir, f))
                ]
                if downloaded:
                    try:
                        total_records = get_total_records(api_url)
                    except Exception as e:
                        logging.warning(
                            "Could not retrieve total records for bulk validation: %s. "
                            "Cannot verify bulk file integrity; falling back to pagination.",
                            e)
                        total_records = None

                    if (total_records is not None and total_records > 0
                            and _is_valid_bulk_file(
                                downloaded[0],
                                min_bulk_size,
                                expected_records=total_records)):
                        _publish_file_atomically(downloaded[0], final_filepath)
                        logging.info(
                            "Direct bulk download complete. Saved to: %s",
                            final_filepath)
                        return
                    else:
                        logging.warning(
                            "Bulk file failed integrity or record count verification. "
                            "Falling back to API pagination.")
        except Exception as e:
            logging.warning(
                "Direct bulk download failed: %s. Falling back to API pagination.",
                e)
        finally:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)

    # 2. Fallback to API pagination
    # Define the page size for each API request.
    skip_count = 0
    records_downloaded = 0

    # Get the total number of records from the API for a reliable failsafe if not already retrieved.
    if total_records is None:
        total_records = get_total_records(api_url)
    if total_records is None or total_records <= 0:
        logging.error(
            "Could not get valid total record count (> 0). Cannot proceed.")
        raise RuntimeError(
            'Download failed due to could not get the total record count.')

    session = requests.Session()
    adapter = requests.adapters.HTTPAdapter(pool_connections=10,
                                            pool_maxsize=10)
    session.mount('https://', adapter)
    session.mount('http://', adapter)

    try:
        # Create a temporary directory for downloaded chunks.
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
        os.makedirs(temp_dir, exist_ok=True)

        staging_filepath = os.path.join(temp_dir,
                                        "staging_fema_nfip_claims.csv")
        logging.info("Starting download to file: %s (staging: %s)",
                     final_filepath, staging_filepath)

        # The main download loop for pagination
        while True:
            csv_url = f"{api_url}?$format=csv&$skip={skip_count}&$top={PAGE_SIZE}"
            logging.info("Requesting data from: %s", csv_url)

            # The download utility incorrectly appends an .xlsx extension.
            util_output_filename = "FimaNfipClaims.xlsx"
            util_output_path = os.path.join(temp_dir, util_output_filename)

            chunk_filename = f"FimaNfipClaims_{skip_count}.csv"
            chunk_filepath = os.path.join(temp_dir, chunk_filename)

            download_success = download_file(url=csv_url,
                                             output_folder=temp_dir,
                                             unzip=False,
                                             tries=10,
                                             delay=10,
                                             backoff=2,
                                             session=session)

            if not download_success or not os.path.exists(util_output_path):
                logging.error(
                    "Failed to download chunk or file not found. Exiting.")
                raise RuntimeError(
                    f"Failed to download chunk at skip={skip_count}.")

            os.rename(util_output_path, chunk_filepath)

            # The file is a plain text CSV, but we read it in binary mode ('rb')
            # to handle potential issues with different line endings (e.g., '\r\n')
            # and ensure the bytes are written exactly as they were read.
            with open(chunk_filepath, 'rb') as f_chunk:
                content = f_chunk.read()

            with open(staging_filepath, 'ab') as f_staging:
                if skip_count == 0:
                    f_staging.write(
                        content if content.endswith(b'\n') else content +
                        b'\n')
                else:
                    split_content = content.split(b'\n', 1)
                    if len(split_content) > 1 and split_content[1].strip():
                        content_without_header = split_content[1]
                        f_staging.write(
                            content_without_header if content_without_header.
                            endswith(b'\n') else content_without_header +
                            b'\n')

            if os.path.exists(chunk_filepath):
                os.remove(chunk_filepath)

            cleaned_content = content.rstrip(b'\r\n')
            num_records_in_chunk = max(0,
                                       len(cleaned_content.split(b'\n')) -
                                       1) if cleaned_content else 0
            records_downloaded += num_records_in_chunk

            logging.info("Downloaded %s of %s records.", records_downloaded,
                         total_records)

            if num_records_in_chunk < PAGE_SIZE:
                logging.info(
                    "Reached the end of the dataset. All records have been downloaded."
                )
                break

            skip_count += PAGE_SIZE

        if total_records > 0 and records_downloaded < total_records:
            logging.error(
                "Expected %s records, but only downloaded %s. Download incomplete.",
                total_records, records_downloaded)
            raise RuntimeError(
                f"Expected {total_records} records, but only downloaded {records_downloaded}"
            )

        if records_downloaded <= 0:
            logging.error("No records were downloaded. Cannot proceed.")
            raise RuntimeError("Download failed: 0 records downloaded.")

        _publish_file_atomically(staging_filepath, final_filepath)

        logging.info(
            "Total download complete. All available records saved to: %s",
            final_filepath)

    except IOError as e:
        logging.error("An error occurred while writing the file: %s", e)
        raise
    finally:
        session.close()
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)


def main(argv):
    """
    The main function that handles the data download process.

    Args:
        argv: List of command line arguments, as provided by absl.
    """
    try:
        download_data(_FLAGS.api_url, _FLAGS.temp_dir, _FLAGS.bulk_url,
                      _FLAGS.output_dir)
    except Exception as e:
        logging.fatal("Download process failed: %s", e)


if __name__ == "__main__":
    app.run(main)

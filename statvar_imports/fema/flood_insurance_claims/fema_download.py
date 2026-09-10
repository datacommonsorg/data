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

import os
import shutil
import sys

from absl import app
from absl import flags
from absl import logging
import requests

script_dir = os.path.dirname(os.path.abspath(__file__))
data_dir = os.path.dirname(os.path.dirname(os.path.dirname(script_dir)))
if data_dir not in sys.path:
    sys.path.insert(0, data_dir)

from util.download_util_script import download_file

flags.DEFINE_string('api_url',
                    'https://www.fema.gov/api/open/v2/FimaNfipClaims',
                    'The base URL of the API endpoint to download data from.')
flags.DEFINE_string(
    'bulk_url',
    'https://www.fema.gov/about/reports-and-data/openfema/FimaNfipClaims.csv',
    'The direct bulk download URL for the full dataset.')
flags.DEFINE_string('temp_dir', 'temp_fema_data',
                    'The temporary directory to store downloaded chunks.')
flags.DEFINE_string('output_dir', None,
                    'The directory to store output files.')
_FLAGS = flags.FLAGS

# Define the page size for each API request.
PAGE_SIZE = 10000


def get_total_records(api_url):
    """
    Makes a preliminary API call to get the total number of records.

    This is necessary because the main download utility and pagination logic
    are not guaranteed to be robust for all API behaviors (e.g., an empty
    final page).

    Args:
        api_url (str): The base URL of the API endpoint.

    Returns:
        int: The total number of records.

    Raises:
        RuntimeError: If the request fails or the response cannot be parsed.
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
                  output_dir: str = None):
    """
    Downloads data from the FEMA API, handling direct bulk download and pagination fallback.

    Args:
        api_url (str): The base URL of the API endpoint.
        temp_dir (str): The path to the temporary directory for downloaded chunks.
        bulk_url (str): The direct bulk download URL for the full dataset.
        output_dir (str): Optional directory for output file. Defaults to
            'input_file' relative to script.
    """
    filename = "fema_nfip_claims.csv"

    if output_dir is None:
        output_dir = os.path.join(script_dir, "input_file")
    elif not os.path.isabs(output_dir):
        output_dir = os.path.abspath(output_dir)

    if not os.path.isabs(temp_dir):
        temp_dir = os.path.join(os.path.dirname(output_dir), temp_dir)

    os.makedirs(output_dir, exist_ok=True)
    final_filepath = os.path.join(output_dir, filename)

    logging.set_verbosity(logging.INFO)

    # 1. Attempt direct bulk download first for speed and reliability
    if bulk_url:
        logging.info("Attempting direct bulk download from: %s", bulk_url)
        try:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
            os.makedirs(temp_dir, exist_ok=True)

            download_success = download_file(url=bulk_url,
                                             output_folder=temp_dir,
                                             unzip=False,
                                             tries=5,
                                             delay=5,
                                             backoff=2)
            if not download_success:
                raise RuntimeError("download_file returned False")
            downloaded_files = [
                os.path.join(temp_dir, f) for f in os.listdir(temp_dir)
                if os.path.isfile(os.path.join(temp_dir, f))
            ]
            if not downloaded_files or os.path.getsize(
                    downloaded_files[0]) == 0:
                raise RuntimeError("Bulk download file is missing or empty.")
            src_file = downloaded_files[0]

            # Validate that the bulk download file is a valid CSV and not an
            # HTML error/maintenance page.
            with open(src_file, 'r', encoding='utf-8', errors='replace') as f:
                first_line = f.readline().strip()

            lower_first_line = first_line.lower()
            if lower_first_line.startswith(('<html', '<!doctype')):
                raise RuntimeError(
                    "Bulk download file appears to be an HTML page, not a CSV.")
            if 'policycount' not in lower_first_line and 'dateofloss' not in lower_first_line:
                raise RuntimeError(
                    "Bulk download file is missing expected CSV header columns.")

            if os.path.exists(final_filepath):
                os.remove(final_filepath)
            shutil.move(src_file, final_filepath)
            logging.info("Direct bulk download complete. Saved to: %s",
                         final_filepath)
            return
        except Exception as e:
            logging.warning(
                "Direct bulk download failed (%s). Falling back to API pagination.",
                e)
        finally:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)

    # 2. Fallback to API pagination
    # Get the total number of records from the API for a reliable failsafe.
    total_records = get_total_records(api_url)
    if total_records == 0:
        logging.error(
            "Total records returned 0 from API metadata. Cannot proceed.")
        raise RuntimeError('Download failed: API metadata reported 0 records.')

    skip_count = 0
    records_downloaded = 0
    temp_merged_filepath = os.path.join(temp_dir, f"merged_{filename}")

    try:
        # Create a temporary directory for downloaded chunks.
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
        os.makedirs(temp_dir, exist_ok=True)

        logging.info("Starting paginated download into temporary staging: %s",
                     temp_merged_filepath)

        # The main download loop for pagination
        while records_downloaded < total_records:
            csv_url = f"{api_url}?$format=csv&$top={PAGE_SIZE}&$skip={skip_count}"
            logging.info("Requesting data from: %s", csv_url)

            # Clean up any leftover chunk files before downloading the next chunk.
            merged_filename = os.path.basename(temp_merged_filepath)
            for f in os.listdir(temp_dir):
                if f != merged_filename:
                    file_to_remove = os.path.join(temp_dir, f)
                    if os.path.isfile(file_to_remove):
                        os.remove(file_to_remove)

            download_success = download_file(url=csv_url,
                                             output_folder=temp_dir,
                                             unzip=False,
                                             tries=10,
                                             delay=10,
                                             backoff=2)

            chunk_files = [
                os.path.join(temp_dir, f)
                for f in os.listdir(temp_dir)
                if f != merged_filename and os.path.isfile(os.path.join(temp_dir, f))
            ]

            if not download_success or not chunk_files:
                logging.error(
                    "Failed to download chunk at skip=%s or file not found. Exiting.",
                    skip_count)
                raise RuntimeError(
                    f"Failed to download chunk at skip={skip_count}.")

            chunk_filepath = chunk_files[0]

            # Read in binary mode to handle byte-accurate line endings.
            with open(chunk_filepath, 'rb') as f_chunk:
                content = f_chunk.read()

            os.remove(chunk_filepath)

            with open(temp_merged_filepath, 'ab') as f_temp:
                if skip_count == 0:
                    f_temp.write(content)
                    if not content.endswith(b'\n'):
                        f_temp.write(b'\n')
                else:
                    split_content = content.split(b'\n', 1)
                    if len(split_content) > 1:
                        content_without_header = split_content[1]
                        if content_without_header:
                            f_temp.write(content_without_header)
                            if not content_without_header.endswith(b'\n'):
                                f_temp.write(b'\n')

            lines = content.strip(b'\r\n').split(b'\n')
            num_records_in_chunk = max(0,
                                       len(lines) -
                                       1) if lines and lines[0] else 0
            records_downloaded += num_records_in_chunk

            logging.info("Downloaded %s of %s records.", records_downloaded,
                         total_records)

            if num_records_in_chunk == 0:
                logging.warning(
                    "Received empty chunk at skip=%s before reaching "
                    "total_records (%s). Exiting loop.", skip_count,
                    total_records)
                break

            if num_records_in_chunk < PAGE_SIZE:
                logging.info(
                    "Reached the end of the dataset. All records have been downloaded."
                )
                break

            skip_count += PAGE_SIZE

        if records_downloaded < total_records:
            logging.error(
                "Download incomplete: only %s of %s records downloaded.",
                records_downloaded, total_records)
            raise RuntimeError(
                f"Download incomplete: only {records_downloaded} of "
                f"{total_records} records downloaded."
            )

        # Atomically replace final file only on full completion
        if os.path.exists(final_filepath):
            os.remove(final_filepath)
        shutil.move(temp_merged_filepath, final_filepath)

        logging.info(
            "Total download complete. All %s available records saved to: %s",
            records_downloaded, final_filepath)

    except IOError as e:
        logging.error("An error occurred while writing the file: %s", e)
        raise
    finally:
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)


def main(argv):
    """
    The main function that handles the data download process.

    Args:
        argv: List of command line arguments, as provided by absl.
    """
    download_data(_FLAGS.api_url, _FLAGS.temp_dir, _FLAGS.bulk_url,
                  _FLAGS.output_dir)


if __name__ == "__main__":
    app.run(main)

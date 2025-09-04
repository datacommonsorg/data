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
import sys
import shutil
import time
import requests
from absl import logging

script_dir = os.path.dirname(os.path.abspath(__file__))
data_dir = os.path.dirname(os.path.dirname(script_dir))
if data_dir not in sys.path:
    sys.path.insert(0, data_dir)

from util.download_util_script import download_file

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
        logging.info("Found a total of %s records.", total_count)
        return total_count
    except requests.exceptions.RequestException as e:
        logging.error("Failed to get total record count: %s", e)
        return None
    except (ValueError, KeyError, TypeError) as e:
        logging.error("Failed to parse the total record count from the response: %s", e)
        return None

def download_fema_csv(api_url, filename="fema_nfip_claims.csv"):
    """
    Downloads a complete CSV file from the FEMA API by handling pagination.

    This function uses a provided utility to download paginated chunks
    and merges them into a single file.

    Args:
        api_url (str): The base URL of the API endpoint.
        filename (str): The name of the final merged file.
    """
    logging.set_verbosity(logging.INFO)

    # Define the page size for each API request.
    PAGE_SIZE = 1000
    skip_count = 0
    records_downloaded = 0
    temp_dir = "temp_fema_data"
    final_filepath = filename
    
    # Get the total number of records from the API for a reliable failsafe.
    total_records = get_total_records(api_url)
    if total_records is None:
        logging.fatal("Could not get the total record count. Cannot proceed.")
        return

    try:
        # Create a temporary directory for downloaded chunks.
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
        os.makedirs(temp_dir)
        
        logging.info("Starting download to file: %s", final_filepath)

        # The main download loop for pagination
        while records_downloaded < total_records:
            csv_url = f"{api_url}?$format=csv&$skip={skip_count}"
            logging.info("Requesting data from: %s", csv_url)
            
           
            util_output_filename = "FimaNfipClaims.xlsx"
            util_output_path = os.path.join(temp_dir, util_output_filename)

            # Then, define the unique filename our script will use for processing.
            chunk_filename = f"FimaNfipClaims_{skip_count}.xlsx"
            chunk_filepath = os.path.join(temp_dir, chunk_filename)
          
            download_success = download_file(
                url=csv_url,
                output_folder=temp_dir,
                unzip=False,
                tries=3,
                delay=5,
                backoff=2
            )
            
            # Check for download success and if the utility's output file exists.
            if not download_success or not os.path.exists(util_output_path):
                logging.error("Failed to download chunk or file not found. Exiting.")
                break

            # Rename the downloaded file to a unique name so the utility
            # downloads a fresh copy on the next iteration.
            os.rename(util_output_path, chunk_filepath)
            
            # Read the downloaded chunk from its new unique path.
            with open(chunk_filepath, 'rb') as f_chunk:
                content = f_chunk.read()

            # Append content to the final file, handling the header.
            with open(final_filepath, 'ab') as f_final:
                if skip_count == 0:
                    # For the first chunk, write the entire content (including header).
                    f_final.write(content)
                else:
                    # For subsequent chunks, strip the header before writing.
                    content_without_header = content.split(b'\n', 1)[1]
                    f_final.write(content_without_header)

            # Check how many records were in the chunk
            num_records_in_chunk = len(content.split(b'\n')) - 1
            records_downloaded += num_records_in_chunk

            logging.info("Downloaded %s of %s records.", records_downloaded, total_records)
            
            # If the number of records is less than the page size, it's the last page.
            if num_records_in_chunk < PAGE_SIZE:
                logging.info("Reached the end of the dataset. All records have been downloaded.")
                break
            
            # Increment the skip counter for the next request.
            skip_count += PAGE_SIZE

        logging.info("Total download complete. All available records saved to: %s", final_filepath)

    except IOError as e:
        logging.error("An error occurred while writing the file: %s", e)
    finally:
        # Clean up the temporary directory.
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)

if __name__ == "__main__":
    api_url = "https://www.fema.gov/api/open/v2/FimaNfipClaims"
    download_fema_csv(api_url)


# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the 'License');
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#         https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an 'AS IS' BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# How to run the script to download the files:
# python3 download_util_script.py --url="<url>" --unzip=<True if files have to be unzipped.>

import os
import sys
from absl import app
from absl import flags
from absl import logging
import requests
from retry import retry
from urllib.parse import urlparse
import zipfile

MODULE_DIR = os.path.dirname(os.path.dirname(__file__))
DATA_DIR = os.path.join(MODULE_DIR, '..')

sys.path.append(MODULE_DIR)
sys.path.append(os.path.join(DATA_DIR, 'data/util'))

FLAGS = flags.FLAGS
flags.DEFINE_string('url', None, 'URL of the file to download')
# --- CHANGE THIS LINE ---
flags.DEFINE_string('output_folder', None, # Changed default from 'input_folder' to None
                    'Folder to save the downloaded file')
# --- END CHANGE ---
flags.DEFINE_bool('unzip', False,
                  'Unzip the downloaded file if it is a zip file')

flags.DEFINE_integer('retry_tries', 3, 'Number of times to retry a download.')
flags.DEFINE_integer('retry_delay', 5, 'Initial delay in seconds between retries.')
flags.DEFINE_integer('retry_backoff', 2,
                     'Backoff factor for retry delay (e.g., 2 means delay doubles each time).')


def _retry_method(url: str, headers: dict, tries: int, delay: int, backoff: int) -> requests.Response:
    """
    Attempts to make a GET request to a URL with retries.

    Args:
        url: The URL to request.
        headers: Optional dictionary of HTTP headers to send with the request.
        tries: Number of times to retry.
        delay: Initial delay between retries.
        backoff: Backoff factor for retry delay.

    Returns:
        A requests.Response object if the request is successful.

    Raises:
        requests.exceptions.RequestException: If the request fails after all retries.
    """

    @retry(tries=tries, delay=delay, backoff=backoff,
           exceptions=(requests.exceptions.ConnectionError,
                       requests.exceptions.Timeout,
                       requests.exceptions.HTTPError))
    def retry_download(url: str, headers: dict) -> requests.Response:
        logging.info("Attempting to download from: %s", url)
        # Using stream=True for potentially large files and adding a timeout
        response = requests.get(url, headers=headers, stream=True, timeout=30)
        response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
        return response

    return retry_download(url, headers)


def unzip_file(file_path: str, output_folder: str) -> None:
    """
    Unzips a zip file to the specified output_folder.

    Args:
        file_path: The path to the zip file.
        output_folder: The folder where the contents will be extracted.
    """
    try:
        with zipfile.ZipFile(file_path, 'r') as zip_ref:
            zip_ref.extractall(output_folder)
        logging.info(f"File unzipped to: {output_folder}")
        os.remove(file_path)  # Remove the zip file after successful extraction
    except zipfile.BadZipFile as e:
        logging.error(f"Error unzipping file '{file_path}': Not a valid zip file or corrupted. Error: {e}")
        raise ValueError(f"Invalid Zip File: {file_path}") from e
    except OSError as e:
        logging.error(f"OS error during unzipping file '{file_path}': {e}")
        raise
    except Exception as e:
        logging.error(f"An unexpected error occurred while unzipping file '{file_path}': {e}")
        raise


def download_file(url: str, output_folder: str, unzip: bool, headers: dict = None, tries: int = 3,
                  delay: int = 5, backoff: int = 2) -> bool:
    """
    Downloads file from the URL and saves it to a specified folder.
    The function returns True on success, False on failure.

    Args:
        url: URL of the file to download.
        output_folder: The local folder to save the downloaded files.
        unzip: If True, attempts to unzip the downloaded file if it's a zip file.
        headers: Optional dictionary of HTTP headers to send with the request.
        tries: Number of retry attempts.
        delay: Initial delay for retries.
        backoff: Backoff factor for retries.

    Returns:
        bool: True if the download (and optional unzip) was successful, False otherwise.
    """
    logging.info(f"Attempting to download from: {url}")
    file_path = None  # Initialize file_path for cleanup in except block

    try:
        # --- URL scheme validation: Crucial for handling MissingSchema error ---
        parsed_url = urlparse(url)
        if not parsed_url.scheme or not parsed_url.netloc:
            logging.error(f"Invalid URL format or missing scheme for '{url}'. "
                          "Please ensure URL starts with 'http://' or 'https://'.")
            return False # Return False for invalid URL
        # --- End URL scheme validation ---

        file_name = os.path.basename(parsed_url.path)
        if not file_name:
            logging.warning(f"Unable to infer filename from URL '{url}'. Using a default name.")
            file_name = "downloaded_file"

        # Logic to append .xlsx if no extension is found and it's not a zip
        if '.' not in file_name and not unzip:
            file_name = file_name + '.xlsx'
            logging.info(f"Appended '.xlsx' extension. Final inferred filename: {file_name}")

        file_path = os.path.join(output_folder, file_name)

        # Ensure output folder exists
        os.makedirs(output_folder, exist_ok=True)
        logging.info(f"Output folder '{output_folder}' ensured to exist.")

        # If file already exists, skip download
        if os.path.exists(file_path):
            logging.info(f"File already exists at {file_path}. Skipping download.")
            if unzip and file_name.endswith('.zip'):
                try:
                    unzip_file(file_path, output_folder)
                    logging.info("Existing zip file successfully unzipped.")
                except Exception as e:
                    logging.error(f"Failed to unzip existing file {file_path}: {e}")
                    return False
            return True # Explicit return True on existing file skip (or successful unzip)

        response = _retry_method(url, headers, tries, delay, backoff)

        # Stream content to file to handle potentially large files
        with open(file_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):  # 8KB chunks
                f.write(chunk)

        logging.info(f"File successfully downloaded to: {file_path}")

        if unzip and file_name.endswith('.zip'):
            try:
                unzip_file(file_path, output_folder)
                logging.info("Downloaded zip file successfully unzipped.")
            except Exception as e:
                logging.error(f"Error during unzip for '{file_path}': {e}")
                if os.path.exists(file_path):
                    os.remove(file_path)
                return False

        logging.info(f"Download and processing for {url} completed successfully.")
        return True # Explicit final success return

    # Catch specific requests-related exceptions
    except requests.exceptions.RequestException as e:
        logging.error(f"Download failed for '{url}' due to network/HTTP error: {e}")
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
        return False # Return False on request failure

    # Catch errors from URL parsing or OS operations (e.g., creating directories, file I/O)
    except (ValueError, OSError) as e:
        logging.error(f"Error processing URL or file system for '{url}': {e}")
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
        return False

    # Catch any other unexpected Python errors
    except Exception as e:
        logging.error(f"An unexpected error occurred for URL '{url}': {e}")
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
        return False


def main(_):
    logging.set_verbosity(logging.INFO)
    logging.info("Script execution started...")
    url = FLAGS.url
    output_folder = FLAGS.output_folder
    unzip = FLAGS.unzip
    retry_tries = FLAGS.retry_tries
    retry_delay = FLAGS.retry_delay
    retry_backoff = FLAGS.retry_backoff

    if not url:
        logging.fatal("--url is required. Exiting.")
        sys.exit(1) # Indicate failure to the system if URL is missing

    # No need for an explicit check here; absl.flags will handle it
    # because 'output_folder' is now defined with a default of None
    # and marked as required.

    if not download_file(url, output_folder, unzip, None, retry_tries, retry_delay, retry_backoff):
        logging.error("File download or processing failed. Check logs for details.")
        sys.exit(1)
    else:
        logging.info("Script processing completed successfully.")


if __name__ == '__main__':
    flags.mark_flag_as_required('url')
    flags.mark_flag_as_required('output_folder')
    app.run(main)
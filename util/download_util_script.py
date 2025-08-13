# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 20 ('License');
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#           https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an 'AS IS' BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# How to run the script to download the files:
# python3 download_util_script.py --download_url="<url>" --unzip=<True if files have to be unzipped.>

import os
import sys
from absl import app
from absl import flags
from absl import logging
import requests
from retry import retry
from urllib.parse import urlparse
import zipfile
import datetime
import time

FLAGS = flags.FLAGS
flags.DEFINE_string('download_url', None, 'URL of the file to download')
flags.DEFINE_string('output_folder', None, 'Folder to save the downloaded file')
flags.DEFINE_bool('unzip', False,
                  'Unzip the downloaded file if it is a zip file')

flags.DEFINE_integer('retry_tries', 3, 'Number of times to retry a download.')
flags.DEFINE_integer('retry_delay', 5,
                     'Initial delay in seconds between retries.')
flags.DEFINE_integer(
    'retry_backoff', 2,
    'Backoff factor for retry delay (e.g., 2 means delay doubles each time).')


def _retry_method(url: str, headers: dict, tries: int, delay: int,
                  backoff: int) -> requests.Response:
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

    @retry(tries=tries,
           delay=delay,
           backoff=backoff,
           exceptions=(requests.exceptions.ConnectionError,
                       requests.exceptions.Timeout,
                       requests.exceptions.HTTPError))
    def _perform_request(url: str,
                         headers: dict,
                         method: str = 'GET') -> requests.Response:
        logging.info(f"Attempting {method} request to: {url}")
        if method == 'HEAD':
            response = requests.head(url,
                                     headers=headers,
                                     allow_redirects=True,
                                     timeout=10)
        else:  # Default to GET
            response = requests.get(url,
                                    headers=headers,
                                    stream=True,
                                    timeout=30)
        response.raise_for_status(
        )  # Raise HTTPError for bad responses (4xx or 5xx)
        return response

    return _perform_request(url, headers)


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

    except zipfile.BadZipFile as e:
        logging.error(
            f"Error unzipping file '{file_path}': Not a valid zip file or corrupted. Error: {e}"
        )
        # Re-raising as a custom exception or a more specific ValueError
        # allows the caller to catch this specific unzipping failure.
        raise ValueError(f"Invalid Zip File: {file_path}") from e
    except OSError as e:
        logging.error(f"OS error during unzipping file '{file_path}': {e}")
        raise  # Re-raise original OSError to propagate
    except Exception as e:
        logging.error(
            f"An unexpected error occurred while unzipping file '{file_path}': {e}"
        )
        raise  # Re-raise any other unexpected exception


def download_file(url: str,
                  output_folder: str,
                  unzip: bool,
                  headers: dict = None,
                  tries: int = 3,
                  delay: int = 5,
                  backoff: int = 2) -> bool:
    """
    Downloads file from the URL and saves it to a specified folder.
    The function returns True on success, False on failure.
    Includes logic to check file timestamp against server's Last-Modified header,
    re-downloading only if the local file is stale.

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
            logging.error(
                f"Invalid URL format or missing scheme for '{url}'. "
                "Please ensure URL starts with 'http://' or 'https://'.")
            return False
        # --- End URL scheme validation ---

        # --- Output folder validation: Ensure it's not an empty string ---
        if not output_folder or not output_folder.strip():
            logging.fatal(
                f"Invalid output_folder specified: '{output_folder}'. "
                "Output path cannot be empty or consist only of whitespace.")
            return False
        # --- End Output folder validation ---

        file_name = os.path.basename(parsed_url.path)
        server_last_modified_timestamp = None

        # Perform a HEAD request to get headers (Content-Type, Last-Modified)
        try:
            temp_head_response = requests.head(url,
                                               headers=headers,
                                               allow_redirects=True,
                                               timeout=10)
            temp_head_response.raise_for_status()
            last_modified_header = temp_head_response.headers.get(
                'Last-Modified')
        except requests.exceptions.RequestException as e:
            logging.warning(
                f"Direct HEAD request failed for '{url}' (cannot get Last-Modified): {e}"
            )
            last_modified_header = None

        if last_modified_header:
            try:
                server_last_modified_timestamp = datetime.datetime.strptime(
                    last_modified_header,
                    '%a, %d %b %Y %H:%M:%S %Z').timestamp()
                logging.debug(
                    f"Server Last-Modified: {last_modified_header} (Unix: {server_last_modified_timestamp})"
                )
            except ValueError:
                logging.warning(
                    f"Could not parse Last-Modified header from '{url}': '{last_modified_header}'"
                )

        # --- Filename inference logic ---
        if not file_name:
            default_file_name = "downloaded_file"
            logging.warning(
                f"Unable to infer filename from URL '{url}'. Using a default name: '{default_file_name}'."
            )
            file_name = default_file_name
        else:
            if '.' not in file_name and not unzip:
                file_name = file_name + '.xlsx'
                logging.info(
                    f"Appended '.xlsx' extension. Final inferred filename: {file_name}"
                )

        file_path = os.path.join(output_folder, file_name)

        # Ensure output folder exists
        os.makedirs(output_folder, exist_ok=True)
        logging.info(f"Output folder '{output_folder}' ensured to exist.")

        # --- File Staleness Check ---
        if os.path.exists(file_path):
            local_file_timestamp = os.path.getmtime(file_path)
            logging.info(
                f"File already exists at {file_path}.URL is {url} .Local last modified: {datetime.datetime.fromtimestamp(local_file_timestamp)}"
            )

            if server_last_modified_timestamp:
                if local_file_timestamp >= server_last_modified_timestamp - 1:
                    logging.info(
                        "Local file is up-to-date (or newer) compared to server. Skipping download."
                    )
                    if unzip and (file_name.endswith('.zip') or
                                  file_name.endswith('.ashx')):
                        # Call unzip_file. Its internal exception handling will propagate.
                        unzip_file(file_path, output_folder)
                        logging.info(
                            f"Existing zip file '{file_path}' from URL '{url}' successfully unzipped."
                        )
                    return True  # File is up-to-date, no download needed
                else:
                    logging.info(
                        f"Local file is older than server's version. Re-downloading '{file_name}'."
                    )
            else:
                logging.warning(
                    f"Server did not provide 'Last-Modified' header for '{url}'. Cannot check staleness. "
                    "Skipping download of existing file without clear reason.")
                if unzip and (file_name.endswith('.zip') or
                              file_name.endswith('.ashx')):
                    # Call unzip_file. Its internal exception handling will propagate.
                    unzip_file(file_path, output_folder)
                    logging.info("Existing zip file successfully unzipped.")
                return True  # Treat as up-to-date if no server timestamp for comparison

        # --- Proceed with download if file doesn't exist or is stale ---
        response = _retry_method(url, headers, tries, delay, backoff)

        with open(file_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        logging.info(
            f"File successfully downloaded to: {file_path} and the url is '{url}'"
        )

        if unzip and (file_name.endswith('.zip') or
                      file_name.endswith('.ashx')):
            # Call unzip_file. Its internal exception handling will propagate.
            unzip_file(file_path, output_folder)
            logging.info("Downloaded zip file successfully unzipped.")

        logging.info(
            f"Download and processing for {url} completed successfully.")
        return True

    # --- Catch specific exceptions related to requests, unzipping, or OS errors ---
    # We now catch ValueError, which unzip_file can raise for BadZipFile.
    except (requests.exceptions.RequestException, ValueError, OSError) as e:
        # Check if the error came from unzip_file for more specific logging
        if isinstance(e, ValueError) and "Invalid Zip File" in str(e):
            logging.error(
                f"Processing failed: Unzipping error for '{file_path}'. Error: {e}"
            )
        elif isinstance(e, OSError):
            logging.error(
                f"Processing failed: File system error for '{url}'. Error: {e}")
        else:  # Must be requests.exceptions.RequestException
            logging.error(
                f"Download failed for '{url}' due to network/HTTP error: {e}")

        # Clean up partially downloaded/corrupted file if an error occurred during download or processing
        if file_path and os.path.exists(file_path):
            logging.info(
                f"Deleting partially downloaded or corrupted file: '{file_path}'."
            )
            os.remove(file_path)
        return False

    # --- Catch any other unexpected Python errors ---
    except Exception as e:
        logging.fatal(f"An unexpected error occurred for URL '{url}': {e}")
        if file_path and os.path.exists(file_path):
            logging.info(
                f"Deleting partially downloaded or corrupted file: '{file_path}'."
            )
            os.remove(file_path)
        return False


def main(_):
    logging.set_verbosity(logging.INFO)
    logging.info("Script execution started...")
    url = FLAGS.download_url
    output_folder = FLAGS.output_folder
    unzip = FLAGS.unzip
    retry_tries = FLAGS.retry_tries
    retry_delay = FLAGS.retry_delay
    retry_backoff = FLAGS.retry_backoff

    if not url:
        logging.fatal("--download_url is required. Exiting.")
        sys.exit(1)

    if not download_file(url, output_folder, unzip, None, retry_tries,
                         retry_delay, retry_backoff):
        logging.error(
            "File download or processing failed. Check logs for details.")
        sys.exit(1)
    else:
        logging.info("Script processing completed successfully.")


if __name__ == '__main__':
    flags.mark_flag_as_required('download_url')

    flags.mark_flag_as_required('output_folder')

    app.run(main)

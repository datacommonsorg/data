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
"""
This Python Script downloads the EPA files, into the input_files folder to be
made available for further processing.
"""

import os
import requests
import certifi
from retry import retry
from urllib.parse import urlparse
import subprocess
from urllib.error import ContentTooShortError
import sys
import ssl
from absl import logging

ssl._create_default_https_context = ssl._create_unverified_context

_COMMON_PATH = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(1, _COMMON_PATH)

from download_config import *

_DOWNLOAD_PATH = os.path.join(os.path.dirname((__file__)), 'gcs_output', 'input_files')
path_to_company_cert = "/etc/ssl/certs/ca-certificates.crt"

# def check_url_accessibility(url, timeout=10):
#     """
#     Checks if a URL is accessible by making a HEAD request.
#     Returns True if accessible (status 200 OK) and False otherwise.
#     """
#     try:
#         # Use a HEAD request to avoid downloading the entire file just for a check
#         response = requests.head(url, timeout=timeout)
#         response.raise_for_status()  # Raise an HTTPError for bad responses (4xx or 5xx)
#         return True
#     except requests.exceptions.RequestException as e:
#         logging.fatal(f"FATAL: URL check failed for '{url}': {e}")
#         return False


@retry(tries=3, delay=5, backoff=20)
def download_file_with_retry(url):
    """
    Attempts to download a file with retry logic in case of failure.
    Retries up to 'retries' times with a delay of 'delay' seconds between attempts.

    Args:
        url (str): The URL to download.
        retries (int): Number of retry attempts.
        delay (int): Delay in seconds between retries.

    Returns:
        str: The path to the downloaded file.
    """
    global _DOWNLOAD_PATH, path_to_company_cert
    try:
        logging.info(f"Downloading {url}...")
        logging.info(f"certifi.where() -> {certifi.where()}")
        parsed_url = urlparse(url)
        file_name = os.path.basename(parsed_url.path)
        zip_path = os.path.join(_DOWNLOAD_PATH, file_name)

        response = requests.get(url, verify=False, stream=True)
        response.raise_for_status()
        with open(zip_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        logging.info(f"Successfully downloaded {url} to {zip_path} path.")
        return zip_path

    except Exception as e:
        logging.fatal(f"Failed to download {url} due to {e}")
        sys.exit(1)


def download_files(url_folder_map):
    global _DOWNLOAD_PATH
    logging.info(f"Ensuring download directory '{_DOWNLOAD_PATH}' exists.")
    os.makedirs(_DOWNLOAD_PATH, exist_ok=True)
    # if not os.path.exists(_DOWNLOAD_PATH):
    #     os.mkdir(_DOWNLOAD_PATH)
    # os.chdir(_DOWNLOAD_PATH)
    for urls, folders in url_folder_map.items():
        if len(urls) != len(folders):
            logging.fatal(
                "Configuration Error: The number of URLs and folder names in a mapping must match.")
            logging.fatal(f"URLs: {urls}, Folders: {folders}")
            raise SystemExit("The number of urls and folder must match. Exiting.")

        for url, folder in zip(urls, folders):
            try:
                logging.info(f"Processing URL: {url} for folder: {folder}")
                downloaded_file_path = download_file_with_retry(url)
                if downloaded_file_path:
                    logging.info(f"URL {url} downloaded to {downloaded_file_path}")
                    extract_dir = os.path.join(_DOWNLOAD_PATH, folder)
                    os.makedirs(extract_dir, exist_ok=True)
                    logging.info(f"Extracting {downloaded_file_path} to {extract_dir} using 7z...")
                    subprocess.run(["7z", "x", downloaded_file_path, f"-o{extract_dir}"])
                else:
                    logging.fatal(f"Error downloading {url} due to error: {e}")
            except Exception as e:
                logging.fatal(f"Error downloading {url} due to error: {e}")

    #remove meta data files
    for root, _, files in os.walk(_DOWNLOAD_PATH):
        for file in files:
            if file.endswith('.txt') or file.endswith('.pdf') or file.endswith(
                    '.xlsx') or 'tribes' in file:
                os.remove(os.path.join(root, file))


# --- Your main function ---
def main():
    """
    Main function to orchestrate the file download process.
    """
    global _DOWNLOAD_PATH
    logging.set_verbosity(1)
    logging.info(f"Script execution started.")
    logging.info(f'Download path is set to {_DOWNLOAD_PATH}')
    download_files(url_folder_map)  # url_folder_map is accessible because it's a global variable
    logging.info(f"Script execution finished.")


if __name__ == "__main__":
    main()

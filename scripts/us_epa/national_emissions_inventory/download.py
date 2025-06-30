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
import urllib.request
import requests
import zipfile
import shutil
import subprocess
import time
from urllib.error import ContentTooShortError
import sys
import ssl
import logging

ssl._create_default_https_context = ssl._create_unverified_context

_COMMON_PATH = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(1, _COMMON_PATH)
from download_config import *

_DOWNLOAD_PATH = os.path.join(os.path.dirname((__file__)), 'input_files')

def check_url_accessibility(url, timeout=10):
    """
    Checks if a URL is accessible by making a HEAD request.
    Returns True if accessible (status 200 OK) and False otherwise.
    """
    try:
        # Use a HEAD request to avoid downloading the entire file just for a check
        response = requests.head(url, timeout=timeout)
        response.raise_for_status() # Raise an HTTPError for bad responses (4xx or 5xx)
        return True
    except requests.exceptions.RequestException as e:
        logging.fatal(f"FATAL: URL check failed for '{url}': {e}")
        return False


def download_file_with_retry(url, retries=3, delay=5):
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
    attempt = 0
    while attempt < retries:
        try:
            logging.info(
                f"Downloading {url} (Attempt {attempt + 1}/{retries})...")
            zip_path, _ = urllib.request.urlretrieve(url)
            logging.info(f"Successfully downloaded {url} to {zip_path}.")
            return zip_path

        except ContentTooShortError:
            logging.warning(
                f"Download incomplete for {url}. Retrying in {delay} seconds..."
            )
            time.sleep(delay)
            attempt += 1
        except Exception as e:
            logging.error(f"Error downloading {url}: {e}")
            logging.fatal(
                f"Aborting download for {url} due to unrecoverable error.")
            raise Exception(
                f"Failed to download {url} due to an unexpected error: {e}")

    logging.fatal(
        f"Failed to download {url} after {retries} attempts due to repeated incomplete downloads."
    )
    raise Exception(f"Failed to download {url} after {retries} attempts.")


def download_files(url_folder_map):
    logging.info(f"Ensuring download directory '{_DOWNLOAD_PATH}' exists.")
    if not os.path.exists(_DOWNLOAD_PATH):
        os.mkdir(_DOWNLOAD_PATH)
    os.chdir(_DOWNLOAD_PATH)

    for urls, folders in url_folder_map.items():
        if len(urls) != len(folders):
            logging.fatal(
                "Configuration Error: The number of URLs and folder names in a mapping must match."
            )
            logging.fatal(f"URLs: {urls}, Folders: {folders}")
            raise SystemExit(
                "The number of urls and folder must match. Exiting.")

        for url, folder in zip(urls, folders):
            try:
                logging.info(f"Processing URL: {url} for folder: {folder}")
                zip_path = download_file_with_retry(url)
                extract_dir = os.path.join(_DOWNLOAD_PATH, folder)
                os.makedirs(extract_dir, exist_ok=True)
                logging.info(
                    f"Extracting {zip_path} to {extract_dir} using 7z...")
                subprocess.run(["7z", "x", zip_path, f"-o{extract_dir}"])
            except Exception as e:
                logging.error(f"Skipping processing of {url} due to error: {e}")
                logging.warning(f"Moving to the next URL in the map.")

                continue  # Skip this URL and continue with the next one

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
    logging.info(f"Script execution started.")
    download_files(
        url_folder_map
    )  # url_folder_map is accessible because it's a global variable
    logging.info(f"Script execution finished.")


if __name__ == "__main__":
    main()

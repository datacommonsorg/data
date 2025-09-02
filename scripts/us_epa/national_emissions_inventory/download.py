# Copyright 2025 Google LLC
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
import subprocess
import sys
import ssl
import json
from absl import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from download_config import DOWNLOAD_CONFIG

# --- Configuration ---
MAX_WORKERS = 5  # Number of concurrent downloads
PROGRESS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             'gcs_output', 'in_progress.json')
DOWNLOAD_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             'gcs_output', 'input_files')

# --- SSL Context ---
ssl._create_default_https_context = ssl._create_unverified_context


def load_progress():
    """Loads the set of downloaded URLs from the progress file."""
    if not os.path.exists(PROGRESS_FILE):
        return set()
    try:
        with open(PROGRESS_FILE, 'r') as f:
            return set(json.load(f))
    except (IOError, json.JSONDecodeError) as e:
        logging.error(f"Error loading progress file: {e}")
        return set()


def save_progress(url):
    """Saves a completed URL to the progress file."""
    downloaded_urls = load_progress()
    downloaded_urls.add(url)
    try:
        with open(PROGRESS_FILE, 'w') as f:
            json.dump(list(downloaded_urls), f, indent=4)
    except IOError as e:
        logging.error(f"Error saving progress for URL {url}: {e}")


def download_and_unzip(config):
    """
    Downloads and unzips a single file as defined in the config.
    """
    url = config.get("url")
    folder = config.get("folder")

    if not url or not folder:
        return f"Skipping invalid config item: {config}"

    try:
        logging.info(f"Processing URL: {url} for folder: {folder}")
        file_name = os.path.basename(urlparse(url).path)
        zip_path = os.path.join(DOWNLOAD_PATH, file_name)
        extract_dir = os.path.join(DOWNLOAD_PATH, folder)

        # Download the file
        response = requests.get(url, verify=False, stream=True)
        response.raise_for_status()
        with open(zip_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        logging.info(f"Successfully downloaded {url} to {zip_path}")

        # Unzip the file
        logging.info(f"Extracting {zip_path} to {extract_dir} using 7z...")
        subprocess.run(["7z", "x", zip_path, f"-o{extract_dir}"], check=True)
        logging.info(f"Extraction of {zip_path} complete.")

        # Remove the zip file
        os.remove(zip_path)
        logging.info(f"Removed zip file: {zip_path}")

        # Save progress
        save_progress(url)
        return f"Successfully processed {url}"

    except requests.exceptions.RequestException as e:
        return f"Failed to download {url}: {e}"
    except subprocess.CalledProcessError as e:
        return f"Failed to extract {zip_path}: {e}"
    except Exception as e:
        return f"An unexpected error occurred with {url}: {e}"


def main():
    """
    Main function to orchestrate the file download process.
    """
    logging.info("Script execution started.")
    downloaded_urls = load_progress()
    urls_to_download = [
        item for item in DOWNLOAD_CONFIG
        if item.get("url") not in downloaded_urls
    ]

    if not urls_to_download:
        logging.info("All files have been downloaded. Nothing to do.")
        return

    logging.info(f"Found {len(urls_to_download)} files to download.")

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {
            executor.submit(download_and_unzip, item): item
            for item in urls_to_download
        }

        for future in as_completed(futures):
            url = futures[future].get('url')
            try:
                result = future.result()
                logging.info(result)
            except Exception as e:
                logging.error(f"An error occurred for URL {url}: {e}")

    logging.info("Script execution finished.")


if __name__ == "__main__":
    from urllib.parse import urlparse
    main()

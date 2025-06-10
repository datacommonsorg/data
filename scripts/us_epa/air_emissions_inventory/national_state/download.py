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
import json
import urllib.request
from google.cloud import storage  # For GCS integration
from absl import flags, app, logging  # Use absl for flag handling

# Configure logging to show messages in the terminal
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Define flags
_FLAGS = flags.FLAGS
flags.DEFINE_string('config_path', '',
                    'Path to the configuration file in the GCS bucket.')

# Hardcoded GCS bucket name
GCS_BUCKET_NAME = "datcom-csv"

# Download path for files
_DOWNLOAD_PATH = os.path.join(os.path.dirname(__file__), 'input_files')


def check_url_status(url: str) -> bool:
    """
    Check if the given URL is reachable and log URL info.

    Args:
        url (str): The URL to check.

    Returns:
        bool: True if the URL is reachable (status code 200), False otherwise.
    """
    try:
        with urllib.request.urlopen(url) as response:
            status_code = response.status
            logging.info(f"URL {url} is reachable. Status code: {status_code}")
            return status_code == 200
    except Exception as e:
        logging.fatal(f"Failed to reach URL {url}. Details: {e}")
        return False


def read_config_from_gcs(config_path: str) -> list:
    """
    Reads a configuration file from GCS and parses the download URLs.

    Args:
        config_path (str): The path to the configuration file in the bucket.

    Returns:
        list: A list of URLs to download.
    """
    try:
        client = storage.Client()
        bucket = client.get_bucket(GCS_BUCKET_NAME)
        blob = bucket.blob(config_path)
        config_data = json.loads(blob.download_as_text())
        logging.info(f"Successfully read configuration from GCS: {config_path}")

        # Extract URLs from the config structure
        urls = [
            entry["download_path"]
            for entry in config_data
            if "download_path" in entry
        ]
        return urls
    except Exception as e:
        logging.fatal(
            f"Failed to read configuration file from GCS. Details: {e}")
        return []


def download_files(urls: list) -> None:
    """
    Download files from specified URLs and log the status.

    Args:
        urls (list): A list of file URLs to download.

    Returns:
        None
    """
    if not os.path.exists(_DOWNLOAD_PATH):
        os.mkdir(_DOWNLOAD_PATH)
    os.chdir(_DOWNLOAD_PATH)

    for file_url in urls:
        # Check URL status before proceeding
        if not check_url_status(file_url):
            logging.fatal(f"URL not reachable: {file_url}. Skipping download.")

        file_name = file_url.split("/")[-1]

        try:
            file_path = os.path.join(_DOWNLOAD_PATH, file_name)
            urllib.request.urlretrieve(file_url, file_path)
            logging.info(f"Successfully downloaded: {file_name} to {file_path}")
        except Exception as e:
            logging.fatal(
                f"Failed to download {file_name} from {file_url}. Details: {e}")


def main(argv):
    # Get the config path from the flags
    config_path = _FLAGS.config_path

    if not config_path:
        logging.fatal(
            "Please provide the --config_path flag with a valid GCS path.")
        return

    # Read URLs from the GCS-hosted config file
    urls = read_config_from_gcs(config_path)

    # Proceed to download files
    if urls:
        download_files(urls)
    else:
        logging.fatal("No URLs to download. Exiting program.")


if __name__ == '__main__':
    app.run(main)

# Copyright 2024 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json, os, requests, sys
from pathlib import Path
from absl import app, logging, flags
from retry import retry
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

_FLAGS = flags.FLAGS
flags.DEFINE_string('input_file_path', 'input_files', 'Input files path')
flags.DEFINE_string(
    'config_file', 'gs://unresolved_mcf/cdc/environmental/import_configs.json',
    'Config file path')

_MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
_INPUT_FILE_PATH = None
sys.path.append(os.path.join(_MODULE_DIR, '../../../util/'))
import file_util

record_count_query = '?$query=select%20count(*)%20as%20COLUMN_ALIAS_GUARD__count'

# GCS works well with multiples of 256 KiB.
DEFAULT_CHUNK_SIZE = 8 * 1024 * 1024 # 8 MB

# Define the exceptions we want to retry on.
# This includes common network-related issues.
RETRYABLE_EXCEPTIONS = (
    requests.exceptions.ConnectionError,
    requests.exceptions.ChunkedEncodingError,
    requests.exceptions.Timeout,
)


def download_files(importname, configs):

    def download_with_retry(url: str, input_file_name: str, chunk_size: int = DEFAULT_CHUNK_SIZE):
        """
        Downloads a large file from a URL with retries and an improved progress indicator.

        Args:
            url: The URL of the file to download.
            input_file_name: The name of the file to save the download as.
            chunk_size: The chunk size in bytes for downloading.
        """
        logging.info(f"Starting download from URL: {url}")
        filename = os.path.join(_INPUT_FILE_PATH, input_file_name)

        @retry(
            stop=stop_after_attempt(5),  # Stop after 5 attempts
            wait=wait_exponential(multiplier=1, min=4, max=30),  # Exponential backoff with jitter
            retry=retry_if_exception_type(RETRYABLE_EXCEPTIONS),
            reraise=True  # Reraise the exception if all retries fail
        )
        def download_file():
            downloaded_bytes = 0
            last_logged_progress = 0

            with requests.get(url, stream=True, timeout=60) as response:
                response.raise_for_status()  # Raise an exception for bad status codes

                total_size_in_bytes = int(response.headers.get('content-length', 0))
                logging.info(f"Total file size: {total_size_in_bytes / (1024 * 1024):.2f} MB")

                with open(filename, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=chunk_size):
                        if chunk:  # filter out keep-alive new chunks
                            f.write(chunk)
                            downloaded_bytes += len(chunk)

                            if total_size_in_bytes > 0:
                                # Log progress every 10%
                                progress = int((downloaded_bytes / total_size_in_bytes) * 100)
                                if progress >= last_logged_progress + 10:
                                    logging.info(f"Downloaded {progress}% ({downloaded_bytes / (1024 * 1024):.2f} MB)")
                                    last_logged_progress = progress
                            else:
                                # If total size is unknown, log every 100 MB
                                if downloaded_bytes >= last_logged_progress + (100 * 1024 * 1024):
                                    logging.info(f"Downloaded {downloaded_bytes / (1024 * 1024):.2f} MB")
                                    last_logged_progress = downloaded_bytes


            logging.info(f"Successfully downloaded {downloaded_bytes / (1024 * 1024):.2f} MB to {filename}")

        try:
            download_file()
        except requests.exceptions.HTTPError as e:
            logging.error(f"HTTP Error while downloading {url}: {e}")
        except Exception as e:
            logging.error(f"An unexpected error occurred while downloading {url}: {e}")

    try:
        for config in configs:
            if config["import_name"] == importname:
                files = config["files"]
                for file_info in files:
                    url_new = file_info["url"]
                    logging.info(f"URL from config file {url_new}")
                    input_file_name = file_info["input_file_name"]
                    logging.info(f"Input File Name {input_file_name}")

                    get_record_count = requests.get(
                        url_new.replace('.csv', record_count_query))
                    if get_record_count.status_code == 200:
                        record_count = json.loads(
                            get_record_count.text
                        )[0]['COLUMN_ALIAS_GUARD__count']
                        logging.info(
                            f"Numbers of records found for the URL {url_new} is {record_count}"
                        )
                        url_new = f"{url_new}?$limit={record_count}&$offset=0"
                        download_with_retry(url_new, input_file_name)
                        logging.info(
                            "Successfully downloaded the source data...!!!!")
                    else:
                        logging.error(
                            f"Failed to download files, Status code: {get_record_count.status_code}"
                        )

    except Exception as e:
        logging.fatal(f"Error downloading URL {url_new} - {e}")


def main(_):
    """Main function to download the csv files."""
    global _INPUT_FILE_PATH
    _INPUT_FILE_PATH = os.path.join(_FLAGS.input_file_path)
    _INPUT_FILE_PATH = os.path.join(_MODULE_DIR, 'gcs_output', _FLAGS.input_file_path)
    Path(_INPUT_FILE_PATH).mkdir(parents=True, exist_ok=True)
    importname = sys.argv[1]
    logging.info(f'Loading config: {_FLAGS.config_file}')
    with file_util.FileIO(_FLAGS.config_file, 'r') as f:
        config = json.load(f)
    download_files(importname, config)


if __name__ == "__main__":
    app.run(main)

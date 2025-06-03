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

#How to run the script to download the files:
#python3 download_util_script.py --url="<url>" --unzip=<True if files have to be unzipped.>



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
DATA_DIR = MODULE_DIR.split('/data/')[0]
sys.path.append(MODULE_DIR)
sys.path.append(os.path.join(DATA_DIR, 'data/util'))

FLAGS = flags.FLAGS
flags.DEFINE_string('url', None, 'URL of the file to download')
flags.DEFINE_string('output_folder', 'input_folder',
                    'Folder to save the downloaded file')
flags.DEFINE_bool('unzip', False,
                  'Unzip the downloaded file if it is a zip file')

flags.DEFINE_integer('retry_tries', 3, 'Number of times to retry a download.')
flags.DEFINE_integer('retry_delay', 5, 'Initial delay in seconds between retries.')
flags.DEFINE_integer('retry_backoff', 2,
                     'Backoff factor for retry delay (e.g., 2 means delay doubles each time).')


def _retry_method(url: str, headers, tries, delay, backoff) -> requests.Response:
    """
    Attempts to make a GET request to a URL with retries.

    Args:
        url: The URL to request.
        headers: Optional dictionary of HTTP headers to send with the request.

    Returns:
        A requests.Response object if the request is successful.

    Raises:
        requests.exceptions.RequestException: If the request fails after retries.
    """

    @retry(tries=tries, delay=delay, backoff=backoff)
    def retry_download(url: str, headers):
        logging.info("Attempting to download from: %s", url)
        if headers:
            response = requests.get(url, headers=headers)
        else:
            response = requests.get(url)
        response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
        return response

    return retry_download(url, headers)

def unzip_file(file_path, output_folder):
    """
    Unzips a zip file to the specified path_to_save.
    Args:
        file_path: The path to the zip file.
        path_to_save: The folder where the contents will be extracted.
    """
    try:
        with zipfile.ZipFile(file_path, 'r') as zip_ref:
            zip_ref.extractall(output_folder)
        logging.info(f"File unzipped to: {output_folder}")
        os.remove(file_path)
    except zipfile.BadZipFile as e:
        logging.error(
            f"Error unzipping file '{file_path}': Not a valid zip file or corrupted. Error: {e}")
        raise  # Re-raise to terminate the main download process
    except OSError as e:
        logging.error(f"OS error during unzipping file '{file_path}': {e}")
        raise  # Re-raise to terminate the main download process
    except Exception as e:
        logging.error(f"An unexpected error occurred while unzipping file '{file_path}': {e}")
        raise  # Re-raise to terminate the main download process

def download_file(url, output_folder, unzip, headers:dict={}, tries=3,
                 delay=5,
                 backoff=2):
    """
    Downloads file from the URLs and saves them to a specified folder.
    If a file already exists at the target path, its download is skipped.
    The script will terminate if any single download or unzip operation fails.
    Args:
        url: URLs of the files to download.
        output_folder: The local folder to save the downloaded files.
                       Defaults to 'input_files'.
        unzip: If True, attempts to unzip each downloaded file if it's a zip file.
        headers: Optional dictionary of HTTP headers to send with each request.
    Raises:
        requests.exceptions.RequestException: If a download fails after retries.
        zipfile.BadZipFile: If an unzip operation encounters an invalid zip file.
        OSError: If an operating system error occurs (e.g., path issues).
        Exception: For any other unexpected errors during processing.
    """
    try:
        logging.info(f"Downloading from: {url}")
        file_name = os.path.basename(urlparse(url).path)
        if not file_name:
            logging.error(f"Invalid URL: {url}")
            return
        if '.' not in file_name:
            file_name = file_name + '.xlsx'
        file_path = os.path.join(output_folder, file_name)

        response = _retry_method(url, headers,tries, delay,backoff)
        with open(file_path, "wb") as f:
            f.write(response.content)

        logging.info(f"File saved to: {file_path}")

        if unzip and file_name.endswith('.zip'):
            unzip_file(file_path, output_folder)
    except requests.exceptions.RequestException as e:
        logging.error(f"Error downloading file from '{url}': {e}. Terminating.")
        raise  # Re-raise to be caught by main function

    except ValueError as e:  # Catch the specific ValueError for invalid URLs
        logging.error(f"Invalid URL processing error: {e}. Terminating.")
        raise  # Re-raise to be caught by main function

    except Exception as e:
        logging.error(f"An unexpected error occurred for URL '{url}': {e}. Terminating.")
        raise  # Re-raise to be caught by main function



def main(_):
    logging.set_verbosity(logging.INFO)
    logging.info("Started...")
    url = FLAGS.url
    output_folder = FLAGS.output_folder
    unzip = FLAGS.unzip
    retry_tries = FLAGS.retry_tries
    retry_delay = FLAGS.retry_delay
    retry_backoff = FLAGS.retry_backoff
    if not url:
        logging.fatal("--url is required.")

    # try:
    download_file(url, output_folder, unzip, None, retry_tries, retry_delay, retry_backoff)
    logging.info("Script processing completed")
    # except Exception as ex:
    #     logging.fatal(
    #         f"terminating script to avoid partial import - error {ex} ")

    logging.info("Completed...")


if __name__ == '__main__':
    flags.mark_flag_as_required('url')
    app.run(main)
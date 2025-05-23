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
"""
statvar_download_util.py

Python utility to download files dynamically from given URLs.

USAGE(as import):
-----------------
from statvar_download_util import StatVarDownloader
downloader = StatVarDownloader()
downloader.download_file("https://example.com/data.csv")

USAGE(as script):
python statvar_download_util.py
-----------------
Requirements:
- absl-py(pip install absl-py)
"""

import os
import sys
import time
from pathlib import Path
from urllib.parse import urlparse
import requests
from absl import app, logging
from absl import flags

_FLAGS = flags.FLAGS

flags.DEFINE_string('url', '', 'url to download the file')
flags.DEFINE_string('destination_path', './downloads',
                    'download folder')
flags.DEFINE_string('output_filename', 'my_data.csv',
                    'download file name')
class StatVarDownloader:

    def __init__(self, retry_count: int = 3, timeout: int = 10):
        #Initializes the downloader with retry and timeout settings.
        self.retry_count = retry_count
        self.timeout = timeout

    def _download_file(self,
                       url: str,
                       destination_path: str = None,
                       output_filename: str = None) -> bool:
        """
        Downloads a single file with retry logic
        If destination_path is not provided, uses current directory
        If output_filename is not provided, extracts filename from URL
        """
        if not url:
            logging.warning("URL must be provided.")
            return False
        if destination_path is None:
            destination_path = os.getcwd()

        #Extract filename from URL if not provided
        if output_filename is None:
            output_filename = os.path.basename(urlparse(url).path)
            if not output_filename:
                logging.warning("Unable to infer filename from URL.")
                return False
        output_path = os.path.join(destination_path, output_filename)

        for attempt in range(1, self.retry_count + 1):
            try:
                logging.info(f"Downloading from {url} (Attempt {attempt})...")
                response = requests.get(url, stream=True, timeout=self.timeout)
                if response.status_code == 200:
                    #Only create output folder after successful request
                    os.makedirs(os.path.dirname(output_path), exist_ok=True)
                    with open(output_path, "wb") as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            f.write(chunk)
                    logging.info(f"File saved to: {output_path}")
                    return True
                else:
                    logging.warning(
                        f"Attempt {attempt+1} failed: Status{response.status_code}"
                    )
            except Exception as e:
                logging.warning(f"Attempt {attempt+1} failed: {e}")
                time.sleep(1)
        logging.error(f"Failed to download after {self.retry_count} attempts.")
        return False


def main(argv):
    #Sample test inside the execution
    url = _FLAGS.url
    destination_path = _FLAGS.destination_path
    output_filename =_FLAGS.output_filename
    print(url)
    exit(0)
    if not url:
        logging.fatal(
            "Please provide the --url flag with a valid url link.")
        return

    downloader = StatVarDownloader()
    success = downloader._download_file(url, destination_path, output_filename)

    if success:
        logging.info("File download completed successfully.")
    else:
        logging.error("File download failed.")


if __name__ == "__main__":
    app.run(main)
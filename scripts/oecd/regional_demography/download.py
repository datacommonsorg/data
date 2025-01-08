# Copyright 2020 Google LLC
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

import io
import requests
import sys
import time
import pandas as pd
from absl import logging

sys.path.append('../')


def download_data_to_file_and_df(url,
                                 filename=False,
                                 is_download_required=False,
                                 csv_filepath=None):
    """Downloads data from the given URL, saves it to a file, and returns a pandas DataFrame.

    Args:
        url: The URL of the data to download.
        filename: The filename to save the downloaded data.

    Returns:
        A pandas DataFrame containing the downloaded data, or None on error.
    """
    if is_download_required and filename:
        logging.info("Downloading from url %s", url)
        max_retries = 3
        retry_delay = 2

        for attempt in range(1, max_retries + 1):
            response = requests.get(url, stream=True)
            if response.status_code == 200:
                with open(filename, 'wb') as f:
                    f.write(response.content)
                logging.info("Downloaded input file to %s (attempt %d)",
                             filename, attempt)
                df = pd.read_csv(filename, low_memory=False)
                return df

            else:
                logging.error(
                    f"Error downloading data: {response.status_code} (attempt {attempt})"
                )
                time.sleep(retry_delay)  # Wait before retrying

        # If all retries fail, return None
        logging.error(f"Failed to download data after {max_retries} attempts")
        return None

    else:
        logging.info("Reading from a file  %s", csv_filepath)
        df = pd.read_csv(csv_filepath, low_memory=False)
        return df

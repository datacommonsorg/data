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

import os
import sys
import pandas as pd
from absl import logging, app
import zipfile

# Set up module path to access the utility script
_MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
data_dir = os.path.dirname(os.path.dirname(os.path.dirname(_MODULE_DIR)))
sys.path.append(data_dir)

from util.download_util_script import download_file

# The API URL to download the subnational population data as a CSV zip archive.
_API_URL = "http://api.worldbank.org/v2/country/all/indicator/SP.POP.TOTL?downloadformat=csv"

def unzip_file(inputdir):
    """
    Unzips the downloaded file.
    """
    try:
        zip_path = os.path.join(inputdir, "SP.POP.TOTL.zip")
        os.rename(os.path.join(inputdir, "SP.POP.TOTL"), zip_path)
        logging.info(f"Renamed downloaded file to '{zip_path}'.")

        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(inputdir)
        logging.info(f"Successfully unzipped '{zip_path}'.")
        os.remove(zip_path)
        logging.info(f"Removed '{zip_path}'.")

    except Exception as e:
        logging.fatal(f"An error occurred while processing the downloaded file: {e}")
        raise RuntimeError("Failed to process downloaded files.") from e

def main(_):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    source_dir = os.path.join(script_dir, "source")

    if not os.path.exists(source_dir):
        os.makedirs(source_dir)
        logging.info(f"Created source directory: {source_dir}")

    logging.info("Downloading World Bank subnational population data via API...")
    download_success = download_file(
        url=_API_URL,
        output_folder=source_dir,
        unzip=False  # We will handle unzipping manually
    )

    if download_success:
        logging.info("Download complete. Unzipping files...")
        unzip_file(source_dir)
        logging.info("Script finished successfully. Raw files are in the 'source' directory.")
    else:
        logging.fatal("Failed to download the data file.")
        raise RuntimeError("Download failed.")

if __name__ == "__main__":
   app.run(main)

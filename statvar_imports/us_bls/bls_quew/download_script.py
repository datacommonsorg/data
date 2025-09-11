# Copyright 2025 Google LLC
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

import datetime
import os
import sys
from absl import app
from absl import logging

_SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(_SCRIPT_PATH, '../../../util/'))
from download_util_script import download_file

logging.set_verbosity(logging.INFO)


def main(_):
    """
    Main function to download Quarterly and Annual data from BLS.gov.
    """
    CURRENT_YEAR = datetime.datetime.now().year
    BASE_DIR = "input_files"
    # Data is available from 1990
    START_YEAR = 1990

    datasets_to_download = {
        "quarterly": "https://data.bls.gov/cew/data/files/{year}/csv/{year}_qtrly_singlefile.zip",
        "annual": "https://data.bls.gov/cew/data/files/{year}/csv/{year}_annual_singlefile.zip",
    }

    for name, url_template in datasets_to_download.items():
        logging.info(f"Starting download for {name} data...")
        output_dir = os.path.join(BASE_DIR, name)
        
        start_year = START_YEAR
        while start_year <= CURRENT_YEAR:
            url = url_template.format(year=start_year)
            logging.info(f"Downloading {name} data for year {start_year} from {url}")
            if not download_file(
                url=url,
                output_folder=output_dir,
                unzip=True
            ):
                logging.error(f"Failed to download data for {name} {start_year} from {url}")
            start_year += 1
        logging.info(f"Finished downloading all {name} data.")


if __name__ == "__main__":
    app.run(main)
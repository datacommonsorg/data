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


def main(_):
    CURRENT_YEAR = datetime.datetime.now().year
    BASE_DIR = "input_files"

    #  Quarterly Data download logic 
    QUARTERLY_URL = "https://data.bls.gov/cew/data/files/{year}/csv/{year}_qtrly_singlefile.zip"
    quarterly_output_dir = os.path.join(BASE_DIR, "quarterly")
    # data start from the 1990 in the UI
    current_year = 1990
    while current_year <= CURRENT_YEAR:
        url = QUARTERLY_URL.format(year=current_year)
        download_file(
            url=url,
            output_folder=quarterly_output_dir,
            unzip=True
        )
        current_year += 1

    # Annual Data download logic
    ANNUAL_URL = "https://data.bls.gov/cew/data/files/{year}/csv/{year}_annual_singlefile.zip"
    annual_output_dir = os.path.join(BASE_DIR, "annual")
    
    current_year = 1990
    while current_year <= CURRENT_YEAR:
        url = ANNUAL_URL.format(year=current_year)
        download_file(
            url=url,
            output_folder=annual_output_dir,
            unzip=True
        )
        current_year += 1

if __name__ == "__main__":
    app.run(main)

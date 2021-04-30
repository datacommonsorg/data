# Copyright 2021 Google LLC
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
Utility to download all EIA Form-860 data for a given year, and prepare the
data for import.

Run this script in this folder:
python3 main.py
"""
from absl import app, flags
import io
import os
import requests
import zipfile

import utility

FLAGS = flags.FLAGS
flags.DEFINE_boolean('skip_import', False, 'Skips downloading data.')

URL = 'https://www.eia.gov/electricity/data/eia860/xls/eia8602019.zip'
OUT_PATH = 'tmp_raw_data'
UTILITY_IN_FILENAME = '1___Utility_Y2019.xlsx'
UTILITY_OUT_FILENAME = '1_utility.csv'
PLANT_IN_FILENAME = '2___Plant_Y2019.xlsx'

# module_dir_ is the path to where this module is running from.
module_dir_ = os.path.dirname(__file__)


def download_file(url: str, save_path: str):
    full_save_path = os.path.join(module_dir_, save_path)
    print(f'Downloading {url} to {full_save_path}')
    r = requests.get(url, stream=True)
    z = zipfile.ZipFile(io.BytesIO(r.content))
    z.extractall(full_save_path)


def main(argv):
    if not FLAGS.skip_import:
        download_file(URL, OUT_PATH)
    utility.process(os.path.join(module_dir_, OUT_PATH, UTILITY_IN_FILENAME),
                    UTILITY_OUT_FILENAME)


if __name__ == '__main__':
    app.run(main)

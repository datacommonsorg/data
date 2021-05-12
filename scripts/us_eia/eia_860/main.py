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
import sys
import zipfile

# Allows the following module imports to work when running as a script
sys.path.append(
    os.path.dirname(
    os.path.dirname(os.path.dirname(
        os.path.abspath(__file__)))))
from us_eia.eia_860 import utility, power_plant

FLAGS = flags.FLAGS
flags.DEFINE_boolean('skip_import', False, 'Skips downloading data.')

_URL = 'https://www.eia.gov/electricity/data/eia860/xls/eia8602019.zip'
_RAW_PATH = 'test_data'

_DATASETS = [
    # processor, input-excel, expected-csv
    (utility.process, '1___Utility_Y2019.xlsx', '1_utility.csv'),
    (power_plant.process, '2___Plant_Y2019.xlsx', '2_plant.csv'),
]

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
        download_file(_URL, _RAW_PATH)
    for (processor, in_file, out_csv) in _DATASETS:
        processor(os.path.join(module_dir_, _RAW_PATH, in_file),
                  os.path.join(module_dir_, out_csv))


if __name__ == '__main__':
    app.run(main)

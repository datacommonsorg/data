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
Utility to download all EIA data from https://api.eia.gov/bulk/manifest.txt
Files are stored in raw_data.

Run this script in this folder:
python3 download_bulk.py
"""
import sys
import io
import os
import zipfile

import requests
import pandas as pd

import utility

URL = 'https://www.eia.gov/electricity/data/eia860/xls/eia8602019.zip'
OUT_PATH = 'tmp_raw_data'
UTILITY_IN_FILENAME = '1___Utility_Y2019.xlsx'
UTILITY_OUT_FILENAME = '1_utility.csv'
PLANT_IN_FILENAME = '2___Plant_Y2019.xlsx'


def download_file(url: str, save_path: str):
    print(f'Downloading {url} to {save_path}')
    r = requests.get(url, stream=True)
    z = zipfile.ZipFile(io.BytesIO(r.content))
    z.extractall(save_path)

def main():
    utility.process(os.path.join(OUT_PATH, UTILITY_IN_FILENAME), UTILITY_OUT_FILENAME)

if __name__ == '__main__':
    main()
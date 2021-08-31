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
Author: Padma Gundapaneni @padma-g
Date: 8/30/2021
Description: Utility to download all CDC 500 PLACES data.
URL: https://chronicdata.cdc.gov/browse?category=500+Cities+%26+Places

Files are stored in raw_data.

Run this script from this directory:
python3 download_bulk.py
"""

import os

import requests

DATA_URLS = {
    "county_raw_data.csv":
        "https://chronicdata.cdc.gov/resource/swc5-untb.csv",
    "city_raw_data.csv":
        "https://chronicdata.cdc.gov/resource/eav7-hnsx.csv",
    "censustract_raw_data.csv":
        "https://chronicdata.cdc.gov/resource/cwsq-ngmh.csv",
    "zipcode_raw_data.csv":
        "https://chronicdata.cdc.gov/resource/qnzd-25i4.csv"
}


def download_file(url: str, save_path: str):
    """
    Args:
        url: url to the file to be downloaded
        save_path: path for the downloaded file to be stored
    Returns:
        a downloaded csv file in the specified file path
    """
    print(f'Downloading {url} to {save_path}')
    request = requests.get(url, stream=True)
    with open(save_path, 'wb') as file:
        file.write(request.content)


def main():
    """Main function to download the files."""
    data_dir = os.path.join(os.getcwd(), 'raw_data')
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
    for dataset_name, url in DATA_URLS.items():
        print(dataset_name)
        save_path = os.path.join(data_dir, dataset_name)
        download_file(url, save_path)


if __name__ == '__main__':
    main()

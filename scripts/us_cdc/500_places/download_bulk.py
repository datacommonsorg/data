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
import json
from google.cloud import storage

# Initialize GCP storage client
client = storage.Client()

# Define your GCP bucket and file name
bucket_name = 'datcom-csv'  # Replace with your bucket name
file_name = 'cdc500_places/download_config.json'  # Replace with your file name

# Download the file from GCP Storage
bucket = client.get_bucket(bucket_name)
blob = bucket.blob(file_name)

# Read the JSON content from the blob
json_data = blob.download_as_text()

# Load the JSON data
_CONFIG_FILE = json.loads(json_data)


def download_file(release_year, url: str, save_path: str):
    """
    Args:
        url: url to the file to be downloaded
        save_path: path for the downloaded file to be stored
    Returns:
        a downloaded csv file in the specified file path
    """
    print(f'Downloading {url} for the year {release_year} to {save_path}')
    request = requests.get(url, stream=True)
    with open(save_path, 'wb') as file:
        file.write(request.content)


def main():
    """Main function to download the files."""
    data_dir = os.path.join(os.getcwd(), 'raw_data')
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
    for item in _CONFIG_FILE:
        release_year = item["release_year"]
        for url_dict in item["parameter"]:
            save_path = os.path.join(data_dir, url_dict['FILE_NAME'])
            download_file(release_year, url_dict['URL'], save_path)


if __name__ == '__main__':
    main()

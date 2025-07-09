# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#         https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import os
import requests
from absl import app
from absl import logging
import zipfile
import json
import shutil
import config

def download_data_from_zip_url(json_api_url, output_folder, target_extension):
    """
    Fetches a JSON dictionary from a URL, extracts a ZIP file URL from it,
    downloads the ZIP, unzips its contents, filters to keep only specified files,
    and cleans up temporary files/folders.

    Args:
        json_api_url : The URL that returns a JSON dictionary containing the ZIP file URL.
        output_folder : The local directory where target files will be stored.
        target_extension: The file extension (e.g., '.csv', '.xlsx') to filter and keep.
    """

    try:
        api_response = requests.get(json_api_url)
        api_response.raise_for_status()
        data_dict_from_api = api_response.json() 
    except Exception as e:
        logging.fatal(f"An unexpected error occurred while fetching/parsing initial JSON from {json_api_url}: {e}")
    
    extracted_zip_url = list(data_dict_from_api.values())[0]

    if '?' in extracted_zip_url:
        zip_filename = os.path.basename(extracted_zip_url.split('?')[0])
    else:
        zip_filename = os.path.basename(extracted_zip_url)

    download_path = os.path.join(output_folder, zip_filename)
    try:
        os.makedirs(output_folder, exist_ok=True)
        logging.info(f"Ensured output directory exists: {output_folder}")
    except OSError as e:
        logging.error(f"Error creating directory '{output_folder}': {e}")

    logging.info(f"Downloading ZIP from {extracted_zip_url} to {download_path}...")
    try:
        with requests.get(extracted_zip_url, stream=True) as r: 
            r.raise_for_status()

            with open(download_path, 'wb') as f:
                f.write(r.content) 

        logging.info(f"Successfully downloaded: {zip_filename}")
    except requests.exceptions.RequestException as e:
        logging.error(f"Error downloading the ZIP file from {extracted_zip_url}: {e}")
    

    logging.info(f"Unzipping {download_path} to {output_folder} ")
    temp_extract_folder = os.path.join(output_folder, "temp_zip_extract")

    try:
        # Create the temporary extraction folder
        os.makedirs(temp_extract_folder, exist_ok=True)

        with zipfile.ZipFile(download_path, 'r') as zip_ref:
            zip_ref.extractall(temp_extract_folder)
        logging.info(f"All contents temporarily unzipped to {temp_extract_folder}")

        # Data cleaning and file restructuring
        for root, dirs, files in os.walk(temp_extract_folder):
            for file in files:
                file_path = os.path.join(root, file)
                if file.lower().endswith(target_extension.lower()):
                    target_file_path = os.path.join(output_folder, os.path.basename(file))
                    shutil.move(file_path, target_file_path)
                    logging.info(f"  Moved {target_extension.upper()} file: {file} to {output_folder}")
                else:
                    os.remove(file_path)
                    logging.info(f"  Removed non-{target_extension.upper()} file: {file}")

    except Exception as e:
        logging.error(f"An unexpected error occurred during unzipping or file filtering: {e}")
    finally:
        if os.path.exists(temp_extract_folder):
            shutil.rmtree(temp_extract_folder)
            logging.info(f"Cleaned up temporary extraction folder: {temp_extract_folder}")

    # Remove the original downloaded zip file
    if os.path.exists(download_path):
        os.remove(download_path)
        logging.info(f"Removed temporary zip file: {download_path}")


def main(argv):
    
    datasets_to_download = config.hate_crime_publication_api_url
    for dataset_info in datasets_to_download:
        api_url = dataset_info["api_url"]
        output_folder = dataset_info["output_folder"]
        target_extension = dataset_info["target_extension"]

        logging.info(f" Processing dataset from: {api_url}")
        download_data_from_zip_url(api_url, output_folder, target_extension)
        logging.info(f"Finished processing dataset from: {api_url}")


if __name__ == '__main__':
    app.run(main)
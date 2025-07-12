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

def download_hate_crime_data(json_api_url, output_folder):
    """
    Fetches a JSON dictionary from a URL, extracts a ZIP file URL from it,
    downloads the ZIP, unzips its contents, filters to keep only CSV files,
    and cleans up temporary files/folders.

    Args:
        json_api_url : The URL that returns a JSON dictionary containing the ZIP file URL.
        output_folder : The local directory where CSV files will be stored.
    """

    try:
        api_response = requests.get(json_api_url)
        api_response.raise_for_status() 
        data_dict_from_api = api_response.json() # Parse the response as a JSON dictionary
    except Exception as e:
        logging.fatal(f"An unexpected error occurred while fetching/parsing initial JSON: {e}")
        
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
        with requests.get(extracted_zip_url) as r: 
            r.raise_for_status() 

            with open(download_path, 'wb') as f:
                f.write(r.content) 

        logging.info(f"Successfully downloaded: {zip_filename}")
    except requests.exceptions.RequestException as e:
        logging.error(f"Error downloading the ZIP file from {extracted_zip_url}: {e}")


    logging.info(f"Unzipping {download_path} to {output_folder} ")
    # temporary folder for initial extraction
    temp_extract_folder = os.path.join(output_folder, "temp_zip_extract") 

    try:
        # Create the temporary extraction folder
        os.makedirs(temp_extract_folder, exist_ok=True)

        with zipfile.ZipFile(download_path, 'r') as zip_ref:
            zip_ref.extractall(temp_extract_folder) 
        logging.info(f"All contents temporarily unzipped to {temp_extract_folder}")
        #data cleaning and csv folder restructuring 
        for root, dirs, files in os.walk(temp_extract_folder):
            for file in files:
                file_path = os.path.join(root, file)
                if file.lower().endswith('.csv'):
                    # Moved CSV to the main OUTPUT_FOLDER
                    target_csv_path = os.path.join(output_folder, os.path.basename(file))
                    os.replace(file_path, target_csv_path) 
                    logging.info(f"  Moved CSV: {file} to {output_folder}")
                    
                else:
                    os.remove(file_path)
                    logging.info(f"  Removed non-CSV file: {file}")

    except Exception as e:
        print(f"An unexpected error occurred during unzipping or file filtering: {e}")
    finally:
        # Ensure the temporary folder is removed, even if errors occur
        if os.path.exists(temp_extract_folder):
            # Remove the temporary folder and its contents
            shutil.rmtree(temp_extract_folder) 
            print(f"Cleaned up temporary extraction folder: {temp_extract_folder}")
            
    os.remove(download_path)
    print(f"Removed temporary zip file: {download_path}")
    
def main(argv):

    api_url = config.hate_crime_api_url
    target_folder = "hate_crime_data"
    download_hate_crime_data(api_url, target_folder)

if __name__ == '__main__':
  app.run(main)
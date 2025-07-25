# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#        https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import datetime
import os
import re
import requests
import shutil
import zipfile
from absl import app
from absl import logging


def download_zip_file(extracted_zip_url, output_folder):
    """
    Downloads a ZIP file from the  URL to the specified output folder.

    Args:
        extracted_zip_url (str): The direct URL of the ZIP file.
        output_folder (str): The local directory where the ZIP file will be stored.

    Returns:
        str: The full path to the downloaded ZIP file if successful, None otherwise.
    """
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

    logging.info(
        f"Downloading ZIP from {extracted_zip_url} to {download_path}...")
    try:
        with requests.get(extracted_zip_url, stream=True) as r:
            r.raise_for_status()
            with open(download_path, 'wb') as f:
                f.write(r.content)
        logging.info(f"Successfully downloaded: {zip_filename}")
        return download_path
    except requests.exceptions.RequestException as e:
        logging.warning(
            f"Error downloading the ZIP file from {extracted_zip_url}: {e}. Skipping this download."
        )
        if os.path.exists(download_path):
            os.remove(download_path)


def process_zip_file(download_path, output_folder, extracted_year):
    """
    Unzips the downloaded ZIP file, filters the files based on the patterns,
    moves them to the output folder, and cleans up temporary files.

    Args:
        download_path (str): The full path to the downloaded ZIP file.
        output_folder (str): The local directory where  table file will be stored.
        extracted_year (str): The year used for file filtering .
    """
    if not download_path or not os.path.exists(download_path):
        logging.error(
            f"Cannot process ZIP: {download_path} does not exist or was not downloaded."
        )

    logging.info(f"Unzipping {download_path} to {output_folder} ")
    temp_extract_folder = os.path.join(output_folder, "temp_zip_extract")
    found_target_file = False
    try:
        os.makedirs(temp_extract_folder, exist_ok=True)

        with zipfile.ZipFile(download_path, 'r') as zip_ref:
            zip_ref.extractall(temp_extract_folder)
        logging.info(
            f"All contents temporarily unzipped to {temp_extract_folder}")

        table_year_pattern = re.compile(
            f"^Table_.*?{(str(extracted_year))}\.[^.]+$", re.IGNORECASE)
        for root, dirs, files in os.walk(temp_extract_folder):
            for file in files:
                file_path = os.path.join(root, file)
                if table_year_pattern.search(os.path.basename(file).lower()):
                    target_file_path = os.path.join(output_folder,
                                                    os.path.basename(file))
                    shutil.move(file_path, target_file_path)
                    logging.info(
                        f"  Moved matching file: {file} to {output_folder}")
                    found_target_file = True
                else:
                    os.remove(file_path)
                    logging.info(f"  Removed non-matching file: {file}")

        if not found_target_file:
            logging.warning(
                f"No file matching 'Table_{extracted_year}.(any_extension)' found in the extracted content from {os.path.basename(download_path)}."
            )

    except Exception as e:
        logging.error(
            f"An unexpected error occurred during unzipping or file filtering: {e}"
        )
    finally:
        #remove the temp_extract_folder and downloaded folders
        shutil.rmtree(temp_extract_folder)
        os.remove(download_path)
        logging.info(
            f"Removed temporary zip file: {download_path} and temporary extraction folder: {temp_extract_folder}"
        )


def main(argv):
    start_year = 2020
    current_year = datetime.datetime.now().year
    base_output_dir = "hate_crime_publication_data"

    try:
        os.makedirs(base_output_dir, exist_ok=True)
        logging.info(f"Ensured base output directory exists: {base_output_dir}")
    except OSError as e:
        logging.fatal(f"Error creating base directory '{base_output_dir}': {e}")

    for year in range(start_year, current_year + 1):
        api_url = f"https://cde.ucr.cjis.gov/LATEST/s3/signedurl?key=additional-datasets/hate-crime/hate_crime_{year}.zip"
        output_folder_for_year = os.path.join(
            base_output_dir, f"hate_crime_publication_{year}_data")

        logging.info(f"process dataset for year: {year} from: {api_url}")

        api_response = requests.get(api_url)
        api_response.raise_for_status()
        data_dict_from_api = api_response.json()
        if not data_dict_from_api:
            logging.warning(
                f"JSON response for {api_url} is empty or does not contain expected data. Skipping year {year}."
            )
            continue
        extracted_zip_url = list(data_dict_from_api.values())[0]
        download_path = download_zip_file(extracted_zip_url,
                                          output_folder_for_year)
        if download_path:
            process_zip_file(download_path, output_folder_for_year, str(year))

        logging.info(f"Finished processing attempt for year: {year}")


if __name__ == '__main__':
    app.run(main)

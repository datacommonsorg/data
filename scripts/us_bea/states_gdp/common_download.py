# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import os
import zipfile
from absl import logging
import requests
from retry import retry

logging.set_verbosity(logging.INFO)


@retry(tries=3, delay=5, backoff=2)
def download_and_extract_to_folders(zip_link, output_folder):
    """
    Downloads a ZIP file from a given URL using the requests module with retry,
    stores the ZIP file in the specified output folder, extracts all CSV files
    from the ZIP into the same folder, and saves them.

    Args:
        zip_link (str): The URL of the ZIP file to download.
        output_folder (str, optional): The name of the folder where the ZIP
                                       and CSV files will be saved.
                                       Defaults to "input_data".
    """
    logging.info(f"Downloading ZIP file from: {zip_link}")

    try:
        os.makedirs(output_folder, exist_ok=True)
        zip_filename = os.path.join(output_folder, os.path.basename(zip_link))

        try:
            response = requests.get(zip_link, stream=True)
            response.raise_for_status(
            )  # Raise an exception for bad status codes

            # Save the ZIP file
            with open(zip_filename, 'wb') as zip_outfile:
                for chunk in response.iter_content(chunk_size=8192):
                    zip_outfile.write(chunk)
            logging.info(f"Successfully downloaded ZIP file to: {zip_filename}")

            with zipfile.ZipFile(zip_filename) as zip_file:
                for member in zip_file.namelist():
                    if member.lower().endswith('.csv'):
                        logging.info(
                            f"Extracting and saving file: {member} to '{output_folder}'"
                        )
                        try:
                            with zip_file.open(member) as csv_file:
                                data = csv_file.read().decode('utf-8')
                                output_path = os.path.join(
                                    output_folder, member)
                                with open(output_path, 'w',
                                          encoding='utf-8') as outfile:
                                    outfile.write(data)
                                logging.info(
                                    f"Successfully extracted and saved: {member} to '{output_folder}'"
                                )
                        except Exception as e:
                            logging.fatal(
                                f"An error occurred while processing file '{member}': {e}"
                            )
        except requests.exceptions.RequestException as e:
            logging.fatal(f"Error downloading ZIP file after retries: {e}")
            return
        except zipfile.BadZipFile:
            logging.fatal(
                f"Error: Downloaded file is not a valid ZIP file: {zip_filename}"
            )
            return

    except Exception as e:
        logging.fatal(f"An unexpected error occurred: {e}")


if __name__ == "__main__":
    zip_url = "https://apps.bea.gov/regional/zip/SQGDP.zip"
    output_directory = "input_data"
    download_and_extract_to_folders(zip_url, output_folder=output_directory)
    logging.info(
        f"\nZIP and CSV files saved to the '{output_directory}' folder.")

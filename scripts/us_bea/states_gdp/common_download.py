# Copyright 2025 Google LLC
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
import pandas as pd
import zipfile
import io
from urllib.request import urlopen
from urllib.error import HTTPError, URLError
import csv
import os


def download_and_extract_to_folders(zip_link,
                                    file_names,
                                    output_folder="input_folders"):
    """
    Downloads a ZIP file from a given URL, extracts multiple specified CSV files,
    and saves each CSV file to the specified output folder.

    Args:
        zip_link (str): The URL of the ZIP file to download.
        file_names (list): A list of file names (strings) of the CSV files to extract
                           from the ZIP archive.
        output_folder (str, optional): The name of the folder where the extracted
                                       CSV files will be saved. Defaults to "input_folders".
    """
    print(f"Downloading ZIP file from: {zip_link}")

    try:

        os.makedirs(output_folder, exist_ok=True)

        # Open zip file from link.
        with urlopen(zip_link) as resp:
            zip_file = zipfile.ZipFile(io.BytesIO(resp.read()))

            for file in file_names:
                print(
                    f"Extracting and saving file: {file} to '{output_folder}'")
                try:
                    with zip_file.open(file) as csv_file:
                        data = csv_file.read().decode('utf-8')
                        output_path = os.path.join(output_folder, file)
                        with open(output_path, 'w',
                                  encoding='utf-8') as outfile:
                            outfile.write(data)
                        print(
                            f"Successfully extracted and saved: {file} to '{output_folder}'"
                        )
                except KeyError:
                    print(
                        f"Warning: File '{file}' not found in the ZIP archive.")
                except Exception as e:
                    print(
                        f"An error occurred while processing file '{file}': {e}"
                    )
    except Exception as e:
        print(f"An unexpected error occurred: {e}")


if __name__ == "__main__":
    zip_url = "https://apps.bea.gov/regional/zip/SQGDP.zip"
    files_to_extract = [
        'SQGDP1__ALL_AREAS_2005_2024.csv', 'SQGDP2__ALL_AREAS_2005_2024.csv'
    ]
    output_directory = "input_folders"

    download_and_extract_to_folders(zip_url, files_to_extract, output_directory)

    print(f"\nCSV files saved to the '{output_directory}' folder.")

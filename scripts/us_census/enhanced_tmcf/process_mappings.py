# Copyright 2023 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the 'License');
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#         https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an 'AS IS' BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
'''Processing the mappings + enhanced TMCF for US Census.

The following steps are followed:

1. Using the FLAGS provided, first check that the input TMCF + mappings files are found. Note: there are sample files provided (in this same directory) for the mappings and super/enhanced TMCF for one US Census table.
2. Use the mappings file to download all the zip files (if not already done).
3. Unzip the downloaded zip files and keep the CSV file with the relevant Data (identified by the `data_csv_file_unique_substring` flag).
4. Write all downloaded data CSV files to the input directory.
5. Process the super/enhanced TMCF file along with all the CSV files downloaded. It is assumed that all CSV files correspond to the same super/enhanced TMCF.
6. Parse all the CSV files with the super/enhanced TMCF and produce one (traditional) TMCF file with modified CSV files.
7. The output directory contains all the produced output files (one TMCF and processed CSV files). They can now be validated with the dc-import tool.
'''

import json
import os
import requests
import sys
import time

from absl import app
from absl import flags
from typing import Dict, List
from zipfile import ZipFile

import process_etmcf

# Allows the following module imports to work when running as a script
_SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(_SCRIPT_PATH, '../..'))

FLAGS = flags.FLAGS

flags.DEFINE_string(
    'data_directory', 'data',
    'Data directory (full path OR path relative to current working directory)')
flags.DEFINE_string(
    'zip_download_path', 'zip_download',
    'Zip file download directory (contained in the data_directory)')
flags.DEFINE_string('input_directory', 'input',
                    'Inputs directory (contained in the data_directory)')
flags.DEFINE_string('output_directory', 'output',
                    'Inputs directory (contained in the data_directory)')
flags.DEFINE_string('mappings_file', 'mappings.txt', 'Mappings File.')
flags.DEFINE_string('input_etmcf_filename', 'input_etmcf',
                    'Enhanced TMCF filename.')
flags.DEFINE_string(
    'data_csv_file_unique_substring', 'Data.csv',
    'The unique substring in the name of the data CSV file, e.g. Data.csv for ABC_Data.csv This is used to keep only the relevant CSV file from the zip download.'
)

NUM_RETRIES = 10


def _get_zip_download_url(url: str, json_params: Dict) -> str:
    x = requests.post(url, json=json_params)
    print(x.content)
    return json.loads(x.text)['response']['url']


def _download_zip(url: str, filepath: str) -> None:
    response = requests.get(url, stream=True)
    with open(filepath, "wb") as f:
        for chunk in response.iter_content(chunk_size=512):
            if chunk:  # filter out keep-alive new chunks
                f.write(chunk)

    # Read the file back and check if it is a valid zip file.
    # If it is not a zipfile, it will raise an Exception.
    ZipFile(filepath, 'r')


def _read_write_files_from_zip(zip_filepath, unzipped_data_path,
                               csv_filename) -> None:
    unzip_files = False

    with ZipFile(zip_filepath, 'r') as z:
        csv_files = []
        for zip_file in z.namelist():
            if not os.path.exists(os.path.join(unzipped_data_path,
                                               csv_filename)):
                if FLAGS.data_csv_file_unique_substring in zip_file:
                    unzip_files = True
                    csv_files.append(zip_file)

        if len(csv_files) > 1:
            raise Exception(
                f"Zip archive file cannot have more than one file with name containing {FLAGS.data_csv_file_unique_substring}"
            )
        if unzip_files and not csv_files:
            raise Exception(
                f"No CSV files (with names containing {FLAGS.data_csv_file_unique_substring}) were found to download. Check zip file: {zip_filepath}"
            )
        if unzip_files:
            print(f"Unzipping/Extracting files from: {zip_filepath}")
            print(f"Unzipping/Extracting files to: {unzipped_data_path}/")
            z.extractall(unzipped_data_path, members=csv_files)
            os.rename(os.path.join(unzipped_data_path, csv_files[0]),
                      os.path.join(unzipped_data_path, csv_filename))
        else:
            print("All files were previously extracted. Not re-extracting.")


def _get_post_requests_from_file(post_requests_filename: str) -> List[Dict]:
    req_file = open(post_requests_filename, 'r')

    post_reqs = []
    current_url = ""
    current_req_json_str = ""
    for line in req_file.readlines():
        if not line.strip():
            # This means a new line.
            req = {
                "url": current_url,
                "json_params": json.loads(current_req_json_str)
            }
            post_reqs.append(req)
            # Reset the current_url and current_req_json.
            current_url = ""
            current_req_json_str = ""
            continue

        if "POST" in line:
            current_url = line.strip().split("POST ")[1]
        else:
            current_req_json_str += line
    return post_reqs


def _download_mapping_file(post_req: Dict, data_path: str,
                           zip_download_path: str):
    print(f"Starting to process the post_req: {post_req}")
    url = post_req["url"]
    json_params = post_req["json_params"]
    table_id = json_params.get("request", {}).get("id", "")
    table_g = json_params.get("request", {}).get("g", "")

    zip_file_name = table_id + "_" + table_g + ".zip"
    csv_file_name = table_id + "_" + table_g + ".csv"
    zipped_filepath = os.path.join(zip_download_path, zip_file_name)

    if not os.path.exists(zipped_filepath):
        print("Get the zip file download url.")
        download_url = _get_zip_download_url(url, json_params)

        print(
            f"Downloading the zip file: {zip_file_name} at filepath: {zipped_filepath}"
        )
        for i in range(NUM_RETRIES):
            try:
                print(f"  Try # {i}")
                _download_zip(download_url, zipped_filepath)
                print("   Succeeded.")
                break
            except:
                seconds = 5
                print(
                    f"        Sleeping for {seconds}s to allow more time for the zip file to be ready."
                )
                time.sleep(seconds)
    else:
        print(
            f"Zip file ({zip_file_name}) already downloaded. Not re-downloading."
        )

    _read_write_files_from_zip(zipped_filepath, data_path, csv_file_name)


def main(_):
    # Validate the Flags.
    assert FLAGS.data_directory
    assert FLAGS.zip_download_path
    assert FLAGS.input_directory
    assert FLAGS.output_directory
    assert FLAGS.data_csv_file_unique_substring

    # Check that the data_directory and input_path are valid.
    if not os.path.exists(FLAGS.data_directory):
        raise Exception(
            f"data_directory must exist. Provided: {FLAGS.data_directory}")

    input_path = os.path.join(FLAGS.data_directory, FLAGS.input_directory)
    if not os.path.exists(input_path):
        raise Exception(
            f"input_directory must exist. Provided: {FLAGS.input_directory}. Resolved to path: {input_path}"
        )

    # If the zip directory or output directory are not found, create them.
    zip_download_path = os.path.join(FLAGS.data_directory,
                                     FLAGS.zip_download_path)
    output_path = os.path.join(FLAGS.data_directory, FLAGS.output_directory)

    if not os.path.exists(zip_download_path):
        print(
            f"zip_download_path does not exist. Creating it: {zip_download_path}"
        )
        os.mkdir(zip_download_path)

    if not os.path.exists(output_path):
        print(f"output_path does not exist. Creating it: {output_path}")
        os.mkdir(output_path)

    # Check that the mappings and TMCF files (after resolving the paths) are valid.
    mappings_filepath = os.path.join(input_path, FLAGS.mappings_file)
    if not os.path.exists(mappings_filepath):
        raise Exception(
            f"mappings_file must exist. Provided: {FLAGS.mappings_file}. Resolved to path: {mappings_filepath}"
        )

    input_etmcf_filepath = os.path.join(input_path,
                                        FLAGS.input_etmcf_filename + ".tmcf")
    if not os.path.exists(input_etmcf_filepath):
        raise Exception(
            f"input_etmcf_filename (.tmcf) must exist. Provided: {FLAGS.input_etmcf_filename}. Resolved to path: {input_etmcf_filepath}"
        )

    # Reading the post reqs file.
    print("Reading the post reqs (mappings) file.")
    reqs = _get_post_requests_from_file(mappings_filepath)
    print(f"Found {len(reqs)} post requests.")

    count = 1
    for req in reqs:
        print(f"*********** Downloading {count}  **********")
        _download_mapping_file(req, input_path, zip_download_path)
        count += 1
    print("Done downloading zip archives and data CSV files.")

    # Now processing the TMCF file along with the data CSV files.
    print("Starting to process the CSV files + eTMCF file.")
    count = 1
    for filename in os.listdir(input_path):
        if filename.startswith(".") or "csv" not in filename:
            continue

        print("**************************************************")
        print(
            f"   Processing: {count} - {filename} and {FLAGS.input_etmcf_filename}"
        )
        csv_filename = filename.replace(".csv", "")
        process_etmcf.process_enhanced_tmcf(
            input_path, output_path, FLAGS.input_etmcf_filename, csv_filename,
            FLAGS.input_etmcf_filename + "_processed",
            csv_filename.replace("$", "_") + "_processed")
        print("**************************************************")
        count += 1


if __name__ == '__main__':
    app.run(main)

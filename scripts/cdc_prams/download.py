# Copyright 2022 Google LLC
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
This Python Script downloads the datasets in a txt, zip format,
Unzips it and makes it available for further processing
"""
import io
import tabula as tb
import zipfile
import os
import requests


def download_file(input_url: list, download_directory: str) -> None:
    """
    Function to Download and Unzip the file provided in url

    Args: download_file_url: url of the file to be downloaded as a string

    Returns: None
    """
    # This extracts the filename from the complete URL,
    # also removes the .gz extension.
    # Example - ....national_household_travel_survey//hlth_ehis_bm1i.tsv.gz
    # is made hlth_ehis_bm1i.tsv.gz
    path = download_directory + os.sep + 'input_files'
    if not os.path.exists(path):
        os.mkdir(path)
    for download_file_url in input_url:
        # Example, file_name_with_compression_ext: NHTS_2009_transfer_AL.zip
        file_name_with_compression_ext = os.path.basename(download_file_url)
        # Example, file_name_without_compression_ext: NHTS_2009_transfer_AL.txt
        file_name_without_compression_ext = os.path.splitext(
            file_name_with_compression_ext)[0]
        out_file = path + os.sep + file_name_with_compression_ext
        print(download_file_url)
        req = requests.get(download_file_url)
        if not download_file_url.endswith(".zip"):
            with open(out_file, 'wb') as file:
                file.write(req.content)
        else:
            with zipfile.ZipFile(io.BytesIO(req.content)) as zipfileout:
                zipfileout.extractall(path)

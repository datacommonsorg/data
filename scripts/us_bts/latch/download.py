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
"""
This Python Script downloads the datasets in a txt, zip format,
Unzips it and makes it available for further processing
"""
import io
import os
import urllib
import gzip
import zipfile
import requests


def download_and_extract_files(input_urls: list,
                               download_directory: str) -> None:
    """
    Function to Download and Unzip the file provided in url.

    Args:
    input_urls (list): list of url of the files to be downloaded as a string
    download_directory (str): Download Directory
    """
    # This extracts the filename from the complete URL,
    # also removes the .gz extension.
    path = os.path.join(download_directory, 'input_files')
    os.makedirs(path, exist_ok=True)

    for download_file_url in input_urls:
        # Example, file_name_with_compression_ext: NHTS_2009_transfer_AL.zip
        #file_name_with_ext = os.path.basename(download_file_url)
        file_name_with_ext = download_file_url.split('/')[-1]
        # Example, file_name_without_compression_ext: NHTS_2009_transfer_AL.txt
        file_name_without_compression_ext = os.path.splitext(
            file_name_with_ext)[0]

        if ".zip" in file_name_with_ext:
            req = requests.get(download_file_url)
            with zipfile.ZipFile(io.BytesIO(req.content)) as zipfileout:
                zipfileout.extractall(path)

        elif ".gz" in file_name_with_ext:
            out_file = os.path.join(path, file_name_without_compression_ext)
            with urllib.request.urlopen(download_file_url) as response:
                with gzip.GzipFile(fileobj=response) as uncompressed:
                    file_content = uncompressed.read()
            with open(out_file, 'wb') as f:
                f.write(file_content)

        else:
            out_file = os.path.join(path, file_name_with_ext)
            req = requests.get(download_file_url)
            with open(out_file, 'wb') as file:
                file.write(req.content)

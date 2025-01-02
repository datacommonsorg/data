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
This Python Script downloads the datasets in a gzip format,
Unzips it and makes it available for further processing
"""
import gzip
import urllib.request
from absl import logging


def download_gz_file(download_file_url: str, download_path: str) -> None:
    """
    Function to download and unzip the file.

    Args:
        download_file_url (str): url of the file to be downloaded as a string
        download_path (str): local directory to download the file

    Returns:
        None
    """
    file_name = download_file_url.split("/")[-1][:-3].split("?")[0]
    output_file = download_path + "/" + file_name

    with urllib.request.urlopen(download_file_url) as response:
        with gzip.GzipFile(fileobj=response) as uncompressed:
            file_content = uncompressed.read()

    # write to file in binary mode 'wb'
    with open(output_file, 'wb') as f:
        f.write(file_content)


def download_files(download_files_url: list, download_path: str) -> None:
    """
    This Method calls the download function from the commons directory
    to download all the input files.

    Args:
        download_file_url (str): url of the file to be downloaded as a string
        download_path (str): local directory to download the file

    Returns:
        None
    """
    try:
        for download_file_url in download_files_url:
            download_gz_file(download_file_url, download_path)
    except Exception as e:
        logging.fatal(
            f'Download Error: {e} - URL - {download_file_url} path - {download_path}'
        )

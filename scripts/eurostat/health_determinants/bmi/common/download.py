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
import os
import urllib.request


def download_file(input_urls: list, download_directory: str) -> None:
    """
    Function to Download and Unzip the file provided in url

    Args: download_file_url: url of the file to be downloaded as a string

    Returns: None
    """
    # This extracts the filename from the complete URL,
    # also removes the .gz extension.
    # Example - ....-prod/BulkDownloadListing?file=data/hlth_ehis_bm1i.tsv.gz
    # is made hlth_ehis_bm1i.tsv.gz
    path = download_directory + os.sep + 'input_files'
    if not os.path.exists(path):
        os.mkdir(path)
    for download_file_url in input_urls:
        # Example, file_name_with_compression_ext: hlth_ehis_bm1i.tsv.gz
        file_name_with_compression_ext = os.path.basename(download_file_url)
        # Example, file_name_without_compression_ext: hlth_ehis_bm1i.tsv
        file_name_without_compression_ext = os.path.splitext(
            file_name_with_compression_ext)[0]
        out_file = path + os.sep + file_name_without_compression_ext

        with urllib.request.urlopen(download_file_url) as response:
            with gzip.GzipFile(fileobj=response) as uncompressed:
                file_content = uncompressed.read()

        # write to file in binary mode 'wb'
        with open(out_file, 'wb') as f:
            f.write(file_content)

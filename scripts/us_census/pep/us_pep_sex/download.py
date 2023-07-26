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
This Python Script downloads the US PEP files, into the input_files folder to be 
made available for further processing.
"""
import os
import urllib.request

_DOWNLOAD_PATH = os.path.join(os.path.dirname((__file__)), 'input_files')


def download_files() -> None:
    """
    This Method calls the download function from the commons directory
    to download all the input files.

    Args:
        None

    Returns:
        None
    """
    with open("scripts/us_census/pep/us_pep_sex/input_urls.txt",
              "r") as url_files:
        input_urls = url_files.readlines()
    if not os.path.exists(_DOWNLOAD_PATH):
        os.mkdir(_DOWNLOAD_PATH)
    os.chdir(_DOWNLOAD_PATH)

    for file in input_urls:
        file_name = file.split("/")[-1]
        urllib.request.urlretrieve(file, file_name)


if __name__ == '__main__':
    download_files()

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
This Python Script calls the download script in the common folder of eurostat,
the download script takes INPUT_URLs and current directory as input
and downloads the files.
"""
import os
import sys
import json
from absl import app

# pylint: disable=import-error
# pylint: disable=wrong-import-position
# For import common.download
_COMMON_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(1, _COMMON_PATH)
from download import download_file

_CODE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__)))
from constants import INPUT_URLS_CONFIG, BASE_URL, FILE_NAMES
# pylint: enable=import-error
# pylint: enable=wrong-import-position
_URLS_CONFIG_FILE = os.path.join(_CODE_DIR, INPUT_URLS_CONFIG)


def _create_urls() -> list:
    """
    Read URLS config file(input_urls_config.json) and creates list of
    urls to be downloaded.

    Returns:
        list: list of input urls.
    """
    urls_config = None
    with open(_URLS_CONFIG_FILE, "r", encoding="UTF-8") as config:
        urls_config = json.load(config)

    if urls_config is None:
        return []

    input_files_urls = []
    for year in urls_config.keys():
        conf = urls_config[year]
        base_url = conf[BASE_URL]
        file_names = conf[FILE_NAMES]
        input_files_urls += [
            base_url.format(file_name=file) for file in file_names
        ]
    return input_files_urls


def download_files(download_directory: str) -> None:
    """
    This Method calls the download function from the commons directory
    to download all the input files.

    Args:
        download_directory (str):Location where the files need to be downloaded.

    Returns:
        None
    """
    # List to provide the URLs of input files to download script.
    input_urls = _create_urls()
    download_file(input_urls, download_directory)


def main(_):
    download_files(_CODE_DIR)


if __name__ == '__main__':
    app.run(main)

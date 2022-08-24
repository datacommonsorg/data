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

from absl import app, flags

# pylint: disable=import-error
# pylint: disable=wrong-import-position
# For import common.download

_COMMON_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(1, _COMMON_PATH)
from common import import_download_details, download

# pylint: enable=import-error
# pylint: enable=wrong-import-position
_FLAGS = flags.FLAGS
flags.DEFINE_string("import_name", "alcohol_consumption",
                    "Import name for which input files will be downloaded")


def download_files(download_directory: str, filenames: str, input_url: str,
                   file_extension: str) -> None:
    """
    This Method calls the download function from the commons directory
    to download all the input files.

    Args:
        download_directory (str):Location where the files need to be downloaded.

    Returns:
        None
    """
    # pylint: disable=invalid-name
    for file in filenames:
        INPUT_URLS = [input_url + str(file) + file_extension]
        download.download_file(INPUT_URLS, download_directory)
    # pylint: enable=invalid-name


def main(_):
    download_details = import_download_details.download_details[
        _FLAGS.import_name]
    download_path = os.path.dirname((__file__)) + "/../" + _FLAGS.import_name
    download_files(download_path, download_details["filenames"],
                   download_details["input_url"],
                   download_details["file_extension"])


if __name__ == '__main__':
    app.run(main)

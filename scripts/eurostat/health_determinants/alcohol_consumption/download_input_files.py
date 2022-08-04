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
from common import download
# pylint: enable=import-error
# pylint: enable=wrong-import-position

_FLAGS = flags.FLAGS
flags.DEFINE_string("download_directory", os.path.dirname((__file__)),
                    "Directory path where input files need to be downloaded")


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
    filenames = [
        "al1e", "al1i", "al1u", "al3e", "al3i", "al3u", "al2e", "al2i", "al2u",
        "al1b", "al1c", "de10", "de6"
    ]
    # pylint: disable=invalid-name
    for file in filenames:
        INPUT_URLS = [
        "https://ec.europa.eu/eurostat/estat-navtree-portlet-prod/"+\
            "BulkDownloadListing?file=data/hlth_ehis_"+ str(file) + ".tsv.gz"]
        download.download_file(INPUT_URLS, download_directory)
    # pylint: enable=invalid-name


def main(_):
    download_files(_FLAGS.download_directory)


if __name__ == '__main__':
    app.run(main)

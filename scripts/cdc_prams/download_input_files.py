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
from absl import app, flags
from download import download_file

_FLAGS = flags.FLAGS
flags.DEFINE_string("download_directory", os.path.dirname((__file__)),
                    "Directory path where input files need to be downloaded")


def download_files(download_directory: str) -> None:
    '''
     This Method calls the download function from the commons directory
    to download all the input files.

    Args:
        download_directory (str):Location where the files need to be downloaded.

    Returns:
        None
    '''
    files = [
        'All-Sites-PRAMS-MCH-Indicators-508.pdf',
        'Alabama-PRAMS-MCH-Indicators-508.pdf',
        'Alaska-PRAMS-MCH-Indicators-508.pdf',
        'Arizona-PRAMS-MCH-Indicators-508.pdf',
        'Arkansas-PRAMS-MCH-Indicators-508.pdf',
        'Colorado-PRAMS-MCH-Indicators-508.pdf',
        'Connecticut-PRAMS-MCH-Indicators-508.pdf',
        'Delaware-PRAMS-MCH-Indicators-508.pdf',
        'District-Columbia-PRAMS-MCH-Indicators-508.pdf',
        'Florida-PRAMS-MCH-Indicators-508.pdf',
        'Georgia-PRAMS-MCH-Indicators-508.pdf',
        'Hawaii-PRAMS-MCH-Indicators-508.pdf',
        'Illinois-PRAMS-MCH-Indicators-508.pdf',
        'Indiana-PRAMS-MCH-Indicators-508.pdf',
        'Iowa-PRAMS-MCH-Indicators-508.pdf',
        'Kansas-PRAMS-MCH-Indicators-508.pdf',
        'Kentucky-PRAMS-MCH-Indicators-508.pdf',
        'Louisiana-PRAMS-MCH-Indicators-508.pdf',
        'Maine-PRAMS-MCH-Indicators-508.pdf',
        'Maryland-PRAMS-MCH-Indicators-508.pdf',
        'Massachusetts-PRAMS-MCH-Indicators-508.pdf',
        'Michigan-PRAMS-MCH-Indicators-508.pdf',
        'Minnesota-PRAMS-MCH-Indicators-508.pdf',
        'Mississippi-PRAMS-MCH-Indicators-508.pdf',
        'Missouri-PRAMS-MCH-Indicators-508.pdf',
        'Montana-PRAMS-MCH-Indicators-508.pdf',
        'Nebraska-PRAMS-MCH-Indicators-508.pdf',
        'New-Hampshire-PRAMS-MCH-Indicators-508.pdf',
        'New-Jersey-PRAMS-MCH-Indicators-508.pdf',
        'New-Mexico-PRAMS-MCH-Indicators-508.pdf',
        'New-York-City-PRAMS-MCH-Indicators-508.pdf',
        'New-York-PRAMS-MCH-Indicators-508.pdf',
        'North-Carolina-PRAMS-MCH-Indicators-508.pdf',
        'North-Dakota-PRAMS-MCH-Indicators-508.pdf',
        'Oklahoma-PRAMS-MCH-Indicators-508.pdf',
        'Oregon-PRAMS-MCH-Indicators-508.pdf',
        'Pennsylvania-PRAMS-MCH-Indicators-508.pdf',
        'Puerto-Rico-PRAMS-MCH-Indicators-508.pdf',
        'Rhode-Island-PRAMS-MCH-Indicators-508.pdf',
        'South-Dakota-PRAMS-MCH-Indicators-508.pdf',
        'Tennessee-PRAMS-MCH-Indicators-508.pdf',
        'Texas-PRAMS-MCH-Indicators-508.pdf',
        'Utah-PRAMS-MCH-Indicators-508.pdf',
        'Vermont-PRAMS-MCH-Indicators-508.pdf',
        'Virginia-PRAMS-MCH-Indicators-508.pdf',
        'Washington-PRAMS-MCH-Indicators-508.pdf',
        'West-Virginia-PRAMS-MCH-Indicators-508.pdf',
        'Wisconsin-PRAMS-MCH-Indicators-508.pdf',
        'Wyoming-PRAMS-MCH-Indicators-508.pdf'
    ]
    INPUT_URL = [
        'https://www.cdc.gov/prams/prams-data/mch-indicators/states/pdf/2020/' +
        file for file in files
    ]
    download_file(INPUT_URL, download_directory)


def main(_):
    download_files(_FLAGS.download_directory)


if __name__ == '__main__':
    app.run(main)

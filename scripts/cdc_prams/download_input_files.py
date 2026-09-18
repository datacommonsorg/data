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
This Python script downloads CDC PRAMS MCH Indicators PDF reports for
all states and national/territory sites.
"""
import os
import sys
from absl import app, flags

_CODEDIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _CODEDIR)

from download import download_file

_FLAGS = flags.FLAGS
flags.DEFINE_string(
    "download_directory", _CODEDIR,
    "Directory path where input_files/ folder will be populated")
flags.DEFINE_string("year", "2020", "Data release year to download")
flags.DEFINE_boolean("overwrite", False,
                     "Whether to force re-download existing files")

FILES = [
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
    'Indiana-PRAMS-MCH-Indicators-508.pdf', 'Iowa-PRAMS-MCH-Indicators-508.pdf',
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
    'Texas-PRAMS-MCH-Indicators-508.pdf', 'Utah-PRAMS-MCH-Indicators-508.pdf',
    'Vermont-PRAMS-MCH-Indicators-508.pdf',
    'Virginia-PRAMS-MCH-Indicators-508.pdf',
    'Washington-PRAMS-MCH-Indicators-508.pdf',
    'West-Virginia-PRAMS-MCH-Indicators-508.pdf',
    'Wisconsin-PRAMS-MCH-Indicators-508.pdf',
    'Wyoming-PRAMS-MCH-Indicators-508.pdf'
]


def download_files(download_directory: str,
                   year: str = "2020",
                   overwrite: bool = False) -> None:
    """
    Downloads all PRAMS indicator PDFs for the given year.

    Args:
        download_directory (str): Base directory where input_files will be saved.
        year (str): Data release year.
        overwrite (bool): If True, re-downloads existing files.
    """
    base_url = f"https://www.cdc.gov/prams/prams-data/mch-indicators/states/pdf/{year}/"
    input_urls = [base_url + f for f in FILES]
    download_file(input_urls, download_directory, overwrite=overwrite)


def main(_):
    download_files(_FLAGS.download_directory,
                   year=_FLAGS.year,
                   overwrite=_FLAGS.overwrite)


if __name__ == '__main__':
    app.run(main)

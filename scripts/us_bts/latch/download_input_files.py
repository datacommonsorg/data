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
from download import download_file
# pylint: enable=import-error
# pylint: enable=wrong-import-position

_FLAGS = flags.FLAGS
flags.DEFINE_string("download_directory", os.path.dirname((__file__)),
                    "Directory path where input files need to be downloaded")

STATE_2009_BASE_URL = ('https://www.bts.dot.gov/sites/bts.dot.gov/files/legacy/'
                       'subject_areas/national_household_travel_survey/')

_STATE_2009_NAMES = [
    'NHTS_2009_transfer_AL.zip', 'NHTS_2009_transfer_AK.zip',
    'NHTS_2009_transfer_AZ.zip', 'NHTS_2009_transfer_AR.zip',
    'NHTS_2009_transfer_CA.zip', 'NHTS_2009_transfer_CO.zip',
    'NHTS_2009_transfer_CT.zip', 'NHTS_2009_transfer_DE.zip',
    'NHTS_2009_transfer_DC.zip', 'NHTS_2009_transfer_FL.zip',
    'NHTS_2009_transfer_GA.zip', 'NHTS_2009_transfer_HI.zip',
    'NHTS_2009_transfer_ID.zip', 'NHTS_2009_transfer_IL.zip',
    'NHTS_2009_transfer_IN.zip', 'NHTS_2009_transfer_IA.zip',
    'NHTS_2009_transfer_KS.zip', 'NHTS_2009_transfer_KY.zip',
    'NHTS_2009_transfer_LA.zip', 'NHTS_2009_transfer_ME.zip',
    'NHTS_2009_transfer_MD.zip', 'NHTS_2009_transfer_MA.zip',
    'NHTS_2009_transfer_MI.zip', 'NHTS_2009_transfer_MN.zip',
    'NHTS_2009_transfer_MS.zip', 'NHTS_2009_transfer_MO.zip',
    'NHTS_2009_transfer_MT.zip', 'NHTS_2009_transfer_ND.zip',
    'NHTS_2009_transfer_NE.zip', 'NHTS_2009_transfer_NV.zip',
    'NHTS_2009_transfer_NH.zip', 'NHTS_2009_transfer_NJ.zip',
    'NHTS_2009_transfer_NM.zip', 'NHTS_2009_transfer_NY.zip',
    'NHTS_2009_transfer_NC.zip', 'NHTS_2009_transfer_NC.zip',
    'NHTS_2009_transfer_OH.zip', 'NHTS_2009_transfer_OK.zip',
    'NHTS_2009_transfer_OR.zip', 'NHTS_2009_transfer_PA.zip',
    'NHTS_2009_transfer_RI.zip', 'NHTS_2009_transfer_SC.zip',
    'NHTS_2009_transfer_SD.zip', 'NHTS_2009_transfer_TN.zip',
    'NHTS_2009_transfer_TX.zip', 'NHTS_2009_transfer_UT.zip',
    'NHTS_2009_transfer_VT.zip', 'NHTS_2009_transfer_VA.zip',
    'NHTS_2009_transfer_WA.zip', 'NHTS_2009_transfer_WV.zip',
    'NHTS_2009_transfer_WI.zip', 'NHTS_2009_transfer_WY.zip'
]

_STATES_2009_URLS = [
    STATE_2009_BASE_URL.format(state=state) for state in _STATE_2009_NAMES
]

_STATES_2017_URLS = [
    "https://www.bts.dot.gov/sites/bts.dot.gov/files/nhts2017/latch_2017-b.csv"
]


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
    input_urls = _STATES_2009_URLS + _STATES_2017_URLS
    download_file(input_urls, download_directory)


def main(_):
    download_files(_FLAGS.download_directory)


if __name__ == '__main__':
    app.run(main)

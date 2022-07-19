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

# pylint: disable=line-too-long
_STATES_2009_URLS = [
    'https://www.bts.dot.gov/sites/bts.dot.gov/files/legacy/subject_areas/national_household_travel_survey/NHTS_2009_transfer_AL.zip',
    'https://www.bts.dot.gov/sites/bts.dot.gov/files/legacy/subject_areas/national_household_travel_survey/NHTS_2009_transfer_AK.zip',
    'https://www.bts.dot.gov/sites/bts.dot.gov/files/legacy/subject_areas/national_household_travel_survey/NHTS_2009_transfer_AZ.zip',
    'https://www.bts.dot.gov/sites/bts.dot.gov/files/legacy/subject_areas/national_household_travel_survey/NHTS_2009_transfer_AR.zip',
    'https://www.bts.dot.gov/sites/bts.dot.gov/files/legacy/subject_areas/national_household_travel_survey/NHTS_2009_transfer_CA.zip',
    'https://www.bts.dot.gov/sites/bts.dot.gov/files/legacy/subject_areas/national_household_travel_survey/NHTS_2009_transfer_CO.zip',
    'https://www.bts.dot.gov/sites/bts.dot.gov/files/legacy/subject_areas/national_household_travel_survey/NHTS_2009_transfer_CT.zip',
    'https://www.bts.dot.gov/sites/bts.dot.gov/files/legacy/subject_areas/national_household_travel_survey/NHTS_2009_transfer_DE.zip',
    'https://www.bts.dot.gov/sites/bts.dot.gov/files/legacy/subject_areas/national_household_travel_survey/NHTS_2009_transfer_DC.zip',
    'https://www.bts.dot.gov/sites/bts.dot.gov/files/legacy/subject_areas/national_household_travel_survey/NHTS_2009_transfer_FL.zip',
    'https://www.bts.dot.gov/sites/bts.dot.gov/files/legacy/subject_areas/national_household_travel_survey/NHTS_2009_transfer_GA.zip',
    'https://www.bts.dot.gov/sites/bts.dot.gov/files/legacy/subject_areas/national_household_travel_survey/NHTS_2009_transfer_HI.zip',
    'https://www.bts.dot.gov/sites/bts.dot.gov/files/legacy/subject_areas/national_household_travel_survey/NHTS_2009_transfer_ID.zip',
    'https://www.bts.dot.gov/sites/bts.dot.gov/files/legacy/subject_areas/national_household_travel_survey/NHTS_2009_transfer_IL.zip',
    'https://www.bts.dot.gov/sites/bts.dot.gov/files/legacy/subject_areas/national_household_travel_survey/NHTS_2009_transfer_IN.zip',
    'https://www.bts.dot.gov/sites/bts.dot.gov/files/legacy/subject_areas/national_household_travel_survey/NHTS_2009_transfer_IA.zip',
    'https://www.bts.dot.gov/sites/bts.dot.gov/files/legacy/subject_areas/national_household_travel_survey/NHTS_2009_transfer_KS.zip',
    'https://www.bts.dot.gov/sites/bts.dot.gov/files/legacy/subject_areas/national_household_travel_survey/NHTS_2009_transfer_KY.zip',
    'https://www.bts.dot.gov/sites/bts.dot.gov/files/legacy/subject_areas/national_household_travel_survey/NHTS_2009_transfer_LA.zip',
    'https://www.bts.dot.gov/sites/bts.dot.gov/files/legacy/subject_areas/national_household_travel_survey/NHTS_2009_transfer_ME.zip',
    'https://www.bts.dot.gov/sites/bts.dot.gov/files/legacy/subject_areas/national_household_travel_survey/NHTS_2009_transfer_MD.zip',
    'https://www.bts.dot.gov/sites/bts.dot.gov/files/legacy/subject_areas/national_household_travel_survey/NHTS_2009_transfer_MA.zip',
    'https://www.bts.dot.gov/sites/bts.dot.gov/files/legacy/subject_areas/national_household_travel_survey/NHTS_2009_transfer_MI.zip',
    'https://www.bts.dot.gov/sites/bts.dot.gov/files/legacy/subject_areas/national_household_travel_survey/NHTS_2009_transfer_MN.zip',
    'https://www.bts.dot.gov/sites/bts.dot.gov/files/legacy/subject_areas/national_household_travel_survey/NHTS_2009_transfer_MS.zip',
    'https://www.bts.dot.gov/sites/bts.dot.gov/files/legacy/subject_areas/national_household_travel_survey/NHTS_2009_transfer_MO.zip',
    'https://www.bts.dot.gov/sites/bts.dot.gov/files/legacy/subject_areas/national_household_travel_survey/NHTS_2009_transfer_MT.zip',
    'https://www.bts.dot.gov/sites/bts.dot.gov/files/legacy/subject_areas/national_household_travel_survey/NHTS_2009_transfer_ND.zip',
    'https://www.bts.dot.gov/sites/bts.dot.gov/files/legacy/subject_areas/national_household_travel_survey/NHTS_2009_transfer_NE.zip',
    'https://www.bts.dot.gov/sites/bts.dot.gov/files/legacy/subject_areas/national_household_travel_survey/NHTS_2009_transfer_NV.zip',
    'https://www.bts.dot.gov/sites/bts.dot.gov/files/legacy/subject_areas/national_household_travel_survey/NHTS_2009_transfer_NH.zip',
    'https://www.bts.dot.gov/sites/bts.dot.gov/files/legacy/subject_areas/national_household_travel_survey/NHTS_2009_transfer_NJ.zip',
    'https://www.bts.dot.gov/sites/bts.dot.gov/files/legacy/subject_areas/national_household_travel_survey/NHTS_2009_transfer_NM.zip',
    'https://www.bts.dot.gov/sites/bts.dot.gov/files/legacy/subject_areas/national_household_travel_survey/NHTS_2009_transfer_NY.zip',
    'https://www.bts.dot.gov/sites/bts.dot.gov/files/legacy/subject_areas/national_household_travel_survey/NHTS_2009_transfer_NC.zip',
    'https://www.bts.dot.gov/sites/bts.dot.gov/files/legacy/subject_areas/national_household_travel_survey/NHTS_2009_transfer_NC.zip',
    'https://www.bts.dot.gov/sites/bts.dot.gov/files/legacy/subject_areas/national_household_travel_survey/NHTS_2009_transfer_OH.zip',
    'https://www.bts.dot.gov/sites/bts.dot.gov/files/legacy/subject_areas/national_household_travel_survey/NHTS_2009_transfer_OK.zip',
    'https://www.bts.dot.gov/sites/bts.dot.gov/files/legacy/subject_areas/national_household_travel_survey/NHTS_2009_transfer_OR.zip',
    'https://www.bts.dot.gov/sites/bts.dot.gov/files/legacy/subject_areas/national_household_travel_survey/NHTS_2009_transfer_PA.zip',
    'https://www.bts.dot.gov/sites/bts.dot.gov/files/legacy/subject_areas/national_household_travel_survey/NHTS_2009_transfer_RI.zip',
    'https://www.bts.dot.gov/sites/bts.dot.gov/files/legacy/subject_areas/national_household_travel_survey/NHTS_2009_transfer_SC.zip',
    'https://www.bts.dot.gov/sites/bts.dot.gov/files/legacy/subject_areas/national_household_travel_survey/NHTS_2009_transfer_SD.zip',
    'https://www.bts.dot.gov/sites/bts.dot.gov/files/legacy/subject_areas/national_household_travel_survey/NHTS_2009_transfer_TN.zip',
    'https://www.bts.dot.gov/sites/bts.dot.gov/files/legacy/subject_areas/national_household_travel_survey/NHTS_2009_transfer_TX.zip',
    'https://www.bts.dot.gov/sites/bts.dot.gov/files/legacy/subject_areas/national_household_travel_survey/NHTS_2009_transfer_UT.zip',
    'https://www.bts.dot.gov/sites/bts.dot.gov/files/legacy/subject_areas/national_household_travel_survey/NHTS_2009_transfer_VT.zip',
    'https://www.bts.dot.gov/sites/bts.dot.gov/files/legacy/subject_areas/national_household_travel_survey/NHTS_2009_transfer_VA.zip',
    'https://www.bts.dot.gov/sites/bts.dot.gov/files/legacy/subject_areas/national_household_travel_survey/NHTS_2009_transfer_WA.zip',
    'https://www.bts.dot.gov/sites/bts.dot.gov/files/legacy/subject_areas/national_household_travel_survey/NHTS_2009_transfer_WV.zip',
    'https://www.bts.dot.gov/sites/bts.dot.gov/files/legacy/subject_areas/national_household_travel_survey/NHTS_2009_transfer_WI.zip',
    'https://www.bts.dot.gov/sites/bts.dot.gov/files/legacy/subject_areas/national_household_travel_survey/NHTS_2009_transfer_WY.zip'
]
# pylint: enable=line-too-long

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

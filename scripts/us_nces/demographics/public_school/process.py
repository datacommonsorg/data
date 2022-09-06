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
This Python Script Load the datasets, cleans it
and generates cleaned CSV, MCF, TMCF file.
Before running this module, run download_input_files.py script, it downloads
required input files, creates necessary folders for processing.
Folder information
input_files - downloaded files (from US nces website) are placed here
output_files - output files (mcf, tmcf and csv are written here)
"""

import os
import sys

MODULE_DIR = os.path.dirname(__file__)
sys.path.insert(1, MODULE_DIR + '/../..')
# pylint:disable=wrong-import-position
# pylint:disable=import-error
# pylint:disable=wildcard-import
from common.us_education import USEducation
from config import *
# pylint:enable=wrong-import-position
# pylint:enable=import-error
# pylint:disable=wildcard-import

class NCESPublicSchool(USEducation):
    """
    This Class has requried methods to generate Cleaned CSV,
    MCF and TMCF Files.
    """
    _school_type = SCHOOL_TYPE
    _split_headers_using_school_type = SPLIT_HEADER_ON_SCHOOL_TYPE

if __name__ == '__main__':
    input_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                              "input_files")
    ip_files = os.listdir(input_path)
    ip_files = [input_path + os.sep + file for file in ip_files if file != ".DS_Store"]

    # Defining Output Files
    data_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                  "output_files")

    cleaned_csv_path = os.path.join(data_file_path, CSV_FILE_NAME)
    mcf_path = os.path.join(data_file_path, MCF_FILE_NAME)
    tmcf_path = os.path.join(data_file_path, TMCF_FILE_NAME)

    loader = NCESPublicSchool(ip_files, cleaned_csv_path, mcf_path, tmcf_path)
    print(loader.generate_csv())
    # loader.generate_mcf()
    # loader.generate_tmcf()
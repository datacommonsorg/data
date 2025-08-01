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
from absl import flags
from absl import app
from absl import logging

MODULE_DIR = os.path.dirname(__file__)
sys.path.insert(1, MODULE_DIR + '/../..')
from common.us_education import USEducation
from config import *


class NCESPublicSchool(USEducation):
    """
    This Class has requried methods to generate Cleaned CSV,
    MCF and TMCF Files.
    """
    _import_name = SCHOOL_TYPE
    _split_headers_using_school_type = SPLIT_HEADER_ON_SCHOOL_TYPE
    _exclude_columns = EXCLUDE_DATA_COLUMNS
    _include_columns = POSSIBLE_DATA_COLUMNS
    _include_col_place = POSSIBLE_PLACE_COLUMNS
    _exclude_col_place = EXCLUDE_PLACE_COLUMNS
    _observation_period = OBSERVATION_PERIOD
    _key_col_place = PLACE_KEY_COLUMNS
    _exclude_list = EXCLUDE_LIST
    _school_id = DROP_BY_VALUE
    _renaming_columns = RENAMING_PUBLIC_COLUMNS


if __name__ == '__main__':
    try:
        logging.set_verbosity(1)
        logging.info("Main Method Starts For Public School District ")
        gcs_output_dir_local = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "gcs_output")
        input_path_base = os.path.join(gcs_output_dir_local, "input_files")
        os.makedirs(input_path_base, exist_ok=True)
        input_files_to_process = []
        if os.path.exists(input_path_base):
            for year_folder_name in sorted(os.listdir(input_path_base)):
                year_folder_path = os.path.join(input_path_base,
                                                year_folder_name)
                if os.path.isdir(year_folder_path):
                    for file_name in sorted(os.listdir(year_folder_path)):
                        full_file_path = os.path.join(year_folder_path,
                                                      file_name)
                        input_files_to_process.append(full_file_path)

        if not input_files_to_process:
            logging.warning(
                f"No CSV files found in {input_path_base} or its year subfolders. Please ensure download_input_files.py has been run and placed files correctly."
            )
        output_file_path = os.path.join(gcs_output_dir_local, "output_files")
        os.makedirs(output_file_path, exist_ok=True)

        output_file_path_place = os.path.join(gcs_output_dir_local,
                                              "output_place")
        os.makedirs(output_file_path_place, exist_ok=True)

        cleaned_csv_path = os.path.join(output_file_path, CSV_FILE_NAME)
        mcf_path = os.path.join(output_file_path, MCF_FILE_NAME)
        tmcf_path = os.path.join(output_file_path, TMCF_FILE_NAME)
        csv_path_place = os.path.join(output_file_path_place, CSV_FILE_PLACE)
        duplicate_csv_place = os.path.join(output_file_path_place,
                                           CSV_DUPLICATE_NAME)
        tmcf_path_place = os.path.join(output_file_path_place, TMCF_FILE_PLACE)

        loader = NCESPublicSchool(input_files_to_process, cleaned_csv_path,
                                  mcf_path, tmcf_path, csv_path_place,
                                  duplicate_csv_place, tmcf_path_place)
        loader.generate_csv()
        loader.generate_mcf()
        loader.generate_tmcf()
        logging.info("Main Method Completed For Public School District ")

    except Exception as e:
        logging.fatal(f"Error While Running Public School Process: {e} ")

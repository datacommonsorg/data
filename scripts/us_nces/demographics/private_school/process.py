# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
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
import warnings
from absl import app, flags, logging

warnings.simplefilter(action='ignore', category=FutureWarning)
warnings.simplefilter(action='ignore', category=DeprecationWarning)

MODULE_DIR = os.path.dirname(__file__)
sys.path.insert(1, MODULE_DIR + '/../..')
from common.us_education import USEducation
from config import *

# Define Flags
FLAGS = flags.FLAGS
flags.DEFINE_bool('stats', False, 'Generate Stats data (CSV, MCF, TMCF).')
flags.DEFINE_bool('place', False, 'Generate Place data (CSV, TMCF).')


class NCESPrivateSchool(USEducation):
    """
    This Class has required methods to generate Cleaned CSV,
    MCF and TMCF Files.
    """
    _import_name = SCHOOL_TYPE
    _split_headers_using_school_type = SPLIT_HEADER_ON_SCHOOL_TYPE
    _include_columns = POSSIBLE_DATA_COLUMNS
    _exclude_columns = EXCLUDE_DATA_COLUMNS
    _include_col_place = POSSIBLE_PLACE_COLUMNS
    _exclude_col_place = EXCLUDE_PLACE_COLUMNS
    _generate_statvars = True
    _observation_period = OBSERVATION_PERIOD
    _exclude_list = EXCLUDE_LIST
    _school_id = DROP_BY_VALUE
    _renaming_columns = RENAMING_PRIVATE_COLUMNS

    def set_include_columns(self, columns: list):
        self._include_columns = columns

    def set_exclude_columns(self, columns: list):
        self._exclude_columns = columns

    def set_generate_statvars_flag(self, flag: bool):
        self._generate_statvars = flag


def main(argv):
    # Flag Validation: Throw error if no flags are used
    if not FLAGS.stats and not FLAGS.place:
        raise app.UsageError(
            "No execution flag provided. You must specify either --stats or --place."
        )

    try:
        logging.set_verbosity(logging.INFO)
        logging.info("Main Method Starts For Private School District")

        # Path Setup
        gcs_output_dir_local = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "gcs_folder")
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
                f"No CSV files found in {input_path_base}. Ensure download_input_files.py was run."
            )

        # Output Directories
        output_file_path = os.path.join(gcs_output_dir_local, "output_files")
        os.makedirs(output_file_path, exist_ok=True)

        output_file_path_place = os.path.join(gcs_output_dir_local,
                                              "output_place")
        os.makedirs(output_file_path_place, exist_ok=True)

        # File Paths
        cleaned_csv_path = os.path.join(output_file_path, CSV_FILE_NAME)
        mcf_path = os.path.join(output_file_path, MCF_FILE_NAME)
        tmcf_path = os.path.join(output_file_path, TMCF_FILE_NAME)
        cleaned_csv_place = os.path.join(output_file_path_place, CSV_FILE_PLACE)
        duplicate_csv_place = os.path.join(output_file_path_place,
                                           CSV_DUPLICATE_NAME)
        tmcf_path_place = os.path.join(output_file_path_place, TMCF_FILE_PLACE)

        # Initialize Loader
        loader = NCESPrivateSchool(input_files_to_process, cleaned_csv_path,
                                   mcf_path, tmcf_path, cleaned_csv_place,
                                   duplicate_csv_place, tmcf_path_place)

        # Conditional Execution based on flags
        if FLAGS.stats:
            logging.info("Triggering Stats Import...")
            loader.set_generate_statvars_flag(True)
            loader.generate_csv()
            loader.generate_mcf()
            loader.generate_tmcf()

        if FLAGS.place:
            logging.info("Triggering Place Import...")
            # Disable statvars so processing focuses on entity/place data
            loader.set_generate_statvars_flag(False)
            loader.generate_csv()
            loader.generate_tmcf()

        logging.info("Main Method Completed For Private School District")

    except Exception as e:
        logging.fatal(f"Error While Running Private School Process: {e}", exc_info=True)


if __name__ == '__main__':
    app.run(main)

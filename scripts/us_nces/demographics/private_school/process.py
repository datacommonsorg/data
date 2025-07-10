# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
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
import shutil
import sys
from absl import flags
from absl import app
from absl import logging
import warnings

warnings.simplefilter(action='ignore', category=FutureWarning)
warnings.simplefilter(action='ignore', category=DeprecationWarning)
warnings.simplefilter(action='ignore', category=FutureWarning)
MODULE_DIR = os.path.dirname(__file__)
sys.path.insert(1, MODULE_DIR + '/../..')
from common.us_education import USEducation
from config import *
from google.cloud import storage
from urllib.parse import urlparse

_FLAGS = flags.FLAGS
flags.DEFINE_string('project_id', 'datcom-204919',
                    'The Google Cloud project ID.')
flags.DEFINE_string(
    'gcs_input_file_path',
    'gs://unresolved_mcf/us_nces/demographics/private_school/semi_automation_input_files',
    'Path to gcs bucket')

class NCESPrivateSchool(USEducation):
    """
    This Class has requried methods to generate Cleaned CSV,
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


def main(_):
    try:
        logging.info("Main Method Starts For Private School ")

        # Get the full GCS URI from the flag
        full_gcs_uri = _FLAGS.gcs_input_file_path

        # Use urlparse to extract bucket_name and gcs_base_path (path within the bucket)
        parsed_uri = urlparse(full_gcs_uri)
        bucket_name = parsed_uri.netloc
        gcs_base_path = parsed_uri.path.lstrip('/')
        # Now you can use these derived variables
        storage_client = storage.Client(project=_FLAGS.project_id)
        input_files_to_process = []
        year_prefixes = set()
        blobs_and_prefixes = storage_client.list_blobs(bucket_name,
                                                       prefix=gcs_base_path +
                                                       '/',
                                                       delimiter='/')

        for page in blobs_and_prefixes.pages:
            if page.prefixes:  # Check if there are any prefixes (year folders) on this page
                for prefix in page.prefixes:
                    year_prefixes.add(prefix)

        # This `if` statement covers the "FIRST IF" scenario for GCP:
        # If no year folders (prefixes) were found under gcs_base_path, it means the "base directory" is empty or doesn't have expected subfolders.
        if year_prefixes:
            for year_prefix in sorted(list(year_prefixes)):
                # The very fact that `year_prefix` came from `page.prefixes` means it's a directory-like structure.
                # So, the "SECOND IF" (if os.path.isdir(year_folder_path)) is implicitly handled by the nature of `year_prefix`.
                logging.info(
                    f"Checking GCP path: gs://{bucket_name}/{year_prefix}")

                files_in_year_folder = storage_client.list_blobs(
                    bucket_name, prefix=year_prefix)

                for blob in files_in_year_folder:
                    if blob.name.endswith('.csv') and blob.name != year_prefix:
                        full_gcs_file_path = f"gs://{bucket_name}/{blob.name}"
                        input_files_to_process.append(full_gcs_file_path)
                        logging.info(f"Found file: {full_gcs_file_path}")
        else:
            logging.warning(
                f"No year subfolders found in gs://{bucket_name}/{gcs_base_path}. "
                "Please ensure files are correctly placed in the GCP bucket.")

        if not input_files_to_process:
            logging.warning(
                f"No CSV files found in gs://{bucket_name}/{gcs_base_path} or its year subfolders. "
                "Please ensure files are correctly placed in the GCP bucket.")
        output_file_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "output_files")
        os.makedirs(output_file_path, exist_ok=True)

        output_file_path_place = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "output_place")
        os.makedirs(output_file_path_place, exist_ok=True)

        cleaned_csv_path = os.path.join(output_file_path, CSV_FILE_NAME)
        mcf_path = os.path.join(output_file_path, MCF_FILE_NAME)
        tmcf_path = os.path.join(output_file_path, TMCF_FILE_NAME)
        cleaned_csv_place = os.path.join(output_file_path_place, CSV_FILE_PLACE)
        duplicate_csv_place = os.path.join(output_file_path_place,
                                           CSV_DUPLICATE_NAME)
        tmcf_path_place = os.path.join(output_file_path_place, TMCF_FILE_PLACE)

        # Pass the list of actual CSV file paths
        loader = NCESPrivateSchool(input_files_to_process, cleaned_csv_path,
                                   mcf_path, tmcf_path, cleaned_csv_place,
                                   duplicate_csv_place, tmcf_path_place)

        loader.generate_csv()
        loader.generate_mcf()
        loader.generate_tmcf()
        logging.info("Main Method Completed For Private School District ")
    except Exception as e:
        logging.fatal(f"Error While Running Private School Process: {e} ")

if __name__ == "__main__":
    app.run(main)

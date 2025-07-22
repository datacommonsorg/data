# Copyright 2020 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import unittest
import os
import pandas as pd
import tempfile
import sys

MODULE_DIR = os.path.dirname(__file__)
sys.path.insert(0, MODULE_DIR)
from preprocess_csv import process_data, generate_tmcf

sys.path.insert(1, os.path.join(MODULE_DIR, '../'))
from download import download_data_to_file_and_df

TEST_DATASET_DIR = os.path.join(MODULE_DIR, "test_data", "sample_data")

EXPECTED_FILES_DIR = os.path.join(MODULE_DIR, "test_data", "expected_files")


class TestProcess(unittest.TestCase):
    """
    TestPreprocess is inherting unittest class
    properties which further requried for unit testing.
    The test will be conducted for OECD Deaths Sample Datasets,
    It will be generating CSV and TMCF files based on the sample input.
    Comparing the data with the expected files.
    """

    @classmethod
    def setUpClass(cls):
        with tempfile.TemporaryDirectory() as tmp_dir:
            cls.cleaned_csv_file_path = os.path.join(tmp_dir, "data.csv")
            cls.tmcf_file_path = os.path.join(tmp_dir, "test_census.tmcf")

            input_file = os.path.join(TEST_DATASET_DIR, "data.csv")
            input_df = download_data_to_file_and_df('',
                                                    filename=False,
                                                    is_download_required=False,
                                                    csv_filepath=input_file)
            preprocess_df = process_data(input_df, cls.cleaned_csv_file_path)
            generate_tmcf(preprocess_df, cls.tmcf_file_path)

            with open(cls.tmcf_file_path, encoding="UTF-8") as tmcf_file:
                cls.actual_tmcf_data = tmcf_file.read()

            with open(cls.cleaned_csv_file_path,
                      encoding="utf-8-sig") as csv_file:
                cls.actual_csv_data = csv_file.read()

    def test_mcf_tmcf_files(self):
        """
        This method is required to test between output generated
        preprocess script and expected output files like MCF File
        """

        expected_tmcf_file_path = os.path.join(EXPECTED_FILES_DIR,
                                               "OECD_deaths_cleaned.tmcf")

        with open(expected_tmcf_file_path,
                  encoding="UTF-8") as expected_tmcf_file:
            expected_tmcf_data = expected_tmcf_file.read()

        self.assertEqual(expected_tmcf_data.strip(),
                         self.actual_tmcf_data.strip())

    def test_create_csv(self):
        """
        This method is required to test between output generated
        preprocess script and excepted output files like CSV
        """
        expected_csv_file_path = os.path.join(EXPECTED_FILES_DIR,
                                              "OECD_deaths_cleaned.csv")

        expected_csv_data = ""
        with open(expected_csv_file_path,
                  encoding="utf-8") as expected_csv_file:
            expected_csv_data = expected_csv_file.read()

        self.assertEqual(expected_csv_data.strip(),
                         self.actual_csv_data.strip())


if __name__ == '__main__':
    unittest.main()

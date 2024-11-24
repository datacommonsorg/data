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
Script to automate the testing for USA Population preprocess script.
"""

import os
import unittest
from os import path
from download import download
import pandas as pd
# module_dir_ is the path to where this test is running from.
module_dir_ = os.path.dirname(__file__)
_TEST_DATA_FOLDER = os.path.join(module_dir_, "test_data")
_OP_DATA_FOLDER = os.path.join(module_dir_, "test_output_data_download")


class TestPreprocess(unittest.TestCase):
    """
    TestPreprocess is inherting unittest class
    properties which further requried for unit testing
    """

    def test_create_xlsx(self):
        """
        This method is required to test between output generated
        preprocess script and excepted output files like XLSX
        """
        ip_data_path = [os.path.join(_TEST_DATA_FOLDER, "test_census_data.csv")]
        download(_OP_DATA_FOLDER, ip_data_path)
        expected_xlsx_file_path = os.path.join(
            _TEST_DATA_FOLDER, "download_expected_USA_Population_Count.xlsx")

        expected_df = pd.read_excel(expected_xlsx_file_path)
        actual_df = pd.read_excel(_OP_DATA_FOLDER + "/test_census_data.xlsx")

        if path.exists(_OP_DATA_FOLDER):
            os.remove(_OP_DATA_FOLDER)

        self.assertEqual(True, actual_df.equals(expected_df))

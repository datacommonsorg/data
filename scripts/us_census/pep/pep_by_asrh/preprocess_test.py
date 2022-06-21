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
import tempfile
from preprocess import process
# _MODULE_DIR is the path to where this test is running from.
_MODULE_DIR = os.path.dirname(__file__)
_TEST_DATA_FOLDER = os.path.join(_MODULE_DIR, "test_data")


class TestPreprocess(unittest.TestCase):
    """
    TestPreprocess is inherting unittest class
    properties which further requried for unit testing.
    The test will be conducted for US Census Sample Datasets,
    It will be generating CSV, MCF and TMCF files based on the sample input.
    Comparing the data with the expected files.
    """

    def __init__(self, methodName: str = ...) -> None:
        super().__init__(methodName)

        with tempfile.TemporaryDirectory() as tmp_dir:
            cleaned_csv_file_path = os.path.join(tmp_dir,
                                                 "test_output_data.csv")
            mcf_file_path = os.path.join(tmp_dir, "test_census.mcf")
            tmcf_file_path = os.path.join(tmp_dir, "test_census.tmcf")

            file_list = [
                'NC-EST2020_Nationals.csv', 'co-est00int-alldata_county.csv',
                'sasrh_state.txt'
            ]
            ip_data_path = [
                os.path.join(_TEST_DATA_FOLDER, "datasets", file_name)
                for file_name in file_list
            ]

            process(ip_data_path, cleaned_csv_file_path, mcf_file_path,
                    tmcf_file_path)

            with open(mcf_file_path, encoding="UTF-8") as mcf_file:
                self._actual_mcf_data = mcf_file.read()

            with open(tmcf_file_path, encoding="UTF-8") as tmcf_file:
                self._actual_tmcf_data = tmcf_file.read()

            with open(cleaned_csv_file_path, encoding="utf-8") as csv_file:
                self._actual_csv_data = csv_file.read()

    def test_mcf_tmcf_files(self):
        """
        This method is required to test between output generated
        preprocess script and excepted output files like MCF File
        """
        expected_mcf_file_path = os.path.join(
            _TEST_DATA_FOLDER, "expected_usa_population_asrh.mcf")

        expected_tmcf_file_path = os.path.join(
            _TEST_DATA_FOLDER, "expected_usa_population_asrh.tmcf")

        with open(expected_mcf_file_path,
                  encoding="UTF-8") as expected_mcf_file:
            expected_mcf_data = expected_mcf_file.read()

        with open(expected_tmcf_file_path,
                  encoding="UTF-8") as expected_tmcf_file:
            expected_tmcf_data = expected_tmcf_file.read()

        self.assertEqual(expected_mcf_data.strip(),
                         self._actual_mcf_data.strip())
        self.assertEqual(expected_tmcf_data.strip(),
                         self._actual_tmcf_data.strip())

    def test_create_csv(self):
        """
        This method is required to test between output generated
        preprocess script and excepted output files like CSV
        """
        expected_csv_file_path = os.path.join(
            _TEST_DATA_FOLDER, "expected_usa_population_asrh.csv")

        with open(expected_csv_file_path,
                  encoding="utf-8") as expected_csv_file:
            expected_csv_data = expected_csv_file.read()

        self.assertEqual(expected_csv_data.strip(),
                         self._actual_csv_data.strip())

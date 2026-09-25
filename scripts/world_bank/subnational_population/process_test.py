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
Script to automate the testing for EuroStat BMI process script.
"""

import os
import unittest
import sys
import tempfile
# module_dir is the path to where this test is running from.
MODULE_DIR = os.path.dirname(__file__)
sys.path.insert(0, MODULE_DIR)
# pylint: disable=wrong-import-position
from process import Subnational

sys.path.insert(1, MODULE_DIR + '/../../statvar')
#pylint:disable=wrong-import-position
#pylint:disable=import-error
#pylint:disable=wildcard-import
from mcf_diff import diff_mcf_files
from stat_var_processor import process

sys.path.insert(1, MODULE_DIR + '/../../../util')
from counters import Counters

# pylint: enable=wrong-import-position

TEST_DATASET_DIR = os.path.join(MODULE_DIR, "test_data", "datasets")
EXPECTED_FILES_DIR = os.path.join(MODULE_DIR, "test_data", "expected_files")


class TestProcess(unittest.TestCase):
    """
    TestPreprocess is inherting unittest class
    properties which further requried for unit testing.
    The test will be conducted for EuroStat BMI Sample Datasets,
    It will be generating CSV, MCF and TMCF files based on the sample input.
    Comparing the data with the expected files.
    """

    def __init__(self, methodName: str = ...) -> None:
        super().__init__(methodName)

        with tempfile.TemporaryDirectory() as tmp_dir:
            test_data_files = os.listdir(TEST_DATASET_DIR)
            ip_data = [
                os.path.join(TEST_DATASET_DIR, file_name)
                for file_name in test_data_files
            ]
            CLEANED_CSV_FILE_PATH = os.path.join(tmp_dir, "subnational.csv")
            MCF_FILE_PATH = os.path.join(tmp_dir, "subnational.mcf")
            TMCF_FILE_PATH = os.path.join(tmp_dir, "subnational.tmcf")
            output_path = os.path.join(tmp_dir, "subnational")

            _conf_path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)), "config.json")
            # The pv_map has Each column mapped to the desired property.
            # countrystatecode.json has the dcid mapping.
            _pv_map = [
                f'{MODULE_DIR}/pvmap.py',
                f'observationAbout:{MODULE_DIR}/countrystatecode.json',
            ]
            process(data_processor_class=Subnational,
                    input_data=ip_data,
                    output_path=output_path,
                    config_file=_conf_path,
                    pv_map_files=_pv_map)

            with open(MCF_FILE_PATH, encoding="UTF-8") as mcf_file:
                self.actual_mcf_data = mcf_file.read()[1:]

            with open(TMCF_FILE_PATH, encoding="UTF-8") as tmcf_file:
                self.actual_tmcf_data = tmcf_file.readlines()

            with open(CLEANED_CSV_FILE_PATH, encoding="utf-8-sig") as csv_file:
                self.actual_csv_data = csv_file.read()

    def test_mcf_tmcf_files(self):
        """
        This method is required to test between output generated
        preprocess script and excepted output files like MCF File
        """
        expected_mcf_file_path = os.path.join(EXPECTED_FILES_DIR,
                                              "subnational.mcf")
        with open(expected_mcf_file_path,
                  encoding="UTF-8") as expected_mcf_file:
            expected_mcf_data = expected_mcf_file.read()

        counters = Counters()
        diff_mcf = diff_mcf_files(expected_mcf_data, self.actual_mcf_data,
                                  {'show_diff_nodes_only': True}, counters)
        self.assertEqual(
            diff_mcf, '', f'Found diffs in MCF nodes:' +
            f'"{expected_mcf_data}" vs "{self.actual_mcf_data}":' +
            f'{diff_mcf}\nCounters: {counters.get_counters_string()}')
        # Creating expected tmcf file
        expected_tmcf_file_path = os.path.join(EXPECTED_FILES_DIR,
                                               "subnational.tmcf")
        with open(expected_tmcf_file_path,
                  encoding="UTF-8") as expected_tmcf_file:
            expected_tmcf_data = expected_tmcf_file.readlines()
        # Comparing the sorted expected file with temporary tmcf file.
        # The files are sorted because the order in the temporary tmcf file
        # changes every time the test is executed
        self.assertEqual(
            sorted(expected_tmcf_data), sorted(self.actual_tmcf_data),
            f'Mismatched actual:{expected_tmcf_data} expected:{self.actual_tmcf_data}'
        )

    def test_create_csv(self):
        """
        This method is required to test between output generated
        preprocess script and excepted output files like CSV
        """
        expected_csv_file_path = os.path.join(EXPECTED_FILES_DIR,
                                              "subnational.csv")

        expected_csv_data = ""
        with open(expected_csv_file_path,
                  encoding="utf-8") as expected_csv_file:
            expected_csv_data = expected_csv_file.read()

        self.assertEqual(expected_csv_data.strip(),
                         self.actual_csv_data.strip())


if __name__ == '__main__':
    unittest.main()
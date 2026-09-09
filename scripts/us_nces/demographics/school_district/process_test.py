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

import os
import unittest
from unittest.mock import patch
import sys
import tempfile
# module_dir is the path to where this test is running from.
MODULE_DIR = os.path.dirname(__file__)
sys.path.insert(0, MODULE_DIR)
# pylint: disable=wrong-import-position
from process import NCESDistrictSchool
# pylint: enable=wrong-import-position

TEST_DATASET_DIR = os.path.join(MODULE_DIR, "test_data", "sample_input")
EXPECTED_FILES_DIR = os.path.join(MODULE_DIR, "test_data", "sample_output")


class TestProcess(unittest.TestCase):
    """
    TestProcess inherits from unittest.TestCase.
    The test is conducted for NCES School District Demographic Sample Datasets.
    It generates CSV, MCF, and TMCF files based on sample inputs and compares
    the output with expected files.
    """
    test_data_files = os.listdir(TEST_DATASET_DIR)

    ip_data = [
        os.path.join(TEST_DATASET_DIR, file_name)
        for file_name in test_data_files
    ]

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._tmp_dir = tempfile.TemporaryDirectory()
        tmp_dir = cls._tmp_dir.name
        cleaned_csv_file_path = os.path.join(tmp_dir,
                                             "test_school_district.csv")
        mcf_file_path = os.path.join(tmp_dir, "test_school_district.mcf")
        tmcf_file_path = os.path.join(tmp_dir, "test_school_district.tmcf")
        csv_path_place = os.path.join(tmp_dir,
                                      "test_school_district_place.csv")
        tmcf_path_place = os.path.join(tmp_dir,
                                       "test_school_district_place.tmcf")
        dup_csv_path_place = os.path.join(
            tmp_dir, "test_school_district_place_dup.csv")

        loader = NCESDistrictSchool(cls.ip_data, cleaned_csv_file_path,
                                    mcf_file_path, tmcf_file_path,
                                    csv_path_place, dup_csv_path_place,
                                    tmcf_path_place)

        with patch(
                "common.us_education.dc_api_is_defined_dcid",
                side_effect=lambda nodes, *args, **kwargs:
            {n: True for n in nodes},
        ):
            loader.generate_csv()
            loader.generate_mcf()
            loader.generate_tmcf()

        with open(mcf_file_path, encoding="UTF-8") as mcf_file:
            cls.actual_mcf_data = mcf_file.read()

        with open(tmcf_file_path, encoding="UTF-8") as tmcf_file:
            cls.actual_tmcf_data = tmcf_file.read()

        with open(cleaned_csv_file_path, encoding="utf-8-sig") as csv_file:
            cls.actual_csv_data = csv_file.read()

        with open(tmcf_path_place, encoding="UTF-8") as tmcf_file:
            cls.actual_tmcf_place = tmcf_file.read()

        with open(csv_path_place, encoding="utf-8-sig") as csv_file:
            cls.actual_csv_place = csv_file.read()

    @classmethod
    def tearDownClass(cls):
        cls._tmp_dir.cleanup()
        super().tearDownClass()

    def test_mcf_tmcf_files(self):
        """
        This method is required to test between output generated
        preprocess script and expected output files like MCF File
        """
        expected_mcf_file_path = os.path.join(
            EXPECTED_FILES_DIR, "us_nces_demographics_district_school.mcf")

        expected_tmcf_file_path = os.path.join(
            EXPECTED_FILES_DIR, "us_nces_demographics_district_school.tmcf")

        expected_tmcf_place_path = os.path.join(
            EXPECTED_FILES_DIR, "us_nces_demographics_district_place.tmcf")

        with open(expected_mcf_file_path,
                  encoding="UTF-8") as expected_mcf_file:
            expected_mcf_data = expected_mcf_file.read()

        with open(expected_tmcf_file_path,
                  encoding="UTF-8") as expected_tmcf_file:
            expected_tmcf_data = expected_tmcf_file.read()

        with open(expected_tmcf_place_path,
                  encoding="UTF-8") as expected_tmcf_file_place:
            expected_tmcf_place = expected_tmcf_file_place.read()

        self.assertEqual(expected_mcf_data.strip(),
                         self.actual_mcf_data.strip())
        self.assertEqual(expected_tmcf_data.strip(),
                         self.actual_tmcf_data.strip())
        self.assertEqual(expected_tmcf_place.strip(),
                         self.actual_tmcf_place.strip())

    def test_create_csv(self):
        """
        This method is required to test between output generated
        preprocess script and expected output files like CSV
        """
        expected_csv_file_path = os.path.join(
            EXPECTED_FILES_DIR, "us_nces_demographics_district_school.csv")

        expected_csv_data = ""
        with open(expected_csv_file_path,
                  encoding="utf-8") as expected_csv_file:
            expected_csv_data = expected_csv_file.read()

        self.assertEqual(expected_csv_data.strip(),
                         self.actual_csv_data.strip())

        expected_csv_file_path = os.path.join(
            EXPECTED_FILES_DIR, "us_nces_demographics_district_place.csv")

        expected_csv_data = ""
        with open(expected_csv_file_path,
                  encoding="utf-8") as expected_csv_file:
            expected_csv_place = expected_csv_file.read()

        self.assertEqual(expected_csv_place.strip(),
                         self.actual_csv_place.strip())


if __name__ == '__main__':
    unittest.main()

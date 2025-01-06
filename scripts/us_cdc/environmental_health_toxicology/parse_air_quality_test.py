# Copyright 2021 Google LLC
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

from absl import logging
import parse_air_quality

_MODULE_DIR = os.path.dirname(__file__)
TEST_DATA_DIR = os.path.join(_MODULE_DIR, 'test_data')
INPUT_DIR = 'input_files'
OUTPUT_DIR = 'actual_output_files'
OUTPUT_FILES = 'expected_output_files'

# test data for each import type
TEST_DATA = {
    "CDC_OzoneCensusTract": {
        "input_dir":
            os.path.join(TEST_DATA_DIR, "CDC_OzoneCensusTract", INPUT_DIR),
        "output_dir":
            os.path.join(TEST_DATA_DIR, "CDC_OzoneCensusTract", OUTPUT_DIR),
        "expected_file":
            os.path.join(TEST_DATA_DIR, "CDC_OzoneCensusTract", OUTPUT_FILES,
                         "Census_Tract_Level_Ozone_Concentrations_0.csv"),
        "actual_file":
            os.path.join(TEST_DATA_DIR, "CDC_OzoneCensusTract", OUTPUT_DIR,
                         "Census_Tract_Level_Ozone_Concentrations_0.csv"),
    },
    "CDC_OzoneCounty": {
        "input_dir":
            os.path.join(TEST_DATA_DIR, "CDC_OzoneCounty", INPUT_DIR),
        "output_dir":
            os.path.join(TEST_DATA_DIR, "CDC_OzoneCounty", OUTPUT_DIR),
        "expected_file":
            os.path.join(TEST_DATA_DIR, "CDC_OzoneCounty", OUTPUT_FILES,
                         "OzoneCounty.csv"),
        "actual_file":
            os.path.join(TEST_DATA_DIR, "CDC_OzoneCounty", OUTPUT_DIR,
                         "OzoneCounty.csv"),
    },
    "CDC_PM25CensusTract": {
        "input_dir":
            os.path.join(TEST_DATA_DIR, "CDC_PM25CensusTract", INPUT_DIR),
        "output_dir":
            os.path.join(TEST_DATA_DIR, "CDC_PM25CensusTract", OUTPUT_DIR),
        "expected_file":
            os.path.join(TEST_DATA_DIR, "CDC_PM25CensusTract", OUTPUT_FILES,
                         "PM2.5CensusTract_0.csv"),
        "actual_file":
            os.path.join(TEST_DATA_DIR, "CDC_PM25CensusTract", OUTPUT_DIR,
                         "PM2.5CensusTract_0.csv"),
    },
    "CDC_PM25County": {
        "input_dir":
            os.path.join(TEST_DATA_DIR, "CDC_PM25County", INPUT_DIR),
        "output_dir":
            os.path.join(TEST_DATA_DIR, "CDC_PM25County", OUTPUT_DIR),
        "expected_file":
            os.path.join(TEST_DATA_DIR, "CDC_PM25County", OUTPUT_FILES,
                         "PM25county.csv"),
        "actual_file":
            os.path.join(TEST_DATA_DIR, "CDC_PM25County", OUTPUT_DIR,
                         "PM25county.csv"),
    },
}


class TestParseAirQuality(unittest.TestCase):

    def __init__(self, methodName: str = ...) -> None:
        super().__init__(methodName)

    def test_clean_air_quality_data(self):
        """
        Tests the clean_air_quality_data function for all the 4 imports.
        """
        for import_type, test_data in TEST_DATA.items():
            output_dir = test_data["output_dir"]
            os.makedirs(output_dir, exist_ok=True)

            paq.clean_air_quality_data(test_data["input_dir"],
                                       test_data["output_dir"], import_type)

            with open(test_data["actual_file"],
                      encoding="utf-8") as actual_csv_file:
                actual_csv_data = actual_csv_file.read().strip()

            with open(test_data["expected_file"],
                      encoding="utf-8") as expected_csv_file:
                expected_csv_data = expected_csv_file.read().strip()

            self.assertEqual(expected_csv_data, actual_csv_data)


if __name__ == '__main__':
    unittest.main()

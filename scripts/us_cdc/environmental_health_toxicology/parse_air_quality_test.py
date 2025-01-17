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
from .parse_air_quality import clean_air_quality_data

_MODULE_DIR = os.path.dirname(__file__)
TEST_DATA_DIR = os.path.join(_MODULE_DIR, 'test_data')
INPUT_DIR = 'input_files'
OUTPUT_DIR = 'actual_output_files'
OUTPUT_FILES = 'expected_output_files'

# test data for each import type
TEST_DATA = [{
    "import_name":
        "CDC_PM25CensusTract",
    "input_dir":
        os.path.join(TEST_DATA_DIR, "CDC_PM25CensusTract", INPUT_DIR),
    "output_dir":
        os.path.join(TEST_DATA_DIR, "CDC_PM25CensusTract", OUTPUT_DIR),
    "expected_file":
        os.path.join(TEST_DATA_DIR, "CDC_PM25CensusTract", OUTPUT_FILES,
                     "PM2.5CensusTract_0.csv"),
    "files": [{
        "input_file_name":
            "PM2.5CensusTractPollution_input_0.csv",
        "output_file_name":
            os.path.join(TEST_DATA_DIR, "CDC_PM25CensusTract", OUTPUT_DIR,
                         "PM2.5CensusTract_0.csv")
    }]
}, {
    "import_name":
        "CDC_OzoneCensusTract",
    "input_dir":
        os.path.join(TEST_DATA_DIR, "CDC_OzoneCensusTract", INPUT_DIR),
    "output_dir":
        os.path.join(TEST_DATA_DIR, "CDC_OzoneCensusTract", OUTPUT_DIR),
    "expected_file":
        os.path.join(TEST_DATA_DIR, "CDC_OzoneCensusTract", OUTPUT_FILES,
                     "Census_Tract_Level_Ozone_Concentrations_0.csv"),
    "files": [{
        "input_file_name":
            "Census_Tract_Level_Ozone_Concentrations_input_0.csv",
        "output_file_name":
            os.path.join(TEST_DATA_DIR, "CDC_OzoneCensusTract", OUTPUT_DIR,
                         "Census_Tract_Level_Ozone_Concentrations_0.csv")
    }]
}, {
    "import_name":
        "CDC_PM25County",
    "input_dir":
        os.path.join(TEST_DATA_DIR, "CDC_PM25County", INPUT_DIR),
    "output_dir":
        os.path.join(TEST_DATA_DIR, "CDC_PM25County", OUTPUT_DIR),
    "expected_file":
        os.path.join(TEST_DATA_DIR, "CDC_PM25County", OUTPUT_FILES,
                     "PM25county.csv"),
    "files": [{
        "input_file_name":
            "PM2.5County_input_0.csv",
        "output_file_name":
            os.path.join(TEST_DATA_DIR, "CDC_PM25County", OUTPUT_DIR,
                         "PM25county.csv")
    }]
}, {
    "import_name":
        "CDC_OzoneCounty",
    "input_dir":
        os.path.join(TEST_DATA_DIR, "CDC_OzoneCounty", INPUT_DIR),
    "output_dir":
        os.path.join(TEST_DATA_DIR, "CDC_OzoneCounty", OUTPUT_DIR),
    "expected_file":
        os.path.join(TEST_DATA_DIR, "CDC_OzoneCounty", OUTPUT_FILES,
                     "OzoneCounty.csv"),
    "files": [{
        "input_file_name":
            "OzoneCounty_input.csv",
        "output_file_name":
            os.path.join(TEST_DATA_DIR, "CDC_OzoneCounty", OUTPUT_DIR,
                         "OzoneCounty.csv"),
    }]
}]


class TestParseAirQuality(unittest.TestCase):

    def __init__(self, methodName: str = ...) -> None:
        super().__init__(methodName)

    def test_clean_air_quality_data(self):
        """
        Tests the clean_air_quality_data function for all the 4 imports.
        """
        for data in TEST_DATA:
            for data1 in data["files"]:
                output_dir = data["output_dir"]
                os.makedirs(output_dir, exist_ok=True)
                clean_air_quality_data(TEST_DATA, data["import_name"],
                                       data["input_dir"], output_dir)
                with open(data1["output_file_name"],
                          encoding="utf-8") as actual_csv_file:
                    actual_csv_data = actual_csv_file.read().strip()
                with open(data["expected_file"],
                          encoding="utf-8") as expected_csv_file:
                    expected_csv_data = expected_csv_file.read().strip()

                self.assertEqual(expected_csv_data, actual_csv_data)


if __name__ == '__main__':
    unittest.main()

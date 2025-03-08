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
from process_annual_reporting import *
import pandas as pd
import tempfile
import sys

MODULE_DIR = os.path.dirname(__file__)
sys.path.insert(0, MODULE_DIR)

TEST_DATASET_DIR = os.path.join(MODULE_DIR, "test_data", "sample_input")

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
        input_path = os.path.join(MODULE_DIR, "test_data", "sample_input")

        cleaned_dataframe = generate_processed_csv(input_path)

        # for each unique column generate the statvar with constraints
        unique_columns = cleaned_dataframe['variable'].unique().tolist()
        unique_places = cleaned_dataframe['Reporting Area'].unique().tolist()

        # column - statvar dictionary map
        sv_map, dcid_df = generate_statvar_map_for_columns(
            unique_columns, unique_places)

        # map the statvars to column names
        cleaned_dataframe = pd.merge(cleaned_dataframe,
                                     dcid_df,
                                     on=['Reporting Area', 'variable'],
                                     how='left')

        #TODO: 2. If reporting area is US Territories, drop observation and make a sum of case counts across US States with mMethod = dc/Aggregate

        cleaned_dataframe = cleaned_dataframe[[
            'observationAbout', 'observationDate', 'variableMeasured',
            'measurementMethod', 'value', 'observationPeriod', 'variable'
        ]]
        with tempfile.NamedTemporaryFile(delete=False,
                                         suffix=".csv") as temp_file:
            # Get the temporary file path
            temp_file_path = temp_file.name

            # Write the DataFrame to the temporary CSV file
            cleaned_dataframe.to_csv(temp_file_path,
                                     index=False,
                                     encoding='utf-8-sig')
            # TODO: Write to csv + tmcf + sv mcf (can be global)

            with open(temp_file_path, encoding="utf-8-sig") as csv_file:
                self.actual_csv_data = csv_file.read()

    def test_create_csv(self):
        """
        This method is required to test between output generated
        preprocess script and excepted output files like CSV
        """
        expected_csv_file_path = os.path.join(
            EXPECTED_FILES_DIR, "cdc_nndss_annual_by_reporting_area_tables.csv")

        expected_csv_data = ""
        with open(expected_csv_file_path,
                  encoding="utf-8") as expected_csv_file:
            expected_csv_data = expected_csv_file.read()

        self.assertEqual(expected_csv_data.strip(),
                         self.actual_csv_data.strip())


if __name__ == "__main__":
    unittest.main()

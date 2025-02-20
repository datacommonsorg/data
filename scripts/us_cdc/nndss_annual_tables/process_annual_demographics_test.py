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
from process_annual_demographics import *
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
        file_list = os.path.join(MODULE_DIR, "test_data", "sample_input")

        # process each table and clean the dataset
        sv4, tab4 = process_table_4(file_list)
        sv5, tab5 = process_table_5(file_list)
        sv6, tab6 = process_table_6(file_list)
        sv7, tab7 = process_table_7(file_list)

        # make a single dataframe of cleaned data and statvar pvs
        cleaned_dataframe = pd.concat([tab4, tab5, tab6, tab7],
                                      ignore_index=True)
        full_sv_df = pd.concat([sv4, sv5, sv6, sv7], ignore_index=True)
        full_sv_df = full_sv_df.drop_duplicates(keep='first')
        del tab4, tab5, tab6, tab7, sv4, sv5, sv6, sv7
        # associate the disease name and dcid to clean_dataframe
        cleaned_dataframe = pd.merge(cleaned_dataframe,
                                     full_sv_df,
                                     on='variable',
                                     how='left')
        del full_sv_df
        # statvar dataframe with all constraints
        full_sv_df = cleaned_dataframe[[
            'ignore_label', 'variable', 'name', 'dcid'
        ]]
        full_sv_df = full_sv_df.drop_duplicates(keep='first')
        # generate statvars from full_sv_df
        full_sv_df = generate_statvars(full_sv_df)
        # merge statvar dcid with full df
        cleaned_dataframe = pd.merge(
            cleaned_dataframe,
            full_sv_df,
            on=['ignore_label', 'variable', 'name', 'dcid'],
            how='left')
        # filter rows that have a defined statvar dcid
        cleaned_dataframe = cleaned_dataframe[cleaned_dataframe['sv_dcid'] !=
                                              '']
        obs_df = cleaned_dataframe[[
            'observationAbout', 'observationDate', 'sv_dcid',
            'measurementMethod', 'value', 'observationPeriod', 'variable'
        ]]
        obs_df.rename(columns={'sv_dcid': 'variableMeasured'}, inplace=True)

        with tempfile.NamedTemporaryFile(delete=False,
                                         suffix=".csv") as temp_file:
            # Get the temporary file path
            temp_file_path = temp_file.name

            # Write the DataFrame to the temporary CSV file
            obs_df.to_csv(temp_file_path, index=False, encoding='utf-8-sig')
            # TODO: Write to csv + tmcf + sv mcf (can be global)
            with open(temp_file_path, encoding="utf-8-sig") as csv_file:
                self.actual_csv_data = csv_file.read()

    def test_create_csv(self):
        """
        This method is required to test between output generated
        preprocess script and expected output files like CSV
        """
        expected_csv_file_path = os.path.join(
            EXPECTED_FILES_DIR, "cdc_nndss_annual_by_demographics.csv")

        expected_csv_data = ""
        with open(expected_csv_file_path,
                  encoding="utf-8") as expected_csv_file:
            expected_csv_data = expected_csv_file.read()

        self.assertEqual(expected_csv_data.strip(),
                         self.actual_csv_data.strip())


if __name__ == "__main__":

    unittest.main()

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
Script to automate the testing for USA Population by Race preprocess script.
"""

import os
import unittest
import pandas as pd
from postprocess import _generate_mcf
from postprocess import _generate_tmcf
# module_dir_ is the path to where this test is running from.
module_dir_ = os.path.dirname(__file__)
test_data_folder = os.path.join(module_dir_, "test_data")
op_data_folder = os.path.join(module_dir_, "test_output_data")


class TestPreprocess(unittest.TestCase):
    """
    TestPreprocess is inherting unittest class
    properties which further requried for unit testing
    """
    #os.chdir('/op_data_folder')
    os.system('python Nationals/national_1980_1990.py')
    os.system('python State/state_1980_1990.py')
    os.system('python County/county_1980_1989.py')

    testlist = [
        'nationals_result_1980_1990.csv', 'state_result_1980_1990.csv',
        'county_result_1980_1989.csv'
    ]

    df1 = pd.DataFrame()

    for i in testlist:
        df = pd.read_csv(i, header=0)
        for col in df.columns:
            df[col] = df[col].astype("str")
        df1 = pd.concat([df, df1], ignore_index=True)

    df1['Year'] = df1['Year'].astype(float).astype(int)
    df1.drop(columns=['Unnamed: 0'], inplace=True)
    df1['geo_ID'] = df1['geo_ID'].str.strip()
    df1.sort_values(by=['Year', 'geo_ID'], ascending=True, inplace=True)
    print(df1.columns)
    df1.to_csv("sex_race_test.csv", index=False)
    test_list1 = df1.columns.to_list()

    _generate_mcf(test_list1, 2)
    _generate_tmcf(test_list1, 2)

    def test_mcf_tmcf_files(self):
        """
        This method is required to test between output generated
        preprocess script and excepted output files like MCF File
        """
        expected_mcf_file_path = os.path.join(
            test_data_folder, "Expected_Population_Estimates_By_Sex_Race.mcf")

        expected_tmcf_file_path = os.path.join(
            test_data_folder, "Expected_Population_Estimates_By_Sex_Race.tmcf")

        with open(expected_mcf_file_path,
                  encoding="UTF-8") as expected_mcf_file:
            expected_mcf_data = expected_mcf_file.read()

        with open(expected_tmcf_file_path,
                  encoding="UTF-8") as expected_tmcf_file:
            expected_tmcf_data = expected_tmcf_file.read()

        with open('Sex_Race_aggregate.mcf', encoding="UTF-8") as mcf_file:
            mcf_data = mcf_file.read()

        with open('Sex_Race_aggregate.tmcf', encoding="UTF-8") as tmcf_file:
            tmcf_data = tmcf_file.read()

        self.assertEqual(expected_mcf_data.strip(), mcf_data.strip())
        self.assertEqual(expected_tmcf_data.strip(), tmcf_data.strip())

    def test_create_csv(self):
        """
        This method is required to test between output generated
        preprocess script and excepted output files like CSV
        """
        expected_csv_file_path = os.path.join(
            test_data_folder, "Expected_Population_Estimates_By_Sex_Race.csv")

        expected_csv_data = ""
        with open(expected_csv_file_path,
                  encoding="utf-8-sig") as expected_csv_file:
            expected_csv_data = expected_csv_file.read()

        with open('sex_race_test.csv', encoding="utf-8-sig") as csv_file:
            csv_data = csv_file.read()

        self.assertEqual(expected_csv_data.strip(), csv_data.strip())

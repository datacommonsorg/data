# # Copyright 2020 Google LLC
# #
# # Licensed under the Apache License, Version 2.0 (the "License");
# # you may not use this file except in compliance with the License.
# # You may obtain a copy of the License at
# #
# #     https://www.apache.org/licenses/LICENSE-2.0
# #
# # Unless required by applicable law or agreed to in writing, software
# # distributed under the License is distributed on an "AS IS" BASIS,
# # WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# # See the License for the specific language governing permissions and
# # limitations under the License.

import datasets
import unittest
import os
import pandas as pd
import csv
import re
import codecs
import csv

MODULE_DIR = os.path.dirname(__file__)

TEST_DATASET_DIR = os.path.join(MODULE_DIR, "test_data", "input_data")
EXPECTED_FILES_DIR = os.path.join(MODULE_DIR, "test_data", "expected_files")


def get_datarow_measurement_method(filename):
    data_row = []
    with open(os.path.join(TEST_DATASET_DIR, filename), 'r') as file_content:
        csv_reader = csv.DictReader(file_content)
        for row in csv_reader:
            data_row.append(row)
            measurement_method = re.match(r"(.*)\.csv", filename).group(1)
    return data_row, measurement_method


def get_sv_mapping(indicator_code):
    for file in os.listdir(TEST_DATASET_DIR):
        if file.endswith('_mapping.csv'):
            with open(os.path.join(TEST_DATASET_DIR, file),
                      'r') as file_content:
                csv_reader = csv.DictReader(file_content)
                for row in csv_reader:
                    series_code = row['seriescode']
                    if series_code == indicator_code:
                        svs = {series_code: row}
                        return svs


def fetch_expected_output(indicator_code):
    for file in os.listdir(EXPECTED_FILES_DIR):
        if file.endswith('.csv'):
            with open(os.path.join(EXPECTED_FILES_DIR, file),
                      'r') as file_content:
                csv_reader = csv.DictReader(file_content)
                for row in csv_reader:
                    indicator = row['indicatorcode']
                    if indicator == indicator_code:
                        expected_output = row
    return expected_output


class TestMyFunction(unittest.TestCase):

    def get_required_data(self, filename, indicator_code):
        data_row, measurement_method = get_datarow_measurement_method(
            'WorldBank_FINDEX_CSV.csv')
        svs = get_sv_mapping(indicator_code)
        expected_output = fetch_expected_output(indicator_code)
        return data_row, measurement_method, svs, expected_output

    def test_input1(self):
        data_row, measurement_method, svs, expected_output = self.get_required_data(
            'WorldBank_FINDEX_CSV.csv',
            'account.t.d',
        )
        self.assertEqual(
            datasets.get_observations_from_data_row(data_row[0], svs,
                                                    measurement_method)[0],
            expected_output)

    def test_input2(self):
        data_row, measurement_method, svs, expected_output = self.get_required_data(
            'WorldBank_FINDEX_CSV.csv',
            'account.t.d.1',
        )
        self.assertEqual(
            datasets.get_observations_from_data_row(data_row[1], svs,
                                                    measurement_method)[0],
            expected_output)


if __name__ == '__main__':
    unittest.main()

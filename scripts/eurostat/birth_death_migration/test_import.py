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
from import_data import preprocess_data, clean_data
import pandas as pd


class TestPreprocess(unittest.TestCase):
    maxDiff = None

    def test1(self):
        """Simple unit test on melting csv content"""
        self._test_preprocess_output('./test/test1')

    def test2(self):
        """Simple integration test on output csv content"""
        self._test_csv_output('./test/test2')

    def _test_preprocess_output(self, dir_path: str):
        """Generates a melted csv file, given an input data file.
        Compares the expected.csv to the output.csv file
        to make sure the function is performing as designed.
        Args:
            dir_path (str): the path of the directory containing:
            data.tsv and expected.csv.
        Returns:
            str: expected output == actual output.
        """

        input_path = os.path.join(dir_path, "data.tsv")
        output_path = os.path.join(dir_path, "output.csv")
        expected_path = os.path.join(dir_path, "expected.csv")

        if not os.path.exists(input_path):
            self.fail(input_path + " doesn't exist!")
        if not os.path.exists(expected_path):
            self.fail(expected_path + " doesn't exist!")

        # Generate the output csv file.
        input_df = pd.read_csv(input_path, sep='\s*\t\s*', engine='python')
        preprocess_data(input_df).to_csv(output_path, index=False)
        # Get the content from the csv file.
        actual_f = open(output_path, 'r+')
        actual: str = actual_f.read()
        actual_f.close()

        # Get the content of the expected output.
        expected_f = open(expected_path, 'r+')
        expected = expected_f.read()
        expected_f.close()

        self.assertEqual(actual, expected)

    def _test_csv_output(self, dir_path: str):
        """Generates a csv file, given an input data file.
        Compares the expected.csv to the output.csv file
        to make sure the function is performing as designed.
        Args:
            dir_path (str): the path of the directory containing:
            data.tsv and expected.csv.
        Returns:
            str: expected output == actual output.
        """

        input_path = os.path.join(dir_path, "data.tsv")
        output_path = os.path.join(dir_path, "output.csv")
        expected_path = os.path.join(dir_path, "expected.csv")

        if not os.path.exists(input_path):
            self.fail(input_path + " doesn't exist!")
        if not os.path.exists(expected_path):
            self.fail(expected_path + " doesn't exist!")

        # Generate the output csv file.
        input_df = pd.read_csv(input_path, sep='\s*\t\s*', engine='python')
        clean_data(preprocess_data(input_df), output_path)
        # Get the content from the csv file.
        actual_f = open(output_path, 'r+')
        actual: str = actual_f.read()
        actual_f.close()

        # Get the content of the expected output.
        expected_f = open(expected_path, 'r+')
        expected = expected_f.read()
        expected_f.close()

        self.assertEqual(actual, expected)


if __name__ == '__main__':
    unittest.main()

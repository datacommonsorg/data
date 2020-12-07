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
from io import StringIO
from os import path
from typing import Dict
import pandas as pd
from Covid19India import Covid19India


class TestCovid19India(unittest.TestCase):

    def test1(self):
        """Simple test with both state and district data for two states."""
        state_to_source = {"WB": "./tests/test1/WB.json",
                           "UP": "./tests/test1/UP.json"}
        self._test_csv_output(state_to_source, "./tests/test1/")

    def test2(self):
        """Simple test with only one state data, no district data."""
        state_to_source = {"WB": "./tests/test2/WB.json"}
        self._test_csv_output(state_to_source, "./tests/test2/")

    def test3(self):
        """Simple test with empty data for two states. NULL case."""
        state_to_source = {"WB": "./tests/test3/WB.json",
                           "UP": "./tests/test3/UP.json"}
        self._test_csv_output(state_to_source, "./tests/test3/")

    def _test_csv_output(self,
                         state_to_source: Dict[str, str],
                         dir_path: str):
        """Given the paths to the json files containing data for each state,
        runs the function and compares the expected.csv to the output.csv
        file to ensure everything is working as expected.
        @param state_to_source: dict state's isoCode->json containing data.
        @param dir_path: the tests's directory containing the json data and
        expected CSV file.
        @returns assertion that output.csv == expected.csv.
        """

        # The expected output is found within the directory.
        expected_path: str = path.join(dir_path, "expected.csv")

        # Make sure the expected.csv file exists.
        if not path.exists(expected_path):
            self.fail(expected_path + " doesn't exist!")

        # Read the expected.csv value.
        f_expected = open(expected_path, 'rt')
        expected_csv = f_expected.read()

        # Run the script and get write the output to a StringIO.
        f_actual = StringIO()
        Covid19India(state_to_source=state_to_source,
                     output=f_actual)
        actual_csv = f_actual.getvalue()

        # Assert both CSVs are equal.
        self.assertEqual(expected_csv, actual_csv)

        # Close opened file.
        f_expected.close()


if __name__ == '__main__':
    unittest.main()

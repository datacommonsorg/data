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
from WikiParser import WikiParser


class TestWikiParser(unittest.TestCase):

    def test1(self):
        """Simple test with two valid places."""
        state_to_source = {"ABC": "./tests/test1/ABC.html",
                           "XYZ": "./tests/test1/XYZ.html"}
        self._test_csv_output(state_to_source, "./tests/test1/")

    def test2(self):
        """Test with no 'total cases' label"""
        state_to_source = {"FR": "./tests/test2/france.html"}
        self._test_csv_output(state_to_source, "./tests/test2/")

    def test3(self):
        """Simple test with an inncorrect and a correct table.
        One of the tables is valid, the other is not. The invalid table
        should be skipped."""
        state_to_source = {"test3": "./tests/test3/test3.html",
                            "FR": "./tests/test3/france.html"}
        self._test_csv_output(state_to_source, "./tests/test3/")

    def _test_csv_output(self,
                         state_to_source: Dict[str, str],
                         dir_path: str):
        """Given the paths to the HTML files containing data for each place,
        runs the function and compares the expected.csv to the output.csv
        file to ensure everything is working as expected.
        @param state_to_source: dict state's wikidataId->HTML containing data.
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

        # Run the script and write the output to a StringIO.
        f_actual = StringIO()
        WikiParser(state_to_source=state_to_source, output=f_actual)
        actual_csv = f_actual.getvalue()

        # Assert both CSVs are equal.
        self.assertEqual(expected_csv, actual_csv)

        # Close opened file.
        f_expected.close()


if __name__ == '__main__':
    unittest.main()

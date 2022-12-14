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
from .covidmobility import csv_to_mcf
from os import path


class TestCovidMobility(unittest.TestCase):
    maxDiff = None

    def test1(self):
        """Simple test 1"""
        self._test_mcf_output('./tests/test1')

    def test2(self):
        """Simple test 2"""
        self._test_mcf_output('./tests/test2')

    def test3(self):
        """Tests a row with empty data."""
        self._test_mcf_output('./tests/test3')

    def test4(self):
        """Tests a row with an empty date."""
        self._test_mcf_output('./tests/test4')

    def _test_mcf_output(self, dir_path: str):
        """Generates an MCF file, given an input data file.
        Compares the expected.mcf to the output.mcf file
        to make sure the function is performing as designed.

        Args:
            dir_path (str): the path of the directory containing:
            data.csv and expected.mcf.

        Returns:
            str: expected output == actual output.
        """

        module_dir = path.dirname(path.realpath(__file__))
        input_path = path.join(module_dir, dir_path, "data.csv")
        output_path = path.join(module_dir, dir_path, "output.mcf")
        expected_path = path.join(module_dir, dir_path, "expected.mcf")

        if not path.exists(input_path):
            self.fail(input_path + " doesn't exist!")
        if not path.exists(expected_path):
            self.fail(expected_path + " doesn't exist!")

        # Generate the output mcf file.
        csv_to_mcf(input_path, output_path)

        # Get the content from the MCF file.
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

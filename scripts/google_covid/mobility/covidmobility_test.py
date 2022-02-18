# Copyright 2022 Google LLC
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

import os
import sys
import tempfile
import unittest

# Allows the following module imports to work when running as a script
_CODE_DIR = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(1, os.path.join(_CODE_DIR, '../../'))
from google_covid.mobility import covidmobility

_TESTDIR = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                        'test_data')


class TestCovidMobility(unittest.TestCase):
    maxDiff = None

    def test_main(self):
        for d in ['test1', 'test2', 'test3', 'test4']:
            print('Running test', d)
            self._test_csv_output(os.path.join(_TESTDIR, d))

    def _test_csv_output(self, dir_path: str):
        """Generates an MCF file, given an input data file.
        Compares the expected.csv to the output.csv file
        to make sure the function is performing as designed.

        Args:
            dir_path (str): the path of the directory containing:
            data.csv and expected.mcf.

        Returns:
            str: expected output == actual output.
        """

        with tempfile.TemporaryDirectory() as tmp_dir:
            input_path = os.path.join(dir_path, "data.csv")
            expected_path = os.path.join(dir_path, "expected.csv")
            output_path = os.path.join(tmp_dir, "output.csv")

            if not os.path.exists(input_path):
                self.fail(input_path + " doesn't exist!")
            if not os.path.exists(expected_path):
                self.fail(expected_path + " doesn't exist!")

            # Generate the output mcf file.
            covidmobility.clean_csv(input_path, output_path)

            # Get the content from the MCF file.
            actual_f = open(output_path, 'r+')
            actual: str = actual_f.read()
            actual_f.close()

            # Get the content of the expected output.
            expected_f = open(expected_path, 'r+')
            expected: str = expected_f.read()
            expected_f.close()

            self.assertEqual(actual, expected)


if __name__ == '__main__':
    unittest.main()

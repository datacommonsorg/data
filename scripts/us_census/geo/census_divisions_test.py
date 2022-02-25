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
"""Test for census_divisions.py"""

import os
import sys
import tempfile
import unittest

# Allows the following module imports to work when running as a script
# relative to data/scripts/
sys.path.append(
    os.path.sep.join([
        '..'
        for x in filter(lambda x: x == os.path.sep,
                        os.path.abspath(__file__).split('data/scripts/')[1])
    ]))

# module_dir_ is the path to where this test is running from.
module_dir_ = os.path.dirname(__file__)

import census_divisions


class TestProcess(unittest.TestCase):

    def compare_files(self, actual_files: list, expected_files: list):
        '''Raise a test failure if actual and expected files differ.'''
        self.assertEqual(len(actual_files), len(expected_files))
        for i in range(0, len(actual_files)):
            with open(actual_files[i], 'r') as actual_f:
                actual_str = actual_f.read()
            with open(expected_files[i], 'r') as expected_f:
                expected_str = expected_f.read()
            self.assertEqual(
                actual_str, expected_str,
                f'Mismatched files:\nactual:{actual_files[i]}\nexpected:{expected_files[i]}'
            )

    def test_process(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            mcf_file = os.path.join(tmp_dir, 'test_output.mcf')
            csv_file = os.path.join(module_dir_, 'census_region_geocodes.csv')
            census_divisions.process(csv_file, mcf_file)
            expected_file = os.path.join(module_dir_, 'geo_CensusDivision.mcf')
            self.compare_files(actual_files=[mcf_file],
                               expected_files=[expected_file])

            with open(mcf_file, 'r') as f:
                actual_mcf = f.read()

            os.remove(mcf_file)

            with open(expected_file, 'r') as f:
                expected_mcf = f.read()

            self.assertEqual(expected_mcf, actual_mcf)


if __name__ == '__main__':
    unittest.main()

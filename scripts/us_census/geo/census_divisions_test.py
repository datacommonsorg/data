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
# relative to scripts/
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import census_divisions


class TestProcess(unittest.TestCase):

    def test_process(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            mcf_file = os.path.join(tmp_dir, 'test_output.mcf')
            census_divisions.process('census_region_geocodes.csv', mcf_file)

            with open(mcf_file) as f:
                actual_mcf = f.read()

            os.remove(mcf_file)

            with open('geo_CensusDivision.mcf') as f:
                expected_mcf = f.read()

            self.assertEqual(expected_mcf, actual_mcf)


if __name__ == '__main__':
    unittest.main()

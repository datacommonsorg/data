# Copyright 2021 Google LLC
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
'''
Unit tests for country_boundaries_mcf_generator.py

Usage: ./run_tests.sh -p scripts/world_bank/
'''
import unittest
import os
import tempfile
import sys

sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__)))))
from world_bank.boundaries import country_boundaries_mcf_generator as mcf_gen

module_dir_ = os.path.dirname(__file__)

DP0_FNAME = 'countries.dp0.mcfgeojson.mcf'
DP3_FNAME = 'countries.dp3.mcfgeojson.mcf'


class CountyBoundariesMcfGeneratorTest(unittest.TestCase):

    def test_output_mcf(self):
        with tempfile.TemporaryDirectory() as test_mcf_dir:
            test_export_dir = os.path.join(module_dir_, 'test_data')
            mcf_gen.EPS_LEVEL_MAP = {0: 0, 0.05: 3}
            gen = mcf_gen.CountryBoundariesMcfGenerator('', test_export_dir,
                                                        test_mcf_dir)
            gen.output_mcf({'code': ['LIE']})

            with open(os.path.join(test_mcf_dir, DP3_FNAME)) as test_dp3, open(
                    os.path.join(test_export_dir, DP3_FNAME)) as expected_dp3:
                self.assertEqual(test_dp3.read(), expected_dp3.read())

            with open(os.path.join(test_mcf_dir, DP0_FNAME)) as test_dp0, open(
                    os.path.join(test_export_dir, DP0_FNAME)) as expected_dp0:
                self.assertEqual(test_dp0.read(), expected_dp0.read())


if __name__ == '__main__':
    unittest.main()

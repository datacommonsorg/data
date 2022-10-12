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
'''
Unit tests for gpcc_spi_aggregation.py
Usage: python3 -m unittest discover -v -s ../ -p "gpcc_spi_aggregation_test.py"
'''
import unittest
import os
import tempfile
import filecmp
from .gpcc_spi_aggregation import run_gpcc_spi_aggregation

# module_dir is the path to where this test is running from.
module_dir = os.path.dirname(__file__)


class GPCCSPIAggregationTest(unittest.TestCase):

    def test_process_main(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            place_area_ratio_json_path = os.path.join(
                module_dir, 'testdata/place_area_ratio.json')

            in_pattern = os.path.join(
                module_dir, 'testdata/expected_gpcc_spi_pearson*.csv')

            output_paths = run_gpcc_spi_aggregation(in_pattern, tmp_dir,
                                                    place_area_ratio_json_path)

            in_12 = in_pattern.replace('*', '_12')
            expected_12 = os.path.join(module_dir,
                                       'testdata/expected_agg_12.csv')

            self.assertTrue(filecmp.cmp(output_paths[in_12], expected_12))

            in_72 = in_pattern.replace('*', '_72')
            expected_72 = os.path.join(module_dir,
                                       'testdata/expected_agg_72.csv')
            self.assertTrue(filecmp.cmp(output_paths[in_72], expected_72))


if __name__ == '__main__':
    unittest.main()

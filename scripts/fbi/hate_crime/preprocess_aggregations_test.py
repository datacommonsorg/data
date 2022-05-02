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
"""Tests for geo_id_resolver.py"""

import filecmp
import os
import unittest
from preprocess_aggregations import process_main


class HatecrimeAggTest(unittest.TestCase):

    def test_process_main(self):
        _SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))
        process_main(input_csv=os.path.join(_SCRIPT_PATH, 'testdata',
                                            'hate_crime_sample.csv'),
                     output_path='./tmp')
        self.assertTrue(
            filecmp.cmp(os.path.join(_SCRIPT_PATH, 'testdata',
                                     'aggregations_expected',
                                     'aggregation.csv'),
                        os.path.join(_SCRIPT_PATH, 'tmp', 'aggregation.csv'),
                        shallow=False))
        self.assertTrue(
            filecmp.cmp(os.path.join(_SCRIPT_PATH, 'testdata',
                                     'aggregations_expected',
                                     'aggregation.mcf'),
                        os.path.join(_SCRIPT_PATH, 'tmp', 'aggregation.mcf'),
                        shallow=False))


if __name__ == '__main__':
    unittest.main()

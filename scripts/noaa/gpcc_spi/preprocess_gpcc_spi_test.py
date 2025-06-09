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
Unit tests for preprocess_gpcc_spi.py
Usage: python -m unittest discover -v -s ../ -p "preprocess_gpcc_spi_test.py"
'''
import unittest
from .preprocess_gpcc_spi import preprocess_one
import os
import tempfile
import filecmp
from dataclasses import dataclass

# module_dir is the path to where this test is running from.
module_dir = os.path.dirname(__file__)


@dataclass
class TestCase:
    input: str
    expected: str
    start_date: str
    end_date: str


class GPCCSPIPreprocessTest(unittest.TestCase):

    def test_preprocess(self):

        test_cases = [
            TestCase(input=os.path.join(module_dir,
                                        'testdata/gpcc_spi_pearson_12.nc'),
                     start_date='1988-01-01',
                     end_date='1988-12-01',
                     expected=os.path.join(
                         module_dir,
                         'testdata/expected_gpcc_spi_pearson_12.csv')),
            TestCase(input=os.path.join(module_dir,
                                        'testdata/gpcc_spi_pearson_72.nc'),
                     start_date='1988-01-01',
                     end_date='1988-12-01',
                     expected=os.path.join(
                         module_dir,
                         'testdata/expected_gpcc_spi_pearson_72.csv'))
        ]

        for test_case in test_cases:
            with tempfile.TemporaryDirectory() as tmp_dir:
                output_path = preprocess_one(test_case.start_date,
                                             test_case.end_date,
                                             test_case.input, tmp_dir)
                self.assertTrue(filecmp.cmp(output_path, test_case.expected))


if __name__ == '__main__':
    unittest.main()

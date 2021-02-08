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

import filecmp
import os
import json
import tempfile
import unittest
from india_rbi.unemployment_rate_india.preprocess import UnempolymentRateIndiaLoader

# module_dir_ is the path to where this test is running from.
module_dir_ = os.path.dirname(__file__)


class TestPreprocess(unittest.TestCase):

    def test_create_csv(self):
        xlsx_file = os.path.join(module_dir_, 'test_data/test.XLSX')
        sheet_no = 0
        statisticalVariable = "UnemploymentRate_Person_Urban"
        expected_file = open(os.path.join(module_dir_,
                                          'test_data/expected.csv'))
        expected_data = expected_file.read()
        expected_file.close()

        result_file_path = os.path.join(module_dir_,
                                        'test_data/test_cleaned.csv')

        loader = UnempolymentRateIndiaLoader(xlsx_file, sheet_no,
                                             statisticalVariable)
        loader.load()
        loader.process()
        loader.save(result_file_path)

        result_file = open(result_file_path)
        result_data = result_file.read()
        result_file.close()

        os.remove(result_file_path)
        self.assertTrue(expected_data == result_data)


if __name__ == '__main__':
    unittest.main()

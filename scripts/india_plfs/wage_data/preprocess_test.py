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

__author__ = ["Thejesh GN (i@thejeshgn.com)"]

import filecmp
import os
import json
import tempfile
import unittest
from india_plfs.wage_data.preprocess import PLFSWageDataLoader

# module_dir_ is the path to where this test is running from.
module_dir_ = os.path.dirname(__file__)


class TestPreprocess(unittest.TestCase):

    def test_create_cleaned_wage_csv(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            xlsx_file = os.path.join(module_dir_, 'test_data/test.xlsx')
            expected_file_path = os.path.join(module_dir_,
                                              'test_data/expected.csv')
            result_file_path = os.path.join(module_dir_,
                                            'test_data/test_cleaned.csv')

            loader = PLFSWageDataLoader(xlsx_file, period="2018-10")
            loader.load()
            loader.process()
            loader.save(csv_file_path=result_file_path)

            expected_file = open(expected_file_path)
            expected_file_data = expected_file.read()
            expected_file.close()

            result_file = open(result_file_path)
            result_file_data = result_file.read()
            result_file.close()

            os.remove(result_file_path)

        self.maxDif = None
        self.assertEqual(expected_file_data, result_file_data)


if __name__ == '__main__':
    unittest.main()

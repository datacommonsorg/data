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
import pandas as pd
from india_post.pincodes.preprocess import IndiaPostPincodesDataLoader

# module_dir_ is the path to where this test is running from.
module_dir_ = os.path.dirname(__file__)


class TestPreprocess(unittest.TestCase):

    def test_create_cleaned_csv(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            pincode_csv_path = os.path.join(module_dir_, 'test_data/test.csv')
            clean_csv_file_path = os.path.join(module_dir_,
                                               'test_data/clean.csv')
            clean_tmcf_file_path = os.path.join(module_dir_,
                                                'test_data/clean.tmcf')

            expected_tmcf_file_path = os.path.join(module_dir_,
                                                   'test_data/expected.tmcf')
            expected_csv_file_path = os.path.join(module_dir_,
                                                  'test_data/expected.csv')

            loader = IndiaPostPincodesDataLoader(pincode_csv_path,
                                                 clean_csv_file_path,
                                                 clean_tmcf_file_path)
            loader.process()
            loader.save()
            clean_df = pd.read_csv(clean_csv_file_path, dtype=str)

            expected_tmcf_file = open(expected_tmcf_file_path)
            expected_tmcf_file_data = expected_tmcf_file.read()
            expected_tmcf_file.close()

            result_tmcf_file = open(clean_tmcf_file_path)
            result_tmcf_file_data = result_tmcf_file.read()
            result_tmcf_file.close()

            expected_csv_file = open(expected_csv_file_path)
            expected_csv_file_data = expected_csv_file.read()
            expected_csv_file.close()

            result_csv_file = open(clean_csv_file_path)
            result_csv_file_data = result_csv_file.read()
            result_csv_file.close()

            os.remove(clean_csv_file_path)
            os.remove(clean_tmcf_file_path)

            self.maxDif = None
            self.assertEqual(len(clean_df.columns), 5)
            self.assertEqual(len(clean_df), 1405)
            self.assertEqual(expected_tmcf_file_data, result_tmcf_file_data)
            self.assertEqual(expected_csv_file_data, result_csv_file_data)


if __name__ == '__main__':
    unittest.main()

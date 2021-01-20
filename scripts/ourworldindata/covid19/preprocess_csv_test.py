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

import filecmp
import os
import tempfile
import unittest
from preprocess_csv import create_formatted_csv_file
from preprocess_csv import create_tmcf_file

# module_dir_ is the path to where this test is running from.
module_dir_ = os.path.dirname(__file__)


class TestPreprocessCsvTest(unittest.TestCase):

    def test_create_csv(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            f = os.path.join(module_dir_, 'test_data/test_data.csv')
            expected_csv_file = os.path.join(
                module_dir_, 'test_data/expected_formatted_data.csv')
            with open(f, "r") as f_in:
                result_csv_file = os.path.join(tmp_dir,
                                               'OurWorldInData_Covid19.csv')
                create_formatted_csv_file(f_in, result_csv_file)
                same_csv = filecmp.cmp(result_csv_file, expected_csv_file)

                os.remove(result_csv_file)

        self.assertTrue(same_csv)

    def test_create_tmcf(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            expected_tmcf_file = os.path.join(
                module_dir_, 'test_data/expected_covid19.tmcf')
            result_tmcf_file = os.path.join(tmp_dir,
                                            'OurWorldInData_Covid19.tmcf')

            create_tmcf_file(result_tmcf_file)

            same_tmcf = filecmp.cmp(result_tmcf_file, expected_tmcf_file)

            os.remove(result_tmcf_file)

        self.assertTrue(same_tmcf)


if __name__ == '__main__':
    unittest.main()

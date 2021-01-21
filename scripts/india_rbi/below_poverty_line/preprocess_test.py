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
from india_rbi.below_poverty_line.preprocess import BelowPovertyLineDataLoader

# module_dir_ is the path to where this test is running from.
module_dir_ = os.path.dirname(__file__)


class TestPreprocess(unittest.TestCase):

    def test_create_csv(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            xlsx_file = os.path.join(module_dir_, 'test_data/test.XLSX')
            expected_file = os.path.join(module_dir_, 'test_data/expected.csv')
            result_file = os.path.join(tmp_dir, 'test_cleaned.csv')

            loader = BelowPovertyLineDataLoader(xlsx_file)
            loader.download()
            loader.process()
            loader.save(csv_file_path=result_file)

            same = filecmp.cmp(result_file, expected_file)
            os.remove(result_file)

        self.assertTrue(same)


if __name__ == '__main__':
    unittest.main()

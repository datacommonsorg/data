# Copyright 2021 Google LLC
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

import unittest

from .column_map_validator import *


class TestColumnMapValidator(unittest.TestCase):

    def test_check_column_map(self):
        cur_dir = os.path.dirname(__file__)
        ret = check_column_map(
            os.path.join(cur_dir,
                         './testdata/column_map_from_zip_expected.json'),
            os.path.join(cur_dir, './testdata/S2702_yearwise_columns.json'),
            os.path.join(cur_dir, './testdata/spec_s2702.json'),
            os.path.join(cur_dir, './tmp'))
        with open(
                os.path.join(
                    cur_dir,
                    'testdata/expected_column_map_validation.json')) as fp:
            self.maxDiff = None
            self.assertCountEqual(ret, json.load(fp))


if __name__ == '__main__':
    unittest.main()

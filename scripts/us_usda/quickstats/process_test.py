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
"""Tests for process.py"""

import csv
import io
import unittest
from process import to_csv_rows, get_survey_county_data, write_csv, load_svs


class ProcessTest(unittest.TestCase):

    def test_write_csv(self):
        expected = None
        with open('testdata/expected.csv') as f:
            expected = f.read()

        svs = load_svs()
        api_data = get_survey_county_data(2022, 'ALAMEDA', 'testdata')
        csv_rows = to_csv_rows(api_data, svs)
        out = io.StringIO()
        print(csv_rows)
        write_csv(out, csv_rows)
        self.assertEqual(expected, out.getvalue())


if __name__ == '__main__':
    unittest.main()

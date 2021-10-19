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
from process import get_statvars, write_csv

class ProcessTest(unittest.TestCase):

  def test_write_csv(self):
    with open('./testdata/input.csv') as f_in:
      d = get_statvars('statvars')
      reader = csv.DictReader(f_in, delimiter='\t')
      f_out = io.StringIO()
      f_expected = open('testdata/expected.csv')
      expected = f_expected.read()
      f_expected.close()
      write_csv(reader, f_out, d)
      self.assertEqual(expected, f_out.getvalue())

if __name__ == '__main__':
    unittest.main()

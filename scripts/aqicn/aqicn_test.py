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
'''Tests for aqicn.py

Usage: python3 -m unittest discover -v -s ../ -p "aqicn_test.py"
'''
import csv
import io
import os
import unittest
from .aqicn import *

MODULE = os.path.dirname(__file__)


class AqicnTest(unittest.TestCase):

    def test_write_csv(self):
        with open(os.path.join(MODULE, 'testdata/input.csv'), 'r') as f:
            csvfile = csv.reader(f, delimiter=',')
            output = io.StringIO()
            keys = set()
            write_csv(csvfile, output, keys)

        with open(os.path.join(MODULE, 'testdata/expected.csv'),
                  'r') as expected:
            expected_str = expected.read()
            self.assertEqual(output.getvalue(), expected_str)


if __name__ == '__main__':
    unittest.main()

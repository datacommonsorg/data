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
"""
Test periodic table processing
"""

import filecmp
from os import path
import sys
import tempfile
import unittest

# Allows the following module imports to work when running as a script
# module_dir_ is the path to where this code is running from.
module_dir_ = path.dirname(__file__)
sys.path.append(path.join(module_dir_))

import process


class TestPeriodicTableProcess(unittest.TestCase):

  def test_csv_process(self):
     tmp_dir = tempfile.mkdtemp()
     process.process('periodic_table.csv', path.join(tmp_dir, 'elements'))

     with open(path.join(tmp_dir, 'elements.csv')) as csv_file:
       out_csv = csv_file.read()
     with open(path.join(module_dir_, 'elements.csv')) as expected_csv:
       expected_out_csv = expected_csv.read()
     self.assertEqual(out_csv, expected_out_csv)

     with open(path.join(tmp_dir, 'elements.tmcf')) as tmcf_file:
       out_tmcf = tmcf_file.read()
     with open(path.join(module_dir_, 'elements.tmcf')) as expected_tmcf:
       expected_out_tmcf = expected_tmcf.read()
     self.assertEqual(out_tmcf, expected_out_tmcf)



if __name__ == '__main__':
  unittest.main()

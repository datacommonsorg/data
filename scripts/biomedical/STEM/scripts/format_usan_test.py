# Copyright 2023 Google LLC
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

import os
import filecmp
import unittest
from format_usan import *

MODULE_DIR = str(Path(os.path.dirname(__file__)))
print(MODULE_DIR)
_FLAGS = None
def set_flag():
	global _FLAGS
	_FLAGS = flags.FLAGS
	flags.DEFINE_string('output_dir', 'scripts/test_data/output_file/usan.csv',
                    'Output directory for generated files.')
	flags.DEFINE_string('input_dir', 'scripts/test_data/input_file/usan_test_data.xlsx',
                    'Input directory where .dmp files downloaded.')
     
	_FLAGS(sys.argv)

class TestUSANSTEM(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        set_flag()

    def test_csv_check(self):
        main(_FLAGS)
        same = filecmp.cmp(
             _FLAGS.output_dir,
             MODULE_DIR + '/test_data/output_file/expected_usan.csv')
        self.assertTrue(same)


if __name__ == '__main__':
    unittest.main()

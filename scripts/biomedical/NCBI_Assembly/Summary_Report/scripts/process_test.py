# Copyright 2024 Google LLC
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
# Author: Sanika Prasad
# Date: 05/31/2024

import os
import copy
import filecmp
import unittest
from pathlib import Path
from process import *

MODULE_DIR = str(Path(os.path.dirname(__file__)))
_FLAGS = None


def set_flag():
	global _FLAGS
	_FLAGS = flags.FLAGS
	flags.DEFINE_string('output_dir', 'test_data/output_file/',
                        'Output directory for generated files.')
	flags.DEFINE_string('input_dir',
                        'scripts/test_data/input/assembly_summary_genbank.txt',
                        'Input directory where .txt files downloaded.')	
	flags.DEFINE_string('input_dir1',
                        'scripts/test_data/input/assembly_summary_refseq.txt',
                        'Output directory for generated files.')
	flags.DEFINE_string('tax_id_dcid_mapping',
                        'scripts/test_data/input/tax_id_dcid_mapping.txt',
                        'Input directory where .txt files downloaded.')
	_FLAGS(sys.argv)

class TestSummaryReport(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        set_flag()

    def test_csv_check(self):
        main(_FLAGS)
        test_output = os.path.join(MODULE_DIR, _FLAGS.output_dir)
        same = filecmp.cmp(
            os.path.join(test_output,'ncbi_assembly_summary.csv'), MODULE_DIR +
            '/test_data/output_file/expected_ncbi_assembly_summary.csv')
        self.assertTrue(same)


if __name__ == '__main__':
    unittest.main()

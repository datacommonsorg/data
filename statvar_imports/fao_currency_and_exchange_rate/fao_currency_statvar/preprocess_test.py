# Copyright 2025 Google LLC
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
Script to automate the testing for FAO_Currency_statvar import.
"""

import os
import shutil
import sys
import tempfile
import unittest
from absl import app, logging
import pandas as pd

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if _SCRIPT_DIR not in sys.path:
    sys.path.insert(0, _SCRIPT_DIR)
sys.modules.pop('preprocess', None)

from preprocess import melt_year_and_flag_columns

input_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         "testdata/")


class TestPreprocess(unittest.TestCase):
    """
    This module is used to test FAO_Currency_Statvar data processing.
    It will generate and test input CSV file for given test input file
    and compare it with expected results.
    """

    def setUp(self):
        self._temp_dir = tempfile.mkdtemp()
        input_file = os.path.join(input_dir, 'Exchange_rate_E_All_Data.csv')
        self.actual_output_file = os.path.join(self._temp_dir,
                                               'final_input_data.csv')
        self.expected_output_file = os.path.join(
            input_dir, 'final_input_data_expected.csv')

        melt_year_and_flag_columns(input_file, self.actual_output_file)

    def tearDown(self):
        shutil.rmtree(self._temp_dir, ignore_errors=True)

    def test_input_csv_files(self):
        """
        This method tests input csv files generated using preprocess module against
        expected results.
        """
        # Compare as tables with a small float tolerance: the last digits of
        # parsed floats differ across pandas/numpy builds.
        pd.testing.assert_frame_equal(pd.read_csv(self.actual_output_file),
                                      pd.read_csv(self.expected_output_file),
                                      check_exact=False,
                                      rtol=1e-12)

        logging.info("Testing completed for preprocessed input file!")


def main(argv):
    unittest.main()


if __name__ == '__main__':
    app.run(main)

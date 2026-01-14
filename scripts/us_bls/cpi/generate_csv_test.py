# Copyright 2025 Google LLC
# Author: Shamim Ansari
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
import os
import tempfile
import unittest

import pandas as pd

from .generate_csv import process

MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
TEST_DATA_DIR = os.path.join(MODULE_DIR, 'test_data')
INPUT_FILES_DIR = os.path.join(TEST_DATA_DIR, 'input_files')
EXPECTED_OUTPUT_DIR = os.path.join(TEST_DATA_DIR, 'expected_output')


class TestGenerateCSV(unittest.TestCase):

    def test_cpi_u(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            process(INPUT_FILES_DIR, temp_dir, int(1946))

            generated_file = os.path.join(temp_dir, "cpi_u.csv")
            expected_file = os.path.join(EXPECTED_OUTPUT_DIR, "cpi_u.csv")

            generated_df = pd.read_csv(generated_file)
            expected_df = pd.read_csv(expected_file)

            pd.testing.assert_frame_equal(generated_df, expected_df)

    def test_cpi_w(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            process(INPUT_FILES_DIR, temp_dir, int(1946))

            generated_file = os.path.join(temp_dir, "cpi_w.csv")
            expected_file = os.path.join(EXPECTED_OUTPUT_DIR, "cpi_w.csv")

            generated_df = pd.read_csv(generated_file)
            expected_df = pd.read_csv(expected_file)

            pd.testing.assert_frame_equal(generated_df, expected_df)

    def test_c_cpi_u(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            process(INPUT_FILES_DIR, temp_dir, int(1946))

            generated_file = os.path.join(temp_dir, "c_cpi_u.csv")
            expected_file = os.path.join(EXPECTED_OUTPUT_DIR, "c_cpi_u.csv")

            generated_df = pd.read_csv(generated_file)
            expected_df = pd.read_csv(expected_file)

            pd.testing.assert_frame_equal(generated_df, expected_df)


if __name__ == '__main__':
    unittest.main()

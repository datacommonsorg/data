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

import unittest
import os
import tempfile
import filecmp
import shutil
from .process import *


class ProcessEnhancedTest(unittest.TestCase):

    def setUp(self):
        self.test_data_dir = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), 'test_data')
        self.temp_dir = tempfile.mkdtemp()
        self.intermediate_path = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_script(self):
        input_path = os.path.join(self.test_data_dir, 'input')
        expected_path = os.path.join(self.test_data_dir, 'expected')
        process_files(input_path, self.temp_dir, self.intermediate_path)

        # Compare the output files
        expected_files = sorted(os.listdir(expected_path))
        generated_files = sorted(os.listdir(self.temp_dir))

        self.assertEqual(len(expected_files), len(generated_files),
                         "Number of files mismatch")

        for expected_file, generated_file in zip(expected_files,
                                                 generated_files):
            expected_file_path = os.path.join(expected_path, expected_file)
            generated_file_path = os.path.join(self.temp_dir, generated_file)

            self.assertTrue(
                filecmp.cmp(expected_file_path,
                            generated_file_path,
                            shallow=False),
                f"File content mismatch: {expected_file} and {generated_file}")


if __name__ == '__main__':
    unittest.main()

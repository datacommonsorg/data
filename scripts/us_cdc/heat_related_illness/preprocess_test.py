# Copyright 2022 Google LLC
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
"""Tests for preprocess.py."""

import os
import unittest
from preprocess import process

_SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))


class EPHHeatRelatedIllness(unittest.TestCase):

    def __init__(self, methodName: str = ...) -> None:
        super().__init__(methodName)
        self.exp_path = os.path.join(_SCRIPT_PATH, 'testdata', 'expected_files')
        self.act_path = os.path.join(_SCRIPT_PATH, 'testdata', 'actual_files')
        csv_path = os.path.join(self.act_path, 'cleaned.csv')
        mcf_path = os.path.join(self.act_path, 'output.mcf')
        input_path = os.path.join(_SCRIPT_PATH, 'testdata', 'cleaned_data/')
        try:
            os.makedirs(self.act_path)
        except FileExistsError:
            pass  # Directory already exists

        # generates actual output in tmp directory
        process(csv_path, mcf_path, input_path)

        with open(csv_path, 'r', encoding='utf-8') as f_result:
            self.actual_csv_result = f_result.read()

        with open(mcf_path, 'r', encoding='utf-8') as f_result:
            self.actual_mcf_result = f_result.read()

    def test_csv(self):
        expected_csv_path = os.path.join(self.exp_path, 'expected_output.csv')

        with open(expected_csv_path, 'r', encoding='utf-8') as f_expected:
            expected_result = f_expected.read()

        self.assertEqual(self.actual_csv_result, expected_result)

    def test_mcf(self):
        expected_mcf_path = os.path.join(self.exp_path, 'expected_output.mcf')

        with open(expected_mcf_path, 'r', encoding='utf-8') as f_expected:
            expected_result = f_expected.read()

        self.assertEqual(self.actual_mcf_result, expected_result)


if __name__ == '__main__':
    unittest.main()

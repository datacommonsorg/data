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
"""Tests for gho_categories_process.py"""

import os
import sys
import tempfile
import unittest

sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__)))))

from .gho_categories_process import process_categories
from .gho_categories_process import _COUNTERS_SV_GROUPS

_CODEDIR = os.path.dirname(os.path.realpath(__file__))

_INPUT_DATA_DIR = os.path.join(_CODEDIR, 'test_data', 'input')
_INPUT_SVS_FILENAME = os.path.join(_INPUT_DATA_DIR, 'SVs.mcf')
_INPUT_SV_CATEGORY_FILENAME = os.path.join(_INPUT_DATA_DIR, 'Categories.csv')

_EXPECTED_DIR = os.path.join(_CODEDIR, 'test_data', 'expected')
_EXPECTED_CATEGORY_FILENAME = os.path.join(_EXPECTED_DIR, 'categories.svg.mcf')
_EXPECTED_SVS_FILENAME = os.path.join(_EXPECTED_DIR, 'svs_output.mcf')

_EXPECTED_COUNTERS = {
    "lines_processed": 36,
    "svs_processed": 5,
    "other_category": 1,
    "existing_categories": 1,
}


def compare_files(t, output_path, expected_path):
    with open(output_path) as gotf:
        got = gotf.read()
        with open(expected_path) as wantf:
            want = wantf.read()
            t.assertEqual(got, want)


class ProcessTest(unittest.TestCase):

    def test_sv_categories_e2e(self):
        self.maxDiff = None
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_output_cat_file = os.path.join(tmp_dir, 'out_cat.svg.mcf')
            tmp_output_svs_file = os.path.join(tmp_dir, 'out_svs.mcf')
            process_categories(_INPUT_SVS_FILENAME, _INPUT_SV_CATEGORY_FILENAME,
                               tmp_output_cat_file, tmp_output_svs_file)

            self.assertEqual(_COUNTERS_SV_GROUPS, _EXPECTED_COUNTERS)
            compare_files(self, tmp_output_cat_file,
                          _EXPECTED_CATEGORY_FILENAME)
            compare_files(self, tmp_output_svs_file, _EXPECTED_SVS_FILENAME)


if __name__ == '__main__':
    unittest.main()

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
"""Tests for acs_spec_generator.py"""

import unittest
import tempfile

from .acs_spec_generator import *

_SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))
_TEST_ZIP = os.path.join(_SCRIPT_PATH, 'testdata', 'S2303_alabama_2019.zip')
_EXPECTED_SPEC_PATH = os.path.join(_SCRIPT_PATH, 'testdata',
                                   'expected_generated_spec.json')


class TestSpecGenerator(unittest.TestCase):

    def test_spec_generation(self):
        zip_path_list = [_TEST_ZIP]

        with tempfile.TemporaryDirectory() as tmp_dir:
            combined_spec_out = create_combined_spec(get_spec_list(), tmp_dir)
            all_columns = columns_from_zip_list(zip_path_list=zip_path_list)

            guess_spec = create_new_spec(all_columns,
                                         combined_spec_out,
                                         output_path=tmp_dir)

            # Sorting values in spec if they are of type list.
            guess_spec['ignoreColumns XXXXX'].sort()
            guess_spec['ignoreTokens XXXXX'].sort()

            # inferredSpec and universePVs are not deterministic.
            del guess_spec['inferredSpec']
            del guess_spec['universePVs']

            f = open(_EXPECTED_SPEC_PATH, 'r')
            expected_spec = json.load(f)
            f.close()

            self.assertEqual(guess_spec, expected_spec)


if __name__ == '__main__':
    unittest.main()

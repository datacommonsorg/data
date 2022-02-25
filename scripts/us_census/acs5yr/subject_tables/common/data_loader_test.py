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
""" Test for the data loader for the subject tables"""

import os
import sys
import unittest

# Allows the following module imports to work when running as a script
# relative to data/scripts/
sys.path.append('/'.join([
    '..' for x in filter(lambda x: x == '/',
                         os.path.abspath(__file__).split('data/scripts/')[1])
]))

from data_loader import process_subject_tables

base_path = os.path.dirname(__file__)


# TODO: Use a smaller spec for tests
class DataLoaderBaseTest(unittest.TestCase):
    # TODO: resolve issues to the spec and column map based on current working directory
    def test_zip_file_input(self):
        process_subject_tables(
            table_prefix='test_zip_alabama',
            input_path=os.path.join(base_path, "./testdata/s2702_alabama.zip"),
            output_dir=os.path.join(base_path, "./testdata/"),
            column_map_path=os.path.join(
                base_path, "./testdata/column_map_from_zip_expected.json"),
            spec_path=os.path.join(base_path, "./testdata/spec_s2702.json"),
            debug=False,
            delimiter='!!',
            has_percent=True)

    def test_csv_file_input(self):
        process_subject_tables(
            table_prefix='test_csv_2013',
            input_path=os.path.join(base_path,
                                    "./testdata/ACSST5Y2013_S2702.csv"),
            output_dir=os.path.join(base_path, "./testdata/"),
            column_map_path=os.path.join(
                base_path, "./testdata/column_map_from_zip_expected.json"),
            spec_path=os.path.join(base_path, "./testdata/spec_s2702.json"),
            debug=False,
            delimiter='!!',
            has_percent=True)

    # TODO: add tests for processing a directory of files


if __name__ == '__main__':
    unittest.main()

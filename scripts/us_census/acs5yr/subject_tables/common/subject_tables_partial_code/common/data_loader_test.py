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
from re import L
import unittest
import os
from .data_loader import process_subject_tables

base_path = os.path.dirname(__file__)

"""
Tasks:
====
1. add tests for processing a directory of files
2. add expected data for existing import files/spec along with assertEqual statements in the script
"""

class DataLoaderBaseTest(unittest.TestCase):
    def test_zip_file_input(self):
        prefix = 'test_zip_alabama'
        output_path = os.path.join(base_path, "./testdata/")
        process_subject_tables(
            table_prefix=prefix,
            input_path=os.path.join(base_path, "./testdata/s2702_alabama.zip"),
            output_dir=output_path,
            column_map_path=os.path.join(
                base_path, "./testdata/column_map_from_zip_expected.json"),
            spec_path=os.path.join(base_path, "./testdata/spec_s2702.json"),
            debug=False,
            delimiter='!!',
            has_percent=True)

        # remove all files after complete
        for files in os.listdir(output_path):
            if prefix in files:
                os.remove(os.path.join(output_path, files))

    def test_csv_file_input(self):
        prefix = 'test_csv_2013'
        output_path = os.path.join(base_path, "./testdata/")
        process_subject_tables(
            table_prefix=prefix,
            input_path=os.path.join(base_path,
                                    "./testdata/ACSST5Y2013_S2702.csv"),
            output_dir=output_path,
            column_map_path=os.path.join(
                base_path, "./testdata/column_map_from_zip_expected.json"),
            spec_path=os.path.join(base_path, "./testdata/spec_s2702.json"),
            debug=False,
            delimiter='!!',
            has_percent=True)

        # remove all files after complete
        for files in os.listdir(output_path):
            if prefix in files:
                os.remove(os.path.join(output_path, files))

if __name__ == '__main__':
    unittest.main()

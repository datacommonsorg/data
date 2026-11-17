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
import tempfile
import unittest

from .data_loader import SubjectTableDataLoaderBase
from .data_loader import process_subject_tables

base_path = os.path.dirname(__file__)


# TODO: Use a smaller spec for tests
class DataLoaderBaseTest(unittest.TestCase):
    # TODO: resolve issues to the spec and column map based on current working directory
    def test_zip_file_input(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            process_subject_tables(
                table_prefix='test_zip_alabama',
                input_path=os.path.join(base_path,
                                        "./testdata/s2702_alabama.zip"),
                output_dir=tmp_dir,
                column_map_path=os.path.join(
                    base_path, "./testdata/column_map_from_zip_expected.json"),
                spec_path=os.path.join(base_path, "./testdata/spec_s2702.json"),
                debug=False,
                delimiter='!!',
                has_percent=True)
            for ext in ['_cleaned.csv', '_output.mcf', '_output.tmcf']:
                with open(os.path.join(
                        tmp_dir, f'test_zip_alabama{ext}')) as actual, open(
                            os.path.join(base_path,
                                         f'./testdata/test_zip_alabama{ext}')
                        ) as expected:
                    self.assertEqual(actual.read(), expected.read())

    def test_csv_file_input(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            process_subject_tables(
                table_prefix='test_csv_2013',
                input_path=os.path.join(base_path,
                                        "./testdata/ACSST5Y2013_S2702.csv"),
                output_dir=tmp_dir,
                column_map_path=os.path.join(
                    base_path, "./testdata/column_map_from_zip_expected.json"),
                spec_path=os.path.join(base_path, "./testdata/spec_s2702.json"),
                debug=False,
                delimiter='!!',
                has_percent=True)
            for ext in ['_cleaned.csv', '_output.mcf', '_output.tmcf']:
                with open(os.path.join(
                        tmp_dir, f'test_csv_2013{ext}')) as actual, open(
                            os.path.join(
                                base_path,
                                f'./testdata/test_csv_2013{ext}')) as expected:
                    self.assertEqual(actual.read(), expected.read())

    def test_invalid_filename_raises_value_error(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            invalid_csv = os.path.join(tmp_dir, "invalid_filename_S2702.csv")
            with open(
                    os.path.join(base_path, "./testdata/ACSST5Y2013_S2702.csv"),
                    "r") as src, open(invalid_csv, "w") as dst:
                dst.write(src.read())
            with self.assertRaisesRegex(ValueError,
                                        "Unable to extract year from filename"):
                process_subject_tables(
                    table_prefix='test_invalid',
                    input_path=invalid_csv,
                    output_dir=tmp_dir,
                    column_map_path=os.path.join(
                        base_path,
                        "./testdata/column_map_from_zip_expected.json"),
                    spec_path=os.path.join(base_path,
                                           "./testdata/spec_s2702.json"),
                    debug=False,
                    delimiter='!!',
                    has_percent=True)

    def test_top_bottom_code_normalization(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            loader = SubjectTableDataLoaderBase(
                table_id='test_norm',
                col_delimiter='!!',
                has_percent=False,
                debug=False,
                output_path_dir=tmp_dir,
                json_spec=os.path.join(base_path, "./testdata/spec_s2702.json"),
                column_map_path=os.path.join(
                    base_path, "./testdata/column_map_from_zip_expected.json"),
                decimal_places=3,
                estimate_period=5,
                header_row=1)
            self.assertEqual(loader._clean_cell_value('100-'), '100')
            self.assertEqual(loader._clean_cell_value('3,500+'), '3500')
            self.assertEqual(loader._clean_cell_value('3500+'), '3500')

    # TODO: add tests for processing a directory of files


if __name__ == '__main__':
    unittest.main()

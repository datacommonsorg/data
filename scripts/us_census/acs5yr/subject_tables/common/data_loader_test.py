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
import json
import os
import tempfile
import unittest

import pandas as pd

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
            df = pd.DataFrame(
                {'val': ['100-', '3,500+', '3500+', '-', '***', '1348']})
            cleaned_df = loader._replace_ignore_values_with_nan(df)
            self.assertEqual(cleaned_df['val'].iloc[0], '100')
            self.assertEqual(cleaned_df['val'].iloc[1], '3500')
            self.assertEqual(cleaned_df['val'].iloc[2], '3500')
            self.assertTrue(pd.isna(cleaned_df['val'].iloc[3]))
            self.assertTrue(pd.isna(cleaned_df['val'].iloc[4]))
            self.assertEqual(cleaned_df['val'].iloc[5], '1348')

            b25031_dir = os.path.join(base_path, "../B25031")
            test_csv_path = os.path.join(
                tmp_dir, "ACSDT5Y2023.B25031_data_with_overlays.csv")
            with open(test_csv_path, "w") as f:
                f.write("GEO_ID,NAME,B25031_001E,B25031_001M\n")
                f.write("Geography,Geographic Area Name,"
                        "Estimate!!Median gross rent --!!Total:,"
                        "Margin of Error!!Median gross rent --!!Total:\n")
                f.write("0400000US01,Alabama,100-,***\n")
                f.write('0400000US06,California,"3,500+",***\n')
                f.write("0400000US36,New York,3500+,***\n")
            process_subject_tables(
                table_prefix='test_b25031_codes',
                input_path=test_csv_path,
                output_dir=tmp_dir,
                column_map_path=os.path.join(b25031_dir,
                                             "testdata/column_map.json"),
                spec_path=os.path.join(b25031_dir, "B25031_spec.json"),
                debug=False,
                delimiter='!!',
                has_percent=False)
            out_df = pd.read_csv(
                os.path.join(tmp_dir, "test_b25031_codes_cleaned.csv"))
            self.assertEqual(out_df['Quantity'].tolist(), [100, 3500, 3500])

    def test_replace_ignore_values_with_nan_default_preserves_formatted(self):
        loader = SubjectTableDataLoaderBase.__new__(SubjectTableDataLoaderBase)
        df = pd.DataFrame({
            'id': ['0400000US06', '0400000US12', '0400000US36'],
            'Geographic Area Name': [
                'California, US', 'Florida, US', 'New York, US'
            ],
            'median_age': ['9.0+', '-', '38.5'],
            'median_income': ['250,000+', '2,500-', '(X)'],
        })
        cleaned = loader._replace_ignore_values_with_nan(df)
        self.assertEqual(cleaned.loc[0, 'median_age'], '9.0+')
        self.assertTrue(pd.isna(cleaned.loc[1, 'median_age']))
        self.assertEqual(cleaned.loc[0, 'median_income'], '250,000+')
        self.assertEqual(cleaned.loc[1, 'median_income'], '2,500-')
        self.assertTrue(pd.isna(cleaned.loc[2, 'median_income']))

    def test_replace_ignore_values_with_nan_cleans_top_bottom_coded(self):
        loader = SubjectTableDataLoaderBase.__new__(SubjectTableDataLoaderBase)
        loader.clean_numeric_values = True
        df = pd.DataFrame({
            'id': ['0400000US06', '0400000US12', '0400000US36'],
            'Geographic Area Name': [
                'California, US', 'Florida, US', 'New York, US'
            ],
            'median_age': ['9.0+', '-', '38.5'],
            'median_income': ['250,000+', '2,500-', '(X)'],
            'neg_val': ['-5.5', '+', '1,234'],
            'whitespace_col': ['   ', ' +', '42.0'],
        })
        cleaned = loader._replace_ignore_values_with_nan(df)
        self.assertEqual(cleaned.loc[0, 'Geographic Area Name'],
                         'California, US')
        self.assertEqual(cleaned.loc[0, 'median_age'], '9.0')
        self.assertTrue(pd.isna(cleaned.loc[1, 'median_age']))
        self.assertEqual(cleaned.loc[0, 'median_income'], '250000')
        self.assertEqual(cleaned.loc[1, 'median_income'], '2500')
        self.assertTrue(pd.isna(cleaned.loc[2, 'median_income']))
        self.assertEqual(cleaned.loc[0, 'neg_val'], '-5.5')
        self.assertTrue(pd.isna(cleaned.loc[1, 'neg_val']))
        self.assertEqual(cleaned.loc[2, 'neg_val'], '1234')
        self.assertTrue(pd.isna(cleaned.loc[0, 'whitespace_col']))
        self.assertTrue(pd.isna(cleaned.loc[1, 'whitespace_col']))
        self.assertEqual(cleaned.loc[2, 'whitespace_col'], '42.0')

    def test_init_sets_clean_numeric_values_flag(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            spec_path = os.path.join(tmp_dir, 'spec.json')
            cmap_path = os.path.join(tmp_dir, 'column_map.json')
            with open(spec_path, 'w') as f:
                json.dump({}, f)
            with open(cmap_path, 'w') as f:
                json.dump({}, f)

            loader_enabled = SubjectTableDataLoaderBase(
                table_id='test',
                output_path_dir=tmp_dir,
                json_spec=spec_path,
                column_map_path=cmap_path,
                clean_numeric_values=True)
            self.assertTrue(loader_enabled.clean_numeric_values)

            loader_default = SubjectTableDataLoaderBase(
                table_id='test',
                output_path_dir=tmp_dir,
                json_spec=spec_path,
                column_map_path=cmap_path)
            self.assertFalse(loader_default.clean_numeric_values)

    # TODO: add tests for processing a directory of files


if __name__ == '__main__':
    unittest.main()

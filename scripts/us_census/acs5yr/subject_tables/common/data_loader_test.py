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

    def test_top_bottom_coded_sentinel_filtering(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            csv_path = os.path.join(tmp_dir, 'ACSST5Y2013_S2702_sentinel.csv')
            with open(csv_path, 'w', encoding='utf-8') as f:
                f.write('"GEO_ID","S2702_C02_001E","S2702_C02_014E",'
                        '"S2702_C02_086E"\n'
                        '"id","Uninsured Population!!Estimate!!Total '
                        'population","Uninsured Population!!Estimate!!Median '
                        'age (years)","Uninsured Population!!Estimate!!Median '
                        'earnings (dollars)"\n'
                        '"0400000US01","655394","100+","2,500-"\n'
                        '"0400000US02","136696","31.6","250,000+"\n')
            process_subject_tables(
                table_prefix='test_sentinel',
                input_path=csv_path,
                output_dir=tmp_dir,
                column_map_path=os.path.join(
                    base_path, './testdata/column_map_from_zip_expected.json'),
                spec_path=os.path.join(base_path, './testdata/spec_s2702.json'),
                debug=False,
                delimiter='!!',
                has_percent=True)
            with open(os.path.join(tmp_dir, 'test_sentinel_cleaned.csv'),
                      encoding='utf-8') as actual:
                cleaned_content = actual.read()
            self.assertNotIn('2,500-', cleaned_content)
            self.assertNotIn('250,000+', cleaned_content)
            self.assertNotIn('100+', cleaned_content)
            self.assertIn(
                '2013,geoId/01,dcid:Count_Person_NoHealthInsurance,655394.0',
                cleaned_content)
            self.assertIn(
                '2013,geoId/01,dcid:Median_Age_Person_NoHealthInsurance,'
                '100.0,Years', cleaned_content)
            self.assertIn(
                '2013,geoId/01,dcid:Median_Income_Person_16OrMoreYears_'
                'NoHealthInsurance_WithEarnings,2500.0,USDollar',
                cleaned_content)
            self.assertIn(
                '2013,geoId/02,dcid:Median_Income_Person_16OrMoreYears_'
                'NoHealthInsurance_WithEarnings,250000.0,USDollar',
                cleaned_content)

    # TODO: add tests for processing a directory of files


if __name__ == '__main__':
    unittest.main()

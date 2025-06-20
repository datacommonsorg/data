# Copyright 2025 Google LLC
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
'''
Unit tests for air_quality_aggregate.py

Usage: python3 -m unittest discover -v -s ../ -p "air_quality_aggregate_test.py"
'''
import unittest, csv, os, sys, tempfile, zipfile, io
from absl import app
from absl import flags
from absl import logging

_FLAGS = flags.FLAGS

module_dir_ = os.path.dirname(__file__)

sys.path.append(module_dir_)

from air_quality_aggregate import create_csv, write_csv, process

MODULE_DIR = os.path.dirname(os.path.abspath(__file__))


class TestCriteriaGasesTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        from absl import flags
        flags.FLAGS(
            ["air_quality_aggregate_test.py", "--output_file_path", "output"])

    def test_write_csv_county(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            with open(
                    os.path.join(
                        module_dir_,
                        'test_data/test_aggregate_import_data_county.csv'),
                    'r') as f:
                test_csv = os.path.join(tmp_dir, 'test_csv.csv')
                create_csv(test_csv)

                reader = csv.DictReader(f)
                write_csv(test_csv, reader)

                expected_csv = os.path.join(
                    module_dir_, 'test_data/test_aggregate_import_county.csv')
                with open(test_csv, 'r') as test:
                    test_str: str = test.read()
                    with open(expected_csv, 'r') as expected:
                        expected_str: str = expected.read()
                        self.assertEqual(test_str, expected_str)
                os.remove(test_csv)

    def test_write_csv_csba(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            with open(
                    os.path.join(
                        module_dir_,
                        'test_data/test_aggregate_import_data_cbsa.csv'),
                    'r') as f:
                test_csv = os.path.join(tmp_dir, 'test_csv.csv')
                create_csv(test_csv)

                reader = csv.DictReader(f)
                write_csv(test_csv, reader)
                expected_csv = os.path.join(
                    module_dir_, 'test_data/test_aggregate_import_cbsa.csv')
                with open(test_csv, 'r') as test:
                    test_str: str = test.read()
                    with open(expected_csv, 'r') as expected:
                        expected_str: str = expected.read()
                        self.assertEqual(test_str, expected_str)
                os.remove(test_csv)

    @classmethod
    def setUpClass(cls):
        #from absl import flags
        if not flags.FLAGS.is_parsed():
            flags.FLAGS(["air_quality_aggregate_test.py"])

    def test_process_generates_correct_output(self):
        with tempfile.TemporaryDirectory(
        ) as tmp_input_dir, tempfile.TemporaryDirectory() as tmp_output_dir:
            # Update FLAGS
            _FLAGS.input_file_path = tmp_input_dir
            _FLAGS.output_file_path = tmp_output_dir
            _FLAGS.aggregate_start_year = 2020
            _FLAGS.aggregate_end_year = 2021  # only 2020 will be processed

            # Sample CSV row
            row = {
                'Date': '2020-01-01',
                'State Code': '06',
                'County Code': '075',
                'AQI': '45',
                'Defining Parameter': 'Ozone',
                'Defining Site': '06-075-0001'
            }

            # Generate CSV content
            csv_content = io.StringIO()
            writer = csv.DictWriter(csv_content, fieldnames=row.keys())
            writer.writeheader()
            writer.writerow(row)
            csv_bytes = csv_content.getvalue().encode('utf-8')

            # Create ZIP files for county and cbsa
            for prefix in [
                    'daily_aqi_by_county_2020', 'daily_aqi_by_cbsa_2020'
            ]:
                zip_path = os.path.join(tmp_input_dir, f"{prefix}.zip")
                with zipfile.ZipFile(zip_path, 'w') as zipf:
                    zipf.writestr(f"{prefix}.csv", csv_bytes)

            # Run the process method
            process(tmp_input_dir, 2020, 2021)

            # Check if the output files were created
            expected_csv_path = os.path.join(MODULE_DIR, tmp_output_dir,
                                             'EPA_AQI.csv')
            expected_tmcf_path = os.path.join(MODULE_DIR, tmp_output_dir,
                                              'EPA_AQI.tmcf')

            self.assertTrue(os.path.isfile(expected_csv_path),
                            "CSV output file not created")

            # Validate CSV content
            with open(expected_csv_path, 'r') as f:
                lines = f.readlines()
                self.assertGreaterEqual(len(lines),
                                        2)  # At least header + 1 data row
                self.assertIn("dcid:geoId/06075", lines[1])
                self.assertIn("dcs:Ozone", lines[1])
                self.assertIn("dcid:epa/060750001", lines[1])


if __name__ == '__main__':
    unittest.main()

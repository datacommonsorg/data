# Copyright 2026 Google LLC
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
"""Unit tests for preprocess.py in statvar_imports/oecd/regional_education."""

import csv
import os
import shutil
import sys
import tempfile
import unittest

# Ensure the directory containing preprocess.py is in sys.path when tests
# are executed from the repository root or CI harnesses.
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if _SCRIPT_DIR not in sys.path:
    sys.path.insert(0, _SCRIPT_DIR)

from preprocess import _filter_csv, preprocess


class PreprocessTest(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.gcs_source_dir = os.path.join(self.temp_dir, 'gcs_output', 'source_files')
        os.makedirs(self.gcs_source_dir, exist_ok=True)
        self.places_file = os.path.join(
            self.temp_dir, 'oecd_regional_education_places_resolved.csv')

    def tearDown(self):
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def _write_places_resolved(self, rows):
        with open(self.places_file, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['place_name', 'dcid', 'name', 'country'])
            for row in rows:
                writer.writerow(row)

    def test_filter_csv_basic_mapping_and_projection(self):
        """Test place resolution and required columns projection."""
        src_csv = os.path.join(self.temp_dir, 'input.csv')
        dst_csv = os.path.join(self.temp_dir, 'output.csv')
        valid_places = {
            'US56': 'dcid:geoId/56',
            'PT19': 'dcid:nuts/PT19',
        }

        header = [
            'REF_AREA', 'TIME_PERIOD', 'UNIT_MULT', 'SEX', 'Education level',
            'AGE', 'OBS_VALUE', 'STATISTICAL_OPERATION', 'EXTRA_COL'
        ]
        rows = [
            ['US56', '2020', '0', '_T', 'Tertiary education', 'Y25T64', '35.5', 'NORMAL', 'foo'],
            ['PT19', '2021', '0', 'F', 'Secondary education', 'Y25T34', '42.1', '', 'bar'],
        ]
        with open(src_csv, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(header)
            writer.writerows(rows)

        _filter_csv(src_csv, dst_csv, valid_places)

        with open(dst_csv, 'r', encoding='utf-8') as f:
            out_rows = list(csv.reader(f))

        expected_header = [
            'REF_AREA', 'TIME_PERIOD', 'UNIT_MULT', 'SEX', 'Education level',
            'AGE', 'OBS_VALUE'
        ]
        self.assertEqual(out_rows[0], expected_header)
        self.assertEqual(len(out_rows), 3)
        self.assertEqual(out_rows[1][0], 'dcid:geoId/56')
        self.assertEqual(out_rows[1][6], '35.5')
        self.assertEqual(out_rows[2][0], 'dcid:nuts/PT19')
        self.assertEqual(out_rows[2][6], '42.1')

    def test_filter_csv_drops_statistical_operation_se(self):
        """Test rows with STATISTICAL_OPERATION == 'SE' (Standard Error) are dropped."""
        src_csv = os.path.join(self.temp_dir, 'input.csv')
        dst_csv = os.path.join(self.temp_dir, 'output.csv')
        valid_places = {'US56': 'dcid:geoId/56'}

        header = [
            'REF_AREA', 'TIME_PERIOD', 'UNIT_MULT', 'SEX', 'Education level',
            'AGE', 'OBS_VALUE', 'STATISTICAL_OPERATION'
        ]
        rows = [
            ['US56', '2020', '0', '_T', 'Tertiary education', 'Y25T64', '35.5', 'SE'],
            ['US56', '2020', '0', '_T', 'Tertiary education', 'Y25T64', '35.5', 'ESTIMATE'],
        ]
        with open(src_csv, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(header)
            writer.writerows(rows)

        _filter_csv(src_csv, dst_csv, valid_places)

        with open(dst_csv, 'r', encoding='utf-8') as f:
            out_rows = list(csv.reader(f))

        self.assertEqual(len(out_rows), 2)  # Header + 1 kept row
        self.assertEqual(out_rows[1][0], 'dcid:geoId/56')

    def test_filter_csv_drops_empty_obs_value(self):
        """Test rows with empty or whitespace OBS_VALUE are dropped."""
        src_csv = os.path.join(self.temp_dir, 'input.csv')
        dst_csv = os.path.join(self.temp_dir, 'output.csv')
        valid_places = {'US56': 'dcid:geoId/56'}

        header = [
            'REF_AREA', 'TIME_PERIOD', 'UNIT_MULT', 'SEX', 'Education level',
            'AGE', 'OBS_VALUE'
        ]
        rows = [
            ['US56', '2020', '0', '_T', 'Tertiary education', 'Y25T64', ''],
            ['US56', '2020', '0', '_T', 'Tertiary education', 'Y25T64', '   '],
            ['US56', '2020', '0', '_T', 'Tertiary education', 'Y25T64', '12.4'],
        ]
        with open(src_csv, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(header)
            writer.writerows(rows)

        _filter_csv(src_csv, dst_csv, valid_places)

        with open(dst_csv, 'r', encoding='utf-8') as f:
            out_rows = list(csv.reader(f))

        self.assertEqual(len(out_rows), 2)  # Header + 1 kept row
        self.assertEqual(out_rows[1][6], '12.4')

    def test_filter_csv_logs_unmapped_places(self):
        """Test unmapped places are logged to counters/unresolved_places.csv."""
        src_csv = os.path.join(self.temp_dir, 'input.csv')
        dst_csv = os.path.join(self.temp_dir, 'output.csv')
        unmapped_log = os.path.join(self.temp_dir, 'unmapped.csv')
        valid_places = {'US56': 'dcid:geoId/56'}

        header = [
            'REF_AREA', 'TIME_PERIOD', 'UNIT_MULT', 'SEX', 'Education level',
            'AGE', 'OBS_VALUE'
        ]
        rows = [
            ['US56', '2020', '0', '_T', 'Tertiary education', 'Y25T64', '12.4'],
            ['UNKNOWN_1', '2020', '0', '_T', 'Tertiary education', 'Y25T64', '15.0'],
            ['UNKNOWN_2', '2020', '0', '_T', 'Tertiary education', 'Y25T64', '18.0'],
        ]
        with open(src_csv, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(header)
            writer.writerows(rows)

        _filter_csv(src_csv, dst_csv, valid_places, unmapped_log_path=unmapped_log)

        with open(dst_csv, 'r', encoding='utf-8') as f:
            out_rows = list(csv.reader(f))
        self.assertEqual(len(out_rows), 2)

        self.assertTrue(os.path.exists(unmapped_log))
        with open(unmapped_log, 'r', encoding='utf-8') as f:
            unmapped_entries = [row[0] for row in csv.reader(f)]
        self.assertIn('UNKNOWN_1', unmapped_entries)
        self.assertIn('UNKNOWN_2', unmapped_entries)

    def test_filter_csv_preserves_already_prefixed_dcid(self):
        """Test clean_ref starting with 'dcid:' is preserved even without explicit map entry."""
        src_csv = os.path.join(self.temp_dir, 'input.csv')
        dst_csv = os.path.join(self.temp_dir, 'output.csv')
        valid_places = {}

        header = [
            'REF_AREA', 'TIME_PERIOD', 'UNIT_MULT', 'SEX', 'Education level',
            'AGE', 'OBS_VALUE'
        ]
        rows = [
            ['dcid:country/USA', '2020', '0', '_T', 'Tertiary education', 'Y25T64', '45.0'],
        ]
        with open(src_csv, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(header)
            writer.writerows(rows)

        _filter_csv(src_csv, dst_csv, valid_places)

        with open(dst_csv, 'r', encoding='utf-8') as f:
            out_rows = list(csv.reader(f))
        self.assertEqual(len(out_rows), 2)
        self.assertEqual(out_rows[1][0], 'dcid:country/USA')

    def test_filter_csv_raises_on_empty_source(self):
        """Test ValueError is raised when source file is empty."""
        src_csv = os.path.join(self.temp_dir, 'empty.csv')
        dst_csv = os.path.join(self.temp_dir, 'output.csv')
        with open(src_csv, 'w', encoding='utf-8') as f:
            pass

        with self.assertRaises(ValueError):
            _filter_csv(src_csv, dst_csv, {'US56': 'dcid:geoId/56'})

    def test_filter_csv_raises_when_all_rows_dropped(self):
        """Test critical safeguard: ValueError raised if 100% of rows are dropped."""
        src_csv = os.path.join(self.temp_dir, 'input.csv')
        dst_csv = os.path.join(self.temp_dir, 'output.csv')
        valid_places = {'US56': 'dcid:geoId/56'}

        header = [
            'REF_AREA', 'TIME_PERIOD', 'UNIT_MULT', 'SEX', 'Education level',
            'AGE', 'OBS_VALUE'
        ]
        rows = [
            ['UNMAPPED', '2020', '0', '_T', 'Tertiary education', 'Y25T64', '12.4'],
        ]
        with open(src_csv, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(header)
            writer.writerows(rows)

        with self.assertRaises(ValueError) as ctx:
            _filter_csv(src_csv, dst_csv, valid_places)
        self.assertIn("Critical: All 1 rows in", str(ctx.exception))

    def test_filter_csv_raises_on_missing_required_columns(self):
        """Test ValueError is raised when source CSV lacks any required columns."""
        src_csv = os.path.join(self.temp_dir, 'input.csv')
        dst_csv = os.path.join(self.temp_dir, 'output.csv')
        valid_places = {'US56': 'dcid:geoId/56'}

        # Omit 'Education level' and 'SEX'
        header = ['REF_AREA', 'TIME_PERIOD', 'UNIT_MULT', 'AGE', 'OBS_VALUE']
        rows = [['US56', '2020', '0', 'Y25T64', '35.5']]
        with open(src_csv, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(header)
            writer.writerows(rows)

        with self.assertRaises(ValueError) as ctx:
            _filter_csv(src_csv, dst_csv, valid_places)
        self.assertIn("missing required columns", str(ctx.exception))
        self.assertIn("Education level", str(ctx.exception))
        self.assertIn("SEX", str(ctx.exception))

    def test_preprocess_e2e_with_raw_file(self):
        """Test full preprocess execution when raw SDMX file is present in source_files."""
        self._write_places_resolved([
            ['US56', 'geoId/56', 'Wyoming', 'United States'],
            ['PT19', 'dcid:nuts/PT19', 'Oeste', 'Portugal'],
        ])

        raw_filename = 'A.EDU_ATTAIN.DSD_REG_EDU.csv'
        raw_path = os.path.join(self.gcs_source_dir, raw_filename)
        header = [
            'REF_AREA', 'TIME_PERIOD', 'UNIT_MULT', 'SEX', 'Education level',
            'AGE', 'OBS_VALUE', 'STATISTICAL_OPERATION'
        ]
        rows = [
            ['US56', '2020', '0', '_T', 'Tertiary education', 'Y25T64', '35.5', 'NORMAL'],
            ['PT19', '2021', '0', 'F', 'Secondary education', 'Y25T34', '42.1', ''],
            ['US56', '2020', '0', '_T', 'Tertiary education', 'Y25T64', '1.2', 'SE'],
        ]
        with open(raw_path, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(header)
            writer.writerows(rows)

        preprocess(base_path=self.temp_dir)

        target_csv = os.path.join(self.gcs_source_dir, 'oecd_regional_education_data.csv')
        self.assertTrue(os.path.isfile(target_csv))
        # Verify raw file was preserved for GCS archiving
        self.assertTrue(os.path.isfile(raw_path))
        # Verify tmp file was replaced
        self.assertFalse(os.path.isfile(os.path.join(self.gcs_source_dir, 'filtered_tmp.csv')))

        with open(target_csv, 'r', encoding='utf-8') as f:
            out_rows = list(csv.reader(f))
        self.assertEqual(len(out_rows), 3)  # Header + 2 valid rows
        self.assertEqual(out_rows[1][0], 'dcid:geoId/56')
        self.assertEqual(out_rows[2][0], 'dcid:nuts/PT19')

    def test_preprocess_selects_newest_candidate_file(self):
        """Test newest candidate file by mtime is selected when multiple candidates exist."""
        import time

        self._write_places_resolved([
            ['US56', 'geoId/56', 'Wyoming', 'United States'],
        ])

        header = [
            'REF_AREA', 'TIME_PERIOD', 'UNIT_MULT', 'SEX', 'Education level',
            'AGE', 'OBS_VALUE'
        ]
        # Create older file
        older_file = os.path.join(self.gcs_source_dir, 'A.........')
        with open(older_file, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(header)
            writer.writerow(['US56', '2020', '0', '_T', 'Tertiary education', 'Y25T64', '10.0'])

        # Set older mtime
        old_time = time.time() - 100
        os.utime(older_file, (old_time, old_time))

        # Create newer file with different pattern (e.g. OECD_REG_EDU.csv)
        newer_file = os.path.join(self.gcs_source_dir, 'OECD_REG_EDU.csv')
        with open(newer_file, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(header)
            writer.writerow(['US56', '2020', '0', '_T', 'Tertiary education', 'Y25T64', '99.0'])

        new_time = time.time()
        os.utime(newer_file, (new_time, new_time))

        preprocess(base_path=self.temp_dir)

        target_csv = os.path.join(self.gcs_source_dir, 'oecd_regional_education_data.csv')
        with open(target_csv, 'r', encoding='utf-8') as f:
            out_rows = list(csv.reader(f))
        # Value 99.0 from newer_file should have been selected
        self.assertEqual(out_rows[1][6], '99.0')

    def test_preprocess_missing_places_resolved_raises(self):
        """Test preprocess raises FileNotFoundError if places_resolved file does not exist."""
        if os.path.exists(self.places_file):
            os.remove(self.places_file)
        with self.assertRaises(FileNotFoundError):
            preprocess(base_path=self.temp_dir)


if __name__ == '__main__':
    unittest.main()

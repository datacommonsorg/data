# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the 'License');
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#         https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an 'AS IS' BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Unit tests for preprocess.py."""

import csv
import os
import sys
import tempfile
import unittest

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.abspath(os.path.join(_SCRIPT_DIR, '..', '..'))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from statvar_imports.israel_census import preprocess  # pylint: disable=g-import-not-at-top


class PreprocessTest(unittest.TestCase):

    def test_convert_dem1_2_and_dem1_14_xls_to_unscaled_csv(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            raw_dir = os.path.join(tmp_dir, 'input_files')
            out_dir = os.path.join(tmp_dir, 'staged_inputs')
            os.makedirs(raw_dir, exist_ok=True)

            # Write mock dem1_2.xls (as CSV rows for _read_mifkad_table_rows)
            with open(os.path.join(raw_dir, 'dem1_2.xls'),
                      'w',
                      encoding='utf-8',
                      newline='') as fp:
                writer = csv.writer(fp, lineterminator='\n')
                writer.writerow([
                    '',
                    '74121.8',
                    '36638.9',
                    '37482.9',
                    '68232.0',
                    '33630.3',
                    '34601.8',
                    '5889.8',
                    '3008.7',
                    '2881.1',
                    'TOTAL',
                ])

            # Write mock dem1_14.xls
            with open(os.path.join(raw_dir, 'dem1_14.xls'),
                      'w',
                      encoding='utf-8',
                      newline='') as fp:
                writer = csv.writer(fp, lineterminator='\n')
                writer.writerow([
                    '0-14',
                    '20906',
                    '20906',
                    '-',
                    '-',
                    '-',
                    '-',
                    '14-0',
                ])

            preprocess.build_input_tables(raw_dir, out_dir)

            with open(
                    os.path.join(out_dir,
                                 'isr_urban_rural_gender_aa1_2008.csv'),
                    'r',
                    encoding='utf-8',
            ) as fp:
                urb_rows = list(csv.DictReader(fp))
            self.assertEqual(len(urb_rows), 1)
            self.assertEqual(urb_rows[0]['Region'], 'ISR')
            self.assertEqual(urb_rows[0]['Year'], '2008')
            self.assertEqual(urb_rows[0]['Grand totalTotal'], '')
            self.assertEqual(urb_rows[0]['Grand totalMales'], '36638.9')
            self.assertEqual(urb_rows[0]['Urban localitiesTotal'], '68232')

            with open(
                    os.path.join(out_dir, 'isr_age_maritalstatus_2008.csv'),
                    'r',
                    encoding='utf-8',
            ) as fp:
                age_rows = list(csv.DictReader(fp))
            self.assertEqual(len(age_rows), 1)
            self.assertEqual(age_rows[0]['Region'], 'ISR')
            self.assertEqual(age_rows[0]['Year'], '2008')
            self.assertEqual(age_rows[0]['Age group'], '0-14')
            self.assertEqual(age_rows[0]['Total'], '20906')
            self.assertEqual(age_rows[0]['Never married'], '20906')

    def test_build_input_tables_copies_existing_csv_files_untouched(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            raw_dir = os.path.join(tmp_dir, 'input_files')
            out_dir = os.path.join(tmp_dir, 'staged_inputs')
            os.makedirs(raw_dir, exist_ok=True)

            pop_csv = os.path.join(raw_dir,
                                   'isr_population_religion_1949_2021.csv')
            raw_content = 'Region,Year,total,jews,nonjews,Others,arab\nISR,1949,1173.9,1013.9,160,0,160\n'
            with open(pop_csv, 'w', encoding='utf-8', newline='') as fp:
                fp.write(raw_content)

            preprocess.build_input_tables(raw_dir, out_dir)
            staged_pop = os.path.join(out_dir,
                                      'isr_population_religion_1949_2021.csv')
            with open(staged_pop, 'r', encoding='utf-8') as fp:
                self.assertEqual(fp.read(), raw_content)


if __name__ == '__main__':
    unittest.main()

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

    def test_extract_cbs_series_population_vital_and_cod_from_raw_csv(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            pop_csv = os.path.join(tmp_dir,
                                   'cbs_series_population_religion.csv')
            with open(pop_csv, 'w', encoding='utf-8', newline='') as fp:
                writer = csv.writer(fp, lineterminator='\n')
                writer.writerow([
                    'id',
                    'time_name',
                    'unit_name',
                    'path_level4_name',
                    'path_name_id_name',
                    'obs_time_period',
                    'obs_value',
                ])
                writer.writerow([
                    '3700',
                    'Year',
                    'Thousands',
                    'At End of Period',
                    'Total',
                    '2024-01',
                    '10065.5',
                ])
                writer.writerow([
                    '3701',
                    'Year',
                    'Thousands',
                    'At End of Period',
                    'Jews',
                    '2024-01',
                    '7212.9',
                ])
                writer.writerow([
                    '3703',
                    'Year',
                    'Thousands',
                    'At End of Period',
                    'Jews and Others',
                    '2024-01',
                    '7693.3',
                ])
                writer.writerow([
                    '3704',
                    'Year',
                    'Thousands',
                    'At End of Period',
                    'Arab Population',
                    '2024-01',
                    '2111.8',
                ])
                writer.writerow([
                    '3700',
                    'Year',
                    'Thousands',
                    'At End of Period',
                    'Total',
                    '2025-01',
                    '7766.7',
                ])
                writer.writerow([
                    '3703',
                    'Year',
                    'Thousands',
                    'At End of Period',
                    'Jews and Others',
                    '2025-01',
                    '7730.0',
                ])
                writer.writerow([
                    '3704',
                    'Year',
                    'Thousands',
                    'At End of Period',
                    'Arab Population',
                    '2025-01',
                    '2130.6',
                ])

            pop_obs = preprocess._extract_cbs_series_population_religion_obs(
                pop_csv)
            self.assertNotIn(('country/ISR', '2025', 'IND_Count_Person'),
                             pop_obs)
            self.assertEqual(
                pop_obs[('country/ISR', '2024', 'IND_Count_Person')],
                '10065500')
            self.assertEqual(
                pop_obs[('country/ISR', '2024', 'IND_Count_Person_Judaism')],
                '7212900',
            )
            self.assertEqual(
                pop_obs[('country/ISR', '2024', 'IND_Count_Person_Arab')],
                '2111800',
            )
            self.assertEqual(
                pop_obs[(
                    'country/ISR',
                    '2024',
                    'IND_Count_Person_CBSIsraelNonJudaismOrNonArabChristianOrNoReligion',
                )],
                '480400',
            )

            vital_csv = os.path.join(tmp_dir, 'cbs_series_vital_statistics.csv')
            with open(vital_csv, 'w', encoding='utf-8', newline='') as fp:
                writer = csv.writer(fp, lineterminator='\n')
                writer.writerow([
                    'id',
                    'time_name',
                    'path_level4_name',
                    'path_name_id_name',
                    'obs_time_period',
                    'obs_value',
                ])
                writer.writerow([
                    '3752',
                    'Year',
                    'Arab Population',
                    'Live-Births',
                    '2023-01',
                    '42862',
                ])

            vital_obs = preprocess._extract_cbs_series_vital_statistics_obs(
                vital_csv)
            self.assertEqual(
                vital_obs[(
                    'country/ISR',
                    '2023',
                    'IND_Count_BirthEvent_LiveBirth_Arab',
                )],
                '42862',
            )

            cod_csv = os.path.join(tmp_dir, 'cbs_series_cause_of_death.csv')
            with open(cod_csv, 'w', encoding='utf-8', newline='') as fp:
                writer = csv.writer(fp, lineterminator='\n')
                writer.writerow([
                    'id',
                    'time_name',
                    'path_level4_name',
                    'path_name_id_name',
                    'obs_time_period',
                    'obs_value',
                ])
                writer.writerow([
                    '70015',
                    'Year',
                    'Ischaemic Heart Diseases',
                    'Total Population| Males',
                    '2022-01',
                    '24.0',
                ])

            cod_obs = preprocess._extract_cbs_series_cause_of_death_obs(cod_csv)
            self.assertEqual(
                cod_obs[(
                    'country/ISR',
                    '2022',
                    'IND_Count_MortalityEvent_CoronaryHeartDisease_Male_AsAFractionOf_Count_Person_Male',
                )],
                '24',
            )

    def test_extract_cbs_boardsgenerator_census_2008_obs_from_csv(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            c2008_csv = os.path.join(tmp_dir, 'cbs_census_2008_regions.csv')
            with open(c2008_csv, 'w', encoding='utf-8', newline='') as fp:
                writer = csv.writer(fp, lineterminator='\n')
                writer.writerow([
                    'region_code',
                    'data_mode',
                    'group_id',
                    'group_name',
                    'subject_id',
                    'subject_name',
                    'value',
                ])
                writer.writerow([
                    '999',
                    'Machoz',
                    '3',
                    'Total',
                    '218',
                    'Those aged 15 and over – total (thousands)',
                    '5227.3',
                ])
                writer.writerow([
                    '21',
                    'Nafa',
                    '2',
                    'Demography',
                    '18',
                    'Population – total (thousands)',
                    '104.5',
                ])
                writer.writerow([
                    '21',
                    'Nafa',
                    '3',
                    'Total',
                    '224',
                    'Those aged 65+ – total (thousands) **',
                    '8.4',
                ])

            by_ds = preprocess._extract_cbs_boardsgenerator_census_2008_obs(
                c2008_csv)
            self.assertEqual(
                by_ds['isr_agebracket_gender_aa1_2008'][(
                    'country/ISR',
                    '2008',
                    'IND_Count_Person_15OrMoreYears',
                )],
                '5227300',
            )
            self.assertEqual(
                by_ds['isr_subdistrict_population_gender_2008'][(
                    'wikidataId/Q5423089',
                    '2008',
                    'IND_Count_Person',
                )],
                '104500',
            )
            self.assertEqual(
                by_ds['isr_subdistrict_age_gender_2008'][(
                    'wikidataId/Q5423089',
                    '2008',
                    'IND_Count_Person_65OrMoreYears',
                )],
                '8400',
            )

    def test_build_input_tables_writes_all_11_wide_and_2d_csvs(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            raw_dir = os.path.join(tmp_dir, 'input_files')
            out_dir = os.path.join(tmp_dir, 'staged_inputs')
            os.makedirs(raw_dir, exist_ok=True)
            pop_csv = os.path.join(raw_dir,
                                   'cbs_series_population_religion.csv')
            with open(pop_csv, 'w', encoding='utf-8', newline='') as fp:
                writer = csv.writer(fp, lineterminator='\n')
                writer.writerow(
                    ['id', 'time_name', 'obs_time_period', 'obs_value'])
                writer.writerow(['3700', 'Year', '2020-01', '9289.8'])

            tables = preprocess.build_input_tables(raw_dir, out_dir)
            self.assertEqual(len(tables), 11)
            with open(
                    os.path.join(out_dir,
                                 'isr_population_religion_1949_2021.csv'),
                    'r',
                    encoding='utf-8',
            ) as fp:
                rows = list(csv.DictReader(fp))
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]['observationAbout'], 'country/ISR')
            self.assertEqual(rows[0]['observationDate'], '2020')
            self.assertEqual(rows[0]['total'], '9289800')


if __name__ == '__main__':
    unittest.main()

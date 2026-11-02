#!/usr/bin/env python3
# Copyright 2026 Google LLC
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
"""Unit and processor tests for Sweden Census Category 1 (Demographic) import."""

import csv
import glob
import json
import os
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

from absl import flags

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
  sys.path.insert(0, SCRIPT_DIR)

import download_demographic  # pylint: disable=g-import-not-at-top

FLAGS = flags.FLAGS
if not FLAGS.is_parsed():
  FLAGS.mark_as_parsed()

TEST_DATA_DIR = os.path.join(SCRIPT_DIR, 'test_data')
SV_PROCESSOR = os.environ.get(
    'SV_PROCESSOR',
    os.path.abspath(
        os.path.join(
            SCRIPT_DIR,
            '..',
            '..',
            '..',
            'tools',
            'statvar_importer',
            'stat_var_processor.py',
        )
    ),
)
PLACES_CSV = os.path.join(SCRIPT_DIR, 'sweden_places_resolved.csv')


class DownloadDemographicUnitTest(unittest.TestCase):
  """Hermetic unit tests for download_demographic.py functions."""

  def test_parse_int_value(self):
    self.assertEqual(download_demographic._parse_int_value('12345'), 12345)
    self.assertEqual(download_demographic._parse_int_value('..'), 0)
    self.assertEqual(download_demographic._parse_int_value('-'), 0)
    self.assertEqual(download_demographic._parse_int_value(''), 0)

  def test_load_nuts_hierarchy_and_age_to_bracket(self):
    county_name_to_nuts, nuts_groups = download_demographic._load_nuts_hierarchy(
        PLACES_CSV
    )
    self.assertEqual(len(county_name_to_nuts), 21)
    self.assertEqual(len(nuts_groups['nuts1']), 3)
    self.assertEqual(len(nuts_groups['nuts2']), 8)
    self.assertEqual(len(nuts_groups['nuts3']), 21)
    self.assertEqual(download_demographic._age_to_bracket('0', 105), '0-4 år')
    self.assertEqual(download_demographic._age_to_bracket('5', 105), '5-14 år')
    self.assertEqual(
        download_demographic._age_to_bracket('95', 105), '95-104 år'
    )
    self.assertEqual(
        download_demographic._age_to_bracket('110+', 105), '105+ år'
    )
    self.assertEqual(download_demographic._age_to_bracket('95', 95), '95+ år')
    self.assertIsNone(download_demographic._age_to_bracket('tot', 95))

  def test_download_and_write_national_files_mocked(self):
    meta_payload = json.dumps({
        'variables': [
            {'code': 'Alder', 'values': ['0', '5', '105', '110+']},
            {
                'code': 'Kon',
                'values': ['1', '2'],
                'valueTexts': ['män', 'kvinnor'],
            },
            {'code': 'ContentsCode', 'values': ['0000053A']},
            {'code': 'Tid', 'values': ['1860', '2024']},
        ]
    }).encode('utf-8')

    post_payload = json.dumps({
        'data': [
            {'key': ['0', '1', '1860'], 'values': ['100']},
            {'key': ['0', '2', '1860'], 'values': ['90']},
            {'key': ['5', '1', '2024'], 'values': ['200']},
            {'key': ['105', '2', '1860'], 'values': ['..']},
            {'key': ['110+', '2', '2024'], 'values': ['5']},
        ]
    }).encode('utf-8')

    with tempfile.TemporaryDirectory() as tmp_dir:
      with mock.patch.object(
          download_demographic, 'REQUEST_SLEEP_SECONDS', 0.0
      ), mock.patch.object(
          download_demographic.download_util,
          'request_url',
          side_effect=[meta_payload, post_payload],
      ):
        years = download_demographic.download_and_write_national_files(
            output_dir=tmp_dir,
            start_year=1860,
            end_year=2024,
        )
      self.assertEqual(years, ['1860', '2024'])
      for fname in (
          'population_country.csv',
          'population_gender_country.csv',
          'population_age_country.csv',
          'population_age_gender_country.csv',
      ):
        fpath = os.path.join(tmp_dir, fname)
        self.assertTrue(os.path.exists(fpath), f'Missing {fname}')
        with open(fpath, 'r', encoding='utf-8') as f:
          rows = list(csv.reader(f))
        self.assertGreaterEqual(len(rows), 4)
        self.assertIn('1860', rows[2])
        self.assertIn('2024', rows[2])

  def test_download_and_write_subnational_files_mocked(self):
    county_name_to_nuts, _ = download_demographic._load_nuts_hierarchy(
        PLACES_CSV
    )
    county_names = list(county_name_to_nuts.keys())
    county_codes = [f'{i + 1:02d}' for i in range(21)]
    muni_codes = [f'{1000 + i:04d}' for i in range(290)]
    muni_texts = [f'Muni{i}' for i in range(290)]
    meta_payload = json.dumps({
        'variables': [
            {
                'code': 'Region',
                'values': ['00'] + county_codes + muni_codes,
                'valueTexts': ['Riket'] + county_names + muni_texts,
            },
            {
                'code': 'Civilstand',
                'values': ['OG', 'G', 'S', 'ÄKL'],
                'valueTexts': ['ogifta', 'gifta', 'skilda', 'änkor/änklingar'],
            },
            {'code': 'Alder', 'values': ['0', '95', '100+', 'tot']},
            {
                'code': 'Kon',
                'values': ['1', '2'],
                'valueTexts': ['män', 'kvinnor'],
            },
            {'code': 'ContentsCode', 'values': ['BE0101N1']},
            {'code': 'Tid', 'values': ['1968', '2024']},
        ]
    }).encode('utf-8')

    county_payload = json.dumps({
        'data': [
            {'key': ['01', 'OG', '0', '1', '1968'], 'values': ['500']},
        ]
    }).encode('utf-8')
    muni_payload = json.dumps({
        'data': [
            {'key': ['1000', 'G', 'tot', '2', '2024'], 'values': ['300']},
        ]
    }).encode('utf-8')

    with tempfile.TemporaryDirectory() as tmp_dir:
      with mock.patch.object(
          download_demographic, 'REQUEST_SLEEP_SECONDS', 0.0
      ), mock.patch.object(
          download_demographic.download_util,
          'request_url',
          side_effect=[meta_payload, county_payload, muni_payload],
      ):
        years = download_demographic.download_and_write_subnational_files(
            output_dir=tmp_dir,
            places_csv_path=PLACES_CSV,
            start_year=1968,
            end_year=2024,
        )
      self.assertEqual(years, ['1968', '2024'])
      created_csvs = sorted(os.listdir(tmp_dir))
      self.assertEqual(len(created_csvs), 19)
      self.assertIn('population_nuts1.csv', created_csvs)
      self.assertIn('population_municipality.csv', created_csvs)
      self.assertIn('population_age_maritalstatus_gender_nuts3.csv', created_csvs)


class SwedenDemographicProcessorTest(unittest.TestCase):
  """Tests stat_var_processor across representative Demographic groups on test_data/."""

  def _run_and_verify(self, sample_prefix: str):
    input_csv = os.path.join(TEST_DATA_DIR, f'{sample_prefix}_input.csv')
    expected_csv = os.path.join(TEST_DATA_DIR, f'{sample_prefix}_output.csv')
    expected_tmcf = os.path.join(TEST_DATA_DIR, f'{sample_prefix}_output.tmcf')
    self.assertTrue(os.path.exists(input_csv), f'Missing {input_csv}')
    self.assertTrue(os.path.exists(expected_csv), f'Missing {expected_csv}')
    self.assertTrue(os.path.exists(expected_tmcf), f'Missing {expected_tmcf}')

    with tempfile.TemporaryDirectory() as tmp_dir:
      actual_prefix = os.path.join(tmp_dir, sample_prefix)
      test_config_path = os.path.join(tmp_dir, 'test_metadata.csv')
      with open(
          os.path.join(SCRIPT_DIR, 'demographic_metadata.csv'),
          'r',
          encoding='utf-8',
      ) as f_in, open(test_config_path, 'w', encoding='utf-8') as f_out:
        f_out.write(f_in.read())
        f_out.write('generate_statvar_mcf,False\n')
        f_out.write('generate_schema_mcf,False\n')
        f_out.write('reconcile_nodes,False\n')
        f_out.write('recon_lookup_api,False\n')

      cmd = [
          'python3',
          SV_PROCESSOR,
          f'--input_data={input_csv}',
          f'--pv_map={os.path.join(SCRIPT_DIR, "demographic_pvmap.csv")}',
          f'--config_file={test_config_path}',
          f'--places_resolved_csv={PLACES_CSV}',
          f'--statvar_dcid_remap_csv={os.path.join(SCRIPT_DIR, "demographic_statvar_remap.csv")}',
          '--skip_constant_csv_columns=False',
          f'--output_path={actual_prefix}',
      ]
      subprocess.run(cmd, check=True, cwd=tmp_dir)

      actual_csv = f'{actual_prefix}.csv'
      actual_tmcf = f'{actual_prefix}.tmcf'
      with open(expected_csv, 'r', encoding='utf-8') as f_exp, open(
          actual_csv, 'r', encoding='utf-8'
      ) as f_act:
        self.assertEqual(
            f_exp.read().splitlines(), f_act.read().splitlines()
        )

      with open(expected_tmcf, 'r', encoding='utf-8') as f_exp_tmcf, open(
          actual_tmcf, 'r', encoding='utf-8'
      ) as f_act_tmcf:
        self.assertEqual(
            sorted(f_exp_tmcf.read().splitlines()),
            sorted(f_act_tmcf.read().splitlines()),
        )

  def test_population_country(self):
    self._run_and_verify('population_country')

  def test_population_nuts1(self):
    self._run_and_verify('population_nuts1')

  def test_population_maritalstatus_gender_nuts1(self):
    self._run_and_verify('population_maritalstatus_gender_nuts1')

  def test_population_age_maritalstatus_gender_nuts1(self):
    self._run_and_verify('population_age_maritalstatus_gender_nuts1')

  def test_minimal_config_files_and_no_duplicates(self):
    self.assertEqual(
        glob.glob(os.path.join(SCRIPT_DIR, '*_metadata.csv')),
        [os.path.join(SCRIPT_DIR, 'demographic_metadata.csv')],
    )
    self.assertEqual(
        glob.glob(os.path.join(SCRIPT_DIR, '*_pvmap.csv')),
        [os.path.join(SCRIPT_DIR, 'demographic_pvmap.csv')],
    )
    self.assertEqual(
        glob.glob(os.path.join(SCRIPT_DIR, '*_statvar_remap.csv')),
        [os.path.join(SCRIPT_DIR, 'demographic_statvar_remap.csv')],
    )
    for fname in (
        'demographic_metadata.csv',
        'demographic_pvmap.csv',
        'demographic_statvar_remap.csv',
        'sweden_places_resolved.csv',
    ):
      fpath = os.path.join(SCRIPT_DIR, fname)
      with open(fpath, 'r', encoding='utf-8') as f:
        rows = [tuple(r) for r in csv.reader(f) if any(c.strip() for c in r)]
      data_rows = rows[1:]
      keys = [r[0].strip() for r in data_rows]
      self.assertEqual(
          len(keys), len(set(keys)), f'Duplicate keys found in {fname}'
      )
      self.assertEqual(
          len(data_rows),
          len(set(data_rows)),
          f'Duplicate rows found in {fname}',
      )


def tearDownModule():
  for cache_path in (
      os.path.join(SCRIPT_DIR, 'http_cache.sqlite'),
      'http_cache.sqlite',
  ):
    if os.path.exists(cache_path):
      try:
        os.remove(cache_path)
      except OSError:
        pass


if __name__ == '__main__':
  unittest.main()

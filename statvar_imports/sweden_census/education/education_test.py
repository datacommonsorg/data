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
"""Unit tests for Sweden Census Category 3 (Education) import."""

import collections
import csv
import json
import os
import sys
import tempfile
import unittest
from unittest import mock
import requests

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
  sys.path.insert(0, SCRIPT_DIR)

import download_education  # pylint: disable=g-import-not-at-top

TEST_DATA_DIR = os.path.join(SCRIPT_DIR, 'test_data')


def _make_valid_var_map():
  """Constructs a complete valid SCB metadata var_map for testing."""
  county_codes = sorted(download_education.COUNTY_TO_NUTS.keys())
  muni_codes = [f'{1000 + i:04d}' for i in range(290)]
  reg_values = ['00'] + county_codes + muni_codes
  reg_texts = (
      ['Riket']
      + [f'County {c}' for c in county_codes]
      + [f'Muni {m}' for m in muni_codes]
  )
  all_ages = [str(a) for a in range(16, 75)] + ['tot16-74']
  edu_codes = [code for code, _ in download_education.EDUCATION_LEVELS]
  sex_codes = [code for code, _ in download_education.SEX_LEVELS]
  return (
      {
          'Region': {'values': reg_values, 'valueTexts': reg_texts},
          'Alder': {'values': all_ages},
          'UtbildningsNiva': {'values': edu_codes},
          'Kon': {'values': sex_codes},
          'ContentsCode': {'values': ['UF0506A1']},
          'Tid': {'values': ['1985', '2024', '2025']},
      },
      county_codes,
      muni_codes,
  )


class DownloadEducationUnitTest(unittest.TestCase):
  """Hermetic unit tests for download_education.py functions."""

  def test_fetch_metadata_parses_utf8_bom_json(self):
    fake_session = mock.MagicMock(spec=requests.Session)
    fake_resp = mock.MagicMock()
    fake_resp.content = '\ufeff{"title": "Utbildning", "variables": []}'.encode(
        'utf-8'
    )
    fake_session.get.return_value = fake_resp

    result = download_education.fetch_metadata(fake_session)

    self.assertEqual(result, {'title': 'Utbildning', 'variables': []})
    fake_session.get.assert_called_once_with(
        download_education.SCB_API_URL, timeout=60
    )
    fake_resp.raise_for_status.assert_called_once()

  def test_validate_scb_metadata_passes_on_valid_metadata(self):
    var_map, county_codes, muni_codes = _make_valid_var_map()
    download_education.validate_scb_metadata(var_map, county_codes, muni_codes)

  def test_validate_scb_metadata_fails_on_wrong_region_or_code_counts(self):
    var_map, county_codes, muni_codes = _make_valid_var_map()
    with self.assertRaisesRegex(RuntimeError, 'Expected 21 counties'):
      download_education.validate_scb_metadata(
          var_map, county_codes[:-1], muni_codes
      )
    with self.assertRaisesRegex(RuntimeError, 'Expected 290 municipalities'):
      download_education.validate_scb_metadata(
          var_map, county_codes, muni_codes[:-1]
      )
    var_map['UtbildningsNiva']['values'] = ['1', '3']
    with self.assertRaisesRegex(
        RuntimeError, 'Missing expected UtbildningsNiva'
    ):
      download_education.validate_scb_metadata(
          var_map, county_codes, muni_codes
      )

  def test_parse_scb_value_handles_suppressed_markers(self):
    self.assertEqual(download_education._parse_scb_value('450'), 450)
    self.assertEqual(download_education._parse_scb_value('0'), 0)
    for marker in ('..', '.', '-', ''):
      self.assertIsNone(download_education._parse_scb_value(marker))

  def test_query_scb_chunk_success(self):
    fake_session = mock.MagicMock(spec=requests.Session)
    fake_resp = mock.MagicMock()
    fake_resp.status_code = 200
    columns = [
        {'code': 'Region'},
        {'code': 'Alder'},
        {'code': 'UtbildningsNiva'},
        {'code': 'Kon'},
        {'code': 'Tid'},
    ]
    data = [
        {'key': ['01', 'tot16-74', '1', '1', '2024'], 'values': ['123']}
    ]
    fake_resp.content = json.dumps({'columns': columns, 'data': data}).encode(
        'utf-8-sig'
    )
    fake_session.post.return_value = fake_resp

    rows = download_education.query_scb_chunk(
        session=fake_session,
        regions=['01'],
        ages=['tot16-74'],
        edu_codes=['1'],
        sex_codes=['1'],
        years=['2024'],
        contents_code='UF0506B1',
    )
    expected_results = [{
        'Region': '01',
        'Alder': 'tot16-74',
        'UtbildningsNiva': '1',
        'Kon': '1',
        'Tid': '2024',
        'value': '123',
    }]
    self.assertEqual(rows, expected_results)
    self.assertEqual(fake_session.post.call_count, 1)

  def test_query_scb_chunk_fails_immediately_on_400(self):
    fake_session = mock.MagicMock(spec=requests.Session)
    fake_resp = mock.MagicMock()
    fake_resp.status_code = 400
    http_err = requests.HTTPError('400 Client Error', response=fake_resp)
    fake_resp.raise_for_status.side_effect = http_err
    fake_session.post.return_value = fake_resp

    with self.assertRaises(requests.HTTPError):
      download_education.query_scb_chunk(
          session=fake_session,
          regions=['01'],
          ages=['tot16-74'],
          edu_codes=['1'],
          sex_codes=['1'],
          years=['2024'],
          contents_code='UF0506B1',
      )
    self.assertEqual(fake_session.post.call_count, 1)

  def test_write_wide_csv_atomic_and_suppressed_cell_handling(self):
    data_store = collections.defaultdict(int)
    observed_Key = (
        'SE1 Östra Sverige',
        'totalt 16-74 år',
        '1',
        'TOT',
        '2024',
    )
    data_store[observed_Key] = 450
    observed_cells = {observed_Key}

    with tempfile.TemporaryDirectory() as tmp_dir:
      out_csv = os.path.join(tmp_dir, 'test_wide.csv')
      rows_written = download_education.write_wide_csv(
          filepath=out_csv,
          title='Befolkning efter region, ålder, utbildningsnivå och år',
          include_gender=False,
          regions=['SE1 Östra Sverige'],
          age_labels=['totalt 16-74 år'],
          years=['2022', '2023', '2024'],
          data_store=data_store,
          observed_cells=observed_cells,
      )
      self.assertEqual(rows_written, 6)
      self.assertTrue(os.path.exists(out_csv))
      self.assertFalse(os.path.exists(f'{out_csv}.tmp'))

      with open(out_csv, 'r', encoding='utf-8') as f:
        rows = list(csv.reader(f))
      self.assertEqual(
          rows[2],
          ['region', 'ålder', 'utbildningsnivå', '2022', '2023', '2024'],
      )
      # 2022 unobserved cell -> '0' (legacy baseline parity);
      # 2023 unobserved cell -> '' (post-2022 suppressed/missing preserved);
      # 2024 observed cell -> '450'
      self.assertEqual(
          rows[3],
          [
              'SE1 Östra Sverige',
              'totalt 16-74 år',
              'förgymnasial utbildning kortare än 9 år',
              '0',
              '',
              '450',
          ],
      )


class SwedenEducationConfigAndFixtureTest(unittest.TestCase):
  """Verifies PVMap, metadata, remap, validation configs, and test_data fixtures."""

  def test_pvmap_and_remap_coverage(self):
    common_pvmap = os.path.join(SCRIPT_DIR, 'education_common_pvmap.csv')
    total_pvmap = os.path.join(SCRIPT_DIR, 'education_total_pvmap.csv')
    gender_pvmap = os.path.join(SCRIPT_DIR, 'education_gender_pvmap.csv')
    for path in (common_pvmap, total_pvmap, gender_pvmap):
      self.assertTrue(os.path.exists(path), f'Missing {path}')

    with open(common_pvmap, 'r', encoding='utf-8') as f:
      common_keys = {row[0] for row in csv.reader(f) if row}
    for yr in range(1985, 2036):
      self.assertIn(str(yr), common_keys)
    self.assertIn('2463 Åsele', common_keys)

    remap_counts = {
        'education_total_statvar_remap.csv': 6,
        'education_gender_statvar_remap.csv': 12,
        'education_age_statvar_remap.csv': 36,
        'education_age_gender_statvar_remap.csv': 72,
    }
    for filename, expected_svs in remap_counts.items():
      path = os.path.join(SCRIPT_DIR, filename)
      with open(path, 'r', encoding='utf-8') as f:
        rows = list(csv.DictReader(f))
      self.assertEqual(len(rows), expected_svs)

  def test_test_data_fixtures_exist_and_non_empty(self):
    prefixes = (
        'education_nuts1',
        'education_gender_nuts1',
        'education_age_nuts1',
        'education_age_gender_nuts1',
    )
    for prefix in prefixes:
      for suffix in ('_input.csv', '_output.csv', '_output.tmcf'):
        fixture_path = os.path.join(TEST_DATA_DIR, f'{prefix}{suffix}')
        self.assertTrue(os.path.exists(fixture_path), f'Missing {fixture_path}')
        self.assertGreater(os.path.getsize(fixture_path), 0)


if __name__ == '__main__':
  unittest.main()

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
import subprocess
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
SV_PROCESSOR = os.environ.get(
    'SV_PROCESSOR',
    os.path.join(
        SCRIPT_DIR,
        '..',
        '..',
        '..',
        'tools',
        'statvar_importer',
        'stat_var_processor.py',
    ),
)
PLACES_CSV = os.path.join(SCRIPT_DIR, 'sweden_places_resolved.csv')


class DownloadEducationUnitTest(unittest.TestCase):
  """Hermetic unit tests for download_education.py functions."""

  def test_fetch_metadata_parses_utf8_bom_json(self):
    fake_session = mock.MagicMock(spec=requests.Session)
    fake_resp = mock.MagicMock()
    fake_resp.content = '\ufeff{"title": "Utbildning", "variables": []}'.encode(
        'utf-8'
    )
    fake_session.get.return_value = fake_resp

    with mock.patch.object(download_education, '_dc_download_util', None):
      result = download_education.fetch_metadata(fake_session)

    self.assertEqual(result, {'title': 'Utbildning', 'variables': []})
    fake_session.get.assert_called_once_with(
        download_education.SCB_API_URL, timeout=60
    )

  def test_query_scb_chunk_success(self):
    fake_session = mock.MagicMock(spec=requests.Session)
    fake_resp = mock.MagicMock()
    fake_resp.status_code = 200
    expected_rows = [
        {'key': ['01', 'tot16-74', '1', '1', '2024'], 'values': ['123']}
    ]
    fake_resp.content = json.dumps({'data': expected_rows}).encode('utf-8-sig')
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
    self.assertEqual(rows, expected_rows)
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

  def test_write_wide_csv_atomic_and_zero_fill(self):
    data_store = collections.defaultdict(int)
    data_store[('SE1 Östra Sverige', 'totalt 16-74 år', '1', 'TOT', '2024')] = (
        450
    )

    with tempfile.TemporaryDirectory() as tmp_dir:
      out_csv = os.path.join(tmp_dir, 'test_wide.csv')
      rows_written = download_education.write_wide_csv(
          filepath=out_csv,
          title='Befolkning efter region, ålder, utbildningsnivå och år',
          include_gender=False,
          regions=['SE1 Östra Sverige'],
          age_labels=['totalt 16-74 år'],
          years=['2023', '2024'],
          data_store=data_store,
      )
      self.assertEqual(rows_written, 6)
      self.assertTrue(os.path.exists(out_csv))
      self.assertFalse(os.path.exists(f'{out_csv}.tmp'))

      with open(out_csv, 'r', encoding='utf-8') as f:
        rows = list(csv.reader(f))
      self.assertEqual(
          rows[2], ['region', 'ålder', 'utbildningsnivå', '2023', '2024']
      )
      self.assertEqual(
          rows[3],
          [
              'SE1 Östra Sverige',
              'totalt 16-74 år',
              'förgymnasial utbildning kortare än 9 år',
              '0',
              '450',
          ],
      )


class SwedenEducationProcessorTest(unittest.TestCase):
  """Tests stat_var_processor across all 4 marginal groups on test_data/."""

  def _run_and_verify(
      self,
      sample_prefix: str,
      pvmap: str,
      metadata: str,
      remap: str,
  ):
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
          os.path.join(SCRIPT_DIR, metadata), 'r', encoding='utf-8'
      ) as f_in, open(test_config_path, 'w', encoding='utf-8') as f_out:
        f_out.write(f_in.read())
        f_out.write('generate_statvar_mcf,False\n')
        f_out.write('generate_schema_mcf,False\n')

      cmd = [
          'python3',
          SV_PROCESSOR,
          f'--input_data={input_csv}',
          f'--pv_map={os.path.join(SCRIPT_DIR, pvmap)}',
          f'--config_file={test_config_path}',
          f'--places_resolved_csv={PLACES_CSV}',
          f'--statvar_dcid_remap_csv={os.path.join(SCRIPT_DIR, remap)}',
          f'--output_path={actual_prefix}',
      ]
      subprocess.run(cmd, check=True, cwd=SCRIPT_DIR)

      actual_csv = f'{actual_prefix}.csv'
      actual_tmcf = f'{actual_prefix}.tmcf'
      with open(expected_csv, 'r', encoding='utf-8') as f_exp, open(
          actual_csv, 'r', encoding='utf-8'
      ) as f_act:
        self.assertEqual(f_exp.read().splitlines(), f_act.read().splitlines())

      with open(expected_tmcf, 'r', encoding='utf-8') as f_exp_tmcf, open(
          actual_tmcf, 'r', encoding='utf-8'
      ) as f_act_tmcf:
        self.assertEqual(
            f_exp_tmcf.read().splitlines(), f_act_tmcf.read().splitlines()
        )

  def test_group1_total(self):
    self._run_and_verify(
        'education_nuts1',
        'education_total_pvmap.csv',
        'education_total_metadata.csv',
        'education_total_statvar_remap.csv',
    )

  def test_group2_gender(self):
    self._run_and_verify(
        'education_gender_nuts1',
        'education_gender_pvmap.csv',
        'education_gender_metadata.csv',
        'education_gender_statvar_remap.csv',
    )

  def test_group3_age(self):
    self._run_and_verify(
        'education_age_nuts1',
        'education_age_pvmap.csv',
        'education_age_metadata.csv',
        'education_age_statvar_remap.csv',
    )

  def test_group4_age_gender(self):
    self._run_and_verify(
        'education_age_gender_nuts1',
        'education_age_gender_pvmap.csv',
        'education_age_gender_metadata.csv',
        'education_age_gender_statvar_remap.csv',
    )


if __name__ == '__main__':
  unittest.main()

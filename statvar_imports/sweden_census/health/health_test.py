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
"""Unit tests for Sweden Census Category 2 (Health & Vital Statistics) import."""

import collections
import csv
import json
import os
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
from absl import flags
import requests

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

import download_health  # pylint: disable=g-import-not-at-top

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
        )),
)
PLACES_CSV = os.path.join(SCRIPT_DIR, 'sweden_places_resolved.csv')


class DownloadHealthUnitTest(unittest.TestCase):
    """Hermetic unit tests for download_health.py functions."""

    def test_fetch_metadata_parses_utf8_bom_json(self):
        fake_session = mock.MagicMock(spec=requests.Session)
        fake_resp = mock.MagicMock()
        fake_resp.content = (
            '\ufeff{"title": "DodaFodelsearK", "variables": []}'.encode('utf-8')
        )
        fake_session.get.return_value = fake_resp

        result = download_health.fetch_metadata(fake_session,
                                                download_health.SCB_DEATHS_URL)

        self.assertEqual(result, {'title': 'DodaFodelsearK', 'variables': []})
        fake_session.get.assert_called_once_with(download_health.SCB_DEATHS_URL,
                                                 timeout=60)
        fake_resp.raise_for_status.assert_called_once()

    def test_post_scb_query_success(self):
        fake_session = mock.MagicMock(spec=requests.Session)
        fake_resp = mock.MagicMock()
        fake_resp.status_code = 200
        data = [{'key': ['01', 'tot', '1', '2024'], 'values': ['4500']}]
        fake_resp.content = json.dumps({'data': data}).encode('utf-8-sig')
        fake_session.post.return_value = fake_resp

        rows = download_health.post_scb_query(
            session=fake_session,
            url=download_health.SCB_DEATHS_URL,
            query_items=[{
                'code': 'Region',
                'selection': {
                    'filter': 'item',
                    'values': ['01']
                }
            }],
        )
        self.assertEqual(rows, data)
        self.assertEqual(fake_session.post.call_count, 1)

    def test_post_scb_query_raises_on_empty_data(self):
        fake_session = mock.MagicMock(spec=requests.Session)
        fake_resp = mock.MagicMock()
        fake_resp.status_code = 200
        fake_resp.content = json.dumps({'data': []}).encode('utf-8-sig')
        fake_session.post.return_value = fake_resp

        with mock.patch.object(download_health.time, 'sleep'):
            with self.assertRaises(RuntimeError):
                download_health.post_scb_query(
                    session=fake_session,
                    url=download_health.SCB_DEATHS_URL,
                    query_items=[],
                )

    def test_post_scb_query_fails_immediately_on_400(self):
        fake_session = mock.MagicMock(spec=requests.Session)
        fake_resp = mock.MagicMock()
        fake_resp.status_code = 400
        http_err = requests.HTTPError('400 Client Error', response=fake_resp)
        fake_resp.raise_for_status.side_effect = http_err
        fake_session.post.return_value = fake_resp

        with self.assertRaises(requests.HTTPError):
            download_health.post_scb_query(
                session=fake_session,
                url=download_health.SCB_DEATHS_URL,
                query_items=[],
            )
        self.assertEqual(fake_session.post.call_count, 1)

    def test_write_deaths_wide_csv_atomic_and_zero_fill(self):
        data_store = collections.defaultdict(int)
        data_store[('SE1 Östra Sverige', 'totalt ålder', 'TOT', '2024')] = 32100

        with tempfile.TemporaryDirectory() as tmp_dir:
            out_csv = os.path.join(tmp_dir, 'Death_NUTS1.csv')
            rows_written = download_health.write_deaths_wide_csv(
                filepath=out_csv,
                title='Döda efter region, ålder och år',
                include_gender=False,
                regions=['SE1 Östra Sverige'],
                age_labels=['totalt ålder'],
                years=['2023', '2024'],
                data_store=data_store,
            )
            self.assertEqual(rows_written, 1)
            self.assertTrue(os.path.exists(out_csv))
            self.assertFalse(os.path.exists(f'{out_csv}.tmp'))

            with open(out_csv, 'r', encoding='utf-8') as f:
                rows = list(csv.reader(f))
            self.assertEqual(rows[2], ['region', 'ålder', '2023', '2024'])
            self.assertEqual(
                rows[3],
                ['SE1 Östra Sverige', 'totalt ålder', '0', '32100'],
            )

    def test_format_fertility_val(self):
        self.assertEqual(download_health._format_fertility_val('1.60'), '1.6')
        self.assertEqual(download_health._format_fertility_val('1.75'), '1.75')
        self.assertEqual(download_health._format_fertility_val('..'), '..')
        self.assertEqual(download_health._format_fertility_val('-'), '..')

    def test_download_deaths_aggregates_ages_and_nuts(self):
        fake_session = mock.MagicMock(spec=requests.Session)
        hist_meta = {
            'variables': [
                {
                    'code': 'Tid',
                    'values': ['2024']
                },
                {
                    'code': 'ContentsCode',
                    'values': ['BE0101D9']
                },
                {
                    'code': 'Region',
                    'values': ['00', '01', '0114'],
                    'valueTexts': ['Riket', 'Stockholms län', 'Upplands Väsby'],
                },
            ]
        }
        ckm_meta = {
            'variables': [
                {
                    'code': 'Tid',
                    'values': ['2025']
                },
                {
                    'code': 'ContentsCode',
                    'values': ['0000081B']
                },
            ]
        }
        county_hist_rows = [
            {
                'key': ['01', '0', '1', '2024'],
                'values': ['10']
            },
            {
                'key': ['01', '100+', '2', '2024'],
                'values': ['5']
            },
            {
                'key': ['01', 'tot', '1', '2024'],
                'values': ['100']
            },
            {
                'key': ['01', 'tot', '2', '2024'],
                'values': ['..']
            },
        ]
        county_ckm_rows = [
            {
                'key': ['01', '100+1', '2', '2025'],
                'values': ['7']
            },
            {
                'key': ['01', 'TotSA', '1', '2025'],
                'values': ['110']
            },
        ]
        muni_hist_rows = [
            {
                'key': ['0114', 'tot', '1', '2024'],
                'values': ['25']
            },
        ]
        muni_ckm_rows = [
            {
                'key': ['0114', 'TotSA', '1', '2025'],
                'values': ['30']
            },
        ]

        with tempfile.TemporaryDirectory() as tmp_dir, mock.patch.object(
                download_health,
                'fetch_metadata',
                side_effect=[hist_meta, ckm_meta],
        ), mock.patch.object(
                download_health,
                'post_scb_query',
                side_effect=[
                    county_hist_rows,
                    county_ckm_rows,
                    muni_hist_rows,
                    muni_ckm_rows,
                ],
        ), mock.patch.object(download_health.time, 'sleep'):
            download_health.download_deaths(fake_session, tmp_dir)

            with open(os.path.join(tmp_dir, 'Death_NUTS1.csv'),
                      'r',
                      encoding='utf-8') as f:
                nuts1_rows = list(csv.reader(f))
            self.assertEqual(nuts1_rows[2], ['region', 'ålder', '2024', '2025'])
            self.assertEqual(
                nuts1_rows[3],
                ['SE1 Östra Sverige', 'totalt ålder', '100', '110'])

            with open(
                    os.path.join(tmp_dir, 'Death_age_gender_NUTS1.csv'),
                    'r',
                    encoding='utf-8',
            ) as f:
                age_rows = list(csv.reader(f))
            self.assertIn(['SE1 Östra Sverige', '0-4 år', 'män', '10', '0'],
                          age_rows)
            self.assertIn(['SE1 Östra Sverige', '95+ år', 'kvinnor', '5', '7'],
                          age_rows)

    def test_download_fertility_writes_csv(self):
        fake_session = mock.MagicMock(spec=requests.Session)
        fert_meta = {
            'variables': [
                {
                    'code': 'Tid',
                    'values': ['2024', '2025']
                },
                {
                    'code': 'ContentsCode',
                    'values': ['000001J4']
                },
                {
                    'code': 'Region',
                    'values': ['0114'],
                    'valueTexts': ['Upplands Väsby'],
                },
            ]
        }
        fert_rows = [
            {
                'key': ['0114', '1', '2024'],
                'values': ['1.40']
            },
            {
                'key': ['0114', '2', '2024'],
                'values': ['1.55']
            },
            {
                'key': ['0114', '1', '2025'],
                'values': ['..']
            },
            {
                'key': ['0114', '2', '2025'],
                'values': ['1.52']
            },
        ]
        with tempfile.TemporaryDirectory() as tmp_dir, mock.patch.object(
                download_health, 'fetch_metadata',
                return_value=fert_meta), mock.patch.object(
                    download_health, 'post_scb_query',
                    return_value=fert_rows), mock.patch.object(
                        download_health.time, 'sleep'):
            download_health.download_fertility(fake_session, tmp_dir)
            out_path = os.path.join(tmp_dir,
                                    'FertilityRate_gender_Muncipality.csv')
            with open(out_path, 'r', encoding='utf-8') as f:
                rows = list(csv.reader(f))
            self.assertEqual(rows[2], ['region', 'kön', '2024', '2025'])
            self.assertEqual(rows[3],
                             ['0114 Upplands Väsby', 'män', '1.4', '..'])
            self.assertEqual(rows[4],
                             ['0114 Upplands Väsby', 'kvinnor', '1.55', '1.52'])

    def test_download_livebirths_writes_csv_and_validates_keys(self):
        fake_session = mock.MagicMock(spec=requests.Session)
        lb_meta = {'variables': [{'code': 'Tid', 'values': ['2025']}]}
        lb_rows = [
            {
                'key': ['1+2', '2025'],
                'values': ['98657']
            },
            {
                'key': ['1', '2025'],
                'values': ['50723']
            },
            {
                'key': ['2', '2025'],
                'values': ['47934']
            },
        ]
        with tempfile.TemporaryDirectory() as tmp_dir, mock.patch.object(
                download_health, 'fetch_metadata',
                return_value=lb_meta), mock.patch.object(download_health,
                                                         'post_scb_query',
                                                         return_value=lb_rows):
            download_health.download_livebirths(fake_session, tmp_dir)
            out_path = os.path.join(tmp_dir,
                                    'LiveBirth_gender_total_country.csv')
            with open(out_path, 'r', encoding='utf-8') as f:
                rows = list(csv.reader(f))
            self.assertEqual(rows[2], ['kön', '2025'])
            self.assertEqual(rows[3], ['båda könen', '98657'])
            self.assertEqual(rows[4], ['pojkar', '50723'])
            self.assertEqual(rows[5], ['flickor', '47934'])


class SwedenHealthProcessorTest(unittest.TestCase):
    """Tests stat_var_processor across all 5 Health & Vital Statistics groups on test_data/."""

    def _run_and_verify(
        self,
        sample_prefix: str,
        pvmap: str,
        metadata: str,
        remap: str = '',
    ):
        input_csv = os.path.join(TEST_DATA_DIR, f'{sample_prefix}_input.csv')
        expected_csv = os.path.join(TEST_DATA_DIR,
                                    f'{sample_prefix}_output.csv')
        expected_tmcf = os.path.join(TEST_DATA_DIR,
                                     f'{sample_prefix}_output.tmcf')
        self.assertTrue(os.path.exists(input_csv), f'Missing {input_csv}')
        self.assertTrue(os.path.exists(expected_csv), f'Missing {expected_csv}')
        self.assertTrue(os.path.exists(expected_tmcf),
                        f'Missing {expected_tmcf}')

        with tempfile.TemporaryDirectory() as tmp_dir:
            actual_prefix = os.path.join(tmp_dir, sample_prefix)
            test_config_path = os.path.join(tmp_dir, 'test_metadata.csv')
            with open(os.path.join(SCRIPT_DIR, metadata), 'r',
                      encoding='utf-8') as f_in, open(
                          test_config_path, 'w', encoding='utf-8') as f_out:
                f_out.write(f_in.read())
                f_out.write('generate_statvar_mcf,False\n')
                f_out.write('generate_schema_mcf,False\n')
                f_out.write('reconcile_nodes,False\n')
                f_out.write('recon_lookup_api,False\n')

            cmd = [
                'python3',
                SV_PROCESSOR,
                f'--input_data={input_csv}',
                f'--pv_map={os.path.join(SCRIPT_DIR, pvmap)}',
                f'--config_file={test_config_path}',
                f'--places_resolved_csv={PLACES_CSV}',
                f'--output_path={actual_prefix}',
            ]
            if remap:
                cmd.append(
                    f'--statvar_dcid_remap_csv={os.path.join(SCRIPT_DIR, remap)}'
                )
            subprocess.run(cmd, check=True, cwd=tmp_dir)

            actual_csv = f'{actual_prefix}.csv'
            actual_tmcf = f'{actual_prefix}.tmcf'
            with open(expected_csv, 'r', encoding='utf-8') as f_exp, open(
                    actual_csv, 'r', encoding='utf-8') as f_act:
                self.assertEqual(f_exp.read().splitlines(),
                                 f_act.read().splitlines())

            with open(expected_tmcf, 'r', encoding='utf-8') as f_exp_tmcf, open(
                    actual_tmcf, 'r', encoding='utf-8') as f_act_tmcf:
                self.assertEqual(f_exp_tmcf.read().splitlines(),
                                 f_act_tmcf.read().splitlines())

    def test_deaths_total(self):
        self._run_and_verify(
            'Death_NUTS1',
            'deaths_total_pvmap.csv',
            'deaths_total_metadata.csv',
            'deaths_total_statvar_remap.csv',
        )

    def test_deaths_gender(self):
        self._run_and_verify(
            'Death_gender_NUTS1',
            'deaths_gender_pvmap.csv',
            'deaths_gender_metadata.csv',
            'deaths_gender_statvar_remap.csv',
        )

    def test_deaths_age_gender(self):
        self._run_and_verify(
            'Death_age_gender_NUTS1',
            'deaths_age_gender_pvmap.csv',
            'deaths_age_gender_metadata.csv',
            'deaths_age_gender_statvar_remap.csv',
        )

    def test_fertility_rate(self):
        self._run_and_verify(
            'FertilityRate_gender_Muncipality',
            'fertility_pvmap.csv',
            'fertility_metadata.csv',
        )

    def test_live_births(self):
        self._run_and_verify(
            'LiveBirth_gender_total_country',
            'livebirth_pvmap.csv',
            'livebirth_metadata.csv',
            'livebirth_statvar_remap.csv',
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

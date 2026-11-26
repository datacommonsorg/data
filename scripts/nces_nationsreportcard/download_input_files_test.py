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
"""Offline unit tests for download_input_files.py."""

import csv
import os
import sys
import tempfile
import unittest
from unittest import mock

import requests

MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(MODULE_DIR, '..', '..'))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from scripts.nces_nationsreportcard import download_input_files as dl


def _mock_response(status_code=200, json_payload=None, text=''):
    resp = mock.MagicMock()
    resp.status_code = status_code
    if json_payload is not None:
        resp.json.return_value = json_payload
    else:
        resp.json.side_effect = ValueError('No JSON')
    resp.text = text
    return resp


class DownloadInputFilesTest(unittest.TestCase):
    """Tests query generation, year discovery, fallbacks, and fail-fast I/O."""

    def setUp(self):
        dl._DESCENDING_YEARS_CACHE.clear()
        dl._SCALES_REQUIRING_EXPLICIT_YEARS.clear()
        dl._SCALES_REQUIRING_EXPLICIT_YEARS.update({
            ('MAT', 4, 'MRPS4'),
            ('RED', 12, 'RRPS4'),
        })

    def test_total_query_count_across_all_16_files(self):
        self.assertEqual(len(dl.FILE_SPECS), 16)
        total_queries = sum(
            len(dl.build_query_tasks(spec)) for spec in dl.FILE_SPECS.values())
        self.assertEqual(total_queries, 4644)

    def test_fast_fail_on_http_400_without_retries(self):
        mock_session = mock.MagicMock()
        mock_session.get.return_value = _mock_response(status_code=400,
                                                       text='Bad Request')
        with mock.patch.object(dl, '_get_session', return_value=mock_session):
            rows, status = dl._query_naep_once({'type': 'data'},
                                               read_timeout=10,
                                               max_attempts=3)
        self.assertEqual(rows, [])
        self.assertEqual(status, 'client_error')
        self.assertEqual(mock_session.get.call_count, 1)

    def test_all_descending_years_discovered_without_truncation(self):
        # Verify all 13 assessment years (1996..2024) are passed in descending
        # order without the legacy [:4] truncation timebomb.
        all_years = [
            1996, 2000, 2003, 2005, 2007, 2009, 2011, 2013, 2015, 2017, 2019,
            2022, 2024
        ]
        probe_result = [{
            'year': y,
            'sample': 'R3',
            'yearSampleLabel': str(y),
            'value': 240.0
        } for y in all_years]
        scale_result = [{
            'year': 1996,
            'sample': 'R3',
            'yearSampleLabel': '1996',
            'value': 224.5
        }]

        calls = []

        def fake_get(_, params=None, timeout=None):
            del timeout
            calls.append(dict(params))
            if params['subscale'] == 'MRPCM':
                return _mock_response(200, {
                    'status': 200,
                    'result': probe_result
                })
            return _mock_response(200, {'status': 200, 'result': scale_result})

        mock_session = mock.MagicMock()
        mock_session.get.side_effect = fake_get
        with mock.patch.object(dl, '_get_session', return_value=mock_session):
            rows = dl.fetch_naep_rows('MAT',
                                      4,
                                      'MRPS4',
                                      'TOTAL',
                                      dl.NATIONAL_JURISDICTION,
                                      'MN:MN',
                                      read_timeout=10)

        self.assertEqual(len(rows), 1)
        self.assertEqual(len(calls), 2)
        expected_years = '2024,2022,2019,2017,2015,2013,2011,2009,2007,2005,2003,2000,1996'
        self.assertEqual(calls[1].get('Year'), expected_years)

    def test_red_g12_pilot_fallback_on_55_state_http_400(self):
        calls = []

        def fake_get(_, params=None, timeout=None):
            del timeout
            calls.append(params['jurisdiction'])
            if params['jurisdiction'] == dl.ALL_STATE_JURISDICTIONS:
                return _mock_response(400, text='Unsupported state')
            if params['jurisdiction'] == dl.RED_G12_PILOT_STATES:
                return _mock_response(
                    200, {
                        'status':
                            200,
                        'result': [{
                            'year': 2013,
                            'sample': 'R3',
                            'yearSampleLabel': '2013',
                            'jurisdiction': 'MI',
                            'value': '288.4',
                        }],
                    })
            return _mock_response(400, text='Unexpected')

        mock_session = mock.MagicMock()
        mock_session.get.side_effect = fake_get
        with mock.patch.object(dl, '_get_session', return_value=mock_session):
            rows = dl.fetch_naep_rows('RED',
                                      12,
                                      'RRPCM',
                                      'TOTAL',
                                      dl.ALL_STATE_JURISDICTIONS,
                                      'MN:MN',
                                      read_timeout=10)
        self.assertEqual(calls,
                         [dl.ALL_STATE_JURISDICTIONS, dl.RED_G12_PILOT_STATES])
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['value'], 288.4)

    def test_filter_r3_rows_skips_non_numeric_sentinel_without_raising(self):
        filtered = dl._filter_r3_rows([
            {
                'sample': 'R2',
                'yearSampleLabel': '1996',
                'value': '220.0'
            },
            {
                'sample': 'R3',
                'yearSampleLabel': 'XXXX',
                'value': '220.0'
            },
            {
                'sample': 'R3',
                'yearSampleLabel': '2024',
                'value': '‡'
            },
            {
                'sample': 'R3',
                'yearSampleLabel': '2024',
                'value': '999.0'
            },
            {
                'sample': 'R3',
                'yearSampleLabel': '2024',
                'value': '241.5'
            },
        ])
        self.assertEqual(len(filtered), 2)
        self.assertEqual([r['value'] for r in filtered], [999.0, 241.5])

    def test_transient_failure_raises_and_cleans_up_atomic_tempfile(self):
        mock_session = mock.MagicMock()
        mock_session.get.side_effect = requests.ConnectionError('timeout')

        spec = [{
            'subject': 'MUS',
            'grade': 8,
            'scales': ['MUSRP'],
            'variables': ['TOTAL'],
            'jurisdiction_batches': [dl.NATIONAL_JURISDICTION],
        }]
        with tempfile.TemporaryDirectory() as tmpdir:
            with mock.patch.object(
                    dl, '_get_session',
                    return_value=mock_session), mock.patch('time.sleep'):
                with self.assertRaises(RuntimeError):
                    dl.download_file('naep_national_mus.csv',
                                     spec,
                                     tmpdir,
                                     max_workers=2,
                                     read_timeout=5)
            # Neither target CSV nor leftover .tmp file may exist after failure.
            self.assertEqual(os.listdir(tmpdir), [])

    def test_fdopen_failure_closes_fd_and_removes_tempfile(self):
        spec = [{
            'subject': 'MUS',
            'grade': 8,
            'scales': ['MUSRP'],
            'variables': ['TOTAL'],
            'jurisdiction_batches': [dl.NATIONAL_JURISDICTION],
        }]
        with tempfile.TemporaryDirectory() as tmpdir:
            with mock.patch('os.fdopen',
                            side_effect=OSError('fdopen failed')), mock.patch(
                                'os.close', wraps=os.close) as mock_close:
                with self.assertRaises(OSError):
                    dl.download_file('naep_national_mus.csv',
                                     spec,
                                     tmpdir,
                                     max_workers=1,
                                     read_timeout=5)
            self.assertEqual(mock_close.call_count, 1)
            self.assertEqual(os.listdir(tmpdir), [])

    def test_deterministic_row_order_under_concurrent_workers(self):

        def fake_fetch(subject,
                       grade,
                       scale,
                       variable,
                       jurisdiction,
                       stattype,
                       read_timeout=None):
            del grade, scale, jurisdiction, read_timeout
            return [{
                col: f'{subject}_{variable}_{stattype}'
                for col in dl.CSV_COLUMNS
            }]

        spec = [{
            'subject': 'CIV',
            'grade': 8,
            'scales': ['CIVRP'],
            'variables': ['TOTAL', 'GENDER', 'SLUNCH3'],
            'jurisdiction_batches': [dl.NATIONAL_JURISDICTION],
        }]
        with tempfile.TemporaryDirectory() as tmpdir:
            with mock.patch.object(dl,
                                   'fetch_naep_rows',
                                   side_effect=fake_fetch):
                written = dl.download_file('naep_national_civ.csv',
                                           spec,
                                           tmpdir,
                                           max_workers=4,
                                           read_timeout=10)
            self.assertEqual(written, 12)
            out_csv = os.path.join(tmpdir, 'naep_national_civ.csv')
            with open(out_csv, encoding='utf-8') as f:
                rows = list(csv.DictReader(f))
            expected_order = [
                f'CIV_{var}_{st}' for var in ['TOTAL', 'GENDER', 'SLUNCH3']
                for st in dl.STATTYPE_BATCHES_COMPOSITE
            ]
            self.assertEqual([r['year'] for r in rows], expected_order)

    def test_query_naep_once_logs_outbound_get_at_debug(self):
        mock_session = mock.MagicMock()
        mock_session.get.return_value = _mock_response(200, {
            'status': 200,
            'result': []
        })
        params = {'type': 'data', 'subject': 'MAT', 'grade': '4'}
        with mock.patch.object(dl, '_get_session',
                               return_value=mock_session), mock.patch.object(
                                   dl.logging, 'debug') as mock_debug:
            rows, status = dl._query_naep_once(params,
                                               read_timeout=10,
                                               max_attempts=1)
        self.assertEqual(rows, [])
        self.assertEqual(status, 'ok')
        self.assertTrue(
            any('GET %s params=%s' in str(c.args[0]) and
                c.args[1] == dl.NAEP_API_URL and c.args[2] == params
                for c in mock_debug.call_args_list))

    def test_year_propagated_to_state_batch_fallback_after_dependent_info(self):
        calls = []

        def fake_get(_, params=None, timeout=None):
            del timeout
            calls.append(dict(params))
            juris = params['jurisdiction']
            if params['subscale'] == 'MRPCM':
                return _mock_response(
                    200, {
                        'status':
                            200,
                        'result': [{
                            'year': 2024,
                            'sample': 'R3',
                            'yearSampleLabel': '2024',
                            'value': 240.0,
                        }, {
                            'year': 2022,
                            'sample': 'R3',
                            'yearSampleLabel': '2022',
                            'value': 236.0,
                        }],
                    })
            if juris == dl.ALL_STATE_JURISDICTIONS:
                if 'Year' not in params:
                    return _mock_response(400, text='GetDependentInfo error')
                return _mock_response(400, text='Unsupported state in 55-list')
            return _mock_response(
                200, {
                    'status':
                        200,
                    'result': [{
                        'year': 2024,
                        'sample': 'R3',
                        'yearSampleLabel': '2024',
                        'jurisdiction': juris.split(',')[0],
                        'value': '241.0',
                    }],
                })

        mock_session = mock.MagicMock()
        mock_session.get.side_effect = fake_get
        with mock.patch.object(dl, '_get_session', return_value=mock_session):
            rows = dl.fetch_naep_rows('MAT',
                                      4,
                                      'MRPS4',
                                      'TOTAL',
                                      dl.ALL_STATE_JURISDICTIONS,
                                      'MN:MN',
                                      read_timeout=10)

        self.assertEqual(len(rows), len(dl.STATE_JURISDICTION_BATCHES))
        batch_calls = [
            c for c in calls
            if c['jurisdiction'] in dl.STATE_JURISDICTION_BATCHES
        ]
        self.assertEqual(len(batch_calls), len(dl.STATE_JURISDICTION_BATCHES))
        for batch_call in batch_calls:
            self.assertEqual(batch_call.get('Year'), '2024,2022')

    def test_year_propagated_to_red_g12_pilot_fallback_after_dependent_info(
            self):
        calls = []

        def fake_get(_, params=None, timeout=None):
            del timeout
            calls.append(dict(params))
            juris = params['jurisdiction']
            if params['subscale'] == 'RRPCM':
                if juris == dl.ALL_STATE_JURISDICTIONS:
                    return _mock_response(400, text='Unsupported state')
                return _mock_response(
                    200, {
                        'status':
                            200,
                        'result': [{
                            'year': 2013,
                            'sample': 'R3',
                            'yearSampleLabel': '2013',
                            'value': 288.0,
                        }],
                    })
            if juris == dl.ALL_STATE_JURISDICTIONS:
                if 'Year' not in params:
                    return _mock_response(400, text='GetDependentInfo error')
                return _mock_response(400, text='Non-pilot state rejected')
            if juris == dl.RED_G12_PILOT_STATES:
                return _mock_response(
                    200, {
                        'status':
                            200,
                        'result': [{
                            'year': 2013,
                            'sample': 'R3',
                            'yearSampleLabel': '2013',
                            'jurisdiction': 'MI',
                            'value': '289.5',
                        }],
                    })
            return _mock_response(400, text='Unexpected')

        mock_session = mock.MagicMock()
        mock_session.get.side_effect = fake_get
        with mock.patch.object(dl, '_get_session', return_value=mock_session):
            rows = dl.fetch_naep_rows('RED',
                                      12,
                                      'RRPS4',
                                      'TOTAL',
                                      dl.ALL_STATE_JURISDICTIONS,
                                      'MN:MN',
                                      read_timeout=10)

        self.assertEqual(len(rows), 1)
        pilot_data_calls = [
            c for c in calls if c['jurisdiction'] == dl.RED_G12_PILOT_STATES and
            c['subscale'] == 'RRPS4'
        ]
        self.assertEqual(len(pilot_data_calls), 1)
        self.assertEqual(pilot_data_calls[0].get('Year'), '2013')

    def test_state_batch_fallback_raises_on_dependent_info_error(self):
        mock_session = mock.MagicMock()
        mock_session.get.return_value = _mock_response(
            400, text='GetDependentInfo error')
        params_with_year = {
            'type': 'data',
            'subject': 'MAT',
            'grade': '4',
            'subscale': 'MRPS4',
            'variable': 'TOTAL',
            'jurisdiction': dl.ALL_STATE_JURISDICTIONS,
            'stattype': 'MN:MN',
            'Year': '2024,2022',
        }
        with mock.patch.object(dl, '_get_session', return_value=mock_session):
            with self.assertRaises(RuntimeError):
                dl._fetch_state_batches_fallback(params_with_year,
                                                 read_timeout=10,
                                                 max_attempts=1)


if __name__ == '__main__':
    unittest.main()

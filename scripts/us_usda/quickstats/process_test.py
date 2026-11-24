# Copyright 2021 Google LLC
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
"""Tests for process.py"""

import csv
import io
import os
import sys
import tempfile
import unittest
from unittest import mock

from absl.testing import absltest
import requests

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.abspath(os.path.join(_SCRIPT_DIR, '..', '..', '..'))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from scripts.us_usda.quickstats import process
from scripts.us_usda.quickstats.process import QueryLimitExceededError
from scripts.us_usda.quickstats.process import get_data
from scripts.us_usda.quickstats.process import get_param_values
from scripts.us_usda.quickstats.process import get_survey_county_data
from scripts.us_usda.quickstats.process import get_survey_state_data
from scripts.us_usda.quickstats.process import load_svs
from scripts.us_usda.quickstats.process import process_survey_data
from scripts.us_usda.quickstats.process import to_csv_rows
from scripts.us_usda.quickstats.process import write_csv


class ProcessTest(unittest.TestCase):

    def setUp(self):
        """Setup mock data and objects for the test."""
        process._CACHED_API_KEY = None
        process._HTTP_SESSION = None
        process._HTTP_SESSION_PID = None
        process.request_times.clear()
        self.mock_api_data = {
            'data': [{
                "short_desc": "CORN, GRAIN - ACRES HARVESTED",
                "domaincat_desc": "NOT SPECIFIED",
                "county_code": "001",
                "state_fips_code": "45",
                "year": "2024",
                "value": "15000",
            }, {
                "short_desc": "WHEAT - ACRES HARVESTED",
                "domaincat_desc": "",
                "county_code": "001",
                "state_fips_code": "45",
                "year": "2024",
                "value": "5000",
            }]
        }

    @mock.patch.object(process, 'get_data')
    @mock.patch.object(process, '_write_json_atomic')
    @mock.patch.object(process, 'get_usda_api_key', return_value='mock-api-key')
    def test_write_csv(self, mock_get_api_key, mock_write_json, mock_get_data):
        """Tests the write_csv function without making a real API call."""
        mock_get_data.return_value = self.mock_api_data

        expected_csv_rows = [{
            'variableMeasured': 'dcs:Area_Farm_CornForGrain',
            'observationDate': '2024',
            'observationAbout': 'dcid:geoId/45001',
            'value': 15000,
            'unit': 'dcs:Acre'
        }, {
            'variableMeasured': 'dcs:Area_Farm_WheatForGrain',
            'observationDate': '2024',
            'observationAbout': 'dcid:geoId/45001',
            'value': 5000,
            'unit': 'dcs:Acre'
        }]
        api_data = get_survey_county_data(2025, 'ABBEVILLE', 'testdata')

        self.assertEqual(len(api_data['data']), 2)

        svs = load_svs()
        csv_rows = to_csv_rows(api_data, svs)
        self.assertEqual(csv_rows, expected_csv_rows)

        out = io.StringIO()
        write_csv(out, csv_rows)

        expected_csv_output = """variableMeasured,observationDate,observationAbout,value,unit
dcs:Area_Farm_CornForGrain,2024,dcid:geoId/45001,15000,dcs:Acre
dcs:Area_Farm_WheatForGrain,2024,dcid:geoId/45001,5000,dcs:Acre
"""
        self.assertEqual(expected_csv_output, out.getvalue())

    @mock.patch.object(process.requests.Session, 'get')
    @mock.patch.object(process, 'is_rate_limited', return_value=False)
    def test_get_data_400_no_data_found(self, mock_rate_limit,
                                        mock_requests_get):
        """Tests that get_data returns {'data': []} cleanly when API returns 400 'no data found'."""
        mock_resp = mock.Mock()
        mock_resp.status_code = 400
        mock_resp.json.return_value = {
            "error": ["bad request - unsupported query / no data found"]
        }
        mock_requests_get.return_value = mock_resp

        result = get_data({
            'source_desc': 'SURVEY',
            'year': 2024,
            'county_name': 'FAKECOUNTY'
        })
        self.assertEqual(result, {'data': []})

    @mock.patch.object(process.requests.Session, 'get')
    @mock.patch.object(process, 'is_rate_limited', return_value=False)
    def test_get_data_400_invalid_query(self, mock_rate_limit,
                                        mock_requests_get):
        """Tests that get_data returns {'data': []} cleanly when API returns 400 'invalid query' (e.g. WASHABAUGH)."""
        mock_resp = mock.Mock()
        mock_resp.status_code = 400
        mock_resp.json.return_value = {"error": ["bad request - invalid query"]}
        mock_requests_get.return_value = mock_resp

        result = get_data({
            'source_desc': 'SURVEY',
            'year': 2024,
            'county_name': 'WASHABAUGH'
        })
        self.assertEqual(result, {'data': []})

    @mock.patch.object(process.requests.Session, 'get')
    @mock.patch.object(process, 'is_rate_limited', return_value=False)
    def test_get_data_400_exceeds_limit_raises_query_limit_error(
            self, mock_rate_limit, mock_requests_get):
        """Tests that 400 'exceeds limit=50000' raises QueryLimitExceededError instead of returning empty data."""
        mock_resp = mock.Mock()
        mock_resp.status_code = 400
        mock_resp.text = '{"error": ["bad request - exceeds limit=50000"]}'
        mock_resp.json.return_value = {
            "error": ["bad request - exceeds limit=50000"]
        }
        mock_requests_get.return_value = mock_resp

        with self.assertRaises(QueryLimitExceededError):
            get_data({
                'key': 'super-secret-token-12345',
                'source_desc': 'SURVEY',
                'agg_level_desc': 'COUNTY',
                'year': 2024,
                'state_alpha': 'TX',
            })

    @mock.patch('retry.api.time.sleep')
    @mock.patch.object(process.requests.Session, 'get')
    @mock.patch.object(process, 'is_rate_limited', return_value=False)
    def test_get_data_400_invalid_api_key_raises(self, mock_rate_limit,
                                                 mock_requests_get,
                                                 mock_retry_sleep):
        """Tests that 400 'bad request - invalid api key' raises RequestException instead of returning empty data."""
        secret_key = 'INVALID-SECRET-KEY-999'
        process._CACHED_API_KEY = secret_key
        mock_resp = mock.Mock()
        mock_resp.status_code = 400
        mock_resp.text = f'{{"error": ["bad request - invalid api key {secret_key}"]}}'
        mock_resp.json.return_value = {
            "error": [f"bad request - invalid api key {secret_key}"]
        }
        mock_requests_get.return_value = mock_resp

        with self.assertRaises(requests.exceptions.RequestException) as ctx:
            get_data({
                'key': secret_key,
                'source_desc': 'SURVEY',
                'year': 2024,
                'state_alpha': 'SC',
            })
        self.assertNotIn(secret_key, str(ctx.exception))

    @mock.patch('retry.api.time.sleep')
    @mock.patch.object(process.requests.Session, 'get')
    @mock.patch.object(process, 'is_rate_limited', return_value=False)
    def test_get_data_500_raises_error_and_redacts_api_key(
            self, mock_rate_limit, mock_requests_get, mock_retry_sleep):
        """Tests that get_data retries 504/500 errors, raises RequestException, and redacts the API key."""
        secret_key = 'SECRET-USDA-KEY-987654321'
        process._CACHED_API_KEY = secret_key
        mock_resp = mock.Mock()
        mock_resp.status_code = 504
        mock_resp.raise_for_status.side_effect = requests.exceptions.HTTPError(
            f'504 Server Error: Gateway Timeout for url: '
            f'https://quickstats.nass.usda.gov/api/api_GET?key={secret_key}&year=2026'
        )
        mock_requests_get.return_value = mock_resp

        with self.assertRaises(requests.exceptions.RequestException) as ctx:
            get_data({
                'key': secret_key,
                'source_desc': 'SURVEY',
                'year': 2026,
                'state_alpha': 'NH',
            })

        self.assertNotIn(secret_key, str(ctx.exception))
        self.assertIn('[REDACTED]', str(ctx.exception))
        self.assertEqual(mock_requests_get.call_count, process.RETRY_TRIES)

    @mock.patch.object(process, 'get_data', return_value=None)
    @mock.patch.object(process, 'get_usda_api_key', return_value='mock-api-key')
    def test_get_survey_county_data_none_raises(self, mock_key, mock_get_data):
        """Tests that get_survey_county_data raises RuntimeError if get_data returns None."""
        with self.assertRaises(RuntimeError):
            get_survey_county_data(2025, 'FAKECOUNTY', 'testdata')

    @mock.patch.object(process, 'get_data')
    @mock.patch.object(process,
                       'get_param_values',
                       return_value=['ABBEVILLE', 'AIKEN'])
    @mock.patch.object(process, 'get_usda_api_key', return_value='mock-api-key')
    def test_state_query_falls_back_to_counties_on_limit_exceeded(
            self, mock_key, mock_param_values, mock_get_data):
        """Tests automatic fallback to per-county queries when a state exceeds QuickStats' 50k limit."""
        mock_get_data.side_effect = [
            QueryLimitExceededError('exceeds limit=50000'),
            {
                'data': [self.mock_api_data['data'][0]]
            },
            {
                'data': [self.mock_api_data['data'][1]]
            },
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            result = get_survey_state_data(2024, 'SC', tmpdir)
            self.assertEqual(len(result['data']), 2)
            mock_param_values.assert_called_once_with('county_name',
                                                      state_alpha='SC',
                                                      agg_level_desc='COUNTY')

    @mock.patch.object(process.time, 'sleep')
    @mock.patch.object(process, '_execute_partition_batch')
    def test_two_pass_retry_recovers_transient_state_failure(
            self, mock_exec_batch, mock_sleep):
        """Tests that a state failing in pass 1 is retried in pass 2 and succeeds."""

        def side_effect(partitions, year, svs, input_dir, reuse_existing):
            if not reuse_existing:
                parts_dir = process.get_parts_dir(input_dir, year)
                with open(f'{parts_dir}/SC.csv', 'w', newline='') as f:
                    write_csv(f, to_csv_rows(self.mock_api_data, svs))
                return [('SC', True, ''), ('NH', False, '504 Gateway Timeout')]
            self.assertEqual(partitions, ['NH'])
            return [('NH', True, '')]

        mock_exec_batch.side_effect = side_effect
        svs = load_svs()

        with tempfile.TemporaryDirectory() as tmpdir:
            in_dir = os.path.join(tmpdir, 'input')
            out_dir = os.path.join(tmpdir, 'output')
            process_survey_data(2024, svs, in_dir, out_dir, states=['SC', 'NH'])

            self.assertEqual(mock_exec_batch.call_count, 2)
            mock_sleep.assert_called_once_with(
                process.SECOND_PASS_COOLDOWN_SECONDS)
            agg_csv = os.path.join(out_dir, 'ag-2024.csv')
            self.assertTrue(os.path.exists(agg_csv))
            with open(agg_csv, newline='') as f:
                rows = list(csv.DictReader(f))
            self.assertEqual(len(rows), 2)

    @mock.patch.object(process, '_execute_partition_batch')
    def test_stale_part_csvs_cleaned_before_run(self, mock_exec_batch):
        """Tests that leftover .csv files in parts/{year} are cleared before a new run."""

        def side_effect(partitions, year, svs, input_dir, reuse_existing):
            parts_dir = process.get_parts_dir(input_dir, year)
            with open(f'{parts_dir}/SC.csv', 'w', newline='') as f:
                write_csv(f, [to_csv_rows(self.mock_api_data, svs)[0]])
            return [('SC', True, '')]

        mock_exec_batch.side_effect = side_effect
        svs = load_svs()

        with tempfile.TemporaryDirectory() as tmpdir:
            in_dir = os.path.join(tmpdir, 'input')
            out_dir = os.path.join(tmpdir, 'output')
            stale_dir = process.get_parts_dir(in_dir, 2024)
            os.makedirs(stale_dir, exist_ok=True)
            with open(f'{stale_dir}/STALE.csv', 'w', newline='') as f:
                write_csv(f, [{
                    'variableMeasured': 'dcs:Count_Farm',
                    'observationDate': '2024',
                    'observationAbout': 'dcid:geoId/99999',
                    'value': 999,
                    'unit': '',
                }])

            process_survey_data(2024, svs, in_dir, out_dir, states=['SC'])

            with open(os.path.join(out_dir, 'ag-2024.csv'), newline='') as f:
                rows = list(csv.DictReader(f))
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]['observationAbout'], 'dcid:geoId/45001')

    def test_http_session_reused_within_process_and_reset_on_fork(self):
        """Tests fork-safe per-PID requests.Session caching."""
        s1 = process._get_http_session()
        s2 = process._get_http_session()
        self.assertIs(s1, s2)
        process._HTTP_SESSION_PID = -1
        s3 = process._get_http_session()
        self.assertIsNot(s1, s3)

    @mock.patch.object(process.time, 'sleep')
    @mock.patch.object(process, '_execute_partition_batch')
    def test_two_pass_retry_raises_when_second_pass_also_fails(
            self, mock_exec_batch, mock_sleep):
        """Tests that persistent failure across both passes raises RuntimeError (no silent data loss)."""
        mock_exec_batch.side_effect = [
            [('SC', True, ''), ('NH', False, '504 Gateway Timeout')],
            [('NH', False, '504 Gateway Timeout')],
        ]
        svs = load_svs()

        with tempfile.TemporaryDirectory() as tmpdir:
            with self.assertRaises(RuntimeError):
                process_survey_data(2026,
                                    svs,
                                    os.path.join(tmpdir, 'input'),
                                    os.path.join(tmpdir, 'output'),
                                    states=['SC', 'NH'])

    @mock.patch('retry.api.time.sleep')
    @mock.patch.object(process.requests.Session, 'get')
    @mock.patch.object(process, 'is_rate_limited', return_value=False)
    @mock.patch.object(process, 'get_usda_api_key', return_value='mock-api-key')
    def test_get_param_values_raises_on_504_instead_of_empty_list(
            self, mock_key, mock_rate_limit, mock_requests_get,
            mock_retry_sleep):
        """Tests that get_param_values raises RuntimeError on 504 instead of silently returning []."""
        mock_resp = mock.Mock()
        mock_resp.status_code = 504
        mock_resp.raise_for_status.side_effect = requests.exceptions.HTTPError(
            '504 Gateway Timeout')
        mock_requests_get.return_value = mock_resp

        with self.assertRaises(RuntimeError):
            get_param_values('state_alpha')


if __name__ == '__main__':
    absltest.main()

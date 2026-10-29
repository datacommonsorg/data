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
"""Unit tests for MOSPI_IndiaPLFS_DailyWages download.py."""

import os
import sys
import tempfile
import unittest
from unittest import mock

import pandas as pd
import requests

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if _SCRIPT_DIR not in sys.path:
    sys.path.insert(0, _SCRIPT_DIR)

import download  # pylint: disable=wrong-import-position


def _sample_api_record(
    year_type: str = 'Agriculture Year',
    year: str = '2017-18',
    quarter: str | None = 'Jul-Sep',
    value: str | None = '252.6',
) -> dict[str, object]:
    return {
        'year_type':
            year_type,
        'year':
            year,
        'frequency':
            'Annually',
        'indicator':
            'Average wage earnings (Rs. 0.00) per day from casual labour work other than public works',
        'state':
            'All India',
        'gender':
            'male',
        'sector':
            'rural',
        'quarter':
            quarter,
        'month':
            None,
        'value':
            value,
        'unit':
            '₹',
    }


def _mock_response(status_code: int, payload: dict[str, object]) -> mock.Mock:
    resp = mock.Mock(spec=requests.Response)
    resp.status_code = status_code
    resp.json.return_value = payload
    if status_code >= 400:
        resp.raise_for_status.side_effect = requests.HTTPError(
            f'HTTP {status_code}', response=resp)
    else:
        resp.raise_for_status.return_value = None
    return resp


class DownloadTest(unittest.TestCase):

    def test_fetch_mospi_daily_wages_paginates_all_pages(self):
        session = mock.Mock(spec=requests.Session)
        page1 = {
            'statusCode':
                True,
            'meta_data': {
                'page': 1,
                'totalRecords': 3,
                'totalPages': 2,
                'recordPerPage': 2,
            },
            'data': [
                _sample_api_record('Agriculture Year', '2017-18', 'Jul-Sep',
                                   '252.6'),
                _sample_api_record('Agriculture Year', '2023-24', 'Oct-Dec',
                                   None),
            ],
        }
        page2 = {
            'statusCode':
                True,
            'meta_data': {
                'page': 2,
                'totalRecords': 3,
                'totalPages': 2,
                'recordPerPage': 2,
            },
            'data': [
                _sample_api_record('Calendar Year', '2025', None, '450.25'),
            ],
        }
        session.get.side_effect = [
            _mock_response(200, page1),
            _mock_response(200, page2),
        ]

        df = download.fetch_mospi_daily_wages(
            session=session,
            api_url='https://api.mospi.gov.in/api/plfs/getData',
            page_size=2,
            retry_delay_seconds=0.01,
        )

        self.assertEqual(session.get.call_count, 2)
        self.assertEqual(len(df), 3)
        self.assertEqual(list(df.columns), download.COLUMNS)
        self.assertEqual(df.iloc[1]['value'], '')
        self.assertEqual(df.iloc[2]['quarter'], '')
        self.assertEqual(df.iloc[2]['value'], '450.25')

    def test_fetch_mospi_daily_wages_raises_on_record_count_mismatch(self):
        session = mock.Mock(spec=requests.Session)
        payload = {
            'statusCode': True,
            'meta_data': {
                'page': 1,
                'totalRecords': 5,
                'totalPages': 1,
                'recordPerPage': 200,
            },
            'data': [_sample_api_record()],
        }
        session.get.return_value = _mock_response(200, payload)

        with self.assertRaisesRegex(RuntimeError, 'does not match'):
            download.fetch_mospi_daily_wages(session=session,
                                             retry_delay_seconds=0.01)

    @mock.patch('download.time.sleep')
    def test_fetch_page_retries_transient_503_and_succeeds(self, mock_sleep):
        session = mock.Mock(spec=requests.Session)
        ok_payload = {'statusCode': True, 'data': [], 'meta_data': {}}
        session.get.side_effect = [
            _mock_response(503, {}),
            requests.Timeout('read timed out'),
            _mock_response(200, ok_payload),
        ]

        result = download._fetch_page(
            session=session,
            api_url='https://api.mospi.gov.in/api/plfs/getData',
            params={'page': 1},
            max_retries=3,
            retry_delay_seconds=1.0,
            retry_backoff=2.0,
        )

        self.assertEqual(result, ok_payload)
        self.assertEqual(session.get.call_count, 3)
        self.assertEqual(mock_sleep.call_count, 2)

    @mock.patch('download.time.sleep')
    def test_fetch_page_does_not_retry_permanent_400(self, mock_sleep):
        session = mock.Mock(spec=requests.Session)
        session.get.return_value = _mock_response(400, {'msg': 'Bad Request'})

        with self.assertRaises(requests.HTTPError):
            download._fetch_page(
                session=session,
                api_url='https://api.mospi.gov.in/api/plfs/getData',
                params={'limit': 500},
                max_retries=3,
            )

        self.assertEqual(session.get.call_count, 1)
        mock_sleep.assert_not_called()

    def test_merge_records_retains_historical_rows_and_updates_new_years(self):
        baseline_df = pd.DataFrame(
            [
                {
                    col: '' if v is None else str(v) for col, v in
                    _sample_api_record('Agriculture Year', '2017-18', 'Jul-Sep',
                                       '252.6').items()
                },
                {
                    col: '' if v is None else str(v)
                    for col, v in _sample_api_record('Calendar Year', '2025',
                                                     None, '440.0').items()
                },
            ],
            columns=download.COLUMNS,
        )
        live_df = pd.DataFrame(
            [
                {
                    col: '' if v is None else str(v)
                    for col, v in _sample_api_record('Calendar Year', '2025',
                                                     None, '445.5').items()
                },
                {
                    col: '' if v is None else str(v)
                    for col, v in _sample_api_record('Calendar Year', '2026',
                                                     None, '470.2').items()
                },
            ],
            columns=download.COLUMNS,
        )

        merged = download.merge_records(baseline_df, live_df)

        self.assertEqual(len(merged), 3)
        by_year = dict(zip(merged['year'], merged['value']))
        self.assertEqual(by_year['2017-18'], '252.6')
        self.assertEqual(by_year['2025'], '445.5')
        self.assertEqual(by_year['2026'], '470.2')

    def test_write_csv_atomically_and_load_baseline_roundtrip(self):
        df = pd.DataFrame(
            [{
                col: '' if v is None else str(v)
                for col, v in _sample_api_record().items()
            }],
            columns=download.COLUMNS,
        )
        with tempfile.TemporaryDirectory() as tmp_dir:
            out_path = os.path.join(tmp_dir, 'nested', 'daily_wages_input.csv')
            download.write_csv_atomically(df, out_path)
            loaded = download.load_baseline_csv(out_path)
            pd.testing.assert_frame_equal(loaded, df)


if __name__ == '__main__':
    unittest.main()

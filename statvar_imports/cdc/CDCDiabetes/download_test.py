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
"""Unit tests for CDCDiabetes download.py and consolidate_historical.py."""

import csv
import os
import subprocess
import sys
import tempfile
from typing import Any
import unittest
from unittest import mock

_CODEDIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(1, _CODEDIR)
sys.path.insert(1, os.path.join(_CODEDIR, '../../util/'))
sys.path.insert(1, os.path.join(_CODEDIR, '../../../util/'))

import consolidate_historical
import download


class _FakeResponse:
    """Minimal mock HTTP response for requests.Session."""

    def __init__(
        self,
        json_data: Any = None,
        text: str = '',
        ok: bool = True,
        status_code: int = 200,
    ):
        self._json_data = json_data
        self.text = text
        self.ok = ok
        self.status_code = status_code

    def raise_for_status(self) -> None:
        if not self.ok:
            raise RuntimeError('HTTP error')

    def json(self) -> Any:
        return self._json_data


class DownloadTest(unittest.TestCase):
    """Tests for CDC USDSS download.py and consolidate_historical.py."""

    def test_format_number_and_parse_estimate_and_stderr(self):
        self.assertEqual(download.format_number(9.8), '9.8')
        self.assertEqual(download.format_number(19.0), '19')
        self.assertEqual(download.format_number(1.2244897959), '1.22449')
        self.assertEqual(download.format_number(float('nan')), '')
        self.assertEqual(download.format_number(float('inf')), '')

        self.assertEqual(
            download.parse_estimate_and_stderr('9.8', '12.2'),
            ('9.8', '1.22449'),
        )
        self.assertIsNone(download.parse_estimate_and_stderr('No Data', '12.2'))
        self.assertIsNone(
            download.parse_estimate_and_stderr('9.8', 'Suppressed'))
        self.assertIsNone(download.parse_estimate_and_stderr('nan', '12.2'))
        self.assertIsNone(download.parse_estimate_and_stderr('9.8', 'inf'))
        self.assertIsNone(download.parse_estimate_and_stderr('-1.0', '12.2'))
        self.assertIsNone(download.parse_estimate_and_stderr('105.0', '110.0'))
        # Inverted confidence interval (upper_limit < percentage) must be rejected.
        self.assertIsNone(download.parse_estimate_and_stderr('12.2', '9.8'))

    def test_parse_counties_by_geoid_filters_invalid_and_pads_fips(self):
        self.assertEqual(download.parse_counties_by_geoid({}), {})
        self.assertEqual(
            download.parse_counties_by_geoid({'counties_list': None}), {})
        self.assertEqual(download.parse_indicator_years([]), {})
        self.assertEqual(
            download.parse_indicator_years([{
                'IndicatorID': 151,
                'YearsList': None
            }]),
            {151: []},
        )
        init_data = {
            'counties_list': [
                {
                    'CDC': 5501,
                    'CC': '1001',
                    'CN': 'Autauga County'
                },
                {
                    'CDC': 8740,
                    'CC': '09110',
                    'CN': 'Capitol Planning Region'
                },
                {
                    'CDC': 5002,
                    'CC': 'null',
                    'CN': 'All Counties'
                },
                {
                    'CDC': 'US',
                    'CC': '00000',
                    'CN': 'United States'
                },
                {
                    'CDC': 5999,
                    'CC': '01000',
                    'CN': 'Alabama State Total'
                },
            ]
        }
        self.assertEqual(
            download.parse_counties_by_geoid(init_data),
            {
                5501: '01001',
                8740: '09110',
            },
        )

    def test_discover_init_app_data_url_fallback_branches(self):
        session = mock.MagicMock()
        session.get.side_effect = [
            _FakeResponse(
                text=
                '<script src="scripts/surveillance_entry.abc123.app.js"></script>'
            ),
            _FakeResponse(text='', ok=False, status_code=404),
        ]
        self.assertEqual(
            download.discover_init_app_data_url(session),
            download.USDSS_DEFAULT_INIT_APP_DATA,
        )

        session.get.side_effect = [
            _FakeResponse(
                text=
                '<script src="scripts/surveillance_entry.abc123.app.js"></script>'
            ),
            _FakeResponse(text='no init app data here', ok=True),
        ]
        self.assertEqual(
            download.discover_init_app_data_url(session),
            download.USDSS_DEFAULT_INIT_APP_DATA,
        )

    def test_download_cdc_diabetes_data_writes_expected_csv(self):
        session = mock.MagicMock()

        def _fake_get(url: str, timeout: int = 60) -> _FakeResponse:
            del timeout
            if url == download.USDSS_REFERER:
                return _FakeResponse(
                    text=
                    '<script src="scripts/surveillance_entry.abc123.app.js"></script>'
                )
            if 'surveillance_entry.abc123.app.js' in url:
                return _FakeResponse(
                    text='const init="InitAppData_1111-2222.json";')
            if 'InitAppData_1111-2222.json' in url:
                return _FakeResponse(
                    json_data={
                        'counties_list': [
                            {
                                'CDC': 5501,
                                'CC': '01001',
                                'CN': 'Autauga County'
                            },
                            {
                                'CDC': 5002,
                                'CC': 'null',
                                'CN': 'All Counties'
                            },
                        ]
                    })
            if url == download.USDSS_YEARS_URL:
                return _FakeResponse(json_data=[
                    {
                        'IndicatorID':
                            151,
                        'YearsList': [
                            {
                                'Year': 2021,
                                'YearID': 342
                            },
                            {
                                'Year': 2022,
                                'YearID': 343
                            },
                        ],
                    },
                    {
                        'IndicatorID': 201,
                        'YearsList': [{
                            'Year': 2022,
                            'YearID': 343
                        }],
                    },
                    {
                        'IndicatorID': 202,
                        'YearsList': [{
                            'Year': 2022,
                            'YearID': 343
                        }],
                    },
                ])
            raise AssertionError(f'Unexpected GET URL: {url}')

        def _fake_post(url: str,
                       json: dict[str, Any],
                       timeout: int = 60) -> _FakeResponse:
            del url, timeout
            ind_id = json['IndicatorID']
            sex_id = json['SexID']
            est = 10.0 + (ind_id % 10) + (sex_id - 591)
            ul = est + 1.96
            return _FakeResponse(
                json_data={
                    'MapData': [
                        {
                            'GeoID': 5501,
                            'Sup': 100,
                            'Est': est,
                            'UL': ul,
                        },
                        {
                            'GeoID': 'US',
                            'Sup': 100,
                            'Est': 99.0,
                            'UL': 100.0,
                        },
                    ]
                })

        session.get.side_effect = _fake_get
        session.post.side_effect = _fake_post

        with tempfile.TemporaryDirectory() as tmp_dir:
            out_csv = download.download_cdc_diabetes_data(
                output_dir=tmp_dir,
                input_filename='cdc_diabetes.csv',
                start_year=2022,
                session=session,
            )
            with open(out_csv, 'r', encoding='utf-8') as fp:
                rows = list(csv.reader(fp))

        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0], download.INPUT_CSV_HEADERS)
        self.assertEqual(rows[1][0], '01001')
        self.assertEqual(rows[1][1], '2022')
        # diabetes (151 % 10 = 1), total (591 - 591 = 0) -> est = 11, stderr = 1
        self.assertEqual(rows[1][2], '11')
        self.assertEqual(rows[1][3], '1')

    def test_fetch_usdss_metrics_raises_on_zero_published_rows(self):
        session = mock.MagicMock()
        session.get.side_effect = [
            _FakeResponse(text=''),
            _FakeResponse(
                json_data={'counties_list': [{
                    'CDC': 5501,
                    'CC': '01001'
                }]}),
            _FakeResponse(json_data=[
                {
                    'IndicatorID': 151,
                    'YearsList': [{
                        'Year': 2022,
                        'YearID': 343
                    }],
                },
                {
                    'IndicatorID': 201,
                    'YearsList': [{
                        'Year': 2022,
                        'YearID': 343
                    }],
                },
                {
                    'IndicatorID': 202,
                    'YearsList': [{
                        'Year': 2022,
                        'YearID': 343
                    }],
                },
            ]),
        ]
        session.post.return_value = _FakeResponse(json_data={
            'MapData': [{
                'GeoID': 5501,
                'Sup': 0,
                'Est': None,
                'UL': None
            }]
        })

        with self.assertRaisesRegex(RuntimeError,
                                    'Zero valid published county estimates'):
            download.fetch_usdss_metrics(start_year=2022, session=session)

    def test_copy_historical_files_from_gcs(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            with mock.patch.object(download.file_util,
                                   'file_copy') as mock_copy:
                download.copy_historical_files_from_gcs('', tmp_dir)
                mock_copy.assert_not_called()
                self.assertFalse(
                    os.path.exists(os.path.join(tmp_dir, 'common_tmcf.tmcf')))

                gcs_dir = 'gs://unresolved_mcf/cdc/diabetes/historical/'
                download.copy_historical_files_from_gcs(gcs_dir, tmp_dir)

                dst_tmcf = os.path.join(tmp_dir, 'common_tmcf.tmcf')
                self.assertTrue(os.path.exists(dst_tmcf))
                with open(dst_tmcf, 'r', encoding='utf-8') as fp:
                    self.assertEqual(fp.read(), download.COMMON_TMCF_CONTENT)

                expected_calls = [
                    mock.call(
                        f'gs://unresolved_mcf/cdc/diabetes/historical/{fname}',
                        os.path.join(tmp_dir, fname),
                    ) for fname in download.HISTORICAL_CSVS
                ]
                mock_copy.assert_has_calls(expected_calls)
                self.assertEqual(mock_copy.call_count,
                                 len(download.HISTORICAL_CSVS))

    def test_consolidate_historical_filters_short_and_suppressed_rows(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            stage_dir = os.path.join(tmp_dir, 'stage')
            os.makedirs(stage_dir, exist_ok=True)
            sample_csv = os.path.join(
                stage_dir, 'DiabetesAtlasCountyData_diabetes2021.csv')
            with open(sample_csv, 'w', encoding='utf-8', newline='') as fp:
                fp.write('observationAbout,observationDate,variableMeasured,'
                         'value,measurementMethod,observationPeriod\n')
                fp.write('dcid:geoId/01001,2021,'
                         'dcid:Percent_Person_20OrMoreYears_WithDiabetes,'
                         '9.6,dcid:AgeAdjustedPrevalence,P1Y\n')
                # Short truncated row (missing value/variableMeasured)
                fp.write('dcid:geoId/01003,2021\n')
                # Suppressed value row
                fp.write('dcid:geoId/01005,2021,'
                         'dcid:Percent_Person_20OrMoreYears_WithDiabetes,'
                         'No Data,dcid:AgeAdjustedPrevalence,P1Y\n')

            out_csv = os.path.join(tmp_dir, 'out',
                                   'cdc_diabetes_historical_2004_2021.csv')
            with mock.patch.object(subprocess, 'run'):
                consolidate_historical.consolidate_files(
                    [sample_csv],
                    out_csv,
                    stage_dir,
                )

            with open(out_csv, 'r', encoding='utf-8') as fp:
                rows = list(csv.reader(fp))
            self.assertEqual(len(rows), 2)
            self.assertEqual(
                rows[1],
                [
                    'dcid:geoId/01001',
                    '2021',
                    'dcid:Percent_Person_20OrMoreYears_WithDiabetes',
                    '9.6',
                    'dcid:AgeAdjustedPrevalence',
                    'P1Y',
                ],
            )


if __name__ == '__main__':
    unittest.main()

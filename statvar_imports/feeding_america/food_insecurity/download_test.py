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
"""Unit tests for FeedingAmerica_FoodInsecurity download.py."""

import csv
import os
import tempfile
import unittest
from unittest import mock

import requests

from statvar_imports.feeding_america.food_insecurity import download


class DownloadTest(unittest.TestCase):

    def test_format_dcid(self):
        self.assertEqual(download.format_dcid('state', '1'), 'dcid:geoId/01')
        self.assertEqual(download.format_dcid('state', '56'), 'dcid:geoId/56')
        self.assertEqual(download.format_dcid('county', '1001'),
                         'dcid:geoId/01001')
        self.assertEqual(download.format_dcid('county', 56045),
                         'dcid:geoId/56045')
        self.assertEqual(download.format_dcid('district', '101'),
                         'dcid:geoId/0101')
        self.assertEqual(download.format_dcid('district', '200'),
                         'dcid:geoId/0200')
        self.assertEqual(download.format_dcid('district', '1198'),
                         'dcid:geoId/1198')
        self.assertEqual(download.format_dcid('district', '5600'),
                         'dcid:geoId/5600')
        self.assertIsNone(download.format_dcid('county', ''))
        self.assertIsNone(download.format_dcid('county', None))
        self.assertIsNone(download.format_dcid('district', 'abc'))
        self.assertIsNone(download.format_dcid('other', '1001'))

    def test_resolve_bands_restores_zero(self):
        self.assertEqual(download.resolve_bands(1.0, None, None),
                         (1.0, None, 0.0))
        self.assertEqual(download.resolve_bands(0.8, 0.2, None),
                         (0.8, 0.2, 0.0))
        self.assertEqual(download.resolve_bands(None, None, 1.0),
                         (0.0, None, 1.0))
        self.assertEqual(download.resolve_bands(0.452, None, 0.548),
                         (0.452, None, 0.548))
        self.assertEqual(download.resolve_bands(None, None, None),
                         (None, None, None))

    def test_to_pct(self):
        self.assertEqual(download.to_pct(None), '')
        self.assertEqual(download.to_pct(0.0), 0.0)
        self.assertEqual(download.to_pct(0.148), 14.8)
        self.assertEqual(download.to_pct(0.123456), 12.3456)

    def test_fetch_json_retries_on_transient_and_succeeds(self):
        transient_resp = mock.MagicMock()
        transient_resp.status_code = 503
        transient_resp.url = 'https://example.com/mapdata'

        good_resp = mock.MagicMock()
        good_resp.status_code = 200
        good_resp.url = 'https://example.com/mapdata'
        good_resp.json.return_value = {'state': []}

        session = mock.MagicMock()
        session.get.side_effect = [transient_resp, good_resp]

        with mock.patch('time.sleep') as mock_sleep:
            data = download.fetch_json(
                'https://example.com/mapdata',
                params={'year': '2024'},
                session=session,
                max_retries=3,
            )
        self.assertEqual(data, {'state': []})
        mock_sleep.assert_called_once_with(1)

    def test_fetch_json_fails_immediately_on_permanent_4xx(self):
        bad_resp = mock.MagicMock()
        bad_resp.status_code = 404
        bad_resp.url = 'https://example.com/mapdata'
        bad_resp.raise_for_status.side_effect = requests.HTTPError(
            '404 Not Found', response=bad_resp)

        session = mock.MagicMock()
        session.get.return_value = bad_resp

        with mock.patch('time.sleep') as mock_sleep:
            with self.assertRaises(RuntimeError):
                download.fetch_json(
                    'https://example.com/mapdata',
                    session=session,
                    max_retries=3,
                )
        mock_sleep.assert_not_called()
        self.assertEqual(session.get.call_count, 1)

    def test_fetch_json_raises_after_max_retries(self):
        session = mock.MagicMock()
        session.get.side_effect = requests.ConnectionError('network down')

        with mock.patch('time.sleep'):
            with self.assertRaises(RuntimeError):
                download.fetch_json(
                    'https://example.com/mapdata',
                    session=session,
                    max_retries=2,
                )
        self.assertEqual(session.get.call_count, 2)

    def test_discover_years_parses_inertia_script_payload(self):
        resp = mock.MagicMock()
        resp.text = ('<html><script data-page="app" type="application/json">'
                     '{"props":{"filters":{"years":[{"year":"2025"},'
                     '{"year":"2021"},{"year":"2020"}]}}}</script></html>')
        session = mock.MagicMock()
        session.get.return_value = resp

        years = download.discover_years(session=session)
        self.assertEqual(years, ['2022', '2023', '2024', '2025'])

    def test_discover_years_parses_escaped_attribute_fallback(self):
        resp = mock.MagicMock()
        resp.text = (
            '<div data-page="{&quot;props&quot;:{&quot;filters&quot;:'
            '{&quot;years&quot;:[{&quot;year&quot;:&quot;2026&quot;}]}}}">'
            '</div>')
        session = mock.MagicMock()
        session.get.return_value = resp

        years = download.discover_years(session=session)
        self.assertIn('2026', years)
        self.assertNotIn('2021', years)

    def test_build_session_disables_cookies(self):
        with download.build_session() as session:
            policy = session.cookies.get_policy()
            self.assertEqual(policy.allowed_domains(), ())

    def test_discover_years_retries_and_succeeds(self):
        transient_resp = mock.MagicMock()
        transient_resp.status_code = 500
        transient_resp.url = 'https://map.feedingamerica.org/'

        good_resp = mock.MagicMock()
        good_resp.status_code = 200
        good_resp.text = (
            '<html><script data-page="app" type="application/json">'
            '{"props":{"filters":{"years":[{"year":"2025"}]}}}'
            '</script></html>')
        session = mock.MagicMock()
        session.get.side_effect = [transient_resp, good_resp]

        with mock.patch('time.sleep') as mock_sleep:
            years = download.discover_years(session=session, max_retries=3)
        self.assertIn('2025', years)
        mock_sleep.assert_called_once_with(1)

    def test_discover_years_does_not_retry_permanent_4xx(self):
        bad_resp = mock.MagicMock()
        bad_resp.status_code = 404
        bad_resp.url = 'https://map.feedingamerica.org/'
        bad_resp.raise_for_status.side_effect = requests.HTTPError(
            '404 Not Found', response=bad_resp)
        session = mock.MagicMock()
        session.get.return_value = bad_resp

        with mock.patch('time.sleep') as mock_sleep:
            years = download.discover_years(session=session, max_retries=3)
        self.assertEqual(years, download.DEFAULT_YEARS)
        mock_sleep.assert_not_called()
        self.assertEqual(session.get.call_count, 1)

    def test_discover_years_fallback_on_error(self):
        session = mock.MagicMock()
        session.get.side_effect = requests.Timeout('timed out')

        with mock.patch('time.sleep'):
            years = download.discover_years(session=session, max_retries=2)
        self.assertEqual(years, download.DEFAULT_YEARS)

    def test_load_baseline_missing_raises(self):
        with self.assertRaises(FileNotFoundError):
            download.load_baseline('/nonexistent/path/baseline.csv')

    def test_build_row_with_mid_band_and_zero_restoration(self):
        row = download.build_row_from_api(
            level='state',
            dcid='dcid:geoId/01',
            year='2024',
            ov={
                'insecurity': 0.148,
                'population': 746550,
                'low_band': 0.405,
                'mid_band': 0.164,
                'high_band': 0.431,
                'cost_per_meal': 3.5,
                'money_needed': 461137000,
            },
            ch={
                'insecurity': 0.183,
                'population': 204830,
                'low_band': 1.0,
                'high_band': None,
            },
            bl={'insecurity': 0.26},
            hi={'insecurity': 0.12},
            wh={'insecurity': 0.10},
        )
        self.assertEqual(
            row['Count_Person_FoodInsecure_AsAFractionOf_Count_Person'], 14.8)
        self.assertEqual(
            row['Count_Person_FoodInsecure_HouseholdIncomeAboveStateLowThresholdAndBelowOrEqualStateHighThreshold_AsAFractionOf_Count_Person_FoodInsecure'],
            16.4,
        )
        self.assertEqual(
            row['Count_Person_FoodInsecure_HouseholdIncomeAboveStateHighThreshold_AsAFractionOf_Count_Person_FoodInsecure'],
            43.1,
        )
        self.assertEqual(
            row['Count_Person_FoodInsecure_HouseholdIncomeAboveStateLowThreshold_AsAFractionOf_Count_Person_FoodInsecure'],
            59.5,
        )
        self.assertEqual(
            row['Count_Child_FoodInsecure_HouseholdIncomeAbove185PercentOfFederalPovertyLine_AsAFractionOf_Count_Child_FoodInsecure'],
            0.0,
        )
        self.assertEqual(row['Mean_CostPerMeal_Person_FoodInSecure'], 3.5)
        self.assertEqual(
            row['Weekly_WeightedFoodSpendAmount_Person_FoodInSecure'], 20.36)
        self.assertEqual(row['Annual_WeightedBudgetShortfall_Food'], 461137000)

    def test_build_row_returns_none_for_all_empty_record(self):
        row = download.build_row_from_api(
            level='district',
            dcid='dcid:geoId/7298',
            year='2023',
            ov={
                'insecurity': None,
                'population': None
            },
            ch={},
            bl={},
            hi={},
            wh={},
        )
        self.assertIsNone(row)

    def test_main_merges_baseline_and_live_api(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            baseline_csv = os.path.join(tmp_dir, 'baseline.csv')
            output_csv = os.path.join(tmp_dir, 'output.csv')
            with open(baseline_csv, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=download.FIELDNAMES)
                writer.writeheader()
                baseline_row = {k: '' for k in download.FIELDNAMES}
                baseline_row.update({
                    'dcid':
                        'geoId/01',
                    'observationDate':
                        '2020',
                    'Count_Person_FoodInsecure_AsAFractionOf_Count_Person':
                        '14.8',
                    'Count_Person_FoodInsecure':
                        '746550',
                    'Count_Person_FoodInsecure_HouseholdIncomeAboveStateLowThresholdAndBelowOrEqualStateHighThreshold_AsAFractionOf_Count_Person_FoodInsecure':
                        '16.4',
                    'Count_Person_FoodInsecure_HouseholdIncomeAboveStateHighThreshold_AsAFractionOf_Count_Person_FoodInsecure':
                        '31.1',
                })
                writer.writerow(baseline_row)

            def fake_fetch_json(_url, params=None, **_kwargs):
                mtype = params['maptype']
                dtype = params['type']
                if mtype == 'county':
                    if dtype == 'overall':
                        return {
                            'state': [{
                                'fips': '1',
                                'insecurity': 0.178,
                                'population': 919160,
                                'low_band': 0.452,
                                'mid_band': None,
                                'high_band': 0.548,
                                'cost_per_meal': 3.58,
                                'money_needed': 624874000,
                            }],
                            'county': [{
                                'fips': '1001',
                                'insecurity': 0.156,
                                'population': 9350,
                                'low_band': 1.0,
                                'mid_band': None,
                                'high_band': None,
                                'cost_per_meal': 3.68,
                                'money_needed': 6528000,
                            }],
                        }
                    if dtype == 'child':
                        return {
                            'state': [{
                                'fips': '1',
                                'insecurity': 0.22,
                                'population': 240000,
                                'low_band': 0.77,
                                'high_band': 0.23,
                            }],
                            'county': [{
                                'fips': '1001',
                                'insecurity': 0.18,
                                'population': 2500,
                                'low_band': 1.0,
                                'high_band': None,
                            }],
                        }
                    return {
                        'state': [{
                            'fips': '1',
                            'insecurity': 0.15
                        }],
                        'county': [{
                            'fips': '1001',
                            'insecurity': 0.14
                        }],
                    }

                # district
                if dtype == 'overall':
                    return {
                        'district': [
                            {
                                'fips': '101',
                                'insecurity': 0.178,
                                'population': 135050,
                                'low_band': 0.492,
                                'mid_band': None,
                                'high_band': 0.508,
                                'cost_per_meal': 3.58,
                                'money_needed': 90000000,
                            },
                            {
                                'fips': '7298',
                                'insecurity': None,
                                'population': None,
                            },
                        ],
                    }
                if dtype == 'child':
                    return {
                        'district': [{
                            'fips': '101',
                            'insecurity': 0.21,
                            'population': 35000,
                            'low_band': 0.75,
                            'high_band': 0.25,
                        }],
                    }
                return {'district': [{'fips': '101', 'insecurity': 0.12}]}

            with (
                    mock.patch.object(download, 'BASELINE_LOCAL', baseline_csv),
                    mock.patch.object(download, 'OUTPUT_INPUT_CSV', output_csv),
                    mock.patch.object(download,
                                      'discover_years',
                                      return_value=['2024']),
                    mock.patch.object(download,
                                      'fetch_json',
                                      side_effect=fake_fetch_json),
            ):
                download.main()

            with open(output_csv, 'r', encoding='utf-8') as f:
                rows = {
                    (r['dcid'], r['observationDate']): r
                    for r in csv.DictReader(f)
                }

            # 1 baseline + 3 live (state, county, district; empty 7298 skipped)
            self.assertEqual(len(rows), 4)
            self.assertNotIn(('dcid:geoId/7298', '2024'), rows)

            # Baseline preserved verbatim with dcid: prefix
            b = rows[('dcid:geoId/01', '2020')]
            self.assertEqual(
                b['Count_Person_FoodInsecure_HouseholdIncomeAboveStateHighThreshold_AsAFractionOf_Count_Person_FoodInsecure'],
                '31.1',
            )

            # State 2024
            st = rows[('dcid:geoId/01', '2024')]
            self.assertEqual(st['Mean_CostPerMeal_Person_FoodInSecure'], '3.58')
            self.assertEqual(st['Annual_WeightedBudgetShortfall_Food'],
                             '624874000')
            self.assertEqual(
                st['Weekly_WeightedFoodSpendAmount_Person_FoodInSecure'],
                '22.41',
            )
            self.assertEqual(
                st['Count_Person_HispanicOrLatino_FoodInSecure_AsAFractionOf_Count_Person_HispanicOrLatino'],
                '15.0',
            )

            # County 2024 zero restoration on high_band
            cty = rows[('dcid:geoId/01001', '2024')]
            self.assertEqual(
                cty['Count_Person_FoodInsecure_HouseholdIncomeAboveStateLowThreshold_AsAFractionOf_Count_Person_FoodInsecure'],
                '0.0',
            )
            self.assertEqual(
                cty['Count_Child_FoodInsecure_HouseholdIncomeAbove185PercentOfFederalPovertyLine_AsAFractionOf_Count_Child_FoodInsecure'],
                '0.0',
            )

            # District 2024 excludes the 3 USDollar StatVars
            dist = rows[('dcid:geoId/0101', '2024')]
            self.assertEqual(dist['Mean_CostPerMeal_Person_FoodInSecure'], '')
            self.assertEqual(
                dist['Weekly_WeightedFoodSpendAmount_Person_FoodInSecure'], '')
            self.assertEqual(dist['Annual_WeightedBudgetShortfall_Food'], '')
            self.assertEqual(dist['Count_Person_FoodInsecure'], '135050')

            # No leftover temporary files
            tmp_files = [
                fn for fn in os.listdir(tmp_dir)
                if fn.startswith('.tmp_feedingamerica_')
            ]
            self.assertEqual(tmp_files, [])


if __name__ == '__main__':
    unittest.main()

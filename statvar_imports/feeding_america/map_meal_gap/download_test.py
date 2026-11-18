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
"""Unit tests for FeedingAmerica_MapMealGap download.py."""

import csv
import io
import os
import tempfile
import unittest
from unittest import mock
import urllib.error

try:
    from statvar_imports.feeding_america.map_meal_gap import download
except ModuleNotFoundError:
    import download


class DownloadTest(unittest.TestCase):

    def test_format_dcid(self):
        self.assertEqual(download.format_dcid('state', '1'), 'dcid:geoId/01')
        self.assertEqual(download.format_dcid('state', '56'), 'dcid:geoId/56')
        self.assertEqual(download.format_dcid('county', '1001'),
                         'dcid:geoId/01001')
        self.assertEqual(download.format_dcid('county', 56045),
                         'dcid:geoId/56045')
        self.assertIsNone(download.format_dcid('county', ''))
        self.assertIsNone(download.format_dcid('other', '1001'))

    def test_resolve_bands_restores_zero(self):
        self.assertEqual(download.resolve_bands(1.0, None, None),
                         (1.0, None, 0.0))
        self.assertEqual(download.resolve_bands(0.8, 0.2, None),
                         (0.8, 0.2, 0.0))
        self.assertEqual(download.resolve_bands(None, None, 1.0),
                         (0.0, None, 1.0))
        self.assertEqual(download.resolve_bands(0.486, 0.109, 0.406),
                         (0.486, 0.109, 0.406))
        self.assertEqual(download.resolve_bands('', 'N/A', None),
                         (None, None, None))

    def test_compute_product(self):
        self.assertEqual(download.compute_product(8670, 0.486), 4213.62)
        self.assertEqual(download.compute_product(2590, 0.0), 0.0)
        self.assertEqual(download.compute_product(None, 0.5), '')
        self.assertEqual(download.compute_product(1000, None), '')
        self.assertEqual(download.compute_product('', '0.5'), '')
        self.assertEqual(download.compute_product('bad', 0.5), '')

    def test_ensure_baseline_raises_when_missing_and_no_gsutil(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            missing_path = os.path.join(tmp_dir, 'missing.csv')
            with (
                    mock.patch.object(download, 'BASELINE_LOCAL', missing_path),
                    mock.patch('shutil.which', return_value=None),
            ):
                with self.assertRaises(FileNotFoundError):
                    download.ensure_baseline()

    def test_ensure_baseline_downloads_via_gsutil_check_true(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            baseline_path = os.path.join(tmp_dir, 'baseline.csv')

            def fake_run(cmd, check=False):
                self.assertTrue(check)
                with open(baseline_path, 'w', encoding='utf-8') as f:
                    f.write('dcid,observationDate\n')

            with (
                    mock.patch.object(download, 'BASELINE_LOCAL',
                                      baseline_path),
                    mock.patch('shutil.which', return_value='/usr/bin/gsutil'),
                    mock.patch('subprocess.run', side_effect=fake_run) as m_run,
            ):
                download.ensure_baseline()
            m_run.assert_called_once()

    def test_fetch_json_retries_and_succeeds(self):
        err = urllib.error.HTTPError('https://example.com', 500, 'Server Error',
                                     {}, None)
        good_resp = mock.MagicMock()
        good_resp.__enter__.return_value.read.return_value = b'{"state": []}'
        with (
                mock.patch('urllib.request.urlopen',
                           side_effect=[err, good_resp]),
                mock.patch('time.sleep') as mock_sleep,
        ):
            data = download.fetch_json('https://example.com', max_retries=3)
        self.assertEqual(data, {'state': []})
        mock_sleep.assert_called_once_with(1)

    def test_fetch_json_retries_on_json_decode_error(self):
        bad_resp = mock.MagicMock()
        bad_resp.__enter__.return_value.read.return_value = b'<html>502</html>'
        good_resp = mock.MagicMock()
        good_resp.__enter__.return_value.read.return_value = b'{"county": []}'
        with (
                mock.patch('urllib.request.urlopen',
                           side_effect=[bad_resp, good_resp]),
                mock.patch('time.sleep') as mock_sleep,
        ):
            data = download.fetch_json('https://example.com', max_retries=3)
        self.assertEqual(data, {'county': []})
        mock_sleep.assert_called_once_with(1)

    def test_fetch_json_raises_after_max_retries(self):
        err = urllib.error.HTTPError('https://example.com', 500, 'Server Error',
                                     {}, None)
        with (
                mock.patch('urllib.request.urlopen', side_effect=err),
                mock.patch('time.sleep'),
        ):
            with self.assertRaises(RuntimeError):
                download.fetch_json('https://example.com', max_retries=2)

    def test_discover_years_parses_inertia_payload(self):
        html_page = ('<html><script data-page="app" type="application/json">'
                     '{"props":{"filters":{"years":[{"year":"2025"}]}}}'
                     '</script></html>').encode('utf-8')
        resp = mock.MagicMock()
        resp.__enter__.return_value = io.BytesIO(html_page)
        with mock.patch('urllib.request.urlopen', return_value=resp):
            years = download.discover_years()
        self.assertIn('2025', years)
        self.assertIn('2020', years)

    def test_main_merges_baseline_and_live_api(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            baseline_csv = os.path.join(tmp_dir, 'baseline.csv')
            output_csv = os.path.join(tmp_dir, 'output.csv')
            with open(baseline_csv, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=download.FIELDNAMES)
                writer.writeheader()
                writer.writerow({
                    'dcid':
                        'geoId/01001',
                    'observationDate':
                        '2019',
                    'Count_Person_FoodInsecure':
                        '8670',
                    'Count_Person_FoodInsecure_EligibleForAllFederalBenefits':
                        ('4213.62'),
                    'Count_Person_FoodInsecure_EligibleForSomeFederalBenefits':
                        ('945.03'),
                    'Count_Person_FoodInsecure_IneligibleForFederalBenefits':
                        '3520.02',
                    'Count_Child_FoodInsecure':
                        '2590',
                    'Count_Child_FoodInsecure_EligibleForManyChildNutritionBenefits':
                        ('1787.1'),
                    'Count_Child_FoodInsecure_IneligibleForChildNutritionBenefits':
                        ('802.9'),
                    'Mean_MealCost_Person_FoodSecure':
                        '3',
                    'Annual_FoodBudgetShortfall':
                        '4439000',
                })

            def fake_fetch_json(url):
                if 'type=overall' in url:
                    return {
                        'state': [{
                            'fips': 'US',
                            'population': 100,
                        }],
                        'county': [{
                            'fips': '1001',
                            'population': 8000,
                            'low_band': 1.0,
                            'mid_band': None,
                            'high_band': None,
                            'cost_per_meal': 3.456,
                            'money_needed': 5000000,
                        }],
                    }
                return {
                    'state': [],
                    'county': [{
                        'fips': '1001',
                        'population': 2000,
                        'low_band': 0.75,
                        'high_band': 0.25,
                    }],
                }

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
                rows = list(csv.DictReader(f))
            self.assertEqual(len(rows), 2)
            self.assertEqual(rows[0]['dcid'], 'dcid:geoId/01001')
            self.assertEqual(rows[0]['observationDate'], '2019')
            self.assertEqual(rows[1]['dcid'], 'dcid:geoId/01001')
            self.assertEqual(rows[1]['observationDate'], '2024')
            self.assertEqual(
                rows[1]
                ['Count_Person_FoodInsecure_IneligibleForFederalBenefits'],
                '0.0',
            )
            self.assertEqual(rows[1]['Mean_MealCost_Person_FoodSecure'], '3.46')


if __name__ == '__main__':
    unittest.main()

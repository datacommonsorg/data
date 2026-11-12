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
"""Unit tests for process_bea_gdp_rpp.py."""

import os
import tempfile
import unittest
from unittest import mock
import urllib.error

from scripts.us_bea.gdp_price_parity import process_bea_gdp_rpp


class ProcessBeaGdpRppTest(unittest.TestCase):

    def setUp(self):
        super().setUp()
        self.test_data_dir = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), 'test_data')

    def test_end_to_end_sample_directory(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            out_csv = os.path.join(tmp_dir, 'output.csv')
            count = process_bea_gdp_rpp.process_all(self.test_data_dir,
                                                    out_csv,
                                                    download=False)
            self.assertEqual(count, 21)

            expected_csv = os.path.join(self.test_data_dir,
                                        'expected_output.csv')
            with open(out_csv, 'r', encoding='utf-8') as f_actual:
                actual_text = f_actual.read()
            with open(expected_csv, 'r', encoding='utf-8') as f_expected:
                expected_text = f_expected.read()
            self.assertEqual(actual_text, expected_text)

    def test_cns_baseline_loading_and_overlay(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            baseline_dir = os.path.join(tmp_dir, 'cns_baseline')
            os.makedirs(baseline_dir, exist_ok=True)
            with open(os.path.join(baseline_dir, 'metro_gdp.csv'),
                      'w',
                      encoding='utf-8') as f:
                f.write('geoid\tyear\tgrossDomesticProduct\tgrowthRate\n'
                        'C10180\t2012\t5932000000\t\n'
                        'C10180\t2013\t6294000000\t6.1\n')
            with open(
                    os.path.join(baseline_dir, 'metro_nominal_gdp.csv'),
                    'w',
                    encoding='utf-8',
            ) as f:
                f.write(
                    'geoid\tyear\tgrossDomesticProduct\nC10180\t2012\t6397000000\n'
                )
            with open(
                    os.path.join(baseline_dir, 'county_gdp_all.csv'),
                    'w',
                    encoding='utf-8',
            ) as f:
                f.write(
                    'geoid\tyear\tnaics\tgrossDomesticProduct\tdataSuppressed\n'
                    'geoId/01001\t2016\tNAICS/10\t1383941000\t\n')

            records = {}
            loaded = process_bea_gdp_rpp.load_cns_baseline(
                baseline_dir, records)
            self.assertEqual(loaded, 6)
            self.assertEqual(
                records[(
                    'dcid:geoId/C10180',
                    'dcs:grossDomesticProduct',
                    '2012',
                    'dcs:BEASurvey',
                    'dcs:USDollar',
                )],
                '5932000000',
            )
            self.assertEqual(
                records[(
                    'dcid:geoId/C10180',
                    'dcid:dc/c3wwfwyx45v5h',
                    '2013',
                    'dcs:BEASurvey',
                    'dcs:USDollar',
                )],
                '6294000000',
            )
            self.assertEqual(
                records[(
                    'dcid:geoId/C10180',
                    'dcid:dc/p9w3tzjzyqrr',
                    '2013',
                    'dcs:BEASurvey',
                    'dcs:USDollar',
                )],
                '6.1',
            )
            self.assertEqual(
                records[(
                    'dcid:geoId/C10180',
                    'dcs:nominalGrossDomesticProduct',
                    '2012',
                    'dcs:BEAGDPMeasure',
                    'dcs:USDollar',
                )],
                '6397000000',
            )

    def test_is_valid_value_and_geofips(self):
        self.assertFalse(process_bea_gdp_rpp.is_valid_value('(NA)'))
        self.assertFalse(process_bea_gdp_rpp.is_valid_value('(D)'))
        self.assertFalse(process_bea_gdp_rpp.is_valid_value('(NM)'))
        self.assertFalse(process_bea_gdp_rpp.is_valid_value(''))
        self.assertTrue(process_bea_gdp_rpp.is_valid_value('123,456.78'))
        self.assertEqual(
            process_bea_gdp_rpp.normalize_county_or_state_geofips('" 00000"'),
            'dcid:country/USA',
        )
        self.assertEqual(
            process_bea_gdp_rpp.normalize_county_or_state_geofips('" 06000"'),
            'dcid:geoId/06',
        )
        self.assertEqual(
            process_bea_gdp_rpp.normalize_county_or_state_geofips('" 06085"'),
            'dcid:geoId/06085',
        )
        self.assertIsNone(
            process_bea_gdp_rpp.normalize_county_or_state_geofips('" 98000"'))
        self.assertEqual(
            process_bea_gdp_rpp.normalize_msa_geofips('"41940"'),
            'dcid:geoId/C41940',
        )

    def test_empty_directory_raises_runtime_error(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            out_csv = os.path.join(tmp_dir, 'out.csv')
            with self.assertRaises(RuntimeError):
                process_bea_gdp_rpp.process_all(tmp_dir,
                                                out_csv,
                                                download=False)

    @mock.patch('time.sleep', return_value=None)
    @mock.patch('urllib.request.urlopen')
    def test_download_with_retries_and_failure(self, mock_urlopen, _):
        mock_urlopen.side_effect = urllib.error.URLError(
            'transient network error')
        with tempfile.TemporaryDirectory() as tmp_dir:
            target = os.path.join(tmp_dir, 'test.zip')
            with self.assertRaises(RuntimeError):
                process_bea_gdp_rpp._download_with_retries(
                    'https://example.com/test.zip', target, max_retries=2)
            self.assertEqual(mock_urlopen.call_count, 2)


if __name__ == '__main__':
    unittest.main()

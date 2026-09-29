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
"""Unit tests for NYS Health Indicators Downloader."""

import os
import sys
import tempfile
import unittest
from unittest import mock
import pandas as pd

# Ensure repository root is in sys.path for local and root-level test runs
script_dir = os.path.dirname(os.path.abspath(__file__))
repo_root = os.path.abspath(os.path.join(script_dir, '../../..'))
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

from statvar_imports.us_newyork.ny_brfss_health_indicators.download import (
    atomic_to_csv,
    download_health_indicators,
)


class DownloadTest(unittest.TestCase):

    def test_atomic_to_csv_failure_cleanup(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            target_path = os.path.join(tmp_dir, 'test_output.csv')
            temp_path = f'{target_path}.tmp'

            with mock.patch.object(pd.DataFrame, 'to_csv') as mock_to_csv:
                def create_empty_tmp(path, index=False):
                    with open(path, 'w'):
                        pass

                mock_to_csv.side_effect = create_empty_tmp
                df = pd.DataFrame([{'col': 'val'}])
                with self.assertRaises(RuntimeError):
                    atomic_to_csv(df, target_path)

            self.assertFalse(os.path.exists(target_path))
            self.assertFalse(os.path.exists(temp_path))

    @mock.patch(
        'statvar_imports.us_newyork.ny_brfss_health_indicators.download.logging.fatal',
        side_effect=SystemExit,
    )
    @mock.patch(
        'statvar_imports.us_newyork.ny_brfss_health_indicators.download.create_session'
    )
    def test_download_health_indicators_http_error(self, mock_create_session,
                                                   mock_fatal):
        mock_session = mock.MagicMock()
        mock_session.__enter__.return_value = mock_session
        mock_create_session.return_value = mock_session
        mock_resp = mock.MagicMock()
        mock_resp.status_code = 500
        mock_resp.text = 'Internal Server Error'
        mock_session.get.return_value = mock_resp

        with tempfile.TemporaryDirectory() as tmp_dir:
            with self.assertRaises(SystemExit):
                download_health_indicators('https://mock-endpoint', tmp_dir)
            mock_fatal.assert_called_once()

    @mock.patch(
        'statvar_imports.us_newyork.ny_brfss_health_indicators.download.logging.fatal',
        side_effect=SystemExit,
    )
    @mock.patch(
        'statvar_imports.us_newyork.ny_brfss_health_indicators.download.create_session'
    )
    def test_download_health_indicators_empty_error(self, mock_create_session,
                                                    mock_fatal):
        mock_session = mock.MagicMock()
        mock_session.__enter__.return_value = mock_session
        mock_create_session.return_value = mock_session
        mock_resp = mock.MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = []
        mock_session.get.return_value = mock_resp

        with tempfile.TemporaryDirectory() as tmp_dir:
            with self.assertRaises(SystemExit):
                download_health_indicators('https://mock-endpoint', tmp_dir)
            mock_fatal.assert_called_once()

    @mock.patch(
        'statvar_imports.us_newyork.ny_brfss_health_indicators.download.create_session'
    )
    def test_download_health_indicators(self, mock_create_session):
        mock_session = mock.MagicMock()
        mock_session.__enter__.return_value = mock_session
        mock_create_session.return_value = mock_session

        mock_records = [
            {
                'years': '2021',
                'region_county': 'Albany',
                'health_indicator_short_name': 'Diabetes',
                'unadjusted_rate': '9.2',
            },
            {
                'years': '2021',
                'region_county': 'Albany',
                'health_indicator_short_name': 'Asthma',
                'unadjusted_rate': '11.3',
            },
            {
                'years': '2021',
                'region_county': 'REGION: Capital Region',
                'health_indicator_short_name': 'Diabetes',
                'unadjusted_rate': '8.5',
            },
            {
                'years': '2021',
                'region_county': 'REGION: Capital Region',
                'health_indicator_short_name': 'Asthma',
                'unadjusted_rate': '10.1',
            },
        ]

        mock_resp = mock.MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.side_effect = [mock_records, []]
        mock_session.get.return_value = mock_resp

        with tempfile.TemporaryDirectory() as tmp_dir:
            count, files = download_health_indicators('https://mock-endpoint',
                                                      tmp_dir)
            mock_session.get.assert_any_call('https://mock-endpoint',
                                             params={
                                                 '$limit': 50000,
                                                 '$offset': 0,
                                                 '$order': ':id'
                                             },
                                             timeout=60)
            self.assertEqual(count, 4)
            self.assertEqual(len(files), 1)

            raw_file = os.path.join(tmp_dir,
                                    'ny_brfss_health_indicators_raw.csv')
            self.assertTrue(os.path.exists(raw_file))
            raw_df = pd.read_csv(raw_file)
            self.assertEqual(len(raw_df), 4)
            self.assertIn('health_indicator_short_name', raw_df.columns)
            self.assertIn('region_county', raw_df.columns)
            self.assertIn('unadjusted_rate', raw_df.columns)


if __name__ == '__main__':
    unittest.main()

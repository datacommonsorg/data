# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Unit tests for download_script.py."""

import json
import os
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch
import pandas as pd

_SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))
if _SCRIPT_PATH not in sys.path:
    sys.path.append(_SCRIPT_PATH)

import download_script


class DownloadScriptTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        download_script._FLAGS.mark_as_parsed()

    def test_sanitize_url_redacts_api_key(self):
        raw_url = (
            'https://loadqa.ndapapi.com/v1/openapi?API_Key=secret123&ind=I7208_5&pageno=1'
        )
        sanitized = download_script._sanitize_url(raw_url)
        self.assertNotIn('secret123', sanitized)
        self.assertIn('API_Key=REDACTED', sanitized)
        self.assertIn('ind=I7208_5', sanitized)

    @patch('download_script.storage.Client')
    def test_load_config_gcs(self, mock_storage_client):
        mock_blob = Mock()
        mock_blob.download_as_text.return_value = '{"datasets": []}'
        mock_bucket = Mock()
        mock_bucket.blob.return_value = mock_blob
        mock_client_instance = Mock()
        mock_client_instance.bucket.return_value = mock_bucket
        mock_storage_client.return_value = mock_client_instance

        config = download_script.load_config(
            'gs://fake_bucket/india_ndap/config.json')
        self.assertEqual(config, {'datasets': []})
        mock_client_instance.bucket.assert_called_once_with('fake_bucket')
        mock_bucket.blob.assert_called_once_with('india_ndap/config.json')

    @patch('download_script.file_util.file_load_py_dict')
    def test_load_config_local(self, mock_file_load):
        mock_file_load.return_value = {'datasets': []}
        config = download_script.load_config('/tmp/fake_config.json')
        self.assertEqual(config, {'datasets': []})
        mock_file_load.assert_called_once_with('/tmp/fake_config.json')

    def test_normalize_datasets_config_top_level_urls(self):
        config = {
            'state_population_url': 'https://example.com/7208',
            'state_urban_population_url': 'https://example.com/7209',
        }
        datasets = download_script.normalize_datasets_config(config)
        self.assertEqual(len(datasets), 2)
        self.assertEqual(datasets[0]['name'], 'state_population')
        self.assertEqual(
            datasets[0]['value_column'],
            'Projected Population (UOM:Number), Scaling Factor:1000',
        )
        self.assertEqual(datasets[1]['name'], 'state_urban_population')
        self.assertEqual(
            datasets[1]['value_column'],
            'Projected Urban Population (UOM:Number), Scaling Factor:1000',
        )

    @patch('download_script._retry_method')
    def test_download_dataset_paginates_and_resolves_headers(self, mock_retry):
        page1 = Mock()
        page1.json.return_value = {
            'Headers': {
                'Items': [
                    {
                        'ID': 'D7208_3',
                        'DisplayName': 'Gender',
                        'indicator_dimension': 'Dimension',
                    },
                    {
                        'ID': 'I7208_4',
                        'DisplayName': 'Projected Population',
                        'indicator_dimension': 'Indicator',
                    },
                ]
            },
            'Data': [
                {
                    'Country': 'India',
                    'StateName': 'Andaman And Nicobar Islands',
                    'Year': 'Calendar Year (Jan - Dec), 2026',
                    'D7208_3': 'Female',
                    'I7208_4': {
                        'TotalPopulationWeight': 193
                    },
                },
                {
                    'Country': 'India',
                    'StateName': 'Andaman And Nicobar Islands',
                    'Year': 'Calendar Year (Jan - Dec), 2026',
                    'D7208_3': 'Male',
                    'I7208_4': {
                        'TotalPopulationWeight': 214
                    },
                },
            ],
        }
        page2 = Mock()
        page2.json.return_value = {'Data': []}
        mock_retry.side_effect = [page1, page2]

        dataset_cfg = {
            'name':
                'state_population',
            'url':
                'https://loadqa.ndapapi.com/v1/openapi?API_Key=secret&ind=I7208_4',
        }
        rows = download_script.download_dataset(dataset_cfg)
        self.assertEqual(
            rows,
            [
                (
                    'India',
                    'Andaman And Nicobar Islands',
                    'Calendar Year (Jan - Dec), 2026',
                    'Female',
                    193,
                ),
                (
                    'India',
                    'Andaman And Nicobar Islands',
                    'Calendar Year (Jan - Dec), 2026',
                    'Male',
                    214,
                ),
            ],
        )
        self.assertEqual(mock_retry.call_count, 2)

    @patch('download_script._retry_method')
    def test_download_dataset_stops_on_duplicate_page(self, mock_retry):
        page_payload = {
            'Data': [{
                'Country': 'India',
                'StateName': 'Goa',
                'Year': 'Calendar Year (Jan - Dec), 2026',
                'D7209_3': 'Female',
                'I7209_4': {
                    'avg': 623
                },
            }]
        }
        resp1 = Mock()
        resp1.json.return_value = page_payload
        resp2 = Mock()
        resp2.json.return_value = page_payload
        mock_retry.side_effect = [resp1, resp2]

        dataset_cfg = {
            'name': 'state_urban_population',
            'url': 'https://loadqa.ndapapi.com/v1/openapi?API_Key=secret',
        }
        rows = download_script.download_dataset(dataset_cfg)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0], (
            'India',
            'Goa',
            'Calendar Year (Jan - Dec), 2026',
            'Female',
            623,
        ))

    @patch('download_script._retry_method')
    def test_download_dataset_raises_on_http_failure(self, mock_retry):
        mock_retry.return_value = None
        dataset_cfg = {
            'name': 'state_population',
            'url': 'https://loadqa.ndapapi.com/v1/openapi?API_Key=secret',
        }
        with self.assertRaises(RuntimeError):
            download_script.download_dataset(dataset_cfg)

    @patch('download_script._retry_method')
    def test_download_dataset_raises_on_invalid_json(self, mock_retry):
        bad_resp = Mock()
        bad_resp.json.side_effect = json.JSONDecodeError(
            'Expecting value', '', 0)
        mock_retry.return_value = bad_resp
        dataset_cfg = {
            'name': 'state_population',
            'url': 'https://loadqa.ndapapi.com/v1/openapi?API_Key=secret',
        }
        with self.assertRaises(RuntimeError):
            download_script.download_dataset(dataset_cfg)

    def test_save_dataset_writes_expected_csv_atomically(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            out_csv = os.path.join(tmp_dir, 'india_state_population_input.csv')
            rows = [
                (
                    'India',
                    'Andaman And Nicobar Islands',
                    'Calendar Year (Jan - Dec), 2026',
                    'Female',
                    193,
                ),
            ]
            dataset_cfg = {
                'name':
                    'state_population',
                'output_file':
                    out_csv,
                'value_column':
                    'Projected Population (UOM:Number), Scaling Factor:1000',
            }
            saved_path = download_script.save_dataset(rows, dataset_cfg)
            self.assertEqual(saved_path, out_csv)
            df = pd.read_csv(out_csv)
            self.assertEqual(
                list(df.columns),
                [
                    'Country',
                    'State',
                    'Year',
                    'Gender',
                    'Projected Population (UOM:Number), Scaling Factor:1000',
                ],
            )
            self.assertEqual(len(df), 1)
            self.assertEqual(df.iloc[0]['State'], 'Andaman And Nicobar Islands')
            self.assertEqual(
                df.iloc[0]
                ['Projected Population (UOM:Number), Scaling Factor:1000'],
                193,
            )

    def test_save_dataset_raises_on_empty_rows(self):
        with self.assertRaises(RuntimeError):
            download_script.save_dataset([], {'name': 'state_population'})


if __name__ == '__main__':
    unittest.main()

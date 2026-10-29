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
import traceback
import unittest
from unittest.mock import Mock, patch

from absl import logging as absl_logging
import pandas as pd
import requests

_SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))
if _SCRIPT_PATH not in sys.path:
    sys.path.append(_SCRIPT_PATH)

import download_script


class DownloadScriptTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        download_script._FLAGS.mark_as_parsed()
        absl_logging.set_verbosity(absl_logging.INFO)

    def _assert_no_secret_in_exception(self, exc: BaseException,
                                       secret: str) -> None:
        self.assertNotIn(secret, str(exc))
        self.assertIsNone(exc.__cause__)
        self.assertIsNone(exc.__context__)
        formatted_tb = ''.join(
            traceback.format_exception(type(exc), exc, exc.__traceback__))
        self.assertNotIn(secret, formatted_tb)

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

    @patch('download_script.storage.Client')
    def test_load_config_rejects_malformed_gcs_uris(self, mock_storage_client):
        invalid_paths = [
            '',
            '   ',
            'gs://',
            'gs://bucket_only',
            'gs://bucket_only/',
            'gs:///missing_bucket.json',
            'gs://fake_bucket/trailing_prefix/',
        ]
        for bad_path in invalid_paths:
            with self.subTest(path=bad_path):
                with self.assertRaises(ValueError):
                    download_script.load_config(bad_path)
        mock_storage_client.assert_not_called()

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

    def test_normalize_datasets_config_rejects_missing_dataset_urls(self):
        with self.assertRaisesRegex(ValueError,
                                    'state_urban_population_url.*7209'):
            download_script.normalize_datasets_config(
                {'state_population_url': 'https://example.com/7208'})

        with self.assertRaisesRegex(ValueError, 'state_population_url.*7208'):
            download_script.normalize_datasets_config(
                {'state_urban_population_url': 'https://example.com/7209'})

        with self.assertRaisesRegex(ValueError,
                                    'state_population_url.*7208.*7209'):
            download_script.normalize_datasets_config({})

    @patch('download_script.requests.Session')
    def test_download_dataset_paginates_and_resolves_headers(
            self, mock_session_cls):
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
        mock_session = Mock()
        mock_session.get.side_effect = [page1, page2]
        mock_session_cls.return_value = mock_session

        secret = 'super_secret_token_123'
        dataset_cfg = {
            'name':
                'state_population',
            'url':
                f'https://loadqa.ndapapi.com/v1/openapi?API_Key={secret}&ind=I7208_4',
        }
        with self.assertLogs(level='INFO') as log_ctx:
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
        mock_session_cls.assert_called_once_with()
        self.assertEqual(mock_session.get.call_count, 2)
        for call in mock_session.get.call_args_list:
            self.assertEqual(call.kwargs.get('stream'), False)
            self.assertEqual(call.kwargs.get('timeout'), 30)
        mock_session.close.assert_called_once_with()

        combined_logs = '\n'.join(log_ctx.output)
        self.assertNotIn(secret, combined_logs)
        self.assertIn('API_Key=REDACTED', combined_logs)

    @patch('download_script.requests.Session')
    def test_download_dataset_stops_on_duplicate_page(self, mock_session_cls):
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
        mock_session = Mock()
        mock_session.get.side_effect = [resp1, resp2]
        mock_session_cls.return_value = mock_session

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
        mock_session.close.assert_called_once_with()

    @patch('download_script.time.sleep')
    @patch('download_script.requests.Session')
    def test_download_dataset_raises_on_http_failure(self, mock_session_cls,
                                                     mock_sleep):
        secret = 'ndap_secret_key_999'
        raw_url = (
            f'https://loadqa.ndapapi.com/v1/openapi?API_Key={secret}&pageno=1')
        err_response = requests.Response()
        err_response.status_code = 503
        http_err = requests.exceptions.HTTPError(
            f'503 Server Error: Service Unavailable for url: {raw_url}',
            response=err_response,
        )

        failing_resp = Mock()
        failing_resp.raise_for_status.side_effect = http_err
        mock_session = Mock()
        mock_session.get.return_value = failing_resp
        mock_session_cls.return_value = mock_session

        dataset_cfg = {
            'name': 'state_population',
            'url': f'https://loadqa.ndapapi.com/v1/openapi?API_Key={secret}',
        }
        with self.assertLogs(level='INFO') as log_ctx:
            with self.assertRaises(RuntimeError) as err_ctx:
                download_script.download_dataset(dataset_cfg)

        self.assertEqual(mock_session.get.call_count, 3)
        self.assertEqual(mock_sleep.call_count, 2)
        mock_session.close.assert_called_once_with()

        self.assertIn('API_Key=REDACTED', str(err_ctx.exception))
        self.assertIn('HTTPError (HTTP 503)', str(err_ctx.exception))
        self._assert_no_secret_in_exception(err_ctx.exception, secret)
        self.assertNotIn(secret, '\n'.join(log_ctx.output))

    @patch('download_script.time.sleep')
    @patch('download_script.requests.Session')
    def test_download_dataset_fails_fast_on_permanent_4xx_without_leaking_key(
            self, mock_session_cls, mock_sleep):
        secret = 'ndap_secret_401'
        raw_url = (
            f'https://loadqa.ndapapi.com/v1/openapi?API_Key={secret}&pageno=1')
        err_response = requests.Response()
        err_response.status_code = 401
        http_err = requests.exceptions.HTTPError(
            f'401 Client Error: Unauthorized for url: {raw_url}',
            response=err_response,
        )

        failing_resp = Mock()
        failing_resp.raise_for_status.side_effect = http_err
        mock_session = Mock()
        mock_session.get.return_value = failing_resp
        mock_session_cls.return_value = mock_session

        dataset_cfg = {
            'name': 'state_population',
            'url': f'https://loadqa.ndapapi.com/v1/openapi?API_Key={secret}',
        }
        with self.assertRaises(RuntimeError) as err_ctx:
            download_script.download_dataset(dataset_cfg)

        self.assertEqual(mock_session.get.call_count, 1)
        mock_sleep.assert_not_called()
        self.assertIn('HTTPError (HTTP 401)', str(err_ctx.exception))
        self._assert_no_secret_in_exception(err_ctx.exception, secret)

    @patch('download_script.time.sleep')
    @patch('download_script.requests.Session')
    def test_download_dataset_retries_transient_connection_error_and_recovers(
            self, mock_session_cls, mock_sleep):
        secret = 'ndap_secret_conn'
        conn_err = requests.exceptions.ConnectionError(
            f'Max retries exceeded with url: /v1/openapi?API_Key={secret}&pageno=1'
        )
        ok_page1 = Mock()
        ok_page1.json.return_value = {
            'Data': [{
                'Country': 'India',
                'StateName': 'Goa',
                'Year': 'Calendar Year (Jan - Dec), 2026',
                'D7208_3': 'Female',
                'I7208_4': {
                    'TotalPopulationWeight': 100
                },
            }]
        }
        empty_page2 = Mock()
        empty_page2.json.return_value = {'Data': []}

        mock_session = Mock()
        mock_session.get.side_effect = [conn_err, ok_page1, empty_page2]
        mock_session_cls.return_value = mock_session

        dataset_cfg = {
            'name': 'state_population',
            'url': f'https://loadqa.ndapapi.com/v1/openapi?API_Key={secret}',
        }
        with self.assertLogs(level='INFO') as log_ctx:
            rows = download_script.download_dataset(dataset_cfg)

        self.assertEqual(len(rows), 1)
        mock_sleep.assert_called_once_with(5.0)
        self.assertNotIn(secret, '\n'.join(log_ctx.output))

    @patch('download_script.time.sleep')
    @patch('download_script.requests.Session')
    def test_download_dataset_retries_body_read_request_exception(
            self, mock_session_cls, mock_sleep):
        secret = 'ndap_secret_stream'
        bad_resp = Mock()
        bad_resp.json.side_effect = requests.exceptions.ChunkedEncodingError(
            f'Connection broken while reading /v1/openapi?API_Key={secret}')
        mock_session = Mock()
        mock_session.get.return_value = bad_resp
        mock_session_cls.return_value = mock_session

        dataset_cfg = {
            'name': 'state_population',
            'url': f'https://loadqa.ndapapi.com/v1/openapi?API_Key={secret}',
        }
        with self.assertRaises(RuntimeError) as err_ctx:
            download_script.download_dataset(dataset_cfg)

        self.assertEqual(mock_session.get.call_count, 3)
        self.assertEqual(mock_sleep.call_count, 2)
        self._assert_no_secret_in_exception(err_ctx.exception, secret)

    @patch('download_script.requests.Session')
    def test_download_dataset_raises_on_invalid_json(self, mock_session_cls):
        secret = 'ndap_secret_json'
        bad_resp = Mock()
        bad_resp.json.side_effect = json.JSONDecodeError(
            'Expecting value', '', 0)
        mock_session = Mock()
        mock_session.get.return_value = bad_resp
        mock_session_cls.return_value = mock_session

        dataset_cfg = {
            'name': 'state_population',
            'url': f'https://loadqa.ndapapi.com/v1/openapi?API_Key={secret}',
        }
        with self.assertRaises(RuntimeError) as err_ctx:
            download_script.download_dataset(dataset_cfg)

        self.assertEqual(mock_session.get.call_count, 1)
        self.assertIn('Failed to parse JSON', str(err_ctx.exception))
        self.assertIn('API_Key=REDACTED', str(err_ctx.exception))
        self._assert_no_secret_in_exception(err_ctx.exception, secret)

    def test_download_dataset_reuses_caller_session_without_closing(self):
        empty_page = Mock()
        empty_page.json.return_value = {'Data': []}
        caller_session = Mock()
        caller_session.get.return_value = empty_page

        dataset_cfg = {
            'name': 'state_population',
            'url': 'https://loadqa.ndapapi.com/v1/openapi?API_Key=secret',
        }
        rows = download_script.download_dataset(dataset_cfg,
                                                session=caller_session)
        self.assertEqual(rows, [])
        caller_session.get.assert_called_once()
        caller_session.close.assert_not_called()

    def test_extract_indicator_value_validates_scalars(self):
        self.assertEqual(
            download_script._extract_indicator_value(
                {'TotalPopulationWeight': 193}),
            193,
        )
        self.assertEqual(
            download_script._extract_indicator_value({'avg': 623.0}),
            623,
        )
        self.assertEqual(
            download_script._extract_indicator_value({'value': '193.5'}),
            193.5,
        )
        self.assertEqual(download_script._extract_indicator_value(0), 0)

        for bad_val in (
                None,
            {},
            {
                'TotalPopulationWeight': None
            },
            {
                'RenamedWeightKey': 193
            },
            {
                'value': {}
            },
                True,
                False,
            [193],
                '',
                '   ',
                'N/A',
                float('nan'),
        ):
            with self.subTest(bad_val=bad_val):
                self.assertIsNone(
                    download_script._extract_indicator_value(bad_val))

    def test_download_dataset_rejects_null_nested_value_and_empty_dimensions(
            self):
        invalid_records = [
            {
                'Country': 'India',
                'StateName': 'Goa',
                'Year': 'Calendar Year (Jan - Dec), 2026',
                'D7208_3': 'Female',
                'I7208_4': {
                    'TotalPopulationWeight': None
                },
            },
            {
                'Country': 'India',
                'StateName': 'Goa',
                'Year': 'Calendar Year (Jan - Dec), 2026',
                'D7208_3': 'Female',
                'I7208_4': {
                    'UnexpectedKey': 193
                },
            },
            {
                'Country': 'India',
                'StateName': '   ',
                'Year': 'Calendar Year (Jan - Dec), 2026',
                'D7208_3': 'Female',
                'I7208_4': {
                    'TotalPopulationWeight': 193
                },
            },
            {
                'Country': 'India',
                'StateName': 'Goa',
                'Year': 'Calendar Year (Jan - Dec), 2026',
                'D7208_3': '',
                'I7208_4': {
                    'TotalPopulationWeight': 193
                },
            },
        ]
        dataset_cfg = {
            'name': 'state_population',
            'url': 'https://loadqa.ndapapi.com/v1/openapi?API_Key=secret',
            'gender_key': 'D7208_3',
            'value_key': 'I7208_4',
        }
        for bad_rec in invalid_records:
            with self.subTest(bad_rec=bad_rec):
                page1 = Mock()
                page1.json.return_value = {'Data': [bad_rec]}
                caller_session = Mock()
                caller_session.get.return_value = page1
                with self.assertRaises(RuntimeError):
                    download_script.download_dataset(dataset_cfg,
                                                     session=caller_session)

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

    @patch('download_script.os.replace', side_effect=OSError('replace failed'))
    def test_save_dataset_cleans_up_temp_file_on_failure(self, _):
        with tempfile.TemporaryDirectory() as tmp_dir:
            out_csv = os.path.join(tmp_dir, 'india_state_population_input.csv')
            rows = [('India', 'Goa', 'Calendar Year (Jan - Dec), 2026',
                     'Female', 100)]
            dataset_cfg = {
                'name': 'state_population',
                'output_file': out_csv,
            }
            with self.assertRaises(OSError):
                download_script.save_dataset(rows, dataset_cfg)
            self.assertEqual(os.listdir(tmp_dir), [])

    def test_save_dataset_raises_on_empty_rows(self):
        with self.assertRaises(RuntimeError):
            download_script.save_dataset([], {'name': 'state_population'})


if __name__ == '__main__':
    unittest.main()

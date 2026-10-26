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
"""Unit tests for Japan Census download_script.py."""

import csv
import os
import sys
import tempfile
import unittest
from unittest import mock

# Ensure repository root and module directory are in sys.path for local and root-level test runs
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.abspath(os.path.join(_SCRIPT_DIR, '../..'))
for _p in (_SCRIPT_DIR, _REPO_ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import download_script


class DownloadScriptTest(unittest.TestCase):

    def setUp(self):
        super().setUp()
        self.sample_api_response = {
            'GET_STATS': {
                'RESULT': {
                    'status': '0',
                    'errorMsg': 'Success.',
                },
                'STATISTICAL_DATA': {
                    'CLASS_INF': {
                        'CLASS_OBJ': [
                            {
                                '@id': 'indicator',
                                'CLASS': {
                                    '@code': '0301010000020020010',
                                    '@name': 'Unemployment rate (Both sexes)',
                                },
                            },
                            {
                                '@id': 'unit',
                                'CLASS': {
                                    '@code': '001',
                                    '$': '%',
                                },
                            },
                            {
                                '@id': 'regionCode',
                                'CLASS': {
                                    '@code': '00000',
                                    '@name': 'Japan',
                                },
                            },
                            {
                                '@id':
                                    'time',
                                'CLASS': [
                                    {
                                        '@code': '1953CY00',
                                        '@name': '1953'
                                    },
                                    {
                                        '@code': '1954CY00',
                                        '@name': '1954'
                                    },
                                ],
                            },
                        ]
                    },
                    'DATA_INF': {
                        'DATA_OBJ': [
                            {
                                'VALUE': {
                                    '@indicator': '0301010000020020010',
                                    '@unit': '001',
                                    '@stat': '00200531',
                                    '@regionCode': '00000',
                                    '@time': '1953CY00',
                                    '@cycle': '3',
                                    '@regionRank': '2',
                                    '@isSeasonal': '1',
                                    '@isProvisional': '0',
                                    '$': '1.9',
                                }
                            },
                            {
                                'VALUE': {
                                    '@indicator': '0301010000020020010',
                                    '@unit': '001',
                                    '@stat': '00200531',
                                    '@regionCode': '00000',
                                    '@time': '1954CY00',
                                    '@cycle': '3',
                                    '@regionRank': '2',
                                    '@isSeasonal': '1',
                                    '@isProvisional': '0',
                                    '$': '2.3',
                                }
                            },
                        ]
                    },
                },
            }
        }

    def test_parse_estat_json_response_success(self):
        records = download_script.parse_estat_json_response(
            self.sample_api_response)
        self.assertEqual(len(records), 2)
        self.assertEqual(records[0]['indicatorCd'], '0301010000020020010')
        self.assertEqual(records[0]['indicatorName'],
                         'Unemployment rate (Both sexes)')
        self.assertEqual(records[0]['unitName'], '%')
        self.assertEqual(records[0]['regionCd'], '00000')
        self.assertEqual(records[0]['regionName'], 'Japan')
        self.assertEqual(records[0]['year'], '1953')
        self.assertEqual(records[0]['value'], '1.9')

    def test_parse_estat_json_response_error_raises(self):
        for status in ('400', '100'):
            error_payload = {
                'GET_STATS': {
                    'RESULT': {
                        'status': status,
                        'errorMsg': 'API error or no data.',
                    }
                }
            }
            with self.assertRaises(RuntimeError):
                download_script.parse_estat_json_response(error_payload)

    def test_write_csv_atomically_failure_cleanup(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            target_path = os.path.join(tmp_dir, 'test_output.csv')
            with mock.patch.object(os.path, 'getsize', return_value=0):
                with self.assertRaises(RuntimeError):
                    download_script._write_csv_atomically(
                        target_path, [{
                            'year': '2020'
                        }])
            self.assertFalse(os.path.exists(target_path))
            self.assertEqual(os.listdir(tmp_dir), [])

    @mock.patch.object(download_script, '_request_estat_json')
    def test_download_dataset_empty_error(self, mock_request_json):
        mock_request_json.return_value = {
            'GET_STATS': {
                'RESULT': {
                    'status': '100',
                    'errorMsg': 'No data.',
                }
            }
        }
        with tempfile.TemporaryDirectory() as tmp_dir:
            out_file = os.path.join(tmp_dir, 'jpn_unemploymentrate.csv')
            with self.assertRaises(RuntimeError):
                download_script.download_dataset(
                    output_filepath=out_file,
                    indicators=['0301010000020020010'],
                    regional_ranks=['2'],
                    batch_size=1,
                )

    @mock.patch.object(download_script, '_request_estat_json')
    def test_download_dataset_writes_csv_atomically(self, mock_request_json):
        mock_request_json.return_value = self.sample_api_response
        with tempfile.TemporaryDirectory() as tmp_dir:
            out_file = os.path.join(tmp_dir, 'jpn_unemploymentrate.csv')
            count = download_script.download_dataset(
                output_filepath=out_file,
                indicators=['0301010000020020010'],
                regional_ranks=['2'],
                batch_size=1,
            )
            self.assertEqual(count, 2)
            self.assertTrue(os.path.exists(out_file))
            with open(out_file, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                header = next(reader)
                self.assertEqual(header[:4],
                                 ['year', 'indicatorCd', 'regionCd', 'value'])
                rows = list(reader)
            self.assertEqual(len(rows), 2)
            self.assertEqual(rows[1][0], '1954')
            self.assertEqual(rows[1][3], '2.3')


if __name__ == '__main__':
    unittest.main()

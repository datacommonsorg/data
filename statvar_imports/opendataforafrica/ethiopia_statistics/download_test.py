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
"""Hermetic unit tests for Ethiopia Statistics download.py."""

import csv
import json
import os
import sys
import tempfile
import unittest
from unittest import mock

_MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.abspath(os.path.join(_MODULE_DIR, '../../..'))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from statvar_imports.opendataforafrica.ethiopia_statistics import download


class DownloadTest(unittest.TestCase):

    def test_format_number(self):
        self.assertEqual(download._format_number(None), '')
        self.assertEqual(download._format_number(float('nan')), '')
        self.assertEqual(download._format_number(49.0), '49')
        self.assertEqual(download._format_number(73750932.0), '73750932')
        self.assertEqual(download._format_number(13.5), '13.5')
        self.assertEqual(download._format_number(0.0), '0')

    def test_extract_annual_values_valid_and_errors(self):
        series = {
            'tsKey': 1,
            'frequency': 'A',
            'startDate': '2000-01-01T00:00:00',
            'endDate': '2002-01-01T00:00:00',
            'values': [10.0, None, 12.5],
        }
        self.assertEqual(download._extract_annual_values(series), {
            2000: 10.0,
            2002: 12.5
        })

        with self.assertRaises(ValueError):
            download._extract_annual_values({**series, 'frequency': 'M'})

        with self.assertRaises(ValueError):
            download._extract_annual_values({**series, 'values': [10.0]})

    def test_transform_udghlsf(self):
        series = [
            {
                'region': {
                    'name': 'Ethiopia',
                    'id': 'KN.A1'
                },
                'variable': {
                    'name': 'Regional Population Distribution, Male',
                    'id': 'KN.B2',
                },
                'frequency': 'A',
                'startDate': '2011-01-01T00:00:00',
                'endDate': '2011-01-01T00:00:00',
                'unit': '%',
                'values': [49.0],
            },
            {
                'region': {
                    'name': 'Ethiopia',
                    'id': 'KN.A1'
                },
                'variable': {
                    'name': 'Gross Calories, All',
                    'id': 'KN.B8'
                },
                'frequency': 'A',
                'startDate': '2000-01-01T00:00:00',
                'endDate': '2002-01-01T00:00:00',
                'unit': 'kcal/capita/day',
                'values': [2211.0, None, 2300.0],
            },
        ]
        headers, rows = download.transform_udghlsf(series)
        self.assertEqual(
            headers, ['Region', 'Variable', 'Units', '2000', '2002', '2011'])
        self.assertEqual(rows, [
            [
                'Ethiopia',
                'Regional Population Distribution, Male',
                '%',
                '',
                '',
                '49',
            ],
            [
                'Ethiopia',
                'Gross Calories, All',
                'kcal/capita/day',
                '2211',
                '2300',
                '',
            ],
        ])

    def test_transform_xtqdbuc(self):
        series = [
            {
                'region': {
                    'name': 'Ethiopia'
                },
                'indicator': {
                    'name': 'Rural population'
                },
                'frequency': 'A',
                'startDate': '2006-01-01T00:00:00',
                'endDate': '2007-01-01T00:00:00',
                'unit': 'thousands',
                'scale': 1000,
                'values': [62895.0, 62012.725],
            },
        ]
        headers, rows = download.transform_xtqdbuc(series)
        self.assertEqual(
            headers, ['Region', 'Indicator', 'Units', 'Scale', '2006', '2007'])
        self.assertEqual(rows, [[
            'Ethiopia',
            'Rural population',
            'thousands',
            'thousands',
            '62.895',
            '62.012725',
        ]])

        with self.assertRaises(ValueError):
            download.transform_xtqdbuc([{**series[0], 'scale': 100}])

    def test_transform_teakvke(self):
        series = [
            {
                'region': {
                    'name': 'Ethiopia'
                },
                'variable': {
                    'name': 'Population, Male'
                },
                'residence': {
                    'name': 'Rural'
                },
                'frequency': 'A',
                'startDate': '2007-01-01T00:00:00',
                'endDate': '2007-01-01T00:00:00',
                'unit': 'Persons',
                'values': [31321214.0],
            },
        ]
        headers, rows = download.transform_teakvke(series)
        self.assertEqual(
            headers,
            ['Region', 'Variable', 'Residence', 'mapper', 'Units', '2007'])
        self.assertEqual(rows, [[
            'Ethiopia',
            'Population, Male',
            'Rural',
            'Population, Male Rural',
            'Persons',
            '31321214',
        ]])

    def test_transform_xpcyhcf(self):
        series = [
            {
                'sex': {
                    'name': 'Total'
                },
                'area': {
                    'name': 'Ethiopia'
                },
                'frequency': 'A',
                'startDate': '2022-01-01T00:00:00',
                'endDate': '2022-01-01T00:00:00',
                'values': [105025989.0],
            },
            {
                'sex': {
                    'name': 'Total'
                },
                'area': {
                    'name': 'Tigray'
                },
                'frequency': 'A',
                'startDate': '2022-01-01T00:00:00',
                'endDate': '2022-01-01T00:00:00',
                'values': [5738996.0],
            },
            {
                'sex': {
                    'name': 'Male'
                },
                'area': {
                    'name': 'Ethiopia'
                },
                'frequency': 'A',
                'startDate': '2022-01-01T00:00:00',
                'endDate': '2022-01-01T00:00:00',
                'values': [52648991.0],
            },
            {
                'sex': {
                    'name': 'Male'
                },
                'area': {
                    'name': 'Tigray'
                },
                'frequency': 'A',
                'startDate': '2022-01-01T00:00:00',
                'endDate': '2022-01-01T00:00:00',
                'values': [2834000.0],
            },
        ]
        headers, rows = download.transform_xpcyhcf(series)
        self.assertEqual(headers, ['', 'Ethiopia', 'Tigray'])
        self.assertEqual(rows, [
            ['Total', '105025989', '5738996'],
            ['Male', '52648991', '2834000'],
        ])

        with self.assertRaises(RuntimeError):
            download.transform_xpcyhcf([{
                'sex': {
                    'name': 'Total'
                },
                'area': {
                    'name': 'Ethiopia'
                },
                'frequency': 'A',
                'startDate': '2023-01-01T00:00:00',
                'endDate': '2023-01-01T00:00:00',
                'values': [100.0],
            }])

    def test_transform_yusibcg(self):
        series = [
            {
                'region': {
                    'id': 'KN.A1',
                    'RegionId': 'ET'
                },
                'variable': {
                    'id': 'KN.B30',
                    'unit': '%'
                },
                'wealth-index': {
                    'id': 'KN.E1'
                },
                'age': {
                    'id': 'KN.C5'
                },
                'sex': {
                    'id': 'KN.D3'
                },
                'frequency': 'A',
                'startDate': '2011-01-01T00:00:00',
                'endDate': '2014-01-01T00:00:00',
                'unit': '%',
                'values': [13.5, None, None, 15.0],
            },
        ]
        headers, rows = download.transform_yusibcg(series)
        self.assertEqual(len(headers), 15)
        self.assertEqual(rows, [
            [
                'KN.A1', 'KN.A1', 'ET', 'KN.B30', 'KN.B30', '%', 'KN.E1',
                'KN.E1', 'KN.C5', 'KN.C5', 'KN.D3', 'KN.D3', 'A', '2011', '13.5'
            ],
            [
                'KN.A1', 'KN.A1', 'ET', 'KN.B30', 'KN.B30', '%', 'KN.E1',
                'KN.E1', 'KN.C5', 'KN.C5', 'KN.D3', 'KN.D3', 'A', '2014', '15'
            ],
        ])

    @mock.patch.object(download.download_util, 'request_url')
    def test_fetch_dataset_raw_pagination_and_write(self, mock_request_url):
        meta_resp = {
            'id':
                'udghlsf',
            'dimensions': [
                {
                    'id': 'region',
                    'name': 'Region'
                },
                {
                    'id': 'variable',
                    'name': 'Variable'
                },
            ],
        }
        reg_resp = {
            'items': [{
                'key': 1,
                'name': 'Ethiopia',
                'hasData': True
            }],
        }
        var_resp = {
            'items': [
                {
                    'key': 10,
                    'name': 'Regional Population Distribution, Male',
                    'hasData': True,
                },
                {
                    'key': 11,
                    'name': 'Regional Population Distribution, Female',
                    'hasData': True,
                },
            ],
        }
        page1 = {
            'continuationToken':
                'tok-page-2',
            'data': [{
                'region': {
                    'name': 'Ethiopia',
                    'id': 'KN.A1'
                },
                'variable': {
                    'name': 'Regional Population Distribution, Male',
                    'id': 'KN.B2',
                },
                'frequency': 'A',
                'startDate': '2011-01-01T00:00:00',
                'endDate': '2011-01-01T00:00:00',
                'unit': '%',
                'values': [49.0],
            }],
        }
        page2 = {
            'continuationToken':
                None,
            'data': [{
                'region': {
                    'name': 'Ethiopia',
                    'id': 'KN.A1'
                },
                'variable': {
                    'name': 'Regional Population Distribution, Female',
                    'id': 'KN.B3',
                },
                'frequency': 'A',
                'startDate': '2011-01-01T00:00:00',
                'endDate': '2011-01-01T00:00:00',
                'unit': '%',
                'values': [51.0],
            }],
        }
        mock_request_url.side_effect = [
            meta_resp, reg_resp, var_resp, page1, page2
        ]

        with tempfile.TemporaryDirectory() as tmp_dir:
            raw_dir = os.path.join(tmp_dir, 'raw_files')
            out_dir = os.path.join(tmp_dir, 'input_files')
            outputs = download.download_all(
                dataset_ids=['udghlsf'],
                raw_dir=raw_dir,
                output_dir=out_dir,
            )

            self.assertIn('udghlsf', outputs)
            raw_path = os.path.join(raw_dir, 'udghlsf_raw.json')
            self.assertTrue(os.path.exists(raw_path))
            with open(raw_path, 'r', encoding='utf-8') as f:
                saved_raw = json.load(f)
            self.assertEqual(len(saved_raw['pages']), 2)

            csv_path = outputs['udghlsf']
            with open(csv_path, 'r', encoding='utf-8') as f:
                csv_rows = list(csv.reader(f))
            self.assertEqual(csv_rows, [
                ['Region', 'Variable', 'Units', '2011'],
                [
                    'Ethiopia', 'Regional Population Distribution, Male', '%',
                    '49'
                ],
                [
                    'Ethiopia', 'Regional Population Distribution, Female', '%',
                    '51'
                ],
            ])

        self.assertEqual(mock_request_url.call_count, 5)
        last_call = mock_request_url.call_args_list[-1]
        self.assertEqual(last_call.kwargs['method'], 'GET')
        self.assertEqual(last_call.kwargs['params'],
                         {'continuationToken': 'tok-page-2'})

    @mock.patch.object(download.download_util, 'request_url')
    def test_fetch_filters_xtqdbuc_and_teakvke(self, mock_request_url):
        meta_resp = {
            'dimensions': [
                {
                    'id': 'region',
                    'name': 'Region'
                },
                {
                    'id': 'variable',
                    'name': 'Variable'
                },
                {
                    'id': 'residence',
                    'name': 'Residence'
                },
            ],
        }
        reg_resp = {
            'items': [
                {
                    'key': 1,
                    'name': 'Ethiopia',
                    'level': 0,
                    'hasData': True
                },
                {
                    'key': 2,
                    'name': 'Afar-Region',
                    'level': 1,
                    'hasData': True
                },
                {
                    'key': 3,
                    'name': 'SubWoreda',
                    'level': 2,
                    'hasData': True
                },
            ],
        }
        var_resp = {
            'items': [
                {
                    'key': 10,
                    'name': 'Population, Male',
                    'hasData': True
                },
                {
                    'key': 11,
                    'name': 'Electricity',
                    'hasData': True
                },
            ],
        }
        res_resp = {
            'items': [{
                'key': 20,
                'name': 'Rural',
                'hasData': True
            }],
        }
        data_resp = {
            'continuationToken':
                None,
            'data': [{
                'region': {
                    'name': 'Ethiopia'
                },
                'variable': {
                    'name': 'Population, Male'
                },
                'residence': {
                    'name': 'Rural'
                },
                'frequency': 'A',
                'startDate': '2007-01-01T00:00:00',
                'endDate': '2007-01-01T00:00:00',
                'unit': 'Persons',
                'values': [100.0],
            }],
        }
        mock_request_url.side_effect = [
            meta_resp, reg_resp, var_resp, res_resp, data_resp
        ]

        result = download.fetch_dataset_raw('teakvke')
        self.assertEqual(len(result['series']), 1)
        post_call = mock_request_url.call_args_list[4]
        stub = {
            d['DimensionId']: d['Members']
            for d in post_call.kwargs['params']['Stub']
        }
        self.assertEqual(stub['region'], [1, 2])
        self.assertEqual(stub['variable'], [10])
        self.assertEqual(stub['residence'], [20])

    @mock.patch.object(download.download_util, 'request_url')
    def test_request_json_error_handling(self, mock_request_url):
        mock_request_url.return_value = None
        with self.assertRaises(RuntimeError):
            download._request_json('https://example.org/api')

        mock_request_url.return_value = 'Underlying data is very large.'
        with self.assertRaises(RuntimeError):
            download._request_json('https://example.org/api')

    def test_unsupported_dataset_raises(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            with self.assertRaises(ValueError):
                download.download_and_transform_dataset('unknown_id', tmp_dir,
                                                        tmp_dir)

    def test_extract_annual_values_null_fields_raise_value_error(self):
        base = {
            'tsKey': 42,
            'frequency': 'A',
            'startDate': '2011-01-01T00:00:00',
            'endDate': '2011-01-01T00:00:00',
            'values': [10.0],
        }
        with self.assertRaisesRegex(ValueError, 'tsKey=42'):
            download._extract_annual_values({**base, 'startDate': None})
        with self.assertRaisesRegex(ValueError, 'tsKey=42'):
            download._extract_annual_values({**base, 'endDate': None})
        with self.assertRaisesRegex(ValueError, 'tsKey=42'):
            download._extract_annual_values({**base, 'values': None})
        with self.assertRaisesRegex(ValueError, 'tsKey=42'):
            download._extract_annual_values({**base, 'values': 'bad'})

    def test_transforms_missing_or_null_dimensions_raise_value_error(self):
        common = {
            'tsKey': 99,
            'frequency': 'A',
            'startDate': '2011-01-01T00:00:00',
            'endDate': '2011-01-01T00:00:00',
            'values': [1.0],
        }
        with self.assertRaisesRegex(ValueError, 'udghlsf.*tsKey=99'):
            download.transform_udghlsf([{**common, 'region': None}])
        with self.assertRaisesRegex(ValueError, 'xtqdbuc.*tsKey=99'):
            download.transform_xtqdbuc([{
                **common,
                'region': {
                    'name': 'Ethiopia'
                },
                'indicator': {
                    'name': None
                },
            }])
        with self.assertRaisesRegex(ValueError, 'teakvke.*tsKey=99'):
            download.transform_teakvke([{
                **common,
                'region': {
                    'name': 'Ethiopia'
                },
                'variable': {
                    'name': 'Population, Male'
                },
            }])
        with self.assertRaisesRegex(ValueError, 'xpcyhcf.*tsKey=99'):
            download.transform_xpcyhcf([{**common, 'sex': None}])
        with self.assertRaisesRegex(ValueError, 'yusibcg.*tsKey=99'):
            download.transform_yusibcg([{
                **common,
                'region': {
                    'id': 'KN.A1'
                },
                'variable': {
                    'id': 'KN.B1'
                },
                'wealth-index': None,
                'age': {
                    'id': 'KN.C1'
                },
                'sex': {
                    'id': 'KN.D1'
                },
            }])

    @mock.patch.object(download.download_util, 'request_url')
    def test_fetch_dataset_raw_handles_null_data_pages(self, mock_request_url):
        meta_resp = {'dimensions': [{'id': 'region', 'name': 'Region'}]}
        reg_resp = {'items': [{'key': 1, 'name': 'Ethiopia', 'hasData': True}]}
        page1 = {'continuationToken': 'tok-2', 'data': None}
        page2 = {
            'continuationToken':
                None,
            'data': [{
                'region': {
                    'name': 'Ethiopia'
                },
                'frequency': 'A',
                'startDate': '2011-01-01T00:00:00',
                'endDate': '2011-01-01T00:00:00',
                'values': [10.0],
            }],
        }
        mock_request_url.side_effect = [meta_resp, reg_resp, page1, page2]
        result = download.fetch_dataset_raw('udghlsf')
        self.assertEqual(len(result['series']), 1)

        mock_request_url.side_effect = [
            meta_resp,
            reg_resp,
            {
                'continuationToken': None,
                'data': None
            },
        ]
        with self.assertRaisesRegex(RuntimeError, 'zero data series'):
            download.fetch_dataset_raw('udghlsf')


if __name__ == '__main__':
    unittest.main()

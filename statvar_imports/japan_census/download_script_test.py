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

from statvar_imports.japan_census import download_script


class DownloadScriptTest(unittest.TestCase):

    def test_write_text_atomically_failure_cleanup(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            target_path = os.path.join(tmp_dir, 'test_output.csv')
            with mock.patch.object(os.path, 'getsize', return_value=0):
                with self.assertRaises(RuntimeError):
                    download_script._write_text_atomically(
                        target_path, '"col1","col2"\n')
            self.assertFalse(os.path.exists(target_path))
            self.assertEqual(os.listdir(tmp_dir), [])

    @mock.patch.object(download_script, 'fetch_dbview_csv')
    def test_download_dbview_dataset_writes_raw_csv(self, mock_fetch_dbview):
        mock_fetch_dbview.return_value = '"col1","col2"\n"val1","val2"\n'
        with tempfile.TemporaryDirectory() as tmp_dir:
            out_file = os.path.join(tmp_dir,
                                    'jpn_gender_age_total_population.csv')
            line_count = download_script.download_dbview_dataset(
                output_filepath=out_file,
                sid='0003410380',
                select_filters={'18': {'020'}},
            )
            self.assertEqual(line_count, 2)
            self.assertTrue(os.path.exists(out_file))
            with open(out_file, 'r', encoding='utf-8') as f:
                self.assertEqual(f.read(), '"col1","col2"\n"val1","val2"\n')

    @mock.patch.object(download_script, 'fetch_dashboard_csv')
    @mock.patch.object(download_script, 'fetch_dbview_csv')
    def test_download_all_downloads_all_17_datasets_and_cleans_stale(
        self,
        mock_fetch_dbview,
        mock_fetch_dashboard,
    ):
        mock_fetch_dbview.return_value = '"col1","col2"\n"val1","val2"\n'
        mock_fetch_dashboard.return_value = '"col1","col2"\n"val1","val2"\n'
        with tempfile.TemporaryDirectory() as tmp_dir:
            stale_file = os.path.join(tmp_dir, 'stale.csv')
            with open(stale_file, 'w', encoding='utf-8') as f:
                f.write('stale\n')
            download_script.download_all(output_dir=tmp_dir, max_workers=1)
            self.assertFalse(os.path.exists(stale_file))
            self.assertEqual(set(os.listdir(tmp_dir)),
                             set(download_script.DBVIEW_CONFIGS.keys()))
            self.assertEqual(len(os.listdir(tmp_dir)), 17)

    @mock.patch.object(download_script, '_create_retry_session')
    def test_fetch_dbview_csv_success_and_filters(self, mock_create_session):
        mock_session = mock.MagicMock()
        mock_create_session.return_value = mock_session

        init_resp = mock.MagicMock()
        dl_page_resp = mock.MagicMock()
        mock_session.get.side_effect = [init_resp, dl_page_resp]

        model_payload = {
            'annotationFlg': '0',
            'rowNoDataDispFlg': '0',
            'colNoDataDispFlg': '0',
            'commaType': '2',
            'replaceSpChars': '3',
            'graphAxis': '',
            'graphBasis': '',
            'graphSort': '',
            'graphTitle': '',
            'graphType': '',
            'inputNumberOfCols': '10',
            'inputNumberOfRows': '10',
            'movementId': '',
            'leftMoveFlg': '0',
            'rightMoveFlg': '0',
            'underMoveFlg': '0',
            'upMoveFlg': '0',
            'matters': {
                '0': {
                    'matterId': 18,
                    'position': 'col',
                    'positionNum': 1,
                    'tableName': 'tab',
                    'dispTableName': '表章項目',
                    'matterName': '表章項目',
                    'initDisp': 1,
                    'listData': {
                        '0': {
                            'code': '020',
                            'name': '人口【人】',
                            'selected': True,
                        },
                        '1': {
                            'code': '040',
                            'name': '人口性比',
                            'selected': True,
                        },
                    },
                },
                '1': {
                    'matterId': 1,
                    'position': 'top',
                    'positionNum': 1,
                    'tableName': 'cat01',
                    'dispTableName': '年齢',
                    'matterName': '年齢',
                    'initDisp': 1,
                    'listData': {
                        '0': {
                            'code': '100',
                            'name': '総数',
                            'selected': True,
                        },
                        '1': {
                            'code': '999',
                            'name': '不詳',
                            'selected': True,
                        },
                    },
                },
            },
        }
        model_resp = mock.MagicMock()
        model_resp.json.return_value = model_payload
        res_resp = mock.MagicMock()
        create_resp = mock.MagicMock()
        create_resp.json.return_value = [{
            'filePath': '/tmp/path',
            'fileList': [{
                'fileNo': '0',
                'fileName': '0003410380.csv',
            }],
        }]
        run_resp = mock.MagicMock()
        run_resp.content = '"col1","col2"\n"100","200"\n'.encode('utf-8')
        mock_session.post.side_effect = [
            model_resp,
            res_resp,
            create_resp,
            run_resp,
        ]

        csv_text = download_script.fetch_dbview_csv(
            sid='0003410380',
            select_filters={'18': {'020'}},
            exclude_filters={'1': {'999'}},
            exclude_suffixes={'1': ('000010',)},
            pos_overrides={'1': ('row', '1')},
        )
        self.assertEqual(csv_text, '"col1","col2"\n"100","200"\n')
        self.assertEqual(mock_session.get.call_count, 2)
        self.assertEqual(mock_session.post.call_count, 4)
        self.assertEqual(mock_session.close.call_count, 1)

    @mock.patch.object(download_script.time, 'sleep')
    @mock.patch.object(download_script, '_create_retry_session')
    def test_fetch_dbview_csv_retries_and_raises_on_error(
        self,
        mock_create_session,
        mock_sleep,
    ):
        mock_session = mock.MagicMock()
        mock_create_session.return_value = mock_session
        mock_session.get.side_effect = RuntimeError('connection timeout')

        with self.assertRaises(RuntimeError):
            download_script.fetch_dbview_csv(sid='0003410380')
        self.assertEqual(mock_session.get.call_count, 4)
        self.assertEqual(mock_sleep.call_count, 3)
        self.assertEqual(mock_session.close.call_count, 4)

    @mock.patch.object(download_script.time, 'sleep')
    @mock.patch.object(download_script, '_create_retry_session')
    def test_fetch_dbview_csv_fails_fast_on_404(
        self,
        mock_create_session,
        mock_sleep,
    ):
        mock_session = mock.MagicMock()
        mock_create_session.return_value = mock_session
        bad_resp = mock.MagicMock(status_code=404)
        http_err = download_script.requests.HTTPError(
            '404 Not Found',
            response=bad_resp,
        )
        mock_session.get.side_effect = http_err

        with self.assertRaises(RuntimeError):
            download_script.fetch_dbview_csv(sid='0003410380')
        self.assertEqual(mock_session.get.call_count, 1)
        self.assertEqual(mock_sleep.call_count, 0)
        self.assertEqual(mock_session.close.call_count, 1)

    @mock.patch.object(download_script.time, 'sleep')
    @mock.patch.object(download_script, '_create_retry_session')
    def test_fetch_dashboard_csv_success_and_error(
        self,
        mock_create_session,
        mock_sleep,
    ):
        mock_session = mock.MagicMock()
        mock_create_session.return_value = mock_session

        ok_resp = mock.MagicMock()
        ok_resp.content = '\ufeff"時点","地域コード"\n"2025年","00000"\n'.encode(
            'utf-8')
        mock_session.get.return_value = ok_resp

        params = {
            'IndicatorCode': '0301010000020020010',
            'RegionCode': '00000',
            'Cycle': '3',
        }
        csv_text = download_script.fetch_dashboard_csv(params)
        self.assertEqual(csv_text, '"時点","地域コード"\n"2025年","00000"\n')

        empty_resp = mock.MagicMock()
        empty_resp.content = b'   '
        mock_session.get.return_value = empty_resp
        with self.assertRaises(RuntimeError):
            download_script.fetch_dashboard_csv(params)
        self.assertEqual(mock_sleep.call_count, 3)
        self.assertEqual(mock_session.close.call_count, 5)


if __name__ == '__main__':
    unittest.main()

# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the 'License');
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#         https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an 'AS IS' BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Unit tests for download_script.py."""

import json
import os
import sys
import tempfile
import unittest
from unittest import mock

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.abspath(os.path.join(_SCRIPT_DIR, '..', '..'))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from statvar_imports.israel_census import download_script  # pylint: disable=wrong-import-position


class DownloadScriptTest(unittest.TestCase):

    def test_fetch_cbs_series_raw_csv_writes_unmodified_bytes(self):
        mock_session = mock.MagicMock()
        resp = mock.MagicMock()
        raw_csv = (
            b'id,time_name,unit_name,path_level4_name,path_name_id_name,obs_time_period,obs_value\n'
            b'3700,Year,Thousands,At End of Period,Total,2024-01,10065.5\n'
            b'3701,Year,Thousands,At End of Period,Jews,2024-01,7212.9\n'
            b'3702,Year,Thousands,At End of Period,Non-Jews,2024-01,2852.6\n'
            b'3703,Year,Thousands,At End of Period,Jews and Others,2024-01,7693.3\n'
            b'3704,Year,Thousands,At End of Period,Arab Population,2024-01,2111.8\n'
        )
        resp.content = raw_csv
        mock_session.get.return_value = resp

        with tempfile.TemporaryDirectory() as tmp_dir:
            dest_csv = os.path.join(tmp_dir, 'cbs_series_2_1_1_1.csv')
            byte_count = download_script.fetch_cbs_series_raw_csv(
                path_id='2,1,1,1',
                dest_path=dest_csv,
                session=mock_session,
                min_annual_rows={},
            )
            self.assertEqual(byte_count, len(raw_csv))
            with open(dest_csv, 'rb') as fp:
                self.assertEqual(fp.read(), raw_csv)

    def test_fetch_cbs_series_raw_csv_fetches_multiple_pages(self):
        mock_session = mock.MagicMock()
        resp_page1 = mock.MagicMock()
        resp_page1.content = (
            b'id,time_name,obs_time_period,obs_value,page_current_page,page_last_page\r\n'
            b'3700,Year,2024-01,10065.5,1,2\r\n'
            b'3701,Year,2024-01,7212.9,1,2\r\n'
            b'3702,Year,2024-01,2852.6,1,2\r\n\r\n')
        resp_page2 = mock.MagicMock()
        resp_page2.content = (
            b'id,time_name,obs_time_period,obs_value,page_current_page,page_last_page\r\n'
            b'3703,Year,2024-01,7693.3,2,2\r\n'
            b'3704,Year,2024-01,2111.8,2,2\r\n\r\n')
        mock_session.get.side_effect = [resp_page1, resp_page2]

        with tempfile.TemporaryDirectory() as tmp_dir:
            dest_csv = os.path.join(tmp_dir, 'cbs_series_2_1_1_1.csv')
            byte_count = download_script.fetch_cbs_series_raw_csv(
                path_id='2,1,1,1',
                dest_path=dest_csv,
                session=mock_session,
                min_unique_series=5,
                min_annual_rows={},
            )
            self.assertEqual(mock_session.get.call_count, 2)
            with open(dest_csv, 'rb') as fp:
                combined = fp.read()
            self.assertEqual(byte_count, len(combined))
            lines = combined.splitlines()
            self.assertEqual(len(lines), 6)
            self.assertTrue(all(line.strip() for line in lines))
            self.assertIn(b'3700,Year,2024-01,10065.5,1,2', combined)
            self.assertIn(b'3704,Year,2024-01,2111.8,2,2', combined)

    def test_fetch_cbs_series_raw_csv_stops_on_stalled_pagination(self):
        mock_session = mock.MagicMock()
        resp_stuck = mock.MagicMock()
        resp_stuck.content = (
            b'id,time_name,obs_time_period,obs_value,page_current_page,page_last_page\n'
            b'3700,Year,2024-01,10065.5,1,2\n')
        mock_session.get.return_value = resp_stuck

        with tempfile.TemporaryDirectory() as tmp_dir:
            dest_csv = os.path.join(tmp_dir, 'cbs_series_2_1_1_1.csv')
            with self.assertRaises(RuntimeError):
                download_script.fetch_cbs_series_raw_csv(
                    path_id='2,1,1,1',
                    dest_path=dest_csv,
                    session=mock_session,
                    min_unique_series=1,
                    min_annual_rows={},
                )
            # 3 attempts x 2 requests (page 1 ok, page 2 returns page_current_page=1 -> stalled)
            self.assertEqual(mock_session.get.call_count, 6)

    def test_fetch_cbs_series_raw_csv_rejects_zero_page_last(self):
        mock_session = mock.MagicMock()
        resp_zero = mock.MagicMock()
        resp_zero.content = (
            b'id,time_name,obs_time_period,obs_value,page_current_page,page_last_page\n'
            b'3700,Year,2024-01,10065.5,1,0\n')
        mock_session.get.return_value = resp_zero

        with tempfile.TemporaryDirectory() as tmp_dir:
            dest_csv = os.path.join(tmp_dir, 'cbs_series_2_1_1_1.csv')
            with self.assertRaises(RuntimeError):
                download_script.fetch_cbs_series_raw_csv(
                    path_id='2,1,1,1',
                    dest_path=dest_csv,
                    session=mock_session,
                    min_unique_series=1,
                    min_annual_rows={},
                )
            self.assertEqual(mock_session.get.call_count, 3)

    def test_fetch_cbs_series_raw_csv_retries_on_page2_timeout(self):
        mock_session = mock.MagicMock()
        resp_page1 = mock.MagicMock()
        resp_page1.content = (
            b'id,time_name,obs_time_period,obs_value,page_current_page,page_last_page\n'
            b'3700,Year,2024-01,10065.5,1,2\n')
        resp_page2 = mock.MagicMock()
        resp_page2.content = (
            b'id,time_name,obs_time_period,obs_value,page_current_page,page_last_page\n'
            b'3701,Year,2024-01,7212.9,2,2\n')
        mock_session.get.side_effect = [
            resp_page1,
            download_script.requests.exceptions.Timeout('page 2 timeout'),
            resp_page1,
            resp_page2,
        ]

        with tempfile.TemporaryDirectory() as tmp_dir:
            dest_csv = os.path.join(tmp_dir, 'cbs_series_2_1_1_1.csv')
            download_script.fetch_cbs_series_raw_csv(
                path_id='2,1,1,1',
                dest_path=dest_csv,
                session=mock_session,
                min_unique_series=1,
                min_annual_rows={},
            )
            self.assertEqual(mock_session.get.call_count, 4)
            with open(dest_csv, 'rb') as fp:
                combined = fp.read()
            self.assertIn(b'3700,Year,2024-01,10065.5,1,2\n', combined)
            self.assertIn(b'3701,Year,2024-01,7212.9,2,2\n', combined)

    def test_fetch_cbs_series_raw_csv_handles_missing_trailing_newline(self):
        mock_session = mock.MagicMock()
        resp_page1 = mock.MagicMock()
        resp_page1.content = (
            b'id,time_name,obs_time_period,obs_value,page_current_page,page_last_page\n'
            b'3700,Year,2024-01,10065.5,1,2')
        resp_page2 = mock.MagicMock()
        resp_page2.content = (
            b'id,time_name,obs_time_period,obs_value,page_current_page,page_last_page\n'
            b'3701,Year,2024-01,7212.9,2,2')
        mock_session.get.side_effect = [resp_page1, resp_page2]

        with tempfile.TemporaryDirectory() as tmp_dir:
            dest_csv = os.path.join(tmp_dir, 'cbs_series_2_1_1_1.csv')
            download_script.fetch_cbs_series_raw_csv(
                path_id='2,1,1,1',
                dest_path=dest_csv,
                session=mock_session,
                min_unique_series=2,
                min_annual_rows={},
            )
            with open(dest_csv, 'rb') as fp:
                lines = fp.read().splitlines()
            self.assertEqual(len(lines), 3)
            self.assertEqual(lines[1], b'3700,Year,2024-01,10065.5,1,2')
            self.assertEqual(lines[2], b'3701,Year,2024-01,7212.9,2,2')

    def test_fetch_cbs_series_raw_csv_cross_attempt_merge_upgrades_empty_value(
            self):
        mock_merge_session = mock.MagicMock()
        r1 = mock.MagicMock()
        r1.content = (b'id,time_name,obs_time_period,obs_value\n\n'
                      b'3700,Year,2023-01,9900.0\n'
                      b'3700,Year,2024-01,')
        r2 = mock.MagicMock()
        r2.content = (b'id,time_name,obs_time_period,obs_value\n'
                      b'3700,Year,2024-01,10065.5\n'
                      b'3700,Year,2022-01,9662.0')
        mock_merge_session.get.side_effect = [r1, r2]
        with tempfile.TemporaryDirectory() as tmp_dir:
            dest_csv = os.path.join(tmp_dir, 'cbs_merged.csv')
            download_script.fetch_cbs_series_raw_csv(
                path_id='2,1,1,1',
                dest_path=dest_csv,
                session=mock_merge_session,
                min_unique_series=1,
                min_annual_rows={'3700': 3},
            )
            with open(dest_csv, 'rb') as fp:
                merged_lines = fp.read().splitlines()
            self.assertEqual(len(merged_lines), 4)
            self.assertIn(b'3700,Year,2023-01,9900.0', merged_lines)
            self.assertIn(b'3700,Year,2024-01,10065.5', merged_lines)
            self.assertIn(b'3700,Year,2022-01,9662.0', merged_lines)

    def test_cause_of_death_min_annual_rows_matches_exact_36_series(self):
        cod_map = download_script.CBS_SERIES_MIN_ANNUAL_ROWS[
            download_script.CBS_SERIES_CAUSE_OF_DEATH_PATH_ID]
        expected_ids = (set(str(sid) for sid in range(70001, 70007)) |
                        set(str(sid) for sid in range(70008, 70014)) |
                        set(str(sid) for sid in range(70015, 70021)) |
                        set(str(sid) for sid in range(70022, 70028)) |
                        set(str(sid) for sid in range(70136, 70142)) |
                        set(str(sid) for sid in range(70143, 70149)))
        self.assertEqual(len(cod_map), 36)
        self.assertEqual(set(cod_map.keys()), expected_ids)
        for unused_all_causes in ('70007', '70021', '70142'):
            self.assertNotIn(unused_all_causes, cod_map)
        self.assertEqual(cod_map['70013'], 70)
        self.assertEqual(cod_map['70027'], 50)
        self.assertEqual(cod_map['70148'], 24)

    def test_fetch_cbs_series_raw_csv_rejected_pages_do_not_leak(self):
        hdr = (b'id,time_name,obs_time_period,obs_value,page_current_page,'
               b'page_last_page\n')
        p1 = mock.MagicMock()
        p1.content = hdr + b'3700,Year,2020-01,100,1,2\n'
        p2_invalid_last = mock.MagicMock()
        p2_invalid_last.content = (hdr + b'3700,Year,2022-01,999,2,0\n'
                                   b'3700,Year,2024-01,888,2,0\n')
        p2_stalled = mock.MagicMock()
        p2_stalled.content = hdr + b'3700,Year,2099-01,777,1,2\n'
        p2_partial = mock.MagicMock()
        p2_partial.content = hdr + b'3700,Year,2021-01,101,2,2\n'

        mock_session = mock.MagicMock()
        mock_session.get.side_effect = [
            p1, p2_invalid_last, p1, p2_stalled, p1, p2_partial
        ]
        with tempfile.TemporaryDirectory() as tmp_dir:
            dest_csv = os.path.join(tmp_dir, 'cbs_clean.csv')
            with self.assertRaises(RuntimeError):
                download_script.fetch_cbs_series_raw_csv(
                    path_id='2,1,1,1',
                    dest_path=dest_csv,
                    session=mock_session,
                    min_unique_series=1,
                    min_annual_rows={'3700': 3},
                )
            self.assertFalse(os.path.exists(dest_csv))

        # Verify rejected rows also do not leak when a later attempt succeeds.
        p2_valid = mock.MagicMock()
        p2_valid.content = (hdr + b'3700,Year,2021-01,101,2,2\n'
                            b'3700,Year,2023-01,103,2,2\n')
        mock_session2 = mock.MagicMock()
        mock_session2.get.side_effect = [
            p1, p2_invalid_last, p1, p2_stalled, p1, p2_valid
        ]
        with tempfile.TemporaryDirectory() as tmp_dir:
            dest_csv = os.path.join(tmp_dir, 'cbs_clean2.csv')
            download_script.fetch_cbs_series_raw_csv(
                path_id='2,1,1,1',
                dest_path=dest_csv,
                session=mock_session2,
                min_unique_series=1,
                min_annual_rows={'3700': 3},
            )
            with open(dest_csv, 'rb') as fp:
                written = fp.read()
            self.assertNotIn(b'2022-01', written)
            self.assertNotIn(b'2024-01', written)
            self.assertNotIn(b'2099-01', written)
            self.assertIn(b'2023-01', written)

    def test_fetch_cbs_series_raw_csv_ignores_blank_obs_value_for_completeness(
            self):
        mock_session = mock.MagicMock()
        resp = mock.MagicMock()
        resp.content = (
            b'id,time_name,obs_time_period,obs_value,page_current_page,'
            b'page_last_page\n'
            b'3700,Year,2024-01,,1,1\n'
            b'3700,Year,2023-01,,1,1\n'
            b'3700,Year,2022-01,,1,1\n')
        mock_session.get.return_value = resp

        with tempfile.TemporaryDirectory() as tmp_dir:
            dest_csv = os.path.join(tmp_dir, 'cbs_blank.csv')
            with self.assertRaisesRegex(RuntimeError,
                                        r"incomplete=\{'3700': \(0, 3\)\}"):
                download_script.fetch_cbs_series_raw_csv(
                    path_id='2,1,1,1',
                    dest_path=dest_csv,
                    session=mock_session,
                    min_unique_series=1,
                    min_annual_rows={'3700': 3},
                )
            self.assertEqual(mock_session.get.call_count, 3)

    def test_fetch_cbs_series_raw_csv_realigns_reordered_columns(self):
        h1 = (b'id,time_name,obs_time_period,obs_value,page_current_page,'
              b'page_last_page\n')
        h2 = (b'id,time_name,obs_value,obs_time_period,page_current_page,'
              b'page_last_page\n')
        # Case 1: Within-attempt multi-page column reordering.
        p1 = mock.MagicMock()
        p1.content = h1 + b'3700,Year,2023-01,9999.0,1,2\n'
        p2 = mock.MagicMock()
        p2.content = h2 + b'3700,Year,10065.5,2024-01,2,2\n'
        mock_session = mock.MagicMock()
        mock_session.get.side_effect = [p1, p2]
        with tempfile.TemporaryDirectory() as tmp_dir:
            dest_csv = os.path.join(tmp_dir, 'cbs_same_attempt.csv')
            download_script.fetch_cbs_series_raw_csv(
                path_id='2,1,1,1',
                dest_path=dest_csv,
                session=mock_session,
                min_unique_series=1,
                min_annual_rows={'3700': 2},
            )
            with open(dest_csv, 'r', encoding='utf-8') as fp:
                rows = fp.read().splitlines()
            self.assertEqual(
                rows[0],
                'id,time_name,obs_time_period,obs_value,page_current_page,'
                'page_last_page')
            self.assertIn('3700,Year,2023-01,9999.0,1,2', rows)
            self.assertIn('3700,Year,2024-01,10065.5,2,2', rows)

        # Case 2: Cross-attempt merge with reordered columns and an extra column.
        a1p1 = mock.MagicMock()
        a1p1.content = h1 + b'3700,Year,2022-01,9000.0,1,2\n'
        a1p2_err = download_script.requests.ConnectionError('drop')
        h2_extra = (b'id,time_name,obs_value,obs_time_period,extra_col,'
                    b'page_current_page,page_last_page\n')
        a2p1 = mock.MagicMock()
        a2p1.content = h1 + b'3700,Year,2023-01,9999.0,1,2\n'
        a2p2 = mock.MagicMock()
        a2p2.content = h2_extra + b'3700,Year,10065.5,2024-01,meta,2,2\n'
        mock_session2 = mock.MagicMock()
        mock_session2.get.side_effect = [a1p1, a1p2_err, a2p1, a2p2]
        with tempfile.TemporaryDirectory() as tmp_dir:
            dest_csv = os.path.join(tmp_dir, 'cbs_cross_attempt.csv')
            download_script.fetch_cbs_series_raw_csv(
                path_id='2,1,1,1',
                dest_path=dest_csv,
                session=mock_session2,
                min_unique_series=1,
                min_annual_rows={'3700': 3},
            )
            with open(dest_csv, 'r', encoding='utf-8') as fp:
                rows = fp.read().splitlines()
            self.assertEqual(
                rows[0],
                'id,time_name,obs_time_period,obs_value,page_current_page,'
                'page_last_page,extra_col')
            self.assertIn('3700,Year,2022-01,9000.0,1,2,', rows)
            self.assertIn('3700,Year,2023-01,9999.0,1,2,', rows)
            self.assertIn('3700,Year,2024-01,10065.5,2,2,meta', rows)

    def test_fetch_cbs_series_raw_csv_rejects_forward_skip_and_non_ascii_digits(
            self):
        hdr = (b'id,time_name,obs_time_period,obs_value,page_current_page,'
               b'page_last_page\n')
        # Forward skip: requested page 2 of 3, received page_current_page=3.
        p1 = mock.MagicMock()
        p1.content = hdr + b'3700,Year,2021-01,100,1,3\n'
        p3 = mock.MagicMock()
        p3.content = hdr + b'3700,Year,2023-01,300,3,3\n'
        mock_session = mock.MagicMock()
        mock_session.get.side_effect = [p1, p3, p1, p3, p1, p3]
        with tempfile.TemporaryDirectory() as tmp_dir:
            with self.assertRaises(RuntimeError):
                download_script.fetch_cbs_series_raw_csv(
                    path_id='2,1,1,1',
                    dest_path=os.path.join(tmp_dir, 'skip.csv'),
                    session=mock_session,
                    min_unique_series=1,
                    min_annual_rows={},
                )
            self.assertEqual(mock_session.get.call_count, 6)

        # Non-ASCII digit ('²') should be rejected without raising ValueError.
        resp_non_ascii = mock.MagicMock()
        resp_non_ascii.content = (hdr +
                                  '3700,Year,2021-01,100,²,1\n'.encode('utf-8'))
        mock_session2 = mock.MagicMock()
        mock_session2.get.return_value = resp_non_ascii
        with tempfile.TemporaryDirectory() as tmp_dir:
            with self.assertRaises(RuntimeError):
                download_script.fetch_cbs_series_raw_csv(
                    path_id='2,1,1,1',
                    dest_path=os.path.join(tmp_dir, 'non_ascii.csv'),
                    session=mock_session2,
                    min_unique_series=1,
                    min_annual_rows={},
                )

        # Conflicting page_last_page values within the same page.
        resp_conflict = mock.MagicMock()
        resp_conflict.content = (hdr + b'3700,Year,2021-01,100,1,3\n'
                                 b'3700,Year,2022-01,101,1,2\n')
        mock_session3 = mock.MagicMock()
        mock_session3.get.return_value = resp_conflict
        with tempfile.TemporaryDirectory() as tmp_dir:
            with self.assertRaises(RuntimeError):
                download_script.fetch_cbs_series_raw_csv(
                    path_id='2,1,1,1',
                    dest_path=os.path.join(tmp_dir, 'conflict.csv'),
                    session=mock_session3,
                    min_unique_series=1,
                    min_annual_rows={},
                )

    def test_downloaders_fail_fast_on_404_and_retry_429(self):

        def _http_error(status: int) -> download_script.requests.HTTPError:
            resp_obj = download_script.requests.Response()
            resp_obj.status_code = status
            return download_script.requests.HTTPError(f'{status} error',
                                                      response=resp_obj)

        with tempfile.TemporaryDirectory() as tmp_dir:
            # Series CSV: 404 fails fast on attempt 1 with 0 sleeps.
            resp_404 = mock.MagicMock()
            resp_404.raise_for_status.side_effect = _http_error(404)
            sess = mock.MagicMock()
            sess.get.return_value = resp_404
            with mock.patch.object(download_script.time, 'sleep') as mock_sleep:
                with self.assertRaises(download_script.requests.HTTPError):
                    download_script.fetch_cbs_series_raw_csv(
                        path_id='2,1,1,1',
                        dest_path=os.path.join(tmp_dir, 's.csv'),
                        session=sess,
                        retry_delay=1.0,
                    )
            self.assertEqual(sess.get.call_count, 1)
            self.assertEqual(mock_sleep.call_count, 0)

            # Series CSV: 429 retries all 3 attempts.
            resp_429 = mock.MagicMock()
            resp_429.raise_for_status.side_effect = _http_error(429)
            sess_429 = mock.MagicMock()
            sess_429.get.return_value = resp_429
            with self.assertRaises(RuntimeError):
                download_script.fetch_cbs_series_raw_csv(
                    path_id='2,1,1,1',
                    dest_path=os.path.join(tmp_dir, 's429.csv'),
                    session=sess_429,
                )
            self.assertEqual(sess_429.get.call_count, 3)

            # BoardsGenerator JSON: 404 fails fast.
            sess_json = mock.MagicMock()
            sess_json.get.return_value = resp_404
            with self.assertRaises(download_script.requests.HTTPError):
                download_script.fetch_cbs_boardsgenerator_census_raw_json(
                    output_dir=tmp_dir,
                    session=sess_json,
                )
            self.assertEqual(sess_json.get.call_count, 1)

            # Mifkad XLS: 404 fails fast.
            sess_xls = mock.MagicMock()
            sess_xls.get.return_value = resp_404
            with self.assertRaises(download_script.requests.HTTPError):
                download_script.fetch_cbs_mifkad_table_raw(
                    xls_name='dem1_2.xls',
                    dest_path=os.path.join(tmp_dir, 'dem1_2.xls'),
                    session=sess_xls,
                )
            self.assertEqual(sess_xls.get.call_count, 1)

    def test_fetch_cbs_series_raw_csv_applies_retry_backoff(self):
        mock_session = mock.MagicMock()
        resp = mock.MagicMock()
        resp.content = b'<!DOCTYPE html><html>WAF</html>'
        mock_session.get.return_value = resp

        with tempfile.TemporaryDirectory() as tmp_dir:
            dest_csv = os.path.join(tmp_dir, 'cbs_series_2_1_1_1.csv')
            with mock.patch.object(download_script.time, 'sleep') as mock_sleep:
                with self.assertRaises(RuntimeError):
                    download_script.fetch_cbs_series_raw_csv(
                        path_id='2,1,1,1',
                        dest_path=dest_csv,
                        session=mock_session,
                        retry_delay=1.0,
                    )
            self.assertEqual(mock_sleep.call_args_list,
                             [mock.call(1.0), mock.call(2.0)])

    def test_fetch_cbs_series_raw_csv_raises_on_invalid_csv(self):
        mock_session = mock.MagicMock()
        resp = mock.MagicMock()
        resp.content = b'<!DOCTYPE html><html>Error</html>'
        mock_session.get.return_value = resp

        with tempfile.TemporaryDirectory() as tmp_dir:
            dest_csv = os.path.join(tmp_dir, 'cbs_series_2_1_1_1.csv')
            with self.assertRaises(RuntimeError):
                download_script.fetch_cbs_series_raw_csv(
                    path_id='2,1,1,1',
                    dest_path=dest_csv,
                    session=mock_session,
                )
            self.assertEqual(mock_session.get.call_count, 3)

    def test_fetch_cbs_series_raw_csv_raises_on_incomplete_series_after_retries(
            self):
        mock_session = mock.MagicMock()
        resp = mock.MagicMock()
        resp.content = (b'id,time_name,obs_time_period,obs_value\n'
                        b'3700,Year,2024-01,10065.5\n')
        mock_session.get.return_value = resp

        with tempfile.TemporaryDirectory() as tmp_dir:
            dest_csv = os.path.join(tmp_dir, 'cbs_series_2_1_1_1.csv')
            with self.assertRaisesRegex(RuntimeError,
                                        r"incomplete=\{'3700': \(1, 2\)\}"):
                download_script.fetch_cbs_series_raw_csv(
                    path_id='2,1,1,1',
                    dest_path=dest_csv,
                    session=mock_session,
                    min_unique_series=5,
                    min_annual_rows={'3700': 2},
                )
            self.assertEqual(mock_session.get.call_count, 3)

    def test_fetch_cbs_boardsgenerator_census_raw_json(self):
        mock_session = mock.MagicMock()
        resp = mock.MagicMock()
        payload = {
            'Groups': [{
                'Id':
                    2,
                'Name':
                    'Demography',
                'Subjects': [{
                    'Id': sid,
                    'Name': f'Subject {sid}',
                    'Value': '104.5',
                } for sid in (18, 19, 20, 218, 219, 220, 221, 222, 223, 224)],
            }]
        }
        resp.json.return_value = payload
        mock_session.get.return_value = resp

        with tempfile.TemporaryDirectory() as tmp_dir:
            dest_json = download_script.fetch_cbs_boardsgenerator_census_raw_json(
                output_dir=tmp_dir,
                session=mock_session,
            )
            with open(dest_json, 'r', encoding='utf-8') as fp:
                records = json.load(fp)
            self.assertEqual(len(records),
                             len(download_script.CBS_CENSUS_2008_REGIONS))
            self.assertEqual(records[0]['region_code'], '999')
            self.assertEqual(records[0]['data_mode'], 'Machoz')
            self.assertEqual(records[0]['payload'], payload)

    def test_fetch_cbs_boardsgenerator_census_raw_json_empty_groups_warns_and_retries(
            self):
        mock_session = mock.MagicMock()
        resp = mock.MagicMock()
        resp.json.return_value = {'Groups': []}
        mock_session.get.return_value = resp

        with tempfile.TemporaryDirectory() as tmp_dir:
            with (mock.patch.object(download_script.time,
                                    'sleep') as mock_sleep,
                  mock.patch.object(download_script.logging, 'warning') as
                  mock_warn):
                with self.assertRaises(RuntimeError):
                    download_script.fetch_cbs_boardsgenerator_census_raw_json(
                        output_dir=tmp_dir,
                        session=mock_session,
                        retry_delay=1.0,
                    )
            self.assertEqual(mock_session.get.call_count, 3)
            self.assertEqual(mock_session.cookies.clear.call_count, 3)
            self.assertEqual(mock_sleep.call_args_list,
                             [mock.call(1.0), mock.call(2.0)])
            self.assertEqual(mock_warn.call_count, 3)

    def test_fetch_cbs_mifkad_table_raw_writes_untouched_bytes(self):
        mock_session = mock.MagicMock()
        resp = mock.MagicMock()
        raw_xls = b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1mock_xls_bytes'
        resp.content = raw_xls
        mock_session.get.return_value = resp

        with tempfile.TemporaryDirectory() as tmp_dir:
            dest_xls = os.path.join(tmp_dir, 'dem1_2.xls')
            byte_count = download_script.fetch_cbs_mifkad_table_raw(
                xls_name='dem1_2.xls',
                dest_path=dest_xls,
                session=mock_session,
            )
            self.assertEqual(byte_count, len(raw_xls))
            with open(dest_xls, 'rb') as fp:
                self.assertEqual(fp.read(), raw_xls)

    def test_fetch_cbs_mifkad_table_raw_rejects_lowercase_html_and_no_double_log(
            self):
        mock_session = mock.MagicMock()
        resp = mock.MagicMock()
        resp.content = b'<!doctype html><html><body>WAF Blocked</body></html>'
        mock_session.get.return_value = resp

        with tempfile.TemporaryDirectory() as tmp_dir:
            dest_xls = os.path.join(tmp_dir, 'dem1_2.xls')
            with (mock.patch.object(download_script.time,
                                    'sleep') as mock_sleep,
                  mock.patch.object(download_script.logging, 'warning') as
                  mock_warn):
                with self.assertRaises(RuntimeError):
                    download_script.fetch_cbs_mifkad_table_raw(
                        xls_name='dem1_2.xls',
                        dest_path=dest_xls,
                        session=mock_session,
                        retry_delay=1.0,
                    )
            self.assertFalse(os.path.exists(dest_xls))
            self.assertEqual(mock_session.get.call_count, 3)
            self.assertEqual(mock_session.cookies.clear.call_count, 3)
            self.assertEqual(mock_sleep.call_args_list,
                             [mock.call(1.0), mock.call(2.0)])
            self.assertEqual(mock_warn.call_count, 3)

        # RequestException should log only once per attempt (no double-logging).
        mock_session2 = mock.MagicMock()
        mock_session2.get.side_effect = download_script.requests.ConnectionError(
            'reset')
        with tempfile.TemporaryDirectory() as tmp_dir:
            with mock.patch.object(download_script.logging,
                                   'warning') as mock_warn:
                with self.assertRaises(RuntimeError):
                    download_script.fetch_cbs_mifkad_table_raw(
                        xls_name='dem1_2.xls',
                        dest_path=os.path.join(tmp_dir, 'dem1_2.xls'),
                        session=mock_session2,
                    )
            self.assertEqual(mock_warn.call_count, 3)

    def test_fetch_cbs_series_raw_csv_rejects_placeholders_and_upgrades_on_merge(
            self):
        # CBS missing tokens ('-', '..', '...', '*') and non-finite strings
        # ('nan', 'inf') must not satisfy min_annual_rows.
        mock_session = mock.MagicMock()
        resp_placeholders = mock.MagicMock()
        resp_placeholders.content = (
            b'id,time_name,obs_time_period,obs_value,page_current_page,'
            b'page_last_page\n'
            b'3700,Year,2024-01,-,1,1\n'
            b'3700,Year,2023-01,..,1,1\n'
            b'3700,Year,2022-01,...,1,1\n'
            b'3700,Year,2021-01,*,1,1\n'
            b'3700,Year,2020-01,nan,1,1\n'
            b'3700,Year,2019-01,inf,1,1\n')
        mock_session.get.return_value = resp_placeholders
        with tempfile.TemporaryDirectory() as tmp_dir:
            with self.assertRaisesRegex(RuntimeError,
                                        r"incomplete=\{'3700': \(0, 2\)\}"):
                download_script.fetch_cbs_series_raw_csv(
                    path_id='2,1,1,1',
                    dest_path=os.path.join(tmp_dir, 'placeholders.csv'),
                    session=mock_session,
                    min_unique_series=1,
                    min_annual_rows={'3700': 2},
                )
            self.assertEqual(mock_session.get.call_count, 3)

        # Cross-attempt merge must upgrade a placeholder ('-') to a numeric obs.
        r1 = mock.MagicMock()
        r1.content = (b'id,time_name,obs_time_period,obs_value\n'
                      b'3700,Year,2023-01,9900.0\n'
                      b'3700,Year,2024-01,-\n')
        r2 = mock.MagicMock()
        r2.content = (b'id,time_name,obs_time_period,obs_value\n'
                      b'3700,Year,2024-01,10065.5\n'
                      b'3700,Year,2022-01,9662.0\n')
        mock_merge = mock.MagicMock()
        mock_merge.get.side_effect = [r1, r2]
        with tempfile.TemporaryDirectory() as tmp_dir:
            dest_csv = os.path.join(tmp_dir, 'upgraded.csv')
            download_script.fetch_cbs_series_raw_csv(
                path_id='2,1,1,1',
                dest_path=dest_csv,
                session=mock_merge,
                min_unique_series=1,
                min_annual_rows={'3700': 3},
            )
            with open(dest_csv, 'rb') as fp:
                lines = fp.read().splitlines()
            self.assertIn(b'3700,Year,2024-01,10065.5', lines)
            self.assertNotIn(b'3700,Year,2024-01,-', lines)

    def test_fetch_cbs_series_raw_csv_counts_unique_ascii_years(self):
        # Duplicate annual periods in the same year ('2024' and '2024-01')
        # collapse to 1 unique year; non-ASCII Arabic-Indic digits count as 0.
        mock_session = mock.MagicMock()
        resp = mock.MagicMock()
        resp.content = ('id,time_name,obs_time_period,obs_value\n'
                        '3700,Year,2024,10000.0\n'
                        '3700,Year,2024-01,10050.0\n'
                        '3700,Year,٢٠٢٣-01,9900.0\n'.encode('utf-8'))
        mock_session.get.return_value = resp
        with tempfile.TemporaryDirectory() as tmp_dir:
            with self.assertRaisesRegex(RuntimeError,
                                        r"incomplete=\{'3700': \(1, 2\)\}"):
                download_script.fetch_cbs_series_raw_csv(
                    path_id='2,1,1,1',
                    dest_path=os.path.join(tmp_dir, 'same_year.csv'),
                    session=mock_session,
                    min_unique_series=1,
                    min_annual_rows={'3700': 2},
                )
            self.assertEqual(mock_session.get.call_count, 3)

        # Blank time_name with sub-annual '2024-02' marks series as sub-annual
        # (0 annual rows), and blank time_name falls back to time_unit='Month'.
        for csv_bytes in (
                b'id,time_name,obs_time_period,obs_value\n'
                b'3700,,2024-01,10000.0\n'
                b'3700,,2024-02,10050.0\n',
                b'id,time_name,time_unit,obs_time_period,obs_value\n'
                b'3700,,Month,2024-01,10000.0\n',
        ):
            sub_sess = mock.MagicMock()
            sub_resp = mock.MagicMock()
            sub_resp.content = csv_bytes
            sub_sess.get.return_value = sub_resp
            with tempfile.TemporaryDirectory() as tmp_dir:
                with self.assertRaisesRegex(RuntimeError,
                                            r"incomplete=\{'3700': \(0, 1\)\}"):
                    download_script.fetch_cbs_series_raw_csv(
                        path_id='2,1,1,1',
                        dest_path=os.path.join(tmp_dir, 'monthly_blank.csv'),
                        session=sub_sess,
                        min_unique_series=1,
                        min_annual_rows={'3700': 1},
                    )

    def test_fetch_cbs_boardsgenerator_census_raw_json_rejects_malformed_groups(
            self):
        malformed_payloads = [
            {
                'Groups': ['bad']
            },
            {
                'Groups': [{
                    'Id': 1,
                    'Subjects': ['bad']
                }]
            },
            {
                'Groups': [{
                    'Id': 1,
                    'Subjects': [{
                        'Id': 18
                    }, 'bad']
                }]
            },
            {
                'Groups': [{
                    'Id': 1,
                    'Subjects': []
                }]
            },
        ]
        for payload in malformed_payloads:
            mock_session = mock.MagicMock()
            resp = mock.MagicMock()
            resp.json.return_value = payload
            mock_session.get.return_value = resp
            with tempfile.TemporaryDirectory() as tmp_dir:
                with self.assertRaises(RuntimeError):
                    download_script.fetch_cbs_boardsgenerator_census_raw_json(
                        output_dir=tmp_dir,
                        session=mock_session,
                    )
                self.assertEqual(mock_session.get.call_count, 3)

    def test_get_session_disables_inner_urllib3_retries(self):
        self.addCleanup(download_script._close_sessions)
        if hasattr(download_script._THREAD_LOCAL, 'session'):
            delattr(download_script._THREAD_LOCAL, 'session')
        sess = download_script._get_session()
        for prefix in ('https://', 'http://'):
            adapter = sess.get_adapter(f'{prefix}apis.cbs.gov.il')
            self.assertEqual(adapter.max_retries.total, 0)

    def test_cause_of_death_min_unique_ids_succeeds_with_only_36_series(self):
        cod_path_id = download_script.CBS_SERIES_CAUSE_OF_DEATH_PATH_ID
        self.assertEqual(
            download_script._CBS_SERIES_MIN_UNIQUE_IDS[cod_path_id], 36)
        sids = sorted(download_script.CBS_SERIES_MIN_ANNUAL_ROWS[cod_path_id])
        csv_lines = ['id,time_name,obs_time_period,obs_value'
                    ] + [f'{sid},Year,2022-01,10.5' for sid in sids]
        mock_session = mock.MagicMock()
        resp = mock.MagicMock()
        resp.content = ('\n'.join(csv_lines) + '\n').encode('utf-8')
        mock_session.get.return_value = resp
        with tempfile.TemporaryDirectory() as tmp_dir:
            dest_csv = os.path.join(tmp_dir, 'cbs_series_4_2_1.csv')
            byte_count = download_script.fetch_cbs_series_raw_csv(
                path_id=cod_path_id,
                dest_path=dest_csv,
                session=mock_session,
                min_annual_rows={},
            )
            self.assertGreater(byte_count, 0)
            self.assertTrue(os.path.exists(dest_csv))

    def test_fetch_cbs_series_raw_csv_rejects_shrinking_and_invalid_page_last(
            self):
        hdr = (b'id,time_name,obs_time_period,obs_value,page_current_page,'
               b'page_last_page\n')
        # Case 1: page 1 claims 3 pages, page 2 claims page_last_page=1 (2 > 1).
        p1 = mock.MagicMock()
        p1.content = hdr + b'3700,Year,2021-01,100,1,3\n'
        p2_gt = mock.MagicMock()
        p2_gt.content = hdr + b'3700,Year,2022-01,200,2,1\n'
        sess1 = mock.MagicMock()
        sess1.get.side_effect = [p1, p2_gt, p1, p2_gt, p1, p2_gt]
        with tempfile.TemporaryDirectory() as tmp_dir:
            dest = os.path.join(tmp_dir, 'shrink_gt.csv')
            with self.assertRaises(RuntimeError):
                download_script.fetch_cbs_series_raw_csv(
                    path_id='2,1,1,1',
                    dest_path=dest,
                    session=sess1,
                    min_unique_series=1,
                    min_annual_rows={},
                )
            self.assertFalse(os.path.exists(dest))

        # Case 2: page 1 claims 3 pages, page 2 shrinks page_last_page to 2.
        p2_shrink = mock.MagicMock()
        p2_shrink.content = hdr + b'3700,Year,2022-01,200,2,2\n'
        sess2 = mock.MagicMock()
        sess2.get.side_effect = [p1, p2_shrink, p1, p2_shrink, p1, p2_shrink]
        with tempfile.TemporaryDirectory() as tmp_dir:
            dest = os.path.join(tmp_dir, 'shrink_mid.csv')
            with self.assertRaises(RuntimeError):
                download_script.fetch_cbs_series_raw_csv(
                    path_id='2,1,1,1',
                    dest_path=dest,
                    session=sess2,
                    min_unique_series=1,
                    min_annual_rows={},
                )
            self.assertFalse(os.path.exists(dest))

        # Case 3: across attempts, page_last_page shrinks from 3 to 2 on page 1.
        p1_shrink = mock.MagicMock()
        p1_shrink.content = hdr + b'3700,Year,2021-01,100,1,2\n'
        p2_err = download_script.requests.exceptions.Timeout('page 2 timeout')
        sess3 = mock.MagicMock()
        sess3.get.side_effect = [p1, p2_err, p1_shrink, p1_shrink]
        with tempfile.TemporaryDirectory() as tmp_dir:
            dest = os.path.join(tmp_dir, 'shrink_cross.csv')
            with self.assertRaises(RuntimeError):
                download_script.fetch_cbs_series_raw_csv(
                    path_id='2,1,1,1',
                    dest_path=dest,
                    session=sess3,
                    min_unique_series=1,
                    min_annual_rows={},
                )
            self.assertFalse(os.path.exists(dest))

    def test_fetch_cbs_series_raw_csv_blocks_stale_single_page_merge_latches(
            self):
        # Case 1: attempt 1 omits page_last_page with 1 series (< page_size=2);
        # attempt 2 omits page_last_page with 2 series (== page_size=2) and
        # page 2 times out. Must NOT commit truncated data via stale latch.
        a1 = mock.MagicMock()
        a1.content = (b'id,time_name,obs_time_period,obs_value\n'
                      b'3700,Year,2021-01,100\n')
        a2_p1 = mock.MagicMock()
        a2_p1.content = (b'id,time_name,obs_time_period,obs_value\n'
                         b'3700,Year,2022-01,200\n'
                         b'3701,Year,2022-01,300\n')
        timeout_err = download_script.requests.exceptions.Timeout('p2 timeout')
        sess1 = mock.MagicMock()
        sess1.get.side_effect = [a1, a2_p1, timeout_err, a2_p1, timeout_err]
        with tempfile.TemporaryDirectory() as tmp_dir:
            dest = os.path.join(tmp_dir, 'latch1.csv')
            with self.assertRaises(RuntimeError):
                download_script.fetch_cbs_series_raw_csv(
                    path_id='2,1,1,1',
                    dest_path=dest,
                    session=sess1,
                    page_size=2,
                    min_unique_series=2,
                    min_annual_rows={'3700': 2},
                )
            self.assertFalse(os.path.exists(dest))

        # Case 2: attempt 1 has page_last_page=1 (incomplete: 1/2 series);
        # attempt 2 omits page_last_page, returns 2 series (== page_size=2),
        # and page 2 times out. Must NOT treat known_last_page=1 as complete.
        a1_lp = mock.MagicMock()
        a1_lp.content = (
            b'id,time_name,obs_time_period,obs_value,page_current_page,'
            b'page_last_page\n'
            b'3700,Year,2024-01,100,1,1\n')
        sess2 = mock.MagicMock()
        sess2.get.side_effect = [a1_lp, a2_p1, timeout_err, a2_p1, timeout_err]
        with tempfile.TemporaryDirectory() as tmp_dir:
            dest = os.path.join(tmp_dir, 'latch2.csv')
            with self.assertRaises(RuntimeError):
                download_script.fetch_cbs_series_raw_csv(
                    path_id='2,1,1,1',
                    dest_path=dest,
                    session=sess2,
                    page_size=2,
                    min_unique_series=2,
                    min_annual_rows={},
                )
            self.assertFalse(os.path.exists(dest))

    def test_fetch_cbs_series_raw_csv_rejects_short_page_before_state_commit_and_unbounded_timeout(
            self):
        hdr_lp = (b'id,time_name,obs_time_period,obs_value,page_current_page,'
                  b'page_last_page\n')
        hdr_no_lp = b'id,time_name,obs_time_period,obs_value\n'

        # Probe 1: Rejected short page must NOT satisfy incomplete_merged via
        # Attempt 1's completed_pages={1, 2}.
        a1_p1 = mock.MagicMock(
            content=hdr_lp +
            b'3700,Year,2021-01,100,1,2\n3701,Year,2021-01,50,1,2\n')
        a1_p2 = mock.MagicMock(content=hdr_lp + b'3701,Year,2022-01,60,2,2\n')
        a2_short = mock.MagicMock(content=hdr_no_lp +
                                  b'3700,Year,2022-01,999\n')
        sess1 = mock.MagicMock()
        sess1.get.side_effect = [a1_p1, a1_p2, a2_short, a2_short]
        with tempfile.TemporaryDirectory() as tmp_dir:
            dest = os.path.join(tmp_dir, 'probe1.csv')
            with self.assertRaisesRegex(RuntimeError,
                                        r'complete_pages=\[1, 2\]/2'):
                download_script.fetch_cbs_series_raw_csv(
                    path_id='2,1,1,1',
                    dest_path=dest,
                    session=sess1,
                    page_size=2,
                    min_unique_series=2,
                    min_annual_rows={'3700': 2},
                )
            self.assertFalse(os.path.exists(dest))

        # Probe 1B: Poisoned row from a rejected short page must NOT leak into
        # a subsequent cross-attempt merge.
        b_a1_p1 = mock.MagicMock(
            content=hdr_no_lp +
            b'3700,Year,2021-01,100\n3701,Year,2021-01,200\n')
        timeout_err = download_script.requests.exceptions.Timeout('p2 timeout')
        b_a2_poison = mock.MagicMock(content=hdr_no_lp +
                                     b'3799,Year,2099-01,99999\n')
        b_a3_p1 = mock.MagicMock(
            content=hdr_no_lp + b'3700,Year,2021-01,-\n3701,Year,2021-01,200\n')
        b_a3_p2 = mock.MagicMock(content=hdr_no_lp + b'3700,Year,2022-01,110\n')
        sess1b = mock.MagicMock()
        sess1b.get.side_effect = [
            b_a1_p1,
            timeout_err,
            b_a2_poison,
            b_a3_p1,
            b_a3_p2,
        ]
        with tempfile.TemporaryDirectory() as tmp_dir:
            dest = os.path.join(tmp_dir, 'probe1b.csv')
            download_script.fetch_cbs_series_raw_csv(
                path_id='2,1,1,1',
                dest_path=dest,
                session=sess1b,
                page_size=2,
                min_unique_series=2,
                min_annual_rows={'3700': 2},
            )
            with open(dest, 'rb') as fp:
                written = fp.read()
            self.assertNotIn(b'3799', written)
            self.assertIn(b'3700,Year,2021-01,100', written)
            self.assertIn(b'3700,Year,2022-01,110', written)

        # Probe 1C: Attempt 1 sets known_last_page=2; Attempt 2 omits
        # page_last_page, returns full page 1, and times out on page 2.
        # Must NOT prematurely succeed using Attempt 1's known_last_page=2.
        c_a2_full = mock.MagicMock(
            content=hdr_no_lp +
            b'3700,Year,2022-01,110\n3701,Year,2022-01,210\n')
        sess1c = mock.MagicMock()
        sess1c.get.side_effect = [
            a1_p1,
            a1_p2,
            c_a2_full,
            timeout_err,
            c_a2_full,
            timeout_err,
        ]
        with tempfile.TemporaryDirectory() as tmp_dir:
            dest = os.path.join(tmp_dir, 'probe1c.csv')
            with self.assertRaises(RuntimeError):
                download_script.fetch_cbs_series_raw_csv(
                    path_id='2,1,1,1',
                    dest_path=dest,
                    session=sess1c,
                    page_size=2,
                    min_unique_series=2,
                    min_annual_rows={'3700': 2},
                )
            self.assertFalse(os.path.exists(dest))

    def test_fetch_cbs_series_raw_csv_fresher_merge_upgrade_and_ragged_pagination(
            self):
        hdr_no_lp = b'id,time_name,obs_time_period,obs_value\n'
        # Probe 1D: Fresher retry value overwrites stale earlier attempt value.
        m1 = mock.MagicMock(content=hdr_no_lp + b'3700,Year,2023-01,9999.0\n')
        m2 = mock.MagicMock(
            content=hdr_no_lp +
            b'3700,Year,2023-01,10065.5\n3700,Year,2024-01,10100.0\n')
        sess_fresh = mock.MagicMock()
        sess_fresh.get.side_effect = [m1, m2]
        with tempfile.TemporaryDirectory() as tmp_dir:
            dest = os.path.join(tmp_dir, 'fresher.csv')
            download_script.fetch_cbs_series_raw_csv(
                path_id='2,1,1,1',
                dest_path=dest,
                session=sess_fresh,
                min_unique_series=1,
                min_annual_rows={'3700': 2},
            )
            with open(dest, 'rb') as fp:
                lines = fp.read().splitlines()
            self.assertIn(b'3700,Year,2023-01,10065.5', lines)
            self.assertNotIn(b'3700,Year,2023-01,9999.0', lines)

        # Probe 4: Page 2 upgrading a blank obs_value from page 1 is accepted.
        hdr_lp = (b'id,time_name,obs_time_period,obs_value,page_current_page,'
                  b'page_last_page\n')
        up_p1 = mock.MagicMock(content=hdr_lp + b'3700,Year,2024-01,,1,2\n')
        up_p2 = mock.MagicMock(content=hdr_lp +
                               b'3700,Year,2024-01,10065.5,2,2\n')
        sess_up = mock.MagicMock()
        sess_up.get.side_effect = [up_p1, up_p2]
        with tempfile.TemporaryDirectory() as tmp_dir:
            dest = os.path.join(tmp_dir, 'page_upgrade.csv')
            download_script.fetch_cbs_series_raw_csv(
                path_id='2,1,1,1',
                dest_path=dest,
                session=sess_up,
                min_unique_series=1,
                min_annual_rows={'3700': 1},
            )
            with open(dest, 'rb') as fp:
                txt = fp.read()
            self.assertIn(b'3700,Year,2024-01,10065.5,2,2', txt)
            self.assertNotIn(b'3700,Year,2024-01,,1,2', txt)

        # Probe 2: Ragged page mixing populated and blank pagination cells fails.
        ragged = mock.MagicMock(
            content=hdr_lp +
            b'3700,Year,2024-01,100,1,1\n3701,Year,2024-01,200,,\n')
        sess_ragged = mock.MagicMock()
        sess_ragged.get.return_value = ragged
        with tempfile.TemporaryDirectory() as tmp_dir:
            with self.assertRaises(RuntimeError):
                download_script.fetch_cbs_series_raw_csv(
                    path_id='2,1,1,1',
                    dest_path=os.path.join(tmp_dir, 'ragged.csv'),
                    session=sess_ragged,
                    min_unique_series=1,
                    min_annual_rows={},
                )

    def test_fetch_cbs_series_raw_csv_rejects_malformed_periods_and_negatives(
            self):
        mock_session = mock.MagicMock()
        resp = mock.MagicMock()
        resp.content = (b'id,time_name,obs_time_period,obs_value\n'
                        b'3700,Year,2024-Q2,10000\n'
                        b'3700,Year,2023xyz,10000\n'
                        b'3700,Year,2022-02,10000\n'
                        b'3700,Year,2021-01,-50\n')
        mock_session.get.return_value = resp
        with tempfile.TemporaryDirectory() as tmp_dir:
            with self.assertRaisesRegex(RuntimeError,
                                        r"incomplete=\{'3700': \(0, 1\)\}"):
                download_script.fetch_cbs_series_raw_csv(
                    path_id='2,1,1,1',
                    dest_path=os.path.join(tmp_dir, 'bad_rows.csv'),
                    session=mock_session,
                    min_unique_series=1,
                    min_annual_rows={'3700': 1},
                )

    def test_is_valid_census_groups_payload_requires_expected_numeric_subject(
            self):
        for bad_payload in (
            {
                'Groups': [{
                    'Subjects': [{}]
                }]
            },
            {
                'Groups': [{
                    'Subjects': [{
                        'Error': 'blocked'
                    }]
                }]
            },
            {
                'Groups': [{
                    'Subjects': [{
                        'Id': 18,
                        'Value': None
                    }]
                }]
            },
            {
                'Groups': [{
                    'Subjects': [{
                        'Id': 18,
                        'Value': '-5.0'
                    }]
                }]
            },
            {
                'Groups': [{
                    'Subjects': [{
                        'Id': 999,
                        'Value': '10.0'
                    }]
                }]
            },
                # Partial Machoz (only 1 of 7 expected subjects) must be rejected.
            {
                'Groups': [{
                    'Subjects': [{
                        'Id': 218,
                        'Value': '10.0'
                    }]
                }]
            },
        ):
            self.assertFalse(
                download_script._is_valid_census_groups_payload(bad_payload))

        machoz_complete = {
            'Groups': [{
                'Subjects': [{
                    'Id': sid,
                    'Value': '10.0'
                } for sid in range(218, 225)]
            }]
        }
        nafa_complete = {
            'Groups': [{
                'Subjects': [{
                    'Id': sid,
                    'Value': '10.0'
                } for sid in (18, 19, 20, *range(218, 225))]
            }]
        }
        self.assertTrue(
            download_script._is_valid_census_groups_payload(machoz_complete,
                                                            data_mode='Machoz'))
        # Machoz-only (7 IDs) lacks Nafa population IDs 18..20.
        self.assertFalse(
            download_script._is_valid_census_groups_payload(machoz_complete,
                                                            data_mode='Nafa'))
        self.assertTrue(
            download_script._is_valid_census_groups_payload(nafa_complete,
                                                            data_mode='Nafa'))
        self.assertTrue(
            download_script._is_valid_census_groups_payload(nafa_complete,
                                                            data_mode='Machoz'))

    def test_download_all_closes_sessions_and_scopes_stale_file_cleanup(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            stale_csv = os.path.join(tmp_dir, 'cbs_old_series.csv')
            stale_xls = os.path.join(tmp_dir, 'old_table.xls')
            keep_py = os.path.join(tmp_dir, 'custom_script.py')
            keep_json = os.path.join(tmp_dir, 'manifest.json')
            for path in (stale_csv, stale_xls, keep_py, keep_json):
                with open(path, 'w', encoding='utf-8') as fp:
                    fp.write('data\n')

            with (mock.patch.object(download_script,
                                    'fetch_cbs_series_datasets_raw',
                                    return_value=[]),
                  mock.patch.object(download_script,
                                    'fetch_cbs_mifkad_table_raw',
                                    return_value=10),
                  mock.patch.object(download_script,
                                    'fetch_cbs_boardsgenerator_census_raw_json',
                                    return_value=os.path.join(
                                        tmp_dir,
                                        'cbs_yishuv_census_2008.json')),
                  mock.patch.object(download_script, '_close_sessions') as
                  mock_close):
                download_script.download_all(tmp_dir, max_workers=1)
            mock_close.assert_called_once()
            self.assertFalse(os.path.exists(stale_csv))
            self.assertFalse(os.path.exists(stale_xls))
            self.assertTrue(os.path.exists(keep_py))
            self.assertTrue(os.path.exists(keep_json))

            # Symlink to _SCRIPT_DIR must skip stale-file cleanup via realpath.
            fake_script_dir = os.path.join(tmp_dir, 'fake_script_dir')
            os.makedirs(fake_script_dir)
            protected_xls = os.path.join(fake_script_dir, 'keep.xls')
            with open(protected_xls, 'w', encoding='utf-8') as fp:
                fp.write('keep\n')
            symlink_dir = os.path.join(tmp_dir, 'link_to_script_dir')
            os.symlink(fake_script_dir, symlink_dir)
            with (mock.patch.object(download_script, '_SCRIPT_DIR',
                                    fake_script_dir),
                  mock.patch.object(download_script,
                                    'fetch_cbs_series_datasets_raw',
                                    return_value=[]),
                  mock.patch.object(download_script,
                                    'fetch_cbs_mifkad_table_raw',
                                    return_value=10),
                  mock.patch.object(download_script,
                                    'fetch_cbs_boardsgenerator_census_raw_json',
                                    return_value=os.path.join(
                                        symlink_dir,
                                        'cbs_yishuv_census_2008.json'))):
                download_script.download_all(symlink_dir, max_workers=1)
            self.assertTrue(os.path.exists(protected_xls))

        # Verify _close_sessions closes tracked sessions and bumps generation.
        download_script._close_sessions()
        sess1 = download_script._get_session()
        with mock.patch.object(sess1, 'close') as mock_sess_close:
            download_script._close_sessions()
        mock_sess_close.assert_called_once()
        sess2 = download_script._get_session()
        self.assertIsNot(sess1, sess2)
        download_script._close_sessions()


if __name__ == '__main__':
    unittest.main()

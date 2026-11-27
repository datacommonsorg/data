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
"""Unit tests for WHO Adolescent Birth Rate data_download.py."""

import csv
import os
import sys
import tempfile
import unittest
from unittest import mock

import requests
from requests.adapters import HTTPAdapter

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if _SCRIPT_DIR not in sys.path:
    sys.path.insert(0, _SCRIPT_DIR)

try:
    from statvar_imports.who.adolescent_birth_rate import data_download
except ModuleNotFoundError:
    import data_download  # type: ignore[no-redef]


def _make_streaming_response(
    chunks: list[bytes],
    status_code: int = 200,
    stream_error: Exception | None = None,
) -> mock.MagicMock:
    """Creates a mock requests.Response supporting context manager & streaming."""
    resp = mock.MagicMock(spec=requests.Response)
    resp.status_code = status_code
    resp.__enter__.return_value = resp
    resp.__exit__.return_value = False
    if status_code >= 400:
        resp.raise_for_status.side_effect = requests.exceptions.HTTPError(
            f'HTTP {status_code}',
            response=resp,
        )
    else:
        resp.raise_for_status.return_value = None

    def _iter_content(chunk_size: int = 8192):
        del chunk_size
        yield from chunks
        if stream_error is not None:
            raise stream_error

    resp.iter_content.side_effect = _iter_content
    return resp


class DataDownloadTest(unittest.TestCase):

    def test_normalize_rate_value_handles_integer_mantissa_scientific_notation(
            self):
        cases = [
            ('1e-09', '1.0e-09'),
            ('8e-08', '8.0e-08'),
            ('4e-09', '4.0e-09'),
            ('-3E+02', '-3.0E+02'),
            ('6.99e-06', '6.99e-06'),
            ('12.34', '12.34'),
            ('0', '0'),
            ('', ''),
        ]
        for raw, expected in cases:
            with self.subTest(raw=raw):
                self.assertEqual(
                    data_download.normalize_rate_value(raw),
                    expected,
                )

    def test_create_retry_session_mounts_retry_adapter_and_skips_4xx(self):
        session = data_download.create_retry_session(
            max_retries=3,
            backoff_factor=1.5,
        )
        self.addCleanup(session.close)

        for prefix in ('https://example.org', 'http://example.org'):
            adapter = session.get_adapter(prefix)
            self.assertIsInstance(adapter, HTTPAdapter)
            retry = adapter.max_retries
            self.assertEqual(retry.total, 3)
            self.assertEqual(retry.connect, 3)
            self.assertEqual(retry.read, 3)
            self.assertEqual(retry.status, 3)
            self.assertEqual(retry.backoff_factor, 1.5)
            self.assertEqual(
                tuple(retry.status_forcelist),
                data_download.RETRYABLE_STATUS_CODES,
            )
            self.assertEqual(retry.allowed_methods, frozenset(['GET']))
            self.assertFalse(retry.raise_on_status)
            self.assertTrue(retry.is_retry('GET', 429))
            self.assertTrue(retry.is_retry('GET', 503))
            self.assertFalse(retry.is_retry('GET', 400))
            self.assertFalse(retry.is_retry('GET', 403))
            self.assertFalse(retry.is_retry('GET', 404))

    def test_download_full_who_data_success_normalizes_scientific_notation(
            self):
        csv_bytes = (
            b'IND_ID,DIM_TIME,DIM_GEO_CODE_M49,GEO_NAME_SHORT,'
            b'DIM_AGE,RATE_PER_1000_N\n'
            b'27D371A,2007,795,Turkmenistan,Y10T14,1e-09\n'
            b'27D371A,2017,275,'
            b'"occupied Palestinian territory, including east Jerusalem",'
            b'Y10T14,8e-08\n'
            b'27D371A,2004,328,Guyana,Y10T14,6.99e-06\n'
            b'27D371A,2024,150,Europe,Y15T19,12.34\n')
        mock_session = mock.MagicMock(spec=requests.Session)
        mock_session.get.return_value = _make_streaming_response([csv_bytes])

        with tempfile.TemporaryDirectory() as tmp_dir:
            out_path = data_download.download_full_who_data(
                indicator_id='TEST_IND',
                output_dir=tmp_dir,
                session=mock_session,
            )

            mock_session.get.assert_called_once_with(
                'https://srhdpeuwpubsa.blob.core.windows.net/whdh/DATADOT/'
                'INDICATOR/TEST_IND_ALL_LATEST.csv',
                stream=True,
                timeout=data_download.DEFAULT_TIMEOUT_SECONDS,
            )
            mock_session.close.assert_not_called()
            self.assertEqual(
                out_path,
                os.path.join(tmp_dir, 'adolescent_birth_rate_input.csv'),
            )
            self.assertEqual(
                os.listdir(tmp_dir),
                ['adolescent_birth_rate_input.csv'],
            )

            with open(out_path, 'r', encoding='utf-8', newline='') as out_file:
                rows = list(csv.DictReader(out_file))
            self.assertEqual(
                [r['RATE_PER_1000_N'] for r in rows],
                ['1.0e-09', '8.0e-08', '6.99e-06', '12.34'],
            )
            self.assertEqual(
                rows[1]['GEO_NAME_SHORT'],
                'occupied Palestinian territory, including east Jerusalem',
            )

    def test_download_full_who_data_uses_explicit_input_url(self):
        csv_bytes = b'DIM_TIME,RATE_PER_1000_N\n2024,0.111\n'
        mock_session = mock.MagicMock(spec=requests.Session)
        mock_session.get.return_value = _make_streaming_response([csv_bytes])
        custom_url = 'https://example.org/custom_who.csv'

        with tempfile.TemporaryDirectory() as tmp_dir:
            patcher = mock.patch.object(
                data_download,
                'create_retry_session',
                return_value=mock_session,
            )
            with patcher as mock_factory:
                out_path = data_download.download_full_who_data(
                    input_url=custom_url,
                    output_dir=tmp_dir,
                )

            mock_factory.assert_called_once_with(
                max_retries=data_download.DEFAULT_MAX_RETRIES,
                backoff_factor=data_download.DEFAULT_BACKOFF_FACTOR,
            )
            mock_session.get.assert_called_once_with(
                custom_url,
                stream=True,
                timeout=data_download.DEFAULT_TIMEOUT_SECONDS,
            )
            mock_session.close.assert_called_once_with()
            self.assertTrue(os.path.exists(out_path))

    def test_download_full_who_data_permanent_4xx_fails_without_retry(self):
        mock_session = mock.MagicMock(spec=requests.Session)
        mock_session.get.return_value = _make_streaming_response(
            [],
            status_code=404,
        )

        with tempfile.TemporaryDirectory() as tmp_dir:
            with self.assertRaises(RuntimeError):
                data_download.download_full_who_data(
                    output_dir=tmp_dir,
                    max_retries=3,
                    backoff_factor=0.0,
                    session=mock_session,
                )
            mock_session.get.assert_called_once()
            self.assertEqual(os.listdir(tmp_dir), [])

    def test_download_full_who_data_http_error_raises_and_cleans_up(self):
        mock_session = mock.MagicMock(spec=requests.Session)
        mock_session.get.return_value = _make_streaming_response(
            [],
            status_code=503,
        )

        with tempfile.TemporaryDirectory() as tmp_dir:
            with self.assertRaises(RuntimeError):
                data_download.download_full_who_data(
                    output_dir=tmp_dir,
                    backoff_factor=0.0,
                    session=mock_session,
                )
            self.assertEqual(os.listdir(tmp_dir), [])

    def test_download_full_who_data_retries_mid_stream_reset_and_succeeds(self):
        csv_bytes = b'DIM_TIME,RATE_PER_1000_N\n2007,1e-09\n'
        partial_resp = _make_streaming_response(
            [b'DIM_TIME,RATE_PER_1000_N\n'],
            stream_error=requests.exceptions.ConnectionError(
                'connection reset'),
        )
        good_resp = _make_streaming_response([csv_bytes])
        mock_session = mock.MagicMock(spec=requests.Session)
        mock_session.get.side_effect = [partial_resp, good_resp]

        with tempfile.TemporaryDirectory() as tmp_dir:
            out_path = data_download.download_full_who_data(
                output_dir=tmp_dir,
                max_retries=2,
                backoff_factor=0.0,
                session=mock_session,
            )

            self.assertEqual(mock_session.get.call_count, 2)
            self.assertEqual(
                os.listdir(tmp_dir),
                ['adolescent_birth_rate_input.csv'],
            )
            with open(out_path, 'r', encoding='utf-8', newline='') as out_file:
                rows = list(csv.DictReader(out_file))
            self.assertEqual([r['RATE_PER_1000_N'] for r in rows], ['1.0e-09'])

    def test_download_full_who_data_connection_error_raises_and_cleans_partial(
            self):
        partial_resp = _make_streaming_response(
            [b'DIM_TIME,RATE_PER_1000_N\n2024,0.5'],
            stream_error=requests.exceptions.ConnectionError(
                'connection reset'),
        )
        mock_session = mock.MagicMock(spec=requests.Session)
        mock_session.get.return_value = partial_resp

        with tempfile.TemporaryDirectory() as tmp_dir:
            with self.assertRaises(RuntimeError):
                data_download.download_full_who_data(
                    output_dir=tmp_dir,
                    max_retries=1,
                    backoff_factor=0.0,
                    session=mock_session,
                )
            self.assertEqual(mock_session.get.call_count, 2)
            self.assertEqual(os.listdir(tmp_dir), [])

            timeout_session = mock.MagicMock(spec=requests.Session)
            timeout_session.get.side_effect = requests.exceptions.Timeout(
                'timed out')
            with self.assertRaises(RuntimeError):
                data_download.download_full_who_data(
                    output_dir=tmp_dir,
                    max_retries=1,
                    backoff_factor=0.0,
                    session=timeout_session,
                )
            self.assertEqual(os.listdir(tmp_dir), [])

    def test_download_full_who_data_empty_and_header_only_raise_and_cleanup(
            self):
        for payload in (b'', b'IND_ID,DIM_TIME,RATE_PER_1000_N\n'):
            with self.subTest(payload=payload):
                mock_session = mock.MagicMock(spec=requests.Session)
                mock_session.get.return_value = _make_streaming_response(
                    [payload])
                with tempfile.TemporaryDirectory() as tmp_dir:
                    with self.assertRaises(RuntimeError):
                        data_download.download_full_who_data(
                            output_dir=tmp_dir,
                            session=mock_session,
                        )
                    self.assertEqual(os.listdir(tmp_dir), [])

    def test_download_full_who_data_invalid_utf8_raises_and_cleans_up(self):
        bad_bytes = (
            b'IND_ID,DIM_TIME,RATE_PER_1000_N\n27D371A,2024,\xff\xfe0.1\n')
        mock_session = mock.MagicMock(spec=requests.Session)
        mock_session.get.return_value = _make_streaming_response([bad_bytes])

        with tempfile.TemporaryDirectory() as tmp_dir:
            with self.assertRaises(UnicodeDecodeError):
                data_download.download_full_who_data(
                    output_dir=tmp_dir,
                    session=mock_session,
                )
            self.assertEqual(os.listdir(tmp_dir), [])


if __name__ == '__main__':
    unittest.main()

# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import sys
import tempfile
import unittest
from unittest import mock

import requests

_MODULE_DIR = os.path.dirname(__file__)
sys.path.insert(0, _MODULE_DIR)

try:
    from . import download_files as df
except ImportError:
    import download_files as df


def _mock_response(chunks=None, text="", status_error=None):
    resp = mock.MagicMock()
    resp.__enter__ = lambda s: s
    resp.__exit__ = lambda s, *args: False
    if status_error is not None:
        resp.raise_for_status.side_effect = status_error
    if chunks is not None:
        resp.iter_content.return_value = chunks
    resp.text = text
    return resp


class TestDownloadFiles(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.orig_input_path = df._INPUT_FILE_PATH
        self.orig_page_size = df._CENSUS_TRACT_PAGE_SIZE
        df._INPUT_FILE_PATH = self.tmpdir.name

    def tearDown(self):
        df._INPUT_FILE_PATH = self.orig_input_path
        df._CENSUS_TRACT_PAGE_SIZE = self.orig_page_size
        self.tmpdir.cleanup()

    def test_stream_url_to_file_writes_chunks_and_checks_status(self):
        dest = os.path.join(self.tmpdir.name, "streamed.csv")
        resp = _mock_response(chunks=[b"a,b\n", b"", b"1,2\n"])
        with mock.patch.object(df.requests, "get", return_value=resp) as get_fn:
            df._stream_url_to_file("https://example.org/data.csv", dest)

        get_fn.assert_called_once_with("https://example.org/data.csv",
                                       stream=True,
                                       timeout=(30, 300))
        resp.raise_for_status.assert_called_once()
        with open(dest, "rb") as f:
            self.assertEqual(f.read(), b"a,b\n1,2\n")

    def test_stream_url_to_file_raises_on_http_error(self):
        dest = os.path.join(self.tmpdir.name, "err.csv")
        resp = _mock_response(
            status_error=requests.exceptions.HTTPError("503 Server Error"))
        with mock.patch.object(df.requests, "get", return_value=resp):
            with self.assertRaises(requests.exceptions.HTTPError):
                df._stream_url_to_file("https://example.org/err.csv", dest)

    def test_download_paginated_multi_page_and_boundary_newline(self):
        df._CENSUS_TRACT_PAGE_SIZE = 2
        seen_urls = []
        pages = [
            b"col1,col2\n1,a\n2,b",  # No trailing newline on page 0
            b"col1,col2\n3,c\n4,d\n",
            b"col1,col2\n5,e\n",
        ]

        def fake_get(url, stream=True, timeout=None):
            seen_urls.append(url)
            if "COLUMN_ALIAS_GUARD__count" in url:
                return _mock_response(
                    text='[{"COLUMN_ALIAS_GUARD__count": "5"}]')
            idx = len(seen_urls) - 2
            return _mock_response(chunks=[pages[idx]])

        cfg = [{
            "import_name":
                "CDC_OzoneCensusTract",
            "files": [{
                "url": "https://example.org/ozone.csv",
                "input_file_name": "ozone.csv"
            }]
        }]

        with mock.patch.object(df.requests, "get", side_effect=fake_get):
            df.download_files("CDC_OzoneCensusTract", cfg)

        self.assertEqual(seen_urls, [
            "https://example.org/ozone" + df.record_count_query,
            "https://example.org/ozone.csv?$limit=2&$offset=0&$order=:id",
            "https://example.org/ozone.csv?$limit=2&$offset=2&$order=:id",
            "https://example.org/ozone.csv?$limit=1&$offset=4&$order=:id",
        ])
        out_path = os.path.join(self.tmpdir.name, "ozone.csv")
        with open(out_path, "rb") as f:
            self.assertEqual(f.read(), b"col1,col2\n1,a\n2,b\n3,c\n4,d\n5,e\n")

    def test_download_paginated_retries_transient_error_and_incomplete_page(
            self):
        df._CENSUS_TRACT_PAGE_SIZE = 2
        attempt = {"count": 0}

        def fake_get(url, stream=True, timeout=None):
            if "COLUMN_ALIAS_GUARD__count" in url:
                return _mock_response(
                    text='[{"COLUMN_ALIAS_GUARD__count": "2"}]')
            attempt["count"] += 1
            if attempt["count"] == 1:
                raise requests.exceptions.ChunkedEncodingError("dropped")
            if attempt["count"] == 2:
                return _mock_response(chunks=[b"col1,col2\n1,a\n"])
            return _mock_response(chunks=[b"col1,col2\n1,a\n2,b\n"])

        cfg = [{
            "import_name":
                "CDC_PM25CensusTract",
            "files": [{
                "url": "https://example.org/pm25.csv",
                "input_file_name": "pm25.csv"
            }]
        }]

        with mock.patch.object(df.requests, "get", side_effect=fake_get), \
             mock.patch("retry.api.time.sleep"):
            df.download_files("CDC_PM25CensusTract", cfg)

        self.assertEqual(attempt["count"], 3)
        with open(os.path.join(self.tmpdir.name, "pm25.csv"), "rb") as f:
            self.assertEqual(f.read(), b"col1,col2\n1,a\n2,b\n")

    def test_download_paginated_header_mismatch_fails_and_cleans_temp_files(
            self):
        df._CENSUS_TRACT_PAGE_SIZE = 2
        page_calls = {"n": 0}

        def fake_get(url, stream=True, timeout=None):
            if "COLUMN_ALIAS_GUARD__count" in url:
                return _mock_response(
                    text='[{"COLUMN_ALIAS_GUARD__count": "3"}]')
            page_calls["n"] += 1
            if page_calls["n"] == 1:
                return _mock_response(chunks=[b"col1,col2\n1,a\n2,b\n"])
            return _mock_response(chunks=[b"other1,other2\n3,c\n"])

        cfg = [{
            "import_name":
                "CDC_OzoneCensusTract",
            "files": [{
                "url": "https://example.org/ozone.csv",
                "input_file_name": "ozone.csv"
            }]
        }]

        with mock.patch.object(df.requests, "get", side_effect=fake_get), \
             mock.patch("retry.api.time.sleep"), \
             mock.patch.object(df.logging, "fatal", side_effect=RuntimeError("fatal")):
            with self.assertRaises(RuntimeError):
                df.download_files("CDC_OzoneCensusTract", cfg)

        self.assertEqual(page_calls["n"],
                         6)  # 1 for page0 + 5 retries for page1
        self.assertFalse(
            os.path.exists(os.path.join(self.tmpdir.name, "ozone.csv")))
        self.assertFalse(
            os.path.exists(os.path.join(self.tmpdir.name, "ozone.csv.tmp")))
        self.assertFalse(
            os.path.exists(os.path.join(self.tmpdir.name,
                                        "ozone.csv.tmp.page")))

    def test_download_paginated_non_transient_error_fails_fast(self):
        df._CENSUS_TRACT_PAGE_SIZE = 2
        page_calls = {"n": 0}

        def fake_get(url, stream=True, timeout=None):
            if "COLUMN_ALIAS_GUARD__count" in url:
                return _mock_response(
                    text='[{"COLUMN_ALIAS_GUARD__count": "2"}]')
            page_calls["n"] += 1
            raise KeyError("unexpected key error")

        cfg = [{
            "import_name":
                "CDC_PM25CensusTract",
            "files": [{
                "url": "https://example.org/pm25.csv",
                "input_file_name": "pm25.csv"
            }]
        }]

        with mock.patch.object(df.requests, "get", side_effect=fake_get), \
             mock.patch("retry.api.time.sleep"), \
             mock.patch.object(df.logging, "fatal", side_effect=RuntimeError("fatal")):
            with self.assertRaises(RuntimeError):
                df.download_files("CDC_PM25CensusTract", cfg)

        self.assertEqual(page_calls["n"], 1)

    def test_county_import_routes_to_single_stream_download(self):
        seen_urls = []

        def fake_get(url, stream=True, timeout=None):
            seen_urls.append(url)
            if "COLUMN_ALIAS_GUARD__count" in url:
                return _mock_response(
                    text='[{"COLUMN_ALIAS_GUARD__count": "2"}]')
            return _mock_response(chunks=[b"col1,col2\n1,a\n2,b\n"])

        cfg = [{
            "import_name":
                "CDC_PM25County",
            "files": [{
                "url": "https://example.org/county.csv",
                "input_file_name": "county.csv"
            }]
        }]

        with mock.patch.object(df.requests, "get", side_effect=fake_get):
            df.download_files("CDC_PM25County", cfg)

        self.assertEqual(seen_urls, [
            "https://example.org/county" + df.record_count_query,
            "https://example.org/county.csv?$limit=2&$offset=0",
        ])
        with open(os.path.join(self.tmpdir.name, "county.csv"), "rb") as f:
            self.assertEqual(f.read(), b"col1,col2\n1,a\n2,b\n")


if __name__ == "__main__":
    unittest.main()

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
"""Unit tests for Brazil Census Table 9514 download module."""

import os
import shutil
import sys
import tempfile
import unittest
from unittest.mock import MagicMock

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

import pandas as pd
import requests

from download import (
    FLAGS,
    download_table_9514,
    get_robust_session,
)


class DownloadTest(unittest.TestCase):
    """Unit test suite for Table 9514 downloader."""

    def setUp(self):
        super().setUp()
        FLAGS.mark_as_parsed()
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)
        super().tearDown()

    def test_robust_session_configuration(self):
        """Verifies session retry configuration includes 429 and 5xx error codes."""
        session = get_robust_session()
        self.assertIsInstance(session, requests.Session)
        adapter = session.adapters.get("https://")
        self.assertIsNotNone(adapter)
        self.assertEqual(adapter.max_retries.total, 10)
        self.assertIn(429, adapter.max_retries.status_forcelist)
        self.assertIn(500, adapter.max_retries.status_forcelist)
        self.assertIn(503, adapter.max_retries.status_forcelist)

    def test_download_table_9514_mocked_success(self):
        """Tests successful download and CSV emission."""
        session = MagicMock()
        mock_response = MagicMock()
        mock_payload = [
            {
                "NC": "Nível Territorial (Código)"
            },
            {
                "NC": "1",
                "D1N": "Brasil",
                "D3N": "2022",
                "D4N": "Total",
                "D5N": "Total",
                "V": "203080756",
            },
            {
                "NC": "1",
                "D1N": "Brasil",
                "D3N": "2022",
                "D4N": "Homens",
                "D5N": "0 a 4 anos",
                "V": "6461689",
            },
        ]
        mock_response.json.return_value = mock_payload
        mock_response.raise_for_status.return_value = None
        session.get.return_value = mock_response

        out_csv = os.path.join(self.test_dir, "output.csv")
        saved_file = download_table_9514(session=session, output_file=out_csv)
        self.assertTrue(os.path.isfile(saved_file))

        df = pd.read_csv(saved_file)
        self.assertEqual(len(df), 2)
        self.assertEqual(list(df.columns),
                         ["Ano", "Localidade", "Idade", "Sexo", "Populacao"])
        self.assertEqual(df["Localidade"].iloc[0], "Brasil")
        self.assertEqual(df["Populacao"].iloc[0], 203080756)

    def test_download_table_9514_empty_response_raises(self):
        """Tests that an empty response payload raises RuntimeError."""
        session = MagicMock()
        mock_response = MagicMock()
        mock_response.json.return_value = []
        mock_response.raise_for_status.return_value = None
        session.get.return_value = mock_response

        out_csv = os.path.join(self.test_dir, "output.csv")
        with self.assertRaises(RuntimeError) as ctx:
            download_table_9514(session=session, output_file=out_csv)
        self.assertIn("Invalid or empty response payload", str(ctx.exception))

    def test_download_table_9514_network_failure_raises(self):
        """Tests that network error raises RuntimeError when fallback is disabled."""
        session = MagicMock()
        session.get.side_effect = requests.ConnectionError(
            "Connection timed out")

        out_csv = os.path.join(self.test_dir, "output.csv")
        with self.assertRaises(RuntimeError) as ctx:
            download_table_9514(session=session,
                                output_file=out_csv,
                                fallback_to_cached=False)
        self.assertIn("Network error fetching Table 9514", str(ctx.exception))

    def test_download_table_9514_fallback_to_cached(self):
        """Tests that fallback to existing CSV succeeds when fallback is enabled."""
        session = MagicMock()
        session.get.side_effect = requests.HTTPError("503 Service Unavailable")

        cached_csv = os.path.join(self.test_dir, "cached.csv")
        with open(cached_csv, "w", encoding="utf-8") as f:
            f.write(
                "Ano,Localidade,Idade,Sexo,Populacao\n2022,Brasil,Total,Total,100\n"
            )

        saved = download_table_9514(session=session,
                                    output_file=cached_csv,
                                    fallback_to_cached=True)
        self.assertEqual(saved, cached_csv)
        self.assertTrue(os.path.isfile(saved))


if __name__ == "__main__":
    unittest.main()

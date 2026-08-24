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

"""Unit tests for brazil_download_script."""

import os
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, call, patch

import pandas as pd
import requests

# Add the script's directory to sys.path so modules can be imported directly
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if _SCRIPT_DIR not in sys.path:
    sys.path.insert(0, _SCRIPT_DIR)

import brazil_download_script
import panel_specs


class BrazilDownloadScriptTest(unittest.TestCase):

    def test_get_robust_session_configuration(self):
        """Verifies session retry configuration includes HTTP 429 and server error codes."""
        session = brazil_download_script.get_robust_session()
        self.assertIsInstance(session, requests.Session)
        adapter = session.adapters.get("https://")
        self.assertIsNotNone(adapter)
        self.assertIsNotNone(adapter.max_retries)
        self.assertEqual(adapter.max_retries.total, 10)
        self.assertEqual(adapter.max_retries.backoff_factor, 1)
        expected_status_codes = {429, 500, 502, 503, 504}
        self.assertTrue(expected_status_codes.issubset(set(adapter.max_retries.status_forcelist)))

    @patch("brazil_download_script.SESSION.get")
    def test_get_available_periods_success(self, mock_get):
        """Tests successful retrieval and filtering of period metadata."""
        mock_response = MagicMock()
        mock_response.json.return_value = [
            {"id": "202103", "literals": ["3º trimestre 2021"]},
            {"id": "202104", "literals": ["4º trimestre 2021"]},
            {"id": "202201", "literals": ["1º trimestre 2022"]},
            {"id": "202202", "literals": ["2º trimestre 2022"]},
            {"id": "202203", "literals": ["3º trimestre 2022"]},
        ]
        mock_get.return_value = mock_response

        periods = brazil_download_script.get_available_periods()
        self.assertEqual(len(periods), 3)
        self.assertEqual([p["id"] for p in periods], ["202201", "202202", "202203"])

    @patch("brazil_download_script.SESSION.get")
    def test_get_available_periods_empty_or_invalid_json(self, mock_get):
        """Tests that empty or non-list response raises RuntimeError."""
        mock_response = MagicMock()
        mock_response.json.return_value = []
        mock_get.return_value = mock_response

        with self.assertRaises(RuntimeError):
            brazil_download_script.get_available_periods()

        mock_response.json.return_value = {"error": "Not found"}
        with self.assertRaises(RuntimeError):
            brazil_download_script.get_available_periods()

    @patch("brazil_download_script.SESSION.get")
    def test_get_available_periods_no_periods_gte_start(self, mock_get):
        """Tests that having no periods >= PERIOD_START raises RuntimeError."""
        mock_response = MagicMock()
        mock_response.json.return_value = [
            {"id": "202001", "literals": ["1º trimestre 2020"]},
            {"id": "202104", "literals": ["4º trimestre 2021"]},
        ]
        mock_get.return_value = mock_response

        with self.assertRaises(RuntimeError):
            brazil_download_script.get_available_periods()

    @patch("brazil_download_script.SESSION.get")
    def test_get_available_periods_network_error(self, mock_get):
        """Tests that network error raises RuntimeError."""
        mock_get.side_effect = requests.exceptions.ConnectionError("Connection refused")
        with self.assertRaises(RuntimeError):
            brazil_download_script.get_available_periods()

    @patch("brazil_download_script.SESSION.get")
    def test_get_available_periods_json_decode_error(self, mock_get):
        """Tests that invalid JSON response raises RuntimeError."""
        mock_response = MagicMock()
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_get.return_value = mock_response

        with self.assertRaises(RuntimeError):
            brazil_download_script.get_available_periods()

    def test_format_quarter_label_from_literals(self):
        """Tests formatting quarter label from literals list."""
        period_item = {
            "id": "202201",
            "literals": ["PNAD Contínua", "1º TRIMESTRE 2022"]
        }
        label = brazil_download_script.format_quarter_label(period_item)
        self.assertEqual(label, "1º trimestre 2022")

    def test_format_quarter_label_fallback_id(self):
        """Tests fallback formatting from YYYYQQ id."""
        period_item = {"id": "202304", "literals": []}
        label = brazil_download_script.format_quarter_label(period_item)
        self.assertEqual(label, "4º trimestre 2023")

    def test_format_quarter_label_fallback_on_error(self):
        """Tests fallback behavior when formatting raises an exception."""
        period_item = {"id": "custom_period", "literals": None}
        label = brazil_download_script.format_quarter_label(period_item)
        self.assertEqual(label, "custom_period")

        with self.assertRaises(RuntimeError):
            brazil_download_script.format_quarter_label({"literals": None})

    @patch("brazil_download_script.SESSION.get")
    def test_fetch_aggregate_series_unclassified(self, mock_get):
        """Tests fetching unclassified series mapped to 'Total'."""
        mock_response = MagicMock()
        mock_response.json.return_value = [
            {
                "id": "4096",
                "variavel": "Taxa de participação",
                "unidade": "%",
                "resultados": [
                    {
                        "classificacoes": [],
                        "series": [
                            {
                                "localidade": {"id": "1", "nome": "Brasil"},
                                "serie": {"202201": "62.1", "202202": "62.6"}
                            }
                        ]
                    }
                ]
            }
        ]
        mock_get.return_value = mock_response

        result = brazil_download_script.fetch_aggregate_series(6461, 4096, "N1[1]", "202201|202202")
        self.assertIn("Total", result)
        self.assertEqual(result["Total"], {"202201": "62.1", "202202": "62.6"})

    @patch("brazil_download_script.SESSION.get")
    def test_fetch_aggregate_series_classified(self, mock_get):
        """Tests fetching classified series with category key extraction."""
        mock_response = MagicMock()
        mock_response.json.return_value = [
            {
                "id": "1641",
                "resultados": [
                    {
                        "classificacoes": [
                            {"id": "629", "categoria": {"32385": "Pessoas de 14 anos ou mais"}}
                        ],
                        "series": [
                            {"serie": {"202201": "175000", "202202": "176000"}}
                        ]
                    },
                    {
                        "classificacoes": [
                            {"id": "629", "categoria": {"32386": "Na força de trabalho"}}
                        ],
                        "series": [
                            {"serie": {"202201": "105000", "202202": "106000"}}
                        ]
                    }
                ]
            }
        ]
        mock_get.return_value = mock_response

        result = brazil_download_script.fetch_aggregate_series(
            6463, 1641, "N1[1]", "202201|202202", classif="629[all]"
        )
        self.assertIn("32385", result)
        self.assertIn("32386", result)
        self.assertEqual(result["32385"]["202201"], "175000")
        self.assertEqual(result["32386"]["202202"], "106000")

    @patch("brazil_download_script.SESSION.get")
    def test_fetch_aggregate_series_invalid_structure(self, mock_get):
        """Tests that invalid API response payload raises RuntimeError."""
        mock_response = MagicMock()
        mock_response.json.return_value = []
        mock_get.return_value = mock_response

        with self.assertRaises(RuntimeError):
            brazil_download_script.fetch_aggregate_series(6461, 4096, "N1[1]", "202201")

        mock_response.json.return_value = [{"empty": "structure"}]
        with self.assertRaises(RuntimeError):
            brazil_download_script.fetch_aggregate_series(6461, 4096, "N1[1]", "202201")

    @patch("brazil_download_script.SESSION.get")
    def test_fetch_aggregate_series_network_error(self, mock_get):
        """Tests that network request error raises RuntimeError."""
        mock_get.side_effect = requests.exceptions.Timeout("Request timed out")
        with self.assertRaises(RuntimeError):
            brazil_download_script.fetch_aggregate_series(6461, 4096, "N1[1]", "202201")

    @patch("brazil_download_script.fetch_aggregate_series")
    def test_fetch_panel_data_all_panels(self, mock_fetch):
        """Tests data fetching, matrix construction, and Excel writing for panels 1 through 4."""
        mock_fetch.return_value = {
            "Total": {"202201": "100", "202202": "105"},
            "32385": {"202201": "200", "202202": "205"},
            "32386": {"202201": "300", "202202": "305"},
            "32387": {"202201": "400", "202202": "405"},
            "32446": {"202201": "500", "202202": "505"},
            "32447": {"202201": "600", "202202": "605"},
            "31722": {"202201": "700", "202202": "705"},
            "31723": {"202201": "800", "202202": "805"},
            "31724": {"202201": "900", "202202": "905"},
            "31727": {"202201": "1000", "202202": "1005"},
            "96170": {"202201": "1100", "202202": "1105"},
            "96171": {"202201": "1200", "202202": "1205"},
            "31731": {"202201": "1300", "202202": "1305"},
            "47947": {"202201": "1400", "202202": "1405"},
            "47948": {"202201": "1500", "202202": "1505"},
            "47949": {"202201": "1600", "202202": "1605"},
            "47950": {"202201": "1700", "202202": "1705"},
            "56622": {"202201": "1800", "202202": "1805"},
            "56623": {"202201": "1900", "202202": "1905"},
            "56624": {"202201": "2000", "202202": "2005"},
            "60032": {"202201": "2100", "202202": "2105"},
            "56627": {"202201": "2200", "202202": "2205"},
            "56628": {"202201": "2300", "202202": "2305"},
            "96165": {"202201": "2400", "202202": "2405"},
        }

        periods = [
            {"id": "202201", "literals": ["1º trimestre 2022"]},
            {"id": "202202", "literals": ["2º trimestre 2022"]},
        ]

        with tempfile.TemporaryDirectory() as tmp_dir:
            with patch.object(brazil_download_script, "DOWNLOAD_DIR", tmp_dir):
                for panel_idx in range(1, 5):
                    brazil_download_script.fetch_panel_data("Brasil", "N1[1]", panel_idx, periods)
                    folder_name = brazil_download_script.PANEL_FOLDER_MAP[panel_idx]
                    expected_filename = f"Brasil_Panel_{panel_idx}_Pesquisa Nacional por Amostra de Domicílios Contínua - Divulgação Trimestral.xlsx"
                    file_path = os.path.join(tmp_dir, folder_name, expected_filename)
                    self.assertTrue(os.path.exists(file_path), f"File {file_path} was not created.")

                    # Verify generated Excel file contents
                    df = pd.read_excel(file_path, header=None)
                    self.assertGreater(len(df), 5)
                    self.assertEqual(df.iloc[0, 0], "Pesquisa Nacional por Amostra de Domicílios Contínua - Divulgação Trimestral")
                    self.assertEqual(df.iloc[2, 0], "Brasil")

    def test_fetch_panel_data_invalid_index(self):
        """Tests that invalid panel index raises ValueError."""
        periods = [{"id": "202201", "literals": ["1º trimestre 2022"]}]
        with self.assertRaises(ValueError):
            brazil_download_script.fetch_panel_data("Brasil", "N1[1]", 99, periods)

    @patch("brazil_download_script.time.sleep")
    @patch("brazil_download_script.fetch_panel_data")
    @patch("brazil_download_script.get_available_periods")
    def test_main_orchestration(self, mock_get_periods, mock_fetch_panel, mock_sleep):
        """Tests the end-to-end main orchestration loop."""
        mock_get_periods.return_value = [
            {"id": "202201", "literals": ["1º trimestre 2022"]}
        ]

        with tempfile.TemporaryDirectory() as tmp_dir:
            with patch.object(brazil_download_script, "DOWNLOAD_DIR", tmp_dir):
                brazil_download_script.main(None)

        mock_get_periods.assert_called_once()
        expected_call_count = len(panel_specs.LOCATIONS) * 4
        self.assertEqual(mock_fetch_panel.call_count, expected_call_count)


if __name__ == "__main__":
    unittest.main()

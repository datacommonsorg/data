import os
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, patch
import pandas as pd
import requests

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from download_input_data import (
    AGE_STEMS,
    LOC_STEMS,
    SEX_STEMS,
    download_and_process,
    fetch_variables,
    get_http_session,
    get_template_map,
    load_template_from_gcs,
    make_request,
)


class DownloadInputDataTest(unittest.TestCase):

    def test_get_template_map(self):
        index = pd.MultiIndex.from_tuples([('0000000', 'POLAND'),
                                           ('0200000', 'DOLNOŚLĄSKIE'),
                                           ('0400000', 'Kujawsko-Pomorskie')],
                                          names=['Code', 'Name'])
        df = pd.DataFrame(index=index)
        t_map = get_template_map(df)
        self.assertEqual(t_map['POLAND'], '0000000')
        self.assertEqual(t_map['DOLNOŚLĄSKIE'], '0200000')
        self.assertEqual(t_map['KUJAWSKO-POMORSKIE'], '0400000')

    def test_get_http_session(self):
        session = get_http_session(retries=3, backoff_factor=0.5)
        self.assertIsNotNone(session)
        self.assertIn('https://', session.adapters)
        adapter = session.adapters['https://']
        self.assertEqual(adapter.max_retries.total, 3)

    def test_stems_definitions(self):
        self.assertEqual(AGE_STEMS['0-2'], '0-2')
        self.assertEqual(AGE_STEMS['65 and more'], '65')
        self.assertIn('męż', SEX_STEMS['males'])
        self.assertIn('kob', SEX_STEMS['females'])
        self.assertIn('miast', LOC_STEMS['in urban areas'])
        self.assertIn('wsi', LOC_STEMS['in rural areas'])

    @patch('download_input_data.storage.Client')
    def test_load_template_from_gcs_success(self, mock_storage_client):
        # Hermetic test: GCS client returns valid template CSV
        mock_blob = MagicMock()
        sample_csv = ("Age,,0-2,0-2\n"
                      "Sex,,total,males\n"
                      "Location,,total,total\n"
                      "Year,,2024,2024\n"
                      "Code,Name,,\n"
                      "0000000,POLAND,100,50\n")
        mock_blob.download_as_text.return_value = sample_csv
        mock_bucket = MagicMock()
        mock_bucket.blob.return_value = mock_blob
        mock_storage_client.return_value.bucket.return_value = mock_bucket

        df = load_template_from_gcs("gs://test-bucket/test-template.csv")
        self.assertIsNotNone(df)
        self.assertEqual(df.columns.nlevels, 4)
        self.assertEqual(df.index.nlevels, 2)
        self.assertEqual(len(df), 1)

    @patch('download_input_data.storage.Client')
    def test_load_template_from_gcs_fallback(self, mock_storage_client):
        # Hermetic test: GCS failure triggers local fallback without live network calls
        mock_storage_client.side_effect = RuntimeError(
            "GCS Unreachable in offline CI")

        df = load_template_from_gcs(
            "gs://non-existent-bucket/non-existent-file.csv")
        self.assertIsNotNone(df)
        self.assertEqual(df.columns.nlevels, 4)
        self.assertEqual(df.index.nlevels, 2)

    def test_make_request_headers_redaction_and_error(self):
        session = MagicMock()
        mock_resp = requests.Response()
        mock_resp.status_code = 200
        session.get.return_value = mock_resp

        headers = {
            'X-ClientId': 'secret-key-123',
            'Accept': 'application/json'
        }
        resp = make_request(session,
                            'https://example.com/api',
                            headers=headers)
        self.assertIsNotNone(resp)
        self.assertEqual(resp.status_code, 200)

        # Exception during request returns None
        session.get.side_effect = requests.RequestException("Connection error")
        failed_resp = make_request(session, 'https://example.com/api')
        self.assertIsNone(failed_resp)

    def test_response_status_code_logging_not_none_on_http_error(self):
        # Verify that non-200 responses log their integer status code and raise RuntimeError
        session = MagicMock()
        mock_resp = requests.Response()
        mock_resp.status_code = 403
        session.get.return_value = mock_resp

        with self.assertLogs(level='ERROR') as cm:
            with self.assertRaises(RuntimeError):
                fetch_variables(session)
            self.assertTrue(
                any("status 403" in log for log in cm.output),
                f"Expected 'status 403' in logs, got: {cm.output}")

    def test_fetch_variables_mocked(self):
        session = MagicMock()
        mock_resp = requests.Response()
        mock_resp.status_code = 200
        mock_resp._content = b'{"results": [{"id": 101, "n1": "ludnosc", "n2": "0-2 mezczyzni"}]}'
        session.get.return_value = mock_resp

        v_map = fetch_variables(session)
        self.assertEqual(len(v_map), 1)
        self.assertIn("101", v_map)
        self.assertEqual(v_map["101"], "ludnosc 0-2 mezczyzni")

    @patch('download_input_data.fetch_variables')
    @patch('download_input_data.load_template_from_gcs')
    @patch('download_input_data.make_request')
    def test_download_and_process_mocked(self, mock_make_request,
                                         mock_load_template, mock_fetch):
        # Hermetic end-to-end processing test using mocked GUS API data and local tempdir
        template_index = pd.MultiIndex.from_tuples(
            [('0000000', 'POLAND'), ('0200000', 'DOLNOŚLĄSKIE')],
            names=['Code', 'Name'])
        template_columns = pd.MultiIndex.from_tuples(
            [
                ('0-2', 'total', 'total', '2024'),
                ('0-2', 'males', 'total', '2024'),
                ('total', 'total', 'total', '2024'),
            ],
            names=['Age', 'Sex', 'Location', 'Year'])
        template_df = pd.DataFrame(10,
                                   index=template_index,
                                   columns=template_columns)
        mock_load_template.return_value = template_df

        # Variable 101: 0-2 males, Variable 102: 0-2 total
        mock_fetch.return_value = {
            '101': 'ludność 0-2 męż',
            '102': 'ludność 0-2'
        }

        # Mock data API responses for variable 101 and 102
        def side_effect(session, url, headers=None, params=None, timeout=60):
            r = requests.Response()
            r.status_code = 200
            if '101' in url:
                r._content = b'''{
                    "results": [
                        {"name": "POLSKA", "values": [{"year": 2024, "val": 50}]},
                        {
                            "name": "DOLNO\xc5\x9aL\xc4\x84SKIE",
                            "values": [{"year": 2024, "val": 20}]
                        }
                    ]
                }'''
            elif '102' in url:
                r._content = b'''{
                    "results": [
                        {"name": "POLSKA", "values": [{"year": 2024, "val": 100}]},
                        {
                            "name": "DOLNO\xc5\x9aL\xc4\x84SKIE",
                            "values": [{"year": 2024, "val": 40}]
                        }
                    ]
                }'''
            else:
                r.status_code = 404
            return r

        mock_make_request.side_effect = side_effect

        with tempfile.TemporaryDirectory() as temp_dir:
            with patch('download_input_data.OUTPUT_DIR', temp_dir):
                download_and_process()
                output_csv = os.path.join(temp_dir,
                                          "StatisticsPoland_input_2024.csv")
                self.assertTrue(os.path.exists(output_csv))

                result_df = pd.read_csv(output_csv,
                                        header=[0, 1, 2, 3],
                                        index_col=[0, 1],
                                        dtype={
                                            0: str,
                                            1: str
                                        })
                self.assertEqual(result_df.index.nlevels, 2)
                self.assertEqual(result_df.columns.nlevels, 4)
                self.assertIn(('0000000', 'POLAND'), result_df.index)
                self.assertIn(('0200000', 'DOLNOŚLĄSKIE'), result_df.index)

    @patch('download_input_data.fetch_variables')
    @patch('download_input_data.load_template_from_gcs')
    def test_download_and_process_raises_on_unmapped_slice(
            self, mock_load_template, mock_fetch):
        template_index = pd.MultiIndex.from_tuples([('0000000', 'POLAND')],
                                                   names=['Code', 'Name'])
        template_columns = pd.MultiIndex.from_tuples(
            [('0-2', 'total', 'total', '2024')],
            names=['Age', 'Sex', 'Location', 'Year'])
        mock_load_template.return_value = pd.DataFrame(
            10, index=template_index, columns=template_columns)
        # Slices present in template but unmatched in metadata
        mock_fetch.return_value = {'999': 'unrelated_variable'}

        with self.assertRaises(RuntimeError) as ctx:
            download_and_process()
        self.assertIn("Failed to match variable for slice", str(ctx.exception))

    @patch('download_input_data.fetch_variables')
    @patch('download_input_data.load_template_from_gcs')
    @patch('download_input_data.make_request')
    def test_download_and_process_raises_on_download_failure(
            self, mock_make_request, mock_load_template, mock_fetch):
        template_index = pd.MultiIndex.from_tuples([('0000000', 'POLAND')],
                                                   names=['Code', 'Name'])
        template_columns = pd.MultiIndex.from_tuples(
            [('0-2', 'total', 'total', '2024')],
            names=['Age', 'Sex', 'Location', 'Year'])
        mock_load_template.return_value = pd.DataFrame(
            10, index=template_index, columns=template_columns)
        mock_fetch.return_value = {'102': 'ludność 0-2'}

        # Mock download returning 500 error
        mock_resp = requests.Response()
        mock_resp.status_code = 500
        mock_make_request.return_value = mock_resp

        with self.assertRaises(RuntimeError) as ctx:
            download_and_process()
        self.assertIn("Download failed with status 500", str(ctx.exception))


if __name__ == '__main__':
    unittest.main()

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

from pathlib import Path
import tempfile
import unittest
from unittest import mock

from google.api_core import exceptions
import requests

try:
    from statvar_imports.nyu_diabetes.tennessee import download
except ModuleNotFoundError:
    import download


class DownloadTest(unittest.TestCase):

    def test_generate_urls_for_tn_and_gcs(self):
        tn_template = 'https://tn.example/{year}/Diabetes_County_{year}.xlsx'
        gcs_template = 'gs://test-bucket/input/Diabetes_County_{year}.xlsx'

        self.assertEqual(download.generate_urls(2019, 2020, tn_template), [
            'https://tn.example/2019/Diabetes_County_2019.xlsx',
            'https://tn.example/2020/Diabetes_County_2020.xlsx',
        ])
        self.assertEqual(download.generate_urls(2019, 2020, gcs_template), [
            'gs://test-bucket/input/Diabetes_County_2019.xlsx',
            'gs://test-bucket/input/Diabetes_County_2020.xlsx',
        ])

    @mock.patch.object(download.storage, 'Client')
    def test_gcs_download_skips_missing_file(self, mock_client):
        downloaded_blob = mock.Mock()
        downloaded_blob.download_to_filename.side_effect = (
            lambda path: Path(path).write_bytes(b'new data'))
        missing_blob = mock.Mock()
        missing_blob.download_to_filename.side_effect = exceptions.NotFound(
            'not found')
        mock_client.return_value.bucket.return_value.blob.side_effect = [
            downloaded_blob,
            missing_blob,
        ]
        urls = [
            'gs://test-bucket/input/Diabetes_County_2019.xlsx',
            'gs://test-bucket/input/Diabetes_County_2020.xlsx',
        ]

        with tempfile.TemporaryDirectory() as temp_dir:
            existing_file = Path(temp_dir) / 'Diabetes_County_2020.xlsx'
            existing_file.write_bytes(b'existing data')

            download.download_files_from_gcs(urls, temp_dir)

            self.assertEqual(
                (Path(temp_dir) / 'Diabetes_County_2019.xlsx').read_bytes(),
                b'new data')
            self.assertTrue(existing_file.exists())
            self.assertEqual(existing_file.read_bytes(), b'existing data')
            self.assertFalse(
                (Path(temp_dir) / 'Diabetes_County_2019.xlsx.tmp').exists())
            self.assertFalse(
                (Path(temp_dir) / 'Diabetes_County_2020.xlsx.tmp').exists())

    @mock.patch.object(download.storage, 'Client')
    def test_gcs_download_fails_when_no_files_exist(self, mock_client):
        blob = mock_client.return_value.bucket.return_value.blob.return_value
        blob.download_to_filename.side_effect = exceptions.NotFound('not found')

        with tempfile.TemporaryDirectory() as temp_dir:
            with self.assertRaisesRegex(RuntimeError,
                                        'No files were downloaded from GCS'):
                download.download_files_from_gcs(
                    ['gs://test-bucket/input/Diabetes_County_2019.xlsx'],
                    temp_dir)

    @mock.patch.object(download.storage, 'Client')
    def test_gcs_download_propagates_unexpected_error(self, mock_client):
        blob = mock_client.return_value.bucket.return_value.blob.return_value
        blob.download_to_filename.side_effect = exceptions.Forbidden(
            'permission denied')

        with tempfile.TemporaryDirectory() as temp_dir:
            with self.assertRaises(exceptions.Forbidden):
                download.download_files_from_gcs(
                    ['gs://test-bucket/input/Diabetes_County_2019.xlsx'],
                    temp_dir)

    @mock.patch.object(download, 'date')
    @mock.patch.object(download, 'create_retry_session')
    def test_download_files_skips_unreleased_year_404(self,
                                                      mock_session_factory,
                                                      mock_date):
        mock_date.today.return_value.year = 2026
        mock_session = mock.Mock()
        mock_resp_success = mock.Mock()
        mock_resp_success.status_code = 200
        mock_resp_success.headers = {'content-length': '8'}
        mock_resp_success.iter_content.return_value = [b'content!']
        mock_resp_success.__enter__ = mock.Mock(return_value=mock_resp_success)
        mock_resp_success.__exit__ = mock.Mock(return_value=False)

        mock_resp_404 = mock.Mock()
        mock_resp_404.status_code = 404

        mock_session.get.side_effect = [mock_resp_success, mock_resp_404]
        mock_session_factory.return_value = mock_session

        with tempfile.TemporaryDirectory() as temp_dir:
            urls = [
                'https://tn.example/2022/Diabetes_County_2022.xlsx',
                'https://tn.example/2024/Diabetes_County_2024.xlsx',
            ]
            download.download_files(urls, temp_dir)
            self.assertTrue(
                (Path(temp_dir) / 'Diabetes_County_2022.xlsx').exists())
        mock_resp_404.close.assert_called_once()
        mock_session.close.assert_called_once()

    @mock.patch.object(download, 'date')
    @mock.patch.object(download, 'create_retry_session')
    def test_download_files_raises_on_due_year_404(self, mock_session_factory,
                                                   mock_date):
        mock_date.today.return_value.year = 2026
        mock_session = mock.Mock()
        mock_resp_success = mock.Mock()
        mock_resp_success.status_code = 200
        mock_resp_success.headers = {'content-length': '8'}
        mock_resp_success.iter_content.return_value = [b'content!']
        mock_resp_success.__enter__ = mock.Mock(return_value=mock_resp_success)
        mock_resp_success.__exit__ = mock.Mock(return_value=False)

        mock_resp_404 = mock.Mock()
        mock_resp_404.status_code = 404

        mock_session.get.side_effect = [mock_resp_success, mock_resp_404]
        mock_session_factory.return_value = mock_session

        with tempfile.TemporaryDirectory() as temp_dir:
            urls = [
                'https://tn.example/2022/Diabetes_County_2022.xlsx',
                'https://tn.example/2020/Diabetes_County_2020.xlsx',
            ]
            with self.assertRaises(requests.exceptions.HTTPError):
                download.download_files(urls, temp_dir)
        mock_resp_404.close.assert_called_once()
        mock_session.close.assert_called_once()

    @mock.patch.object(download, 'create_retry_session')
    def test_download_files_raises_on_initial_404(self, mock_session_factory):
        mock_session = mock.Mock()
        mock_response = mock.Mock()
        mock_response.status_code = 404
        mock_session.get.return_value = mock_response
        mock_session_factory.return_value = mock_session

        with tempfile.TemporaryDirectory() as temp_dir:
            with self.assertRaises(requests.exceptions.HTTPError):
                download.download_files(
                    ['https://tn.example/2023/Diabetes_County_2023.xlsx'],
                    temp_dir)
        mock_response.close.assert_called_once()
        mock_session.close.assert_called_once()

    @mock.patch.object(download, 'create_retry_session')
    def test_download_files_cleans_up_on_unexpected_exception(
            self, mock_session_factory):
        mock_session = mock.Mock()
        mock_resp = mock.Mock()
        mock_resp.status_code = 200
        mock_resp.headers = {'content-length': '8'}
        mock_resp.iter_content.side_effect = OSError('Disk full')
        mock_resp.__enter__ = mock.Mock(return_value=mock_resp)
        mock_resp.__exit__ = mock.Mock(return_value=False)
        mock_session.get.return_value = mock_resp
        mock_session_factory.return_value = mock_session

        with tempfile.TemporaryDirectory() as temp_dir:
            with self.assertRaises(OSError):
                download.download_files(
                    ['https://tn.example/2022/Diabetes_County_2022.xlsx'],
                    temp_dir)
            self.assertFalse(
                (Path(temp_dir) / 'Diabetes_County_2022.xlsx').exists())
        mock_resp.close.assert_called_once()
        mock_session.close.assert_called_once()

    @mock.patch.object(download, 'date')
    @mock.patch.object(download, 'create_retry_session')
    def test_download_files_raises_on_future_year_error(self,
                                                        mock_session_factory,
                                                        mock_date):
        mock_date.today.return_value.year = 2026
        mock_session = mock.Mock()
        mock_resp_success = mock.Mock()
        mock_resp_success.status_code = 200
        mock_resp_success.headers = {'content-length': '8'}
        mock_resp_success.iter_content.return_value = [b'content!']
        mock_resp_success.__enter__ = mock.Mock(return_value=mock_resp_success)
        mock_resp_success.__exit__ = mock.Mock(return_value=False)

        mock_session.get.side_effect = [
            mock_resp_success,
            requests.exceptions.ConnectionError('reset by peer'),
        ]
        mock_session_factory.return_value = mock_session

        with tempfile.TemporaryDirectory() as temp_dir:
            partial_file = Path(temp_dir) / 'Diabetes_County_2024.xlsx'
            partial_file.write_bytes(b'partial corrupt data')

            urls = [
                'https://tn.example/2022/Diabetes_County_2022.xlsx',
                'https://tn.example/2024/Diabetes_County_2024.xlsx',
            ]
            with self.assertRaises(requests.exceptions.ConnectionError):
                download.download_files(urls, temp_dir)
            self.assertTrue(
                (Path(temp_dir) / 'Diabetes_County_2022.xlsx').exists())
            self.assertFalse(partial_file.exists())

    @mock.patch.object(download, 'date')
    @mock.patch.object(download, 'create_retry_session')
    def test_download_files_raises_on_due_year_error(self, mock_session_factory,
                                                     mock_date):
        mock_date.today.return_value.year = 2026
        mock_session = mock.Mock()
        mock_resp_success = mock.Mock()
        mock_resp_success.status_code = 200
        mock_resp_success.headers = {'content-length': '8'}
        mock_resp_success.iter_content.return_value = [b'content!']
        mock_resp_success.__enter__ = mock.Mock(return_value=mock_resp_success)
        mock_resp_success.__exit__ = mock.Mock(return_value=False)

        mock_session.get.side_effect = [
            mock_resp_success,
            requests.exceptions.ConnectionError('reset by peer'),
        ]
        mock_session_factory.return_value = mock_session

        with tempfile.TemporaryDirectory() as temp_dir:
            partial_file = Path(temp_dir) / 'Diabetes_County_2023.xlsx'
            partial_file.write_bytes(b'partial corrupt data')

            urls = [
                'https://tn.example/2022/Diabetes_County_2022.xlsx',
                'https://tn.example/2023/Diabetes_County_2023.xlsx',
            ]
            with self.assertRaises(requests.exceptions.ConnectionError):
                download.download_files(urls, temp_dir)
            self.assertTrue(
                (Path(temp_dir) / 'Diabetes_County_2022.xlsx').exists())
            self.assertFalse(partial_file.exists())

    @mock.patch.object(download, 'create_retry_session')
    def test_download_files_closes_response_on_http_error(
            self, mock_session_factory):
        mock_session = mock.Mock()
        mock_response = mock.Mock()
        mock_response.status_code = 403
        mock_response.raise_for_status.side_effect = (
            requests.exceptions.HTTPError('403 Forbidden'))
        mock_session.get.return_value = mock_response
        mock_session_factory.return_value = mock_session

        with tempfile.TemporaryDirectory() as temp_dir:
            with self.assertRaises(requests.exceptions.HTTPError):
                download.download_files(
                    ['https://tn.example/2022/Diabetes_County_2022.xlsx'],
                    temp_dir)
        mock_response.close.assert_called_once()

    @mock.patch.object(download, 'process_excel_files')
    @mock.patch.object(download, 'download_files_from_gcs')
    @mock.patch.object(download, 'download_files')
    def test_run_falls_back_to_gcs_on_tn_failure(self, mock_download_tn,
                                                 mock_download_gcs,
                                                 mock_process):
        mock_download_tn.side_effect = requests.exceptions.HTTPError(
            '403 Client Error: Forbidden')

        download.run('tn')

        mock_download_tn.assert_called_once()
        mock_download_gcs.assert_called_once()
        mock_process.assert_called_once()

    @mock.patch.object(download, 'process_excel_files')
    @mock.patch.object(download, 'download_files_from_gcs')
    @mock.patch.object(download, 'download_files')
    def test_run_with_gcs_source(self, mock_download_tn, mock_download_gcs,
                                 mock_process):
        download.run('gcs')

        mock_download_tn.assert_not_called()
        mock_download_gcs.assert_called_once()
        mock_process.assert_called_once()


if __name__ == '__main__':
    unittest.main()

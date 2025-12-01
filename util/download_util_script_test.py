import os
import shutil
import unittest
from unittest import mock
import zipfile
from absl import flags
from absl.testing import flagsaver
import requests
from requests.exceptions import HTTPError
import datetime

import download_util_script

FLAGS = flags.FLAGS


class DownloadFileTest(unittest.TestCase):

    def setUp(self):
        self.temp_dir = "test_output"
        os.makedirs(self.temp_dir, exist_ok=True)
        self.saved_flag_values = flagsaver.save_flag_values()

    def tearDown(self):
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
        flagsaver.restore_flag_values(self.saved_flag_values)

    @mock.patch('requests.head')
    @mock.patch('requests.get')
    def test_download_txt_file(self, mock_get, mock_head):
        download_url = "http://example.com/test.txt"
        file_content = b"This is a test file."

        # Configure mock for requests.head()
        mock_head_response = mock.MagicMock()
        mock_head_response.status_code = 200
        mock_head_response.headers = {
            'Last-Modified':
                datetime.datetime.now().strftime('%a, %d %b %Y %H:%M:%S GMT')
        }
        mock_head_response.raise_for_status.return_value = None
        mock_head.return_value = mock_head_response

        # Configure mock for requests.get()
        mock_get_response = mock.MagicMock()
        mock_get_response.status_code = 200
        mock_get_response.iter_content.return_value = [file_content]
        mock_get_response.raise_for_status.return_value = None
        mock_get.return_value = mock_get_response

        # Call the function under test
        result = download_util_script.download_file(download_url, self.temp_dir,
                                                    False)

        # Assertions
        self.assertTrue(
            result, "download_file should return True on successful download.")
        mock_head.assert_called_once_with(download_url,
                                          headers=None,
                                          allow_redirects=True,
                                          timeout=10)
        mock_get.assert_called_once_with(download_url,
                                         headers=None,
                                         stream=True,
                                         timeout=30)

        file_path = os.path.join(self.temp_dir, "test.txt")
        self.assertTrue(os.path.exists(file_path))
        with open(file_path, "rb") as f:
            self.assertEqual(f.read(), file_content)

    @mock.patch('requests.head')
    @mock.patch('requests.get')
    def test_download_file_without_extension(self, mock_get, mock_head):
        download_url = "http://example.com/test"
        file_content = b"This is a test file without extension."

        # Configure mock for requests.head()
        mock_head_response = mock.MagicMock()
        mock_head_response.status_code = 200
        mock_head_response.headers = {
            'Last-Modified':
                datetime.datetime.now().strftime('%a, %d %b %Y %H:%M:%S GMT')
        }
        mock_head_response.raise_for_status.return_value = None
        mock_head.return_value = mock_head_response

        # Configure mock for requests.get()
        mock_get_response = mock.MagicMock()
        mock_get_response.status_code = 200
        mock_get_response.iter_content.return_value = [file_content]
        mock_get_response.raise_for_status.return_value = None
        mock_get.return_value = mock_get_response

        result = download_util_script.download_file(download_url, self.temp_dir,
                                                    False)

        self.assertTrue(
            result, "download_file should return True on successful download.")
        mock_head.assert_called_once_with(download_url,
                                          headers=None,
                                          allow_redirects=True,
                                          timeout=10)
        mock_get.assert_called_once_with(download_url,
                                         headers=None,
                                         stream=True,
                                         timeout=30)

        file_path = os.path.join(self.temp_dir,
                                 "test.xlsx")  # Script appends .xlsx
        self.assertTrue(os.path.exists(file_path))
        with open(file_path, "rb") as f:
            self.assertEqual(f.read(), file_content)

    @mock.patch('requests.head')
    @mock.patch('requests.get')
    def test_download_invalid_url(self, mock_get, mock_head):
        download_url = "invalid_url"

        result = download_util_script.download_file(download_url, self.temp_dir,
                                                    False)

        self.assertFalse(
            result,
            "download_file should return False for an invalid URL format.")
        # Assert that neither head nor get were called as validation should occur first
        mock_head.assert_not_called()
        mock_get.assert_not_called()
        # Ensure no files were created in the output directory
        self.assertFalse(os.listdir(self.temp_dir))

    @mock.patch('requests.head')
    @mock.patch('requests.get')
    def test_download_failure(self, mock_get, mock_head):
        download_url = "http://example.com/error"

        # Configure mock for requests.head() to simulate failure
        mock_head_response = mock.MagicMock()
        mock_head_response.status_code = 404
        mock_head_response.raise_for_status.side_effect = HTTPError(
            "404 Client Error: Not Found for url: " + download_url)
        mock_head.return_value = mock_head_response

        # Configure mock for requests.get() to simulate failure
        mock_get_response = mock.MagicMock()
        mock_get_response.status_code = 404
        mock_get_response.raise_for_status.side_effect = HTTPError(
            "404 Client Error: Not Found for url: " + download_url)
        mock_get.return_value = mock_get_response

        # Pass tries=1 to download_file to disable retries for this test case
        result = download_util_script.download_file(download_url,
                                                    self.temp_dir,
                                                    False,
                                                    tries=1)

        self.assertFalse(
            result, "download_file should return False on download failure.")
        # Assert that both head and get were attempted
        mock_head.assert_called_once_with(download_url,
                                          headers=None,
                                          allow_redirects=True,
                                          timeout=10)
        # requests.get should now only be called once because tries=1
        mock_get.assert_called_once_with(download_url,
                                         headers=None,
                                         stream=True,
                                         timeout=30)
        # Ensure no files (even partially downloaded ones) were left behind
        self.assertFalse(os.listdir(self.temp_dir))

    @mock.patch('requests.head')
    @mock.patch('requests.get')
    def test_download_and_unzip_file(self, mock_get, mock_head):
        download_url = "http://example.com/test.zip"
        # Create a dummy zip file in memory
        zip_content = self._create_test_zip_file_content()

        mock_head_response = mock.MagicMock()
        mock_head_response.status_code = 200
        mock_head_response.headers = {
            'Last-Modified':
                datetime.datetime.now().strftime('%a, %d %b %Y %H:%M:%S GMT')
        }
        mock_head_response.raise_for_status.return_value = None
        mock_head.return_value = mock_head_response

        mock_get_response = mock.MagicMock()
        mock_get_response.status_code = 200
        mock_get_response.iter_content.return_value = [zip_content]
        mock_get_response.raise_for_status.return_value = None
        mock_get.return_value = mock_get_response

        result = download_util_script.download_file(download_url, self.temp_dir,
                                                    True)

        self.assertTrue(
            result,
            "download_file should return True on successful download and unzip."
        )
        self.assertTrue(os.path.exists(os.path.join(
            self.temp_dir, "test.zip")))  # The downloaded zip
        self.assertTrue(
            os.path.exists(os.path.join(self.temp_dir,
                                        "test_file.txt")))  # The unzipped file
        with open(os.path.join(self.temp_dir, "test_file.txt"), "r") as f:
            self.assertEqual(f.read(), "test content")

    def _create_test_zip_file_content(self):
        # Create a in-memory zip file
        # Using BytesIO to simulate file in memory without writing to disk
        from io import BytesIO
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED,
                             False) as zf:
            zf.writestr("test_file.txt", "test content")
        return zip_buffer.getvalue()


if __name__ == '__main__':
    unittest.main()

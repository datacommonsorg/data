# import os
# import sys
# import unittest
# import tempfile
# from unittest.mock import patch, Mock, call
# import requests

# # Assuming statvar_download_util.py is in the same directory or Python path
# try:
#     # If running tests from a directory containing the script
#     import statvar_download_util
# except ImportError:
#     # If the script is in a parent/different directory, adjust path
#     _SCRIPT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
#     sys.path.insert(0, _SCRIPT_DIR)
#     import statvar_download_util


# class TestStatVarDownloader(unittest.TestCase):

#     def setUp(self):
#         """Optional setup if needed for multiple tests"""
#         # Suppress logging during tests to keep output clean
#         # Note: absl logging might behave differently, consider specific setup
#         # if log message verification is critical. For now, we focus on behavior.
#         pass

#     def tearDown(self):
#         """Optional cleanup after each test"""
#         pass

#     # --- Helper to create a mock response ---
#     def _create_mock_response(self, status_code=200, content=b'dummy content', headers=None):
#         """Creates a mock requests.Response object."""
#         mock_resp = Mock()
#         mock_resp.status_code = status_code
#         mock_resp.content = content
#         # Simulate iter_content for streaming downloads
#         mock_resp.iter_content.return_value = [content[i:i + 8192] for i in range(0, len(content), 8192)]
#         # Allow accessing content via __enter__/__exit__ if needed (though not used directly here)
#         mock_resp.__enter__ = Mock(return_value=mock_resp)
#         mock_resp.__exit__ = Mock(return_value=None)
#         mock_resp.headers = headers if headers else {}
#         return mock_resp

#     # --- Test Cases ---

#     @patch('requests.get')
#     def test_download_success_basic(self, mock_get):
#         """Test successful download with explicit destination and filename."""
#         mock_response = self._create_mock_response(status_code=200, content=b'Test data for basic success')
#         mock_get.return_value = mock_response
#         downloader = statvar_download_util.StatVarDownloader()
#         test_url = "https://example.com/data/real_data.csv"
#         output_filename = "downloaded_data.csv"

#         with tempfile.TemporaryDirectory() as tmpdir:
#             destination_path = tmpdir
#             expected_output_path = os.path.join(destination_path, output_filename)

#             success = downloader._download_file(test_url, destination_path, output_filename)

#             self.assertTrue(success, "Download method should return True on success.")
#             mock_get.assert_called_once_with(test_url, stream=True, timeout=downloader.timeout)
#             self.assertTrue(os.path.exists(expected_output_path), "Output file should exist.")
#             with open(expected_output_path, 'rb') as f:
#                 content = f.read()
#             self.assertEqual(content, b'Test data for basic success', "File content should match downloaded data.")

#     @patch('requests.get')
#     def test_download_success_infer_filename(self, mock_get):
#         """Test successful download inferring filename from URL."""
#         mock_response = self._create_mock_response(status_code=200, content=b'Infer filename data')
#         mock_get.return_value = mock_response
#         downloader = statvar_download_util.StatVarDownloader()
#         test_url = "https://example.com/path/to/inferred_name.zip"
#         expected_filename = "inferred_name.zip"

#         with tempfile.TemporaryDirectory() as tmpdir:
#             destination_path = tmpdir
#             expected_output_path = os.path.join(destination_path, expected_filename)

#             success = downloader._download_file(test_url, destination_path=destination_path, output_filename=None)

#             self.assertTrue(success)
#             mock_get.assert_called_once_with(test_url, stream=True, timeout=downloader.timeout)
#             self.assertTrue(os.path.exists(expected_output_path))
#             with open(expected_output_path, 'rb') as f:
#                 self.assertEqual(f.read(), b'Infer filename data')

#     @patch('requests.get')
#     @patch('os.getcwd') # Mock current working directory for default path test
#     def test_download_success_default_path(self, mock_getcwd, mock_get):
#         """Test successful download using default destination path (cwd)."""
#         mock_response = self._create_mock_response(status_code=200, content=b'Default path data')
#         mock_get.return_value = mock_response

#         with tempfile.TemporaryDirectory() as tmpdir:
#             mock_getcwd.return_value = tmpdir # Make os.getcwd() return our temp dir
#             downloader = statvar_download_util.StatVarDownloader()
#             test_url = "https://example.com/default/path/test.txt"
#             output_filename = "explicit_name.txt"
#             expected_output_path = os.path.join(tmpdir, output_filename)

#             success = downloader._download_file(test_url, destination_path=None, output_filename=output_filename)

#             self.assertTrue(success)
#             mock_get.assert_called_once_with(test_url, stream=True, timeout=downloader.timeout)
#             self.assertTrue(os.path.exists(expected_output_path))
#             with open(expected_output_path, 'rb') as f:
#                 self.assertEqual(f.read(), b'Default path data')

#     @patch('requests.get')
#     def test_download_failure_http_error(self, mock_get):
#         """Test download failure due to HTTP error (e.g., 404)."""
#         mock_response = self._create_mock_response(status_code=404, content=b'Not Found')
#         mock_get.return_value = mock_response
#         # Use fewer retries to speed up the test
#         downloader = statvar_download_util.StatVarDownloader(retry_count=2, timeout=5)
#         test_url = "https://example.com/nonexistent.file"
#         output_filename = "should_not_exist.dat"

#         with tempfile.TemporaryDirectory() as tmpdir:
#             destination_path = tmpdir
#             expected_output_path = os.path.join(destination_path, output_filename)

#             success = downloader._download_file(test_url, destination_path, output_filename)

#             self.assertFalse(success, "Download method should return False on HTTP error.")
#             # Check if retries happened
#             self.assertEqual(mock_get.call_count, downloader.retry_count, f"requests.get should be called {downloader.retry_count} times.")
#             # Verify calls were made with correct arguments each time
#             expected_calls = [call(test_url, stream=True, timeout=downloader.timeout)] * downloader.retry_count
#             mock_get.assert_has_calls(expected_calls)
#             self.assertFalse(os.path.exists(expected_output_path), "Output file should not be created on failure.")
#             # Check if the directory was created (it shouldn't be if request fails)
#             self.assertTrue(os.path.exists(destination_path)) # Temp dir exists
#             # Check if subdirs within tmpdir were created (they shouldn't be)
#             self.assertEqual(len(os.listdir(destination_path)), 0, "No files or subdirs should be created in dest path on failure.")


#     @patch('requests.get')
#     @patch('time.sleep', return_value=None) # Mock time.sleep to avoid delays
#     def test_download_failure_request_exception(self, mock_sleep, mock_get):
#         """Test download failure due to requests exception (e.g., timeout)."""
#         # Configure the mock to raise an exception
#         mock_get.side_effect = requests.exceptions.Timeout("Connection timed out")
#         downloader = statvar_download_util.StatVarDownloader(retry_count=3, timeout=5)
#         test_url = "https://example.com/timeout.file"
#         output_filename = "timeout_fail.dat"

#         with tempfile.TemporaryDirectory() as tmpdir:
#             destination_path = tmpdir
#             expected_output_path = os.path.join(destination_path, output_filename)

#             success = downloader._download_file(test_url, destination_path, output_filename)

#             self.assertFalse(success, "Download method should return False on request exception.")
#             self.assertEqual(mock_get.call_count, downloader.retry_count, f"requests.get should be called {downloader.retry_count} times.")
#             # Check that sleep was called between failed attempts
#             self.assertEqual(mock_sleep.call_count, downloader.retry_count -1, "time.sleep should be called between retries.")
#             self.assertFalse(os.path.exists(expected_output_path), "Output file should not be created on failure.")

#     @patch('requests.get')
#     @patch('time.sleep', return_value=None)
#     def test_download_failure_then_success_on_retry(self, mock_sleep, mock_get):
#         """Test scenario where download fails initially but succeeds on retry."""
#         mock_failure_response = self._create_mock_response(status_code=500, content=b'Server Error')
#         mock_success_response = self._create_mock_response(status_code=200, content=b'Success on retry')

#         # Simulate failure on first call, success on second
#         mock_get.side_effect = [
#             requests.exceptions.ConnectionError("Temporary glitch"), # 1st attempt fails with exception
#             mock_failure_response,                                  # 2nd attempt fails with 500
#             mock_success_response                                   # 3rd attempt succeeds
#         ]

#         downloader = statvar_download_util.StatVarDownloader(retry_count=3, timeout=5)
#         test_url = "https://example.com/flaky.service"
#         output_filename = "retry_success.txt"

#         with tempfile.TemporaryDirectory() as tmpdir:
#             destination_path = tmpdir
#             expected_output_path = os.path.join(destination_path, output_filename)

#             success = downloader._download_file(test_url, destination_path, output_filename)

#             self.assertTrue(success, "Download should eventually succeed and return True.")
#             self.assertEqual(mock_get.call_count, 3, "requests.get should be called 3 times.")
#             # Check sleep calls between failures
#             self.assertEqual(mock_sleep.call_count, 2, "time.sleep should be called twice (after 1st and 2nd failures).")
#             self.assertTrue(os.path.exists(expected_output_path), "Output file should exist after successful retry.")
#             with open(expected_output_path, 'rb') as f:
#                 self.assertEqual(f.read(), b'Success on retry', "File content should match the successful response.")


#     def test_download_failure_no_url(self):
#         """Test behavior when no URL is provided."""
#         downloader = statvar_download_util.StatVarDownloader()
#         with tempfile.TemporaryDirectory() as tmpdir:
#             # Use assertLogs to check for the specific warning (optional but good)
#             with self.assertLogs(level='WARNING') as log:
#                  success = downloader._download_file(url=None, destination_path=tmpdir, output_filename="test.file")
#                  self.assertFalse(success)
#             self.assertIn("URL must be provided.", log.output[0])

#             with self.assertLogs(level='WARNING') as log:
#                 success = downloader._download_file(url="", destination_path=tmpdir, output_filename="test.file")
#                 self.assertFalse(success)
#             self.assertIn("URL must be provided.", log.output[0])


#     def test_download_failure_cannot_infer_filename(self):
#         """Test failure when filename cannot be inferred from URL."""
#         downloader = statvar_download_util.StatVarDownloader()
#         # URL path ends with '/' or is just the domain
#         test_url = "https://example.com/"
#         with tempfile.TemporaryDirectory() as tmpdir:
#             with self.assertLogs(level='WARNING') as log:
#                 success = downloader._download_file(url=test_url, destination_path=tmpdir, output_filename=None)
#                 self.assertFalse(success)
#             self.assertIn("Unable to infer filename from URL.", log.output[0])


# if __name__ == '__main__':
#     unittest.main()
    
import unittest
import os
import requests_mock
from absl import flags
from absl.testing import flagsaver
import zipfile
import shutil
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

    @requests_mock.Mocker()
    def test_download_txt_file(self, mock):
        url = "http://example.com/test.txt"
        file_content = b"This is a test file."
        mock.get(url, content=file_content)
        
        download_util_script.download_file(url, self.temp_dir, False)
        
        file_path = os.path.join(self.temp_dir, "test.txt")
        self.assertTrue(os.path.exists(file_path))
        with open(file_path, "rb") as f:
            self.assertEqual(f.read(), file_content)

    @requests_mock.Mocker()
    def test_download_file_without_extension(self, mock):
        url = "http://example.com/test"
        file_content = b"This is a test file without extension."
        mock.get(url, content=file_content)
        
        download_util_script.download_file(url, self.temp_dir, False)
        
        file_path = os.path.join(self.temp_dir, "test.xlsx")
        self.assertTrue(os.path.exists(file_path))
        with open(file_path, "rb") as f:
            self.assertEqual(f.read(), file_content)

    @requests_mock.Mocker()
    def test_download_invalid_url(self, mock):
        url = "invalid_url"
        download_util_script.download_file(url, self.temp_dir, False)
        self.assertFalse(os.listdir(self.temp_dir))

    @requests_mock.Mocker()
    def test_download_failure(self, mock):
        url = "http://example.com/error"
        mock.get(url, status_code=404)
        download_util_script.download_file(url, self.temp_dir, False)
        self.assertFalse(os.listdir(self.temp_dir))

    def _create_test_zip_file(self):
        test_zip_file = os.path.join(self.temp_dir, "test_file.zip")
        with zipfile.ZipFile(test_zip_file, "w") as zf:
            zf.writestr("test_file.txt", "test content")
        with open(test_zip_file, "rb") as f:
            return f.read()

if __name__ == '__main__':
    unittest.main()
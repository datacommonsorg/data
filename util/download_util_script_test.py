import os
import shutil
import unittest
import zipfile
from absl import flags
from absl.testing import flagsaver
import requests_mock
import download_util_script
import datetime # Import to generate Last-Modified header timestamps

FLAGS = flags.FLAGS


class DownloadFileTest(unittest.TestCase):

    def setUp(self):
        self.temp_dir = "test_output"
        os.makedirs(self.temp_dir, exist_ok=True)
        # It's good practice to explicitly reset flags for each test,
        # but flagsaver handles this well between tests.
        self.saved_flag_values = flagsaver.save_flag_values()

    def tearDown(self):
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
        flagsaver.restore_flag_values(self.saved_flag_values)

    @requests_mock.Mocker()
    def test_download_txt_file(self, mock):
        download_url = "http://example.com/test.txt"
        file_content = b"This is a test file."
        
        # 1. Mock the HEAD request that download_file makes for staleness check
        mock.head(download_url, status_code=200, headers={'Last-Modified': datetime.datetime.now().strftime('%a, %d %b %Y %H:%M:%S GMT')})
        # 2. Mock the GET request for the actual file download
        mock.get(download_url, content=file_content)

        # Call the function under test
        result = download_util_script.download_file(download_url, self.temp_dir, False)

        # Assertions
        self.assertTrue(result, "download_file should return True on successful download.")
        file_path = os.path.join(self.temp_dir, "test.txt")
        self.assertTrue(os.path.exists(file_path))
        with open(file_path, "rb") as f:
            self.assertEqual(f.read(), file_content)

    @requests_mock.Mocker()
    def test_download_file_without_extension(self, mock):
        download_url = "http://example.com/test"
        file_content = b"This is a test file without extension."

        # 1. Mock the HEAD request
        mock.head(download_url, status_code=200, headers={'Last-Modified': datetime.datetime.now().strftime('%a, %d %b %Y %H:%M:%S GMT')})
        # 2. Mock the GET request
        mock.get(download_url, content=file_content)

        result = download_util_script.download_file(download_url, self.temp_dir, False)

        self.assertTrue(result, "download_file should return True on successful download.")
        # The script is expected to append .xlsx for files without extensions when not unzipping
        file_path = os.path.join(self.temp_dir, "test.xlsx")
        self.assertTrue(os.path.exists(file_path))
        with open(file_path, "rb") as f:
            self.assertEqual(f.read(), file_content)

    @requests_mock.Mocker()
    def test_download_invalid_url(self, mock):
        # This test case verifies URL format validation, which happens *before* network requests.
        # Thus, no HEAD/GET mocks are strictly necessary as the script should fail early.
        download_url = "invalid_url"
        
        result = download_util_script.download_file(download_url, self.temp_dir, False)
        
        self.assertFalse(result, "download_file should return False for an invalid URL format.")
        # Ensure no files were created in the output directory
        self.assertFalse(os.listdir(self.temp_dir))

    @requests_mock.Mocker()
    def test_download_failure(self, mock):
        download_url = "http://example.com/error"
        # Mock both HEAD and GET to return a failure status code (e.g., 404 Not Found)
        mock.head(download_url, status_code=404)
        mock.get(download_url, status_code=404)

        result = download_util_script.download_file(download_url, self.temp_dir, False)

        self.assertFalse(result, "download_file should return False on download failure.")
        # Ensure no files (even partially downloaded ones) were left behind
        self.assertFalse(os.listdir(self.temp_dir))

    def _create_test_zip_file(self):
        test_zip_file = os.path.join(self.temp_dir, "test_file.zip")
        with zipfile.ZipFile(test_zip_file, "w") as zf:
            zf.writestr("test_file.txt", "test content")
        with open(test_zip_file, "rb") as f:
            return f.read()


if __name__ == '__main__':
    unittest.main()
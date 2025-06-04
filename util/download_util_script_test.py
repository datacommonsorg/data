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

# Copyright 2022 Google LLC
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
"""Tests for preprocess.py."""

import os
import tempfile
import unittest
from preprocess import process

_SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))


class EPHHeatRelatedIllness(unittest.TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.exp_path = os.path.join(_SCRIPT_PATH, 'testdata', 'expected_files')
        cls._tmp_dir = tempfile.TemporaryDirectory()
        cls.act_path = cls._tmp_dir.name
        csv_path = os.path.join(cls.act_path, 'cleaned.csv')
        mcf_path = os.path.join(cls.act_path, 'output.mcf')
        input_path = os.path.join(_SCRIPT_PATH, 'testdata', 'cleaned_data/')

        # generates actual output in tmp directory
        process(csv_path, mcf_path, input_path)

        with open(csv_path, 'r', encoding='utf-8') as f_result:
            cls.actual_csv_result = f_result.read()

        with open(mcf_path, 'r', encoding='utf-8') as f_result:
            cls.actual_mcf_result = f_result.read()

    @classmethod
    def tearDownClass(cls) -> None:
        cls._tmp_dir.cleanup()
        super().tearDownClass()

    def test_csv(self):
        expected_csv_path = os.path.join(self.exp_path, 'expected_output.csv')

        with open(expected_csv_path, 'r', encoding='utf-8') as f_expected:
            expected_result = f_expected.read()

        self.assertEqual(sorted(self.actual_csv_result.splitlines()),
                         sorted(expected_result.splitlines()))

    def test_mcf(self):
        expected_mcf_path = os.path.join(self.exp_path, 'expected_output.mcf')

        with open(expected_mcf_path, 'r', encoding='utf-8') as f_expected:
            expected_result = f_expected.read()

        self.assertEqual(sorted(self.actual_mcf_result.strip().split('\n\n')),
                         sorted(expected_result.strip().split('\n\n')))

    def test_table_to_csv_raises_on_missing_or_empty_table(self):
        import clean_data
        with tempfile.TemporaryDirectory() as tmp_dir:
            csv_out = os.path.join(tmp_dir, 'out.csv')
            with self.assertRaises(ValueError):
                clean_data.table_to_csv('<html><body>No table</body></html>',
                                        csv_out)
            with self.assertRaises(ValueError):
                clean_data.table_to_csv(
                    '<html><body><table><tr><th>HeaderOnly</th></tr></table></body></html>',
                    csv_out)

    def test_download_dynamic_page_retries_and_succeeds(self):
        import clean_data
        from unittest import mock

        with tempfile.TemporaryDirectory() as tmp_dir:
            html_out = os.path.join(tmp_dir, 'test.html')
            mock_driver = mock.MagicMock()
            mock_driver.find_elements.return_value = []
            mock_driver.page_source = (
                '<html><body><table><tr><th>Year</th></tr>'
                '<tr><td>2023</td></tr></table></body></html>')

            # First attempt raises a transient WebDriver error; second succeeds.
            with mock.patch.object(
                    clean_data.webdriver,
                    'Chrome',
                    side_effect=[RuntimeError('Transient error'), mock_driver
                                ]) as mock_chrome, \
                 mock.patch.object(clean_data, 'WebDriverWait'), \
                 mock.patch.object(clean_data.time, 'sleep'):
                result = clean_data.download_dynamic_page(
                    'https://example.com?apiToken=SECRET123', html_out)
                self.assertTrue(result)
                self.assertEqual(mock_chrome.call_count, 2)
                self.assertTrue(os.path.exists(html_out))

    def test_sanitize_url_redacts_api_token(self):
        import clean_data
        raw_url = (
            'https://ephtracking.cdc.gov/qr/370/1/ALL/ALL/1/2020/0'
            '?AgeBandId=1,2&apiToken=637DD2EF-507F-4938-8380-54A179C3132A')
        sanitized = clean_data._sanitize_url(raw_url)
        self.assertNotIn('637DD2EF-507F-4938-8380-54A179C3132A', sanitized)
        self.assertIn('apiToken=REDACTED', sanitized)

    def test_combine_csv_files_raises_on_incomplete_years(self):
        import clean_data
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Write only 2 yearly CSVs instead of the required 2000..2023 range
            for year in (2000, 2001):
                with open(os.path.join(tmp_dir,
                                       f'edVisits_age_gender_{year}.csv'),
                          'w',
                          encoding='utf-8') as f:
                    f.write('State,Year,Data Value\nAlabama,2000,10\n')
            with self.assertRaises(RuntimeError):
                clean_data.combine_csv_files(tmp_dir, 'edVisits_age_gender')


if __name__ == '__main__':
    unittest.main()

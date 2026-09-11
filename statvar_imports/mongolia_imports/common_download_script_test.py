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

"""Unit tests for common_download_script.py."""

import os
import sys
import tempfile
import unittest
from unittest import mock

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(_SCRIPT_DIR)

import common_download_script


class CommonDownloadScriptTest(unittest.TestCase):
    """Tests for Mongolia imports download script logic."""

    def test_table_configurations(self):
        """Validates all table definitions across the 4 domains."""
        self.assertEqual(len(common_download_script.DEMOGRAPHICS_TABLES), 7)
        self.assertEqual(len(common_download_script.EDUCATION_TABLES), 6)
        self.assertEqual(len(common_download_script.HEALTH_TABLES), 6)
        self.assertEqual(len(common_download_script.EMPLOYMENT_TABLES), 6)

        all_tables = (
            common_download_script.DEMOGRAPHICS_TABLES
            + common_download_script.EDUCATION_TABLES
            + common_download_script.HEALTH_TABLES
            + common_download_script.EMPLOYMENT_TABLES
        )
        self.assertEqual(len(all_tables), 25)

        filenames = set()
        for table in all_tables:
            self.assertIn('url', table)
            self.assertIn('filename', table)
            self.assertTrue(
                table['url'].startswith('https://data.1212.mn/api/v1/en/NSO/'),
                f"Invalid URL base: {table['url']}",
            )
            self.assertTrue(
                table['filename'].endswith('.csv'),
                f"Filename must end with .csv: {table['filename']}",
            )
            self.assertNotIn(
                table['filename'],
                filenames,
                f"Duplicate filename detected: {table['filename']}",
            )
            filenames.add(table['filename'])

    @mock.patch('common_download_script.download_util.download_file_from_url')
    def test_fetch_and_save_data_success(self, mock_download):
        """Tests successful download and CSV payload formulation."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            csv_path = os.path.join(tmp_dir, 'sample.csv')

            def mock_side_effect(**kwargs):
                with open(kwargs['output_file'], 'w', encoding='utf-8') as f:
                    f.write('header1,header2\nval1,val2\n')
                return True

            mock_download.side_effect = mock_side_effect

            url = 'https://data.1212.mn/api/v1/en/NSO/test.px'
            common_download_script.fetch_and_save_data(url, csv_path)

            mock_download.assert_called_once_with(
                url=url,
                params={'query': [], 'response': {'format': 'csv'}},
                method='POST',
                timeout=60,
                retries=5,
                retry_secs=5,
                output_file=csv_path,
                overwrite=True,
            )
            self.assertTrue(os.path.exists(csv_path))

    @mock.patch('common_download_script.download_util.download_file_from_url')
    def test_fetch_and_save_data_with_query(self, mock_download):
        """Tests download with custom JSON query filters."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            csv_path = os.path.join(tmp_dir, 'sample_filtered.csv')

            def mock_side_effect(**kwargs):
                with open(kwargs['output_file'], 'w', encoding='utf-8') as f:
                    f.write('header1,header2\nfiltered1,filtered2\n')
                return True

            mock_download.side_effect = mock_side_effect

            url = 'https://data.1212.mn/api/v1/en/NSO/test_query.px'
            query = [{'code': 'Бүс', 'selection': {'filter': 'item', 'values': ['0']}}]
            common_download_script.fetch_and_save_data(url, csv_path, query=query)

            mock_download.assert_called_once_with(
                url=url,
                params={'query': query, 'response': {'format': 'csv'}},
                method='POST',
                timeout=60,
                retries=5,
                retry_secs=5,
                output_file=csv_path,
                overwrite=True,
            )

    @mock.patch('common_download_script.download_util.download_file_from_url')
    def test_fetch_and_save_data_failure_raises_error(self, mock_download):
        """Tests that a failed download raises RuntimeError."""
        mock_download.return_value = False
        with tempfile.TemporaryDirectory() as tmp_dir:
            csv_path = os.path.join(tmp_dir, 'failed.csv')
            with self.assertRaises(RuntimeError):
                common_download_script.fetch_and_save_data(
                    'https://data.1212.mn/api/v1/en/NSO/fail.px', csv_path
                )

    @mock.patch('common_download_script.download_util.download_file_from_url')
    def test_fetch_and_save_data_empty_file_raises_error(self, mock_download):
        """Tests that an empty or near-empty download raises RuntimeError."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            csv_path = os.path.join(tmp_dir, 'empty.csv')

            def mock_side_effect(**kwargs):
                with open(kwargs['output_file'], 'w', encoding='utf-8') as f:
                    f.write('')  # 0 bytes
                return True

            mock_download.side_effect = mock_side_effect

            with self.assertRaises(RuntimeError):
                common_download_script.fetch_and_save_data(
                    'https://data.1212.mn/api/v1/en/NSO/empty.px', csv_path
                )

    @mock.patch('common_download_script.fetch_and_save_data')
    @mock.patch('os.makedirs')
    def test_main_processes_all_25_tables(self, mock_makedirs, mock_fetch):
        """Tests that main() triggers downloads for all 25 tables across 4 domains."""
        common_download_script.main(None)
        self.assertEqual(mock_fetch.call_count, 25)

    def test_registered_unemployed_query_excludes_duplicate_ulaanbaatar(self):
        """Verifies registered unemployed table defines query excluding code 511."""
        target_table = [
            t
            for t in common_download_script.EMPLOYMENT_TABLES
            if t['filename']
            == 'registered_unemployed_by_education_level_region_gender_month.csv'
        ][0]
        self.assertIn('query', target_table)
        query = target_table['query']
        self.assertEqual(query[0]['code'], 'Бүс')
        values = query[0]['selection']['values']
        self.assertIn('5', values)
        self.assertNotIn('511', values)

    @mock.patch('common_download_script.fetch_and_save_data')
    @mock.patch('os.makedirs')
    def test_main_passes_query_for_registered_unemployed(
        self, mock_makedirs, mock_fetch
    ):
        """Verifies that main() forwards query filter for registered unemployed."""
        common_download_script.main(None)
        unemployed_calls = [
            c
            for c in mock_fetch.call_args_list
            if 'registered_unemployed_by_education_level_region_gender_month.csv'
            in c[0][1]
        ]
        self.assertEqual(len(unemployed_calls), 1)
        args, kwargs = unemployed_calls[0]
        query = args[2] if len(args) > 2 else kwargs.get('query')
        self.assertIsNotNone(query)
        self.assertEqual(query[0]['code'], 'Бүс')
        self.assertNotIn('511', query[0]['selection']['values'])


if __name__ == '__main__':
    unittest.main()


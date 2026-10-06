# Copyright 2026 Google LLC
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
"""Unit tests for import-automation/validator/main.py."""

import json
import os
import sys
import unittest
from unittest import mock

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if _SCRIPT_DIR not in sys.path:
    sys.path.insert(0, _SCRIPT_DIR)

import main as validator_main


class ValidatorTest(unittest.TestCase):

    @mock.patch('main.ValidationRunner')
    @mock.patch('main.bigquery_differ.run_bigquery_differ')
    @mock.patch('main.file_util.file_copy')
    @mock.patch('main.file_util.file_get_matching')
    @mock.patch('main.storage.Client')
    def test_run_validation_job_staging(self, mock_storage_cls, mock_matching,
                                        mock_copy, mock_bq_differ,
                                        mock_runner_cls):
        mock_gcs = mock_storage_cls.return_value
        mock_bucket = mock.MagicMock()
        mock_gcs.bucket.return_value = mock_bucket

        blob_store = {
            'scripts/us_fed/treasury/staging_version.txt':
                '2026_09_17',
            'scripts/us_fed/treasury/latest_version.txt':
                '2026_09_10',
            'scripts/us_fed/treasury/2026_09_17/import_summary.json':
                json.dumps({
                    'import_name': 'treasury',
                    'status': 'PENDING'
                }),
        }
        uploaded_blobs = {}

        def _get_blob(path):
            b = mock.MagicMock()
            b.name = path
            b.exists.return_value = path in blob_store
            b.download_as_text.return_value = blob_store.get(path, '')

            def _upload_str(content):
                uploaded_blobs[path] = content

            b.upload_from_string.side_effect = _upload_str
            return b

        mock_bucket.blob.side_effect = _get_blob
        mock_iterator = mock.MagicMock()
        mock_iterator.prefixes = []
        mock_gcs.list_blobs.return_value = mock_iterator

        mock_matching.return_value = ['gs://bucket/file.mcf']
        mock_bq_differ.return_value = {
            'obs_diff_count': 10,
            'schema_diff_count': 0,
        }

        mock_runner = mock_runner_cls.return_value
        mock_runner.run_validations.return_value = (True, [])

        exit_code = validator_main.run_validation_job(
            absolute_import_name='scripts/us_fed:treasury',
            import_config_str='{"gcp_project_id": "test-proj"}',
            version_override='',
            bucket_name='test-bucket',
            bq_dataset='test_dataset',
        )

        self.assertEqual(exit_code, 0)
        summary_blob_key = 'scripts/us_fed/treasury/2026_09_17/import_summary.json'
        self.assertIn(summary_blob_key, uploaded_blobs)
        updated_summary = json.loads(uploaded_blobs[summary_blob_key])
        self.assertEqual(updated_summary['status'], 'STAGING')

    @mock.patch('main.merge_and_save_config')
    @mock.patch('main._read_gcs_text')
    @mock.patch('main.file_util.file_copy')
    @mock.patch('main.file_util.file_get_matching')
    def test_resolve_validation_config_from_gcs(self, mock_matching, mock_copy,
                                                mock_read_gcs, mock_merge):
        mock_client = mock.MagicMock()
        mock_read_gcs.return_value = json.dumps({
            'import_specifications': [{
                'import_name': 'treasury',
                'validation_config_file': 'custom_val.json',
            }]
        })
        mock_matching.return_value = [
            'gs://test-bucket/scripts/us_fed/treasury/2026_09_17/custom_val.json'
        ]
        mock_merge.return_value = '/tmp/test_val/merged_validation_config.json'
        resolved = validator_main._resolve_validation_config(
            client=mock_client,
            bucket_name='test-bucket',
            output_dir='scripts/us_fed/treasury',
            relative_import_dir='scripts/us_fed',
            import_name='treasury',
            version='2026_09_17',
            default_val_config='/default/validation_config.json',
            tmpdir='/tmp/test_val',
        )
        self.assertEqual(resolved,
                         '/tmp/test_val/merged_validation_config.json')
        mock_copy.assert_called_once_with(
            'gs://test-bucket/scripts/us_fed/treasury/2026_09_17/custom_val.json',
            '/tmp/test_val/custom_val.json',
        )
        mock_merge.assert_called_once_with(
            '/default/validation_config.json',
            '/tmp/test_val/custom_val.json',
            '/tmp/test_val',
        )


if __name__ == '__main__':
    unittest.main()

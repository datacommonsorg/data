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
"""Tests for bounded import-summary discovery in GCS."""

import json
import unittest

from google.api_core import exceptions

from agents.common.scripts.list_import_summaries import ImportSummaryListError
from agents.common.scripts.list_import_summaries import list_import_summaries
from agents.common.scripts.list_import_summaries import normalize_import_name


class _Blob:

    def __init__(self,
                 name: str,
                 summary: object | None = None,
                 raw_summary: str | None = None,
                 error: Exception | None = None):
        self.name = name
        self._summary = summary
        self._raw_summary = raw_summary
        self._error = error
        self.download_count = 0

    def download_as_text(self) -> str:
        self.download_count += 1
        if self._error:
            raise self._error
        if self._raw_summary is not None:
            return self._raw_summary
        return json.dumps(self._summary)


class _StorageClient:

    def __init__(self, blobs: list[_Blob]):
        self._blobs = blobs
        self.calls = []

    def list_blobs(self, bucket: str, **kwargs):
        self.calls.append((bucket, kwargs))
        return self._blobs[:kwargs['max_results']]


def _blob(version: str,
          import_name: str = 'Import',
          job_id: str | None = None) -> _Blob:
    job_id = job_id if job_id is not None else f'job-{version}'
    return _Blob(f'scripts/a/Import/{version}/import_summary.json', {
        'import_name': import_name,
        'job_id': job_id,
        'status': 'STAGING',
    })


class ListImportSummariesTest(unittest.TestCase):

    def test_derives_exact_prefix_and_bounded_glob(self):
        client = _StorageClient([])

        result = list_import_summaries('  scripts/a:Import  ',
                                       'project',
                                       'bucket',
                                       client=client)

        self.assertEqual('scripts/a:Import', result['absolute_import_name'])
        self.assertEqual(1000, result['scan_limit'])
        self.assertEqual(1, len(client.calls))
        bucket, kwargs = client.calls[0]
        self.assertEqual('bucket', bucket)
        self.assertEqual('scripts/a/Import/', kwargs['prefix'])
        self.assertEqual('scripts/a/Import/*/import_summary.json',
                         kwargs['match_glob'])
        self.assertEqual(1001, kwargs['max_results'])
        self.assertEqual(1001, kwargs['page_size'])
        self.assertEqual('items(name),nextPageToken', kwargs['fields'])

    def test_returns_newest_five_with_date_and_batch_job_id(self):
        versions = [
            f'2026_08_0{day}T01_02_03_123456_07_00' for day in (3, 1, 7, 2, 6,
                                                                4, 5)
        ]
        blobs = [_blob(version) for version in versions]

        result = list_import_summaries('scripts/a:Import',
                                       'project',
                                       'bucket',
                                       client=_StorageClient(blobs))

        self.assertEqual([
            '2026_08_07T01_02_03_123456_07_00',
            '2026_08_06T01_02_03_123456_07_00',
            '2026_08_05T01_02_03_123456_07_00',
            '2026_08_04T01_02_03_123456_07_00',
            '2026_08_03T01_02_03_123456_07_00',
        ], [item['version'] for item in result['results']])
        self.assertEqual('2026-08-07', result['results'][0]['date'])
        self.assertEqual(
            'gs://bucket/scripts/a/Import/'
            '2026_08_07T01_02_03_123456_07_00',
            result['results'][0]['gcs_version_uri'])
        self.assertEqual('job-2026_08_07T01_02_03_123456_07_00',
                         result['results'][0]['batch_job_id'])
        self.assertTrue(
            all(
                set(item) ==
                {'version', 'date', 'gcs_version_uri', 'batch_job_id'}
                for item in result['results']))
        self.assertEqual(5, result['returned_summary_count'])
        self.assertEqual(5, sum(blob.download_count for blob in blobs))

    def test_skips_non_timestamp_versions_without_downloading_them(self):
        overridden = _blob('manual_override')
        canonical = _blob('2026_08_04T01_02_03_123456_07_00')

        result = list_import_summaries('scripts/a:Import',
                                       'project',
                                       'bucket',
                                       client=_StorageClient(
                                           [overridden, canonical]))

        self.assertEqual(1, result['skipped_non_timestamp_count'])
        self.assertEqual(0, overridden.download_count)
        self.assertEqual(1, canonical.download_count)

    def test_builds_version_uri(self):
        version = '2026_08_04T01_02_03_123456_07_00'
        blob = _Blob(f'scripts/a/Import/{version}/import_summary.json', {
            'import_name': 'Import',
            'job_id': 'job-id',
        })

        result = list_import_summaries('scripts/a:Import',
                                       'project',
                                       'bucket',
                                       client=_StorageClient([blob]))

        self.assertEqual(f'gs://bucket/scripts/a/Import/{version}',
                         result['results'][0]['gcs_version_uri'])

    def test_reports_invalid_or_mismatched_selected_summaries(self):
        prefix = 'scripts/a/Import'
        versions = [
            '2026_08_04T04_00_00_123456_07_00',
            '2026_08_04T03_00_00_123456_07_00',
            '2026_08_04T02_00_00_123456_07_00',
            '2026_08_04T01_00_00_123456_07_00',
        ]
        blobs = [
            _Blob(f'{prefix}/{versions[0]}/import_summary.json',
                  raw_summary='{not-json'),
            _blob(versions[1], import_name='OtherImport'),
            _blob(versions[2], job_id=''),
            _Blob(f'{prefix}/{versions[3]}/import_summary.json',
                  error=exceptions.NotFound('deleted')),
        ]

        result = list_import_summaries('scripts/a:Import',
                                       'project',
                                       'bucket',
                                       client=_StorageClient(blobs))

        self.assertEqual([None, None, None, None],
                         [item['batch_job_id'] for item in result['results']])
        self.assertEqual(
            [f'gs://bucket/{prefix}/{version}' for version in versions],
            [item['gcs_version_uri'] for item in result['results']])
        self.assertEqual([
            'invalid_summary_json', 'summary_import_mismatch',
            'summary_job_id_missing', 'summary_missing'
        ], [issue['code'] for issue in result['issues']])

    def test_returns_date_only_versions(self):
        versions = [f'2026-08-0{day}' for day in (3, 1, 7, 2, 6, 4, 5)]
        blobs = [_blob(version) for version in versions]

        result = list_import_summaries('scripts/a:Import',
                                       'project',
                                       'bucket',
                                       client=_StorageClient(blobs))

        self.assertEqual([
            '2026-08-07',
            '2026-08-06',
            '2026-08-05',
            '2026-08-04',
            '2026-08-03',
        ], [item['version'] for item in result['results']])
        self.assertEqual('2026-08-07', result['results'][0]['date'])

    def test_returns_no_history_when_scan_limit_is_exceeded(self):
        blobs = [
            _blob(f'2026_07_{(index % 28) + 1:02d}T01_02_03_{index:06d}_07_00')
            for index in range(1001)
        ]

        result = list_import_summaries('scripts/a:Import',
                                       'project',
                                       'bucket',
                                       client=_StorageClient(blobs))

        self.assertTrue(result['scan_truncated'])
        self.assertEqual(1001, result['scanned_summary_count'])
        self.assertEqual([], result['results'])
        self.assertEqual(0, sum(blob.download_count for blob in blobs))
        self.assertEqual('summary_scan_limit_exceeded',
                         result['issues'][0]['code'])

    def test_returns_empty_bounded_result(self):
        result = list_import_summaries('scripts/a:Import',
                                       'project',
                                       'bucket',
                                       client=_StorageClient([]))

        self.assertFalse(result['scan_truncated'])
        self.assertEqual(0, result['scanned_summary_count'])
        self.assertEqual(0, result['returned_summary_count'])
        self.assertEqual([], result['results'])
        self.assertEqual([], result['issues'])

    def test_rejects_invalid_identity_and_limit(self):
        for absolute_import_name in ('Import', 'scripts//a:Import',
                                     'scripts/a:Import Name'):
            with self.subTest(absolute_import_name=absolute_import_name):
                with self.assertRaises(ImportSummaryListError):
                    normalize_import_name(absolute_import_name)

        for limit in (0, 6):
            with self.subTest(limit=limit):
                with self.assertRaisesRegex(ImportSummaryListError,
                                            'limit must be between'):
                    list_import_summaries('scripts/a:Import',
                                          'project',
                                          'bucket',
                                          limit=limit,
                                          client=_StorageClient([]))


if __name__ == '__main__':
    unittest.main()

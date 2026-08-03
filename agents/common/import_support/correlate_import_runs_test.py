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
"""Tests for import run correlation across Spanner and GCS."""

from datetime import datetime
from datetime import timezone
import json
import unittest

from agents.common.import_support.correlate_import_runs import classify_workflow_reference
from agents.common.import_support.correlate_import_runs import correlate_import_runs
from agents.common.import_support.correlate_import_runs import ImportRunCorrelationError
from agents.common.import_support.correlate_import_runs import normalize_import_name
from agents.common.import_support.correlate_import_runs import normalize_stored_version
from agents.common.import_support.correlate_import_runs import parse_rfc3339
from agents.common.import_support.correlate_import_runs import query_latest_versions
from agents.common.import_support.correlate_import_runs import query_version_history


def _history_row(import_name='Import',
                 version='2026_01_02',
                 workflow_id=None,
                 comment='import-workflow:workflow-1',
                 update_timestamp=datetime(2026, 1, 2, tzinfo=timezone.utc)):
    return (import_name, version, update_timestamp, workflow_id, 'STAGING', 10,
            1, 2, 3, 4, comment)


class _Snapshot:

    def __init__(self, rows):
        self._rows = rows
        self.calls = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def execute_sql(self, sql, params, param_types):
        self.calls.append((sql, params, param_types))
        rows = self._rows
        if 'MAX(UpdateTimestamp)' in sql:
            latest_by_version = {}
            for row in rows:
                version = row[1]
                update_timestamp = row[2]
                if (version not in latest_by_version or
                        update_timestamp > latest_by_version[version]):
                    latest_by_version[version] = update_timestamp
            rows = sorted(latest_by_version.items(), key=lambda item: item[0])
            rows.sort(key=lambda item: item[1], reverse=True)
        elif 'versions' in params:
            rows = [row for row in rows if row[1] in params['versions']]
        return rows[:params['limit']]


class _SpannerClient:

    def __init__(self, snapshot):
        self._snapshot = snapshot

    def instance(self, instance):
        del instance
        return self

    def database(self, database):
        del database
        return self

    def snapshot(self):
        return self._snapshot


class _Blob:

    def __init__(self, value):
        self._value = value
        self.time_created = datetime(2026, 1, 2, tzinfo=timezone.utc)
        self.updated = datetime(2026, 1, 2, 1, tzinfo=timezone.utc)
        self.generation = 7

    def download_as_text(self):
        return json.dumps(self._value)


class _Bucket:

    def __init__(self, blobs):
        self._blobs = blobs
        self.requests = []

    def get_blob(self, name):
        self.requests.append(name)
        return self._blobs.get(name)


class _StorageClient:

    def __init__(self, bucket):
        self._bucket = bucket

    def bucket(self, name):
        del name
        return self._bucket


class CorrelateImportRunsTest(unittest.TestCase):

    def test_normalizes_absolute_simple_and_gcs_names(self):
        identity = normalize_import_name('scripts/a:Import', 'output/root')

        self.assertEqual('Import', identity['simple_import_name'])
        self.assertEqual('output/root/scripts/a/Import', identity['gcs_prefix'])
        self.assertEqual(['scripts/a:Import', 'Import'],
                         identity['spanner_name_candidates'])

    def test_normalizes_full_uri_and_reports_prefix_mismatch(self):
        version, warnings = normalize_stored_version(
            'gs://bucket/scripts/a/Import/2026_01_02', 'bucket',
            'scripts/a/Import')
        self.assertEqual('2026_01_02', version)
        self.assertEqual([], warnings)

        _, warnings = normalize_stored_version(
            'gs://other/wrong/Import/2026_01_02', 'bucket', 'scripts/a/Import')
        self.assertEqual([
            'stored_version_bucket_mismatch', 'stored_version_prefix_mismatch'
        ], warnings)

    def test_history_query_uses_names_range_and_limit_plus_one(self):
        snapshot = _Snapshot([_history_row(), _history_row()])
        start = datetime(2026, 1, 1, tzinfo=timezone.utc)
        end = datetime(2026, 2, 1, tzinfo=timezone.utc)

        result = query_version_history('project',
                                       'instance',
                                       'database',
                                       ['scripts/a:Import', 'Import'],
                                       1,
                                       start_time=start,
                                       end_time=end,
                                       client=_SpannerClient(snapshot))

        sql, params, _ = snapshot.calls[0]
        self.assertIn('ImportName IN UNNEST(@import_names)', sql)
        self.assertIn('UpdateTimestamp >= @start_time', sql)
        self.assertIn('UpdateTimestamp < @end_time', sql)
        self.assertEqual(2, params['limit'])
        self.assertEqual(['scripts/a:Import', 'Import'], params['import_names'])
        self.assertEqual(1, len(result['rows']))
        self.assertTrue(result['truncated'])

    def test_latest_version_query_groups_events_before_limiting(self):
        snapshot = _Snapshot([
            _history_row(version='2026_01_03',
                         update_timestamp=datetime(2026,
                                                   1,
                                                   3,
                                                   tzinfo=timezone.utc)),
            _history_row(version='2026_01_03',
                         comment='ingestion-workflow:loader-1',
                         update_timestamp=datetime(2026,
                                                   1,
                                                   3,
                                                   tzinfo=timezone.utc)),
            _history_row(version='2026_01_02'),
        ])

        result = query_latest_versions('project',
                                       'instance',
                                       'database',
                                       ['scripts/a:Import', 'Import'],
                                       2,
                                       client=_SpannerClient(snapshot))

        sql, params, _ = snapshot.calls[0]
        self.assertIn('MAX(UpdateTimestamp)', sql)
        self.assertIn('GROUP BY Version', sql)
        self.assertEqual(3, params['limit'])
        self.assertEqual(['2026_01_03', '2026_01_02'],
                         [row['Version'] for row in result['rows']])

    def test_import_version_queries_bare_and_uri_versions(self):
        snapshot = _Snapshot([])
        bucket = _Bucket({
            'scripts/a/Import/2026_01_02/import_summary.json':
                _Blob({
                    'import_name': 'Import',
                    'job_id': 'batch-1',
                    'latest_version': 'gs://bucket/scripts/a/Import/2026_01_02',
                })
        })

        result = correlate_import_runs('import_version',
                                       'scripts/a:Import',
                                       'project',
                                       'instance',
                                       'database',
                                       'project',
                                       'bucket',
                                       version='2026_01_02',
                                       spanner_client=_SpannerClient(snapshot),
                                       storage_client=_StorageClient(bucket))

        sql, params, _ = snapshot.calls[0]
        self.assertIn('Version IN UNNEST(@versions)', sql)
        self.assertEqual(
            ['2026_01_02', 'gs://bucket/scripts/a/Import/2026_01_02'],
            params['versions'])
        self.assertEqual(101, params['limit'])
        self.assertEqual(
            {
                'version': '2026_01_02',
                'gcs_base_path': 'gs://bucket/scripts/a/Import/2026_01_02',
                'workflow_execution_id': None,
                'batch_job_id': 'batch-1',
                'workflow_recorded_at': None,
                'gcs_summary_created_at': '2026-01-02T00:00:00+00:00',
                'missing': ['workflow_execution_id'],
            }, result['runs'][0])

    def test_history_reads_each_unique_summary_once(self):
        snapshot = _Snapshot([
            _history_row(comment='import-workflow:workflow-1'),
            _history_row(comment='ingestion-workflow:workflow-2'),
        ])
        bucket = _Bucket({
            'scripts/a/Import/2026_01_02/import_summary.json':
                _Blob({
                    'import_name': 'Import',
                    'job_id': 'batch-1',
                    'latest_version': 'gs://bucket/scripts/a/Import/2026_01_02',
                })
        })

        result = correlate_import_runs('import_history',
                                       'scripts/a:Import',
                                       'project',
                                       'instance',
                                       'database',
                                       'project',
                                       'bucket',
                                       limit=2,
                                       spanner_client=_SpannerClient(snapshot),
                                       storage_client=_StorageClient(bucket))

        self.assertEqual(1, len(bucket.requests))
        self.assertEqual(1, len(result['runs']))
        self.assertEqual('workflow-1',
                         result['runs'][0]['workflow_execution_id'])
        self.assertEqual('batch-1', result['runs'][0]['batch_job_id'])
        self.assertNotIn('history_events', result)
        self.assertNotIn('gcs_summaries', result)
        self.assertEqual(2, len(snapshot.calls))

    def test_missing_summary_and_workflow_are_partial_results(self):
        snapshot = _Snapshot([_history_row(comment='')])
        result = correlate_import_runs('import_history',
                                       'scripts/a:Import',
                                       'project',
                                       'instance',
                                       'database',
                                       'project',
                                       'bucket',
                                       spanner_client=_SpannerClient(snapshot),
                                       storage_client=_StorageClient(_Bucket(
                                           {})))

        self.assertEqual(
            ['workflow_execution_id', 'gcs_import_summary', 'batch_job_id'],
            result['runs'][0]['missing'])
        self.assertEqual(2, len(snapshot.calls))
        self.assertEqual(101, snapshot.calls[1][1]['limit'])

    def test_conflicting_workflow_ids_preserve_both(self):
        workflow = classify_workflow_reference({
            'WorkflowExecutionID': 'typed-id',
            'Comment': 'import-workflow:comment-id',
        })

        self.assertIsNone(workflow['execution_id'])
        self.assertEqual('typed-id', workflow['typed_execution_id'])
        self.assertEqual('comment-id', workflow['comment_execution_id'])
        self.assertEqual('ambiguous', workflow['confidence'])

    def test_mismatched_stored_uri_does_not_guess_summary(self):
        snapshot = _Snapshot(
            [_history_row(version='gs://other/wrong/Import/2026_01_02')])
        bucket = _Bucket({})

        result = correlate_import_runs('import_history',
                                       'scripts/a:Import',
                                       'project',
                                       'instance',
                                       'database',
                                       'project',
                                       'bucket',
                                       spanner_client=_SpannerClient(snapshot),
                                       storage_client=_StorageClient(bucket))

        self.assertEqual([], bucket.requests)
        self.assertEqual([], result['runs'])
        self.assertEqual(['newer_history_version_rejected'], result['issues'])
        self.assertTrue(result['truncated'])

    def test_history_limit_counts_versions_not_events(self):
        snapshot = _Snapshot([
            _history_row(version='2026_01_03',
                         comment='ingestion-workflow:loader-1',
                         update_timestamp=datetime(2026,
                                                   1,
                                                   3,
                                                   tzinfo=timezone.utc)),
            _history_row(version='2026_01_03',
                         comment='import-workflow:workflow-1',
                         update_timestamp=datetime(2026,
                                                   1,
                                                   3,
                                                   tzinfo=timezone.utc)),
            _history_row(version='2026_01_02',
                         comment='import-workflow:workflow-0'),
        ])
        bucket = _Bucket({
            'scripts/a/Import/2026_01_03/import_summary.json':
                _Blob({
                    'import_name': 'Import',
                    'job_id': 'batch-1',
                    'latest_version': 'gs://bucket/scripts/a/Import/2026_01_03',
                })
        })

        result = correlate_import_runs('import_history',
                                       'scripts/a:Import',
                                       'project',
                                       'instance',
                                       'database',
                                       'project',
                                       'bucket',
                                       spanner_client=_SpannerClient(snapshot),
                                       storage_client=_StorageClient(bucket))

        self.assertEqual(['2026_01_03'],
                         [run['version'] for run in result['runs']])
        self.assertEqual('workflow-1',
                         result['runs'][0]['workflow_execution_id'])
        self.assertTrue(result['truncated'])

    def test_history_limit_finds_versions_and_et_event_beyond_old_scan(self):
        newest = datetime(2026, 1, 3, tzinfo=timezone.utc)
        older = datetime(2026, 1, 2, tzinfo=timezone.utc)
        rows = [
            _history_row(version='2026_01_03',
                         comment='ingestion-workflow:loader-1',
                         update_timestamp=newest) for _ in range(20)
        ]
        rows.extend((
            _history_row(version='2026_01_03',
                         comment='import-workflow:workflow-1',
                         update_timestamp=older),
            _history_row(version='2026_01_02',
                         comment='import-workflow:workflow-0',
                         update_timestamp=older),
        ))
        snapshot = _Snapshot(rows)
        bucket = _Bucket({
            'scripts/a/Import/2026_01_03/import_summary.json':
                _Blob({
                    'import_name': 'Import',
                    'job_id': 'batch-1',
                    'latest_version': 'gs://bucket/scripts/a/Import/2026_01_03',
                }),
            'scripts/a/Import/2026_01_02/import_summary.json':
                _Blob({
                    'import_name': 'Import',
                    'job_id': 'batch-0',
                    'latest_version': 'gs://bucket/scripts/a/Import/2026_01_02',
                }),
        })

        result = correlate_import_runs('import_history',
                                       'scripts/a:Import',
                                       'project',
                                       'instance',
                                       'database',
                                       'project',
                                       'bucket',
                                       limit=2,
                                       spanner_client=_SpannerClient(snapshot),
                                       storage_client=_StorageClient(bucket))

        self.assertEqual(['2026_01_03', '2026_01_02'],
                         [run['version'] for run in result['runs']])
        self.assertEqual('workflow-1',
                         result['runs'][0]['workflow_execution_id'])
        self.assertFalse(result['truncated'])

    def test_rejected_newest_version_marks_older_result_incomplete(self):
        snapshot = _Snapshot([
            _history_row(version='gs://other/wrong/Import/2026_01_03',
                         update_timestamp=datetime(2026,
                                                   1,
                                                   3,
                                                   tzinfo=timezone.utc)),
            _history_row(version='2026_01_02'),
        ])
        bucket = _Bucket({
            'scripts/a/Import/2026_01_02/import_summary.json':
                _Blob({
                    'import_name': 'Import',
                    'job_id': 'batch-1',
                    'latest_version': 'gs://bucket/scripts/a/Import/2026_01_02',
                })
        })

        result = correlate_import_runs('import_history',
                                       'scripts/a:Import',
                                       'project',
                                       'instance',
                                       'database',
                                       'project',
                                       'bucket',
                                       spanner_client=_SpannerClient(snapshot),
                                       storage_client=_StorageClient(bucket))

        self.assertEqual(['2026_01_02'],
                         [run['version'] for run in result['runs']])
        self.assertEqual(['newer_history_version_rejected'], result['issues'])
        self.assertTrue(result['truncated'])

    def test_empty_batch_job_id_is_missing(self):
        snapshot = _Snapshot([])
        bucket = _Bucket({
            'scripts/a/Import/2026_01_02/import_summary.json':
                _Blob({
                    'import_name': 'Import',
                    'job_id': '',
                    'latest_version': 'gs://bucket/scripts/a/Import/2026_01_02',
                })
        })

        result = correlate_import_runs('import_version',
                                       'scripts/a:Import',
                                       'project',
                                       'instance',
                                       'database',
                                       'project',
                                       'bucket',
                                       version='2026_01_02',
                                       spanner_client=_SpannerClient(snapshot),
                                       storage_client=_StorageClient(bucket))

        self.assertEqual('', result['runs'][0]['batch_job_id'])
        self.assertIn('batch_job_id', result['runs'][0]['missing'])

    def test_validates_bounds_and_timestamps(self):
        with self.assertRaisesRegex(ImportRunCorrelationError,
                                    'include a timezone'):
            parse_rfc3339('2026-01-01T00:00:00')
        with self.assertRaisesRegex(ImportRunCorrelationError,
                                    'between 1 and 20'):
            correlate_import_runs('import_history',
                                  'scripts/a:Import',
                                  'p',
                                  'i',
                                  'd',
                                  'p',
                                  'bucket',
                                  limit=21,
                                  spanner_client=_SpannerClient(_Snapshot([])),
                                  storage_client=_StorageClient(_Bucket({})))


if __name__ == '__main__':
    unittest.main()

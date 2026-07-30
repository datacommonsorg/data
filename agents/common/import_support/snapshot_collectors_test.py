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
"""Tests for safe cloud snapshot transformations."""

import base64
import json
import unittest

from agents.common.import_support.snapshot_collectors import composite_status
from agents.common.import_support.snapshot_collectors import collect_batch_logs
from agents.common.import_support.snapshot_collectors import collect_gcs_evidence
from agents.common.import_support.snapshot_collectors import decode_scheduler_job
from agents.common.import_support.snapshot_collectors import list_import_objects
from agents.common.import_support.snapshot_collectors import read_spanner_records
from agents.common.import_support.snapshot_collectors import safe_batch_job
from agents.common.import_support.snapshot_collectors import _SPANNER_COLUMNS


class _Runner:

    def __init__(self, result):
        self.result = result
        self.args = None

    def run_json(self, args, timeout=None):
        del timeout
        self.args = args
        return self.result


class _GcsRunner:

    def __init__(self):
        self.calls = []

    def run_json(self, args, timeout=None):
        del timeout
        self.calls.append(args)
        if args[4].endswith('/**/import_summary.json'):
            return [{
                'bucket': 'bucket',
                'name': 'prefix/version/import_summary.json',
            }]
        return [{
            'bucket': 'bucket',
            'name': f'prefix/object-{index:04d}.mcf',
        } for index in range(1001)]

    def run_text(self, args, timeout=None):
        del timeout
        uri = args[3]
        if uri.endswith('/import_summary.json'):
            return json.dumps({
                'import_name': 'ImportOne',
                'job_id': 'job-one',
                'status': 'STAGING',
            })
        return 'version-one'


class _Snapshot:

    def __init__(self, include_schema=True):
        self.calls = []
        self._include_schema = include_schema

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        del exc_type, exc_value, traceback

    def execute_sql(self, sql, params, param_types):
        self.calls.append((sql, params, param_types))
        if 'INFORMATION_SCHEMA' in sql:
            if not self._include_schema:
                return []
            return [(table, column)
                    for table, columns in _SPANNER_COLUMNS.items()
                    for column in columns]
        return []


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


class SnapshotCollectorsTest(unittest.TestCase):

    def test_scheduler_decoding_keeps_only_safe_config(self):
        argument = {
            'importName':
                'scripts/a:Import',
            'importConfig':
                json.dumps({
                    'gcs_project_id': 'gcs-project',
                    'storage_prod_bucket_name': 'bucket',
                    'dc_api_key': 'must-not-escape',
                }),
        }
        body = base64.b64encode(
            json.dumps({
                'argument': json.dumps(argument)
            }).encode()).decode()
        safe = decode_scheduler_job({
            'name': 'job',
            'httpTarget': {
                'uri': 'https://workflowexecutions.googleapis.com/v1/x',
                'body': body,
            },
        })

        self.assertEqual('scripts/a:Import', safe['target_import_name'])
        self.assertEqual(
            'bucket', safe['target_import_config']['storage_prod_bucket_name'])
        self.assertNotIn('dc_api_key', safe['target_import_config'])

    def test_batch_job_keeps_identity_config_and_resource_facts(self):
        job = {
            'name':
                'projects/p/locations/l/jobs/job',
            'taskGroups': [{
                'taskSpec': {
                    'runnables': [{
                        'container': {
                            'imageUri':
                                'host/project/repo/image:tag',
                            'commands': [
                                '--import_name=scripts/a:Import',
                                '--import_config={"gcs_project_id":"p",'
                                '"dc_api_key":"secret"}',
                            ],
                        }
                    }],
                    'computeResource': {
                        'cpuMilli': 4000
                    },
                }
            }],
        }

        safe = safe_batch_job(job)

        self.assertEqual('scripts/a:Import', safe['import_identity'])
        self.assertEqual({'gcs_project_id': 'p'}, safe['import_config'])
        self.assertEqual(4000, safe['compute_resource']['cpuMilli'])

    def test_storage_listing_is_json_and_bounded(self):
        runner = _Runner([{
            'bucket': 'bucket',
            'name': 'prefix/one.mcf'
        }, {
            'bucket': 'bucket',
            'name': 'prefix/two.mcf'
        }])

        objects, truncated = list_import_objects(runner, 'project', 'bucket',
                                                 'prefix', 1)

        self.assertTrue(truncated)
        self.assertEqual('gs://bucket/prefix/one.mcf', objects[0]['uri'])
        self.assertEqual('objects', runner.args[2])
        self.assertIn('--limit=2', runner.args)

    def test_summary_listing_is_independent_of_artifact_limit(self):
        result = collect_gcs_evidence(_GcsRunner(), 'project', 'bucket',
                                      'prefix', (), 'ImportOne', {'job-one'},
                                      'latest_version.txt', 1000)

        self.assertIn('job-one', result['summaries_by_job_id'])
        self.assertFalse(result['summary_truncated'])
        self.assertTrue(result['objects_truncated'])
        self.assertTrue(result['truncated'])

    def test_batch_logs_are_structured_bounded_and_chronological(self):
        runner = _Runner([{
            'timestamp': '2026-01-01T00:00:03Z',
            'severity': 'ERROR',
            'logName': 'projects/project/logs/batch_task_logs',
            'labels': {
                'job_uid': 'uid-one'
            },
            'jsonPayload': {
                'log_type': 'auto-import-job-stage',
                'stage': 'VALIDATION',
                'latency': 3,
                'status': {
                    'credential': 'must-not-escape'
                },
                'message': 'secret-bearing free text',
            },
            'textPayload': 'more free text',
        }, {
            'timestamp': '2026-01-01T00:00:02Z',
            'labels': {
                'job_uid': 'uid-one'
            },
            'jsonPayload': {
                'log_type': 'auto-import-job-status',
                'import_name': 'ImportOne',
                'stage_name': 'COMPLETED',
                'status': 'SUCCESS',
            },
        }, {
            'timestamp': '2026-01-01T00:00:01Z',
            'jsonPayload': {
                'log_type': 'auto-import-job-status',
            },
        }])

        logs, truncated = collect_batch_logs(runner, 'project', 'uid-one',
                                             '2026-01-01T00:00:00Z',
                                             '2026-01-01T00:01:00Z', 2)

        self.assertTrue(truncated)
        self.assertEqual(['2026-01-01T00:00:02Z', '2026-01-01T00:00:03Z'],
                         [entry['timestamp'] for entry in logs])
        self.assertEqual('VALIDATION', logs[-1]['json_payload']['stage_name'])
        self.assertNotIn('message', logs[-1]['json_payload'])
        self.assertNotIn('status', logs[-1]['json_payload'])
        log_filter = runner.args[3]
        self.assertIn('projects/project/logs/batch_task_logs', log_filter)
        self.assertIn('labels.job_uid="uid-one"', log_filter)
        self.assertNotIn('resource.type="batch_task"', log_filter)
        self.assertIn('--order=desc', runner.args)
        self.assertIn('--limit=3', runner.args)

    def test_semantic_failure_overrides_technical_success(self):
        run = {'state': 'SUCCEEDED'}
        jobs = [{'status': {'state': 'SUCCEEDED'}}]

        self.assertEqual(
            'failed',
            composite_status(run,
                             jobs, {'status': 'VALIDATION'},
                             publication_observed=False))
        self.assertEqual(
            'succeeded',
            composite_status(run,
                             jobs, {'status': 'STAGING'},
                             publication_observed=True))

    def test_spanner_schema_is_verified_and_queries_are_parameterized(self):
        snapshot = _Snapshot()

        result = read_spanner_records('project',
                                      'instance',
                                      'database',
                                      'ImportOne',
                                      client=_SpannerClient(snapshot))

        self.assertEqual({}, result['import_status'])
        self.assertEqual(4, len(snapshot.calls))
        for sql, params, _ in snapshot.calls[1:]:
            self.assertNotIn('ImportOne', sql)
            self.assertEqual('ImportOne', params['import_name'])

    def test_spanner_schema_drift_stops_data_queries(self):
        snapshot = _Snapshot(include_schema=False)

        with self.assertRaisesRegex(ValueError, 'Unsupported Spanner schema'):
            read_spanner_records('project',
                                 'instance',
                                 'database',
                                 'ImportOne',
                                 client=_SpannerClient(snapshot))

        self.assertEqual(1, len(snapshot.calls))


if __name__ == '__main__':
    unittest.main()

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
"""Tests for import snapshot orchestration."""

from dataclasses import replace
from datetime import datetime
from datetime import timezone
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from agents.common.import_support.collect_import_snapshot import build_snapshot
from agents.common.import_support.collect_import_snapshot import _candidate_import_names
from agents.common.import_support.collect_import_snapshot import _collector_help
from agents.common.import_support.collect_import_snapshot import _collect_run
from agents.common.import_support.collect_import_snapshot import _fleet_matches
from agents.common.import_support.collect_import_snapshot import _latest_successful_run
from agents.common.import_support.collect_import_snapshot import SnapshotError
from agents.common.import_support.collect_import_snapshot import SnapshotOptions
from agents.common.import_support.collect_import_snapshot import validate_snapshot
from agents.common.import_support.command_runner import CommandError
from agents.common.import_support.resolve_import import build_import_catalog
from agents.common.import_support.resolve_import import resolve_import


class _UnavailableRunner:

    def run_json(self, args, timeout=None):
        del args, timeout
        raise CommandError('permission denied')


class CollectImportSnapshotTest(unittest.TestCase):

    def _repo(self, root: Path) -> None:
        for directory in ('statvar_imports/agency/import_one', 'scripts',
                          'import-automation/executor/app',
                          'agents/common/schemas'):
            (root / directory).mkdir(parents=True, exist_ok=True)
        (root / 'requirements_all.txt').write_text('', encoding='utf-8')
        (root / 'run_tests.sh').write_text('', encoding='utf-8')
        (root / 'import-automation/executor/app/configs.py').write_text(
            'class ExecutorConfig:\n'
            "    gcp_project_id: str = 'prod-project'\n"
            "    gcs_project_id: str = 'gcs-project'\n"
            "    scheduler_location: str = 'us-central1'\n"
            "    storage_prod_bucket_name: str = 'bucket'\n"
            "    storage_version_filename: str = 'latest_version.txt'\n"
            "    cloud_workflow_id: str = 'workflow'\n",
            encoding='utf-8')
        manifest = {
            'import_specifications': [{
                'import_name': 'ImportOne',
                'cron_schedule': '0 1 * * *',
            }]
        }
        (root / 'statvar_imports/agency/import_one/manifest.json').write_text(
            json.dumps(manifest), encoding='utf-8')
        source_schema = (Path(__file__).parents[1] / 'schemas' /
                         'import_snapshot.schema.json')
        (root / 'agents/common/schemas/import_snapshot.schema.json').write_text(
            source_schema.read_text(encoding='utf-8'), encoding='utf-8')

    def _options(self) -> SnapshotOptions:
        return SnapshotOptions(
            mode='single_import',
            import_name='ImportOne',
            manifest_path='',
            environment='prod',
            scheduler_project='',
            scheduler_location='',
            start_time=datetime(2026, 1, 1, tzinfo=timezone.utc),
            end_time=datetime(2026, 1, 2, tzinfo=timezone.utc),
            run_limit=10,
            scan_limit=100,
            import_limit=100,
            status='',
            import_name_pattern='',
            consecutive_failures=0,
            log_limit=20,
            object_limit=50,
            gcs_project='',
            gcs_bucket='',
            helper_project='',
            helper_location='',
            helper_service='ingestion-helper-service',
            spanner_project='',
            spanner_instance='',
            spanner_database='',
            history_limit=10,
            build_project='',
            build_region='global',
            verbose=False,
        )

    def test_help_lists_collector_flags(self):
        help_text = _collector_help()

        for flag in ('--mode', '--import_name', '--scheduler_project',
                     '--start_time', '--run_limit', '--[no]verbose'):
            with self.subTest(flag=flag):
                self.assertIn(flag, help_text)

    def test_missing_cloud_access_returns_valid_partial_snapshot(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self._repo(root)

            snapshot = build_snapshot(root,
                                      self._options(),
                                      runner=_UnavailableRunner())
            validate_snapshot(root, snapshot)

            item = snapshot['imports'][0]
            self.assertTrue(item['auto_refresh']['configured'])
            self.assertFalse(item['auto_refresh']['deployed'])
            self.assertIn('Scheduler evidence unavailable', item['warnings'][0])

    def test_nonproduction_requires_explicit_coordinates(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self._repo(root)
            options = replace(self._options(), environment='staging')

            with self.assertRaisesRegex(SnapshotError, 'never inferred'):
                build_snapshot(root, options, runner=_UnavailableRunner())

    def test_conflicting_production_coordinates_require_clarification(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self._repo(root)
            options = replace(self._options(), scheduler_project='other')

            with self.assertRaisesRegex(SnapshotError, 'conflicts'):
                build_snapshot(root, options, runner=_UnavailableRunner())

    @mock.patch(
        'agents.common.import_support.collect_import_snapshot.collect_runtime_provenance'
    )
    @mock.patch(
        'agents.common.import_support.collect_import_snapshot.collect_batch_logs'
    )
    def test_preliminary_fleet_status_skips_expensive_reads(
            self, collect_logs, collect_provenance):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self._repo(root)
            record = resolve_import(build_import_catalog(root), 'ImportOne')
            run = {
                'id': 'execution-one',
                'state': 'SUCCEEDED',
                'start_time': '2026-01-01T00:00:00Z',
            }
            batch = {
                'correlation':
                    'exact',
                'evidence': ['job id'],
                'jobs': [{
                    'uid': 'uid-one',
                    'resource_name': 'projects/p/locations/l/jobs/job-one',
                    'image_uri': 'host/project/repo/image:stable',
                    'status': {
                        'state': 'SUCCEEDED'
                    },
                }],
            }
            gcs = {
                'summaries_by_job_id': {
                    'uid-one': {
                        'status': 'VALIDATION'
                    }
                },
                'artifacts_by_job_id': {},
                'version_pointers': {},
            }

            result = _collect_run(root,
                                  _UnavailableRunner(),
                                  replace(self._options(), mode='fleet'), {
                                      'scheduler_project': 'project',
                                      'scheduler_location': 'location',
                                  },
                                  record, {},
                                  run,
                                  gcs, {},
                                  batch,
                                  include_expensive=False)

            self.assertEqual('failed', result['status']['composite'])
            collect_logs.assert_not_called()
            collect_provenance.assert_not_called()

    def test_summary_fallback_requires_unavailable_batch_evidence(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self._repo(root)
            record = resolve_import(build_import_catalog(root), 'ImportOne')
            run = {
                'id': 'execution-one',
                'state': 'SUCCEEDED',
                'result': {
                    'job_id': 'job-one'
                },
            }
            gcs = {
                'summaries_by_job_id': {
                    'job-one': {
                        'import_name': 'ImportOne',
                        'job_id': 'job-one',
                        'status': 'STAGING',
                    }
                },
                'artifacts_by_job_id': {},
                'version_pointers': {},
            }
            cases = ({
                'name': 'expired job',
                'batch': {
                    'jobs': [],
                    'expected_job_id': 'job-one',
                    'unavailable_reason': 'batch_lookup_failed',
                },
                'summary_status': 'STAGING',
                'summary_correlation': 'strongly_correlated',
            }, {
                'name': 'mismatched identity',
                'batch': {
                    'correlation': 'ambiguous',
                    'evidence': ['batch runnable import identity'],
                    'expected_job_id': 'job-one',
                    'unavailable_reason': None,
                    'jobs': [{
                        'import_identity': 'path:OtherImport'
                    }],
                },
                'summary_status': None,
                'summary_correlation': 'unknown',
            })

            for case in cases:
                with self.subTest(case=case['name']):
                    result = _collect_run(root,
                                          _UnavailableRunner(),
                                          self._options(), {
                                              'scheduler_project': 'project',
                                              'scheduler_location': 'location',
                                          },
                                          record, {},
                                          run,
                                          gcs, {},
                                          case['batch'],
                                          include_expensive=False)

                    self.assertEqual(case['summary_status'],
                                     result['import_summary'].get('status'))
                    self.assertEqual(case['summary_correlation'],
                                     result['correlation']['batch_to_summary'])

    @mock.patch(
        'agents.common.import_support.collect_import_snapshot.collect_runtime_provenance'
    )
    def test_runtime_provenance_uses_batch_task_start(self, provenance):
        provenance.return_value = {'confidence': 'unknown'}
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self._repo(root)
            record = resolve_import(build_import_catalog(root), 'ImportOne')
            run = {
                'id': 'execution-one',
                'state': 'SUCCEEDED',
                'start_time': '2026-01-01T00:00:00Z',
            }
            batch = {
                'correlation':
                    'exact',
                'evidence': ['verified identity'],
                'jobs': [{
                    'resource_name':
                        'projects/p/locations/l/jobs/job-one',
                    'image_uri':
                        'host/project/repo/image:stable',
                    'create_time':
                        '2026-01-01T00:01:00Z',
                    'status': {
                        'state': 'SUCCEEDED'
                    },
                    'tasks': [{
                        'status': {
                            'status_events': [{
                                'task_state': 'RUNNING',
                                'event_time': '2026-01-01T00:02:00Z',
                            }]
                        }
                    }],
                }],
            }

            result = _collect_run(root, _UnavailableRunner(), self._options(), {
                'scheduler_project': 'project',
                'scheduler_location': 'location',
            }, record, {}, run, {'version_pointers': {}}, {}, batch)

            self.assertEqual('2026-01-01T00:02:00Z',
                             provenance.call_args.kwargs['task_start_time'])
            self.assertEqual('batch_task_running_event',
                             result['runtime_provenance']['time_basis'])

    def test_consecutive_failures_stop_at_unknown_or_running(self):
        options = replace(self._options(), mode='fleet', consecutive_failures=2)

        def item(*statuses):
            return {
                'identity': {
                    'import_name': 'ImportOne'
                },
                'runs': [{
                    'status': {
                        'composite': status
                    }
                } for status in statuses],
            }

        self.assertTrue(_fleet_matches(item('failed', 'failed'), options))
        self.assertFalse(
            _fleet_matches(item('failed', 'unknown', 'failed'), options))
        self.assertFalse(
            _fleet_matches(item('failed', 'running', 'failed'), options))

    def test_latest_success_can_come_from_version_history(self):
        latest = _latest_successful_run(
            [{
                'id': 'recent-failure',
                'status': {
                    'composite': 'failed'
                },
            }], {
                'version_history': [{
                    'Version': 'version-one',
                    'UpdateTimestamp': '2025-12-31T23:00:00Z',
                    'Status': 'STAGING',
                    'Comment': 'import-workflow:older-success',
                }]
            })

        self.assertEqual('older-success', latest['id'])
        self.assertEqual('version-one', latest['version'])
        self.assertEqual('spanner_version_history', latest['source'])
        self.assertTrue(latest['complete'])

    def test_latest_success_is_explicitly_incomplete_when_unobserved(self):
        latest = _latest_successful_run([], {})

        self.assertIsNone(latest['id'])
        self.assertFalse(latest['complete'])

    def test_fleet_name_filter_is_applied_before_candidate_cap(self):
        executions = [{
            'argument': {
                'import_name': f'path:Import{index:03d}'
            }
        } for index in range(200)]
        executions.append({'argument': {'import_name': 'path:TargetImport'}})
        by_absolute = {
            execution['argument']['import_name']:
                mock.Mock(import_name=execution['argument']
                          ['import_name'].rsplit(':', 1)[-1])
            for execution in executions
        }

        names, truncated = _candidate_import_names(executions, by_absolute,
                                                   'target', 200)

        self.assertEqual(['path:TargetImport'], names)
        self.assertFalse(truncated)

    def test_consecutive_failure_limit_cannot_exceed_run_limit(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self._repo(root)
            options = replace(self._options(),
                              run_limit=1,
                              consecutive_failures=2)

            with self.assertRaisesRegex(SnapshotError, 'cannot exceed'):
                build_snapshot(root, options, runner=_UnavailableRunner())


if __name__ == '__main__':
    unittest.main()

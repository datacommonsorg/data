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
"""Tests executable contracts for import-diagnostics references."""

from pathlib import Path
import unittest

_MUTATING_GCLOUD_COMMANDS = (
    'gcloud scheduler jobs run',
    'gcloud workflows execute',
    'gcloud batch jobs delete',
    'gcloud run services update',
    'gcloud builds submit',
    'gcloud storage cp',
    'gcloud storage mv',
    'gcloud storage rm',
)


class DiagnosticsReferenceTest(unittest.TestCase):

    def setUp(self):
        self._repo_root = Path(__file__).parents[3]
        self._reference_root = (
            self._repo_root / 'agents/skills/dc-import-diagnostics/references')

    def _read_reference(self, name: str) -> str:
        return (self._reference_root / name).read_text(encoding='utf-8')

    def _read_operation(self, name: str, heading: str) -> str:
        reference = self._read_reference(name)
        marker = f'\n## {heading}\n'
        self.assertIn(marker, reference)
        operation = reference.split(marker, maxsplit=1)[1]
        return operation.split('\n## ', maxsplit=1)[0]

    def test_operational_references_do_not_document_mutating_gcloud_commands(
            self):
        references = '\n'.join(
            self._read_reference(name) for name in (
                'imports.md',
                'scheduler.md',
                'spanner.md',
                'gcs.md',
                'batch.md',
            ))

        for command in _MUTATING_GCLOUD_COMMANDS:
            with self.subTest(command=command):
                self.assertNotIn(command, references)

    def test_spanner_reference_supports_only_bounded_current_snapshot_queries(
            self):
        operation = self._read_operation(
            'spanner.md', 'Query the current import-status snapshot')
        sql_lines = [
            line for line in operation.splitlines() if '--sql=' in line
        ]

        self.assertEqual(3, len(sql_lines))
        self.assertTrue(all('WorkflowId' not in line for line in sql_lines))
        self.assertIn(
            "ImportName IN ('<ABSOLUTE_IMPORT_NAME>', '<SIMPLE_IMPORT_NAME>')",
            sql_lines[0])
        self.assertIn("LatestVersion = '<GCS_VERSION_URI>'", sql_lines[1])
        self.assertIn(
            "StatusUpdateTimestamp >= TIMESTAMP('<START_RFC3339_UTC>')",
            sql_lines[2])
        self.assertIn("StatusUpdateTimestamp < TIMESTAMP('<END_RFC3339_UTC>')",
                      sql_lines[2])
        self.assertIn('LIMIT <LIMIT_PLUS_ONE>', sql_lines[2])
        self.assertIn("AND State = '<STATE>'", operation)

    def test_scheduler_reference_keeps_missing_body_distinct_from_bad_body(
            self):
        operation = self._read_operation('scheduler.md',
                                         'Describe and verify a Scheduler job')

        self.assertIn('gcloud scheduler jobs describe <IMPORT_NAME>', operation)
        self.assertIn('if .httpTarget.body', operation)
        self.assertIn('else null', operation)
        self.assertIn('| @base64d | fromjson |', operation)
        self.assertNotIn('fromjson?', operation)
        self.assertNotIn('try ', operation)

    def test_provenance_operation_uses_exact_batch_and_image_resources(self):
        operation = self._read_operation(
            'batch.md', 'Trace a Batch job to source-commit evidence')

        self.assertIn('[Describe Batch job](#describe-one-batch-job)',
                      operation)
        self.assertIn("gcloud artifacts docker images describe '<IMAGE_URI>'",
                      operation)
        self.assertIn('/dockerImages/<URL_ENCODED_IMAGE_AT_DIGEST>', operation)
        self.assertIn("cat-file -e '<GIT_SHA>^{commit}'", operation)
        self.assertNotIn('gcloud builds list', operation)
        self.assertNotIn('gcloud builds describe', operation)
        self.assertNotIn('gcloud artifacts versions describe', operation)

    def test_gcs_reference_keeps_distinct_bounded_operations(self):
        summary_list = self._read_operation('gcs.md',
                                            'List recent import versions')
        version_summary = self._read_operation(
            'gcs.md', 'Read one import version summary')
        last_successful = self._read_operation(
            'gcs.md', 'Find the last successful import version')
        artifacts = self._read_operation(
            'gcs.md', 'List artifacts for one import version')

        for required in ('./agents/common/run_python.sh',
                         'agents/common/scripts/list_import_summaries.py',
                         "--absolute_import_name='<DIRECTORY>:<IMPORT_NAME>'",
                         "--gcs_project='<PROJECT>'", "--gcs_bucket='<BUCKET>'",
                         "--limit='<1_TO_5>'"):
            with self.subTest(summary_list=required):
                self.assertIn(required, summary_list)

        self.assertIn('gcloud storage cat', version_summary)
        self.assertIn('/<VERSION>/import_summary.json', version_summary)
        self.assertIn('/latest_version.txt', last_successful)
        self.assertNotIn('/staging_version.txt', last_successful)
        self.assertIn('gcloud storage objects list', artifacts)
        self.assertIn('/<VERSION>/**', artifacts)
        self.assertIn('--limit=<LIMIT_PLUS_ONE>', artifacts)

    def test_batch_task_and_log_operations_require_exact_bounds(self):
        batch = self._read_operation('batch.md', 'Describe one Batch job')
        tasks = self._read_operation('batch.md', 'List tasks for one Batch job')
        logs = self._read_operation('batch.md', 'Fetch bounded Batch logs')
        logging_reference = (
            self._repo_root /
            'agents/common/references/gcp/logging.md').read_text(
                encoding='utf-8')

        self.assertIn('gcloud batch jobs describe <JOB_ID>', batch)
        self.assertNotIn('gcloud batch jobs list', batch)
        self.assertIn('gcloud batch tasks list', tasks)
        self.assertIn('--job=<JOB_ID>', tasks)
        self.assertIn('--limit=<LIMIT_PLUS_ONE>', tasks)
        self.assertIn('truncated: (length > $limit)', tasks)

        self.assertIn('../../../common/references/gcp/logging.md', logs)
        self.assertIn('labels.job_uid="<JOB_UID>"', logs)
        self.assertIn('timestamp >= "<START>"', logs)
        self.assertIn('timestamp < "<END>"', logs)
        self.assertIn('LIMIT = <LIMIT_PLUS_ONE>', logs)
        self.assertIn("gcloud logging read '<FILTER>'", logging_reference)
        self.assertIn("--limit='<LIMIT>'", logging_reference)

    def test_python_wrapper_uses_repository_environment(self):
        wrapper = (self._repo_root /
                   'agents/common/run_python.sh').read_text(encoding='utf-8')

        self.assertIn('.env/bin/python', wrapper)


if __name__ == '__main__':
    unittest.main()

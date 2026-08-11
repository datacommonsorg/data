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
"""Tests structural and executable contracts for agent recipes."""

from pathlib import Path
import unittest

_RECIPE_HEADINGS = (
    '## Use when',
    '## Required inputs',
    '## Clarify when',
    '## Read-only operation',
    '## Preferred invocation',
    '## Expected output',
    '## Required bounds',
    '## Evidence to retain',
    '## Common failures',
    '## Related repository sources',
)
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


class RecipeContractTest(unittest.TestCase):

    def setUp(self):
        self._repo_root = Path(__file__).parents[3]
        self._recipe_root = self._repo_root / 'agents/common/recipes'
        self._recipe_paths = tuple(
            path for path in self._recipe_root.rglob('*.md')
            if path.name != 'README.md')

    def _read_recipe(self, relative_path: str) -> str:
        return (self._recipe_root / relative_path).read_text(encoding='utf-8')

    def test_recipes_have_standard_structure_and_placement(self):
        self.assertGreater(len(self._recipe_paths), 1)
        self.assertTrue((self._recipe_root / 'README.md').is_file())

        for path in self._recipe_paths:
            relative = path.relative_to(self._recipe_root)
            text = path.read_text(encoding='utf-8')
            with self.subTest(path=relative):
                if relative.parts[0] == 'local':
                    self.assertGreaterEqual(len(relative.parts), 2)
                else:
                    self.assertEqual('gcp', relative.parts[0])
                    self.assertGreaterEqual(len(relative.parts), 3)
                for heading in _RECIPE_HEADINGS:
                    self.assertIn(heading, text)

    def test_recipes_do_not_document_mutating_gcloud_commands(self):
        recipes = '\n'.join(
            path.read_text(encoding='utf-8') for path in self._recipe_paths)

        for command in _MUTATING_GCLOUD_COMMANDS:
            with self.subTest(command=command):
                self.assertNotIn(command, recipes)

    def test_spanner_recipe_supports_only_bounded_current_snapshot_queries(
            self):
        recipe = self._read_recipe('gcp/spanner/query-import-status.md')
        sql_lines = [line for line in recipe.splitlines() if '--sql=' in line]

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
        self.assertIn("AND State = '<STATE>'", recipe)

    def test_scheduler_recipe_keeps_missing_body_distinct_from_bad_body(self):
        recipe = self._read_recipe('gcp/scheduler/describe-job.md')

        self.assertIn('gcloud scheduler jobs describe <IMPORT_NAME>', recipe)
        self.assertIn('if .httpTarget.body', recipe)
        self.assertIn('else null', recipe)
        self.assertIn('| @base64d | fromjson |', recipe)
        self.assertNotIn('fromjson?', recipe)
        self.assertNotIn('try ', recipe)

    def test_provenance_recipe_uses_exact_batch_and_image_resources(self):
        recipe = self._read_recipe('gcp/batch/trace-batch-job-source-commit.md')

        self.assertIn('[Describe Batch job](describe-job.md)', recipe)
        self.assertIn("gcloud artifacts docker images describe '<IMAGE_URI>'",
                      recipe)
        self.assertIn('/dockerImages/<URL_ENCODED_IMAGE_AT_DIGEST>', recipe)
        self.assertIn("cat-file -e '<GIT_SHA>^{commit}'", recipe)
        self.assertNotIn('gcloud builds list', recipe)
        self.assertNotIn('gcloud builds describe', recipe)
        self.assertNotIn('gcloud artifacts versions describe', recipe)

    def test_gcs_recipes_keep_distinct_bounded_operations(self):
        summary_list = self._read_recipe('gcp/gcs/list-import-summaries.md')
        version_summary = self._read_recipe('gcp/gcs/read-version-summary.md')
        pointer = self._read_recipe('gcp/gcs/read-version-pointer.md')
        artifacts = self._read_recipe('gcp/gcs/list-version-artifacts.md')

        for required in ('./agents/common/run_python.sh',
                         'agents/common/scripts/list_import_summaries.py',
                         "--absolute_import_name='<DIRECTORY>:<IMPORT_NAME>'",
                         "--gcs_project='<PROJECT>'", "--gcs_bucket='<BUCKET>'",
                         "--limit='<1_TO_5>'"):
            with self.subTest(summary_list=required):
                self.assertIn(required, summary_list)

        self.assertIn('gcloud storage cat', version_summary)
        self.assertIn('/<VERSION>/import_summary.json', version_summary)
        self.assertIn('/staging_version.txt', pointer)
        self.assertIn('/latest_version.txt', pointer)
        self.assertIn('gcloud storage objects list', artifacts)
        self.assertIn('/<VERSION>/**', artifacts)
        self.assertIn('--limit=<LIMIT_PLUS_ONE>', artifacts)

    def test_batch_task_and_log_operations_require_exact_bounds(self):
        batch = self._read_recipe('gcp/batch/describe-job.md')
        tasks = self._read_recipe('gcp/batch/list-tasks.md')
        logs = self._read_recipe('gcp/logging/fetch-batch-logs.md')
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

        self.assertIn('../../../references/gcp/logging.md', logs)
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

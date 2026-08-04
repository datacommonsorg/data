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
"""Tests for the repository-local agent skill contract."""

import json
from pathlib import Path
import re
import unittest

import yaml

_MARKDOWN_LINK = re.compile(r'\[[^]]+\]\(([^)]+)\)')
_TEXT_SUFFIXES = {'.json', '.md', '.py', '.sh', '.yaml', '.yml'}
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


class SkillContractTest(unittest.TestCase):

    def setUp(self):
        self._repo_root = Path(__file__).parents[3]
        self._skill_path = (self._repo_root /
                            'agents/skills/dc-import-info/SKILL.md')
        self._reference_root = (self._repo_root / 'agents/common/references' /
                                'import-automation')
        self._recipe_root = self._repo_root / 'agents/common/recipes'

    def _read(self, relative_path: str) -> str:
        return (self._repo_root / relative_path).read_text(encoding='utf-8')

    def test_registry_points_to_versioned_skill(self):
        registry = json.loads(self._read('.agents/skills.json'))
        paths = [entry['path'] for entry in registry['entries']]

        self.assertEqual(['agents/skills/dc-import-info'], paths)
        self.assertTrue((self._repo_root / paths[0] / 'SKILL.md').is_file())

    def test_recipes_have_invocation_contract(self):
        recipe_paths = list(self._recipe_root.glob('**/*.md'))

        self.assertGreater(len(recipe_paths), 1)
        for path in recipe_paths:
            text = path.read_text(encoding='utf-8')
            with self.subTest(path=path):
                for heading in _RECIPE_HEADINGS:
                    self.assertIn(heading, text)

    def test_agent_documentation_links_exist(self):
        paths = [
            self._skill_path,
            *self._reference_root.glob('*.md'),
            *self._recipe_root.glob('**/*.md'),
        ]

        for path in paths:
            for target in _MARKDOWN_LINK.findall(
                    path.read_text(encoding='utf-8')):
                if '://' in target or target.startswith('#'):
                    continue
                with self.subTest(source=path, target=target):
                    self.assertTrue((path.parent / target).resolve().is_file())

    def test_reusable_agent_artifacts_are_framework_neutral(self):
        framework_name = 'anti' + 'gravity'
        roots = [self._repo_root / '.agents', self._repo_root / 'agents']

        for root in roots:
            for path in root.rglob('*'):
                if not path.is_file() or path.suffix not in _TEXT_SUFFIXES:
                    continue
                with self.subTest(path=path):
                    self.assertNotIn(
                        framework_name,
                        path.read_text(encoding='utf-8').lower(),
                    )

    def test_skill_keeps_safety_and_conditional_navigation(self):
        skill = self._skill_path.read_text(encoding='utf-8')
        normalized = re.sub(r'\s+', ' ', skill)

        for required in (
                'review: skipped (headless)', 'Infrastructure actually used',
                'Never use MCP tools', "caller's existing GCP authentication",
                'Classify the request before loading context',
                'Do not load architecture, environment configuration, or cloud recipes',
                '../../common/recipes/repository/list-imports.md',
                'read only the selected manifest or requested code'):
            with self.subTest(required=required):
                self.assertIn(required, normalized)

        self.assertNotIn('architecture.md). 3.', normalized)
        self.assertNotIn('## Contents', skill)

    def test_runtime_environment_registry_remains_minimal_and_complete(self):
        registry = yaml.safe_load(
            self._read('agents/common/config/import-environments.yaml'))
        skill = self._skill_path.read_text(encoding='utf-8')
        resolution = self._read(
            'agents/common/references/import-automation/environment-resolution.md'
        )

        self.assertIn('../../common/config/import-environments.yaml', skill)
        self.assertEqual({'default_environment', 'environments'},
                         set(registry))
        self.assertEqual('prod', registry['default_environment'])
        self.assertEqual({'prod', 'staging'}, set(registry['environments']))

        required_fields = {
            'scheduler': {'project', 'location'},
            'workflow': {'project', 'location', 'import_workflow'},
            'batch': {'project', 'location'},
            'gcs': {'client_project', 'output_bucket'},
            'spanner': {'project', 'instance', 'database'},
        }
        for environment_name, environment in registry['environments'].items():
            with self.subTest(environment=environment_name):
                self.assertEqual(set(required_fields), set(environment))
                for section, fields in required_fields.items():
                    self.assertEqual(fields, set(environment[section]))
                    for field in fields:
                        self.assertIsInstance(environment[section][field], str)
                        self.assertTrue(environment[section][field])

        self.assertIn('explicit prompt override', resolution)
        self.assertIn('environment_config', resolution)

    def test_architecture_explains_et_lifecycle_and_partial_evidence(self):
        architecture = self._read(
            'agents/common/references/import-automation/architecture.md')
        normalized = re.sub(r'\s+', ' ', architecture)

        for required in (
                'extraction and transformation (ET)',
                '<directory-from-repository-root>:<import_name>',
                'scripts/census_county_business_patterns:CensusCountyBusinessPatterns',
                'there is not one Workflow definition per import',
                'STAGING -> eligible for acceptance',
                'VALIDATION -> validation failed',
                'SKIP -> no meaningful change',
                'eligible for downstream loading',
                'It does not mean the loader ran or serving data changed',
                'one GCS version directory and import_summary.json',
                '`ImportStatus` is a mutable current snapshot',
                'a Batch failure before `import_summary.json` is written has no GCS history entry',
                'Do not interpret a missing summary as proof that no attempt occurred',
                '[run and status model](run-and-status-model.md)',
                'supplied sibling `import` checkout'):
            with self.subTest(required=required):
                self.assertIn(required, normalized)

        for forbidden in ('IngestionHistory', 'Dataflow', '## Contents',
                          '`dc-import-info`'):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, architecture)

    def test_status_model_separates_current_state_and_finalized_versions(self):
        model = self._read(
            'agents/common/references/import-automation/run-and-status-model.md'
        )
        normalized = re.sub(r'\s+', ' ', model)

        for required in (
                'current mutable snapshot and bounded finalized-version evidence',
                'Return its `State` without reinterpretation as `current_status`',
                'Its `JobId` is the ET Batch identifier',
                'never select, return, or follow it in this skill',
                'A technical failure can stop before a version or summary is complete',
                'Older pre-summary failures are unsupported',
                'reverse lexicographic timestamp-folder order',
                'repeated hour at DST fall-back',
                'scans no more than 100 summary names',
                'returns at most five versions', 'If the scan exceeds 100',
                'returns no history', 'Do not create an overall status',
                'STAGING', 'VALIDATION', 'SKIP',
                'It does not mean every failure event that occurred during that week',
                'previous seven days', 'at most 100 returned current rows'):
            with self.subTest(required=required):
                self.assertIn(required, normalized)

    def test_skill_routes_only_supported_runtime_evidence(self):
        skill = self._skill_path.read_text(encoding='utf-8')
        normalized = re.sub(r'\s+', ' ', skill)

        for required in (
                'Use Scheduler only for a deployed schedule or target question',
                '`ImportStatus` only as a mutable current snapshot',
                'previous seven days', 'at most 100 returned rows',
                'GCS summary-list helper', 'scans at most 100 summary names',
                'up to five recent finalized versions',
                'A Batch failure before `import_summary.json` exists is absent',
                'Describe Batch, tasks, or logs only from an exact',
                'List recent import summaries', 'Query current import status'):
            with self.subTest(required=required):
                self.assertIn(required, normalized)

        for forbidden_route in ('correlate-import-runs.md',
                                'query-import-version-history.md',
                                'describe-execution.md',
                                'list-import-executions.md',
                                'find-historical-summary.md',
                                'read-import-records.md',
                                'describe-ingestion-helper.md',
                                'resolve-runtime-image.md'):
            with self.subTest(forbidden_route=forbidden_route):
                self.assertNotIn(forbidden_route, skill)

    def test_current_status_recipe_excludes_loader_workflow_id(self):
        recipe = self._read(
            'agents/common/recipes/gcp/imports/query-import-status.md')
        normalized = re.sub(r'\s+', ' ', recipe)

        for required in (
                'current mutable snapshot', 'StatusUpdateTimestamp',
                '`current_status`', 'previous seven days',
                'at most 100 returned rows',
                'current rows, not historical events',
                'Never select, return, or follow `ImportStatus.WorkflowId`',
                'Use `JobId` only as the exact ET Batch identifier',
                'LIMIT <LIMIT_PLUS_ONE>'):
            with self.subTest(required=required):
                self.assertIn(required, normalized)

        sql_lines = [line for line in recipe.splitlines() if '--sql=' in line]
        self.assertEqual(2, len(sql_lines))
        self.assertTrue(all('WorkflowId' not in line for line in sql_lines))

    def test_summary_helper_recipe_is_bounded_and_explicitly_partial(self):
        recipe = self._read(
            'agents/common/recipes/gcp/gcs/list-import-summaries.md')
        normalized_recipe = re.sub(r'\s+', ' ', recipe)
        helper = self._read(
            'agents/common/import_support/list_import_summaries.py')

        for required in (
                'list_import_summaries.py', '--absolute_import_name',
                '--gcs_project', '--gcs_bucket', '--gcs_output_prefix',
                '--limit', 'at most 100', 'at most five',
                'scan_truncated=true',
                'finalized-version history, not complete attempt history',
                'Batch failure before summary creation is intentionally absent'
        ):
            with self.subTest(required=required):
                self.assertIn(required, normalized_recipe)

        for required in ('_MAX_RESULT_LIMIT = 5', '_SCAN_LIMIT = 100',
                         'max_results=_SCAN_LIMIT + 1',
                         "fields='items(name),nextPageToken'",
                         "'version': version", "'date': version_date",
                         "'batch_job_id': batch_job_id"):
            with self.subTest(required=required):
                self.assertIn(required, helper)

    def test_removed_history_and_workflow_lookup_paths_are_absent(self):
        deleted_paths = (
            'agents/common/import_support/read_import_records.py',
            'agents/common/import_support/read_import_records_test.py',
            'agents/common/import_support/list_import_runs.py',
            'agents/common/import_support/list_import_runs_test.py',
            'agents/common/import_support/correlate_import_runs.py',
            'agents/common/import_support/correlate_import_runs_test.py',
            'agents/common/recipes/gcp/spanner/read-import-records.md',
            'agents/common/recipes/gcp/imports/correlate-import-runs.md',
            'agents/common/recipes/gcp/imports/query-import-version-history.md',
            'agents/common/recipes/gcp/workflows/list-import-executions.md',
            'agents/common/recipes/gcp/workflows/describe-execution.md',
            'agents/common/recipes/gcp/gcs/find-historical-summary.md',
            'agents/common/recipes/gcp/cloud-run/describe-ingestion-helper.md',
        )
        for relative_path in deleted_paths:
            with self.subTest(path=relative_path):
                self.assertFalse((self._repo_root / relative_path).exists())

        runtime_paths = [
            self._skill_path,
            *self._reference_root.glob('*.md'),
            *self._recipe_root.glob('**/*.md'),
        ]
        runtime_guidance = '\n'.join(
            path.read_text(encoding='utf-8') for path in runtime_paths)
        for forbidden in ('ImportVersionHistory',
                          'gcloud workflows executions list',
                          'gcloud workflows executions describe',
                          'correlate_import_runs.py', 'list_import_runs.py'):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, runtime_guidance)

        requirements = self._read('agents/requirements.txt')
        self.assertNotIn('google-cloud-spanner', requirements)
        self.assertNotIn('google-cloud-workflows', requirements)
        self.assertIn('google-cloud-storage', requirements)

    def test_recipes_do_not_document_mutating_gcloud_commands(self):
        recipes = '\n'.join(
            path.read_text(encoding='utf-8')
            for path in self._recipe_root.glob('**/*.md'))
        forbidden = (
            'gcloud scheduler jobs run',
            'gcloud workflows execute',
            'gcloud batch jobs delete',
            'gcloud run services update',
            'gcloud builds submit',
            'gcloud storage rm',
        )

        for command in forbidden:
            with self.subTest(command=command):
                self.assertNotIn(command, recipes)

    def test_exact_artifact_batch_and_log_recipes_remain_bounded(self):
        artifacts = self._read(
            'agents/common/recipes/gcp/gcs/list-version-artifacts.md')
        batch = self._read('agents/common/recipes/gcp/batch/describe-job.md')
        logs = self._read(
            'agents/common/recipes/gcp/logging/fetch-batch-logs.md')

        self.assertIn('<IMPORT_PREFIX>/<VERSION>/**', artifacts)
        self.assertIn('--limit=<LIMIT_PLUS_ONE>', artifacts)
        self.assertIn('ImportStatus.JobId', batch)
        self.assertIn('summary `job_id`', batch)
        self.assertIn('Do not list candidate jobs', batch)
        for required in ('labels.job_uid', 'timestamp>=', 'timestamp<=',
                         '--limit=<LIMIT_PLUS_ONE>', 'jsonPayload.log_type'):
            with self.subTest(required=required):
                self.assertIn(required, logs)

    def test_python_wrapper_uses_repository_environment_without_minor_pin(
            self):
        wrapper = self._read('agents/common/run_python.sh')

        self.assertIn('.env/bin/python', wrapper)
        self.assertNotIn('Expected Python 3.12', wrapper)


if __name__ == '__main__':
    unittest.main()

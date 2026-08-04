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
"""Tests the repository-local contract presented to import-support agents.

These tests catch drift in local links, routing rules, safety guardrails,
recipe structure, and helper/documentation agreements. They do not exercise
live GCP resources or verify production import behavior.
"""

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
        self._prompt_path = (self._repo_root /
                             'agents/prompts/dc-import-info.md')
        self._common_reference_root = (self._repo_root /
                                       'agents/common/references')
        self._reference_root = (self._common_reference_root /
                                'import-automation')
        self._recipe_root = self._repo_root / 'agents/common/recipes'

    def _read(self, relative_path: str) -> str:
        return (self._repo_root / relative_path).read_text(encoding='utf-8')

    def test_registry_points_to_versioned_skill(self):
        registry = json.loads(self._read('.agents/skills.json'))
        paths = [entry['path'] for entry in registry['entries']]

        self.assertEqual(['agents/skills/dc-import-info'], paths)
        self.assertTrue((self._repo_root / paths[0] / 'SKILL.md').is_file())

    def test_common_helpers_live_under_scripts(self):
        scripts_root = self._repo_root / 'agents/common/scripts'
        for filename in ('__init__.py', 'check_dependencies_test.py',
                         'check_python_dependencies.py',
                         'check_python_dependencies_test.py',
                         'cli_flags_test.py', 'list_imports.py',
                         'list_imports_test.py', 'list_import_summaries.py',
                         'list_import_summaries_test.py',
                         'skill_contract_test.py'):
            with self.subTest(filename=filename):
                self.assertTrue((scripts_root / filename).is_file())

        old_name = 'import_' + 'support'
        self.assertFalse(
            (self._repo_root / 'agents/common' / old_name).exists())

        agent_text = '\n'.join(
            path.read_text(encoding='utf-8')
            for path in (self._repo_root / 'agents').rglob('*')
            if path.is_file() and path.suffix in _TEXT_SUFFIXES)
        self.assertNotIn(f'agents/common/{old_name}', agent_text)
        self.assertNotIn(f'agents.common.{old_name}', agent_text)

        self.assertIn('agents/common/scripts/list_imports.py',
                      self._read('agents/common/recipes/local/list-imports.md'))
        self.assertIn(
            'agents/common/scripts/list_import_summaries.py',
            self._read(
                'agents/common/recipes/gcp/gcs/list-import-summaries.md'))

    def test_dependency_readiness_is_shared_and_failure_routed(self):
        checker = self._read('agents/check_dependencies.sh')
        python_checker = self._read(
            'agents/common/scripts/check_python_dependencies.py')
        readme = self._read('agents/README.md')
        setup = self._read('agents/dependency-setup.md')
        normalized_setup = re.sub(r'\s+', ' ', setup)
        requirements = self._read('agents/requirements.txt')
        skill = self._skill_path.read_text(encoding='utf-8')
        normalized_skill = re.sub(r'\s+', ' ', skill)

        for relative_path in (
                'agents/check_dependencies.sh',
                'agents/common/scripts/check_python_dependencies.py',
                'agents/README.md', 'agents/dependency-setup.md'):
            with self.subTest(relative_path=relative_path):
                self.assertTrue((self._repo_root / relative_path).is_file())

        for required in ('REQUIRED_COMMANDS=(', 'GCLOUD_COMMANDS=(',
                         "'auth print-access-token'",
                         "'auth application-default print-access-token'",
                         '"$1" == \'--local\'', 'set -uo pipefail',
                         'generic loop checks each with command -v',
                         'generic loop appends --help'):
            with self.subTest(checker_requirement=required):
                self.assertIn(required, checker)

        for required in ("('absl-py', 'absl')",
                         "('google-api-core', 'google.api_core')",
                         "('google-auth', 'google.auth')",
                         "('google-cloud-storage', 'google.cloud.storage')",
                         "('pyopenssl', 'OpenSSL')", "('pyyaml', 'yaml')",
                         'synchronized with agents/requirements.txt'):
            with self.subTest(python_requirement=required):
                self.assertIn(required, python_checker)

        for required in ('./agents/check_dependencies.sh --local',
                         './run_tests.sh -r', 'gcloud auth login',
                         'gcloud auth application-default login',
                         'IAM permissions', 'non-interactive Bash process',
                         'might not be loaded',
                         'do not rely solely on personal aliases'):
            with self.subTest(setup_requirement=required):
                self.assertIn(required, normalized_setup)

        self.assertIn('[dependency setup](dependency-setup.md)', readme)
        self.assertNotIn('./agents/check_dependencies.sh', readme)
        self.assertNotIn('## Maintaining dependency lists', setup)
        self.assertIn('synchronized with REQUIRED_MODULES', requirements)
        self.assertIn('command -v "$command_name"', checker)
        self.assertNotIn('type -P', checker)
        self.assertIn('[agent dependency setup](../../dependency-setup.md)',
                      skill)
        self.assertIn('Do not run the readiness checker on every request',
                      normalized_skill)
        self.assertNotIn('gcloud auth login', skill)
        self.assertNotIn('gcloud auth application-default login', skill)

    def test_recipes_have_invocation_contract(self):
        recipe_paths = [
            path for path in self._recipe_root.glob('**/*.md')
            if path.name != 'README.md'
        ]

        self.assertGreater(len(recipe_paths), 1)
        self.assertTrue((self._recipe_root / 'README.md').is_file())
        for path in recipe_paths:
            text = path.read_text(encoding='utf-8')
            with self.subTest(path=path):
                for heading in _RECIPE_HEADINGS:
                    self.assertIn(heading, text)

    def test_recipe_taxonomy_separates_local_and_gcp_services(self):
        readme = self._read('agents/common/recipes/README.md')
        normalized_readme = re.sub(r'\s+', ' ', readme)
        skill = self._skill_path.read_text(encoding='utf-8')
        local_recipe = self._read('agents/common/recipes/local/list-imports.md')
        spanner_recipe = self._read(
            'agents/common/recipes/gcp/spanner/query-import-status.md')

        for required in (
                '`local/`', '`gcp/<service>/`', 'primary GCP service',
                'Python helper implementations in `agents/common/scripts/`',
                'recipe that invokes a helper',
                'cross-service evidence path from atomic recipes',
                'must not copy the other service\'s commands',
                'product recipe may apply a shared service reference',
                'complete product-specific parameters',
                'Upstream skills and playbooks link directly',
                'do not load this README during normal execution'):
            with self.subTest(required=required):
                self.assertIn(required, normalized_readme)

        expected_paths = (
            'agents/common/recipes/local/list-imports.md',
            'agents/common/recipes/gcp/spanner/query-import-status.md',
        )
        for relative_path in expected_paths:
            with self.subTest(path=relative_path):
                self.assertTrue((self._repo_root / relative_path).is_file())

        removed_paths = (
            'agents/common/recipes/repository/list-imports.md',
            'agents/common/recipes/gcp/imports/query-import-status.md',
        )
        for relative_path in removed_paths:
            with self.subTest(path=relative_path):
                self.assertFalse((self._repo_root / relative_path).exists())

        self.assertIn('Recipe ID: `local.list-imports`', local_recipe)
        self.assertIn("--query='<IMPORT_NAME_QUERY>'", local_recipe)
        self.assertIn('Recipe ID: `gcp.spanner.query-import-status`',
                      spanner_recipe)
        self.assertIn('bucket-relative GCS object prefixes', local_recipe)
        self.assertNotIn('../../common/recipes/README.md', skill)
        self.assertNotIn('dc-import-info', readme)
        self.assertNotIn('repository.list-imports', local_recipe + skill)
        self.assertNotIn('gcp.imports.query-import-status',
                         spanner_recipe + skill)

    def test_agent_documentation_links_exist(self):
        paths = [
            self._repo_root / 'agents/README.md',
            self._repo_root / 'agents/dependency-setup.md',
            self._skill_path,
            self._prompt_path,
            *self._common_reference_root.glob('**/*.md'),
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
                '../../common/recipes/local/list-imports.md',
                'read only the selected manifest or requested code'):
            with self.subTest(required=required):
                self.assertIn(required, normalized)

        self.assertNotIn('architecture.md). 3.', normalized)
        self.assertNotIn('## Contents', skill)

    def test_manual_prompt_and_command_grounding_contract(self):
        prompt = self._prompt_path.read_text(encoding='utf-8')
        skill = self._skill_path.read_text(encoding='utf-8')
        normalized_skill = re.sub(r'\s+', ' ', skill)
        pointer_recipe = self._read(
            'agents/common/recipes/gcp/gcs/read-version-pointer.md')

        self.assertLessEqual(len(prompt.split()), 130)
        for required in (
                '`dc-import-info`',
                'Read the exact linked recipe during this turn',
                'Never invent a resource, filename, field, or meaning',
                'loader and serving status',
                'recipe ID or repository path',
        ):
            with self.subTest(prompt_requirement=required):
                self.assertIn(required, prompt)

        for required in (
                '## Ground commands in recipes',
                'Open and read its linked recipe during the current turn',
                'Never reconstruct a command from memory',
                '`is_current`',
                'serving availability',
        ):
            with self.subTest(skill_requirement=required):
                self.assertIn(required, normalized_skill)

        self.assertNotIn('.agents/rules', prompt + skill)
        self.assertIn("/<IMPORT_PREFIX>/staging_version.txt'", pointer_recipe)
        self.assertIn("/<IMPORT_PREFIX>/latest_version.txt'", pointer_recipe)
        self.assertIn('`is_current`', pointer_recipe)
        self.assertIn(
            'This does not prove loader completion or serving availability.',
            re.sub(r'\s+', ' ', pointer_recipe),
        )
        self.assertNotIn('<POINTER_FILENAME>', pointer_recipe)
        self.assertIsNone(
            re.search(r'(?<![_A-Za-z0-9])version\.txt(?![_A-Za-z0-9])',
                      pointer_recipe))

    def test_runtime_environment_registry_remains_minimal_and_complete(self):
        registry = yaml.safe_load(
            self._read('agents/common/config/import-environments.yaml'))
        skill = self._skill_path.read_text(encoding='utf-8')
        resolution = self._read(
            'agents/common/references/import-automation/environment-resolution.md'
        )

        self.assertIn('../../common/config/import-environments.yaml', skill)
        self.assertEqual({'default_environment', 'environments'}, set(registry))
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
                'Cloud Spanner `ImportStatus` is a mutable current snapshot',
                'a Batch failure before `import_summary.json` is written has no GCS history entry',
                'Do not interpret a missing summary as proof that no attempt occurred',
                '[import evidence flow](import-evidence-flow.md)',
                'supplied sibling `import` checkout'):
            with self.subTest(required=required):
                self.assertIn(required, normalized)

        for forbidden in ('IngestionHistory', 'Dataflow', '## Contents',
                          '`dc-import-info`'):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, architecture)

    def test_evidence_flow_composes_identity_and_runtime_evidence(self):
        flow = self._read(
            'agents/common/references/import-automation/import-evidence-flow.md'
        )
        normalized = re.sub(r'\s+', ' ', flow)

        for required in (
                'gcs_object_prefix',
                'scripts/census_county_business_patterns/CensusCountyBusinessPatterns',
                'gs://<output_bucket>/<gcs_object_prefix>',
                'bucket-relative and is not a complete GCS URI',
                'Do not interpret `scripts` or `statvar_imports` as a bucket name',
                'Cloud Spanner table containing one mutable current row',
                'best starting point for current status',
                'it is not complete attempt history',
                'Its `JobId` is the ET Batch identifier',
                'never select or follow it',
                'pre-summary Batch failure is absent',
                '`current_status`, `summary_status`, `is_current`, and `batch_state`',
                'acceptance, and eligibility for downstream loading'):
            with self.subTest(required=required):
                self.assertIn(required, normalized)

        self.assertLess(len(flow.splitlines()), 100)
        self.assertNotIn('## Contents', flow)
        self.assertNotIn('reverse lexicographic', flow)
        self.assertFalse(
            (self._reference_root / 'run-and-status-model.md').exists())

    def test_skill_routes_only_supported_runtime_evidence(self):
        skill = self._skill_path.read_text(encoding='utf-8')
        normalized = re.sub(r'\s+', ' ', skill)

        for required in (
                'Use Scheduler only for a deployed schedule or target question',
                'Cloud Spanner `ImportStatus` table only as a mutable current snapshot',
                'previous seven days', 'at most 100 returned rows',
                'GCS summary-list helper',
                '100 matching summary object names plus one overflow sentinel',
                'up to five recent finalized versions', 'exact GCS version URI',
                'A Batch failure before `import_summary.json` exists is absent',
                'Describe Batch, tasks, or logs only from an exact',
                'only when explicitly requested',
                'trace-batch-job-source-commit.md',
                'List recent import summaries', 'Query current import status'):
            with self.subTest(required=required):
                self.assertIn(required, normalized)

        for forbidden_route in ('correlate-import-runs.md',
                                'query-import-version-history.md',
                                'describe-execution.md',
                                'list-import-executions.md',
                                'find-historical-summary.md',
                                'read-import-records.md',
                                'describe-ingestion-helper.md'):
            with self.subTest(forbidden_route=forbidden_route):
                self.assertNotIn(forbidden_route, skill)

    def test_current_status_recipe_excludes_loader_workflow_id(self):
        recipe = self._read(
            'agents/common/recipes/gcp/spanner/query-import-status.md')
        normalized = re.sub(r'\s+', ' ', recipe)

        for required in (
                'Cloud Spanner table keyed by `ImportName`',
                'current mutable snapshot', 'StatusUpdateTimestamp',
                'DataImportTimestamp', '`current_status`',
                'full exact `gcs_version_uri`',
                "LatestVersion = '<GCS_VERSION_URI>'",
                'reverse-lookup only current snapshots', 'not version history',
                'must not use a bare version',
                'Do not run a state-only query without the UTC window',
                'previous seven days', 'at most 100 returned rows',
                'current rows, not historical events',
                'Never select, return, or follow `ImportStatus.WorkflowId`',
                'Use `JobId` only as the exact ET Batch identifier',
                'LIMIT <LIMIT_PLUS_ONE>'):
            with self.subTest(required=required):
                self.assertIn(required, normalized)

        sql_lines = [line for line in recipe.splitlines() if '--sql=' in line]
        self.assertEqual(3, len(sql_lines))
        self.assertTrue(all('WorkflowId' not in line for line in sql_lines))

    def test_batch_source_commit_recipe_uses_exact_digest_tags_and_labeled_heuristic(
            self):
        recipe = self._read(
            'agents/common/recipes/gcp/batch/trace-batch-job-source-commit.md')
        normalized = re.sub(r'\s+', ' ', recipe)

        for required in (
                'Artifact Registry `DockerImage` resource',
                'Inspect only that resource\'s `tags[]`',
                '<RESOLVED_IMAGE_AT_DIGEST>', '<IMAGE>@<DIGEST>',
                '<URL_ENCODED_IMAGE_AT_DIGEST>',
                'one Artifact Registry request',
                'Another exact tag requires at most two',
                'artifact_registry_lookups: 0',
                'nearest_local_commit_before_launch',
                'correlation_method: heuristic_by_time',
                'Never call it the commit that ran',
                'When exact provenance is not required',
                'do not substitute this time candidate for missing digest evidence',
                'Do not resolve `stable` or `latest`',
                'Never query Cloud Build'):
            with self.subTest(required=required):
                self.assertIn(required, normalized)

        for forbidden in ('gcloud artifacts versions describe',
                          'TAG_LIMIT_PLUS_ONE', 'VERSION_RESOURCE',
                          '<IMAGE>@sha256:<DIGEST>', 'gcloud builds list',
                          'gcloud builds describe'):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, recipe)

    def test_summary_helper_recipe_is_bounded_and_explicitly_partial(self):
        recipe = self._read(
            'agents/common/recipes/gcp/gcs/list-import-summaries.md')
        normalized_recipe = re.sub(r'\s+', ' ', recipe)
        helper = self._read('agents/common/scripts/list_import_summaries.py')
        artifact_layout = re.sub(
            r'\s+', ' ',
            self._read(
                'agents/common/references/import-automation/artifact-layout.md')
        )

        for required in (
                'list_import_summaries.py', '--absolute_import_name',
                '--gcs_project', '--gcs_bucket', '--limit',
                '100 matching summary object names plus one overflow sentinel',
                '101 names maximum', 'at most five', 'scan_truncated=true',
                'finalized-version history, not complete attempt history',
                'gcs_version_uri',
                'Batch failure before summary creation is intentionally absent'
        ):
            with self.subTest(required=required):
                self.assertIn(required, normalized_recipe)

        self.assertIn(
            '100 matching summary object names plus one overflow sentinel',
            artifact_layout)

        self.assertNotIn('gcs_output_prefix', recipe + helper)

        for required in ('_MAX_RESULT_LIMIT = 5', '_SCAN_LIMIT = 100',
                         'max_results=_SCAN_LIMIT + 1',
                         "fields='items(name),nextPageToken'",
                         "'version': version", "'date': version_date",
                         "'gcs_version_uri':", "'batch_job_id': batch_job_id"):
            with self.subTest(required=required):
                self.assertIn(required, helper)

    def test_removed_history_and_workflow_lookup_paths_are_absent(self):
        deleted_paths = (
            'agents/common/references/import-automation/run-and-status-model.md',
            'agents/common/scripts/read_import_records.py',
            'agents/common/scripts/read_import_records_test.py',
            'agents/common/scripts/list_import_runs.py',
            'agents/common/scripts/list_import_runs_test.py',
            'agents/common/scripts/correlate_import_runs.py',
            'agents/common/scripts/correlate_import_runs_test.py',
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
        for forbidden in ('ImportVersionHistory', 'IngestionHistory',
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

    def test_gcs_recipes_keep_distinct_version_operations(self):
        summary_list = self._read(
            'agents/common/recipes/gcp/gcs/list-import-summaries.md')
        version_summary = self._read(
            'agents/common/recipes/gcp/gcs/read-version-summary.md')
        pointer = self._read(
            'agents/common/recipes/gcp/gcs/read-version-pointer.md')
        artifacts = self._read(
            'agents/common/recipes/gcp/gcs/list-version-artifacts.md')

        for recipe_id, recipe in (
            ('gcp.gcs.list-import-summaries', summary_list),
            ('gcp.gcs.read-version-summary', version_summary),
            ('gcp.gcs.read-version-pointer', pointer),
            ('gcp.gcs.list-version-artifacts', artifacts),
        ):
            with self.subTest(recipe_id=recipe_id):
                self.assertIn(f'Recipe ID: `{recipe_id}`', recipe)

        self.assertLess(len(summary_list.splitlines()), 75)
        self.assertIn("Read one supplied or selected version's summary",
                      self._skill_path.read_text(encoding='utf-8'))
        self.assertIn('exact version supplied\nby the user', version_summary)
        self.assertIn('do not run the summary-list helper first',
                      version_summary)
        self.assertNotIn('pointer changed after', version_summary)
        self.assertFalse(
            (self._recipe_root / 'gcp/gcs/read-run-summary.md').exists())

    def test_exact_artifact_batch_and_log_recipes_remain_bounded(self):
        artifacts = self._read(
            'agents/common/recipes/gcp/gcs/list-version-artifacts.md')
        batch = self._read('agents/common/recipes/gcp/batch/describe-job.md')
        tasks = self._read('agents/common/recipes/gcp/batch/list-tasks.md')
        logging_reference = self._read(
            'agents/common/references/gcp/logging.md')
        logs = self._read(
            'agents/common/recipes/gcp/logging/fetch-batch-logs.md')
        skill = self._skill_path.read_text(encoding='utf-8')
        normalized_logging_reference = re.sub(r'\s+', ' ', logging_reference)
        normalized_logs = re.sub(r'\s+', ' ', logs)

        self.assertIn('<IMPORT_PREFIX>/<VERSION>/**', artifacts)
        self.assertIn('--limit=<LIMIT_PLUS_ONE>', artifacts)
        self.assertIn('ImportStatus.JobId', batch)
        self.assertIn('summary `job_id`', batch)
        self.assertIn('Do not list candidate jobs', batch)
        for required in ('--limit=<LIMIT_PLUS_ONE>',
                         "--argjson limit '<LIMIT>'",
                         'truncated: (length > $limit)', '.[0:$limit][]',
                         'exitCode: .taskExecution.exitCode'):
            with self.subTest(required=required):
                self.assertIn(required, tasks)
        for required in ("gcloud logging read '<FILTER>'", '<PROJECT>',
                         '<ORDER>', '<LIMIT>', '<FORMAT>',
                         'timestamp >= "<START>" AND timestamp < "<END>"',
                         "--freshness='<FRESHNESS>'", 'default freshness',
                         'works only with descending order', 'logName =',
                         'resource.type =', 'resource.labels.<KEY> =',
                         'labels.<KEY> =', 'severity >=',
                         'jsonPayload.<FIELD> =', 'textPayload :',
                         'uppercase `AND` or `OR`', 'Prefer a finite limit',
                         'known identifier when practical',
                         'only the fields needed',
                         '`DEFAULT`, `DEBUG`, `INFO`, `NOTICE`, `WARNING`, '
                         '`ERROR`, `CRITICAL`, `ALERT`, and `EMERGENCY`',
                         'matches a substring while `=` matches the whole '
                         'field', 'complete filter in single shell quotes',
                         'severity >= "ERROR"',
                         '(textPayload : "<TERM_1>" OR textPayload : '
                         '"<TERM_2>")',
                         "--format='json(timestamp,severity,textPayload)'"):
            with self.subTest(required=required):
                self.assertIn(required, normalized_logging_reference)
        for forbidden in ('batch_task_logs', 'labels.job_uid',
                          'auto-import-job-stage', 'LIMIT_PLUS_ONE'):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, logging_reference)
        self.assertIn('../../../references/gcp/logging.md', logs)
        self.assertNotIn('gcloud logging read', logs)
        self.assertIn('inclusive UTC start timestamp', normalized_logs)
        self.assertIn('exclusive UTC end timestamp', normalized_logs)
        self.assertNotIn('[AND timestamp', logs)
        self.assertEqual(2, logs.count('timestamp >= "<START>"'))
        self.assertEqual(2, logs.count('timestamp < "<END>"'))
        for parameter in ('FILTER', 'PROJECT', 'ORDER', 'LIMIT', 'FORMAT'):
            with self.subTest(parameter=parameter):
                self.assertEqual(
                    2,
                    len(re.findall(rf'^{parameter} =', logs,
                                   flags=re.MULTILINE)))
        for required in ('batch_task_logs', 'labels.job_uid',
                         'timestamp >= "<START>"', 'timestamp < "<END>"',
                         'LIMIT = <LIMIT_PLUS_ONE>', 'jsonPayload.log_type',
                         'FORMAT = json'):
            with self.subTest(required=required):
                self.assertIn(required, logs)
        self.assertIn('../../common/recipes/gcp/logging/fetch-batch-logs.md',
                      skill)
        self.assertNotIn('common/references/gcp/logging.md', skill)

    def test_python_wrapper_uses_repository_environment_without_minor_pin(self):
        wrapper = self._read('agents/common/run_python.sh')

        self.assertIn('.env/bin/python', wrapper)
        self.assertNotIn('Expected Python 3.12', wrapper)


if __name__ == '__main__':
    unittest.main()

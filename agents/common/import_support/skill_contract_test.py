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

    def test_registry_points_to_versioned_skill(self):
        registry = json.loads(
            (self._repo_root /
             '.agents/skills.json').read_text(encoding='utf-8'))
        paths = [entry['path'] for entry in registry['entries']]

        self.assertEqual(['agents/skills/dc-import-info'], paths)
        self.assertTrue((self._repo_root / paths[0] / 'SKILL.md').is_file())

    def test_recipes_have_invocation_contract(self):
        recipes = self._repo_root / 'agents/common/recipes'
        recipe_paths = list(recipes.glob('**/*.md'))

        self.assertGreater(len(recipe_paths), 1)
        for path in recipe_paths:
            text = path.read_text(encoding='utf-8')
            with self.subTest(path=path):
                for heading in _RECIPE_HEADINGS:
                    self.assertIn(heading, text)

    def test_agent_documentation_links_exist(self):
        skill_root = self._repo_root / 'agents/skills/dc-import-info'
        common_root = self._repo_root / 'agents/common'
        paths = [
            skill_root / 'SKILL.md',
            *skill_root.glob('references/*.md'),
            *common_root.glob('references/**/*.md'),
            *common_root.glob('recipes/**/*.md'),
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

    def test_skill_requires_review_and_repository_tools_for_cloud_access(self):
        skill = (self._repo_root /
                 'agents/skills/dc-import-info/SKILL.md').read_text(
                     encoding='utf-8')

        for required in ('review: skipped (headless)',
                         'Infrastructure actually used', 'Never use MCP tools'):
            with self.subTest(required=required):
                self.assertIn(required, skill)

    def test_skill_uses_simple_runtime_environment_registry(self):
        registry_path = (self._repo_root / 'agents/common/config' /
                         'import-environments.yaml')
        registry_text = registry_path.read_text(encoding='utf-8')
        registry = yaml.safe_load(registry_text)
        skill = (self._repo_root /
                 'agents/skills/dc-import-info/SKILL.md').read_text(
                     encoding='utf-8')
        resolution = (self._repo_root / 'agents/common/references' /
                      'import-automation/environment-resolution.md').read_text(
                          encoding='utf-8')
        workflow_list = (self._repo_root / 'agents/common/recipes/gcp' /
                         'workflows/list-import-executions.md').read_text(
                             encoding='utf-8')
        artifact_layout = (self._repo_root / 'agents/common/references' /
                           'import-automation/artifact-layout.md').read_text(
                               encoding='utf-8')
        correlation = (self._repo_root / 'agents/common/import_support' /
                       'correlate_import_runs.py').read_text(encoding='utf-8')

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
                        value = environment[section][field]
                        self.assertIsInstance(value, str)
                        self.assertTrue(value)

        self.assertIn('explicit prompt override', resolution)
        self.assertIn('environment_config', resolution)
        self.assertIn('effective environment and prompt overrides',
                      workflow_list)
        self.assertNotIn('Scheduler target cannot identify', workflow_list)
        for artifact_name in ('staging_version.txt', 'latest_version.txt',
                              'import_summary.json'):
            with self.subTest(artifact_name=artifact_name):
                self.assertIn(artifact_name, artifact_layout)
        self.assertIn("_SUMMARY_FILENAME = 'import_summary.json'", correlation)

        runtime_docs = '\n'.join(
            (skill, resolution, workflow_list, artifact_layout))
        self.assertNotIn('import-environment-sync-selectors.yaml',
                         runtime_docs)

    def test_architecture_and_shared_policy_are_et_only(self):
        skill = (self._repo_root /
                 'agents/skills/dc-import-info/SKILL.md').read_text(
                     encoding='utf-8')
        architecture = (self._repo_root / 'agents/common/references' /
                        'import-automation/architecture.md').read_text(
                            encoding='utf-8')
        status_model = (self._repo_root / 'agents/common/references' /
                        'import-automation/run-and-status-model.md').read_text(
                            encoding='utf-8')
        normalized_architecture = re.sub(r'\s+', ' ', architecture)
        normalized_status_model = re.sub(r'\s+', ' ', status_model)
        pointer_recipe = (self._repo_root / 'agents/common/recipes/gcp/gcs' /
                          'read-version-pointer.md').read_text(
                              encoding='utf-8')
        deleted_paths = (
            self._repo_root / 'agents/common/recipes/repository' /
            'preview-infrastructure.md',
            self._repo_root / 'agents/common/references/import-automation' /
            'identity-and-access.md',
            self._repo_root / 'agents/common/references/import-automation' /
            'runtime-provenance.md',
        )

        for path in deleted_paths:
            with self.subTest(path=path):
                self.assertFalse(path.exists())
                self.assertNotIn(path.name, skill)

        for required in (
                'operation | resource type | effective value | source',
                'Ask once for approval',
                "caller's existing GCP authentication"):
            with self.subTest(skill_required=required):
                self.assertIn(required, skill)
        for required in (
                'Define the import in Git',
                '<directory-from-repository-root>:<import_name>',
            ('scripts/census_county_business_patterns:'
             'CensusCountyBusinessPatterns'),
                'creates or updates one Cloud Scheduler job',
                'one Workflow execution represents one logical ET attempt',
                '## ET lifecycle concepts',
                'Candidate means generated, not yet selected',
                'Acceptance** is the ET-only transition',
                'does not mean the loader ran or serving',
                'executor reads the selected definition and source data',
                'Finalize and classify a candidate ET version',
                'Apply ET acceptance',
                'only STAGING is eligible for acceptance',
                'records a corresponding ET version checkpoint',
                'VALIDATION or SKIP leaves the previous current ET output',
                'provides queryable version checkpoints',
                'records are created separately',
                '[run and status model](run-and-status-model.md)',
                'loader pipeline (out of scope)',
                'live read-only Scheduler, Workflow, Batch, GCS, and database metadata',
                'supplied sibling `import` checkout'):
            with self.subTest(architecture_required=required):
                self.assertIn(required, normalized_architecture)
        for forbidden in ('spanner-ingestion-workflow', 'Dataflow',
                          'IngestionHistory', 'ImportStatus',
                          'Downstream ingestion', '| Publication |',
                          '`dc-import-info`', 'Load this reference',
                          '## ImportVersionHistory stages',
                          'loader can later add a `SUCCESS` event'):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, architecture + '\n' + status_model)
        for required in (
                'checkpointed ET run is a version recorded',
                'not an exhaustive attempt ledger',
                'A `STAGING` summary proves eligibility, not acceptance',
                'queryable version-event checkpoint history',
                'does not justify listing Workflow executions',
                'describe that exact execution instead of listing',
                'No checkpointed ET run found',
                'request still requires an attempt-level answer',
                'Do not translate that result into `No ET attempt occurred`'):
            with self.subTest(status_model_required=required):
                self.assertIn(required, normalized_status_model)
        self.assertIn('current accepted ET-output question', pointer_recipe)
        self.assertNotIn('publication question', pointer_recipe)

    def test_skill_routes_local_requests_without_architecture_or_cloud(self):
        skill_path = (self._repo_root /
                      'agents/skills/dc-import-info/SKILL.md')
        skill = skill_path.read_text(encoding='utf-8')
        normalized_skill = re.sub(r'\s+', ' ', skill)
        status_model = (self._repo_root / 'agents/common/references' /
                        'import-automation/run-and-status-model.md').read_text(
                            encoding='utf-8')
        workflow_list = (self._repo_root / 'agents/common/recipes/gcp' /
                         'workflows/list-import-executions.md').read_text(
                             encoding='utf-8')
        historical_summary = (self._repo_root / 'agents/common/recipes/gcp' /
                              'gcs/find-historical-summary.md').read_text(
                                  encoding='utf-8')
        deleted_paths = (
            self._repo_root / 'agents/skills/dc-import-info/references' /
            'single-import.md',
            self._repo_root / 'agents/skills/dc-import-info/references' /
            'fleet-search.md',
            self._repo_root / 'agents/skills/dc-import-info/references' /
            'repository-catalog.md',
            self._repo_root / 'agents/common/recipes/catalog.md',
        )

        for path in deleted_paths:
            with self.subTest(path=path):
                self.assertFalse(path.exists())
                self.assertNotIn(path.name, skill)

        self.assertIn('Classify the request before loading references', skill)
        self.assertIn(
            'Do not load architecture, environment configuration, or cloud recipes',
            skill)
        self.assertNotIn('## Repository-only path', skill)
        self.assertNotIn('2. Read [Import automation architecture]', skill)
        self.assertIn('../../common/recipes/repository/list-imports.md', skill)
        self.assertIn('follow its manifest handoff', skill)
        list_imports = (self._repo_root / 'agents/common/recipes/repository' /
                        'list-imports.md').read_text(encoding='utf-8')
        self.assertIn('read its exact manifest specification', list_imports)
        self.assertIn('../../references/import-automation/manifest.md',
                      list_imports)
        self.assertIn('Read manifest-referenced code only when', list_imports)
        self.assertIn('Scheduler evidence is not a prerequisite',
                      normalized_skill)
        for required in (
                'routine single-import run history or latest checkpointed-run status',
                'Do not list Workflow executions merely because checkpoint',
                'failures before checkpointing',
                'describe that exact execution instead of listing',
                'fall back to bounded Workflow history only',
            ('Read routine bounded run history or latest checkpointed-run '
             'status for one import'),
                'Label correlation-only results as checkpointed ET runs'):
            with self.subTest(skill_routing_required=required):
                self.assertIn(required, normalized_skill)
        for forbidden_route in ('describe-ingestion-helper.md',
                                'read-import-records.md',
                                'resolve-runtime-provenance.md'):
            with self.subTest(forbidden_route=forbidden_route):
                self.assertNotIn(forbidden_route, skill)

        self.assertIn('previous 90 days', workflow_list)
        combined = re.sub(r'\s+', ' ', skill + '\n' + status_model)
        for required in ('previous 24 hours',
                         'at most 100 returned Workflow executions',
                         'compact table',
                         'not an exhaustive attempt ledger',
                         '`unknown`'):
            with self.subTest(required=required):
                self.assertIn(required, combined)

        self.assertNotIn('## Collect incrementally', skill)
        collect_section = skill.split(
            '## Collect only required runtime evidence', maxsplit=1)[1]
        collect_section = collect_section.split(
            '## Load detailed knowledge only when needed', maxsplit=1)[0]
        collect_section = re.sub(r'\s+', ' ', collect_section)
        for required in ('recipe that directly answers the request',
                         'deployed schedule or configured Workflow target',
                         'Workflow `result.jobId` → Batch',
                         'import name + Batch job ID → GCS summary',
                         'run and status model'):
            with self.subTest(collect_required=required):
                self.assertIn(required, collect_section)
        self.assertIn('terminal runs newest to oldest', status_model)
        self.assertIn('requested minimum', status_model)
        self.assertNotIn('Spanner row', historical_summary)

        runtime_text = '\n'.join(
            path.read_text(encoding='utf-8')
            for path in self._repo_root.glob('agents/**/*.md'))
        self.assertNotRegex(runtime_text, r'\bfleet\b')
        self.assertNotRegex(runtime_text, r'\bcomposite\b')
        for unclear_term in ('resource coordinate',
                             'infrastructure coordinates',
                             'missing coordinates', 'headless run'):
            with self.subTest(unclear_term=unclear_term):
                self.assertNotIn(unclear_term, runtime_text)
        self.assertNotIn('the runtime-provenance reference', runtime_text)

    def test_skill_and_recipes_do_not_reference_removed_helpers(self):
        paths = [
            self._repo_root / 'agents/skills/dc-import-info/SKILL.md',
            *self._repo_root.glob(
                'agents/skills/dc-import-info/references/*.md'),
            *self._repo_root.glob('agents/common/recipes/**/*.md'),
        ]

        for path in paths:
            text = path.read_text(encoding='utf-8')
            with self.subTest(path=path):
                self.assertNotIn('collect_import_snapshot.py', text)
                self.assertNotIn('collect_provenance.py', text)
                self.assertNotIn('snapshot collector', text.lower())
                self.assertNotIn('resolve_import', text)
                self.assertNotIn('repository.resolve-import', text)
                self.assertNotIn('name_contains', text)

    def test_recipes_do_not_document_mutating_gcloud_commands(self):
        recipes = '\n'.join(
            path.read_text(encoding='utf-8')
            for path in self._repo_root.glob('agents/common/recipes/**/*.md'))
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

    def test_expensive_recipes_are_targeted_and_bounded(self):
        recipe_root = self._repo_root / 'agents/common/recipes/gcp'
        historical = (recipe_root /
                      'gcs/find-historical-summary.md').read_text(
                          encoding='utf-8')
        artifacts = (recipe_root / 'gcs/list-version-artifacts.md').read_text(
            encoding='utf-8')
        logs = (recipe_root /
                'logging/fetch-batch-logs.md').read_text(encoding='utf-8')
        runtime_image = (recipe_root / 'artifact-registry' /
                         'resolve-runtime-image.md').read_text(
                             encoding='utf-8')

        self.assertIn('<YYYY_MM_DD>*/import_summary.json', historical)
        self.assertNotIn('<IMPORT_PREFIX>/**/', historical)
        self.assertIn('<IMPORT_PREFIX>/<VERSION>/**', artifacts)
        self.assertIn('--limit=<LIMIT_PLUS_ONE>', artifacts)
        for required in ('labels.job_uid', 'timestamp>=', 'timestamp<=',
                         '--limit=<LIMIT_PLUS_ONE>', 'jsonPayload.log_type'):
            with self.subTest(log_required=required):
                self.assertIn(required, logs)
        for required in ('gcloud artifacts docker images describe',
                         'gcloud artifacts versions describe',
                         'gcloud auth print-access-token', 'curl --config -',
                         'filter=version="<VERSION_RESOURCE>"',
                         'pageSize=<TAG_LIMIT_PLUS_ONE>', 'nextPageToken',
                         '^[0-9a-f]{40}$',
                         "cat-file -e '<GIT_SHA>^{commit}'",
                         'Do not resolve the current value',
                         'Never query Cloud Build', 'strongly_correlated'):
            with self.subTest(image_required=required):
                self.assertIn(required, runtime_image)
        for forbidden in ('gcloud builds list', 'gcloud builds describe'):
            with self.subTest(image_forbidden=forbidden):
                self.assertNotIn(forbidden, runtime_image)
        docker_describe = runtime_image.split(
            "gcloud artifacts docker images describe", maxsplit=1)[1]
        docker_describe = docker_describe.split('```', maxsplit=1)[0]
        self.assertNotIn('--location=', docker_describe)
        self.assertNotIn('metadata.name', runtime_image)
        self.assertNotIn('gcloud artifacts tags list', runtime_image)

    def test_duplicate_helpers_and_recipes_are_removed(self):
        deleted_paths = (
            self._repo_root / 'agents/common/import_support' /
            'read_import_records.py',
            self._repo_root / 'agents/common/import_support' /
            'read_import_records_test.py',
            self._repo_root / 'agents/common/recipes/gcp/spanner' /
            'read-import-records.md',
            self._repo_root / 'agents/common/recipes/gcp/cloud-run' /
            'describe-ingestion-helper.md',
            self._repo_root / 'agents/common/recipes/gcp/cloud-build' /
            'resolve-runtime-provenance.md',
            self._repo_root / 'agents/common/recipes/gcp/workflows' /
            'describe-execution.md',
        )
        for path in deleted_paths:
            with self.subTest(path=path):
                self.assertFalse(path.exists())

        workflow_recipe = (self._repo_root / 'agents/common/recipes/gcp' /
                           'workflows/list-import-executions.md').read_text(
                               encoding='utf-8')
        for required in ('gcloud workflows executions describe',
                         'do not describe that execution again',
                         'caller starts from an exact execution ID'):
            with self.subTest(workflow_required=required):
                self.assertIn(required, workflow_recipe)

        runtime_guidance = '\n'.join(
            path.read_text(encoding='utf-8')
            for path in self._repo_root.glob('agents/**/*.md'))
        for forbidden in ('gcloud builds list', 'gcloud builds describe',
                          'read_import_records.py',
                          'describe-ingestion-helper.md'):
            with self.subTest(runtime_forbidden=forbidden):
                self.assertNotIn(forbidden, runtime_guidance)

    def test_import_correlation_recipe_is_bounded_and_returns_run_evidence(
            self):
        recipe = (self._repo_root / 'agents/common/recipes/gcp/imports' /
                  'correlate-import-runs.md').read_text(encoding='utf-8')

        for required in ('--mode=import_history', '--mode=import_version',
                         'gcs_base_path', 'workflow_execution_id',
                         'batch_job_id', 'summary status',
                         'bounded checkpointed ET history',
                         'one checkpointed ET',
                         'counts unique versions',
                         'caller must state the effective limit',
                         'bounded version-discovery query', '1 through 20',
                         './agents/common/run_python.sh'):
            with self.subTest(required=required):
                self.assertIn(required, recipe)
        self.assertIn('does not call\nWorkflow or Batch APIs', recipe)
        self.assertNotIn('<IMPORT_PREFIX>/**', recipe)
        self.assertNotIn('Spanner name candidates', recipe)

    def test_python_wrapper_uses_repository_environment_without_minor_pin(
            self):
        wrapper = (self._repo_root /
                   'agents/common/run_python.sh').read_text(encoding='utf-8')

        self.assertIn('.env/bin/python', wrapper)
        self.assertNotIn('Expected Python 3.12', wrapper)


if __name__ == '__main__':
    unittest.main()

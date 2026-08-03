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
            if path.name == 'catalog.md':
                continue
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
                         'Infrastructure actually used', 'Never use MCP tools',
                         'Keep code, manifest, configured schedule'):
            with self.subTest(required=required):
                self.assertIn(required, skill)

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
        historical = (recipe_root / 'gcs/find-historical-summary.md').read_text(
            encoding='utf-8')
        artifacts = (recipe_root / 'gcs/list-version-artifacts.md').read_text(
            encoding='utf-8')
        logs = (recipe_root /
                'logging/fetch-batch-logs.md').read_text(encoding='utf-8')
        builds = (recipe_root /
                  'cloud-build/resolve-runtime-provenance.md').read_text(
                      encoding='utf-8')

        self.assertIn('<YYYY_MM_DD>*/import_summary.json', historical)
        self.assertNotIn('<IMPORT_PREFIX>/**/', historical)
        self.assertIn('<IMPORT_PREFIX>/<VERSION>/**', artifacts)
        self.assertIn('--limit=<LIMIT_PLUS_ONE>', artifacts)
        for required in ('labels.job_uid', 'timestamp>=', 'timestamp<=',
                         '--limit=<LIMIT_PLUS_ONE>', 'jsonPayload.log_type'):
            with self.subTest(log_required=required):
                self.assertIn(required, logs)
        self.assertIn('finishTime<', builds)
        self.assertIn('--limit=<LIMIT>', builds)

    def test_import_correlation_recipe_is_bounded_and_composite(self):
        recipe = (self._repo_root / 'agents/common/recipes/gcp/imports' /
                  'correlate-import-runs.md').read_text(encoding='utf-8')

        for required in ('--mode=import_history', '--mode=import_version',
                         '1 through 20', './agents/common/run_python.sh'):
            with self.subTest(required=required):
                self.assertIn(required, recipe)
        self.assertIn('does not call\nWorkflow or Batch APIs', recipe)
        self.assertNotIn('<IMPORT_PREFIX>/**', recipe)

    def test_python_wrapper_uses_repository_environment_without_minor_pin(self):
        wrapper = (self._repo_root /
                   'agents/common/run_python.sh').read_text(encoding='utf-8')

        self.assertIn('.env/bin/python', wrapper)
        self.assertNotIn('Expected Python 3.12', wrapper)


if __name__ == '__main__':
    unittest.main()

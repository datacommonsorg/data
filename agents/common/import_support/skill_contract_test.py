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
"""Tests for the repository-local Antigravity skill contract."""

import json
from pathlib import Path
import re
import unittest

from jsonschema import Draft202012Validator

_MARKDOWN_LINK = re.compile(r'\[[^]]+\]\(([^)]+)\)')
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

    def test_skill_direct_links_exist(self):
        skill_root = self._repo_root / 'agents/skills/dc-import-info'
        paths = [skill_root / 'SKILL.md', *skill_root.glob('references/*.md')]

        for path in paths:
            for target in _MARKDOWN_LINK.findall(
                    path.read_text(encoding='utf-8')):
                if '://' in target or target.startswith('#'):
                    continue
                with self.subTest(source=path, target=target):
                    self.assertTrue((path.parent / target).resolve().is_file())

    def test_python_wrapper_uses_repository_environment_without_minor_pin(self):
        wrapper = (self._repo_root /
                   'agents/common/run_python.sh').read_text(encoding='utf-8')

        self.assertIn('.env/bin/python', wrapper)
        self.assertNotIn('Expected Python 3.12', wrapper)

    def test_snapshot_schema_is_valid(self):
        schema = json.loads(
            (self._repo_root /
             'agents/common/schemas/import_snapshot.schema.json').read_text(
                 encoding='utf-8'))

        Draft202012Validator.check_schema(schema)


if __name__ == '__main__':
    unittest.main()

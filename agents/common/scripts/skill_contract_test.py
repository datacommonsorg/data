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
"""Tests structural contracts for repository-owned agent guidance."""

import json
from pathlib import Path
import re
import unittest

import yaml

_MARKDOWN_LINK = re.compile(r'\[[^]]+\]\(([^)]+)\)')
_ROUTE_ROW = re.compile(
    r'^\| (?P<need>[^|]+) \| \[[^]]+\]\((?P<target>[^)]+)\) \|$', re.MULTILINE)
_EXPECTED_SKILL_ROUTES = (
    ('Find or select imports', '../../common/recipes/local/list-imports.md'),
    ('Verify deployed Scheduler schedule and Workflow target',
     '../../common/recipes/gcp/scheduler/describe-job.md'),
    ('Read current status for one import, exact current version, or bounded current snapshots across imports',
     '../../common/recipes/gcp/spanner/query-import-status.md'),
    ('List recent finalized versions, GCS paths, and Batch IDs',
     '../../common/recipes/gcp/gcs/list-import-summaries.md'),
    ("Read one supplied or selected version's summary",
     '../../common/recipes/gcp/gcs/read-version-summary.md'),
    ('Read the current candidate or accepted-output pointer',
     '../../common/recipes/gcp/gcs/read-version-pointer.md'),
    ("List one selected version's files",
     '../../common/recipes/gcp/gcs/list-version-artifacts.md'),
    ('Inspect one exact Batch job',
     '../../common/recipes/gcp/batch/describe-job.md'),
    ('Inspect tasks for one exact Batch job',
     '../../common/recipes/gcp/batch/list-tasks.md'),
    ('Fetch bounded structured logs for one exact Batch job',
     '../../common/recipes/gcp/logging/fetch-batch-logs.md'),
    ('Trace an exact Batch job to runtime-image or source-commit evidence, only when explicitly requested',
     '../../common/recipes/gcp/batch/trace-batch-job-source-commit.md'),
)


def _local_markdown_targets(text: str):
    """Yields file portions of local Markdown links."""
    for raw_target in _MARKDOWN_LINK.findall(text):
        target = raw_target.strip()
        if target.startswith('<') and '>' in target:
            target = target[1:target.index('>')]
        else:
            target = target.split(maxsplit=1)[0]
        if (not target or target.startswith('#') or '://' in target or
                target.startswith(('mailto:', 'chatgpt-conversation:'))):
            continue
        target = target.split('#', maxsplit=1)[0]
        if target:
            yield target


class SkillContractTest(unittest.TestCase):

    def setUp(self):
        self._repo_root = Path(__file__).parents[3]
        self._agents_root = self._repo_root / 'agents'
        self._skill_path = self._agents_root / 'skills/dc-import-info/SKILL.md'
        self._prompt_path = self._agents_root / 'prompts/dc-import-info.md'

    def _read(self, relative_path: str) -> str:
        return (self._repo_root / relative_path).read_text(encoding='utf-8')

    def test_registry_points_to_versioned_skill(self):
        registry = json.loads(self._read('.agents/skills.json'))
        paths = [entry['path'] for entry in registry['entries']]

        self.assertIn('agents/skills/dc-import-info', paths)
        self.assertEqual(len(paths), len(set(paths)))
        for path in paths:
            with self.subTest(path=path):
                self.assertTrue((self._repo_root / path / 'SKILL.md').is_file())

    def test_all_agent_markdown_links_resolve(self):
        markdown_paths = tuple(self._agents_root.rglob('*.md'))

        self.assertGreater(len(markdown_paths), 1)
        for source in markdown_paths:
            text = source.read_text(encoding='utf-8')
            for target in _local_markdown_targets(text):
                with self.subTest(source=source, target=target):
                    self.assertTrue(
                        (source.parent / target).resolve().is_file())

    def test_skill_keeps_safety_and_progressive_loading(self):
        skill = self._skill_path.read_text(encoding='utf-8')
        normalized = re.sub(r'\s+', ' ', skill)

        for heading in ('## Safety',
                        '## Classify the request before loading context',
                        '## Review cloud operations', '## Select an operation',
                        '## Report evidence'):
            with self.subTest(heading=heading):
                self.assertIn(heading, skill)

        for guardrail in (
                'Treat GCP and the data repository as read-only',
                'Never replace a missing identifier with a broad',
                'complete attempt history, Workflow execution inspection',
                'loader status, and remediation as unsupported',
                'Do not load architecture, environment configuration, or cloud recipes'
        ):
            with self.subTest(guardrail=guardrail):
                self.assertIn(guardrail, normalized)

        self.assertIn('../../common/recipes/local/list-imports.md', skill)
        self.assertIn(
            '../../common/references/import-automation/architecture.md', skill)
        self.assertIn('../../dependency-setup.md', skill)

    def test_skill_routes_map_to_exact_recipe_paths(self):
        skill = self._skill_path.read_text(encoding='utf-8')
        routes = tuple((match.group('need').strip(), match.group('target'))
                       for match in _ROUTE_ROW.finditer(skill))

        self.assertEqual(_EXPECTED_SKILL_ROUTES, routes)

    def test_manual_prompt_grounds_commands_by_repository_path(self):
        prompt = self._prompt_path.read_text(encoding='utf-8')

        self.assertIn('exact repository recipe path', prompt)
        self.assertNotRegex(prompt, re.compile(r'recipe ID', re.IGNORECASE))

    def test_runtime_environment_registry_is_minimal_and_complete(self):
        registry = yaml.safe_load(
            self._read('agents/common/config/import-environments.yaml'))
        skill = self._skill_path.read_text(encoding='utf-8')
        required_fields = {
            'scheduler': {'project', 'location'},
            'workflow': {'project', 'location', 'import_workflow'},
            'batch': {'project', 'location'},
            'gcs': {'client_project', 'output_bucket'},
            'spanner': {'project', 'instance', 'database'},
        }

        self.assertIn('../../common/config/import-environments.yaml', skill)
        self.assertEqual({'default_environment', 'environments'}, set(registry))
        self.assertEqual('prod', registry['default_environment'])
        self.assertEqual({'prod', 'staging'}, set(registry['environments']))

        for name, environment in registry['environments'].items():
            with self.subTest(environment=name):
                self.assertEqual(set(required_fields), set(environment))
                for section, fields in required_fields.items():
                    self.assertEqual(fields, set(environment[section]))
                    for field in fields:
                        self.assertIsInstance(environment[section][field], str)
                        self.assertTrue(environment[section][field])


if __name__ == '__main__':
    unittest.main()

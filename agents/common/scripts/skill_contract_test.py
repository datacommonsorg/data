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
_MARKDOWN_HEADING = re.compile(r'^\s{0,3}#{1,6}[ \t]+(.+?)(?:[ \t]+#+)?[ \t]*$')
_MARKDOWN_FENCE = re.compile(r'^\s{0,3}(`{3,}|~{3,})')
_ROUTE_ROW = re.compile(
    r'^\| (?P<need>[^|]+) \| \[(?P<label>[^]]+)\]\((?P<target>[^)]+)\) \|$',
    re.MULTILINE)
_EXPECTED_SKILL_ROUTES = (
    ('Find or select imports', 'references/imports.md'),
    ('Verify deployed Scheduler schedule and Workflow target',
     'references/scheduler.md'),
    ('Read current status, the current or latest run or attempt, or the version recorded for the current attempt; or read bounded current snapshots across imports',
     'references/spanner.md'),
    ('List recent or latest import versions, GCS paths, and Batch IDs',
     'references/gcs.md'),
    ("Read one supplied or selected version's summary", 'references/gcs.md'),
    ('Find the last successful or accepted import version',
     'references/gcs.md'),
    ('Compare a current or selected import version with the last successful version',
     'references/import-evidence-flow.md'),
    ("List one selected version's files", 'references/gcs.md'),
    ('Inspect one exact Batch job', 'references/batch.md'),
    ('Inspect tasks for one exact Batch job', 'references/batch.md'),
    ('Fetch bounded structured logs for one exact Batch job',
     'references/batch.md'),
    ('Trace an exact Batch job to runtime-image or source-commit evidence, only when explicitly requested',
     'references/batch.md'),
)


def _local_markdown_links(text: str):
    """Yields file and fragment portions of local Markdown links."""
    for raw_target in _MARKDOWN_LINK.findall(text):
        target = raw_target.strip()
        if target.startswith('<') and '>' in target:
            target = target[1:target.index('>')]
        else:
            target = target.split(maxsplit=1)[0]
        if (not target or '://' in target or target.startswith(
            ('mailto:', 'chatgpt-conversation:'))):
            continue
        path, _, fragment = target.partition('#')
        if path or fragment:
            yield path, fragment


def _markdown_heading_fragments(text: str):
    """Returns GitHub-style fragments for Markdown headings."""
    fragments = set()
    fragment_counts = {}
    fence = None

    for line in text.splitlines():
        fence_match = _MARKDOWN_FENCE.match(line)
        if fence_match:
            marker = fence_match.group(1)
            if fence is None:
                fence = marker
            elif marker[0] == fence[0] and len(marker) >= len(fence):
                fence = None
            continue
        if fence is not None:
            continue

        heading_match = _MARKDOWN_HEADING.match(line)
        if not heading_match:
            continue
        heading = heading_match.group(1).lower()
        base_fragment = re.sub(r'[^\w\- ]', '', heading)
        base_fragment = re.sub(r'\s+', '-', base_fragment)
        duplicate_index = fragment_counts.get(base_fragment, 0)
        fragment_counts[base_fragment] = duplicate_index + 1
        fragment = (base_fragment if duplicate_index == 0 else
                    f'{base_fragment}-{duplicate_index}')
        fragments.add(fragment)

    return fragments


class SkillContractTest(unittest.TestCase):

    def setUp(self):
        self._repo_root = Path(__file__).parents[3]
        self._agents_root = self._repo_root / 'agents'
        self._skill_path = (self._agents_root /
                            'skills/dc-import-diagnostics/SKILL.md')
        self._prompt_path = (self._agents_root /
                             'prompts/dc-import-diagnostics-starter.md')

    def _read(self, relative_path: str) -> str:
        return (self._repo_root / relative_path).read_text(encoding='utf-8')

    def test_registry_points_to_versioned_skill(self):
        registry = json.loads(self._read('.agents/skills.json'))
        paths = [entry['path'] for entry in registry['entries']]

        self.assertIn('agents/skills/dc-import-diagnostics', paths)
        self.assertEqual(len(paths), len(set(paths)))
        for path in paths:
            with self.subTest(path=path):
                self.assertTrue((self._repo_root / path / 'SKILL.md').is_file())

    def test_all_agent_markdown_links_resolve(self):
        markdown_paths = tuple(self._agents_root.rglob('*.md'))
        heading_fragments = {}

        self.assertGreater(len(markdown_paths), 1)
        for source in markdown_paths:
            text = source.read_text(encoding='utf-8')
            for target, fragment in _local_markdown_links(text):
                linked_path = ((source.parent / target).resolve()
                               if target else source.resolve())
                with self.subTest(source=source,
                                  target=target,
                                  fragment=fragment):
                    self.assertTrue(linked_path.is_file())
                    if fragment:
                        if linked_path not in heading_fragments:
                            linked_text = linked_path.read_text(
                                encoding='utf-8')
                            heading_fragments[linked_path] = (
                                _markdown_heading_fragments(linked_text))
                        self.assertIn(fragment, heading_fragments[linked_path])

    def test_troubleshooting_guides_are_reachable_from_entrypoint(self):
        troubleshooting_root = (
            self._agents_root /
            'skills/dc-import-diagnostics/troubleshooting').resolve()
        entrypoint = troubleshooting_root / 'troubleshooting.md'
        all_guides = {
            path.resolve() for path in troubleshooting_root.rglob('*.md')
        }
        reachable = set()
        pending = [entrypoint]

        while pending:
            source = pending.pop()
            if source in reachable:
                continue

            reachable.add(source)
            text = source.read_text(encoding='utf-8')
            for target, _ in _local_markdown_links(text):
                if not target:
                    continue
                linked_path = (source.parent / target).resolve()
                if linked_path in all_guides and linked_path not in reachable:
                    pending.append(linked_path)

        unreachable = sorted(
            str(path.relative_to(troubleshooting_root))
            for path in all_guides - reachable)
        self.assertFalse(
            unreachable,
            'Troubleshooting guides are not reachable from troubleshooting.md: '
            f'{unreachable}')

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
                'loader status, and execution of remediation as unsupported',
                'Do not load architecture, environment configuration, or cloud operational references'
        ):
            with self.subTest(guardrail=guardrail):
                self.assertIn(guardrail, normalized)

        self.assertIn('references/imports.md', skill)
        self.assertIn('references/architecture.md', skill)
        self.assertIn('../../dependency-setup.md', skill)

    def test_skill_routes_map_to_exact_reference_paths(self):
        skill = self._skill_path.read_text(encoding='utf-8')
        routes = tuple((match.group('need').strip(), match.group('target'))
                       for match in _ROUTE_ROW.finditer(skill))

        self.assertEqual(_EXPECTED_SKILL_ROUTES, routes)

    def test_skill_route_labels_match_operation_headings(self):
        skill = self._skill_path.read_text(encoding='utf-8')

        for match in _ROUTE_ROW.finditer(skill):
            label = match.group('label')
            target = match.group('target')
            reference = (self._skill_path.parent /
                         target).read_text(encoding='utf-8')
            with self.subTest(label=label, target=target):
                self.assertRegex(
                    reference,
                    re.compile(rf'^#{{1,2}} {re.escape(label)}$', re.MULTILINE))

    def test_version_terms_route_user_intent_without_duplicating_architecture(
            self):
        skill = self._skill_path.read_text(encoding='utf-8')
        architecture = self._read(
            'agents/skills/dc-import-diagnostics/references/architecture.md')

        for contract in (
                'An **ET attempt**',
                'A **candidate ET version**',
                'A **current ET output**',
                'Successful Batch completion proves only the technical compute outcome',
                '`staging_version.txt`',
                '`latest_version.txt`',
        ):
            with self.subTest(contract=contract):
                self.assertIn(contract, architecture)

        self.assertNotIn('### Runtime terminology', architecture)
        self.assertIn(
            'does not distinguish a run from a version or does not identify whether a version',
            re.sub(r'\s+', ' ', skill))

    def test_manual_prompt_grounds_commands_by_repository_path(self):
        prompt = self._prompt_path.read_text(encoding='utf-8')

        self.assertIn('exact repository reference path', prompt)
        self.assertNotRegex(prompt, re.compile(r'recipe', re.IGNORECASE))

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

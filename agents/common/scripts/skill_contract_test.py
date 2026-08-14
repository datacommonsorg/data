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
import tempfile
import unittest

import yaml

_MARKDOWN_LINK = re.compile(r'\[[^]]+\]\(([^)]+)\)')
_PLAIN_MARKDOWN_HEADING = re.compile(r'^#{1,6} ([A-Za-z0-9][A-Za-z0-9 -]*)$')
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


def _markdown_lines_outside_fences(text: str):
    """Yields line numbers and Markdown outside fenced code blocks."""
    fence = None

    for line_number, line in enumerate(text.splitlines(), start=1):
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

        yield line_number, line


def _local_markdown_links(text: str):
    """Yields local Markdown link paths, fragments, and original targets."""
    for _, line in _markdown_lines_outside_fences(text):
        for raw_target in _MARKDOWN_LINK.findall(line):
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
                yield path, fragment, target


def _plain_heading_fragments(text: str):
    """Maps fragments for the supported plain ATX heading convention."""
    fragments = {}

    for line_number, line in _markdown_lines_outside_fences(text):
        heading_match = _PLAIN_MARKDOWN_HEADING.match(line)
        if not heading_match:
            continue
        heading = heading_match.group(1).lower()
        fragment = re.sub(r' +', '-', heading)
        fragments.setdefault(fragment, []).append(line_number)

    return fragments


def _local_markdown_link_errors(repo_root: Path, entrypoints):
    """Returns errors for reachable local Markdown links."""
    repo_root = repo_root.resolve()
    pending = [path.resolve() for path in entrypoints]
    visited = set()
    heading_fragments = {}
    errors = []

    while pending:
        source = pending.pop()
        if source in visited:
            continue
        visited.add(source)

        try:
            source_name = source.relative_to(repo_root)
        except ValueError:
            errors.append(f'Entry point resolves outside repository: {source}')
            continue
        if not source.is_file():
            errors.append(f'Markdown entry point does not exist: {source_name}')
            continue

        text = source.read_text(encoding='utf-8')
        for target, fragment, raw_target in _local_markdown_links(text):
            linked_path = ((source.parent /
                            target).resolve() if target else source)
            try:
                linked_name = linked_path.relative_to(repo_root)
            except ValueError:
                errors.append(
                    f'{source_name}: local link "{raw_target}" resolves '
                    f'outside repository: {linked_path}')
                continue

            if not linked_path.is_file():
                errors.append(
                    f'{source_name}: local link "{raw_target}" targets '
                    f'missing file: {linked_name}')
                continue

            if fragment:
                if linked_path.suffix.lower() != '.md':
                    errors.append(
                        f'{source_name}: local link "{raw_target}" uses a '
                        f'fragment for non-Markdown file: {linked_name}')
                else:
                    if linked_path not in heading_fragments:
                        linked_text = linked_path.read_text(encoding='utf-8')
                        heading_fragments[linked_path] = (
                            _plain_heading_fragments(linked_text))
                    matching_lines = heading_fragments[linked_path].get(
                        fragment, [])
                    if not matching_lines:
                        errors.append(
                            f'{source_name}: local link "{raw_target}" '
                            f'does not match a plain heading in {linked_name}. '
                            'Referenced headings must use plain "# Heading" '
                            'syntax with only letters, numbers, spaces, and '
                            'hyphens.')
                    elif len(matching_lines) > 1:
                        errors.append(
                            f'{source_name}: local link "{raw_target}" '
                            f'matches {len(matching_lines)} plain headings in '
                            f'{linked_name} at lines {matching_lines}. '
                            'Headings used as fragment destinations must be '
                            'unique within their file.')

            if (linked_path.suffix.lower() == '.md' and
                    linked_path not in visited):
                pending.append(linked_path)

    return errors


class MarkdownLinkContractTest(unittest.TestCase):

    def test_reachable_links_follow_plain_unique_headings_lazily(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir) / 'repo'
            skill = repo_root / 'agents/skills/example/SKILL.md'
            reference = repo_root / 'docs/reference.md'
            unrelated = repo_root / 'agents/unrelated.md'
            skill.parent.mkdir(parents=True)
            reference.parent.mkdir(parents=True)
            unrelated.parent.mkdir(parents=True, exist_ok=True)
            skill.write_text(
                '[Reference](../../../docs/reference.md#stable-section)\n',
                encoding='utf-8')
            reference.write_text(
                '# Reference\n\n'
                '[Details](#details)\n\n'
                '## Stable section\n\n'
                '### Use when\n\n'
                '### Use when\n\n'
                '## Details\n',
                encoding='utf-8')
            unrelated.write_text('[Broken](missing.md)\n', encoding='utf-8')

            self.assertEqual([],
                             _local_markdown_link_errors(repo_root, [skill]))

    def test_referenced_heading_failures_are_actionable(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            repo_root = temp_root / 'repo'
            skill = repo_root / 'agents/skills/example/SKILL.md'
            reference = repo_root / 'docs/reference.md'
            outside = temp_root / 'outside.md'
            skill.parent.mkdir(parents=True)
            reference.parent.mkdir(parents=True)
            outside.write_text('# Outside\n', encoding='utf-8')
            skill.write_text(
                '[Duplicate](../../../docs/reference.md#duplicate-section)\n'
                '[Formatted](../../../docs/reference.md#formatted-section)\n'
                '[Outside](../../../../outside.md)\n',
                encoding='utf-8')
            reference.write_text(
                '## Duplicate section\n\n'
                '## Duplicate section\n\n'
                '## Formatted *section*\n',
                encoding='utf-8')

            errors = _local_markdown_link_errors(repo_root, [skill])
            message = '\n'.join(errors)

            self.assertIn('matches 2 plain headings', message)
            self.assertIn('does not match a plain heading', message)
            self.assertIn('Referenced headings must use plain', message)
            self.assertIn('resolves outside repository', message)
            self.assertIn('SKILL.md', message)


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

    def test_reachable_agent_markdown_links_resolve(self):
        registry = json.loads(self._read('.agents/skills.json'))
        entrypoints = [
            self._repo_root / entry['path'] / 'SKILL.md'
            for entry in registry['entries']
        ]
        entrypoints.append(self._agents_root / 'README.md')

        errors = _local_markdown_link_errors(self._repo_root, entrypoints)

        self.assertFalse(errors, '\n'.join(errors))

    def test_common_references_do_not_depend_on_skills(self):
        common_references = self._agents_root / 'common/references'
        skills_root = (self._agents_root / 'skills').resolve()
        violations = []

        for source in common_references.rglob('*.md'):
            source_name = source.relative_to(self._repo_root)
            text = source.read_text(encoding='utf-8')
            for target, _, raw_target in _local_markdown_links(text):
                if not target:
                    continue
                linked_path = (source.parent / target).resolve()
                try:
                    linked_name = linked_path.relative_to(skills_root)
                except ValueError:
                    continue
                violations.append(
                    f'{source_name} -> agents/skills/{linked_name} '
                    f'(link: {raw_target})')

        self.assertFalse(
            violations,
            'Common references must not depend on skill-owned files:\n' +
            '\n'.join(violations))

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
            for target, _, _ in _local_markdown_links(text):
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
        self.assertIn(
            '../../common/references/import-automation/architecture.md', skill)
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
            'agents/common/references/import-automation/architecture.md')

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


class ImportCodeReviewSkillContractTest(unittest.TestCase):

    def setUp(self):
        self._repo_root = Path(__file__).parents[3]
        self._agents_root = self._repo_root / 'agents'
        self._skill_root = (self._agents_root / 'skills/dc-import-code-review')
        self._skill_path = self._skill_root / 'SKILL.md'
        self._prompt_path = (self._agents_root /
                             'prompts/dc-import-code-review-starter.md')

    def _read(self, relative_path: str) -> str:
        return (self._repo_root / relative_path).read_text(encoding='utf-8')

    def test_review_skill_is_registered_and_discoverable(self):
        registry = json.loads(self._read('.agents/skills.json'))
        paths = [entry['path'] for entry in registry['entries']]
        readme = self._read('agents/README.md')
        prompt = self._prompt_path.read_text(encoding='utf-8')

        self.assertIn('agents/skills/dc-import-code-review', paths)
        self.assertIn('prompts/dc-import-code-review-starter.md', readme)
        self.assertIn('`dc-import-code-review` skill', prompt)

    def test_review_skill_keeps_scope_safety_and_output_contract(self):
        skill = self._skill_path.read_text(encoding='utf-8')
        normalized = re.sub(r'\s+', ' ', skill)

        for contract in (
                'Report findings only for changed files under `scripts/**` and `statvar_imports/**`',
                'Treat the repository and GitHub as read-only',
                'If the review target is ambiguous',
                'Never run `gh pr checkout` over the active worktree',
                'Do not run tests that call live source, Data Commons, or cloud APIs',
                'references/guidelines.md',
                '../../common/references/import-automation/manifest.md',
        ):
            with self.subTest(contract=contract):
                self.assertIn(contract, normalized)

        for heading in ('## Review scope', '## Findings',
                        '## Positive findings', '## Coverage',
                        '## Verification and limitations'):
            with self.subTest(heading=heading):
                self.assertIn(heading, skill)

        for priority in ('| P0 |', '| P1 |', '| P2 |', '| P3 |'):
            with self.subTest(priority=priority):
                self.assertIn(priority, skill)

        for field in ('Finding', 'Impact', 'Recommendation'):
            with self.subTest(field=field):
                self.assertIn(f'- {field}:', skill)

        self.assertIn('Finding: Good - <WHAT WAS DONE CORRECTLY>', skill)
        self.assertIn('| File | Status | Result |', skill)

    def test_review_guidance_stays_single_and_lightweight(self):
        references = sorted(path.name for path in (self._skill_root /
                                                   'references').glob('*.md'))
        guidelines = (self._skill_root /
                      'references/guidelines.md').read_text(encoding='utf-8')

        self.assertEqual(['guidelines.md'], references)
        self.assertFalse((self._skill_root / 'README.md').exists())
        self.assertFalse((self._skill_root / 'scripts').exists())

        for stale_content in ('DCIR-', 'Evidence:', 'Last verified:',
                              '["support@datacommons.org"]', 'logging.fatal()',
                              'exit(1)'):
            with self.subTest(stale_content=stale_content):
                self.assertNotIn(stale_content, guidelines)


if __name__ == '__main__':
    unittest.main()

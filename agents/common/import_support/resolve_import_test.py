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
"""Tests for manifest import resolution."""

import json
from pathlib import Path
import tempfile
import unittest

from agents.common.import_support.resolve_import import build_import_catalog
from agents.common.import_support.resolve_import import ImportResolutionError
from agents.common.import_support.resolve_import import resolve_import


class ResolveImportTest(unittest.TestCase):

    def _write_manifest(self, root: Path, relative_path: str,
                        import_name: str) -> None:
        directory = root / relative_path
        directory.mkdir(parents=True)
        (directory / 'download.py').write_text('', encoding='utf-8')
        manifest = {
            'import_specifications': [{
                'import_name': import_name,
                'cron_schedule': '0 1 * * *',
                'scripts': ['python3 download.py'],
                'provenance_url': 'https://example.test/data',
            }]
        }
        (directory / 'manifest.json').write_text(json.dumps(manifest),
                                                 encoding='utf-8')

    def test_scans_statvar_imports_and_scripts(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self._write_manifest(root, 'statvar_imports/agency/one', 'One')
            self._write_manifest(root, 'scripts/agency/two', 'Two')

            catalog = build_import_catalog(root)

            self.assertEqual({'One', 'Two'}, set(catalog))
            record = resolve_import(catalog, 'Two')
            self.assertEqual('scripts/agency/two:Two',
                             record.absolute_import_name)
            self.assertIn('scripts/agency/two/download.py', record.source_paths)

    def test_duplicate_name_is_not_resolved_silently(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self._write_manifest(root, 'statvar_imports/one', 'Duplicate')
            self._write_manifest(root, 'scripts/two', 'Duplicate')

            with self.assertRaisesRegex(ImportResolutionError, 'not unique'):
                resolve_import(build_import_catalog(root), 'Duplicate')

    def test_repository_import_names_are_unique_and_round_trip(self):
        repo_root = Path(__file__).parents[3]

        catalog = build_import_catalog(repo_root)

        self.assertGreater(len(catalog), 0)
        for import_name, records in catalog.items():
            with self.subTest(import_name=import_name):
                self.assertEqual(1, len(records))
                self.assertEqual(records[0],
                                 resolve_import(catalog, import_name))

    def test_explicit_manifest_must_be_in_an_approved_root(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self._write_manifest(root, 'other/import_one', 'One')

            with self.assertRaisesRegex(ImportResolutionError, 'must be under'):
                build_import_catalog(root,
                                     root / 'other/import_one/manifest.json')

    def test_malformed_manifest_fails_loudly(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            path = root / 'scripts/import_one/manifest.json'
            path.parent.mkdir(parents=True)
            path.write_text('{not-json', encoding='utf-8')

            with self.assertRaisesRegex(ImportResolutionError,
                                        'Unable to parse'):
                build_import_catalog(root)


if __name__ == '__main__':
    unittest.main()

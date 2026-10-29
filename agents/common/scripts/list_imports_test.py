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
"""Tests for repository import catalog queries."""

import json
from pathlib import Path
import tempfile
import unittest

from agents.common.scripts.list_imports import build_import_catalog
from agents.common.scripts.list_imports import ImportCatalogError
from agents.common.scripts.list_imports import ImportRecord
from agents.common.scripts.list_imports import list_imports


def _record(import_name: str, cron_schedule: str | None = None) -> ImportRecord:
    directory = f'statvar_imports/{import_name.lower()}'
    return ImportRecord(import_name=import_name,
                        manifest_path=f'{directory}/manifest.json',
                        import_directory=directory,
                        absolute_import_name=f'{directory}:{import_name}',
                        cron_schedule=cron_schedule)


class ListImportsTest(unittest.TestCase):

    def _write_manifest(self, root: Path, relative_path: str,
                        specifications: list[object]) -> None:
        directory = root / relative_path
        directory.mkdir(parents=True)
        manifest = {'import_specifications': specifications}
        (directory / 'manifest.json').write_text(json.dumps(manifest),
                                                 encoding='utf-8')

    def test_builds_catalog_from_both_approved_roots(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self._write_manifest(root, 'statvar_imports/agency/one', [{
                'import_name': 'One',
                'cron_schedule': '0 1 * * *',
            }])
            self._write_manifest(root, 'scripts/agency/two', [{
                'import_name': 'Two',
            }])

            catalog = build_import_catalog(root)

            self.assertEqual({'One', 'Two'}, set(catalog))
            self.assertEqual('scripts/agency/two:Two',
                             catalog['Two'][0].absolute_import_name)

    def test_builds_catalog_from_multiple_specs_in_one_manifest(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self._write_manifest(root, 'scripts/agency/imports', [{
                'import_name': 'One',
            }, {
                'import_name': 'Two',
            }])

            catalog = build_import_catalog(root)

            self.assertEqual({'One', 'Two'}, set(catalog))
            self.assertEqual('scripts/agency/imports:One',
                             catalog['One'][0].absolute_import_name)
            self.assertEqual('scripts/agency/imports:Two',
                             catalog['Two'][0].absolute_import_name)

    def test_rejects_malformed_manifests_and_specifications(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            path = root / 'scripts/import_one/manifest.json'
            path.parent.mkdir(parents=True)
            path.write_text('{not-json', encoding='utf-8')
            with self.assertRaisesRegex(ImportCatalogError, 'Unable to parse'):
                build_import_catalog(root)

        for specification, expected_error in (([], 'Invalid specification'), ({
                'import_name': ''
        }, 'Empty import_name')):
            with self.subTest(specification=specification):
                with tempfile.TemporaryDirectory() as temp_dir:
                    root = Path(temp_dir)
                    self._write_manifest(root, 'scripts/import_one',
                                         [specification])
                    with self.assertRaisesRegex(ImportCatalogError,
                                                expected_error):
                        build_import_catalog(root)

    def test_uses_strongest_query_strategy(self):
        catalog = {
            'UNData': [_record('UNData')],
            'UNDatabase': [_record('UNDatabase')],
            'PopulationData': [_record('PopulationData')],
            'Other': [_record('Other')],
        }

        cases = (
            ('UNData', 'exact', ['UNData']),
            ('undata', 'case_insensitive_exact', ['UNData']),
            ('und', 'prefix', ['UNData', 'UNDatabase']),
            ('lationd', 'substring', ['PopulationData']),
        )
        for query, strategy, expected_names in cases:
            with self.subTest(query=query):
                result = list_imports(catalog, query=query)
                self.assertEqual(strategy, result['match_strategy'])
                self.assertEqual(
                    expected_names,
                    [item['import_name'] for item in result['results']])

    def test_fuzzy_query_returns_credible_typo_match(self):
        catalog = {
            'UNData': [_record('UNData')],
            'Other': [_record('Other')],
        }

        result = list_imports(catalog, query='undtaa')

        self.assertEqual('fuzzy', result['match_strategy'])
        self.assertEqual(['UNData'],
                         [item['import_name'] for item in result['results']])

        result = list_imports(catalog, query='zz')
        self.assertEqual('none', result['match_strategy'])
        self.assertEqual([], result['results'])

        result = list_imports(catalog, query='zzzzzz')
        self.assertEqual('none', result['match_strategy'])
        self.assertEqual([], result['results'])

    def test_applies_autorefresh_after_selecting_query_strategy(self):
        catalog = {
            'Exact': [_record('Exact')],
            'ExactConfigured': [_record('ExactConfigured', '0 1 * * *')],
        }

        result = list_imports(catalog, query='Exact', autorefresh='configured')

        self.assertEqual('exact', result['match_strategy'])
        self.assertEqual(0, result['matched_import_count'])
        self.assertEqual([], result['results'])

    def test_defaults_to_five_deterministic_results(self):
        catalog = {
            name: [_record(name)]
            for name in ('zulu', 'Echo', 'delta', 'Alpha', 'charlie', 'beta')
        }

        result = list_imports(catalog)

        self.assertEqual('all', result['match_strategy'])
        self.assertEqual(['Alpha', 'beta', 'charlie', 'delta', 'Echo'],
                         [item['import_name'] for item in result['results']])
        self.assertEqual(6, result['matched_import_count'])
        self.assertEqual(5, result['returned_import_count'])
        self.assertTrue(result['result_truncated'])

    def test_returns_bucket_relative_gcs_object_prefix(self):
        record = ImportRecord(
            import_name='ExampleImport',
            manifest_path='scripts/example/manifest.json',
            import_directory='scripts/example',
            absolute_import_name='scripts/example:ExampleImport',
            cron_schedule=None,
        )

        result = list_imports({'ExampleImport': [record]},
                              query='ExampleImport')

        selected = result['results'][0]
        self.assertEqual('scripts/example/ExampleImport',
                         selected['gcs_object_prefix'])
        self.assertFalse(selected['gcs_object_prefix'].startswith('gs://'))

    def test_rejects_invalid_limit_autorefresh_and_duplicate_names(self):
        for limit in (0, 101):
            with self.subTest(limit=limit):
                with self.assertRaisesRegex(ImportCatalogError,
                                            'limit must be between'):
                    list_imports({}, limit=limit)

        with self.assertRaisesRegex(ImportCatalogError, 'autorefresh must be'):
            list_imports({}, autorefresh='invalid')

        record = _record('Duplicate')
        with self.assertRaisesRegex(ImportCatalogError, 'not unique'):
            list_imports({'Duplicate': [record, record]})

    def test_repository_query_finds_undata(self):
        repo_root = Path(__file__).parents[3]

        result = list_imports(build_import_catalog(repo_root), query='undata')

        self.assertEqual('case_insensitive_exact', result['match_strategy'])
        self.assertEqual(1, result['matched_import_count'])
        self.assertEqual('UNData', result['results'][0]['import_name'])
        self.assertEqual('statvar_imports/undata/manifest.json',
                         result['results'][0]['manifest_path'])
        self.assertEqual('statvar_imports/undata/UNData',
                         result['results'][0]['gcs_object_prefix'])


if __name__ == '__main__':
    unittest.main()

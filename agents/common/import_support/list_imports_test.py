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

from pathlib import Path
import unittest

from agents.common.import_support.list_imports import list_imports
from agents.common.import_support.resolve_import import build_import_catalog
from agents.common.import_support.resolve_import import ImportRecord
from agents.common.import_support.resolve_import import ImportResolutionError


def _record(import_name: str, cron_schedule: str | None) -> ImportRecord:
    directory = f'statvar_imports/{import_name.lower()}'
    return ImportRecord(import_name=import_name,
                        manifest_path=f'{directory}/manifest.json',
                        import_directory=directory,
                        absolute_import_name=f'{directory}:{import_name}',
                        spec_index=0,
                        cron_schedule=cron_schedule,
                        scripts=(),
                        source_files=(),
                        provenance_url=None,
                        provenance_description=None,
                        import_inputs=(),
                        validation_config_file=None,
                        user_script_timeout=None,
                        resource_limits={},
                        config_override_keys=(),
                        source_paths=())


class ListImportsTest(unittest.TestCase):

    def test_filters_name_and_configured_autorefresh(self):
        catalog = {
            'ZuluCentral': [_record('ZuluCentral', '0 1 * * *')],
            'alphaCentral': [_record('alphaCentral', None)],
            'Other': [_record('Other', '0 2 * * *')],
        }

        result = list_imports(catalog,
                              name_contains='CENTRAL',
                              autorefresh='configured')

        self.assertEqual(3, result['scanned_import_count'])
        self.assertEqual(1, result['matched_import_count'])
        self.assertEqual('ZuluCentral', result['results'][0]['import_name'])
        self.assertTrue(result['results'][0]['configured_autorefresh'])

        result = list_imports(catalog,
                              name_contains='central',
                              autorefresh='not_configured')

        self.assertEqual('alphaCentral', result['results'][0]['import_name'])
        self.assertFalse(result['results'][0]['configured_autorefresh'])

    def test_sorts_and_reports_truncation(self):
        catalog = {
            'zulu': [_record('zulu', None)],
            'Alpha': [_record('Alpha', None)],
            'beta': [_record('beta', None)],
        }

        result = list_imports(catalog, limit=2)

        self.assertEqual(['Alpha', 'beta'],
                         [item['import_name'] for item in result['results']])
        self.assertEqual(3, result['matched_import_count'])
        self.assertEqual(2, result['returned_import_count'])
        self.assertTrue(result['result_truncated'])

    def test_rejects_invalid_limit_and_duplicate_names(self):
        for limit in (0, 101):
            with self.subTest(limit=limit):
                with self.assertRaisesRegex(ImportResolutionError,
                                            'limit must be between'):
                    list_imports({}, limit=limit)

        record = _record('Duplicate', None)
        with self.assertRaisesRegex(ImportResolutionError, 'not unique'):
            list_imports({'Duplicate': [record, record]})

    def test_repository_catalog_contains_bis_import(self):
        repo_root = Path(__file__).parents[3]
        result = list_imports(build_import_catalog(repo_root),
                              name_contains='CentralBankPolicyRate',
                              autorefresh='configured',
                              limit=20)

        self.assertEqual(1, result['matched_import_count'])
        self.assertEqual('BIS_CentralBankPolicyRate',
                         result['results'][0]['import_name'])
        self.assertEqual('0 05 * * 6', result['results'][0]['cron_schedule'])


if __name__ == '__main__':
    unittest.main()

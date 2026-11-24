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
"""Tests for manifest_utils.py."""

import json
import os
import tempfile
import unittest

from app.executor import manifest_utils


class ParseManifestTest(unittest.TestCase):

    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.manifest_path = os.path.join(self.tmp_dir.name, 'manifest.json')

    def tearDown(self):
        self.tmp_dir.cleanup()

    def test_loads_valid_manifest(self):
        """Tests that a valid manifest file is loaded as a dict."""
        manifest = {'import_specifications': [{'import_name': 'MyImport'}]}
        with open(self.manifest_path, 'w') as f:
            json.dump(manifest, f)

        self.assertEqual(manifest_utils.parse_manifest(self.manifest_path),
                         manifest)

    def test_raises_on_malformed_json(self):
        """Tests that malformed JSON raises a JSONDecodeError."""
        with open(self.manifest_path, 'w') as f:
            f.write('{not json')

        with self.assertRaises(json.JSONDecodeError):
            manifest_utils.parse_manifest(self.manifest_path)


class GetImportSpecTest(unittest.TestCase):

    _MANIFEST = {
        'import_specifications': [
            {
                'import_name': 'First',
                'curator_emails': ['a@example.com']
            },
            {
                'import_name': 'Second',
                'curator_emails': ['b@example.com']
            },
        ]
    }

    def test_returns_matching_spec(self):
        """Tests that the spec with the given import name is returned."""
        self.assertEqual(
            manifest_utils.get_import_spec(self._MANIFEST, 'Second'),
            self._MANIFEST['import_specifications'][1])

    def test_returns_none_when_name_not_found(self):
        """Tests that None is returned for an unknown import name."""
        self.assertIsNone(
            manifest_utils.get_import_spec(self._MANIFEST, 'Missing'))


class GetImportInputFilesTest(unittest.TestCase):

    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.import_dir = self.tmp_dir.name

    def tearDown(self):
        self.tmp_dir.cleanup()

    def _touch(self, *paths):
        for path in paths:
            full_path = os.path.join(self.import_dir, path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            open(full_path, 'w').close()

    def _path(self, *parts):
        return os.path.join(self.import_dir, *parts)

    def test_orders_template_mcf_node_mcf_then_cleaned_csv(self):
        """Tests that files are ordered template_mcf, node_mcf, cleaned_csv."""
        self._touch('data.tmcf', 'schema.mcf', 'output/data.csv')

        files = manifest_utils.get_import_input_files(
            {
                'cleaned_csv': 'output/data.csv',
                'node_mcf': 'schema.mcf',
                'template_mcf': 'data.tmcf',
            }, self.import_dir)

        self.assertEqual(files, [
            self._path('data.tmcf'),
            self._path('schema.mcf'),
            self._path('output', 'data.csv'),
        ])

    def test_expands_wildcards_and_lists_in_sorted_order(self):
        """Tests that wildcards and pattern lists expand in sorted order."""
        self._touch('output/b.csv', 'output/a.csv', 'output/sub/c.csv',
                    'extra.csv')

        files = manifest_utils.get_import_input_files(
            {'cleaned_csv': ['output/**/*.csv', 'extra.csv']}, self.import_dir)

        self.assertEqual(files, [
            self._path('output', 'a.csv'),
            self._path('output', 'b.csv'),
            self._path('output', 'sub', 'c.csv'),
            self._path('extra.csv'),
        ])

    def test_raises_when_exact_file_is_missing(self):
        """Tests that a missing non-wildcard file raises an error naming it."""
        self._touch('data.tmcf')

        with self.assertRaisesRegex(manifest_utils.MissingInputFilesError,
                                    'cleaned_csv:output/data.csv'):
            manifest_utils.get_import_input_files(
                {
                    'template_mcf': 'data.tmcf',
                    'cleaned_csv': 'output/data.csv',
                }, self.import_dir)

    def test_skips_wildcard_matching_no_files(self):
        """Tests that a wildcard matching no files is skipped."""
        self._touch('data.tmcf')

        files = manifest_utils.get_import_input_files(
            {
                'template_mcf': 'data.tmcf',
                'cleaned_csv': 'output/*.csv',
            }, self.import_dir)

        self.assertEqual(files, [self._path('data.tmcf')])

    def test_skips_empty_pattern(self):
        """Tests that an empty pattern is skipped."""
        self._touch('data.tmcf')

        files = manifest_utils.get_import_input_files(
            {
                'template_mcf': 'data.tmcf',
                'node_mcf': '',
            }, self.import_dir)

        self.assertEqual(files, [self._path('data.tmcf')])


if __name__ == '__main__':
    unittest.main()

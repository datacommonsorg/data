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
"""Tests for run_manifest_import."""

import contextlib
import io
import json
import os
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import run_manifest_import  # pylint: disable=wrong-import-position


class RunManifestImportTest(unittest.TestCase):

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.import_dir = self._tmp.name
        self.manifest = os.path.join(self.import_dir, 'manifest.json')

    def tearDown(self):
        self._tmp.cleanup()

    def _touch(self, *paths):
        for path in paths:
            full_path = os.path.join(self.import_dir, path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            open(full_path, 'w').close()

    def _write_manifest(self, import_inputs, import_name='MyImport'):
        with open(self.manifest, 'w') as f:
            json.dump(
                {
                    'import_specifications': [{
                        'import_name': 'OtherImport',
                        'import_inputs': []
                    }, {
                        'import_name': import_name,
                        'import_inputs': import_inputs
                    }]
                }, f)

    def _path(self, *parts):
        return os.path.join(self.import_dir, *parts)

    def test_orders_tmcf_node_mcf_then_csv(self):
        self._touch('data.tmcf', 'schema.mcf', 'output/data.csv')
        files = run_manifest_import.get_import_input_files(
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

    def test_expands_globs_and_lists_in_sorted_order(self):
        self._touch('data.tmcf', 'output/b.csv', 'output/a.csv',
                    'output/sub/c.csv', 'extra.csv')
        files = run_manifest_import.get_import_input_files(
            {
                'template_mcf': 'data.tmcf',
                'cleaned_csv': ['output/**/*.csv', 'extra.csv'],
            }, self.import_dir)
        self.assertEqual(files, [
            self._path('data.tmcf'),
            self._path('output', 'a.csv'),
            self._path('output', 'b.csv'),
            self._path('output', 'sub', 'c.csv'),
            self._path('extra.csv'),
        ])

    def test_glob_without_matches_is_allowed(self):
        self._touch('data.tmcf')
        files = run_manifest_import.get_import_input_files(
            {
                'template_mcf': 'data.tmcf',
                'cleaned_csv': 'output/*.csv'
            }, self.import_dir)
        self.assertEqual(files, [self._path('data.tmcf')])

    def test_warns_when_glob_matches_no_files(self):
        self._touch('data.tmcf', 'extra.csv')
        self._write_manifest([{
            'template_mcf': 'data.tmcf',
            'cleaned_csv': ['output/*.csv', 'extra.csv'],
        }])
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            commands = run_manifest_import.build_commands(
                self.manifest, 'MyImport', run_import_tool='tool')
        self.assertIn('[WARN] input0: no files match cleaned_csv:output/*.csv',
                      stderr.getvalue())
        self.assertEqual(commands[0][-2:],
                         [self._path('data.tmcf'),
                          self._path('extra.csv')])

    def test_no_warning_when_globs_match(self):
        self._touch('data.tmcf', 'output/a.csv')
        self._write_manifest([{
            'template_mcf': 'data.tmcf',
            'cleaned_csv': 'output/*.csv',
        }])
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            run_manifest_import.build_commands(self.manifest,
                                               'MyImport',
                                               run_import_tool='tool')
        self.assertNotIn('WARN', stderr.getvalue())

    def test_missing_literal_file_raises(self):
        self._touch('data.tmcf')
        with self.assertRaisesRegex(run_manifest_import.ManifestImportError,
                                    'cleaned_csv:output/data.csv'):
            run_manifest_import.get_import_input_files(
                {
                    'template_mcf': 'data.tmcf',
                    'cleaned_csv': 'output/data.csv'
                }, self.import_dir)

    def test_unknown_import_name_lists_available_imports(self):
        self._write_manifest([])
        with self.assertRaisesRegex(run_manifest_import.ManifestImportError,
                                    'OtherImport, MyImport'):
            run_manifest_import.build_commands(self.manifest, 'Missing')

    def test_no_import_inputs_raises(self):
        self._write_manifest([])
        with self.assertRaisesRegex(run_manifest_import.ManifestImportError,
                                    'no import_inputs'):
            run_manifest_import.build_commands(self.manifest, 'MyImport')

    def test_builds_one_command_per_import_input(self):
        self._touch('a.tmcf', 'output/a.csv', 'b.tmcf', 'output/b.csv')
        self._write_manifest([{
            'template_mcf': 'a.tmcf',
            'cleaned_csv': 'output/a.csv'
        }, {
            'template_mcf': 'b.tmcf',
            'cleaned_csv': 'output/b.csv'
        }])
        commands = run_manifest_import.build_commands(self.manifest,
                                                      'MyImport',
                                                      tool_args=['-n=4'],
                                                      run_import_tool='tool')
        self.assertEqual(commands, [
            [
                'tool', '-o=' + self._path('MyImport', 'input0', 'genmcf'),
                '-n=4', 'genmcf',
                self._path('a.tmcf'),
                self._path('output', 'a.csv')
            ],
            [
                'tool', '-o=' + self._path('MyImport', 'input1', 'genmcf'),
                '-n=4', 'genmcf',
                self._path('b.tmcf'),
                self._path('output', 'b.csv')
            ],
        ])

    def test_lint_mode_and_custom_output_dir(self):
        self._touch('a.tmcf', 'a.csv')
        self._write_manifest([{
            'template_mcf': 'a.tmcf',
            'cleaned_csv': 'a.csv'
        }])
        out_dir = self._path('custom_out')
        commands = run_manifest_import.build_commands(self.manifest,
                                                      'MyImport',
                                                      mode='lint',
                                                      output_dir=out_dir,
                                                      run_import_tool='tool')
        self.assertEqual(
            commands[0][:3],
            ['tool', '-o=' + os.path.join(out_dir, 'input0', 'lint'), 'lint'])

    @mock.patch.object(run_manifest_import.subprocess, 'run')
    def test_main_dry_run_does_not_run_tool(self, mock_run):
        self._touch('a.tmcf', 'a.csv')
        self._write_manifest([{
            'template_mcf': 'a.tmcf',
            'cleaned_csv': 'a.csv'
        }])
        exit_code = run_manifest_import.main([
            f'--manifest={self.manifest}', '--import_name=MyImport', '--dry_run'
        ])
        self.assertEqual(exit_code, 0)
        mock_run.assert_not_called()

    @mock.patch.object(run_manifest_import.subprocess, 'run')
    def test_main_runs_each_input_and_passes_tool_args(self, mock_run):
        mock_run.return_value = mock.Mock(returncode=0)
        self._touch('a.tmcf', 'a.csv', 'b.tmcf', 'b.csv')
        self._write_manifest([{
            'template_mcf': 'a.tmcf',
            'cleaned_csv': 'a.csv'
        }, {
            'template_mcf': 'b.tmcf',
            'cleaned_csv': 'b.csv'
        }])
        exit_code = run_manifest_import.main([
            f'--manifest={self.manifest}', '--import_name=MyImport', '--',
            '--existence-checks=false'
        ])
        self.assertEqual(exit_code, 0)
        self.assertEqual(mock_run.call_count, 2)
        command = mock_run.call_args_list[0].args[0]
        self.assertIn('--existence-checks=false', command)
        self.assertEqual(mock_run.call_args_list[0].kwargs['cwd'],
                         self.import_dir)

    @mock.patch.object(run_manifest_import.subprocess, 'run')
    def test_main_stops_on_tool_failure(self, mock_run):
        mock_run.return_value = mock.Mock(returncode=3)
        self._touch('a.tmcf', 'a.csv', 'b.tmcf', 'b.csv')
        self._write_manifest([{
            'template_mcf': 'a.tmcf',
            'cleaned_csv': 'a.csv'
        }, {
            'template_mcf': 'b.tmcf',
            'cleaned_csv': 'b.csv'
        }])
        exit_code = run_manifest_import.main(
            [f'--manifest={self.manifest}', '--import_name=MyImport'])
        self.assertEqual(exit_code, 3)
        self.assertEqual(mock_run.call_count, 1)

    def test_main_missing_file_returns_error(self):
        self._write_manifest([{'template_mcf': 'a.tmcf'}])
        exit_code = run_manifest_import.main(
            [f'--manifest={self.manifest}', '--import_name=MyImport'])
        self.assertEqual(exit_code, 1)


if __name__ == '__main__':
    unittest.main()

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
        patcher = mock.patch.object(run_manifest_import.subprocess, 'run')
        self.mock_run = patcher.start()
        self.mock_run.return_value = mock.Mock(returncode=0)
        self.addCleanup(patcher.stop)

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

    def _run_cli(self, *extra_args, import_name='MyImport'):
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            exit_code = run_manifest_import.main([
                f'--manifest={self.manifest}',
                f'--import_name={import_name}',
                *extra_args,
            ])
        return exit_code, stderr.getvalue()

    def test_orders_tmcf_node_mcf_then_csv(self):
        self._touch('data.tmcf', 'schema.mcf', 'output/data.csv')
        self._write_manifest([{
            'cleaned_csv': 'output/data.csv',
            'node_mcf': 'schema.mcf',
            'template_mcf': 'data.tmcf',
        }])

        exit_code, _ = self._run_cli()

        self.assertEqual(exit_code, 0)
        command = self.mock_run.call_args.args[0]
        self.assertEqual(command[-3:], [
            self._path('data.tmcf'),
            self._path('schema.mcf'),
            self._path('output', 'data.csv'),
        ])

    def test_expands_globs_and_lists_in_sorted_order(self):
        self._touch('data.tmcf', 'output/b.csv', 'output/a.csv',
                    'output/sub/c.csv', 'extra.csv')
        self._write_manifest([{
            'template_mcf': 'data.tmcf',
            'cleaned_csv': ['output/**/*.csv', 'extra.csv'],
        }])

        exit_code, _ = self._run_cli()

        self.assertEqual(exit_code, 0)
        command = self.mock_run.call_args.args[0]
        self.assertEqual(command[-5:], [
            self._path('data.tmcf'),
            self._path('output', 'a.csv'),
            self._path('output', 'b.csv'),
            self._path('output', 'sub', 'c.csv'),
            self._path('extra.csv'),
        ])

    def test_warns_and_continues_when_glob_matches_no_files(self):
        self._touch('data.tmcf', 'extra.csv')
        self._write_manifest([{
            'template_mcf': 'data.tmcf',
            'cleaned_csv': ['output/*.csv', 'extra.csv'],
        }])

        exit_code, stderr = self._run_cli()

        self.assertEqual(exit_code, 0)
        self.assertIn('WARN', stderr)
        self.assertIn('cleaned_csv:output/*.csv', stderr)
        command = self.mock_run.call_args.args[0]
        self.assertEqual(command[-2:],
                         [self._path('data.tmcf'),
                          self._path('extra.csv')])

    def test_no_warning_when_globs_match(self):
        self._touch('data.tmcf', 'output/a.csv')
        self._write_manifest([{
            'template_mcf': 'data.tmcf',
            'cleaned_csv': 'output/*.csv',
        }])

        exit_code, stderr = self._run_cli()

        self.assertEqual(exit_code, 0)
        self.assertNotIn('WARN', stderr)

    def test_fails_when_literal_file_is_missing(self):
        self._touch('data.tmcf')
        self._write_manifest([{
            'template_mcf': 'data.tmcf',
            'cleaned_csv': 'output/data.csv',
        }])

        exit_code, stderr = self._run_cli()

        self.assertEqual(exit_code, 1)
        self.assertIn('cleaned_csv:output/data.csv', stderr)
        self.mock_run.assert_not_called()

    def test_fails_and_lists_available_imports_when_import_name_unknown(self):
        self._write_manifest([])

        exit_code, stderr = self._run_cli(import_name='Missing')

        self.assertEqual(exit_code, 1)
        self.assertIn('OtherImport, MyImport', stderr)
        self.mock_run.assert_not_called()

    def test_fails_when_import_has_no_import_inputs(self):
        self._write_manifest([])

        exit_code, stderr = self._run_cli()

        self.assertEqual(exit_code, 1)
        self.assertIn('no import_inputs', stderr)
        self.mock_run.assert_not_called()

    def test_runs_once_per_import_input_and_forwards_tool_args(self):
        self._touch('a.tmcf', 'output/a.csv', 'b.tmcf', 'output/b.csv')
        self._write_manifest([{
            'template_mcf': 'a.tmcf',
            'cleaned_csv': 'output/a.csv'
        }, {
            'template_mcf': 'b.tmcf',
            'cleaned_csv': 'output/b.csv'
        }])

        exit_code, _ = self._run_cli('--', '-n=4', '--existence-checks=false')

        self.assertEqual(exit_code, 0)
        self.assertEqual(self.mock_run.call_count, 2)
        first_call, second_call = self.mock_run.call_args_list
        self.assertEqual(first_call.kwargs['cwd'], self.import_dir)
        self.assertEqual(first_call.args[0][1:], [
            '-o=' + self._path('MyImport', 'input0', 'genmcf'),
            '-n=4',
            '--existence-checks=false',
            'genmcf',
            self._path('a.tmcf'),
            self._path('output', 'a.csv'),
        ])
        self.assertEqual(second_call.args[0][1:], [
            '-o=' + self._path('MyImport', 'input1', 'genmcf'),
            '-n=4',
            '--existence-checks=false',
            'genmcf',
            self._path('b.tmcf'),
            self._path('output', 'b.csv'),
        ])

    def test_supports_lint_mode_and_custom_output_dir(self):
        self._touch('a.tmcf', 'a.csv')
        self._write_manifest([{
            'template_mcf': 'a.tmcf',
            'cleaned_csv': 'a.csv'
        }])
        out_dir = self._path('custom_out')

        exit_code, _ = self._run_cli('--mode=lint', f'--output_dir={out_dir}')

        self.assertEqual(exit_code, 0)
        command = self.mock_run.call_args.args[0]
        self.assertEqual(
            command[1:3],
            ['-o=' + os.path.join(out_dir, 'input0', 'lint'), 'lint'])

    def test_dry_run_does_not_invoke_tool(self):
        self._touch('a.tmcf', 'a.csv')
        self._write_manifest([{
            'template_mcf': 'a.tmcf',
            'cleaned_csv': 'a.csv'
        }])

        exit_code, _ = self._run_cli('--dry_run')

        self.assertEqual(exit_code, 0)
        self.mock_run.assert_not_called()

    def test_stops_immediately_when_tool_fails(self):
        self.mock_run.return_value = mock.Mock(returncode=3)
        self._touch('a.tmcf', 'a.csv', 'b.tmcf', 'b.csv')
        self._write_manifest([{
            'template_mcf': 'a.tmcf',
            'cleaned_csv': 'a.csv'
        }, {
            'template_mcf': 'b.tmcf',
            'cleaned_csv': 'b.csv'
        }])

        exit_code, _ = self._run_cli()

        self.assertEqual(exit_code, 3)
        self.assertEqual(self.mock_run.call_count, 1)

    def test_fails_cleanly_when_tool_cannot_be_launched(self):
        self.mock_run.side_effect = PermissionError('Permission denied')
        self._touch('a.tmcf', 'a.csv')
        self._write_manifest([{
            'template_mcf': 'a.tmcf',
            'cleaned_csv': 'a.csv'
        }])

        exit_code, stderr = self._run_cli()

        self.assertEqual(exit_code, 1)
        self.assertIn('Permission denied', stderr)


if __name__ == '__main__':
    unittest.main()

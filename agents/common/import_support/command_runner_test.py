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
"""Tests for the read-only command boundary."""

from pathlib import Path
import subprocess
import unittest
from unittest import mock

from agents.common.import_support.command_runner import CommandError
from agents.common.import_support.command_runner import ReadOnlyCommandRunner
from agents.common.import_support.command_runner import redact


class CommandRunnerTest(unittest.TestCase):

    def test_rejects_non_allowlisted_operation(self):
        runner = ReadOnlyCommandRunner(Path.cwd())
        with self.assertRaisesRegex(CommandError, 'allowlist'):
            runner.run_json([
                'gcloud', 'batch', 'jobs', 'delete', 'job', '--project=project',
                '--format=json'
            ])

    def test_requires_project_and_json_format(self):
        runner = ReadOnlyCommandRunner(Path.cwd())
        with self.assertRaisesRegex(CommandError, 'must specify --project'):
            runner.run_json(
                ['gcloud', 'batch', 'jobs', 'list', '--format=json'])
        with self.assertRaisesRegex(CommandError, 'must specify --format=json'):
            runner.run_json(
                ['gcloud', 'batch', 'jobs', 'list', '--project=project'])

    @mock.patch('subprocess.run')
    def test_runs_without_shell_and_parses_json(self, run_mock):
        run_mock.return_value = subprocess.CompletedProcess([], 0, '[{"x": 1}]',
                                                            '')
        runner = ReadOnlyCommandRunner(Path.cwd())

        result = runner.run_json([
            'gcloud', 'storage', 'objects', 'list', 'gs://bucket/**',
            '--project=project', '--limit=2', '--format=json'
        ])

        self.assertEqual([{'x': 1}], result)
        self.assertNotIn('shell', run_mock.call_args.kwargs)

    @mock.patch('subprocess.run')
    def test_verbose_logs_safe_operation_and_timing(self, run_mock):
        run_mock.return_value = subprocess.CompletedProcess([], 0, '[]', '')
        runner = ReadOnlyCommandRunner(Path.cwd(), verbose=True)
        args = [
            'gcloud', 'logging', 'read',
            'jsonPayload.message="do not log this payload"',
            '--project=project', '--format=json'
        ]

        with self.assertLogs(
                'agents.common.import_support.command_runner') as captured:
            runner.run_json(args)

        logs = '\n'.join(captured.output)
        self.assertIn('Starting gcloud logging read --project=project', logs)
        self.assertIn('Completed gcloud logging read --project=project', logs)
        self.assertIn('elapsed=', logs)
        self.assertNotIn('do not log this payload', logs)

    @mock.patch('agents.common.import_support.command_runner._LOGGER.info')
    @mock.patch('subprocess.run')
    def test_non_verbose_does_not_log_progress(self, run_mock, log_mock):
        run_mock.return_value = subprocess.CompletedProcess([], 0, '[]', '')

        ReadOnlyCommandRunner(Path.cwd()).run_json([
            'gcloud', 'batch', 'jobs', 'list', '--project=project',
            '--format=json'
        ])

        log_mock.assert_not_called()

    def test_redacts_nested_sensitive_fields(self):
        self.assertEqual({
            'api_key': '<redacted>',
            'nested': {
                'value': 1
            }
        }, redact({
            'api_key': 'secret',
            'nested': {
                'value': 1
            }
        }))


if __name__ == '__main__':
    unittest.main()

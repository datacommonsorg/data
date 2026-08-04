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
"""Tests for agent support CLI flag contracts."""

from pathlib import Path
import subprocess
import sys
import unittest

_REPO_ROOT = Path(__file__).parents[3]
_SCRIPT_ROOT = _REPO_ROOT / 'agents/common/import_support'


class CliFlagsTest(unittest.TestCase):

    def _run(self, script_name: str, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable,
             str(_SCRIPT_ROOT / script_name), *args],
            cwd=_REPO_ROOT,
            capture_output=True,
            check=False,
            text=True)

    def test_help_lists_script_flags(self):
        cases = {
            'list_imports.py': ('query', 'autorefresh', 'limit'),
            'list_import_runs.py':
                ('workflow_resource', 'start_time', 'end_time',
                 'absolute_import_name', 'run_limit', 'scan_limit'),
            'correlate_import_runs.py':
                ('mode', 'absolute_import_name', 'spanner_project',
                 'spanner_instance', 'spanner_database', 'gcs_project',
                 'gcs_bucket', 'gcs_output_prefix', 'version', 'limit',
                 'start_time', 'end_time'),
        }

        for script_name, expected_flags in cases.items():
            with self.subTest(script_name=script_name):
                result = self._run(script_name, '--help')
                output = result.stdout + result.stderr
                self.assertNotIn('FATAL Flags parsing error', output)
                for flag_name in expected_flags:
                    self.assertIn(f'--{flag_name}', output)

    def test_accepts_representative_flag_sets_without_running(self):
        cases = {
            'list_imports.py': (
                '--query',
                'UNData',
                '--autorefresh=configured',
                '--limit',
                '5',
            ),
            'list_import_runs.py': (
                '--workflow_resource',
                'projects/p/locations/l/workflows/w',
                '--start_time=2026-01-01T00:00:00Z',
                '--end_time',
                '2026-01-02T00:00:00Z',
                '--absolute_import_name=scripts/a:Import',
                '--run_limit',
                '10',
                '--scan_limit=100',
            ),
            'correlate_import_runs.py': (
                '--mode=import_history',
                '--absolute_import_name',
                'scripts/a:Import',
                '--spanner_project=p',
                '--spanner_instance',
                'i',
                '--spanner_database=d',
                '--gcs_project',
                'p',
                '--gcs_bucket=b',
                '--gcs_output_prefix',
                'imports',
                '--limit=5',
                '--start_time',
                '2026-01-01T00:00:00Z',
                '--end_time=2026-01-02T00:00:00Z',
            ),
        }

        for script_name, args in cases.items():
            with self.subTest(script_name=script_name):
                result = self._run(script_name, *args, '--only_check_args')
                self.assertEqual(0,
                                 result.returncode,
                                 msg=result.stdout + result.stderr)

    def test_rejects_missing_required_flags(self):
        cases = {
            'list_import_runs.py': '--workflow_resource',
            'correlate_import_runs.py': '--mode',
        }

        for script_name, required_flag in cases.items():
            with self.subTest(script_name=script_name):
                result = self._run(script_name, '--only_check_args')
                self.assertNotEqual(0, result.returncode)
                self.assertIn(required_flag, result.stderr)

    def test_rejects_invalid_correlation_mode(self):
        result = self._run(
            'correlate_import_runs.py',
            '--mode=invalid',
            '--absolute_import_name=scripts/a:Import',
            '--spanner_project=p',
            '--spanner_instance=i',
            '--spanner_database=d',
            '--gcs_project=p',
            '--gcs_bucket=b',
            '--only_check_args',
        )

        self.assertNotEqual(0, result.returncode)
        self.assertIn('--mode', result.stderr)


if __name__ == '__main__':
    unittest.main()

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
_SCRIPT_ROOT = _REPO_ROOT / 'agents/common/scripts'


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
        cases = (
            ('list_imports.py', ('query', 'autorefresh', 'limit')),
            ('list_import_summaries.py', ('absolute_import_name', 'gcs_project',
                                          'gcs_bucket', 'limit')),
        )

        for script_name, expected_flags in cases:
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
            'list_import_summaries.py': (
                '--absolute_import_name',
                'scripts/a:Import',
                '--gcs_project',
                'p',
                '--gcs_bucket=b',
                '--limit=5',
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
            'list_import_summaries.py': '--absolute_import_name',
        }

        for script_name, required_flag in cases.items():
            with self.subTest(script_name=script_name):
                result = self._run(script_name, '--only_check_args')
                self.assertNotEqual(0, result.returncode)
                self.assertIn(required_flag, result.stderr)

    def test_rejects_invalid_summary_limit_before_cloud_access(self):
        result = self._run(
            'list_import_summaries.py',
            '--absolute_import_name=scripts/a:Import',
            '--gcs_project=p',
            '--gcs_bucket=b',
            '--limit=6',
        )

        self.assertEqual(2, result.returncode)
        self.assertIn('limit must be between 1 and 5', result.stderr)


if __name__ == '__main__':
    unittest.main()

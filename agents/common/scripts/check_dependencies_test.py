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
"""Tests for the agents-level dependency readiness shell command."""

import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

_REQUIRED_COMMANDS = ('bash', 'curl', 'git', 'jq', 'python3', 'realpath', 'sed')
_EXPECTED_GCLOUD_HELP_CALLS = (
    'artifacts docker images describe --help',
    'auth list --help',
    'auth print-access-token --help',
    'auth application-default print-access-token --help',
    'batch jobs describe --help',
    'batch tasks list --help',
    'logging read --help',
    'scheduler jobs describe --help',
    'spanner databases execute-sql --help',
    'storage cat --help',
    'storage objects list --help',
)
_TOKEN_SECRET = 'secret-token-that-must-not-be-printed'

_GCLOUD_STUB = r'''#!/bin/bash
if [[ -n "${FAKE_GCLOUD_LOG:-}" ]]; then
  printf '%s\n' "$*" >> "${FAKE_GCLOUD_LOG}"
fi

if [[ "$1" == 'version' ]]; then
  printf '%s\n' 'Google Cloud SDK 999.0.0'
  exit 0
fi

if [[ "$*" == *' --help' ]]; then
  if [[ -n "${FAKE_GCLOUD_UNSUPPORTED:-}" && "$*" == "${FAKE_GCLOUD_UNSUPPORTED} --help" ]]; then
    exit 1
  fi
  exit 0
fi

function emit_value {
  case "$1" in
    pass) printf '%s\n' "${2}" ;;
    empty) printf '' ;;
    fail) return 1 ;;
    *) return 2 ;;
  esac
}

if [[ "$1 $2 $3" == 'auth application-default print-access-token' ]]; then
  emit_value "${FAKE_ADC_MODE:-pass}" "${FAKE_TOKEN_SECRET}"
elif [[ "$1 $2" == 'auth print-access-token' ]]; then
  emit_value "${FAKE_CLI_MODE:-pass}" "${FAKE_TOKEN_SECRET}"
elif [[ "$1 $2" == 'auth list' ]]; then
  emit_value "${FAKE_ACTIVE_MODE:-pass}" 'configured-account@example.com'
else
  exit 2
fi
'''


class CheckDependenciesTest(unittest.TestCase):

    def setUp(self):
        self._tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(self._tempdir.cleanup)
        self._workspace = Path(self._tempdir.name)
        self._repo_root = self._workspace / 'data'
        self._repo_root.mkdir()
        for directory in ('statvar_imports', 'scripts', 'import-automation'):
            (self._repo_root / directory).mkdir()
        for filename in ('requirements_all.txt', 'run_tests.sh'):
            (self._repo_root / filename).touch()

        self._python_checker = (self._repo_root / 'agents/common/scripts' /
                                'check_python_dependencies.py')
        self._python_checker.parent.mkdir(parents=True)
        self._python_checker.write_text(
            "print('PASS     Python agent dependencies')\n", encoding='utf-8')

        python_bin = self._repo_root / '.env/bin/python'
        python_bin.parent.mkdir(parents=True)
        python_bin.symlink_to(sys.executable)

        self._bin_dir = self._workspace / 'bin'
        self._bin_dir.mkdir()
        for command in _REQUIRED_COMMANDS:
            executable = shutil.which(command)
            if executable is None:
                self.fail(
                    f'Test host is missing required fixture tool: {command}')
            (self._bin_dir / command).symlink_to(executable)

        gcloud = self._bin_dir / 'gcloud'
        gcloud.write_text(_GCLOUD_STUB, encoding='utf-8')
        gcloud.chmod(0o755)

        self._gcloud_log = self._workspace / 'gcloud.log'
        self._env = os.environ.copy()
        self._env.update({
            'FAKE_GCLOUD_LOG': str(self._gcloud_log),
            'FAKE_TOKEN_SECRET': _TOKEN_SECRET,
            'PATH': str(self._bin_dir),
        })
        self._checker = Path(
            __file__).parents[3] / 'agents/check_dependencies.sh'

    def _run(self, *args, env_updates=None):
        env = self._env.copy()
        if env_updates:
            env.update(env_updates)
        return subprocess.run(
            ['/bin/bash', str(self._checker), *args],
            cwd=self._repo_root,
            capture_output=True,
            check=False,
            env=env,
            text=True)

    def _gcloud_calls(self):
        if not self._gcloud_log.exists():
            return []
        return self._gcloud_log.read_text(encoding='utf-8').splitlines()

    def _assert_token_not_persisted(self):
        for path in self._workspace.rglob('*'):
            if not path.is_file() or path.is_symlink():
                continue
            with self.subTest(path=path):
                self.assertNotIn(_TOKEN_SECRET,
                                 path.read_text(encoding='utf-8'))

    def test_help_and_invalid_arguments(self):
        help_result = self._run('--help')
        self.assertEqual(0, help_result.returncode)
        self.assertIn('[--local|--help]', help_result.stdout)
        self.assertEqual([], self._gcloud_calls())

        for args in (('--auth',), ('--check-auth',), ('unexpected',),
                     ('--local', '--local')):
            with self.subTest(args=args):
                result = self._run(*args)
                self.assertEqual(2, result.returncode)
                self.assertIn('Usage:', result.stderr)

    def test_local_checks_commands_and_skips_authentication(self):
        result = self._run('--local')

        self.assertEqual(0,
                         result.returncode,
                         msg=result.stdout + result.stderr)
        self.assertIn('Google Cloud SDK 999.0.0', result.stdout)
        self.assertIn('Required gcloud commands', result.stdout)
        self.assertIn('SUGGESTED sibling import checkout', result.stdout)
        self.assertIn('Authentication checks (--local)', result.stdout)
        calls = self._gcloud_calls()
        help_calls = tuple(call for call in calls if call.endswith('--help'))
        self.assertEqual(_EXPECTED_GCLOUD_HELP_CALLS, help_calls)
        self.assertFalse(any(
            '--filter=status:ACTIVE' in call for call in calls))

    def test_missing_local_dependency_skips_authentication(self):
        (self._bin_dir / 'jq').unlink()

        result = self._run()

        self.assertEqual(1, result.returncode)
        self.assertIn('MISSING  command jq', result.stderr)
        self.assertIn('NOT_RUN  Authentication checks', result.stderr)
        self.assertFalse(
            any('--filter=status:ACTIVE' in call
                for call in self._gcloud_calls()))

    def test_missing_python_environment_is_reported(self):
        (self._repo_root / '.env/bin/python').unlink()

        result = self._run('--local')

        self.assertEqual(1, result.returncode)
        self.assertIn('MISSING  Python agent environment', result.stderr)
        self.assertIn('./run_tests.sh -r', result.stderr)

    def test_python_dependency_failure_is_reported(self):
        self._python_checker.write_text('raise SystemExit(1)\n',
                                        encoding='utf-8')

        result = self._run('--local')

        self.assertEqual(1, result.returncode)
        self.assertIn('NOT_RUN  Authentication checks', result.stderr)

    def test_unsupported_exact_gcloud_command_is_reported(self):
        result = self._run(
            '--local',
            env_updates={'FAKE_GCLOUD_UNSUPPORTED': 'batch tasks list'})

        self.assertEqual(1, result.returncode)
        self.assertIn('MISSING  gcloud batch tasks list', result.stderr)

    def test_valid_sibling_import_checkout_is_available(self):
        import_repo = self._workspace / 'import'
        workflow = import_repo / 'pipeline/workflow/import-automation-workflow.yaml'
        workflow.parent.mkdir(parents=True)
        workflow.touch()
        subprocess.run(['git', 'init', '-q', str(import_repo)], check=True)

        result = self._run('--local')

        self.assertEqual(0,
                         result.returncode,
                         msg=result.stdout + result.stderr)
        self.assertIn('AVAILABLE sibling import checkout', result.stdout)

    def test_invalid_sibling_import_checkout_is_advisory(self):
        (self._workspace / 'import').mkdir()

        result = self._run('--local')

        self.assertEqual(0,
                         result.returncode,
                         msg=result.stdout + result.stderr)
        self.assertIn('SUGGESTED sibling import checkout', result.stdout)

    def test_default_checks_both_authentication_paths_without_leaking_tokens(
            self):
        result = self._run()

        self.assertEqual(0,
                         result.returncode,
                         msg=result.stdout + result.stderr)
        output = result.stdout + result.stderr
        self.assertIn('PASS     gcloud CLI authentication', output)
        self.assertIn('PASS     Application Default Credentials', output)
        self.assertNotIn(_TOKEN_SECRET, output)
        self._assert_token_not_persisted()
        calls = self._gcloud_calls()
        runtime_calls = [call for call in calls if not call.endswith('--help')]
        self.assertEqual([
            'version',
            'auth list --filter=status:ACTIVE --format=value(account) --quiet',
            'auth print-access-token --quiet',
            'auth application-default print-access-token --quiet',
        ], runtime_calls)

    def test_empty_cli_token_fails_but_adc_is_still_checked(self):
        result = self._run(env_updates={'FAKE_CLI_MODE': 'empty'})

        self.assertEqual(1, result.returncode)
        self.assertIn('FAILED   gcloud CLI authentication', result.stderr)
        self.assertIn('PASS     Application Default Credentials', result.stdout)
        self.assertIn('auth application-default print-access-token --quiet',
                      self._gcloud_calls())

    def test_cli_and_adc_failures_are_independent(self):
        cases = (
            ({
                'FAKE_ACTIVE_MODE': 'empty'
            }, 'No active gcloud account',
             'PASS     Application Default Credentials'),
            ({
                'FAKE_CLI_MODE': 'fail'
            }, 'gcloud CLI authentication',
             'PASS     Application Default Credentials'),
            ({
                'FAKE_ADC_MODE': 'fail'
            }, 'Application Default Credentials',
             'PASS     gcloud CLI authentication'),
        )

        for updates, failure, success in cases:
            with self.subTest(updates=updates):
                self._gcloud_log.unlink(missing_ok=True)
                result = self._run(env_updates=updates)
                self.assertEqual(1, result.returncode)
                self.assertIn(failure, result.stderr)
                self.assertIn(success, result.stdout)


if __name__ == '__main__':
    unittest.main()

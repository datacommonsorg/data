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
"""Tests for the agents-level Python dependency registry."""

from contextlib import redirect_stderr
from contextlib import redirect_stdout
import io
from pathlib import Path
import unittest
from unittest import mock

from agents.common.scripts import check_python_dependencies


class CheckPythonDependenciesTest(unittest.TestCase):

    def test_registered_distributions_match_agent_requirements(self):
        repo_root = Path(__file__).parents[3]
        requirements = {
            line.strip()
            for line in (repo_root / 'agents/requirements.txt').read_text(
                encoding='utf-8').splitlines()
            if line.strip() and not line.lstrip().startswith('#')
        }
        registered = {
            distribution
            for distribution, _ in check_python_dependencies.REQUIRED_MODULES
        }

        self.assertEqual(requirements, registered)

    def test_all_registered_modules_are_checked(self):
        imported = []

        def importer(module):
            imported.append(module)
            return object()

        unavailable = check_python_dependencies.find_unavailable_modules(
            importer)

        self.assertEqual([], unavailable)
        self.assertEqual([
            module for _, module in check_python_dependencies.REQUIRED_MODULES
        ], imported)

    def test_collects_every_unavailable_module(self):
        failures = {
            'OpenSSL': ModuleNotFoundError(),
            'google.auth': RuntimeError(),
        }

        def importer(module):
            if module in failures:
                raise failures[module]
            return object()

        unavailable = check_python_dependencies.find_unavailable_modules(
            importer)

        self.assertEqual([
            ('google-auth', 'google.auth', 'RuntimeError'),
            ('pyopenssl', 'OpenSSL', 'ModuleNotFoundError'),
        ], unavailable)

    def test_main_reports_one_setup_command_for_all_failures(self):
        failures = [
            ('google-auth', 'google.auth', 'ModuleNotFoundError'),
            ('pyopenssl', 'OpenSSL', 'ImportError'),
        ]
        stdout = io.StringIO()
        stderr = io.StringIO()

        with mock.patch.object(check_python_dependencies,
                               'find_unavailable_modules',
                               return_value=failures), redirect_stdout(
                                   stdout), redirect_stderr(stderr):
            result = check_python_dependencies.main(
                ['check_python_dependencies.py'])

        self.assertEqual(1, result)
        self.assertEqual('', stdout.getvalue())
        self.assertIn('google-auth', stderr.getvalue())
        self.assertIn('pyopenssl', stderr.getvalue())
        self.assertEqual(1, stderr.getvalue().count('./run_tests.sh -r'))

    def test_main_rejects_arguments(self):
        stderr = io.StringIO()

        with redirect_stderr(stderr):
            result = check_python_dependencies.main(
                ['check_python_dependencies.py', '--unexpected'])

        self.assertEqual(2, result)
        self.assertIn('Usage:', stderr.getvalue())


if __name__ == '__main__':
    unittest.main()

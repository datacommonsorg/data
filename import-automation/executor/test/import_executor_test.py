
# Copyright 2020 Google LLC
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
"""
Tests for import_executor.py.
"""

import unittest
from unittest import mock
import subprocess
import tempfile
import os
import json

from app.executor import import_executor
from app import configs

class ImportExecutorTest(unittest.TestCase):

    def test_clean_time(self):
        self.assertEqual(
            '2020_07_15T12_07_17_365264_00_00',
            import_executor._clean_time('2020-07-15T12:07:17.365264+00:00'))
        self.assertEqual(
            '2020_07_15T12_07_17_365264_07_00',
            import_executor._clean_time('2020-07-15T12:07:17.365264-07:00'))

    def test_clean_date(self):
        self.assertEqual(
            '2020-07-15',
            import_executor._clean_date('2020-07-15T12:07:17.365264+00:00'))

    def test_run_with_timeout(self):
        self.assertRaises(subprocess.TimeoutExpired,
                          import_executor._run_with_timeout, ['sleep', '5'],
                          0.1)

    def test_create_venv(self):
        with tempfile.NamedTemporaryFile(mode='w+') as requirements:
            requirements.write('beautifulsoup4\nrequests\n')
            requirements.flush()
            with tempfile.TemporaryDirectory() as venv_dir:
                interpreter_path, proc = import_executor._create_venv(
                    (requirements.name,), venv_dir, 20)
                self.assertEqual(0, proc.returncode)
                with tempfile.NamedTemporaryFile(mode='w+') as script:
                    script.write('import bs4\nimport requests\nprint(123)\n')
                    script.flush()
                    proc = subprocess.run([interpreter_path, script.name],
                                          capture_output=True,
                                          text=True,
                                          timeout=2)
                    self.assertEqual(0, proc.returncode)
                    self.assertEqual('123\n', proc.stdout)

    @mock.patch('app.utils.utctime', lambda: '2020-07-28T20:22:18.311294+00:00')
    def test_run_and_handle_exception(self):

        def raise_exception():
            raise Exception

        result = import_executor.run_and_handle_exception(raise_exception)
        self.assertEqual('failed', result.status)
        self.assertEqual([], result.imports_executed)
        self.assertIn('Exception', result.message)
        self.assertIn('Traceback', result.message)

    @mock.patch('app.executor.import_executor._run_user_script')
    def test_import_one_failure(self, mock_run_user_script):
        """Tests that _import_one catches exceptions and returns a failed status."""
        mock_run_user_script.return_value = subprocess.CompletedProcess(
            args=[''], returncode=1, stdout=b'', stderr=b'error message')

        with tempfile.TemporaryDirectory() as repo_dir:
            with self.assertRaises(import_executor.ExecutionError) as context:
                config = configs.ExecutorConfig()
                config.venv_create_timeout = 20
                config.user_script_timeout = 20
                with tempfile.TemporaryDirectory() as mnt_dir:
                    config.gcs_volume_mount_dir = mnt_dir
                    importer = import_executor.ImportExecutor(
                        uploader=mock.MagicMock(),
                        github=mock.MagicMock(),
                        config=config)
                    absolute_import_dir = os.path.join(repo_dir, 'absolute_dir')
                    os.makedirs(absolute_import_dir)
                    importer._import_one(
                        repo_dir=repo_dir,
                        relative_import_dir='relative_dir',
                        absolute_import_dir=absolute_import_dir,
                        import_spec={'import_name': 'import_name',
                                     'curator_emails': [],
                                     'scripts': ['script.py']})
            self.assertEqual('failed', context.exception.result.status)
            self.assertIn('error message', context.exception.result.message)

    def test_import_one_integration_failure(self):
        """Tests that _import_one catches exceptions and returns a failed status."""
        with tempfile.TemporaryDirectory() as repo_dir:
            with self.assertRaises(import_executor.ExecutionError) as context:
                config = configs.ExecutorConfig()
                config.venv_create_timeout = 20
                config.user_script_timeout = 20
                with tempfile.TemporaryDirectory() as mnt_dir:
                    config.gcs_volume_mount_dir = mnt_dir
                    importer = import_executor.ImportExecutor(
                        uploader=mock.MagicMock(),
                        github=mock.MagicMock(),
                        config=config)
                    absolute_import_dir = os.path.join(repo_dir, 'absolute_dir')
                    os.makedirs(absolute_import_dir)
                    with open(os.path.join(absolute_import_dir, 'script.py'), 'w') as f:
                        f.write('import sys\n')
                        f.write('sys.stderr.write("error message")\n')
                        f.write('exit(1)\n')
                    importer._import_one(
                        repo_dir=repo_dir,
                        relative_import_dir='relative_dir',
                        absolute_import_dir=absolute_import_dir,
                        import_spec={'import_name': 'import_name',
                                     'curator_emails': [],
                                     'scripts': ['script.py']})
            self.assertEqual('failed', context.exception.result.status)
            self.assertIn('error message', context.exception.result.message)

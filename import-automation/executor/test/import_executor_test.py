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

from app.executor import import_executor


class ImportExecutorTest(unittest.TestCase):

    def test_clean_time(self):
        self.assertEqual(
            '2020_07_15T12_07_17_365264_00_00',
            import_executor._clean_time('2020-07-15T12:07:17.365264+00:00'))
        self.assertEqual(
            '2020_07_15T12_07_17_365264_07_00',
            import_executor._clean_time('2020-07-15T12:07:17.365264-07:00'))

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

        result = import_executor.run_and_handle_exception(
            'run', raise_exception)
        self.assertEqual('failed', result.status)
        self.assertEqual([], result.imports_executed)
        self.assertIn('Exception', result.message)
        self.assertIn('Traceback', result.message)

    def test_construct_process_message(self):
        process = subprocess.run('printf "out" & >&2 printf "err" & exit 1',
                                 shell=True,
                                 text=True,
                                 capture_output=True)
        message = import_executor._construct_process_message('message', process)
        expected = (
            'message\n'
            '[Subprocess command]: printf "out" & >&2 printf "err" & exit 1\n'
            '[Subprocess return code]: 1\n'
            '[Subprocess stdout]:\n'
            'out\n'
            '[Subprocess stderr]:\n'
            'err')
        self.assertEqual(expected, message)

    def test_construct_process_message_no_output(self):
        """Tests that _construct_process_message does not append
        empty stdout and stderr to the message."""
        process = subprocess.run('exit 0',
                                 shell=True,
                                 text=True,
                                 capture_output=True)
        message = import_executor._construct_process_message('message', process)
        expected = ('message\n'
                    '[Subprocess command]: exit 0\n'
                    '[Subprocess return code]: 0')
        self.assertEqual(expected, message)

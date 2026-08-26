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
import threading

from app.executor import import_executor
from app.executor.import_executor import ImportStatus, ImportStatusSummary
from tools.import_validation.result import ValidationResult, ValidationStatus


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

    def test_run_with_timeout_async_drains_streams_concurrently(self):
        barrier = threading.Barrier(2)

        def stream(line):
            barrier.wait(timeout=5)
            yield line

        process = mock.Mock(returncode=0)
        process.stdout = stream(b'stdout\n')
        process.stderr = stream(b'stderr\n')

        with mock.patch.object(import_executor.subprocess,
                               'Popen',
                               return_value=process):
            result = import_executor._run_with_timeout_async(['command'], 1)

        self.assertEqual(0, result.returncode)
        self.assertEqual(b'stdout\n', result.stdout)
        self.assertEqual(b'stderr\n', result.stderr)
        process.wait.assert_called_once_with()

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
        self.assertEqual(ImportStatus.FAILURE, result.status)
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
            '[Subprocess return code]: 1')
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

    @mock.patch.object(import_executor, 'log_import_status')
    @mock.patch.object(import_executor, 'log_metric')
    @mock.patch.object(import_executor, 'ValidationRunner')
    def test_validation_metrics_include_deleted_percent_for_each_input(
            self, mock_validation_runner, mock_log_metric, _):
        validation_runners = []
        input_statuses = (False, True)
        for input_index, percent in enumerate((10.0, 20.0)):
            rule_id = f'deleted_percent_{input_index}'
            runner = mock.Mock()
            runner.config.rules = [
                {
                    'validator': 'UNKNOWN_VALIDATOR',
                },
                {
                    'rule_id': rule_id,
                    'validator': 'DELETED_RECORDS_PERCENT',
                },
            ]
            input_status = input_statuses[input_index]
            result_status = (ValidationStatus.PASSED
                             if input_status else ValidationStatus.FAILED)
            runner.run_validations.return_value = (input_status, [
                ValidationResult(result_status,
                                 rule_id,
                                 details={
                                     'percent': percent,
                                     'deleted_records_count': input_index + 1,
                                     'previous_obs_count': 10,
                                 })
            ])
            validation_runners.append(runner)
        mock_validation_runner.side_effect = validation_runners

        config = mock.Mock(invoke_differ_tool=True,
                           ignore_validation_status=False,
                           enable_skip_status=True)
        executor = import_executor.ImportExecutor(mock.Mock(), mock.Mock(),
                                                  config)
        executor._get_latest_version = mock.Mock(return_value='previous')
        executor._invoke_differ_summary = mock.Mock(return_value={
            'obs_diff_count': 1,
            'schema_diff_count': 0,
        })
        executor._get_validation_config_file = mock.Mock(
            return_value='validation_config.json')
        executor._upload_file_helper = mock.Mock()
        import_summary = ImportStatusSummary('test_import')

        with tempfile.TemporaryDirectory() as import_dir:
            status = executor._invoke_import_validation(
                'repo', 'relative', import_dir, {
                    'import_name': 'test_import',
                    'import_inputs': [{}, {}],
                }, 'version', import_summary)

        self.assertFalse(status)
        self.assertEqual(2, mock_log_metric.call_count)
        for input_index, call in enumerate(mock_log_metric.call_args_list):
            expected_level = 'INFO' if input_statuses[input_index] else 'ERROR'
            expected_status = ('SUCCESS'
                               if input_statuses[input_index] else 'FAILURE')
            self.assertEqual(expected_level, call.args[1])
            self.assertEqual(f'input{input_index}',
                             call.args[3]['import_input'])
            self.assertEqual(expected_status, call.args[3]['status'])
            self.assertEqual((input_index + 1) * 10.0,
                             call.args[3]['deleted_records_percent'])
            self.assertEqual(input_index + 1,
                             call.args[3]['deleted_records_count'])
            self.assertEqual(10, call.args[3]['previous_obs_count'])

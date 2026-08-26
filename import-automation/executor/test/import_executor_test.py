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
    def test_validation_results_are_added_to_final_import_status(
            self, mock_validation_runner, mock_log_metric,
            mock_log_import_status):
        first_runner = mock.Mock()
        first_runner.run_validations.return_value = (False, [
            ValidationResult(ValidationStatus.FAILED,
                             'check_deleted_records_percent',
                             details={
                                 'percent': 10,
                                 'threshold': 1.5,
                                 'enabled': True,
                                 'note': 'short value',
                                 'long_value': 'x' * 257,
                                 'missing_goldens': ['dcid:example'],
                                 'not_a_number': float('nan'),
                                 'too_large': 10**10000,
                             }),
            ValidationResult(ValidationStatus.PASSED,
                             'check_non_scalar_details',
                             details={'failed_rows': []}),
        ])
        second_runner = mock.Mock()
        second_runner.run_validations.return_value = (True, [
            ValidationResult(ValidationStatus.PASSED,
                             123,
                             details={'missing_refs_count': 2})
        ])
        mock_validation_runner.side_effect = [first_runner, second_runner]

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
        for call in mock_log_metric.call_args_list:
            self.assertEqual(import_executor.AUTO_IMPORT_JOB_STAGE,
                             call.args[0])
            self.assertEqual('ERROR', call.args[1])
            self.assertEqual('Import: test_import, validation: False',
                             call.args[2])
            self.assertEqual({'stage', 'latency', 'status'}, set(call.args[3]))
            self.assertEqual('VALIDATION', call.args[3]['stage'])
            self.assertEqual('FAILURE', call.args[3]['status'])

        self.assertEqual(ImportStatus.FAILURE,
                         mock_log_import_status.call_args.args[2])
        logged_results = mock_log_import_status.call_args.kwargs[
            'validation_results']
        self.assertEqual([
            ('input0', 'check_deleted_records_percent', 'FAILED'),
            ('input0', 'check_non_scalar_details', 'PASSED'),
            ('input1', '123', 'PASSED'),
        ], [(result['input_prefix'], result['rule_id'], result['status'])
            for result in logged_results])
        self.assertEqual([
            {
                'field': 'percent',
                'number_value': 10.0,
            },
            {
                'field': 'threshold',
                'number_value': 1.5,
            },
            {
                'field': 'enabled',
                'bool_value': True,
            },
            {
                'field': 'note',
                'string_value': 'short value',
            },
        ], logged_results[0]['details'])
        self.assertEqual([], logged_results[1]['details'])
        self.assertEqual([{
            'field': 'missing_refs_count',
            'number_value': 2.0,
        }], logged_results[2]['details'])

    @mock.patch.object(import_executor, 'log_import_status')
    @mock.patch.object(import_executor, 'log_metric')
    @mock.patch.object(import_executor, 'ValidationRunner')
    def test_validation_with_no_rules_logs_empty_results(
            self, mock_validation_runner, _, mock_log_import_status):
        mock_validation_runner.return_value.run_validations.return_value = (
            True, [])
        config = mock.Mock(invoke_differ_tool=False,
                           ignore_validation_status=False,
                           enable_skip_status=False)
        executor = import_executor.ImportExecutor(mock.Mock(), mock.Mock(),
                                                  config)
        executor._get_latest_version = mock.Mock(return_value='previous')
        executor._get_validation_config_file = mock.Mock(
            return_value='validation_config.json')
        import_summary = ImportStatusSummary('test_import')

        with tempfile.TemporaryDirectory() as import_dir:
            status = executor._invoke_import_validation(
                'repo', 'relative', import_dir, {
                    'import_name': 'test_import',
                    'import_inputs': [{}],
                }, 'version', import_summary)

        self.assertTrue(status)
        self.assertEqual(ImportStatus.SUCCESS,
                         mock_log_import_status.call_args.args[2])
        self.assertEqual([], mock_log_import_status.call_args.kwargs[
            'validation_results'])

    @mock.patch.object(import_executor, 'log_metric')
    def test_log_import_status_includes_validation_results(
            self, mock_log_metric):
        for validation_results in ([{
                'input_prefix': 'input0',
                'rule_id': 'check_empty_import',
                'status': 'PASSED',
                'details': [],
        }], []):
            with self.subTest(validation_results=validation_results):
                import_executor.log_import_status(
                    'test_import',
                    import_executor.ImportStage.VALIDATION,
                    ImportStatus.SUCCESS,
                    validation_results=validation_results)

                self.assertEqual(
                    validation_results,
                    mock_log_metric.call_args.args[3]['validation_results'])
                self.assertNotIn('validation_results_omitted_count',
                                 mock_log_metric.call_args.args[3])
                mock_log_metric.reset_mock()

    @mock.patch.object(import_executor, 'log_metric')
    def test_log_import_status_omits_oversized_validation_results(
            self, mock_log_metric):
        validation_results = [{
            'input_prefix': 'input0',
            'rule_id': 'check_empty_import',
            'status': 'PASSED',
            'details': [],
        }]

        with mock.patch.object(import_executor,
                               'MAX_VALIDATION_RESULTS_LOG_SIZE_BYTES', 1):
            import_executor.log_import_status(
                'test_import',
                import_executor.ImportStage.VALIDATION,
                ImportStatus.SUCCESS,
                validation_results=validation_results)

        metrics = mock_log_metric.call_args.args[3]
        self.assertEqual([], metrics['validation_results'])
        self.assertEqual(1, metrics['validation_results_omitted_count'])
        self.assertEqual('test_import', metrics['import_name'])
        self.assertEqual('VALIDATION', metrics['stage_name'])
        self.assertEqual('SUCCESS', metrics['status'])

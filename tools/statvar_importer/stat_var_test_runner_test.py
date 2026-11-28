# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the 'License');
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#         https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an 'AS IS' BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Unit tests for stat_var_test_runner.py."""

import ast
import json
import os
import shutil
import sys
import tempfile
import unittest
from unittest import mock

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(_SCRIPT_DIR)
sys.path.append(os.path.dirname(_SCRIPT_DIR))
sys.path.append(os.path.dirname(os.path.dirname(_SCRIPT_DIR)))
sys.path.append(
    os.path.join(os.path.dirname(os.path.dirname(_SCRIPT_DIR)), 'util'))

import stat_var_test_runner


class StatVarTestRunnerTest(unittest.TestCase):

    def setUp(self):
        super().setUp()
        self._temp_dir = tempfile.TemporaryDirectory()
        self._test_dir = self._temp_dir.name

    def tearDown(self):
        self._temp_dir.cleanup()
        super().tearDown()

    def _write_file(self, rel_path: str, content: str) -> str:
        full_path = os.path.join(self._test_dir, rel_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, 'w') as f:
            f.write(content)
        return full_path

    def test_init_with_in_memory_dict_and_list(self):
        cfg = {'test_name': 'single_test'}
        runner_dict = stat_var_test_runner.StatVarProcessorTestRunner(
            test_config=cfg)
        self.assertEqual(runner_dict.get_config(), [cfg])
        self.assertEqual(runner_dict.get_local_dir(), os.getcwd())

        runner_list = stat_var_test_runner.StatVarProcessorTestRunner(
            test_config=[cfg])
        self.assertEqual(runner_list.get_config(), [cfg])

        runner_load = stat_var_test_runner.StatVarProcessorTestRunner()
        runner_load.load_config(cfg)
        self.assertEqual(runner_load.get_config(), [cfg])

    def test_keep_temp_dir_retains_directory(self):
        runner = stat_var_test_runner.StatVarProcessorTestRunner(
            keep_temp_dir=True)
        temp_path = runner._temp_dir_name
        self.assertTrue(os.path.isdir(temp_path))
        del runner
        try:
            self.assertTrue(os.path.isdir(temp_path))
        finally:
            if os.path.isdir(temp_path):
                shutil.rmtree(temp_path)

    def test_diff_files_detects_added_deleted_modified_and_matched(self):
        expected = self._write_file(
            'expected.csv',
            'observationAbout,variableMeasured,observationDate,value\n'
            'country/ARE,Count_Person,2000,100\n',
        )
        actual_same = self._write_file(
            'actual_same.csv',
            'observationAbout,variableMeasured,observationDate,value\n'
            'country/ARE,Count_Person,2000,100\n',
        )
        actual_added = self._write_file(
            'actual_added.csv',
            'observationAbout,variableMeasured,observationDate,value\n'
            'country/ARE,Count_Person,2000,100\n'
            'country/ARE,Count_Person,2001,200\n',
        )
        actual_modified = self._write_file(
            'actual_modified.csv',
            'observationAbout,variableMeasured,observationDate,value\n'
            'country/ARE,Count_Person,2000,999\n',
        )
        actual_deleted = self._write_file(
            'actual_deleted.csv',
            'observationAbout,variableMeasured,observationDate,value\n',
        )

        diff_cfg = {'fingerprint_dcid': 1}
        res_same = stat_var_test_runner.diff_files([actual_same], [expected],
                                                   diff_cfg)
        self.assertEqual(res_same['diff_status'], 'MATCHED')
        self.assertEqual(res_same['added'], 0)
        self.assertEqual(res_same['missing'], 0)
        self.assertEqual(res_same['modified'], 0)

        res_added = stat_var_test_runner.diff_files([actual_added], [expected],
                                                    diff_cfg)
        self.assertEqual(res_added['diff_status'], 'ADDED')
        self.assertEqual(res_added['added'], 1)

        res_mod = stat_var_test_runner.diff_files([actual_modified], [expected],
                                                  diff_cfg)
        self.assertEqual(res_mod['diff_status'], 'MODIFIED')
        self.assertEqual(res_mod['modified'], 1)

        res_del = stat_var_test_runner.diff_files([actual_deleted], [expected],
                                                  diff_cfg)
        self.assertEqual(res_del['diff_status'], 'DELETED')
        self.assertEqual(res_del['missing'], 1)

        actual_added_and_deleted = self._write_file(
            'actual_added_and_deleted.csv',
            'observationAbout,variableMeasured,observationDate,value\n'
            'country/ARE,Count_Person,2005,500\n',
        )
        res_combo = stat_var_test_runner.diff_files([actual_added_and_deleted],
                                                    [expected], diff_cfg)
        self.assertEqual(res_combo['diff_status'], 'ADDED|DELETED')
        self.assertEqual(res_combo['added'], 1)
        self.assertEqual(res_combo['missing'], 1)

    def test_verify_outputs_missing_files_fail_and_use_output_name(self):
        expected = self._write_file(
            'expected.csv',
            'observationAbout,variableMeasured,observationDate,value\n'
            'country/ARE,Count_Person,2000,100\n',
        )
        runner = stat_var_test_runner.StatVarProcessorTestRunner()
        out_dir = os.path.join(self._test_dir, 'out')
        os.makedirs(out_dir, exist_ok=True)

        status_missing_expected = runner.verify_outputs(
            [{
                'output_name':
                    'missing_exp',
                'output_file':
                    'out.csv',
                'expected_output_file':
                    os.path.join(self._test_dir, 'does_not_exist.csv'),
            }],
            {},
            out_dir,
            self._test_dir,
        )
        self.assertEqual(status_missing_expected['status'], 'FAIL')
        self.assertIn('missing_exp', status_missing_expected)
        self.assertEqual(status_missing_expected['missing_exp']['diff_status'],
                         'MISSING_EXPECTED')

        status_missing_actual = runner.verify_outputs(
            [{
                'output_name': 'missing_act',
                'output_file': 'no_such_output.csv',
                'expected_output_file': expected,
            }],
            {},
            out_dir,
            self._test_dir,
        )
        self.assertEqual(status_missing_actual['status'], 'FAIL')
        self.assertIn('missing_act', status_missing_actual)
        self.assertEqual(status_missing_actual['missing_act']['diff_status'],
                         'MISSING_ACTUAL')

    def test_run_statvar_processor_uses_temp_dir_and_no_quotes(self):
        config_path = self._write_file(
            'test_config.json',
            json.dumps([{
                'test_name': 'sample import/v1.0',
                'statvar_processor_args': {
                    'config_file': 'metadata.csv',
                    'input_data': 'test_data/input.csv',
                    'output_path': 'output/sample_output',
                },
            }]),
        )
        runner = stat_var_test_runner.StatVarProcessorTestRunner(
            test_config_file=config_path)

        captured = {}

        def fake_run_script(**kwargs):
            captured.update(kwargs)
            return {'returncode': 0}

        with mock.patch.object(stat_var_test_runner,
                               'run_script',
                               side_effect=fake_run_script):
            status = runner.run_statvar_processor(runner.get_config()[0])

        args = captured['args']
        output_path_args = [a for a in args if a.startswith('--output_path=')]
        counters_args = [a for a in args if a.startswith('--output_counters=')]
        self.assertEqual(len(output_path_args), 1)
        self.assertEqual(len(counters_args), 1)
        self.assertNotIn('"', output_path_args[0])
        self.assertNotIn('"', counters_args[0])
        self.assertTrue(output_path_args[0].startswith(
            f'--output_path={runner._temp_dir_name}'))
        self.assertIn('sample_import_v1_0', status['test_dir'])
        self.assertTrue(counters_args[0].startswith(
            f'--output_counters={runner._temp_dir_name}'))
        self.assertTrue(status['output_dir'].startswith(runner._temp_dir_name))
        self.assertEqual(captured['cwd'], os.path.realpath(self._test_dir))

        # Intermediate files are saved in the temp dir and tests run without
        # API keys by default.
        intermediate_args = [
            a for a in args if a.startswith('--intermediate_dir=')
        ]
        self.assertEqual(len(intermediate_args), 1)
        self.assertTrue(intermediate_args[0].startswith(
            f'--intermediate_dir={runner._temp_dir_name}'))
        self.assertEqual(captured['unset_env'], ['DC_API_KEY', 'MAPS_API_KEY'])

    def test_run_statvar_processor_applies_default_test_configs(self):
        self._write_file(
            'metadata.csv',
            'parameter,value\n'
            'header_rows,1\n'
            'reconcile_nodes,1\n',
        )
        config_path = self._write_file(
            'test_config.json',
            json.dumps([{
                'test_name': 'config_test',
                'statvar_processor_args': {
                    'config_file': 'metadata.csv',
                },
                'statvar_processor_config': {
                    'recon_lookup_api': True,
                },
            }]),
        )
        runner = stat_var_test_runner.StatVarProcessorTestRunner(
            test_config_file=config_path)

        captured = {}

        def fake_run_script(**kwargs):
            captured.update(kwargs)
            return {'returncode': 0}

        with mock.patch.object(stat_var_test_runner,
                               'run_script',
                               side_effect=fake_run_script):
            runner.run_statvar_processor(runner.get_config()[0])

        config_args = [
            a for a in captured['args'] if a.startswith('--config_file=')
        ]
        self.assertEqual(len(config_args), 1)
        config_file = config_args[0].split('=', 1)[1]
        self.assertTrue(config_file.startswith(runner._temp_dir_name))
        with open(config_file) as f:
            processor_config = ast.literal_eval(f.read())
        # Configs from the import's config file are retained.
        self.assertEqual(processor_config['header_rows'], '1')
        # Default configs for tests override the import's config.
        self.assertIs(processor_config['reconcile_nodes'], False)
        self.assertIs(processor_config['resolve_places'], False)
        self.assertIs(processor_config['output_only_new_statvars'], False)
        self.assertIs(processor_config['generate_schema_mcf'], False)
        # Configs in the test override the defaults.
        self.assertIs(processor_config['recon_lookup_api'], True)

    def test_write_processor_config_parses_dict_string(self):
        runner = stat_var_test_runner.StatVarProcessorTestRunner(
            test_config={'test_name': 'dict_config_test'})
        with mock.patch.object(stat_var_test_runner.file_util,
                               'file_get_matching') as mock_matching:
            out_file = runner._write_processor_config(
                " {'header_rows': 2, 'reconcile_nodes': True} ",
                {'reconcile_nodes': False},
                self._test_dir,
            )
            mock_matching.assert_not_called()
        with open(out_file) as f:
            processor_config = ast.literal_eval(f.read())
        self.assertEqual(processor_config['header_rows'], 2)
        self.assertIs(processor_config['reconcile_nodes'], False)

    def test_get_error_counters(self):
        counters_file = self._write_file(
            'counters.csv',
            '"key","value"\n'
            '"1:process_input_error-unresolved-place",3\n'
            '"1:process_input_input-rows-processed",141\n'
            '"2:prepare_output_error-duplicate-statvars",0\n'
            '"error-svobs-missing-property",2\n'
            '"warning-missing-property-key",48792\n'
            '"dropped-svobs-unresolved-place",5\n'
            '"1:process_input_dropped-svobs-unresolved-date",4\n'
            '"dc-api-unresolved-places",7\n',
        )
        self.assertEqual(
            stat_var_test_runner.get_error_counters(counters_file), {
                '1:process_input_error-unresolved-place': 3,
                'error-svobs-missing-property': 2,
                'dropped-svobs-unresolved-place': 5,
            })
        # Expected error counters are ignored.
        self.assertEqual(
            stat_var_test_runner.get_error_counters(
                counters_file,
                ['error-unresolved-place', 'dropped-svobs-unresolved-place']),
            {'error-svobs-missing-property': 2})
        # A counters file that doesn't exist has no error counters.
        self.assertEqual(
            stat_var_test_runner.get_error_counters(
                os.path.join(self._test_dir, 'no_counters.csv')), {})
        # Counters are loaded as csv for other file extensions too.
        counters_txt = self._write_file(
            'counters.txt',
            '"key","value"\n'
            '"error-unresolved-place",1\n',
        )
        self.assertEqual(stat_var_test_runner.get_error_counters(counters_txt),
                         {'error-unresolved-place': 1})

    def test_run_tests_fails_on_error_counters(self):
        test_config = {
            'test_name': 'error_test',
            'statvar_processor_args': {
                'output_path': 'output/res',
            },
        }

        def fake_run_script(**kwargs):
            # Save counters with an error as the statvar processor does.
            counters_arg = [
                a for a in kwargs['args'] if a.startswith('--output_counters=')
            ][0]
            counters_file = counters_arg.split('=', 1)[1]
            os.makedirs(os.path.dirname(counters_file), exist_ok=True)
            with open(counters_file, 'w') as f:
                f.write('"key","value"\n'
                        '"1:process_input_error-unresolved-place",3\n')
            return {'returncode': 0}

        with mock.patch.object(stat_var_test_runner,
                               'run_script',
                               side_effect=fake_run_script):
            runner = stat_var_test_runner.StatVarProcessorTestRunner(
                test_config=dict(test_config))
            result = runner.run_tests()
            self.assertEqual(result['status'], 'FAIL')
            self.assertEqual(result['error_test']['error_counters'],
                             {'1:process_input_error-unresolved-place': 3})

            # The test passes if the error counter is expected.
            test_config['expected_error_counters'] = ['error-unresolved-place']
            runner = stat_var_test_runner.StatVarProcessorTestRunner(
                test_config=dict(test_config))
            result = runner.run_tests()
            self.assertEqual(result['status'], 'PASS')
            self.assertNotIn('error_counters', result['error_test'])

    def test_strip_api_keys_off_keeps_api_keys(self):
        runner = stat_var_test_runner.StatVarProcessorTestRunner(
            test_config={'test_name': 'keys_test'}, strip_api_keys=False)

        captured = {}

        def fake_run_script(**kwargs):
            captured.update(kwargs)
            return {'returncode': 0}

        with mock.patch.object(stat_var_test_runner,
                               'run_script',
                               side_effect=fake_run_script):
            runner.run_statvar_processor(runner.get_config()[0])
        self.assertIsNone(captured['unset_env'])

    def test_run_script_unset_env_removes_variables(self):
        script_path = self._write_file(
            'print_env.py',
            'import os\n'
            'print("DC=" + os.environ.get("DC_API_KEY", "unset"))\n'
            'print("OTHER=" + os.environ.get("OTHER_VAR", "unset"))\n',
        )
        with mock.patch.dict(os.environ, {'DC_API_KEY': 'from_parent'}):
            status = stat_var_test_runner.run_script(
                interpreter='',
                script=script_path,
                args=[],
                cwd=self._test_dir,
                env={
                    'DC_API_KEY': 'from_env_file',
                    'OTHER_VAR': 'kept'
                },
                output_dir=self._test_dir,
                log_dir=os.path.join(self._test_dir, 'env_logs'),
                quiet=True,
                unset_env=['DC_API_KEY'],
            )
        self.assertEqual(status['returncode'], 0)
        with open(status['stdout']) as f:
            output = f.read()
        self.assertIn('DC=unset', output)
        self.assertIn('OTHER=kept', output)

    def test_run_tests_restores_cwd_and_writes_relative_test_output(self):
        expected = self._write_file(
            'test_data/expected.csv',
            'observationAbout,variableMeasured,observationDate,value\n'
            'country/ARE,Count_Person,2000,100\n',
        )
        config_path = self._write_file(
            'test_config.json',
            json.dumps([{
                'test_name':
                    'cwd_test',
                'statvar_processor_args': {
                    'output_path': 'output/res',
                },
                'statvar_processor_outputs': [{
                    'output_name': 'csv_out',
                    'output_file': 'output/res.csv',
                    'expected_output_file': 'test_data/expected.csv',
                    'diff_config': {
                        'fingerprint_dcid': 1
                    },
                }],
            }]),
        )
        caller_dir = os.path.join(self._test_dir, 'caller')
        os.makedirs(caller_dir, exist_ok=True)
        orig_cwd = os.getcwd()
        os.chdir(caller_dir)
        try:
            runner = stat_var_test_runner.StatVarProcessorTestRunner(
                test_config_file=config_path)

            def fake_run_script(**kwargs):
                out_dir = kwargs['output_dir']
                os.makedirs(out_dir, exist_ok=True)
                with open(expected) as src, open(
                        os.path.join(out_dir, 'res.csv'), 'w') as dst:
                    dst.write(src.read())
                return {'returncode': 0}

            with mock.patch.object(stat_var_test_runner,
                                   'run_script',
                                   side_effect=fake_run_script):
                result = runner.run_tests(test_output='summary.json')

            self.assertEqual(result['status'], 'PASS')
            self.assertEqual(os.getcwd(), os.path.realpath(caller_dir))
            # The test summary is saved as JSON relative to the caller's dir.
            with open(os.path.join(caller_dir, 'summary.json')) as f:
                summary = json.load(f)
            self.assertEqual(summary['status'], 'PASS')
            self.assertEqual(
                summary['cwd_test']['output_status']['csv_out']['diff_status'],
                'MATCHED')
        finally:
            os.chdir(orig_cwd)

    def test_run_script_parallel_stdout_stderr_and_interpreter_fallback(self):
        script_path = self._write_file(
            'emit_large.py',
            'import sys\n'
            'sys.stdout.write("O" * 100000 + "\\n")\n'
            'sys.stderr.write("E" * 100000 + "\\n")\n',
        )
        log_dir = os.path.join(self._test_dir, 'logs')
        status = stat_var_test_runner.run_script(
            interpreter='',
            script=script_path,
            args=[],
            cwd=self._test_dir,
            env={},
            output_dir=self._test_dir,
            log_dir=log_dir,
        )
        self.assertEqual(status['returncode'], 0)
        self.assertTrue(os.path.exists(status['stdout']))
        self.assertTrue(os.path.exists(status['stderr']))
        self.assertGreaterEqual(os.path.getsize(status['stdout']), 100000)
        self.assertGreaterEqual(os.path.getsize(status['stderr']), 100000)

    def test_run_script_quiet_mode_hides_script_logs(self):
        script_path = self._write_file(
            'emit_small.py',
            'import sys\nprint("hello_out")\nprint("hello_err", file=sys.stderr)\n',
        )
        log_dir = os.path.join(self._test_dir, 'quiet_logs')
        with mock.patch.object(stat_var_test_runner.logging,
                               'info') as mock_log:
            status = stat_var_test_runner.run_script(
                interpreter='',
                script=script_path,
                args=[],
                cwd=self._test_dir,
                env={},
                output_dir=self._test_dir,
                log_dir=log_dir,
                quiet=True,
            )
        self.assertEqual(status['returncode'], 0)
        logged_msgs = [str(call.args[0]) for call in mock_log.call_args_list]
        self.assertFalse(
            any('hello_out' in m or 'hello_err' in m for m in logged_msgs))
        with open(status['stdout']) as f:
            self.assertIn('hello_out', f.read())
        with open(status['stderr']) as f:
            self.assertIn('hello_err', f.read())

    def test_get_env_dict_supports_env_list_and_dict_files(self):
        env_list = self._write_file(
            'env.list',
            '# comment\n'
            'FOO=bar\n'
            'export BAZ="qux"\n',
        )
        env_json = self._write_file('env.json', '{"JSON_KEY": "json_val"}')
        env_csv = self._write_file('env.csv', 'key,value\nCSV_KEY,csv_val\n')

        self.assertEqual(stat_var_test_runner.get_env_dict(env_list), {
            'FOO': 'bar',
            'BAZ': 'qux'
        })
        self.assertEqual(stat_var_test_runner.get_env_dict(env_json),
                         {'JSON_KEY': 'json_val'})
        self.assertEqual(stat_var_test_runner.get_env_dict(env_csv),
                         {'CSV_KEY': 'csv_val'})


if __name__ == '__main__':
    unittest.main()

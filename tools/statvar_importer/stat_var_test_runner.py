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
"""Utilities to test statvar imports.

StatVar imports use a JSON test config for regression tests that invoke
statvar processor with a specified set of configs on a test input and
verifies the expected output files.
The test config is a file named statvar_test_config.json in the import folder,
or statvar_test_config_<name>.json for an import with more than one.
The test config is a list of statvar processor command line invocation
settings with each invocation as a dictionary with the following sections:
  test_name: name of the test for logs
  env_file: a file with environment variables such as API keys
  statvar_processor_args: dictionary with the command line arguments
    for statvar processor configs.
  statvar_processor_config: (optional) dictionary of statvar processor
    configs for the test, such as 'reconcile_nodes'. Unlike command line
    arguments, these override the configs in the import's config_file. They
    also override the default configs for tests in
    _DEFAULT_TEST_PROCESSOR_CONFIG.
  expected_error_counters: (optional) list of error counters of the statvar
    processor that are expected for the test, such as 'error-unresolved-place'.
    A test fails if the statvar processor has any other error counter.
  expected_outputs:
    A dictionary of expected output files mapped to output files.

  All file references are releative to the import folder with the
  test config.

Example:
[
  # Parameters for a single invocation of statvar processor
  {
    "test_name": "Test_Import",

    # Enviroment file loaded with dictionary of env settings
    # such as API keys
    "env_file": "gs://datcom-prod-imports/config/test_env.csv"

    # Statvar processor command line arguments
    "statvar_processor_args": {
      "config_file": "metadata.csv",
      "pv_map": "import_pvmap.csv",
      "places_resolved_csv": "places.csv",
      "input_data": "test_data/sample_input.csv",
      "existing_statvar_mcf": "gs://datcom-imports-test/Test_Import/statvars.mcf",
    },

    # Statvar processor configs for the test that override the defaults
    "statvar_processor_config": {
      "reconcile_nodes": true,
    },

    # Statvar processor output files with expected outputs to compare with
    "statvar_processor_outputs": [
      {
        "output_name": "Test_Import_Observations",
        "output_file": "<path to output file for a local run>",
        "expected_output_file": "test_data/sample_output.csv",
      },
    ]
  }
]

"""

import ast
import json
import os
import pprint
import re
import subprocess
import sys
import tempfile
import threading
import time

from absl import app
from absl import flags
from absl import logging

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(_SCRIPT_DIR)
sys.path.append(os.path.dirname(_SCRIPT_DIR))
sys.path.append(os.path.dirname(os.path.dirname(_SCRIPT_DIR)))
sys.path.append(
    os.path.join(os.path.dirname(os.path.dirname(_SCRIPT_DIR)), 'util'))

from counters import Counters
import file_util
from mcf_diff import diff_mcf_files
from mcf_file_util import get_value_list

_FLAGS = flags.FLAGS

# Environment variables with API keys removed for the statvar processor.
_API_KEY_ENV_VARS = ['DC_API_KEY', 'MAPS_API_KEY']

# Default statvar processor configs for all tests.
# These turn off lookups in external services, such as the Data Commons API,
# so that tests don't depend on the network or the API quota.
# A test can override these in its 'statvar_processor_config' section.
_DEFAULT_TEST_PROCESSOR_CONFIG = {
    # Don't look up schema in the DC API for reconciliation.
    'recon_lookup_api': False,
    # Don't reconcile generated nodes with the Data Commons schema.
    'reconcile_nodes': False,
    # Don't resolve places with APIs. The statvar processor still resolves
    # places with the test's places_resolved_csv, if any.
    'resolve_places': False,
    # Don't look up generated statvars in the DC API to drop existing ones.
    # The statvar MCF output has all statvars instead of only the new ones.
    'output_only_new_statvars': False,
    # Don't generate the schema MCF, which looks up schema in the DC API.
    'generate_schema_mcf': False,
}


def _define_flags():
    flags.DEFINE_string('test_config', '', 'JSON test config file')
    flags.DEFINE_string('test_output', '', 'Output JSON file with test summary')
    flags.DEFINE_bool(
        'keep_temp_dir',
        False,
        'Retain temp dir after test completes for debugging test failures.',
    )
    flags.DEFINE_bool(
        'quiet',
        False,
        'Quiet mode that hides child script stdout/stderr logs.',
    )
    flags.DEFINE_bool(
        'strip_api_keys',
        True,
        'Remove the API keys from the environment of the statvar processor.'
        ' This does not turn off lookups in APIs, which is done with the'
        ' default statvar processor configs for tests. Without a key, the'
        ' statvar processor skips resolving places with the API.',
    )


class StatVarProcessorTestRunner:
    """Class to run statvar processor for a test config
  """

    def __init__(self,
                 test_config_file: str | dict | list = None,
                 test_config: list | dict = None,
                 keep_temp_dir: bool = False,
                 quiet: bool = False,
                 strip_api_keys: bool = True):
        self._keep_temp_dir = keep_temp_dir
        self._quiet = quiet
        self._strip_api_keys = strip_api_keys
        if self._keep_temp_dir:
            self._temp_dir = None
            self._temp_dir_name = tempfile.mkdtemp(prefix='statvar_test_')
        else:
            self._temp_dir = tempfile.TemporaryDirectory(prefix='statvar_test_')
            self._temp_dir_name = self._temp_dir.name
        self._test_config = []
        self._test_config_file = None
        if test_config:
            self.load_config(test_config)
        self.load_config(test_config_file)

    def load_config(self, test_config_file: str | dict | list):
        """Loads a test config from a JSON file, dict, or list of dicts."""
        if not test_config_file:
            return
        if isinstance(test_config_file, dict):
            self._test_config.append(test_config_file)
        elif isinstance(test_config_file, list):
            self._test_config.extend(test_config_file)
        else:
            file_config = file_util.file_load_py_dict(test_config_file)
            logging.info(f'Loading test config: {file_config}')
            if isinstance(file_config, dict):
                self._test_config.append(file_config)
            elif file_config:
                self._test_config.extend(file_config)
            self._test_config_file = os.path.realpath(test_config_file)

    def get_config(self) -> list:
        """Returns the test config."""
        return self._test_config

    def get_local_dir(self) -> str:
        """Returns the local directory for the test."""
        if self._test_config_file:
            return os.path.dirname(self._test_config_file)
        return os.getcwd()

    def run_tests(self, test_output: str = None) -> dict:
        """Runs all the statvar processor tests and verifies each output.

        Args:
          test_output: JSON file with the test output status

        Returns:
          JSON dict with the test summary
        """
        if test_output and file_util.file_is_local(test_output):
            test_output = os.path.abspath(test_output)
        orig_cwd = os.getcwd()
        cwd = self.get_local_dir()
        os.chdir(cwd)
        try:
            logging.info(
                f'Running statvar processor for {len(self._test_config)} tests from {cwd}'
            )
            return_status = {'status': 'PASS'}
            for index, test_config in enumerate(self._test_config):
                test_name = test_config.get('test_name')
                if not test_name:
                    test_name = f'statvar-processor-test-{index}'
                    basedir = os.path.basename(self.get_local_dir())
                    if basedir:
                        test_name += '-' + basedir
                    test_config['test_name'] = test_name
                logging.info(
                    f'Running statvar processor test: {index}:{test_name}')
                test_status = self.run_statvar_processor(test_config)
                if test_status.get('error_counters'):
                    return_status['status'] = 'FAIL'
                if test_status.get('returncode', 1) != 0:
                    logging.error(
                        f'statvar processor test failed for {test_name}: {test_status}'
                    )
                    return_status['status'] = 'FAIL'
                else:
                    outputs = test_config.get('statvar_processor_outputs')
                    if outputs:
                        output_status = self.verify_outputs(
                            outputs,
                            test_config,
                            test_status.get('output_dir'),
                            test_status.get('test_dir'),
                        )
                        if output_status.get('status', '') != 'PASS':
                            logging.error(
                                f'Failed to verify outputs for test: {index}:{test_name}:{output_status}'
                            )
                            return_status['status'] = 'FAIL'
                        test_status['output_status'] = output_status
                return_status[test_name] = test_status
                logging.info(
                    f'statvar processor test: {index}:{test_name}: {return_status["status"]}'
                )
            if self._keep_temp_dir:
                return_status['temp_dir'] = self._temp_dir_name
                logging.info(
                    f'Retaining temp dir for debugging: {self._temp_dir_name}')
            if test_output:
                with file_util.FileIO(test_output, 'w') as output_file:
                    json.dump(return_status, output_file, indent=2)
            return return_status
        finally:
            os.chdir(orig_cwd)

    def run_statvar_processor(self, config: dict) -> dict:
        """Runs a single instance of statvar processor."""
        test_name = config.get('test_name', 'statvar_processor_test')
        safe_test_name = re.sub(r'[^A-Za-z0-9_-]+', '_', str(test_name))
        test_dir = os.path.join(self._temp_dir_name, safe_test_name)
        output_dir = os.path.join(test_dir, 'output')
        env_dict = get_env_dict(config.get("env_file"))
        # Build the statvar processor commandline
        args_dict = dict(config.get('statvar_processor_args', {}))
        if 'output_path' in args_dict:
            val = str(args_dict['output_path'])
            if file_util.file_is_local(val) and not os.path.isabs(val):
                resolved_output_path = os.path.join(test_dir, val)
            else:
                resolved_output_path = val
            args_dict['output_path'] = resolved_output_path
            if val.endswith('/'):
                output_dir = resolved_output_path
            else:
                output_dir = os.path.dirname(resolved_output_path)
        else:
            args_dict['output_path'] = os.path.join(output_dir, safe_test_name)

        if 'output_counters' in args_dict:
            counters_val = str(args_dict['output_counters'])
            if file_util.file_is_local(
                    counters_val) and not os.path.isabs(counters_val):
                args_dict['output_counters'] = os.path.join(
                    test_dir, counters_val)
        else:
            args_dict['output_counters'] = os.path.join(output_dir,
                                                        'statvar_counters.csv')

        # Save intermediate files such as csv for xls inputs and the http
        # cache in the temp dir instead of the import folder.
        if 'intermediate_dir' in args_dict:
            intermediate_val = str(args_dict['intermediate_dir'])
            if file_util.file_is_local(
                    intermediate_val) and not os.path.isabs(intermediate_val):
                args_dict['intermediate_dir'] = os.path.join(
                    test_dir, intermediate_val)
        else:
            args_dict['intermediate_dir'] = os.path.join(
                test_dir, 'intermediate')

        # Apply the default statvar processor configs for tests and any
        # overrides for the test over the import's config file.
        processor_config = dict(_DEFAULT_TEST_PROCESSOR_CONFIG)
        processor_config.update(config.get('statvar_processor_config', {}))
        if processor_config:
            args_dict['config_file'] = self._write_processor_config(
                args_dict.get('config_file'), processor_config, test_dir)

        cmd_args = [f'--{arg}={val}' for arg, val in args_dict.items()]
        cwd = self.get_local_dir()
        script_status = run_script(
            interpreter=sys.executable,
            script=os.path.join(_SCRIPT_DIR, 'stat_var_processor.py'),
            args=cmd_args,
            cwd=cwd,
            env=env_dict,
            output_dir=output_dir,
            log_dir=os.path.join(output_dir, 'debug'),
            quiet=self._quiet,
            unset_env=_API_KEY_ENV_VARS if self._strip_api_keys else None,
        )
        script_status['output_dir'] = output_dir
        script_status['test_dir'] = test_dir
        # Check for errors counted by the statvar processor, such as
        # 'error-unresolved-place', that don't fail the statvar processor.
        error_counters = get_error_counters(
            args_dict['output_counters'], config.get('expected_error_counters'))
        if error_counters:
            logging.error(
                f'Got error counters for test {test_name}: {error_counters}')
            script_status['error_counters'] = error_counters
        return script_status

    def _write_processor_config(self, config_file: str, test_config: dict,
                                test_dir: str) -> str:
        """Returns a config file with the import's configs and test configs.

        Statvar processor configs such as 'reconcile_nodes' are not command
        line flags and can only be set in the config file. So the configs in
        the import's config file are saved along with the configs for the test
        into a new config file in the test folder.

        Args:
          config_file: config file for the import, relative to the import
            folder, or a dictionary of configs as a string.
          test_config: dictionary of configs for the test that override the
            configs in config_file.
          test_dir: folder for the new config file.

        Returns:
          the new config file with the configs for the test.
        """
        merged_config = {}
        if config_file:
            config_file = str(config_file)
            local_dir = self.get_local_dir()
            config_files = file_util.file_get_matching([
                file if not file_util.file_is_local(file) or os.path.isabs(file)
                else os.path.join(local_dir, file)
                for file in config_file.split(',')
            ])
            if config_files:
                merged_config.update(file_util.file_load_py_dict(config_files))
            else:
                # Config is a dictionary instead of a file.
                try:
                    dict_config = ast.literal_eval(config_file)
                except (SyntaxError, ValueError):
                    dict_config = None
                if isinstance(dict_config, dict):
                    merged_config.update(dict_config)
                else:
                    logging.warning(
                        f'Ignoring config file not found: {config_file}')
        merged_config.update(test_config)
        os.makedirs(test_dir, exist_ok=True)
        test_config_file = os.path.join(test_dir, 'statvar_processor_config.py')
        with file_util.FileIO(test_config_file, 'w') as output_file:
            output_file.write(pprint.pformat(merged_config, indent=4))
        logging.info(
            f'Saved statvar processor configs {config_file} with test configs:'
            f' {test_config} into {test_config_file}')
        return test_config_file

    def verify_outputs(self,
                       outputs: list[dict],
                       config: dict,
                       output_path: str,
                       test_dir: str = None) -> dict:
        """Compare actual and expected outputs.

        Args:
          outputs: list of expected and actual outputs to be compared.
            each item in the list is a dictionary:
            {
              output_name: (optional) name of the output for debug and logs
              output_file: actual output file to be compared.
                this is a local file or path relative to test_dir/output_path
              expected_output_file: path to expected file to be compared with
              diff_config: (optional) dictionary with diff configs such as:
                ignore_property: 'name'
            }

        Returns:
          dictionary with the overall status as well as a list
          of status per output.
          {
            'status': 'PASS' if there are no diffs else 'FAIL'

            # diff summary per output
            '<output_name>': {
              <summary of diffs for output>
              'diff_status': 'MATCHED' or 'ADDED' or 'DELETED' or 'MODIFIED'
              'missing': count of deleted nodes
              'added': count of added nodes
              'modified': count of modified nodes
            },
          }
        """
        logging.info(f'Comparing outputs: {outputs}')
        return_status = {'status': 'PASS'}
        for index, output in enumerate(outputs):
            expected_spec = output.get('expected_output_file')
            expected_files = file_util.file_get_matching(expected_spec)
            output_name = output.get('output_name') or output.get('name')
            if not expected_files:
                output_name = output_name or f'output_{index}'
                logging.error(
                    f'Missing expected output file for {output_name}: {output}')
                return_status['status'] = 'FAIL'
                return_status[output_name] = {
                    'diff_status': 'MISSING_EXPECTED',
                    'expected': expected_spec,
                }
                continue
            if not output_name:
                output_name = (
                    f'output_{index}_{os.path.basename(expected_files[0])}')
            actual_files = output.get('output_file')
            actuals = []
            for file in get_value_list(actual_files):
                matching_files = []
                if file_util.file_is_local(file) and not os.path.isabs(file):
                    search_paths = []
                    if test_dir:
                        search_paths.append(os.path.join(test_dir, file))
                    if output_path:
                        search_paths.append(os.path.join(output_path, file))
                    search_paths.append(file)
                    for candidate in search_paths:
                        matching_files = file_util.file_get_matching(candidate)
                        if matching_files:
                            break
                else:
                    matching_files = file_util.file_get_matching(file)
                if matching_files:
                    actuals.extend(matching_files)
            if not actuals:
                logging.error(
                    f'Missing actual outputs for {output_name}: {output}')
                return_status['status'] = 'FAIL'
                return_status[output_name] = {
                    'diff_status': 'MISSING_ACTUAL',
                    'actual': actual_files,
                    'expected': expected_files,
                }
                continue
            diff_status = diff_files(
                actuals, expected_files, output.get('diff_config'),
                os.path.join(output_path, f'{output_name}.diff'))
            if diff_status.get('diff_status') != 'MATCHED':
                return_status['status'] = 'FAIL'
                logging.error(
                    f'Failed to match {index}:{output}, diff: {diff_status}')
            return_status[output_name] = diff_status
        logging.info(
            f'Verify outputs: {return_status.get("status")} for {outputs}')
        return return_status


def get_error_counters(counters_file: str,
                       expected_counters: list = None) -> dict:
    """Returns the error counters from a statvar processor counters file.

  The statvar processor counts errors, such as 'error-unresolved-place', in
  counters with a name that starts with 'error-' after an optional prefix for
  the processing stage, such as '1:process_input_error-unresolved-place'.

  Args:
    counters_file: csv file with the counters saved by the statvar processor
      with the columns: key, value.
    expected_counters: list of error counters to be ignored, without the
      prefix for the processing stage, such as 'error-unresolved-place'.

  Returns:
    dictionary of error counter name to value for counters with a value
    greater than 0 that are not expected.
  """
    error_counters = {}
    counters_files = file_util.file_get_matching(counters_file)
    if not counters_files:
        # The statvar processor failed before it saved the counters.
        return error_counters
    expected = set(get_value_list(expected_counters or []))
    # The statvar processor saves counters as csv for any file extension,
    # so load the file as csv instead of with file_load_py_dict(), which
    # picks the format by the file extension.
    counters = file_util.file_load_csv_dict(counters_files[0],
                                            key_column='key',
                                            value_column='value')
    for name, counter_value in counters.items():
        error_pos = name.find('error-')
        if error_pos < 0 or (error_pos > 0 and name[error_pos - 1] != '_'):
            continue
        if name[error_pos:] in expected:
            continue
        try:
            value = float(counter_value or 0)
        except ValueError:
            continue
        if value > 0:
            error_counters[name] = value
    return error_counters


def get_env_dict(filename: str) -> dict:
    """Returns a dictionary of env variable settings from a file.

  Args:
    filename: file with the environemnt settings.
      It can be a csv, json, txt or shell file.

  Returns:
    dictionary of env variable to values mappings.
  """
    env_dict = {}
    if isinstance(filename, dict):
        # arguent is a dictionary of env variables. Use it as is.
        return filename

    env_files = file_util.file_get_matching(filename)
    for env_file in env_files:
        _, file_ext = os.path.splitext(env_file)
        file_ext_lower = file_ext.lower()
        if (file_util.file_is_csv(env_file) or
                file_ext_lower in ('.json', '.py', '.pkl')):
            # Load dictionary from CSV, JSON, Python dict, or pickle file.
            env_dict.update(file_util.file_load_py_dict(env_file))
        else:
            # Load line-based env files (.env, .list, env.list, .sh, .txt, etc.)
            with file_util.FileIO(env_file) as fp:
                for line in fp.readlines():
                    line = line.strip()
                    if not line or line.startswith('#'):
                        # Ignore empty and commented lines
                        continue
                    if line.startswith('export '):
                        line = line[len('export '):].strip()
                    if '=' in line:
                        env_var, value = line.split('=', 1)
                        env_var = env_var.strip().strip('"\'')
                        value = value.strip().strip('"\'')
                        env_dict[env_var] = value

    logging.info(f'Loaded {len(env_dict)} env vars from {env_files}')
    return env_dict


def run_script(interpreter: str,
               script: str,
               args: list,
               cwd: str,
               env: dict,
               output_dir: str,
               log_dir: str,
               quiet: bool = False,
               unset_env: list = None) -> dict:
    """Run a commandline script as a child process

        Args:
          interpreter: interpreter for the script such as python, bash
          script: local or full path to the script file.
          args: command line arguments for the script as a list
          cwd: current directory for the script
          env: dictionary of environment variables.
          output_dir: folder for output files generated by the script, if any.
          log_dir: directory to store logs.
          quiet: if True, suppress streaming child stdout/stderr to logging.
          unset_env: list of environment variables removed for the script,
            even if set in env.

        Returns:
          dictionary of command and status
        """
    cmd_args = []
    if not interpreter:
        if script and script.endswith('.py'):
            interpreter = sys.executable
        elif script and script.endswith('.sh'):
            interpreter = 'bash'
    if interpreter:
        cmd_args.append(interpreter)
    if script:
        cmd_args.append(script)
    if args:
        cmd_args.extend(args)

    logging.info(f'Running command: {cmd_args} in {cwd}, env: {env}')
    env_dict = dict(os.environ)
    if env:
        env_dict.update(env)
    for env_var in unset_env or []:
        env_dict.pop(env_var, None)
    if log_dir and file_util.file_is_local(log_dir):
        os.makedirs(log_dir, exist_ok=True)
    start_time = time.perf_counter()
    process = subprocess.Popen(
        cmd_args,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env_dict,
    )

    # Drain stdout and stderr in parallel to prevent pipe deadlocks.
    stderr_file = os.path.join(log_dir, 'stderr.log')
    stdout_file = os.path.join(log_dir, 'stdout.log')

    def drain_stream(stream, log_file, stream_name):
        try:
            with file_util.FileIO(log_file, 'wb') as f_log:
                for line in stream:
                    f_log.write(line)
                    if not quiet:
                        text = line.decode('utf-8', errors='replace')
                        logging.info(f'{stream_name}: {text.rstrip()}')
        finally:
            stream.close()

    stdout_thread = threading.Thread(
        target=drain_stream,
        args=(process.stdout, stdout_file, 'stdout'),
    )
    stderr_thread = threading.Thread(
        target=drain_stream,
        args=(process.stderr, stderr_file, 'stderr'),
    )
    stdout_thread.start()
    stderr_thread.start()

    # Wait for process and log threads to complete.
    process.wait()
    stdout_thread.join()
    stderr_thread.join()
    end_time = time.perf_counter()
    return_code = process.returncode
    duration = end_time - start_time

    logging.info(
        f'Completed command: {cmd_args}, return code: {return_code}, time: {duration} secs, logs in: {log_dir}'
    )

    return {
        'command': ' '.join(cmd_args),
        'cwd': cwd,
        'returncode': return_code,
        'output_path': output_dir,
        'debug': log_dir,
        'duration': duration,
        'stdout': stdout_file,
        'stderr': stderr_file,
    }


def diff_files(actual: str,
               expected: str,
               diff_config: dict = None,
               diff_output_file: str = None) -> dict:
    """Compares actual and expected files and returns dictionary with results.

  Args:
    actual: list of actual files as csv or mcf.
    expected: list of expected output files as csv or mcf
    diff_config: dictionary of diff settings (refer to mcf_diff:diff_mcf_files)
      compare_dcids: list of dcids to be compared
      compare_nodes_with_pv: only compare nodes that have a listed propeorty:value
      ignore_nodes_with_pv: ignore nodes with any of the property:value listed
      compare_property: only compare listed propeorties in a node

  Returns:
      {
        diff_status: MATCHED or ADDED or DELETED or MODIFIED
        diff_output: log file with all the text style diffs with +|- prefixes.
        missing: count of expected nodes missing in actual
        added: count of unexpected nodes in actual not in expected
        modified: count of expected nodes with modified pvs in actual
        diff_sample: a sample of diff output
      }
  """
    if diff_config is None:
        diff_config = {}

    counters = Counters()
    diff_str = diff_mcf_files(actual, expected, diff_config, counters)
    deleted = counters.get_counter('dcid-missing-in-nodes1')
    added = counters.get_counter('dcid-missing-in-nodes2')
    modified = counters.get_counter('nodes-with-diff')
    statuses = []
    if added:
        statuses.append('ADDED')
    if modified:
        statuses.append('MODIFIED')
    if deleted:
        statuses.append('DELETED')
    status = '|'.join(statuses) if statuses else 'MATCHED'
    return_status = {
        'actual': actual,
        'expected': expected,
        'diff_status': status,
        'missing': deleted,
        'added': added,
        'modified': modified,
        'counters': counters.get_counters(),
    }
    logging.info(f'Diff summary: {return_status}')

    if diff_str:
        if diff_output_file:
            with file_util.FileIO(diff_output_file, 'w') as diff_file:
                diff_file.write(diff_str)
            return_status['diff_output'] = diff_output_file
        return_status['diff_sample'] = diff_str[:1000]

    return return_status


def main(_):
    statvar_processor_tester = StatVarProcessorTestRunner(
        test_config_file=_FLAGS.test_config,
        keep_temp_dir=_FLAGS.keep_temp_dir,
        quiet=_FLAGS.quiet,
        strip_api_keys=_FLAGS.strip_api_keys,
    )
    test_result = statvar_processor_tester.run_tests(_FLAGS.test_output)
    logging.info(f'Test result: {test_result}')
    if test_result.get('status') != 'PASS':
        sys.exit(1)


if __name__ == '__main__':
    _define_flags()
    app.run(main)

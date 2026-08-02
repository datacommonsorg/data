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
The test config is a list of statvar processor command line invocation
settings with each invocation as a dictionary with the following sections:a
  test_name: name of the test for logs
  env_file: a file with environment variables such as API keys
  statvar_processor_args: dictionary with the command line arguments
    for statvar processor configs.
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

import os
import sys
import subprocess
import tempfile
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

import file_util
from mcf_diff import diff_mcf_files
from mcf_file_util import get_value_list

from counters import Counters

flags.DEFINE_string('test_config', '', 'JSON test config file')
flags.DEFINE_string('test_output', '', 'Output JSON file with test summary')

_FLAGS = flags.FLAGS

_BASH_PATH = os.environ.get('BASH_PATH', 'bash')


class StatVarProcessorTestRunner:
    """Class to run statvar processor for a test config
  """

    def __init__(self, test_config_file: str = None, test_config: dict = None):
        self._temp_dir = tempfile.TemporaryDirectory()
        self._test_config = []
        if test_config:
            self._test_config.extend(test_config)
        self._env_dict = {}
        self.load_config(test_config_file)
        self._counters = Counters()

    def __del__(self):
        """Cleanup local files."""
        self._temp_dir.cleanup()

    def load_config(self, test_config_file: str):
        """Loads a test config from a JSON file."""
        if test_config_file:
            file_config = file_util.file_load_py_dict(test_config_file)
            logging.info(f'Loading test config: {file_config}')
            self._test_config.extend(file_config)
            self._test_config_file = os.path.realpath(test_config_file)
        self._env_dict.update(
            get_env_dict(self._test_config[0].get('env_file', '')))

    def get_config(self) -> dict:
        """Returns the test config."""
        return self._test_config

    def get_local_dir(self) -> str:
        """Returns the local directory for the test."""
        if self._test_config_file:
            return os.path.dirname(self._test_config_file)
        return os.getcwd()

    def get_env_dict(self) -> dict:
        """Returns the environment variables for the test."""
        return self._env_dict

    def run_tests(self, test_output: str = None) -> dict:
        """Runs all the statvar processor test and verified each output.

        Args:
          test_output: JSON file with the test output status

        Returns:
          JSON dict with the test summary
        """
        cwd = self.get_local_dir()
        os.chdir(cwd)
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
            logging.info(f'Running statvar processor test: {index}:{test_name}')
            test_status = self.run_statvar_processor(test_config)
            if test_status.get('returncode', 1) != 0:
                logging.error(
                    f'statvar processor test failed for {test_name}: {test_status}'
                )
                return_status['status'] = 'FAIL'
            else:
                outputs = test_config.get('statvar_processor_outputs')
                if outputs:
                    output_status = self.verify_outputs(
                        outputs, test_config, test_status.get('output_dir'))
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
        if test_output:
            file_util.file_write_py_dict(return_status, test_output)
        return return_status

    def run_statvar_processor(self,
                              config: dict,
                              override_args: dict = {}) -> dict:
        """Runs a single instance of statvar processor."""
        test_name = config.get('test_name', 'statvar_processor_test')
        test_dir = os.path.join(self._temp_dir.name, test_name)
        output_dir = os.path.join(test_dir, 'output')
        env_dict = dict(self.get_env_dict())
        env_dict.update(get_env_dict(config.get("env_file")))
        # Build the statvar processor commandline
        cmd_args = merge_args([
            {
                '--output_path': '"{output_dir}"',
                '--output_counters': '"{output_dir}/statvar_counters.json"',
            },
            config.get('statvar_processor_args', {}),
            override_args,
        ])
        output_arg = get_arg(cmd_args, '--output_path')
        if output_arg:
            output_dir = os.path.realpath(output_arg)
            if not output_dir.endswith('/'):
                output_dir = os.path.dirname(output_dir)
        cwd = self.get_local_dir()
        script_status = run_script(
            interpreter=sys.executable,
            script=os.path.join(_SCRIPT_DIR, 'stat_var_processor.py'),
            args=cmd_args,
            cwd=cwd,
            env=env_dict,
            output_dir=output_dir,
            log_dir=os.path.join(output_dir, 'debug'),
        )
        script_status['output_dir'] = output_dir
        return script_status

    def verify_outputs(self, outputs: list[dict], config: dict,
                       output_path: dir) -> dict:
        """Compare actual and expected outputs.

        Args:
          outputs: list of expected and actual outputs to be compared.
            each item in the list is a dictionary:
            {
              output_name: (optional) name of the output for debug and logs
              output_file: actual output file to be compared.
                this is a local file or path relative to output_path
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
              'diff_status': 'MATCHED' or 'DELETED' or 'MODIFIED'
              'deleted': count of deleted nodes
              'modified': count of modified nodes
            },
          }
        """
        logging.info(f'Comparing outputs: {outputs}')
        return_status = {'status': 'PASS'}
        for index, output in enumerate(outputs):
            expected_files = file_util.file_get_matching(
                output.get('expected_output_file'))
            if not expected_files:
                logging.warning(
                    f'Ignoring config without expected file: {output}')
                continue
            output_name = output.get('name')
            if not output_name:
                output_name = f'output_{index}_{os.path.basename(expected_files[0])}'
            if output_name in return_status:
                output_name = output_name + '-' + str(index)
            actual_files = output.get('output_file')
            actuals = []
            for file in get_value_list(actual_files):
                matching_files = file_util.file_get_matching(
                    os.path.join(output_path, file))
                if not matching_files:
                    matching_files = file_util.file_get_matching(file)
                if matching_files:
                    actuals.extend(matching_files)
            if not actuals:
                logging.error(f'Missing outputs for {output}')
                return_status['status'] = 'ERROR'
            diff_status = diff_files(
                actuals, expected_files, output.get('diff_config', {}),
                os.path.join(output_path, f'{output_name}.diff'))
            if diff_status.get('diff_status') != 'MATCHED':
                return_status['status'] = 'FAIL'
                logging.error(
                    f'Failed to match {index}:{output}, diff: {diff_status}')
            return_status[output_name] = diff_status
            return_status[output_name]['name'] = output_name
        logging.info(
            f'Verify outputs: {return_status.get("status")} for {outputs}')
        return return_status


def merge_args(self, args: list[dict]) -> dict:
    """Returns a dictionary of command line args from a list of args.

  Args:
    args: list of dictionary of command line argument and valies:
      [
        { 'arg1': 'value1', ...},
        { ...},
        ...
      }

  Returns:
    Dictionary of command line args with the value from the last arg.
  """

    if not isinstance(args, list):
        args = list(args)

    # Merge arguments keeping the last value
    merged_args = dict()
    for args_dict in args:
        for arg, value in args_dict.items():
            if value is not None and not arg.startswith('--'):
                arg = '--' + arg
            merged_args[arg] = value

    return merged_args


def get_args_list(self, args: dict) -> list:
    """Returns a list of command line args."""
    cmd_args = []
    if isinstance(args, dict):
        for arg, val in args.items():
            if val:
                cmd_args.append(f'{arg}={val}')
            else:
                cmd_args.append(f'{arg}')
    elif isinstance(args, list):
        cmd_args.extend(args)
    else:
        cmd_args.append(args)
    return cmd_args


def get_arg(self, args_dict: dict, arg: str, default=None) -> str:
    """Returns the value of a specific arg if present."""
    return args_dict.get(arg, default)


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
        if file_ext == '.sh' or file_ext == ".txt" or file_ext == '.env':
            # File has one variable per line
            with file_util.FileIO(env_file) as fp:
                for line in fp.readlines():
                    line = line.strip()
                    if line.startswith('#'):
                        # Ignore commented lines
                        continue
                    if '=' in line:
                        env_var, value = line.split('=', 1)
                        env_var = env_var.strip().strip('"')
                        value = value.strip().strip('"')
                        env_dict[env_var] = value
        else:
            # Assume the file is a dictionary
            env_dict.update(file_util.file_load_py_dict(env_file))

    logging.info(f'Loaded {len(env_dict)} env vars from {env_files}')
    return env_dict


def run_script(interpreter: str, script: str, args: list | dict, cwd: str,
               env: dict, output_dir: str, log_dir: str) -> dict:
    """Run a commandline script as a child process

        Args:
          interpreter: interpreter for the script such as python, bash
          script: local or full path to the script file.
          args: command line arguments for the script as a list
          cwd: current directory for the script
          env: dictionary of environment variables.
          output_dir: fodler for output files generated by the script, if any.
          log_dir: directory to store logs.

        Returns:
          dictionary of command and status
        """
    cmd_args = []
    if interpreter:
        cmd_args.append(interpreter)
    else:
        if script and script.endswith('.py'):
            # For python scripts use the current script's python binary
            interpreter = sys.executable
        if script and script.endswith('.sh'):
            # For shell scripts use bash
            interpreter = _BASH_PATH
    if script:
        cmd_args.append(script)
    if args:
        cmd_args.extend(get_args_list(args))

    logging.info(f'Running command: {cmd_args} in {cwd}, env: {env}')
    env_dict = dict(os.environ)
    if env:
        env_dict.update(env)
    start_time = time.perf_counter()
    process = subprocess.Popen(
        cmd_args,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env_dict,
    )

    # Log output continuously until the command completes.
    stderr_file = os.path.join(log_dir, 'stderr.log')
    stdout_file = os.path.join(log_dir, 'stdout.log')
    with file_util.FileIO(stderr_file, 'wb') as f_err:
        for line in process.stderr:
            f_err.write(line)
            logging.info(f'stderr: {line}')
    with file_util.FileIO(stdout_file, 'wb') as f_out:
        for line in process.stdout:
            f_out.write(line)
            logging.info(f'stdout: {line}')

    # Wait for process to complete
    process.wait()
    end_time = time.perf_counter()
    return_code = process.returncode
    duration = end_time - start_time

    logging.info(
        f'Completed command: {cmd_args}, return code: {return_code}, time: {duration} secs, logs in: {log_dir}'
    )

    return {
        'command': ' '.join(cmd_args),
        'args': args,
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
               diff_config: dict = {},
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
        status: MATCH or DELETED or MODIFIED
        diff_log: log file with all the text style diffs with +|- prefixes.
        missing: count of expected nodes missing in actual
        modified: count of nodes expected nodes with modified pvs in actual
        sample: a sample of 100 lines of diff output
      }
  """

    counters = Counters()
    diff_str = diff_mcf_files(actual, expected, diff_config, counters)
    matched = counters.get_counter('nodes-matched')
    deleted = counters.get_counter('dcid-missing-in-nodes1')
    added = counters.get_counter('dcid-missing-in-nodes2')
    modified = counters.get_counter('nodes-with-diff')
    status = 'MATCHED'
    if modified:
        status = 'MODIFIED'
    if deleted:
        status = 'DELETED'
    return_status = {
        'actual': actual,
        'expected': expected,
        'diff_status': status,
        'missing': deleted,
        'modified': modified,
        'added': added,
        'matched': matched,
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
        test_config_file=_FLAGS.test_config)
    test_result = statvar_processor_tester.run_tests(_FLAGS.test_output)
    logging.info(f'Test result: {test_result}')


if __name__ == '__main__':
    app.run(main)

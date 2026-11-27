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
"""Regression tests for all statvar imports with a statvar_test_config.json.

Scans the import folders under statvar_imports/ for files named
statvar_test_config.json, or statvar_test_config_<name>.json for an import
with more than one test config, and runs the statvar processor regression
test for each one
with tools/statvar_importer/stat_var_test_runner.py.

Each config is run in its own child process as the test runner changes the
current directory, which is process wide. Child processes run in parallel.
A test also fails if it leaves new files in the import folder.

Environment variables:
  STATVAR_IMPORTS_TEST_WORKERS: number of test configs to run in parallel.
    Defaults to 80% of the CPUs to leave capacity for other processing.
  STATVAR_IMPORTS_TEST_TIMEOUT: seconds to wait for the tests of one config.
    Defaults to 1800.

To run the tests for a single import or a folder of imports:
  python3 statvar_imports/statvar_imports_test.py \
    --test_root=statvar_imports/<import>
"""

import argparse
from concurrent import futures
import fnmatch
import json
import os
import signal
import subprocess
import sys
import tempfile
import unittest

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_DIR = os.path.dirname(_SCRIPT_DIR)
sys.path.append(_SCRIPT_DIR)
sys.path.append(_REPO_DIR)
sys.path.append(os.path.join(_REPO_DIR, 'util'))
sys.path.append(os.path.join(_REPO_DIR, 'tools', 'statvar_importer'))

import stat_var_test_runner

# Test config files such as statvar_test_config.json and
# statvar_test_config_<name>.json.
_TEST_CONFIG_PATTERN = 'statvar_test_config*.json'
_ENV_WORKERS = 'STATVAR_IMPORTS_TEST_WORKERS'
_ENV_TIMEOUT = 'STATVAR_IMPORTS_TEST_TIMEOUT'
# Fraction of CPUs used by default to run tests in parallel.
_DEFAULT_CPU_FRACTION = 0.8
_DEFAULT_TIMEOUT_SECS = 1800
# Number of trailing log lines of a failed test shown in the failure message.
_LOG_TAIL_LINES = 20
_LOG_LINE_CHARS = 300

# Folder scanned for test configs, set with the command line argument
# --test_root. Defaults to the statvar_imports/ folder with this file.
_test_root = None


def _get_env_number(name: str, default: float, number_type=int):
    """Returns the positive number set in the environment variable."""
    value = os.environ.get(name, '').strip()
    if not value:
        return default
    try:
        number = number_type(value)
    except ValueError:
        number = 0
    if number <= 0:
        raise ValueError(f'{name} must be a positive number, got: {value!r}')
    return number


def get_test_root() -> str:
    """Returns the folder to be scanned for test configs."""
    return os.path.abspath(_test_root or _SCRIPT_DIR)


def get_num_workers(num_configs: int) -> int:
    """Returns the number of test configs to run in parallel."""
    default = max(1, int((os.cpu_count() or 1) * _DEFAULT_CPU_FRACTION))
    return max(1, min(num_configs, _get_env_number(_ENV_WORKERS, default)))


def find_test_configs(root_dir: str) -> list[str]:
    """Returns the sorted test config files in all folders under root_dir."""
    configs = []
    for dirpath, dirnames, filenames in os.walk(root_dir):
        # Skip hidden folders such as .env and python caches.
        dirnames[:] = [
            d for d in dirnames if not d.startswith('.') and d != '__pycache__'
        ]
        for filename in fnmatch.filter(filenames, _TEST_CONFIG_PATTERN):
            configs.append(os.path.join(dirpath, filename))
    return sorted(configs)


def _list_files(root_dir: str) -> set[str]:
    """Returns the files in all folders under root_dir, except python caches."""
    files = set()
    for dirpath, dirnames, filenames in os.walk(root_dir):
        dirnames[:] = [d for d in dirnames if d != '__pycache__']
        for filename in filenames:
            files.add(os.path.relpath(os.path.join(dirpath, filename),
                                      root_dir))
    return files


def _kill_process_group(process: subprocess.Popen):
    """Kills the process and the statvar processor it started."""
    if not hasattr(os, 'killpg'):
        # Process groups are not supported on this platform.
        process.kill()
        return
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except (ProcessLookupError, PermissionError):
        process.kill()


def run_test_config(test_config: str, timeout: float = None) -> dict:
    """Runs the tests in a test config in a child process.

    Args:
      test_config: path to the statvar_test_config.json file.
      timeout: seconds to wait for the test to complete.

    Returns:
      dictionary with the test summary from the test runner with the keys:
        status: 'PASS' if all tests in the config passed,
          'FAIL' if a test failed, 'TIMEOUT' if the tests did not complete or
          'ERROR' if the test runner failed without a test summary.
        returncode: exit code of the test runner.
        log: tail of the test runner log if status is not PASS.
        new_files: files left in the import folder by the test, if any.
    """
    import_dir = os.path.dirname(os.path.abspath(test_config))
    files_before = _list_files(import_dir)
    with tempfile.TemporaryDirectory(prefix='statvar_imports_test_') as tmp_dir:
        test_output = os.path.join(tmp_dir, 'test_output.json')
        log_file = os.path.join(tmp_dir, 'test_runner.log')
        command = [
            sys.executable,
            stat_var_test_runner.__file__,
            f'--test_config={test_config}',
            f'--test_output={test_output}',
            '--quiet',
        ]
        timed_out = False
        with open(log_file, 'wb') as log:
            # Run in a new session to kill the test runner along with the
            # statvar processor it started on a timeout.
            process = subprocess.Popen(command,
                                       cwd=_REPO_DIR,
                                       stdin=subprocess.DEVNULL,
                                       stdout=log,
                                       stderr=subprocess.STDOUT,
                                       start_new_session=True)
            try:
                process.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                timed_out = True
                _kill_process_group(process)
                process.wait()
            except BaseException:
                _kill_process_group(process)
                process.wait()
                raise

        result = {}
        if os.path.exists(test_output):
            # The test runner saves the summary as a JSON dictionary.
            try:
                with open(test_output, encoding='utf-8') as output:
                    result = json.load(output)
            except (OSError, ValueError) as e:
                result = {'error': f'Unable to load test summary: {e}'}
        if not isinstance(result, dict):
            result = {'error': f'Unexpected test summary: {result!r}'}
        result['returncode'] = process.returncode
        if timed_out:
            result['status'] = 'TIMEOUT'
            result['error'] = f'Test did not complete in {timeout} secs'
        elif 'status' not in result:
            result['status'] = 'ERROR'
        elif result['status'] == 'PASS' and process.returncode != 0:
            # Test runner exits with a non-zero code for any failure.
            result['status'] = 'ERROR'
        new_files = sorted(_list_files(import_dir) - files_before)
        if new_files:
            # Tests should save all files in a temp folder.
            result['new_files'] = new_files
            if result['status'] == 'PASS':
                result['status'] = 'FAIL'
        if result['status'] != 'PASS':
            with open(log_file, errors='replace') as log:
                lines = log.read().splitlines()
            result['log'] = '\n'.join(
                line[:_LOG_LINE_CHARS] for line in lines[-_LOG_TAIL_LINES:])
        return result


def run_test_configs(test_configs: list[str],
                     num_workers: int = None,
                     timeout: float = None) -> dict:
    """Runs the test configs in parallel.

    Args:
      test_configs: list of statvar_test_config.json files.
      num_workers: number of test configs to run in parallel.
      timeout: seconds to wait for each test config.

    Returns:
      dictionary of test config file to the test summary dictionary
      with the key 'status' set to 'PASS' if all tests in the config passed.
    """
    if not test_configs:
        return {}
    if not num_workers:
        num_workers = get_num_workers(len(test_configs))
    results = {}
    # Threads only wait for child processes that run the tests.
    with futures.ThreadPoolExecutor(max_workers=num_workers) as executor:
        test_futures = {
            executor.submit(run_test_config, config, timeout): config
            for config in test_configs
        }
        for future in futures.as_completed(test_futures):
            config = test_futures[future]
            try:
                results[config] = future.result()
            except Exception as e:
                results[config] = {
                    'status': 'ERROR',
                    'error': f'{type(e).__name__}: {e}'
                }
    return {config: results[config] for config in test_configs}


def get_failure_message(test_config: str, result: dict, root_dir: str) -> str:
    """Returns a message with the status of a failed test config."""
    import_dir = os.path.dirname(test_config)
    if import_dir != root_dir:
        import_dir = os.path.relpath(import_dir, root_dir)
    lines = [
        f'{import_dir}: {result.get("status")}'
        f' (exit code: {result.get("returncode")}, config: {test_config})'
    ]
    if result.get('error'):
        lines.append(f'  error: {result["error"]}')
    if result.get('new_files'):
        lines.append('  new files left in the import folder:'
                     f' {result["new_files"]}')
    for test_name, test_status in result.items():
        if not isinstance(test_status, dict):
            continue
        # Summary of a single statvar processor test in the config.
        lines.append(f'  test: {test_name}:'
                     f' statvar processor exit code:'
                     f' {test_status.get("returncode")}')
        if test_status.get('error_counters'):
            lines.append('    error counters:'
                         f' {test_status["error_counters"]}')
        output_status = test_status.get('output_status', {})
        for output_name, diff in output_status.items():
            if isinstance(diff, dict):
                lines.append(f'    output: {output_name}:'
                             f' {diff.get("diff_status")}')
    if result.get('log'):
        lines.append('  test runner log:')
        lines.extend(f'    {line}' for line in result['log'].splitlines())
    return '\n'.join(lines)


class StatVarImportsTest(unittest.TestCase):

    def test_statvar_imports(self):
        root_dir = get_test_root()
        test_configs = find_test_configs(root_dir)
        if not test_configs:
            self.skipTest(f'No {_TEST_CONFIG_PATTERN} found under {root_dir}')
        timeout = _get_env_number(_ENV_TIMEOUT, _DEFAULT_TIMEOUT_SECS, float)
        results = run_test_configs(test_configs, timeout=timeout)
        failures = [
            get_failure_message(config, result, root_dir)
            for config, result in results.items()
            if result.get('status') != 'PASS'
        ]
        if failures:
            self.fail(f'{len(failures)} of {len(test_configs)} statvar import'
                      f' tests failed under {root_dir}:\n' +
                      '\n'.join(failures))


if __name__ == '__main__':
    _parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    _parser.add_argument(
        '--test_root',
        default='',
        help='Folder to scan for test configs. Defaults to statvar_imports/.')
    _args, _unittest_args = _parser.parse_known_args()
    _test_root = _args.test_root
    unittest.main(argv=[sys.argv[0]] + _unittest_args)

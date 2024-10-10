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
"""Import executor that downloads GitHub repositories and executes data imports

based on manifests.
"""

import dataclasses
import json
import logging
import os
import subprocess
import tempfile
import time
import traceback
from typing import Callable, Dict, Iterable, List, Optional, Tuple

from app import configs
from app import utils
from app.executor import cloud_run_simple_import
from app.executor import import_target
from app.service import email_notifier
from app.service import file_uploader
from app.service import github_api
from app.service import import_service

# Email address for status messages.
_SUCCESS_EMAIL_ADDR = 'datacommons+release@google.com'
_FAILURE_EMAIL_ADDR = 'datacommons-alerts+importautomation@google.com'

_SEE_LOGS_MESSAGE = (
    'Please find logs in the Logs Explorer of the GCP project associated with'
    ' Import Automation.')


@dataclasses.dataclass
class ExecutionResult:
    """Describes the result of the execution of an import."""

    # Status of the execution, one of 'succeeded', 'failed', or 'pass'
    status: str
    # Absolute import names of the imports executed
    imports_executed: List[str]
    # Description of the result
    message: str


class ExecutionError(Exception):
    """Exception to signal that an error has occurred during the execution

  of an import.

  Attributes:
      result: ExecutionResult object describing the result of the execution.
  """

    def __init__(self, execution_result: ExecutionResult):
        super().__init__()
        self.result = execution_result


class ImportExecutor:
    """Import executor that downloads GitHub repositories and executes

  data imports based on manifests.

  Attributes:
      uploader: FileUploader object for uploading the generated data files to
        some place.
      github: GitHubRepoAPI object for communicating with GitHUB API.
      config: ExecutorConfig object containing configurations for the execution.
      notifier: EmailNotifier object for sending notificaiton emails.
      importer: ImportServiceClient object for invoking the Data Commons
        importer.
      local_repo_dir: (Only applies to Updates) The full path to the GitHub
        repository on local. If provided, the local_repo_dir is used for Update
        related operations instead of cloning a fresh version (latest master
        branch) of the repo on GitHub. The path shoud be provided to the root
        directory of the repo, e.g. `<base_path_on_disk>/data`.
  """

    def __init__(
        self,
        uploader: file_uploader.FileUploader,
        github: github_api.GitHubRepoAPI,
        config: configs.ExecutorConfig,
        notifier: email_notifier.EmailNotifier = None,
        importer: import_service.ImportServiceClient = None,
        local_repo_dir: str = '',
    ):
        self.uploader = uploader
        self.github = github
        self.config = config
        self.notifier = notifier
        self.importer = importer
        self.local_repo_dir: str = local_repo_dir

    def execute_imports_on_commit(self, commit_sha: str) -> ExecutionResult:
        """Executes imports upon a GitHub commit.

    Args:
        commit_sha: ID of the commit as a string.

    Returns:
        ExecutionResult object describing the results of the imports.
    """
        return run_and_handle_exception(
            self._execute_imports_on_commit_helper,
            commit_sha,
        )

    def execute_imports_on_update(self,
                                  absolute_import_name: str) -> ExecutionResult:
        """Executes imports upon a scheduled update.

    Args:
        absolute_import_name: Absolute import name of the imports to execute of
          the form <path to dir with manifest>:<import name> as a string. E.g.,
          scripts/us_fed/treasury:USFed_MaturityRates. <import name> can be
          'all' to execute all imports within the directory.

    Returns:
        ExecutionResult object describing the results of the imports.
    """
        return run_and_handle_exception(
            self._execute_imports_on_update_helper,
            absolute_import_name,
        )

    def _execute_imports_on_update_helper(
            self, absolute_import_name: str) -> ExecutionResult:
        """Helper for execute_imports_on_update.

    Args:
        absolute_import_name: See execute_imports_on_update.

    Returns:
        ExecutionResult object describing the results of the executions.

    Raises:
        ExecutionError: The execution of an import failed for any reason.
    """
        logging.info('%s: BEGIN', absolute_import_name)
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_dir = ''
            if self.local_repo_dir:
                # Do not clone/download from GitHub. Instead, use the
                # provided local path to the repo's root directory.
                logging.info(
                    '%s: using local repo at: %s',
                    absolute_import_name,
                    self.local_repo_dir,
                )
                repo_dir = self.local_repo_dir
            else:
                # Clone/download from GitHub.
                logging.info('%s: downloading repo', absolute_import_name)
                repo_dir = self.github.download_repo(
                    tmpdir, timeout=self.config.repo_download_timeout)
                logging.info('%s: downloaded repo %s', absolute_import_name,
                             repo_dir)

            executed_imports = []

            # An example import_dir is 'scripts/us_fed/treasury'
            import_dir, import_name = import_target.split_absolute_import_name(
                absolute_import_name)
            absolute_import_dir = os.path.join(repo_dir, import_dir)
            manifest_path = os.path.join(absolute_import_dir,
                                         self.config.manifest_filename)
            manifest = parse_manifest(manifest_path)
            logging.info('%s: loaded manifest %s', absolute_import_name,
                         manifest_path)

            for spec in manifest['import_specifications']:
                import_name_in_spec = spec['import_name']
                if import_name in ('all', import_name_in_spec):
                    try:
                        self._import_one(
                            repo_dir=repo_dir,
                            relative_import_dir=import_dir,
                            absolute_import_dir=absolute_import_dir,
                            import_spec=spec,
                        )
                    except Exception:
                        raise ExecutionError(
                            ExecutionResult('failed', executed_imports,
                                            traceback.format_exc()))
                    executed_imports.append(
                        import_target.get_absolute_import_name(
                            import_dir, import_name_in_spec))

        logging.info('%s: END', absolute_import_name)
        return ExecutionResult('succeeded', executed_imports, 'No issues')

    def _execute_imports_on_commit_helper(
        self,
        commit_sha: str,
    ) -> ExecutionResult:
        """Helper for execute_imports_on_commit.

    Args: See execute_imports_on_commit.

    Returns:
        ExecutionResult object describing the results of the executions.

    Raises:
        ExecutionError: The execution of an import failed for any reason.
    """

        # Import targets specified in the commit message,
        # e.g., 'scripts/us_fed/treasury:constant_maturity', 'constant_maturity'
        targets = import_target.find_targets_in_commit(commit_sha, 'IMPORTS',
                                                       self.github)
        if not targets:
            return ExecutionResult(
                'pass', [], 'No import target specified in commit message')
        # Relative paths to directories having files changed by the commit
        # containing manifests, e.g. 'scripts/us_fed/treasury'.
        manifest_dirs = self.github.find_dirs_in_commit_containing_file(
            commit_sha, self.config.manifest_filename)

        with tempfile.TemporaryDirectory() as tmpdir:
            repo_dir = self.github.download_repo(
                tmpdir, commit_sha, self.config.repo_download_timeout)

            logging.info(f'Downloaded repo: {repo_dir}')

            imports_to_execute = import_target.find_imports_to_execute(
                targets=targets,
                manifest_dirs=manifest_dirs,
                manifest_filename=self.config.manifest_filename,
                repo_dir=repo_dir,
            )

            executed_imports = []
            for relative_dir, spec in imports_to_execute:
                try:
                    self._import_one(
                        repo_dir=repo_dir,
                        relative_import_dir=relative_dir,
                        absolute_import_dir=os.path.join(
                            repo_dir, relative_dir),
                        import_spec=spec,
                    )

                except Exception:
                    raise ExecutionError(
                        ExecutionResult('failed', executed_imports,
                                        traceback.format_exc()))
                absolute_name = import_target.get_absolute_import_name(
                    relative_dir, spec['import_name'])
                executed_imports.append(absolute_name)

            return ExecutionResult('succeeded', executed_imports, 'No issues')

    def _import_one(
        self,
        repo_dir: str,
        relative_import_dir: str,
        absolute_import_dir: str,
        import_spec: dict,
    ) -> None:
        """Executes an import.

    Args:
        repo_dir: Absolute path to the repository, as a string.
        relative_import_dir: Path to the directory containing the manifest as a
          string, relative to the root directory of the repository.
        absolute_import_dir: Absolute path to the directory containing the
          manifest as a string.
        import_spec: Specification of the import as a dict.
    """
        import_name = import_spec['import_name']
        absolute_import_name = import_target.get_absolute_import_name(
            relative_import_dir, import_name)
        time_start = time.time()
        try:
            self._import_one_helper(
                repo_dir=repo_dir,
                relative_import_dir=relative_import_dir,
                absolute_import_dir=absolute_import_dir,
                import_spec=import_spec,
            )
            time_taken = '{0:.2f}'.format(time.time() - time_start)
            if self.notifier:
                msg = f'Successful Import: {import_name} ({absolute_import_name})\nn'
                msg += f'Script execution time taken = {time_taken}s'
                self.notifier.send(
                    subject=f'Import Automation Success - {import_name}',
                    body=msg,
                    receiver_addresses=[_SUCCESS_EMAIL_ADDR],
                )

        except Exception as exc:
            if self.notifier:
                msg = f'Failed Import: {import_name} ({absolute_import_name})\n\n'
                msg += f'{_SEE_LOGS_MESSAGE}\n\n'
                msg += f'Stack Trace: \n'
                msg += f'{exc}'
                self.notifier.send(
                    subject=f'Import Automation Failure - {import_name}',
                    body=msg,
                    receiver_addresses=[_FAILURE_EMAIL_ADDR],
                )
            raise exc

    def _import_one_helper(
        self,
        repo_dir: str,
        relative_import_dir: str,
        absolute_import_dir: str,
        import_spec: dict,
    ) -> None:
        """Helper for _import_one.

    Args: See _import_one.
    """
        urls = import_spec.get('data_download_url')
        if urls:
            for url in urls:
                utils.download_file(url, absolute_import_dir,
                                    self.config.file_download_timeout)

        version = _clean_time(utils.pacific_time())
        with tempfile.TemporaryDirectory() as tmpdir:
            requirements_path = os.path.join(absolute_import_dir,
                                             self.config.requirements_filename)
            central_requirements_path = os.path.join(
                repo_dir, self.config.requirements_filename)
            interpreter_path, process = _create_venv(
                (central_requirements_path, requirements_path),
                tmpdir,
                timeout=self.config.venv_create_timeout,
            )

            _log_process(process=process)
            process.check_returncode()

            script_paths = import_spec.get('scripts')
            for path in script_paths:
                script_path = os.path.join(absolute_import_dir, path)
                simple_job = cloud_run_simple_import.get_simple_import_job_id(
                    import_spec, script_path)
                if simple_job:
                    # Running simple import as cloud run job.
                    cloud_run_simple_import.cloud_run_simple_import_job(
                        import_spec=import_spec,
                        config_file=script_path,
                        env=self.config.user_script_env,
                        version=version,
                        image=import_spec.get('image'),
                    )
                else:
                    # Run import script locally.
                    process = _run_user_script(
                        interpreter_path=interpreter_path,
                        script_path=script_path,
                        timeout=self.config.user_script_timeout,
                        args=self.config.user_script_args,
                        cwd=absolute_import_dir,
                        env=self.config.user_script_env,
                    )
                    _log_process(process=process)
                    process.check_returncode()

        inputs = self._upload_import_inputs(
            import_dir=absolute_import_dir,
            output_dir=f'{relative_import_dir}/{import_spec["import_name"]}',
            version=version,
            import_inputs=import_spec.get('import_inputs', []),
        )

        if self.importer:
            self.importer.delete_previous_output(relative_import_dir,
                                                 import_spec)
            try:
                self.importer.delete_import(
                    relative_import_dir,
                    import_spec,
                    block=True,
                    timeout=self.config.importer_delete_timeout,
                )
            except import_service.ImportNotFoundError as exc:
                # If this is the first time executing this import,
                # there will be no previous import
                logging.warning(str(exc))

            self.importer.smart_import(
                relative_import_dir,
                inputs,
                import_spec,
                block=True,
                timeout=self.config.importer_import_timeout,
            )

    def _upload_import_inputs(
        self,
        import_dir: str,
        output_dir: str,
        version: str,
        import_inputs: List[Dict[str, str]],
    ) -> import_service.ImportInputs:
        """Uploads the generated import data files.

    Data files are uploaded to <output_dir>/<version>/, where <version> is a
    time string and is written to <output_dir>/<storage_version_filename>
    after the uploads are complete.

    Args:
        import_dir: Absolute path to the directory with the manifest, as a
          string.
        output_dir: Path to the output directory, as a string.
        import_inputs: List of import inputs each as a dict mapping import types
          to relative paths within the repository. This is parsed from the
          'import_inputs' field in the manifest.

    Returns:
        ImportInputs object containing the paths to the uploaded inputs.
    """
        uploaded = import_service.ImportInputs()
        for import_input in import_inputs:
            for input_type in self.config.import_input_types:
                path = import_input.get(input_type)
                if path:
                    dest = f'{output_dir}/{version}/{os.path.basename(path)}'
                    self._upload_file_helper(
                        src=os.path.join(import_dir, path),
                        dest=dest,
                    )
                    setattr(uploaded, input_type, dest)
        self.uploader.upload_string(
            version,
            os.path.join(output_dir, self.config.storage_version_filename))
        return uploaded

    def _upload_file_helper(self, src: str, dest: str) -> None:
        """Uploads a file from src to dest.

    Args:
        src: Path to the file to upload, as a string.
        dest: Path to where the file is to be uploaded to, as a string.
    """
        self.uploader.upload_file(src, dest)


def parse_manifest(path: str) -> dict:
    """Parses the import manifest.

  Args:
      path: Path to the import manifest file as a string.

  Returns:
      The parsed manifest as a dict.

  Raises:
      Same exceptions as open and json.load if the file does not exist or
      contains malformed json.
  """
    with open(path) as file:
        return json.load(file)


def run_and_handle_exception(
    exec_func: Callable,
    *args,
) -> ExecutionResult:
    """Runs a method that executes imports and handles its exceptions.

  Args:
      exec_func: The method to execute.
      args: List of arguments sent to exec_func.

  Returns:
      ExecutionResult object describing the results of the imports.
  """
    try:
        return exec_func(*args)
    except ExecutionError as exc:
        logging.exception('ExecutionError was thrown')
        result = exc.result
        return result
    except Exception:
        logging.exception('An unexpected exception was thrown')
        message = traceback.format_exc()
        return ExecutionResult('failed', [], message)


def _run_with_timeout_async(args: List[str],
                            timeout: float,
                            cwd: str = None,
                            env: dict = None) -> subprocess.CompletedProcess:
    """Runs a command in a subprocess asynchronously and emits the stdout/stderr.

  Args:
      args: Command to run as a list. Each element is a string.
      timeout: Maximum time the command can run for in seconds as a float.
      cwd: Current working directory of the process as a string.

  Returns:
      subprocess.CompletedProcess object used to run the command.

  Raises:
      Same exceptions as subprocess.run.
  """
    try:
        logging.info(
            f'Launching async command: {args} with timeout {timeout} in {cwd}, env:'
            f' {env}')
        start_time = time.time()
        stdout = []
        stderr = []
        process = subprocess.Popen(
            args,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
        )

        # Log output continuously until the command completes.
        for line in process.stderr:
            stderr.append(line)
            logging.info(f'Process stderr: {line}')
        for line in process.stdout:
            stdout.append(line)
            logging.info(f'Process stdout: {line}')

        end_time = time.time()

        return_code = process.returncode
        end_msg = (
            f'Completed script: "{args}", Return code: {return_code}, time:'
            f' {end_time - start_time:.3f} secs.\n')
        logging.info(end_msg)
        return subprocess.CompletedProcess(
            args=args,
            returncode=return_code,
            stdout=b''.join(stdout),
            stderr=b''.join(stderr),
        )
    except Exception as e:
        message = traceback.format_exc()
        logging.exception(
            f'An unexpected exception was thrown: {e} when running {args}:'
            f' {message}')
        return subprocess.CompletedProcess(
            args=args,
            returncode=1,
            stdout=b''.join(stdout),
            stderr=b''.join(stderr),
        )


def _run_with_timeout(args: List[str],
                      timeout: float,
                      cwd: str = None,
                      env: dict = None) -> subprocess.CompletedProcess:
    """Runs a command in a subprocess.

  Args:
      args: Command to run as a list. Each element is a string.
      timeout: Maximum time the command can run for in seconds as a float.
      cwd: Current working directory of the process as a string.
      env: Dict of environment variables for the command.

  Returns:
      subprocess.CompletedProcess object used to run the command.

  Raises:
      Same exceptions as subprocess.run.
  """
    try:
        logging.info(
            f'Running command: {args} with timeout {timeout} in dir:{cwd} with'
            f' Env:{env}')
        process = subprocess.run(args,
                                 capture_output=True,
                                 text=True,
                                 timeout=timeout,
                                 cwd=cwd,
                                 env=env)
        logging.info(
            f'Completed command: {args}, retcode: {process.returncode}, stdout:'
            f' {process.stdout}, stderr: {process.stderr}')
        return process
    except Exception as e:
        message = traceback.format_exc()
        logging.exception(
            f'An unexpected exception was thrown: {e} when running {args}:'
            f' {message}')
        return None


def _create_venv(requirements_path: Iterable[str], venv_dir: str,
                 timeout: float) -> Tuple[str, subprocess.CompletedProcess]:
    """Creates a Python virtual environment.

  The virtual environment is created with --system-site-packages set,
  which allows it to access modules installed on the host. This provides
  the opportunity to use the requirements.txt file for this project as
  a central requirement file for all user scripts.

  Args:
      requirements_path: List of paths to pip requirement files listing the
        dependencies to install, each as a string.
      venv_dir: Path to the directory to create the virtual environment in as a
        string.
      timeout: Maximum time the creation script can run for in seconds as a
        float.

  Returns:
      A tuple consisting of the path to the created interpreter as a string
      and a subprocess.CompletedProcess object used to create the environment.

  Raises:
      Same exceptions as subprocess.run.
  """
    with tempfile.NamedTemporaryFile(mode='w', suffix='.sh') as script:
        script.write(f'python3 -m venv --system-site-packages {venv_dir}\n')
        script.write(f'. {venv_dir}/bin/activate\n')
        for path in requirements_path:
            if os.path.exists(path):
                script.write(
                    f'python3 -m pip install --no-cache-dir --requirement {path}\n'
                )
        script.flush()

        process = _run_with_timeout(['bash', script.name], timeout)
        return os.path.join(venv_dir, 'bin/python3'), process


def _run_user_script(
    interpreter_path: str,
    script_path: str,
    timeout: float,
    args: list = None,
    cwd: str = None,
    env: dict = None,
) -> subprocess.CompletedProcess:
    """Runs a user Python script.

  Args:
      script_path: Path to the user script to run as a string.
      interpreter_path: Path to the Python interpreter to run the user script as
        a string.
      timeout: Maximum time the user script can run for in seconds as a float.
      args: A list of arguments each as a string to pass to the user script on
        the command line.
      cwd: Current working directory of the process as a string.
      env: Dict of environment variables for the user script run.

  Returns:
      subprocess.CompletedProcess object used to run the script.

  Raises:
      subprocess.TimeoutExpired: The user script did not finish
          within timeout.
  """
    script_args = [interpreter_path]
    script_args.extend(script_path.split(' '))
    if args:
        script_args.extend(args)
    return _run_with_timeout_async(script_args, timeout, cwd, env)


def _clean_time(
    time: str, chars_to_replace: Tuple[str] = (':', '-', '.', '+')) -> str:
    """Replaces some characters with underscores.

  Args:
      time: Time string.
      chars_to_replace: List of characters to replace with underscores.

  Returns:
      Time string with the characters replaced.
  """
    for char in chars_to_replace:
        time = time.replace(char, '_')
    return time


def _construct_process_message(message: str,
                               process: subprocess.CompletedProcess) -> str:
    """Constructs a log message describing the result of a subprocess.

  Args:
      message: Brief log message as a string.
      process: subprocess.CompletedProcess object whose arguments, return code,
        stdout, and stderr are to be added to the message.
  """
    command = process.args
    if isinstance(command, list):
        command = utils.list_to_str(command, ' ')
    message = (f'{message}\n'
               f'[Subprocess command]: {command}\n'
               f'[Subprocess return code]: {process.returncode}')
    if process.stdout:
        message += f'\n[Subprocess stdout]:\n{process.stdout}'
    if process.stderr:
        message += f'\n[Subprocess stderr]:\n{process.stderr}'
    return message


def _log_process(process: subprocess.CompletedProcess,) -> None:
    """Logs the result of a subprocess.

  Args:
      process: subprocess.CompletedProcess object whose arguments, return code,
        stdout, and stderr are to be logged.
  """
    message = 'Subprocess succeeded'
    if process.returncode:
        message = 'Subprocess failed'
    message = _construct_process_message(message, process)
    logging.info(message)

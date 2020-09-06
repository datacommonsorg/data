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
Import executor that downloads GitHub repositories and executes data imports
based on manifests.
"""

import json
import os
import subprocess
import tempfile
import logging
import traceback
from typing import Tuple, List, Dict, Optional, Callable, Iterable
import dataclasses

from app import utils
from app import configs
from app.service import dashboard_api
from app.executor import import_target
from app.service import github_api
from app.service import file_uploader
from app.service import email_notifier
from app.service import import_service

_SYSTEM_RUN_INIT_FAILED_MESSAGE = ('Failed to initialize the system run '
                                   'with the import progress dashboard')

_SEE_DASHBOARD_MESSAGE = (
    'See dashboard for logs: '
    'https://dashboard-frontend-dot-datcom-data.uc.r.appspot.com/')


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
        result: ExecutionResult object describing the result
            of the execution.
    """

    def __init__(self, execution_result: ExecutionResult):
        super().__init__()
        self.result = execution_result


class ImportExecutor:
    """Import executor that downloads GitHub repositories and executes
    data imports based on manifests.

    Attributes:
        uploader: FileUploader object for uploading the generated data files
            to some place.
        github: GitHubRepoAPI object for communicating with GitHUB API.
        config: ExecutorConfig object containing configurations
            for the execution.
        dashboard: DashboardAPI object for communicating with the
            import progress dashboard. If not provided, the executor will not
            communicate with the dashboard.
        notifier: EmailNotifier object for sending notificaiton emails.
        importer: ImportServiceClient object for invoking the
            Data Commons importer.
    """

    def __init__(self,
                 uploader: file_uploader.FileUploader,
                 github: github_api.GitHubRepoAPI,
                 config: configs.ExecutorConfig,
                 dashboard: dashboard_api.DashboardAPI = None,
                 notifier: email_notifier.EmailNotifier = None,
                 importer: 'import_service.ImportServiceClient' = None):
        self.uploader = uploader
        self.github = github
        self.config = config
        self.dashboard = dashboard
        self.notifier = notifier
        self.importer = importer

    def execute_imports_on_commit(self,
                                  commit_sha: str,
                                  repo_name: str = None,
                                  branch_name: str = None,
                                  pr_number: str = None) -> ExecutionResult:
        """Executes imports upon a GitHub commit.

        repo_name, branch_name, and pr_number are used only for logging to
        the import progress dashboard.

        Args:
            commit_sha: ID of the commit as a string.
            repo_name: Name of the repository the commit is for as a string.
            branch_name: Name of the branch the commit is for as a string.
            pr_number: If the commit is a part of a pull request, the number of
                the pull request as an int.
        Returns:
            ExecutionResult object describing the results of the imports.
        """
        run_id = None
        try:
            if self.dashboard:
                run_id = _init_run_helper(dashboard=self.dashboard,
                                          commit_sha=commit_sha,
                                          repo_name=repo_name,
                                          branch_name=branch_name,
                                          pr_number=pr_number)['run_id']
        except Exception:
            logging.exception(_SYSTEM_RUN_INIT_FAILED_MESSAGE)
            return _create_system_run_init_failed_result(traceback.format_exc())

        return run_and_handle_exception(run_id, self.dashboard,
                                        self._execute_imports_on_commit_helper,
                                        commit_sha, run_id)

    def execute_imports_on_update(self,
                                  absolute_import_name: str) -> ExecutionResult:
        """Executes imports upon a scheduled update.

        Args:
            absolute_import_name: Absolute import name of the imports to
                execute of the form <path to dir with manifest>:<import name>
                as a string. E.g., scripts/us_fed/treasury:USFed_MaturityRates.
                <import name> can be 'all' to execute all imports within
                the directory.

        Returns:
            ExecutionResult object describing the results of the imports.
        """
        run_id = None
        try:
            if self.dashboard:
                run_id = _init_run_helper(self.dashboard)['run_id']
        except Exception:
            logging.exception(_SYSTEM_RUN_INIT_FAILED_MESSAGE)
            return _create_system_run_init_failed_result(traceback.format_exc())

        return run_and_handle_exception(run_id, self.dashboard,
                                        self._execute_imports_on_update_helper,
                                        absolute_import_name, run_id)

    def _execute_imports_on_update_helper(
            self,
            absolute_import_name: str,
            run_id: str = None) -> ExecutionResult:
        """Helper for execute_imports_on_update.

        Args:
            absolute_import_name: See execute_imports_on_update.
            run_id: ID of the system run as a string. This is only used to
                communicate with the import progress dashboard.

        Returns:
            ExecutionResult object describing the results of the executions.

        Raises:
            ExecutionError: The execution of an import failed for any reason.
        """
        logging.info('%s: BEGIN', absolute_import_name)
        with tempfile.TemporaryDirectory() as tmpdir:
            logging.info('%s: downloading repo', absolute_import_name)
            repo_dir = self.github.download_repo(
                tmpdir, timeout=self.config.repo_download_timeout)
            logging.info('%s: downloaded repo %s', absolute_import_name,
                         repo_dir)
            if self.dashboard:
                self.dashboard.info(f'Downloaded repo: {repo_dir}',
                                    run_id=run_id)

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
                            run_id=run_id)
                    except Exception:
                        raise ExecutionError(
                            ExecutionResult('failed', executed_imports,
                                            traceback.format_exc()))
                    executed_imports.append(
                        import_target.get_absolute_import_name(
                            import_dir, import_name_in_spec))

        logging.info('%s: END', absolute_import_name)
        return ExecutionResult('succeeded', executed_imports, 'No issues')

    def _execute_imports_on_commit_helper(self,
                                          commit_sha: str,
                                          run_id: str = None
                                         ) -> ExecutionResult:
        """Helper for execute_imports_on_commit.

        Args:
            See execute_imports_on_commit.
            run_id: ID of the system run as a string. This is only used to
                communicate with the import progress dashboard.

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
            if self.dashboard:
                self.dashboard.info(f'Downloaded repo: {repo_dir}',
                                    run_id=run_id)

            imports_to_execute = import_target.find_imports_to_execute(
                targets=targets,
                manifest_dirs=manifest_dirs,
                manifest_filename=self.config.manifest_filename,
                repo_dir=repo_dir)

            executed_imports = []
            for relative_dir, spec in imports_to_execute:
                try:
                    self._import_one(repo_dir=repo_dir,
                                     relative_import_dir=relative_dir,
                                     absolute_import_dir=os.path.join(
                                         repo_dir, relative_dir),
                                     import_spec=spec,
                                     run_id=run_id)

                except Exception:
                    raise ExecutionError(
                        ExecutionResult('failed', executed_imports,
                                        traceback.format_exc()))
                absolute_name = import_target.get_absolute_import_name(
                    relative_dir, spec['import_name'])
                executed_imports.append(absolute_name)

            if self.dashboard:
                self.dashboard.update_run(
                    {
                        'status': 'succeeded',
                        'time_completed': utils.utctime()
                    }, run_id)

            return ExecutionResult('succeeded', executed_imports, 'No issues')

    def _import_one(self,
                    repo_dir: str,
                    relative_import_dir: str,
                    absolute_import_dir: str,
                    import_spec: dict,
                    run_id: str = None) -> None:
        """Executes an import.

        Args:
            repo_dir: Absolute path to the repository, as a string.
            relative_import_dir: Path to the directory containing the manifest
                as a string, relative to the root directory of the repository.
            absolute_import_dir: Absolute path to the directory containing
                the manifest as a string.
            import_spec: Specification of the import as a dict.
            run_id: ID of the system run that executes the import. This is only
                used to communicate with the import progress dashboard.
        """
        import_name = import_spec['import_name']
        absolute_import_name = import_target.get_absolute_import_name(
            relative_import_dir, import_name)
        curator_emails = import_spec['curator_emails']
        attempt_id = None
        if self.dashboard:
            attempt = _init_attempt_helper(
                dashboard=self.dashboard,
                run_id=run_id,
                import_name=import_name,
                absolute_import_name=absolute_import_name,
                provenance_url=import_spec['provenance_url'],
                provenance_description=import_spec['provenance_description'])
            attempt_id = attempt['attempt_id']
        try:
            self._import_one_helper(repo_dir=repo_dir,
                                    relative_import_dir=relative_import_dir,
                                    absolute_import_dir=absolute_import_dir,
                                    import_spec=import_spec,
                                    run_id=run_id,
                                    attempt_id=attempt_id)
            if self.notifier:
                self.notifier.send(
                    subject=(f'Import Automation - {absolute_import_name} '
                             f'- Succeeded'),
                    body=_SEE_DASHBOARD_MESSAGE,
                    receiver_addresses=curator_emails)

        except Exception as exc:
            if self.dashboard:
                _mark_import_attempt_failed(attempt_id=attempt_id,
                                            message=traceback.format_exc(),
                                            dashboard=self.dashboard)
            if self.notifier:
                self.notifier.send(
                    subject=(f'Import Automation - {absolute_import_name} '
                             f'- Failed'),
                    body=_SEE_DASHBOARD_MESSAGE,
                    receiver_addresses=curator_emails)
            raise exc

    def _import_one_helper(self,
                           repo_dir: str,
                           relative_import_dir: str,
                           absolute_import_dir: str,
                           import_spec: dict,
                           run_id: str = None,
                           attempt_id: str = None) -> None:
        """Helper for _import_one.

        Args:
            See _import_one.
            attempt_id: ID of the import attempt executed by the system run
                with the run_id, as a string. This is only used to communicate
                with the import progress dashboard.
        """
        urls = import_spec.get('data_download_url')
        if urls:
            for url in urls:
                utils.download_file(url, absolute_import_dir,
                                    self.config.file_download_timeout)
                if self.dashboard:
                    self.dashboard.info(f'Downloaded: {url}',
                                        attempt_id=attempt_id,
                                        run_id=run_id)

        with tempfile.TemporaryDirectory() as tmpdir:
            requirements_path = os.path.join(absolute_import_dir,
                                             self.config.requirements_filename)
            central_requirements_path = os.path.join(
                repo_dir, self.config.requirements_filename)
            interpreter_path, process = _create_venv(
                (central_requirements_path, requirements_path),
                tmpdir,
                timeout=self.config.venv_create_timeout)

            _log_process(process=process,
                         dashboard=self.dashboard,
                         attempt_id=attempt_id,
                         run_id=run_id)
            process.check_returncode()

            script_paths = import_spec.get('scripts')
            for path in script_paths:
                process = _run_user_script(
                    interpreter_path=interpreter_path,
                    script_path=os.path.join(absolute_import_dir, path),
                    timeout=self.config.user_script_timeout,
                    cwd=absolute_import_dir)
                _log_process(process=process,
                             dashboard=self.dashboard,
                             attempt_id=attempt_id,
                             run_id=run_id)
                process.check_returncode()

        inputs = self._upload_import_inputs(
            import_dir=absolute_import_dir,
            output_dir=f'{relative_import_dir}/{import_spec["import_name"]}',
            import_inputs=import_spec.get('import_inputs', []),
            attempt_id=attempt_id)

        if self.importer:
            self.importer.delete_previous_output(relative_import_dir,
                                                 import_spec)

            if self.dashboard:
                self.dashboard.info(
                    f'Submitting job to delete the previous import',
                    attempt_id=attempt_id,
                    run_id=run_id)
            try:
                self.importer.delete_import(
                    relative_import_dir,
                    import_spec,
                    block=True,
                    timeout=self.config.importer_delete_timeout)
            except import_service.ImportNotFoundError as exc:
                # If this is the first time executing this import,
                # there will be no previous import
                logging.warning(str(exc))
            if self.dashboard:
                self.dashboard.info(f'Deleted previous import',
                                    attempt_id=attempt_id,
                                    run_id=run_id)
                self.dashboard.info(f'Submitting job to perform the import',
                                    attempt_id=attempt_id,
                                    run_id=run_id)
            self.importer.smart_import(
                relative_import_dir,
                inputs,
                import_spec,
                block=True,
                timeout=self.config.importer_import_timeout)
            if self.dashboard:
                self.dashboard.info(f'Import succeeded',
                                    attempt_id=attempt_id,
                                    run_id=run_id)

        if self.dashboard:
            self.dashboard.update_attempt(
                {
                    'status': 'succeeded',
                    'time_completed': utils.utctime()
                }, attempt_id)

    def _upload_import_inputs(
            self,
            import_dir: str,
            output_dir: str,
            import_inputs: List[Dict[str, str]],
            attempt_id: str = None) -> 'import_service.ImportInputs':
        """Uploads the generated import data files.

        Data files are uploaded to <output_dir>/<version>/, where <version> is a
        time string and is written to <output_dir>/<storage_version_filename>
        after the uploads are complete.

        Args:
            import_dir: Absolute path to the directory with the manifest,
                as a string.
            output_dir: Path to the output directory, as a string.
            import_inputs: List of import inputs each as a dict mapping
                import types to relative paths within the repository. This is
                parsed from the 'import_inputs' field in the manifest.
            attempt_id: ID of the import attempt executed by the system run
                with the run_id, as a string. This is only used to communicate
                with the import progress dashboard.

        Returns:
            ImportInputs object containing the paths to the uploaded inputs.
        """
        uploaded = import_service.ImportInputs()
        version = _clean_time(utils.pacific_time())
        for import_input in import_inputs:
            for input_type in self.config.import_input_types:
                path = import_input.get(input_type)
                if path:
                    dest = f'{output_dir}/{version}/{os.path.basename(path)}'
                    self._upload_file_helper(src=os.path.join(import_dir, path),
                                             dest=dest,
                                             attempt_id=attempt_id)
                    setattr(uploaded, input_type, dest)
        self.uploader.upload_string(
            version,
            os.path.join(output_dir, self.config.storage_version_filename))
        return uploaded

    def _upload_file_helper(self,
                            src: str,
                            dest: str,
                            attempt_id: str = None) -> None:
        """Uploads a file from src to dest.

        Args:
            src: Path to the file to upload, as a string.
            dest: Path to where the file is to be uploaded to, as a string.
            attempt_id: ID of the import attempt executed by the system run
                with the run_id, as a string. This is only used to communicate
                with the import progress dashboard.
        """
        if self.dashboard:
            with open(src) as file:
                self.dashboard.info(
                    f'Uploaded {src}: {file.readline().strip()}',
                    attempt_id=attempt_id)
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


def run_and_handle_exception(run_id: Optional[str],
                             dashboard: Optional[dashboard_api.DashboardAPI],
                             exec_func: Callable, *args) -> ExecutionResult:
    """Runs a method that executes imports and handles its exceptions.

    run_id and dashboard are for logging to the import progress dashboard.
    They can be None to not perform such logging.

    Args:
        run_id: ID of the system run as a string.
        dashboard: DashboardAPI for logging to the import progress dashboard.
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
        if dashboard:
            _mark_system_run_failed(run_id, str(result), dashboard)
        return result
    except Exception:
        logging.exception('An unexpected exception was thrown')
        message = traceback.format_exc()
        if dashboard:
            _mark_system_run_failed(run_id, message, dashboard)
        return ExecutionResult('failed', [], message)


def _run_with_timeout(args: List[str],
                      timeout: float,
                      cwd: str = None) -> subprocess.CompletedProcess:
    """Runs a command in a subprocess.

    Args:
        args: Command to run as a list. Each element is a string.
        timeout: Maximum time the command can run for in seconds as a float.
        cwd: Current working directory of the process as a string.

    Returns:
        subprocess.CompletedProcess object used to run the command.

    Raises:
        Same exceptions as subprocess.run.
    """
    return subprocess.run(args,
                          capture_output=True,
                          text=True,
                          timeout=timeout,
                          cwd=cwd)


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
        venv_dir: Path to the directory to create the virtual environment in
            as a string.
        timeout: Maximum time the creation script can run for in seconds
            as a float.

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
                script.write('python3 -m pip install --no-cache-dir '
                             f'--requirement {path}\n')
        script.flush()

        process = _run_with_timeout(['bash', script.name], timeout)
        return os.path.join(venv_dir, 'bin/python3'), process


def _run_user_script(interpreter_path: str,
                     script_path: str,
                     timeout: float,
                     args: list = None,
                     cwd: str = None) -> subprocess.CompletedProcess:
    """Runs a user Python script.

    Args:
        script_path: Path to the user script to run as a string.
        interpreter_path: Path to the Python interpreter to run the
            user script as a string.
        timeout: Maximum time the user script can run for in seconds
            as a float.
        args: A list of arguments each as a string to pass to the
            user script on the command line.
        cwd: Current working directory of the process as a string.

    Returns:
        subprocess.CompletedProcess object used to run the script.

    Raises:
        subprocess.TimeoutExpired: The user script did not finish
            within timeout.
    """
    if args is None:
        args = []
    return _run_with_timeout([interpreter_path, script_path] + list(args),
                             timeout, cwd)


def _init_run_helper(dashboard: dashboard_api.DashboardAPI,
                     commit_sha: str = None,
                     repo_name: str = None,
                     branch_name: str = None,
                     pr_number: str = None) -> Dict:
    """Initializes a system run with the import progress dashboard."""
    run = {}
    if commit_sha:
        run['commit_sha'] = commit_sha
    if repo_name:
        run['repo_name'] = repo_name
    if branch_name:
        run['branch_name'] = branch_name
    if pr_number:
        run['pr_number'] = pr_number
    return dashboard.init_run(run)


def _init_attempt_helper(dashboard: dashboard_api.DashboardAPI, run_id: str,
                         import_name: str, absolute_import_name: str,
                         provenance_url: str,
                         provenance_description: str) -> Dict:
    """Initializes an import attempt with the import progress dashboard."""
    return dashboard.init_attempt({
        'run_id': run_id,
        'import_name': import_name,
        'absolute_import_name': absolute_import_name,
        'provenance_url': provenance_url,
        'provenance_description': provenance_description
    })


def _mark_system_run_failed(run_id: str, message: str,
                            dashboard: dashboard_api.DashboardAPI) -> Dict:
    """Communicates with the import progress dashboard that a system run
    has failed.
    
    Args:
        run_id: ID of the system run.
        message: An additional message to log to the dashboard
            with level critical.
        dashboard: DashboardAPI object for the communicaiton.
    
    Returns:
        Updated system run returned from the dashboard.
    """
    dashboard.critical(message, run_id=run_id)
    return dashboard.update_run(
        {
            'status': 'failed',
            'time_completed': utils.utctime()
        }, run_id=run_id)


def _mark_import_attempt_failed(attempt_id: str, message: str,
                                dashboard: dashboard_api.DashboardAPI) -> Dict:
    """Communicates with the import progress dashboard that an import attempt
    has failed.
    
    Args:
        attempt_id: ID of the import attempt.
        message: An additional message to log to the dashboard
            with level critical.
        dashboard: DashboardAPI object for the communicaiton.
    
    Returns:
        Updated import attempt returned from the dashboard.
    """
    dashboard.critical(message, attempt_id=attempt_id)
    return dashboard.update_attempt(
        {
            'status': 'failed',
            'time_completed': utils.utctime()
        }, attempt_id)


def _create_system_run_init_failed_result(trace):
    """Creates an ExecutionResult indicating failures."""
    return ExecutionResult('failed', [],
                           f'{_SYSTEM_RUN_INIT_FAILED_MESSAGE}\n{trace}')


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
        process: subprocess.CompletedProcess object whose arguments,
            return code, stdout, and stderr are to be added to the message.
    """
    command = process.args
    if isinstance(command, list):
        command = utils.list_to_str(command, ' ')
    message = (f'{message}\n'
               f'[Subprocess command]: {command}\n'
               f'[Subprocess return code]: {process.returncode}')
    if process.stdout:
        message += '\n[Subprocess stdout]:\n' f'{process.stdout}'
    if process.stderr:
        message += '\n[Subprocess stderr]:\n' f'{process.stderr}'
    return message


def _log_process(process: subprocess.CompletedProcess,
                 dashboard: dashboard_api.DashboardAPI = None,
                 attempt_id: str = None,
                 run_id: str = None) -> None:
    """Logs the result of a subprocess.

    dashboard, attempt_id, and run_id are only for logging to the import
    progress dashboard. They can be None to not perform such logging.

    Args:
        process: subprocess.CompletedProcess object whose arguments,
            return code, stdout, and stderr are to be logged.
        dashboard: DashboardAPI object to communicate with the
            import progress dashboard.
        attempt_id: ID of the import attempt as a string.
        run_id: ID of the system run as a string.
    """
    message = 'Subprocess succeeded'
    if process.returncode:
        message = 'Subprocess failed'
    message = _construct_process_message(message, process)
    if process.returncode:
        if dashboard:
            dashboard.critical(message, attempt_id=attempt_id, run_id=run_id)
    else:
        logging.info(message)
        if dashboard:
            dashboard.info(message, attempt_id=attempt_id, run_id=run_id)

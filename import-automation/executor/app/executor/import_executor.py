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
import re
import subprocess
import tempfile
import logging
import traceback
import typing
import dataclasses

from app import utils
from app import configs
from app.service import dashboard_api
from app.executor import validation
from app.executor import import_target
from app.service import github_api
from app.service import file_uploader

_SYSTEM_RUN_INIT_FAILED_MESSAGE = ('Failed to initialize the system run '
                                   'with the import progress dashboard')


def parse_manifest(path: str) -> dict:
    """Parses the import manifest.

    Args:
        path: Path to the import manifest file as a string.

    Returns:
        The parsed manifest as a dict.
    """
    with open(path) as file:
        return json.load(file)


@dataclasses.dataclass
class ExecutionResult:
    """Describes the result of an execution."""
    # Status of the execution, one of 'succeeded', 'failed', or 'pass'
    status: str
    # Absolute import names of the imports executed
    imports_executed: typing.List[str]
    # Description of the result
    message: str


class ExecutionError(Exception):

    def __init__(self, execution_result):
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
        dashboard: DashboardAPI for communicating with the
            import progress dashboard. If not provided, the executor will not
            communicate with the dashboard.
    """

    def __init__(self,
                 uploader: file_uploader.FileUploader,
                 github: github_api.GitHubRepoAPI,
                 config: configs.ExecutorConfig,
                 dashboard: dashboard_api.DashboardAPI = None):
        self.uploader = uploader
        self.github = github
        self.config = config
        self.dashboard = dashboard

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

        return _run_and_handle_exception(run_id, self.dashboard,
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

        return _run_and_handle_exception(run_id, self.dashboard,
                                         self._execute_imports_on_update_helper,
                                         absolute_import_name, run_id)

    def _execute_imports_on_update_helper(
            self,
            absolute_import_name: str,
            run_id: str = None) -> ExecutionResult:

        logging.info('%s: BEGIN', absolute_import_name)
        with tempfile.TemporaryDirectory() as tmpdir:
            logging.info('%s: downloading repo', absolute_import_name)
            repo_dirname = self.github.download_repo(tmpdir)
            logging.info(absolute_import_name + ': downloaded repo ' +
                         repo_dirname)
            if self.dashboard:
                self.dashboard.info(f'Downloaded repo: {repo_dirname}',
                                    run_id=run_id)

            executed_imports = []

            # An example import_dir is 'scripts/us_fed/treasury'
            import_dir, import_name = import_target.split_absolute_import_name(
                absolute_import_name)
            absolute_import_dir = os.path.join(tmpdir, repo_dirname, import_dir)
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
                            relative_import_dir=import_dir,
                            absolute_import_dir=absolute_import_dir,
                            import_spec=spec,
                            run_id=run_id)
                    except Exception:
                        raise ExecutionError(
                            ExecutionResult('failed', executed_imports,
                                            traceback.format_exc()))
                    executed_imports.append(
                        f'{import_dir}:{import_name_in_spec}')

        logging.info('%s: END', absolute_import_name)
        return ExecutionResult('succeeded', executed_imports, 'No issues')

    def _execute_imports_on_commit_helper(self,
                                          commit_sha: str,
                                          run_id: str = None
                                         ) -> ExecutionResult:

        commit_info = self.github.query_commit(commit_sha)
        commit_message = commit_info['commit']['message']

        # Relative paths to directories having files changed by the commit
        # containing manifests, e.g. 'scripts/us_fed/treasury'.
        manifest_dirs = self.github.find_dirs_in_commit_containing_file(
            commit_sha, self.config.manifest_filename)
        # Import targets specified in the commit message,
        # e.g., 'scripts/us_fed/treasury:constant_maturity', 'constant_maturity'
        targets = import_target.parse_commit_message_targets(commit_message)
        if not targets:
            message = ('No import target specified in commit message '
                       '({commit_message})')
            return ExecutionResult('pass', [], message)

        with tempfile.TemporaryDirectory() as tmpdir:
            repo_dir = self.github.download_repo(tmpdir, commit_sha)
            if self.dashboard:
                self.dashboard.info(f'Downloaded repo: {repo_dir}',
                                    run_id=run_id)
            repo_dir = os.path.join(tmpdir, repo_dir)

            validation.are_import_targets_valid(targets, list(manifest_dirs),
                                                repo_dir,
                                                self.config.manifest_filename)

            # Import targets specified in the commit message can be absolute,
            # e.g., 'scripts/us_fed/treasury:constant_maturity'.
            # Add the directory components, e.g., 'scripts/us_fed/treasury',
            # to manifest_dirs.
            for target in import_target.filter_absolute_import_names(targets):
                import_dir, _ = import_target.split_absolute_import_name(target)
                manifest_dirs.add(import_dir)
            # At this point, manifest_dirs contains all the directories that
            # will be looked at to look for imports.

            executed_imports = []
            for import_dir in manifest_dirs:
                absolute_import_dir = os.path.join(repo_dir, import_dir)
                manifest_path = os.path.join(absolute_import_dir,
                                             self.config.manifest_filename)
                manifest = parse_manifest(manifest_path)
                validation.is_manifest_valid(manifest, repo_dir, import_dir)

                for spec in manifest['import_specifications']:
                    import_name = spec['import_name']
                    if not import_target.import_targetted_by_commit(
                            import_dir, import_name, targets):
                        continue
                    try:
                        self._import_one(
                            relative_import_dir=import_dir,
                            absolute_import_dir=absolute_import_dir,
                            import_spec=spec,
                            run_id=run_id)
                    except Exception:
                        raise ExecutionError(
                            ExecutionResult('failed', executed_imports,
                                            traceback.format_exc()))
                    absolute_name = import_target.get_absolute_import_name(
                        import_dir, import_name)
                    executed_imports.append(absolute_name)

            return ExecutionResult('succeeded', executed_imports, 'No issues')

    def _import_one(self,
                    relative_import_dir: str,
                    absolute_import_dir: str,
                    import_spec: dict,
                    run_id: str = None) -> None:
        """Executes an import.

        Args:
            relative_import_dir: Path to the directory containing the manifest
                as a string, relative to the root directory of the repository.
            absolute_import_dir: Absolute path to the directory containing
                the manifest as a string.
            import_spec: Specification of the import as a dict.
            run_id: ID of the system run that executes the import.
        """
        attempt_id = None
        if self.dashboard:
            import_name = import_spec['import_name']
            attempt = _init_attempt_helper(
                dashboard=self.dashboard,
                run_id=run_id,
                import_name=import_name,
                absolute_import_name=import_target.get_absolute_import_name(
                    relative_import_dir, import_name),
                provenance_url=import_spec['provenance_url'],
                provenance_description=import_spec['provenance_description'])
            attempt_id = attempt['attempt_id']
        try:
            self._import_one_helper(relative_import_dir=relative_import_dir,
                                    absolute_import_dir=absolute_import_dir,
                                    import_spec=import_spec,
                                    run_id=run_id,
                                    attempt_id=attempt_id)
        except Exception as exc:
            if self.dashboard:
                _mark_import_attempt_failed(attempt_id=attempt_id,
                                            message=traceback.format_exc(),
                                            dashboard=self.dashboard)
            raise exc

    def _import_one_helper(self,
                           relative_import_dir: str,
                           absolute_import_dir: str,
                           import_spec: dict,
                           run_id: str = None,
                           attempt_id: str = None) -> None:
        urls = import_spec.get('data_download_url')
        if urls:
            for url in urls:
                utils.download_file(url, '')
                if self.dashboard:
                    self.dashboard.info(f'Downloaded: {url}',
                                        attempt_id=attempt_id)

        with tempfile.TemporaryDirectory() as tmpdir:
            requirements_path = os.path.join(absolute_import_dir,
                                             self.config.requirements_filename)
            interpreter_path, process = _create_venv(
                requirements_path,
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

        self._upload_import_inputs(
            import_dir=absolute_import_dir,
            output_dir=f'{relative_import_dir}/{import_spec["import_name"]}',
            import_inputs=import_spec.get('import_inputs', []),
            attempt_id=attempt_id)

        # TODO(intrepiditee): Call the dev importer

    def _upload_import_inputs(self,
                              import_dir: str,
                              output_dir: str,
                              import_inputs: typing.List[typing.Dict[str, str]],
                              attempt_id: str = None) -> None:

        version = _clean_time(utils.pacific_time())
        for import_input in import_inputs:
            for input_type in self.config.import_input_types:
                path = import_input.get(input_type)
                if path:
                    self._upload_file_helper(
                        src=os.path.join(import_dir, path),
                        dest=f'{output_dir}/{version}/{os.path.basename(path)}',
                        attempt_id=attempt_id)
        self.uploader.upload_string(
            version,
            os.path.join(output_dir, self.config.storage_version_filename))

    def _upload_file_helper(self,
                            src: str,
                            dest: str,
                            attempt_id: str = None) -> None:
        if self.dashboard:
            with open(src) as file:
                self.dashboard.info(
                    f'Uploaded {src}: {file.readline().strip()}',
                    attempt_id=attempt_id)
        self.uploader.upload_file(src, dest)


def _run_and_handle_exception(run_id: typing.Optional[str],
                              dashboard: typing.Optional[
                                  dashboard_api.DashboardAPI],
                              exec_func: typing.Callable,
                              *args) -> ExecutionResult:
    """Runs a method of ImportExecutor that executes imports and handles
    its exceptions.

    run_id and dashboard are for logging to the import progress dashboard.
    They can be None to not perform such logging.

    Args:
        run_id: ID of the system run as a string.
        dashboard: DashboardAPI for logging to the import progress dashboard.
        exec_func: A method of ImportExecutor to execute.
        args: List of arguments sent to exec_func.

    Returns:
        ExecutionResult object describing the results of the imports.
    """
    try:
        return exec_func(*args)
    except ExecutionError as exc:
        logging.exception('ExecutionError was thrown')
        if dashboard:
            _mark_system_run_failed(run_id, str(exc.result), dashboard)
        return exc.result
    except Exception:
        logging.exception('An unexpected exception was thrown')
        message = traceback.format_exc()
        if dashboard:
            _mark_system_run_failed(run_id, message, dashboard)
        return ExecutionResult('failed', [], message)


def _run_with_timeout(args: typing.List[str],
                      timeout: float,
                      cwd: str = None) -> subprocess.CompletedProcess:
    """Runs a command in a subprocess.

    Args:
        args: Command to run as a list. Each element is a string.
        timeout: Maximum time the command can run for in seconds as a float.
        cwd: Current working directory of the process as a string.

    Returns:
        subprocess.CompletedProcess object used to run the command.
    """
    return subprocess.run(args,
                          capture_output=True,
                          text=True,
                          timeout=timeout,
                          cwd=cwd)


def _create_venv(
        requirements_path: str, venv_dir: str,
        timeout: float) -> typing.Tuple[str, subprocess.CompletedProcess]:
    """Creates a Python virtual environment.

    The virtual environment is created with --system-site-packages set,
    which allows it to access modules installed on the host. This provides
    the opportunity to use the requirements.txt file for this project as
    a central requirement file for all user scripts.

    Args:
        requirements_path: Path to a pip requirement file listing the
            dependencies to install as a string.
        venv_dir: Path to the directory to create the virtual environment in
            as a string.
        timeout: Maximum time the creation script can run for in seconds
            as a float.

    Returns:
        A tuple consisting of the path to the created interpreter as a string
        and a subprocess.CompletedProcess object used to create the environment.
    """
    with tempfile.NamedTemporaryFile(mode='w', suffix='.sh') as script:
        script.write(f'python3 -m venv --system-site-packages {venv_dir}\n')
        script.write(f'. {venv_dir}/bin/activate\n')
        if os.path.exists(requirements_path):
            script.write('python3 -m pip install --upgrade pip\n')
            script.write('python3 -m pip install --no-cache-dir '
                         f'--requirement {requirements_path}\n')
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
                     pr_number: str = None) -> dict:
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
                         provenance_description: str) -> dict:
    return dashboard.init_attempt({
        'run_id': run_id,
        'import_name': import_name,
        'absolute_import_name': absolute_import_name,
        'provenance_url': provenance_url,
        'provenance_description': provenance_description
    })


def _mark_system_run_failed(run_id: str, message: str,
                            dashboard: dashboard_api.DashboardAPI) -> dict:
    dashboard.critical(message, run_id=run_id)
    return dashboard.update_run({'status': 'failed'}, run_id=run_id)


def _mark_import_attempt_failed(attempt_id: str, message: str,
                                dashboard: dashboard_api.DashboardAPI) -> dict:
    dashboard.critical(message, attempt_id=attempt_id)
    return dashboard.update_attempt({'status': 'failed'}, attempt_id=attempt_id)


def _create_system_run_init_failed_result(trace):
    return ExecutionResult('failed', [],
                           f'{_SYSTEM_RUN_INIT_FAILED_MESSAGE}\n{trace}')


def _clean_time(time: str) -> str:
    """Given a time string, replaces ':', '-', and '.' with '_'."""
    return re.sub(r'[:\-.]', '_', time)


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
        message += ('\n[Subprocess stdout]:\n' f'{process.stdout}')
    if process.stderr:
        message += ('\n[Subprocess stderr]:\n' f'{process.stderr}')
    return message


def _log_process(process: subprocess.CompletedProcess,
                 dashboard: 'dashboard_api.DashboardAPI',
                 attempt_id: str = None,
                 run_id: str = None) -> None:
    """Logs the result of a subprocess.

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
        logging.critical(message)
        if dashboard:
            dashboard.critical(message, attempt_id=attempt_id, run_id=run_id)
    else:
        logging.info(message)
        if dashboard:
            dashboard.info(message, attempt_id=attempt_id, run_id=run_id)

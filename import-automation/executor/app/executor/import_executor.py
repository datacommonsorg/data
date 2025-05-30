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
import glob
import json
import logging
import os
import shutil
import shlex
import sys
import subprocess
import tempfile
import time
import traceback
from typing import Callable, Dict, Iterable, List, Optional, Tuple

REPO_DIR = os.path.dirname(
    os.path.dirname(
        os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
sys.path.append(os.path.join(REPO_DIR, 'tools', 'import_differ'))
sys.path.append(os.path.join(REPO_DIR, 'tools', 'import_validation'))
sys.path.append(os.path.join(REPO_DIR, 'util'))

import file_util

from import_differ import ImportDiffer
from import_validation import ImportValidation
from app import configs
from app import utils
from app.executor import cloud_run_simple_import
from app.executor import import_target
from app.service import email_notifier
from app.service import file_uploader
from app.service import github_api
from app.service import import_service
from google.cloud import storage

# Email address for status messages.
_DEBUG_EMAIL_ADDR = 'datacommons-debug+imports@google.com'
_ALERT_EMAIL_ADDR = 'datacommons-test-alerts+imports@google.com'

_SEE_LOGS_MESSAGE = (
    'Please find logs in the Logs Explorer of the GCP project associated with'
    ' Import Automation.')

_IMPORT_METADATA_MCF_TEMPLATE = """
Node: dcid:dc/base/{import_name}
typeOf: dcid:Provenance
lastDataRefreshDate: "{last_data_refresh_date}"
"""


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
        curator_emails = import_spec['curator_emails']
        dc_email_aliases = [_ALERT_EMAIL_ADDR, _DEBUG_EMAIL_ADDR]
        time_start = time.time()
        try:
            self._import_one_helper(
                repo_dir=repo_dir,
                relative_import_dir=relative_import_dir,
                absolute_import_dir=absolute_import_dir,
                import_spec=import_spec,
            )
            time_taken = '{0:.2f}'.format(time.time() - time_start)
            logging.info(f'Import Automation Success - {import_name}')
            logging.info(f'Script execution time taken = {time_taken}s')

        except Exception as exc:
            if self.notifier and not self.config.disable_email_notifications:
                msg = f'Failed Import: {import_name} ({absolute_import_name})\n\n'
                msg += f'{_SEE_LOGS_MESSAGE}\n\n'
                msg += f'Stack Trace: \n'
                msg += f'{exc}'
                self.notifier.send(
                    subject=f'Import Automation Failure - {import_name}',
                    body=msg,
                    receiver_addresses=dc_email_aliases + curator_emails,
                )
            raise exc

    def _get_latest_version(self, import_dir: str) -> str:
        """
        Find previous import data in GCS.
        Returns:
          GCS path for the latest import data.
        """
        bucket = storage.Client(self.config.gcs_project_id).bucket(
            self.config.storage_prod_bucket_name)
        blob = bucket.get_blob(
            f'{import_dir}/{self.config.storage_version_filename}')
        if not blob or not blob.download_as_text():
            logging.error(
                f'Not able to find latest_version.txt in {import_dir}.')
            return ''
        latest_version = blob.download_as_text()
        return f'gs://{bucket.name}/{import_dir}/{latest_version}'

    def _invoke_import_validation(self, repo_dir: str, relative_import_dir: str,
                                  absolute_import_dir: str, import_spec: dict,
                                  version: str) -> bool:
        """ 
        Performs validations on import data.
        """
        validation_status = True
        config_file = import_spec.get('validation_config_file', '')
        if config_file:
            config_file_path = os.path.join(absolute_import_dir, config_file)
        else:
            config_file_path = os.path.join(repo_dir,
                                            self.config.validation_config_file)
        logging.info(f'Validation config file: {config_file_path}')

        import_dir = f'{relative_import_dir}/{import_spec["import_name"]}'

        latest_version = self._get_latest_version(import_dir)
        logging.info(f'Latest version: {latest_version}')
        differ_job_name = 'differ'

        # Trigger validations for each tmcf/csv under import_inputs.
        import_inputs = import_spec.get('import_inputs', [])
        for import_input in import_inputs:
            try:
                template_mcf = import_input['template_mcf']
                cleaned_csv = glob.glob(
                    os.path.join(absolute_import_dir,
                                 import_input['cleaned_csv']))
            except KeyError:
                logging.error(
                    'Skipping validation due to missing import input spec.')
                continue
            import_prefix = template_mcf.split('.')[0]
            validation_output_path = os.path.join(absolute_import_dir,
                                                  import_prefix, 'validation')
            current_data_path = os.path.join(validation_output_path, '*.mcf')
            previous_data_path = latest_version + f'/{import_prefix}/validation/*.mcf'
            summary_stats = os.path.join(validation_output_path,
                                         'summary_report.csv')
            validation_output_file = os.path.join(validation_output_path,
                                                  'validation_output.csv')
            differ_output = os.path.join(validation_output_path,
                                         'point_analysis_summary.csv')
            # Run dc import tool to generate resolved mcf.
            logging.info('Generating resolved mcf...')
            import_tool_args = [
                f'-o={validation_output_path}',
                'genmcf',
                template_mcf,
            ]
            if cleaned_csv:
                import_tool_args.extend(cleaned_csv)
            process = _run_user_script(
                interpreter_path='java',
                script_path='-jar ' + self.config.import_tool_path,
                timeout=self.config.user_script_timeout,
                args=import_tool_args,
                cwd=absolute_import_dir,
                env=os.environ.copy(),
            )
            _log_process(process=process)
            process.check_returncode()
            logging.info('Generated resolved mcf in %s', validation_output_path)

            if self.config.invoke_import_validation:
                # Invoke differ and validation scripts.
                if latest_version and len(
                        file_util.file_get_matching(previous_data_path)) > 0:
                    logging.info('Invoking differ tool...')
                    differ = ImportDiffer(
                        current_data=current_data_path,
                        previous_data=previous_data_path,
                        output_location=validation_output_path,
                        differ_tool=self.config.differ_tool_path,
                        project_id=self.config.gcp_project_id,
                        job_name=differ_job_name,
                        file_format='mcf',
                        runner_mode='native')
                    differ.run_differ()

                    logging.info('Invoking validation script...')
                    validation = ImportValidation(config_file_path,
                                                  differ_output, summary_stats,
                                                  validation_output_file)
                    status = validation.run_validations()
                    if validation_status:
                        validation_status = status
                else:
                    logging.error(
                        'Skipping validation due to missing latest mcf file')
            else:
                logging.info(
                    'Skipping import validations as per import config.')

            if not self.config.skip_gcs_upload:
                # Upload output to GCS.
                gcs_output = f'{import_dir}/{version}/{import_prefix}/validation'
                logging.info(
                    f'Uploading validation output to GCS path: {gcs_output}')
                for filename in os.listdir(validation_output_path):
                    filepath = os.path.join(validation_output_path, filename)
                    if os.path.isfile(filepath):
                        dest = f'{gcs_output}/{filename}'
                        self.uploader.upload_file(
                            src=filepath,
                            dest=dest,
                        )
        return validation_status

    def _create_mount_point(self, gcs_volume_mount_dir: str,
                            cleanup_gcs_volume_mount: bool,
                            absolute_import_dir: str, import_name: str) -> None:
        mount_path = os.path.join(gcs_volume_mount_dir, import_name)
        out_path = os.path.join(absolute_import_dir, 'gcs_output')
        logging.info(f'Mount path: {mount_path}, Out path: {out_path}')
        if cleanup_gcs_volume_mount and os.path.exists(mount_path):
            shutil.rmtree(mount_path)
        if os.path.lexists(out_path):
            os.unlink(out_path)
        os.makedirs(mount_path, exist_ok=True)
        os.symlink(mount_path, out_path, target_is_directory=True)

    def _invoke_import_job(self, absolute_import_dir: str, import_spec: dict,
                           version: str, interpreter_path: str,
                           process: subprocess.CompletedProcess) -> None:
        script_paths = import_spec.get('scripts')
        import_name = import_spec['import_name']
        self._create_mount_point(self.config.gcs_volume_mount_dir,
                                 self.config.cleanup_gcs_volume_mount,
                                 absolute_import_dir, import_name)
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
                script_interpreter = _get_script_interpreter(
                    script_path, interpreter_path)
                script_env = os.environ.copy()
                if self.config.user_script_env:
                    script_env.update(self.config.user_script_env)
                process = _run_user_script(
                    interpreter_path=script_interpreter,
                    script_path=script_path,
                    timeout=self.config.user_script_timeout,
                    args=self.config.user_script_args,
                    cwd=absolute_import_dir,
                    env=script_env,
                )
                _log_process(process=process)
                process.check_returncode()

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
        import_name = import_spec['import_name']
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
                repo_dir, 'import-automation', 'executor',
                self.config.requirements_filename)
            interpreter_path, process = _create_venv(
                (central_requirements_path, requirements_path),
                tmpdir,
                timeout=self.config.venv_create_timeout,
            )

            _log_process(process=process)
            process.check_returncode()

            self._invoke_import_job(absolute_import_dir=absolute_import_dir,
                                    import_spec=import_spec,
                                    version=version,
                                    interpreter_path=interpreter_path,
                                    process=process)

            logging.info("Invoking import validations")
            validation_status = self._invoke_import_validation(
                repo_dir=repo_dir,
                relative_import_dir=relative_import_dir,
                absolute_import_dir=absolute_import_dir,
                import_spec=import_spec,
                version=version)
            logging.info(
                f'Validations completed with status: {validation_status}')

        if self.config.skip_gcs_upload:
            logging.info("Skipping GCS upload")
            return

        inputs = self._upload_import_inputs(
            import_dir=absolute_import_dir,
            output_dir=f'{relative_import_dir}/{import_name}',
            version=version,
            import_spec=import_spec,
            validation_status=validation_status)

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
            self, import_dir: str, output_dir: str, version: str,
            import_spec: dict,
            validation_status: bool) -> import_service.ImportInputs:
        """Uploads the generated import data files.

    Data files are uploaded to <output_dir>/<version>/, where <version> is a
    time string and is written to <output_dir>/<storage_version_filename>
    after the uploads are complete.

    Args:
        import_dir: Absolute path to the directory with the manifest, as a
          string.
        output_dir: Path to the output directory, as a string.
        import_inputs: Specification of the import as a dict.

    Returns:
        ImportInputs object containing the paths to the uploaded inputs.
    """
        uploaded = import_service.ImportInputs()
        import_inputs = import_spec.get('import_inputs', [])
        for import_input in import_inputs:
            for input_type in self.config.import_input_types:
                path = import_input.get(input_type)
                if not path:
                    continue
                for file in file_util.file_get_matching(
                        os.path.join(import_dir, path)):
                    if file:
                        dest = f'{output_dir}/{version}/{os.path.basename(file)}'
                        self._upload_file_helper(
                            src=file,
                            dest=dest,
                        )
                uploaded_dest = f'{output_dir}/{version}/{os.path.basename(path)}'
                setattr(uploaded, input_type, uploaded_dest)

        # Upload any files downloaded from source
        source_files = [
            os.path.join(import_dir, file)
            for file in import_spec.get('source_files', [])
        ]
        source_files = file_util.file_get_matching(source_files)
        for file in source_files:
            dest = f'{output_dir}/{version}/source_files/{os.path.basename(file)}'
            self._upload_file_helper(
                src=file,
                dest=dest,
            )

        if self.config.ignore_validation_status or validation_status:
            self.uploader.upload_string(
                version,
                os.path.join(output_dir, self.config.storage_version_filename))
            self.uploader.upload_string(
                self._import_metadata_mcf_helper(import_spec),
                os.path.join(output_dir,
                             self.config.import_metadata_mcf_filename))
        else:
            logging.error(
                "Skipping latest version update due to validation failure.")
        return uploaded

    def _upload_file_helper(self, src: str, dest: str) -> None:
        """Uploads a file from src to dest.

    Args:
        src: Path to the file to upload, as a string.
        dest: Path to where the file is to be uploaded to, as a string.
    """
        self.uploader.upload_file(src, dest)

    def _import_metadata_mcf_helper(self, import_spec: dict) -> str:
        """Generates import_metadata_mcf node for import.

        Args:
            import_spec: Specification of the import as a dict.

        Returns:
            import_metadata_mcf node.
        """
        node = _IMPORT_METADATA_MCF_TEMPLATE.format_map({
            "import_name": import_spec.get('import_name'),
            "last_data_refresh_date": _clean_date(utils.utctime())
        })
        next_data_refresh_date = utils.next_utc_date(
            import_spec.get('cron_schedule'))
        if next_data_refresh_date:
            node += f'nextDataRefreshDate: "{next_data_refresh_date}"\n'
        return node


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
                            env: dict = None,
                            name: str = None) -> subprocess.CompletedProcess:
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
        logging.info(f'Launching async command for {name}: {args} '
                     f'with timeout {timeout} in {cwd}, env: {env}')
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
            logging.info(f'Process stderr:{name}: {line}')
        for line in process.stdout:
            stdout.append(line)
            logging.info(f'Process stdout:{name}: {line}')

        # Wait in case script has closed stderr/stdout early.
        process.wait()
        end_time = time.time()

        return_code = process.returncode
        end_msg = (f'Completed script:{name}: "{args}", '
                   f'Return code: {return_code}, '
                   f'time: {end_time - start_time:.3f} secs.\n')
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
            f'An unexpected exception was thrown: {e} when running {name}:'
            f'{args}: {message}')
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
        raise e


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
        os.environ['PATH'] = os.path.join(venv_dir,
                                          'bin') + ':' + os.environ.get('PATH')
        return os.path.join(venv_dir, 'bin/python3'), process


def _get_script_interpreter(script: str, py_interpreter: str) -> str:
    """Returns the interpreter for the script.

    Args:
        script: user script to be executed
        py_interpreter: Path to python within virtual environment

    Returns:
        interpreter for user script, such as python for .py, bash for .sh
        Returns None if the script has no extension.
    """
    if not script:
        return None

    base, ext = os.path.splitext(script.split(' ')[0])
    match ext:
        case '.py':
            return py_interpreter
        case '.sh':
            return 'bash'
        case _:
            logging.info(f'Unknown extension for script: {script}.')
            return None

    return py_interpreter


def _run_user_script(
    interpreter_path: str,
    script_path: str,
    timeout: float,
    args: list = None,
    cwd: str = None,
    env: dict = None,
    name: str = None,
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
      name: Name of the script.

  Returns:
      subprocess.CompletedProcess object used to run the script.

  Raises:
      subprocess.TimeoutExpired: The user script did not finish
          within timeout.
  """
    script_args = []
    if interpreter_path:
        script_args.append(interpreter_path)
    script_args.extend(shlex.split(script_path))
    if args:
        script_args.extend(args)
    return _run_with_timeout_async(script_args, timeout, cwd, env, name)


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


def _clean_date(time: str) -> str:
    """Converts ISO8601 time string to YYYY-MM-DD format.

    Args:
        time: Time string in ISO8601 format.

    Returns:
        YYYY-MM-DD date.
    """
    return time[:10]


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

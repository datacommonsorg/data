import re
import json
import logging
import os
import subprocess
import tempfile

from app import configs
from app.service import dashboard_api
from app.service import github_api
from app.service import gcs_io
from app.executor import validation
from app import utils


def parse_manifest(path):
    """Parses the import manifest.

    Args:
        path: Path to the import manifest file as a string

    Returns:
        The parsed manifest as a dict.
    """
    with open(path, 'r') as file:
        return json.load(file)


def parse_commit_message_targets(commit_message):
    """Parses the import targets from a commit message.

    Import targets are specified by including
    IMPORTS=<comma separated list of import names> in the commit message.

    Args:
        commit_message: GitHub commit message as a string.

    Returns:
        A list of import names each as a string.
    """
    target_lists = re.findall(r'(?:IMPORTS=)((?:\w+)(?:,\w+)*)', commit_message)
    if not len(target_lists):
        raise ValueError(
            f'No import targets found in the commit message ({commit_message})')
    targets = set()
    for target_list in target_lists:
        targets.update(target_list.split(','))
    return list(targets)


def construct_log(message, level='info', time_logged=None,
                  run_id=None, attempt_id=None, process=None):
    """Constructs a progress log that can be sent to the dashboard.

    Args:
        message: Log message as a string.
        level: Log level as a string.
        time_logged: Time logged in ISO format with UTC timezone as a string.
        run_id: ID of the system run to link to as a string.
        attempt_id: ID of the import attempt to link to as a string.
        process: subprocess.CompletedProcess object that has been executed and
            that needs to be logged.

    Returns:
        Constructed progress log ready to be sent to the dashboard as a dict.

    Raises:
        ValueError: Neither run_id nor attempt_id is specified.
    """
    if not run_id and not attempt_id:
        raise ValueError('Neither run_id nor attempt_id is specified')
    if not time_logged:
        time_logged = utils.utctime()
    log = {'message': message, 'level': level, 'time_logged': time_logged}
    if run_id:
        log['run_id'] = run_id
    if attempt_id:
        log['attempt_id'] = attempt_id
    if process:
        log['args'] = (utils.list_to_str(process.args, ' ')
                       if isinstance(process.args, list)
                       else process.args)
        log['return_code'] = process.returncode
        if not process.returncode:
            log['level'] = 'error'
        if process.stdout:
            log['stdout'] = process.stdout
        if process.stderr:
            log['stderr'] = process.stderr
    return log


def run_with_timeout(args, timeout):
    """Run the command described by args.

    Args:
        args: Command to run as a list. Each element is a string.
        timeout: Maximum time the command can run for in seconds as an int.

    Returns:
        subprocess.CompletedProcess object used to run the command.
    """
    return subprocess.run(args, capture_output=True, text=True, timeout=timeout)


def create_venv(requirements_path, venv_dir,
                timeout=configs.VENV_CREATE_TIMEOUT):
    """Creates a Python virtual environment.

    Args:
        requirements_path: Path to a pip requirement file listing the
            dependencies to install as a string.
        venv_dir: Path to a directory to create the virtual environment in
            as a string.
        timeout: Maximum time the creation script can run for in seconds
            as an int.

    Returns:
        Path to the created interpreter as a string.
        subprocess.CompletedProcess object used to create the environment.
    """
    with tempfile.NamedTemporaryFile(mode='w', suffix='.sh') as script:
        script.write(f'python3 -m virtualenv --verbose --clear {venv_dir}\n')
        script.write(f'. {venv_dir}/bin/activate\n')
        script.write('python3 -m pip install --verbose --no-cache-dir '
                     f'--requirement {requirements_path}\n')
        script.flush()

        process = run_with_timeout(['bash', script.name], timeout)
        return os.path.join(venv_dir, 'bin/python'), process


def run_user_script(interpreter_path, script_path, args=[],
                    timeout=configs.USER_SCRIPT_TIMEOUT):
    """Runs a user script.

    Args:
        script_path: Path to the user script to run as a string.
        interpreter_path: Path to the Python interpreter to run the
            user script as a string.
        args: A list of arguments each as a string to pass to the
            user script on the command line.
        timeout: Maximum time the user script can run for in seconds
            as an int.

    Returns:
        subprocess.CompletedProcess object used to run the script.

    Raises:
        subprocess.TimeoutExpired: The user script did not finish
            within timeout.
    """
    return run_with_timeout([interpreter_path, script_path] + list(args),
                            timeout)


def execute_imports_on_commit(commit_sha,
                              repo_name=None, branch_name=None, pr_number=None):
    """Executes imports upon a GitHub commit that is a part of a pull request
    to the master branch of datacommonsorg/data.

    repo_name, branch_name, and pr_number are used only for logging purposes.

    Args:
        commit_sha: ID of the commit as a string.
        repo_name: Name of the repository from which the pull request is created
            as a string.
        branch_name: Name of the branch the pull request wants to merge
            as a stirng.
        pr_number: Number of the pull request as an int.

    Returns:
        A string describing the results of the imports.
    """
    dashboard = dashboard_api.DashboardAPI()
    run = {'commit_sha': commit_sha}
    if repo_name:
        run['repo_name'] = repo_name
    if branch_name:
        run['branch_name'] = branch_name
    if pr_number:
        run['pr_number'] = pr_number
    run = dashboard.init_run(run)

    run_id = run['run_id']

    github = github_api.GitHubRepoAPI()

    commit_info = github.query_commit(commit_sha)
    commit_author_username = commit_info['author']['login']
    commit_message = commit_info['commit']['message']

    manifest_dirs = github.find_dirs_in_commit_containing_file(
        commit_sha, configs.MANIFEST_FILENAME)
    import_targets = parse_commit_message_targets(commit_message)
    valid, err = validation.import_targets_valid(import_targets, manifest_dirs)
    if not valid:
        return err

    with tempfile.TemporaryDirectory() as tmpdir:
        repo_dirname = github.download_repo(tmpdir, commit_sha)
        cwd = os.path.join(tmpdir, repo_dirname)
        os.chdir(cwd)

        dashboard.info(f'Downloaded repo: {repo_dirname}', run_id=run_id)

        import_all = 'all' in import_targets
        for dir_path in manifest_dirs:
            manifest_path = os.path.join(dir_path, configs.MANIFEST_FILENAME)
            manifest = parse_manifest(manifest_path)
            for spec in manifest['import_specifications']:
                import_name = spec['import_name']
                absolute_name = utils.get_absolute_import_name(dir_path, import_name)
                if import_all or absolute_name in import_targets or import_name in import_targets:
                    import_one(dir_path, spec, run_id, dashboard)

    return 'success'


def execute_imports_on_update(absolute_import_name):
    """Executes imports upon a scheduled update.

    Args:
        absolute_import_name: Absolute import name of the imports to execute of
            the form <path to directory with manifest>:<import name>. E.g.,
            scripts/us_fed/treasury_constant_maturity_rates:USFed_ConstantMaturityRates.
            <import name> can be 'all' to execute all imports within
            the directory.

    Returns:
        A string describing the results of the imports.
    """
    dashboard = dashboard_api.DashboardAPI()
    run = dashboard.init_run({})
    run_id = run['run_id']
    github = github_api.GitHubRepoAPI()
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_dirname = github.download_repo(tmpdir)
        cwd = os.path.join(tmpdir, repo_dirname)
        os.chdir(cwd)

        dashboard.info(f'Downloaded repo: {repo_dirname}', run_id=run_id)

        dir_path, import_name = utils.split_relative_import_name(
            absolute_import_name)
        manifest_path = os.path.join(dir_path, configs.MANIFEST_FILENAME)
        manifest = parse_manifest(manifest_path)
        for spec in manifest['import_specifications']:
            if import_name == 'all' or import_name == spec['import_name']:
                import_one(dir_path, spec, run_id, dashboard)

    return 'success'


def import_one(dir_path, import_spec, run_id, dashboard):
    """Executes an import.

    Args:
        dir_path: Path to the direcotry containing the manifest as a string.
        import_spec: Specification of the import as a dict.
        run_id: ID of the system run the import belongs to.
        dashboard: DashboardAPI object to communicate with the
            import progress dashboard.
    """
    import_name = import_spec['import_name']
    attempt = dashboard.init_attempt(
        {
            'run_id': run_id,
            'import_name': import_name,
            'absolute_import_name': utils.get_absolute_import_name(dir_path, import_name),
            'provenance_url': import_spec['provenance_url'],
            'provenance_description': import_spec['provenance_description']
        })
    attempt_id = attempt['attempt_id']

    cwd = os.getcwd()
    os.chdir(dir_path)

    urls = import_spec.get('data_download_url')
    if urls:
        for url in urls:
            utils.download_file(url, '.')
            dashboard.info(f'Downloaded: {url}', attempt_id=attempt_id)

    with tempfile.TemporaryDirectory() as tmpdir:
        interpreter_path, process = create_venv(configs.REQUIREMENTS_FILENAME, tmpdir)
        dashboard.info(f'Installed dependencies: {process.stdout}', attempt_id=attempt_id)

        script_paths = import_spec.get('scripts')
        for path in script_paths:
            process = run_user_script(interpreter_path, path)
            dashboard.info(f'Run {path}: {process.stdout}', attempt_id=attempt_id)

    import_inputs = import_spec.get('import_inputs', [])
    for import_input in import_inputs:
        time = utils.utctime()
        path_prefix = f'{dir_path}:{import_name}/{time}'
        bucket_io = gcs_io.GCSBucketIO()

        template_mcf = import_input.get('template_mcf')
        cleaned_csv = import_input.get('cleaned_csv')
        node_mcf = import_input.get('node_mcf')
        if template_mcf:
            with open(template_mcf, 'r') as f:
                dashboard.info(f'Generated template MCF: {f.readline()}',
                               attempt_id=attempt_id)
            bucket_io.upload_file(
                template_mcf,
                f'{path_prefix}/{os.path.basename(template_mcf)}')

        if cleaned_csv:
            with open(cleaned_csv, 'r') as f:
                dashboard.info(f'Generated cleaned CSV: {f.readline()}',
                               attempt_id=attempt_id)
            bucket_io.upload_file(
                cleaned_csv,
                f'{path_prefix}/{os.path.basename(cleaned_csv)}')

        if node_mcf:
            with open(node_mcf, 'r') as f:
                dashboard.info(f'Generated node MCF: {f.readline()}',
                               attempt_id=attempt_id)
            bucket_io.upload_file(
                node_mcf,
                f'{path_prefix}/{os.path.basename(node_mcf)}')

    os.chdir(cwd)

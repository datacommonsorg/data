import re
import json
import os
import subprocess
import tempfile
import logging

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
    with open(path) as file:
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
    targets = set()
    for target_list in target_lists:
        targets.update(target_list.split(','))
    return list(targets)


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
        if os.path.exists(requirements_path):
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


def _execute_imports_on_commit_helper(commit_sha, run_id):
    dashboard = dashboard_api.DashboardAPI()
    github = github_api.GitHubRepoAPI()

    commit_info = github.query_commit(commit_sha)
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
                absolute_name = utils.get_absolute_import_name(dir_path,
                                                               import_name)
                if import_all or absolute_name in import_targets or \
                        import_name in import_targets:
                    import_name = spec['import_name']
                    attempt_id = _init_attempt(
                        run_id,
                        import_name,
                        os.path.join(dir_path, import_name),
                        spec['provenance_url'],
                        spec['provenance_description'])['attempt_id']
                    import_one(dir_path, spec, run_id, attempt_id)
    return 'success'


def _init_run(commit_sha=None, repo_name=None, branch_name=None, pr_number=None):
    dashboard = dashboard_api.DashboardAPI()
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
    run_id = _init_run(commit_sha, repo_name, branch_name, pr_number)['run_id']

    try:
        return _execute_imports_on_commit_helper(commit_sha, run_id)
    except Exception as e:
        logging.exception(e)
        mark_system_run_failed(run_id)
        return f'{e}'


def mark_system_run_failed(run_id):
    dashboard = dashboard_api.DashboardAPI()
    dashboard.critical('Failed', run_id=run_id)
    return dashboard.update_run({'status': 'failed'}, run_id=run_id)


def mark_import_attempt_failed(attempt_id):
    dashboard = dashboard_api.DashboardAPI()
    dashboard.critical('Failed', attempt_id=attempt_id)
    return dashboard.update_attempt({'status': 'failed'}, attempt_id=attempt_id)


def _execute_imports_on_update_helper(absolute_import_name, run_id):
    logging.info(absolute_import_name + ': BEGIN')
    github = github_api.GitHubRepoAPI()
    dashboard = dashboard_api.DashboardAPI()
    with tempfile.TemporaryDirectory() as tmpdir:
        logging.info(absolute_import_name + ': downloading repo')
        repo_dirname = github.download_repo(tmpdir)
        logging.info(absolute_import_name + ': downloaded repo ' + repo_dirname)
        cwd = os.path.join(tmpdir, repo_dirname)
        os.chdir(cwd)

        dashboard.info(f'Downloaded repo: {repo_dirname}', run_id=run_id)

        dir_path, import_name = utils.split_relative_import_name(
            absolute_import_name)
        manifest_path = os.path.join(dir_path, configs.MANIFEST_FILENAME)
        manifest = parse_manifest(manifest_path)
        logging.info(absolute_import_name + ': loaded manifest ' + manifest_path)
        for spec in manifest['import_specifications']:
            if import_name == 'all' or import_name == spec['import_name']:
                import_one(dir_path, spec, run_id, run_id)

    logging.info(absolute_import_name + ': END')
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
    run_id = absolute_import_name
    try:
        return _execute_imports_on_update_helper(absolute_import_name, run_id)
    except Exception as e:
        logging.exception(e)
        mark_system_run_failed(run_id)
        return f'{e}'


def _init_attempt(run_id, import_name, absolute_import_name,
                  provenance_url, provenance_description):
    dashboard = dashboard_api.DashboardAPI()
    return dashboard.init_attempt({
        'run_id': run_id,
        'import_name': import_name,
        'absolute_import_name': absolute_import_name,
        'provenance_url': provenance_url,
        'provenance_description': provenance_description
    })


def _import_one_helper(dir_path, import_spec, run_id, attempt_id):
    cwd = os.getcwd()
    os.chdir(dir_path)

    dashboard = dashboard_api.DashboardAPI()

    urls = import_spec.get('data_download_url')
    if urls:
        for url in urls:
            utils.download_file(url, '.')
            dashboard.info(f'Downloaded: {url}', attempt_id=attempt_id)

    with tempfile.TemporaryDirectory() as tmpdir:
        interpreter_path, process = create_venv(configs.REQUIREMENTS_FILENAME,
                                                tmpdir)
        log = dashboard_api.construct_log(
            'Installing dependencies',
            process=process, run_id=run_id, attempt_id=attempt_id)
        dashboard.log(log)
        process.check_returncode()

        script_paths = import_spec.get('scripts')
        for path in script_paths:
            process = run_user_script(interpreter_path, path)
            log = dashboard_api.construct_log(
                f'Running {path}',
                process=process, run_id=run_id, attempt_id=attempt_id)
            dashboard.log(log)
            process.check_returncode()

    time = utils.utctime()
    path_prefix = f'{dir_path}_{import_spec["import_name"]}/{time}'
    import_inputs = import_spec.get('import_inputs', [])
    for i, import_input in enumerate(import_inputs):

        bucket_io = gcs_io.GCSBucketIO()

        template_mcf = import_input.get('template_mcf')
        cleaned_csv = import_input.get('cleaned_csv')
        node_mcf = import_input.get('node_mcf')
        if template_mcf:
            with open(template_mcf) as f:
                dashboard.info(f'Generated template MCF: {f.readline()}',
                               attempt_id=attempt_id)
            bucket_io.upload_file(
                template_mcf,
                f'{path_prefix}/{os.path.basename(template_mcf)}')

        if cleaned_csv:
            with open(cleaned_csv) as f:
                dashboard.info(f'Generated cleaned CSV: {f.readline()}',
                               attempt_id=attempt_id)
            bucket_io.upload_file(
                cleaned_csv,
                f'{path_prefix}/{os.path.basename(cleaned_csv)}')

        if node_mcf:
            with open(node_mcf) as f:
                dashboard.info(f'Generated node MCF: {f.readline()}',
                               attempt_id=attempt_id)
            bucket_io.upload_file(
                node_mcf,
                f'{path_prefix}/{os.path.basename(node_mcf)}')

    os.chdir(cwd)


def import_one(dir_path, import_spec, run_id, attempt_id):
    """Executes an import.

    Args:
        dir_path: Path to the direcotry containing the manifest as a string.
        import_spec: Specification of the import as a dict.
        run_id: ID of the system run the import belongs to.
        attempt_id: Attempt ID.
    """
    try:
        return _import_one_helper(dir_path, import_spec, run_id, attempt_id)
    except Exception as e:
        mark_import_attempt_failed(attempt_id)
        raise e

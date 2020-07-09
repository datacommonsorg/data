import re
import json
import logging
import os
import subprocess
import tempfile

import requests

from app import configs
from app.service import dashboard_api
from app.service import github_api
from app.service import gcs_io
from app.executor import validation
from app import utils


def parse_manifest(path):
    with open(path, 'r') as file:
        return json.load(file)


def parse_commit_message_targets(commit_message):
    targets = re.findall(
        r'(?:IMPORTS=)((?:[a-zA-Z\d])(?:,[a-zA-Z\d]+)*)',
        commit_message).split(',')
    return list(set(targets))


def create_venv(requirements_path, venv_dir):
    with tempfile.NamedTemporaryFile(mode='w+', suffix='.sh') as bash_script:
        create_template = 'python3 -m virtualenv --verbose --clear {}\n'
        activate_template = '. {}/bin/activate\n'
        pip_template = 'python3 -m pip install --verbose --no-cache-dir --requirement {}\n'
        bash_script.write(create_template.format(venv_dir))
        bash_script.write(activate_template.format(venv_dir))
        bash_script.write(pip_template.format(requirements_path))
        bash_script.flush()

        process = subprocess.run(
            ['bash', bash_script.name], check=True, capture_output=True)
    return os.path.join(venv_dir, 'bin/python'), process


def run_user_script(script_path, interpreter_path):
    return subprocess.run([interpreter_path, script_path], check=True, capture_output=True)


def execute_imports(task_info):
    client_id = configs.get_dashboard_oauth_client_id()

    valid, err = validation.task_info_valid(task_info)
    if not valid:
        return err

    repo_name = task_info['REPO_NAME']
    commit_sha = task_info['COMMIT_SHA']
    branch_name = task_info['BRANCH_NAME']
    pr_number = task_info['PR_NUMBER']

    run = dashboard_api.init_run(
        client_id,
        {
            'repo_name': repo_name,
            'branch_name': branch_name,
            'pr_number': pr_number,
            'commit_sha': commit_sha
        })
    run_id = run['run_id']


    auth_access_token = configs.get_github_auth_access_token()

    commit_info = github_api.query_commit(
        configs.REPO_OWNER_USERNAME, repo_name, commit_sha, configs.GITHUB_AUTH_USERNAME, auth_access_token)

    commit_author_username = commit_info['author']['login']
    commit_message = commit_info['commit']['message']

    manifest_dirs = github_api.find_dirs_in_commit_containing_file(
        configs.REPO_OWNER_USERNAME, repo_name, commit_sha, configs.MANIFEST_FILENAME, configs.GITHUB_AUTH_USERNAME, auth_access_token)
    import_targets = parse_commit_message_targets(commit_message)
    valid, err = validation.import_targets_valid(import_targets, manifest_dirs)
    if not valid:
        return err

    with tempfile.TemporaryDirectory() as tmpdir:
        repo_dirname = github_api.download_repo(configs.REPO_OWNER_USERNAME, repo_name, commit_sha, tmpdir, configs.GITHUB_AUTH_USERNAME, auth_access_token)
        cwd = os.path.join(tmpdir, repo_dirname)
        os.chdir(cwd)

        dashboard_api.log_info(client_id, f'Downloaded repo: ' + repo_dirname, run_id=run_id)

        import_all = 'all' in import_targets
        for dir_path in manifest_dirs:
            manifest_path = os.path.join(dir_path, configs.MANIFEST_FILENAME)
            manifest = parse_manifest(manifest_path)
            for spec in manifest['import_specifications']:
                import_name = spec['import_name']
                absolute_name = utils.get_absolute_import_name(dir_path, import_name)
                if import_all or absolute_name in import_targets or import_name in import_targets:
                    import_one(dir_path, spec, commit_sha, client_id, run_id)

    return 'success'


def import_one(dir_path, import_spec, commit_sha, client_id, run_id):
    import_name = import_spec['import_name']
    attempt = dashboard_api.init_attempt(
        client_id,
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
            dashboard_api.log_info(client_id, 'Downloaded: ' + url, attempt_id=attempt_id)

    with tempfile.TemporaryDirectory() as tmpdir:
        interpreter_path, process = create_venv(configs.REQUIREMENTS_FILENAME, tmpdir)
        dashboard_api.log_info(client_id, 'Installed dependencies: ' + process.stdout, attempt_id=attempt_id)

        script_paths = import_spec.get('scripts')
        for path in script_paths:
            process = run_user_script(path, interpreter_path)
            dashboard_api.log_info(client_id, f'Run {path}: {process.stdout}', attempt_id=attempt_id)


    import_inputs = import_spec.get('import_inputs', [])
    for import_input in import_inputs:
        template_mcf = import_input.get('template_mcf')
        cleaned_csv = import_input.get('cleaned_csv')
        node_mcf = import_input.get('node_mcf')

        if template_mcf:
            with open(template_mcf, 'r') as f:
                dashboard_api.log_info(client_id, f'Generated template MCF: {f.readline()}', attempt_id=attempt_id)

        if cleaned_csv:
            with open(cleaned_csv, 'r') as f:
                dashboard_api.log_info(client_id, f'Generated cleaned CSV: {f.readline()}', attempt_id=attempt_id)

        if node_mcf:
            with open(node_mcf, 'r') as f:
                dashboard_api.log_info(client_id, f'Generated node MCF: {f.readline()}', attempt_id=attempt_id)

    os.chdir(cwd)

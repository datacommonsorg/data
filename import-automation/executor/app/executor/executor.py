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
from app.executor import validation
from app.executor import utils


MANIFEST_FILENAME = 'manifest.json'
REPO_OWNER_USERNAME = 'intrepiditee'
VENV_NAME = 'executor_env'
REQUIREMENTS_FILENAME = 'requirements.txt'


def parse_manifest(path):
    with open(path, 'r') as file:
        return json.load(file)


def parse_commit_message_targets(commit_message):
    targets = re.findall('(?<=\\\\)(?:(?:\w+/)+\w+:)?\w+', commit_message)
    return list(set(targets))


def create_venv(venv_name, requirements_path, dest_dir):
    venv_dir = os.path.join(dest_dir, venv_name)
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
    return os.path.join(venv_dir, '/bin/python'), process


def run_user_script(script_path, interpreter_path):
    return subprocess.run([interpreter_path, script_path], check=True, capture_output=True)


def execute_imports(task_info):
    # client_id = configs.get_dashboard_oauth_client_id()
    client_id = 1

    valid, err = validation.task_info_valid(task_info)
    if not valid:
        return err

    repo_name = task_info['REPO_NAME']
    commit_sha = task_info['COMMIT_SHA']
    branch_name = task_info['BRANCH_NAME']
    pr_number = task_info['PR_NUMBER']

    # dashboard_api.dashboard_init_progress(
    #     client_id,
    #     {
    #         'attempt_id': commit_sha,
    #         'branch_name': branch_name,
    #         'repo_name': repo_name,
    #         'pr_number': pr_number
    #     }
    # )

    commit_info = github_api.query_commit(
        REPO_OWNER_USERNAME, repo_name, commit_sha)

    commit_author_username = commit_info['author']['login']
    commit_message = commit_info['commit']['message']

    manifest_dirs = github_api.find_dirs_in_commit_containing_file(
        REPO_OWNER_USERNAME, repo_name, commit_sha, MANIFEST_FILENAME)
    import_targets = parse_commit_message_targets(commit_message)
    valid, err = validation.import_targets_valid(import_targets, manifest_dirs)
    if not valid:
        return err

    with tempfile.TemporaryDirectory() as temp_dir:
        repo_dirname = github_api.download_repo(REPO_OWNER_USERNAME, repo_name, commit_sha, temp_dir.name)
        os.chdir(os.path.join(temp_dir.name, repo_dirname))

        # dashboard_api.dashboard_log_info(client_id, commit_sha, f'Downloaded repo: ' + repo_dirname)

        interpreter_path, process = create_venv(VENV_NAME, REQUIREMENTS_FILENAME, '.')
        # dashboard_api.dashboard_log_info(client_id, commit_sha, f'Installed dependencies: {process.stdout}')

        import_all = 'all' in import_targets
        for dir_path in manifest_dirs:
            manifest_path = os.path.join(dir_path, MANIFEST_FILENAME)
            manifest = parse_manifest(manifest_path)
            for spec in manifest['import_specifications']:
                import_name = spec['import_name']
                absolute_name = utils.get_absolute_import_name(dir_path, import_name)
                if import_all or absolute_name in import_targets or import_name in import_targets:
                    import_one(dir_path, spec, commit_sha, client_id, interpreter_path)


def import_one(dir_path, import_spec, commit_sha, client_id, interpreter_path):
    
    cwd = os.getcwd()
    os.chdir(dir_path)

    # dashboard_api.dashboard_update(client_id, commit_sha, import_progress={
    #     'import_name': import_spec['import_name'],
    #     'provenance_description': import_spec['provenance_description'],
    #     'provenance_url': import_spec['provenance_url']
    # })

    urls = import_spec.get('data_download_url')
    if urls:
        for url in urls:
            utils.download_file(url, '.')

    download_script_path = import_spec.get('data_download_script')
    if download_script_path:
        process = run_user_script(download_script_path, interpreter_path)

    cleaning_script_path = import_spec.get('data_cleaning_script')
    if cleaning_script_path:
        process = run_user_script(cleaning_script_path, interpreter_path)

    os.chdir(cwd)

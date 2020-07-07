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
REQUIREMENTS_FILENAME = 'requirements.txt'


def parse_manifest(path):
    with open(path, 'r') as file:
        return json.load(file)


def parse_commit_message_targets(commit_message):
    targets = re.findall('(?<=\\\\)(?:(?:\w+/)+\w+:)?\w+', commit_message)
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

    auth_username = 'intrepiditee'
    auth_access_token = os.environ['GITHUB_ACCESS_TOKEN']

    commit_info = github_api.query_commit(
        REPO_OWNER_USERNAME, repo_name, commit_sha, auth_username, auth_access_token)

    commit_author_username = commit_info['author']['login']
    commit_message = commit_info['commit']['message']

    manifest_dirs = github_api.find_dirs_in_commit_containing_file(
        REPO_OWNER_USERNAME, repo_name, commit_sha, MANIFEST_FILENAME, auth_username, auth_access_token)
    import_targets = parse_commit_message_targets(commit_message)
    valid, err = validation.import_targets_valid(import_targets, manifest_dirs)
    if not valid:
        return err

    with tempfile.TemporaryDirectory() as tmpdir:
        repo_dirname = github_api.download_repo(REPO_OWNER_USERNAME, repo_name, commit_sha, tmpdir, auth_username, auth_access_token)
        cwd = os.path.join(tmpdir, repo_dirname)
        os.chdir(cwd)

        # dashboard_api.dashboard_log_info(client_id, commit_sha, f'Downloaded repo: ' + repo_dirname)

        # dashboard_api.dashboard_log_info(client_id, commit_sha, f'Installed dependencies: {process.stdout}')

        import_all = 'all' in import_targets
        for dir_path in manifest_dirs:
            manifest_path = os.path.join(dir_path, MANIFEST_FILENAME)
            manifest = parse_manifest(manifest_path)
            for spec in manifest['import_specifications']:
                import_name = spec['import_name']
                absolute_name = utils.get_absolute_import_name(dir_path, import_name)
                if import_all or absolute_name in import_targets or import_name in import_targets:
                    import_one(dir_path, spec, commit_sha, client_id)
    
    return 'success'


def import_one(dir_path, import_spec, commit_sha, client_id):
    
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


    with tempfile.TemporaryDirectory() as tmpdir:
        interpreter_path, process = create_venv(REQUIREMENTS_FILENAME, tmpdir)
        download_script_path = import_spec.get('data_download_script')
        if download_script_path:
            try:
                process = run_user_script(download_script_path, interpreter_path)
            except Exception as e:
                logging.error(e)
                logging.error(e.output)
                logging.error(e.stdout)
                logging.error(e.stderr)

        cleaning_script_path = import_spec.get('data_cleaning_script')
        if cleaning_script_path:
            process = run_user_script(cleaning_script_path, interpreter_path)

    import_inputs = import_spec.get('import_inputs', [])
    for import_input in import_inputs:
        template_mcf = import_input.get('template_mcf')
        cleaned_csv = import_input.get('cleaned_csv')
        node_mcf = import_input.get('node_mcf')

        if template_mcf:
            with open(template_mcf, 'r') as f:
                print(f.readline())

        if cleaned_csv:
            with open(cleaned_csv, 'r') as f:
                print(f.readline())

        if node_mcf:
            with open(node_mcf, 'r') as f:
                print(f.readline())

    os.chdir(cwd)

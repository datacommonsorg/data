import os
import re
import shutil
import tarfile
import tempfile

import requests

GITHUB_API_HOST = 'https://api.github.com'

GITHUB_COMMIT_API = (
    GITHUB_API_HOST +
    '/repos/{owner_username}/{repo_name}/commits/{commit_sha}'
)

GITHUB_CONTENT_API = (
    GITHUB_API_HOST +
    '/repos/{owner_username}/{repo_name}/contents/{dir_path}?ref={commit_sha}'
)

GITHUB_USER_API = GITHUB_API_HOST + '/users/{name}'

GITHUB_DOWNLOAD_API = (
    GITHUB_API_HOST +
    '/repos/{owner_username}/{repo_name}/tarball/{commit_sha}'
)


def _build_commit_query(owner_username, repo_name, commit_sha):
    return GITHUB_COMMIT_API.format_map({
        'owner_username': owner_username,
        'repo_name': repo_name,
        'commit_sha': commit_sha
    })



def _get_auth(auth_username, auth_access_token):
    if not auth_username or not auth_access_token:
        return None
    return (auth_username, auth_access_token)


def query_commit(owner_username, repo_name, commit_sha, auth_username=None, auth_access_token=None):
    commit_query = _build_commit_query(owner_username, repo_name, commit_sha)
    auth = _get_auth(auth_username, auth_access_token)
    response = requests.get(commit_query, auth=auth)
    response.raise_for_status()
    return response.json()


def query_changed_files_in_commit(owner_username, repo_name, commit_sha, auth_username=None, auth_access_token=None):
    commit_info = query_commit(owner_username, repo_name, commit_sha, auth_username, auth_access_token)
    return [entry['filename'] for entry in commit_info['files']]


def query_files_in_dir(owner_username, repo_name, commit_sha, dir_path, auth_username=None, auth_access_token=None):
    content_query = GITHUB_CONTENT_API.format_map({
        'owner_username': owner_username,
        'repo_name': repo_name,
        'commit_sha': commit_sha,
        'dir_path': dir_path
    })
    auth = _get_auth(auth_username, auth_access_token)
    response = requests.get(content_query, auth=auth)
    response.raise_for_status()
    content_info = response.json()
    return [entry['name'] for entry in content_info if entry['type'] == 'file']


def find_dirs_in_commit_containing_file(
    owner_username, repo_name, commit_sha, containing, auth_username=None, auth_access_token=None):
    """
    Example:
            Repository data owned by intrepiditee has a file
            README.md in branch fed at
            data/script/us_fed/treausy_constant_maturity_rates/README.md.

            Commit aa4a2551c7682cdddab46794a406f898862a9d49 to branch fed
            changes some files in
            data/script/us_fed/treausy_constant_maturity_rates and its
            subdirectories.

            This method will pick one of the changed files, e.g.
            data/script/us_fed/treausy_constant_maturity_rates/foo/bar/file,
            and go up one directory by another starting from bar until the
            current directory contains the file we are looking for.

            In this case, script/us_fed/treausy_constant_maturity_rates
            will be returned.
    """
    changed_files = query_changed_files_in_commit(
        owner_username, repo_name, commit_sha, auth_username, auth_access_token)
    found_dirs = set()
    for file_path in changed_files:
        dir_path = os.path.dirname(file_path)
        find_dirs_up_path_containing_file(
            owner_username, repo_name, commit_sha,
            dir_path, containing, found_dirs, auth_username, auth_access_token)
    return list(found_dirs)



def find_dirs_up_path_containing_file(
    owner_username, repo_name, commit_sha, dir_path, containing, found_dirs, auth_username=None, auth_access_token=None):
    while dir_path and dir_path not in found_dirs:
        files_in_dir = query_files_in_dir(
            owner_username, repo_name, commit_sha, dir_path, auth_username, auth_access_token)
        for filename in files_in_dir:
            if filename == containing:
                found_dirs.add(dir_path)
        dir_path = os.path.dirname(dir_path)


def download_repo(owner_username, repo_name, commit_sha, dest_dir, auth_username=None, auth_access_token=None):
    local_filename = commit_sha
    download_query = GITHUB_DOWNLOAD_API.format_map({
        'owner_username': owner_username,
        'repo_name': repo_name,
        'commit_sha': commit_sha
    })

    auth = _get_auth(auth_username, auth_access_token)
    with tempfile.NamedTemporaryFile(suffix='.tar.gz') as temp_file:
        with requests.get(download_query, auth=auth, stream=True) as response:
            shutil.copyfileobj(response.raw, temp_file)
            temp_file.flush()

        with tarfile.open(temp_file.name, 'r') as tar:
            tar.extractall(dest_dir)
            extracted_repo_name = tar.getnames()[0]
    
    return extracted_repo_name

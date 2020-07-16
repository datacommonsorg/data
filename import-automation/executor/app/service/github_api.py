import os
import shutil
import tarfile
import tempfile
import http

import requests

from app import configs

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


class GitHubRepoAPI:
    def __init__(self,
                 owner_username=configs.REPO_OWNER_USERNAME,
                 repo_name=configs.REPO_NAME,
                 auth_username=configs.GITHUB_AUTH_USERNAME,
                 auth_access_token=None):
        self.owner = owner_username
        self.repo = repo_name
        if not auth_access_token:
            auth_access_token = configs.get_github_auth_access_token()
        self.auth = (auth_username, auth_access_token)

    def _build_content_query(self, commit_sha, path):
        return GITHUB_CONTENT_API.format_map({
            'owner_username': self.owner,
            'repo_name': self.repo,
            'commit_sha': commit_sha,
            'dir_path': path
        })

    def _build_commit_query(self, commit_sha):
        return GITHUB_COMMIT_API.format_map({
            'owner_username': self.owner,
            'repo_name': self.repo,
            'commit_sha': commit_sha
        })

    def query_commit(self, commit_sha):
        commit_query = self._build_commit_query(commit_sha)
        response = requests.get(commit_query, auth=self.auth)
        response.raise_for_status()
        return response.json()

    def query_changed_files_in_commit(self, commit_sha):
        """Finds the paths of files changed by a commit.

        Example:
            Assume commit '12f23f1eeg234' to rhe repository modifies
            'scripts/README.md', adds 'scripts/us_fed/README.md', and removes
            'utils/foo.py'.

            The method call
                query_changed_files_in_commit('12f23f1eeg234')
            returns [
                ('scripts/README.md', 'modified'),
                ('scripts/us_fed/README.md', 'added'),
                ('utils/foo.py', 'removed')
            ]

        Args:
            commit_sha: Commit ID as a string.

        Returns:
            A list of tuples each of the form (<path>, <status>), where <path>
            is the path to the file in the repository and <status> indicates
            how the file is changed.
        """
        commit_info = self.query_commit(commit_sha)
        files = []
        for entry in commit_info['files']:
            files.append((entry['filename'], entry['status']))
        return files

    def query_files_in_dir(self, commit_sha, dir_path):
        content_query = GITHUB_CONTENT_API.format_map({
            'owner_username': self.owner,
            'repo_name': self.repo,
            'commit_sha': commit_sha,
            'dir_path': dir_path
        })
        response = requests.get(content_query, auth=self.auth)
        response.raise_for_status()
        content_info = response.json()
        return [entry['name'] for entry in content_info if entry['type'] == 'file']

    def _dir_exists(self, commit_sha, dir_path):
        """Checks whether a directory still exists in the repository
        after a commit.

        Args:
            commit_sha: Commit ID as a string
            dir_path: Path to the directory to check as a string.

        Returns:
            True if the directory exists. False, otherwise.
        """
        content_query = self._build_content_query(commit_sha, dir_path)
        response = requests.get(content_query, auth=self.auth)
        ok = response.status_code == http.HTTPStatus.OK
        not_found = response.status_code == http.HTTPStatus.NOT_FOUND
        if not ok and not not_found:
            response.raise_for_status()
        return response.status_code != http.HTTPStatus.NOT_FOUND

    def find_dirs_in_commit_containing_file(self, commit_sha, containing):
        """
        Example:
            Assume the repository has a file README.md at foo/bar/README.md and
            at README.md.

            Commit 1r9f121 changes some files in foo/bar and its
            subdirectories, say foo/bar/a/b/c/file.

            The method call
                find_dirs_in_commit_containing_file('1r9f121', 'README.md')
            climbs up the paths of the changed files to look for directories
            that contain a file named 'README.md'. For foo/bar/a/b/c/file,
            foo/bar/a/b/c is first searched, followed by foo/bar/a/b,
            foo/bar/a, foo/bar, and foo in order.
            ['foo/bar', ''] will be returned.

            In this case, script/us_fed/treausy_constant_maturity_rates
            will be returned.
        """
        changed_files = self.query_changed_files_in_commit(commit_sha)
        found_dirs = set()
        searched = set()
        for file_path, status in changed_files:
            dir_path = os.path.dirname(file_path)
            exist = self._dir_exists(commit_sha, dir_path)
            if status == 'removed' and not exist:
                continue

            found_dirs.update(self._find_dirs_up_path_containing_file(
                commit_sha, dir_path, containing, searched))

        return list(found_dirs)

    def _path_containing_file(self, commit_sha, dir_path, containing):
        """Checks if the directory in the repository contains a file.

        Example:
            There is a README.md in foo/bar when commit '21d12fr2' happens.
            The method call
                _path_containing_file('21d12fr2', 'foo/bar', 'README.md')
            returns True.

        Args:
            commit_sha: Commit ID as a string.
            dir_path: Path of the directory to search in as a string.
            containing: Name of the file to search for as a string.

        Returns:
            True if the directory contains a file with the given name. False,
            otherwise.
        """
        files_in_dir = self.query_files_in_dir(commit_sha, dir_path)
        for filename in files_in_dir:
            if filename == containing:
                return True
        return False

    def _find_dirs_up_path_containing_file(
            self, commit_sha, dir_path, containing, searched):
        """Given a path pointing at a directory in the repository, searches for
        a file in the directory and its parent directories.

        Example:
            Assume the repository has a subdirectory called 'scripts' and
            'scripts' has a subdirectory called 'us_fed'.
            There is a 'README.md' in the root directory of the repository and
            another in 'us_fed'.

            The method call
                _find_dirs_up_path_containing_file(
                    'dw1f231asdf1321', scripts/us_fed', 'README.md', set())
            first searches in 'us_fed' and adds 'scripts/us_fed' to
            'found_dirs'. It then searches in 'scripts' and the root directory
            of the repository.
            {'scripts/us_fed', ''} is returned.

        Args:
            commit_sha: Commit ID as a string.
            dir_path: Path to the directory where the search begins as a string.
            containing: Filename to search for as a string.
            searched: Set object containng paths of directories to skip over.
                If a directory is already in 'searched', it and its parent
                directories will not be searched. Directories searched this
                time are also added to it.

        Returns:
            A list of directory paths each as a string.
        """
        found_dirs = set()
        while dir_path:
            if dir_path in searched:
                return found_dirs
            searched.add(dir_path)
            if self._path_containing_file(commit_sha, dir_path, containing):
                found_dirs.add(dir_path)
            dir_path = os.path.dirname(dir_path)

        # Search root
        if '' not in searched:
            searched.add('')
            if self._path_containing_file(commit_sha, '', containing):
                found_dirs.add('')
        return found_dirs

    def download_repo(self, dest_dir, commit_sha=None):
        """Downloads the repository.

        Example:
            Assume the repository is named 'data-demo' owned by 'intrepiditee'.
            The method call
                download_repo('download_dir', '12ef23231a')
            returns 'download_dir/intrepiditee-data-demo-12ef23231a'.

        Args:
            dest_dir: Directory to download the repository into as a string.
            commit_sha: Commit ID that defines the version of the repository
                to download as a string. If not supplied, the master branch
                is downloaded.

        Returns:
            Path to the downloaded repository as a string.
        """
        if not commit_sha:
            commit_sha = ''
        download_query = GITHUB_DOWNLOAD_API.format_map({
            'owner_username': self.owner,
            'repo_name': self.repo,
            'commit_sha': commit_sha
        })

        with tempfile.NamedTemporaryFile(suffix='.tar.gz') as temp_file:
            with requests.get(download_query, auth=self.auth, stream=True) as response:
                response.raise_for_status()
                shutil.copyfileobj(response.raw, temp_file)
                temp_file.flush()

            with tarfile.open(temp_file.name) as tar:
                files = tar.getnames()
                if not files:
                    raise FileNotFoundError(
                        'Downloaded tar file does not contain the repository')
                tar.extractall(dest_dir)
                return os.path.commonpath(files)

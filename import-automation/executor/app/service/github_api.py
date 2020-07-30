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
GitHub API client for querying information about a repository.
"""

import os
import tarfile
import tempfile
import http
from typing import Dict, Set, List

import requests

from app import utils

_GITHUB_API_HOST = 'https://api.github.com'

_GITHUB_COMMIT_API = (_GITHUB_API_HOST +
                     '/repos/{owner_username}/{repo_name}/commits/{commit_sha}')

_GITHUB_CONTENT_API = (
        _GITHUB_API_HOST +
    '/repos/{owner_username}/{repo_name}/contents/{dir_path}?ref={commit_sha}')

_GITHUB_USER_API = _GITHUB_API_HOST + '/users/{name}'

_GITHUB_DOWNLOAD_API = (
        _GITHUB_API_HOST +
    '/repos/{owner_username}/{repo_name}/tarball/{commit_sha}')


class GitHubRepoAPI:
    """GitHub API client for querying information about a repository.

    Attributes:
        owner: Username of the owner of the repository as a string.
        repo: Name of the repository as a string.
        auth: Tuple consisting of the username of the account to authenticate
            with GitHub and the access token.
    """
    def __init__(self,
                 repo_owner_username: str,
                 repo_name: str,
                 auth_username: str = '',
                 auth_access_token: str = ''):
        self.owner = repo_owner_username
        self.repo = repo_name
        self.auth = (auth_username, auth_access_token)

    def query_commit(self, commit_sha: str) -> Dict:
        """Queries the information about a commit to the repository.

        Args:
            commit_sha: ID of the commit as a string.

        Returns:
            Information about the commit as a dict.
        """
        commit_query = self._build_commit_query(commit_sha)
        response = requests.get(commit_query, auth=self.auth)
        response.raise_for_status()
        return response.json()

    def find_dirs_in_commit_containing_file(self, commit_sha: str,
                                            containing: str) -> Set[str]:
        """Finds the directories and their parent directories touched by a
        commit that contain a specific file.

        Example:
            Assume the repository has a file README.md at foo/bar/README.md and
            at ./README.md.

            Commit 1r9f121 changes some files in foo/bar and its
            subdirectories, say foo/bar/a/b/c/file.

            The method call
                find_dirs_in_commit_containing_file('1r9f121', 'README.md')
            climbs up the paths of the changed files to look for directories
            that contain a file named 'README.md'. For foo/bar/a/b/c/file,
            foo/bar/a/b/c is first searched, followed by foo/bar/a/b,
            foo/bar/a, foo/bar, and foo in order.
            ['foo/bar', ''] will be returned.

        Args:
            commit_sha: ID of the commit as a string.
            containing: Name of the file to look for, as a string.

        Returns:
            Set of directory paths each as a string. The paths are relative
            to the root directory of the repository.
        """
        changed_files = self._query_changed_files_in_commit(commit_sha)
        found_dirs = set()
        searched = set()
        for file_path, status in changed_files:
            dir_path = os.path.dirname(file_path)
            exist = self._dir_exists(commit_sha, dir_path)
            if status == 'removed' and not exist:
                continue
            found_dirs.update(
                self._find_dirs_up_path_containing_file(commit_sha, dir_path,
                                                        containing, searched))
        return found_dirs

    def download_repo(self,
                      dest_dir: str,
                      commit_sha: str = None,
                      timeout: float = None) -> str:
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
            timeout: Maximum time downloading the repository can take in
                seconds, as a float. The actual timeout will be a rough
                approximation to this, likely several seconds larger.

        Returns:
            Path to a directory containing the downloaded repository,
            as a string. The repository's contents are downloaded and copied
            into the same directory structure within the returned directory.

        Raises:
            requests.Timeout: Downloading timed out.
        """
        if not commit_sha:
            commit_sha = ''
        download_query = _GITHUB_DOWNLOAD_API.format_map({
            'owner_username': self.owner,
            'repo_name': self.repo,
            'commit_sha': commit_sha
        })

        with tempfile.TemporaryDirectory() as tmpdir:
            repo_tar = utils.download_file(download_query, tmpdir, timeout)
            with tarfile.open(repo_tar) as tar:
                files = tar.getnames()
                if not files:
                    raise FileNotFoundError(
                        'Downloaded tar file does not contain the repository')
                tar.extractall(dest_dir)
                return os.path.join(dest_dir,
                                    _get_path_first_component(files[0]))

    def _build_content_query(self, commit_sha: str, path: str) -> str:
        """Formats the URL for querying the contents of a directory at the
        state of a commit.

        Args:
            commit_sha: ID of the commit as a string.
            path: Path to the directory as a string, relative to the root
                directory of the repository.

        Returns:
            URL as a string.
        """
        return _GITHUB_CONTENT_API.format_map({
            'owner_username': self.owner,
            'repo_name': self.repo,
            'commit_sha': commit_sha,
            'dir_path': path
        })

    def _build_commit_query(self, commit_sha: str) -> str:
        """Formats the URL for querying information about a commit.

        Args:
            commit_sha: ID of the commit as a string.

        Returns:
            URL as a string.
        """
        return _GITHUB_COMMIT_API.format_map({
            'owner_username': self.owner,
            'repo_name': self.repo,
            'commit_sha': commit_sha
        })

    def _query_changed_files_in_commit(self,
                                       commit_sha: str) -> List[str]:
        """Finds the paths of files changed by a commit.

        Example:
            Assume commit '12f23f1eeg234' to rhe repository modifies
            'scripts/README.md', adds 'scripts/us_fed/README.md', and removes
            'utils/foo.py'.

            The method call
                _query_changed_files_in_commit('12f23f1eeg234')
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

    def _query_files_in_dir(self, commit_sha: str,
                            dir_path: str) -> List[str]:
        """Queries the files in a directory at the state of a commit.

        Only files are returned, not directories.

        Args:
            commit_sha: ID of the commit as a string.
            dir_path: Path to the directory as a string, relative to the root
                directory of the repository.

        Returns:
            List of relative paths to the files, each as a string.
        """
        content_query = _GITHUB_CONTENT_API.format_map({
            'owner_username': self.owner,
            'repo_name': self.repo,
            'commit_sha': commit_sha,
            'dir_path': dir_path
        })
        response = requests.get(content_query, auth=self.auth)
        response.raise_for_status()
        content_info = response.json()
        return [
            entry['name'] for entry in content_info if entry['type'] == 'file'
        ]

    def _dir_exists(self, commit_sha: str, dir_path: str) -> bool:
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
        is_ok = response.status_code == http.HTTPStatus.OK
        is_not_found = response.status_code == http.HTTPStatus.NOT_FOUND
        if not is_ok and not is_not_found:
            response.raise_for_status()
        return response.status_code != http.HTTPStatus.NOT_FOUND

    def _path_containing_file(self, commit_sha: str, dir_path: str,
                              containing: str) -> bool:
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
        files_in_dir = self._query_files_in_dir(commit_sha, dir_path)
        for filename in files_in_dir:
            if filename == containing:
                return True
        return False

    def _find_dirs_up_path_containing_file(
            self, commit_sha: str, dir_path: str, containing: str,
            searched: Set[str]) -> Set[str]:
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
            A set of directory paths each as a string.
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


def _get_path_first_component(path: str) -> str:
    """Returns the first component of a path.

    Example:
        _get_path_first_component('data/foo/bar/README.md') returns 'data'.
        _get_path_first_component('/data/foo/bar/README.md') returns ''.
        _get_path_first_component('data') returns 'data'.
         _get_path_first_component('') returns ''.
    """
    index = path.find(os.path.sep)
    if index != -1:
        return path[:index]
    return path

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
GitHub API client for downloading a repository.
"""

import logging
import os
import tarfile
import tempfile

from app import utils

_GITHUB_API_HOST = 'https://api.github.com'

_GITHUB_DOWNLOAD_API = (
    _GITHUB_API_HOST +
    '/repos/{owner_username}/{repo_name}/tarball/{commit_sha}')


class GitHubRepoAPI:
    """GitHub API client for downloading a repository.

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
        """Constructs a GitHubRepoAPI.

        Args:
            repo_owner_username: See owner in Attributes.
            repo_name: See repo in Attributes.
            auth_username: The username of the account to authenticate
                with GitHub, as a string.
            auth_access_token: The corresponding access token as a string.
        """
        self.owner = repo_owner_username
        self.repo = repo_name
        self.auth = (auth_username, auth_access_token)
        logging.info('GitHubRepoAPI.__init__: Initialized with repository %s',
                     self._format_repo_name())

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
        logging.info(
            'GitHubRepoAPI.download_repo: '
            'Downloading repository %s at commit %s to %s',
            f'{self._format_repo_name()}', commit_sha, dest_dir)
        if not commit_sha:
            commit_sha = ''
        download_query = _GITHUB_DOWNLOAD_API.format_map({
            'owner_username': self.owner,
            'repo_name': self.repo,
            'commit_sha': commit_sha
        })

        with tempfile.TemporaryDirectory() as tmpdir:
            repo_tar = utils.download_file(download_query, tmpdir, timeout)
            logging.info('GitHubRepoAPI.download_repo: Downloaded tar %s',
                         repo_tar)
            with tarfile.open(repo_tar) as tar:
                files = tar.getnames()
                if not files:
                    raise FileNotFoundError(
                        'Downloaded tar file does not contain the repository')
                tar.extractall(dest_dir)
                repo_dir = os.path.join(dest_dir,
                                        _get_path_first_component(files[0]))
                logging.info(
                    'GitHubRepoAPI.download_repo: '
                    'Extracted repository %s', repo_dir)
                return repo_dir

    def _format_repo_name(self):
        """Returns {self.owner}/{self.repo}."""
        return f'{self.owner}/{self.repo}'


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

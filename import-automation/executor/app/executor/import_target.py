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
Import targets specified in the commit message are of the form:
1) <path to directory containing the manifest>:<import name>
    The import with the import name in the directory is executed.
2) <import name>
    The import with the import name in the only directory touched by the
    import is executed.
3) <path to directory containing the manifest>:all
    All imports in the directory are executed.
4) all
    All imports in directories touched by the commit are executed.
"""

import os
import re
from typing import List, Tuple, Dict, Set

from app import utils
from app.service import github_api
from app.executor import validation
from app.executor import import_executor

_ALLOWED_PATH_CHARS = 'A-Za-z0-9-_/'
_ALLOWED_RELATIVE_IMPORT_NAME_CHARS = 'A-Za-z0-9-_'
_ALLOWED_ABSOLUTE_IMPORT_NAME_CHARS = (
    f'{_ALLOWED_PATH_CHARS}:'
    f'{_ALLOWED_RELATIVE_IMPORT_NAME_CHARS}')
_ABSOLUTE_IMPORT_NAME_REGEX = r'[{}]+:[{}]+'.format(
    _ALLOWED_PATH_CHARS, _ALLOWED_RELATIVE_IMPORT_NAME_CHARS)
_RELATIVE_IMPORT_NAME_REGEX = r'[{}]+'.format(
    _ALLOWED_RELATIVE_IMPORT_NAME_CHARS)
_IMPORT_NAME_REGEX = r'{}|{}'.format(_ABSOLUTE_IMPORT_NAME_REGEX,
                                     _RELATIVE_IMPORT_NAME_REGEX)


def get_absolute_import_name(dir_path: str, import_name: str) -> str:
    """Joins a relative import path with an import name."""
    return f'{dir_path}:{import_name}'


def is_absolute_import_name(import_name: str) -> bool:
    """Checks if an import name is absolute."""
    return re.fullmatch(_ABSOLUTE_IMPORT_NAME_REGEX, import_name) is not None


def is_relative_import_name(import_name: str) -> bool:
    """Checks if an import name is relative."""
    return re.fullmatch(_RELATIVE_IMPORT_NAME_REGEX, import_name) is not None


def split_absolute_import_name(import_name: str) -> List[str]:
    """Splits an absolute import name into a relative import path and an
    import name."""
    return import_name.split(':')


def filter_relative_import_names(import_names: List[str]) -> List[str]:
    """Given a list of import names, filters out the relative import names."""
    return list(name for name in import_names if is_relative_import_name(name))


def filter_absolute_import_names(import_names):
    """Given a list of import names, filters out the absolute import names."""
    return list(name for name in import_names if is_absolute_import_name(name))


def parse_commit_message_targets(commit_message: str,
                                 tag: str = 'IMPORTS') -> List[str]:
    """Parses the targets from a commit message.

    Targets are specified by including a comma separated list of
    import names in the commit message using a tag such as IMPORTS.
    The format is <tag>=<import name>[,<import name>...]. E.g.,
    'IMPORTS=scripts/us_fed:treasury,scripts/us_bls:cpi' and
    'SCHEDULES=treasury'.

    There cannot be spaces between import names or a comma at the
    end of the list. E.g.,
    'IMPORTS=scripts/us_fed:treasury, scripts/us_bls:cpi' and
    'SCHEDULES=treasury,' are invalid.

    Args:
        commit_message: GitHub commit message as a string.
        tag: The tag that starts the list, as a string.

    Returns:
        A list of import names each as a string.
    """
    targets = utils.parse_tag_list(commit_message, tag,
                                   _ALLOWED_ABSOLUTE_IMPORT_NAME_CHARS)
    for target in targets:
        if (not target or target.isspace()
                or (not is_absolute_import_name(target)
                    and not is_relative_import_name(target))):
            raise ValueError(f'Target "{target}" is not valid')
    return targets


def is_import_targetted_by_commit(import_dir: str, import_name: str,
                                  import_targets: List[str]) -> bool:
    """Checks if an import should be executed upon the commit.

    See module docstring for the rules.

    Args:
        import_dir: Path to the directory containing the manifest as a string,
            relative to the root directory of the repository.
        import_name: Name of the import in the manifest as a string.
        import_targets: List of relative and absolute import names each as
            a string parsed from the commit message.

    Returns:
        True, if the import should be executed. False, otherwise.
    """
    absolute_name = get_absolute_import_name(import_dir, import_name)
    absolute_all = get_absolute_import_name(import_dir, 'all')
    return ('all' in import_targets or absolute_name in import_targets
            or import_name in import_targets or absolute_all in import_targets)


def find_targets_in_commit(commit_sha: str, tag: str,
                           github: github_api.GitHubRepoAPI) -> List[str]:
    """Finds the targets specified in the commit message of a GitHub commit.

    Args:
        commit_sha: ID of the commit as a string.
        tag: The tag used to specify the list of targets, as a string.
        github: GitHubRepoAPI object for querying the GitHub API.

    Returns:
        List of import names each as a string.
    """
    commit_info = github.query_commit(commit_sha)
    commit_message = commit_info['commit']['message']
    return parse_commit_message_targets(commit_message, tag)


def find_imports_to_execute(targets: List[str], manifest_dirs: Set[str],
                            manifest_filename: str,
                            repo_dir: str) -> List[Tuple[str, Dict]]:
    """Finds imports to execute on a GitHub commit.

    Args:
        targets: List of import targets specified by the commit message each as
            a string.
        manifest_dirs: Set of subdirectories of the repository touched by the
            commit each as a string.
        manifest_filename: Filename of the manifest as a string.
        repo_dir: Absolute path to the repository as a string.

    Returns:
        List of tuples each consisting of 1) the path, as a string, to the
        directory containing an import to execute, relative to the root
        directory of the repository and 2) the import specification, as a dict,
        of the import to execute.

    Raises:
        ValueError: The import targets are not valid (see
            are_import_targets_valid) or the manifest is not valid (see
            is_manifest_valid).
    """
    validation.are_import_targets_valid(targets, list(manifest_dirs), repo_dir,
                                        manifest_filename)

    # Import targets specified in the commit message can be absolute,
    # e.g., 'scripts/us_fed/treasury:constant_maturity'.
    # Add the directory components, e.g., 'scripts/us_fed/treasury',
    # to manifest_dirs.
    manifest_dirs = set(manifest_dirs)
    for target in filter_absolute_import_names(targets):
        import_dir, _ = split_absolute_import_name(target)
        manifest_dirs.add(import_dir)
    # At this point, manifest_dirs contains all the directories that
    # will be looked at to look for imports.

    imports_to_execute = []
    for import_dir in manifest_dirs:
        absolute_import_dir = os.path.join(repo_dir, import_dir)
        manifest_path = os.path.join(absolute_import_dir, manifest_filename)
        manifest = import_executor.parse_manifest(manifest_path)
        validation.is_manifest_valid(manifest, repo_dir, import_dir)

        for spec in manifest['import_specifications']:
            if not is_import_targetted_by_commit(import_dir,
                                                 spec['import_name'], targets):
                continue
            imports_to_execute.append((import_dir, spec))
    return imports_to_execute

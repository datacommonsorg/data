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
Functions for validating import targets specified in commit messages, manifests,
and import specifications.
"""

import os
import typing

from app import utils
from app.executor import import_executor
from app.executor import import_target

_TASK_INFO_REQUIRED_FIELDS = [
    'REPO_NAME', 'BRANCH_NAME', 'COMMIT_SHA', 'PR_NUMBER'
]
_MANIFEST_REQUIRED_FIELDS = ['import_specifications']
_IMPORT_SPECIFICATION_REQUIRED_FIELDS = [
    'import_name', 'provenance_url', 'provenance_description', 'curator_emails'
]


def is_task_info_valid(task_info: typing.Dict):
    """Ensures that the task info sent to the app is valid.

    Checks that required fields are present. Not currently used.

    Args:
        task_info: The task info to check as a dict.

    Raises:
        ValueError: The task info is not valid.
    """
    missing_keys = _filter_missing_keys(_TASK_INFO_REQUIRED_FIELDS, task_info)
    if missing_keys:
        raise ValueError(f'Missing {utils.list_to_str(missing_keys)} in '
                         f'task info {task_info}')


def are_import_targets_valid(import_targets: typing.List[str],
                             manifest_dirs: typing.List[str], repo_dir: str,
                             manifest_filename: str) -> None:
    """Ensures that the import targets specified in the commit message
    are valid.

    Checks that:
    If the commit touches multiple directories:
        1) Only absolute import names are used, with the exception of 'all'.
        2) The manifests exist.
        3) Imports pointed to by the absolute import names exist in the
           manifests.
    If the commit only touches one directory:
        1) The manifests exist.
        2) Imports pointed to by the absolute import names exist in the
           manifests.
        2) Imports pointed to by the relative import names exist in the
           manifest in the touched directory.

    Args:
        import_targets: List of import targets each as a string parsed from
            the commit message.
        manifest_dirs: List of relative paths to directories touched by the
            commit containing manifests, each as a string.
        repo_dir: Absolute path to the repository as a string.
        manifest_filename: Filename of the manifest.

    Raises:
        ValueError: Some of the targets are not valid.
    """
    relative_names = import_target.filter_relative_import_names(import_targets)
    if ('all' not in import_targets and len(manifest_dirs) > 1 and
            relative_names):
        raise ValueError('Commit touched multiple directories '
                         f'({manifest_dirs}) but {relative_names} '
                         'are relative import names')
    if len(manifest_dirs) == 1:
        import_dir = manifest_dirs[0]
        for import_name in relative_names:
            _import_name_exists_in_manifest(repo_dir, import_dir, import_name,
                                            manifest_filename)

    absolute_names = import_target.filter_absolute_import_names(import_targets)
    for absolute_name in absolute_names:
        import_dir, import_name = import_target.split_absolute_import_name(
            absolute_name)
        _import_name_exists_in_manifest(repo_dir, import_dir, import_name,
                                        manifest_filename)


def is_manifest_valid(manifest: typing.Dict, repo_dir: str,
                      import_dir: str) -> None:
    """Ensures that the manifest is valid.

    Checks that:
        1) Required fields are present.
        2) Each import specification is valid. See _is_import_spec_valid.

    Args:
        manifest: The manifest to check as a dict.
        repo_dir: Absolute path to the repository.
        import_dir: Path to the directory containing the manifest, relative
            to the root directory of the repository, as a string.

    Raises:
        ValueError: THe manifest is not valid.
    """
    missing_keys = _filter_missing_keys(_MANIFEST_REQUIRED_FIELDS, manifest)
    if missing_keys:
        raise ValueError(f'Missing {utils.list_to_str(missing_keys)} in '
                         f'manifest ({manifest})')
    for spec in manifest['import_specifications']:
        _is_import_spec_valid(spec, repo_dir, import_dir)


def _get_import_names_in_manifest(manifest: typing.Dict) -> typing.List[str]:
    """Gets all the import names in the manifest.

    The manifest should have an import_specification field whose values are
    dicts and have an import_name field.

    Args:
        manifest: The manifest as a dict.

    Returns:
        List of import names in the manifest each as a string.
    """
    return [
        spec.get('import_name')
        for spec in manifest.get('import_specifications', [])
    ]


def _import_name_exists_in_manifest(repo_dir, import_dir, import_name,
                                    manifest_filename):
    """Ensures that an import name exists in one of the import specifications
    in a manifest.

    The manifest is read from <repo_dir>/<import_dir>/<manifest_filename>.

    Args:
        repo_dir: Absolute path to the repository as a string.
        import_dir: Path to the directory containing the manifest, relative to
            the root directory of the repository as a string.
        import_name: Import name to check as a string.
        manifest_filename: Filename of the manifest as a string.

    Raises:
        ValueError: The manifest does not exist or the import name is not found
            in the manifest.
    """
    try:
        manifest = import_executor.parse_manifest(
            os.path.join(repo_dir, import_dir, manifest_filename))
    except FileNotFoundError:
        raise ValueError(
            f'{os.path.join(import_dir, manifest_filename)} does not exist')
    if (import_name != 'all' and
            import_name not in _get_import_names_in_manifest(manifest)):
        raise ValueError(f'{import_name} not found in '
                         f'{os.path.join(import_dir, manifest_filename)}')


def _is_import_spec_valid(import_spec, repo_dir, import_dir):
    """Ensures that the import specification is valid.

    Checks that:
        1) Required fields are present.
        2) Script paths exist.

    Args:
        import_spec: The import specification to check as a dict.
        repo_dir: Absolute path to the repository.
        import_dir: Path to the directory with the manifest that contains the
            import specification, relative to the root directory of
            the repository, as a string.

    Raises:
        ValueError: THe import specification is not valid.
    """
    missing_keys = _filter_missing_keys(_IMPORT_SPECIFICATION_REQUIRED_FIELDS,
                                        import_spec)
    if missing_keys:
        raise ValueError(f'Missing {utils.list_to_str(missing_keys)} in '
                         f'import specification ({import_spec})')

    absolute_script_paths = [
        os.path.join(repo_dir, import_dir,
                     path.split(' ')[0])
        for path in import_spec.get('scripts', [])
        if path
    ]
    missing_paths = _filter_missing_paths(absolute_script_paths)
    if missing_paths:
        raise ValueError(f'{utils.list_to_str(missing_paths)} not found')


def _filter_missing_paths(paths: typing.List[str]) -> typing.List[str]:
    """Given a list of paths, returns the paths that point to files and
    directories that do not exist.

    Raises:
        Same exceptions as os.path.exists.
    """
    return list(path for path in paths if not os.path.exists(path))


def _filter_missing_keys(keys: typing.Any,
                         a_dict: typing.Dict) -> typing.List[typing.Any]:
    """Given a list of keys each as a string and a dict, returns the keys in
    the list that are not present in the dict or have empty values."""
    return list(key for key in keys if not a_dict.get(key))

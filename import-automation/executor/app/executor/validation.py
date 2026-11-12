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
Functions for validating manifests and import specifications.
"""

import os
import typing

from app import utils

_MANIFEST_REQUIRED_FIELDS = ['import_specifications']
_IMPORT_SPECIFICATION_REQUIRED_FIELDS = [
    'import_name', 'provenance_url', 'provenance_description', 'curator_emails'
]


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

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

import re
import typing

_ALLOWED_PATH_CHARS = 'A-Za-z0-9-_/'
_ALLOWED_RELATIVE_IMPORT_NAME_CHARS = 'A-Za-z0-9-_'
_ALLOWED_ABSOLUTE_IMPORT_NAME_CHARS = (f'{_ALLOWED_PATH_CHARS}:'
                                       f'{_ALLOWED_RELATIVE_IMPORT_NAME_CHARS}')
_ABSOLUTE_IMPORT_NAME_REGEX = r'[{}]+:[{}]+'.format(
    _ALLOWED_PATH_CHARS, _ALLOWED_RELATIVE_IMPORT_NAME_CHARS)
_RELATIVE_IMPORT_NAME_REGEX = r'[{}]+'.format(
    _ALLOWED_RELATIVE_IMPORT_NAME_CHARS)
_IMPORT_NAME_REGEX = r'{}|{}'.format(
    _ABSOLUTE_IMPORT_NAME_REGEX, _RELATIVE_IMPORT_NAME_REGEX)


def get_absolute_import_name(dir_path, import_name):
    return f'{dir_path}:{import_name}'


def absolute_import_name(import_name):
    return re.fullmatch(_ABSOLUTE_IMPORT_NAME_REGEX, import_name) is not None


def relative_import_name(import_name):
    return re.fullmatch(_RELATIVE_IMPORT_NAME_REGEX, import_name) is not None


def split_absolute_import_name(import_name):
    return import_name.split(':')


def get_relative_import_names(import_names):
    return list(name for name in import_names if relative_import_name(name))


def get_absolute_import_names(import_names):
    return list(name for name in import_names if absolute_import_name(name))


def parse_commit_message_targets(commit_message: str) -> typing.List[str]:
    """Parses the import targets from a commit message.

    Import targets are specified by including
    IMPORTS=<comma separated list of import names> in the commit message.

    Args:
        commit_message: GitHub commit message as a string.

    Returns:
        A list of import names each as a string.
    """
    targets = set()
    pattern = r'(?:IMPORTS=)([{},]+)'.format(
        _ALLOWED_ABSOLUTE_IMPORT_NAME_CHARS)
    target_lists = re.findall(pattern, commit_message)
    for target_list in target_lists:
        for target in target_list.split(','):
            if not target or target.isspace():
                continue
            if absolute_import_name(target) or relative_import_name(target):
                targets.add(target)
            else:
                raise ValueError(f'Import target {target} is not valid')
    return list(targets)


def import_targetted_by_commit(
        import_dir: str,
        import_name: str,
        import_targets: typing.List[str]) -> bool:
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
    absolute_name = get_absolute_import_name(
        import_dir, import_name)
    absolute_all = get_absolute_import_name(import_dir, 'all')
    return ('all' in import_targets or
            absolute_name in import_targets or
            import_name in import_targets or
            absolute_all in import_targets)

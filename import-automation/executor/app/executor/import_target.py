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
Helper functions for parsing and validating import target names of the form:
<path to directory containing the manifest>:<import name>
"""

import re
from typing import List

_ALLOWED_PATH_CHARS = 'A-Za-z0-9-_/'
_ALLOWED_RELATIVE_IMPORT_NAME_CHARS = 'A-Za-z0-9-_'
_ABSOLUTE_IMPORT_NAME_REGEX = r'[{}]+:[{}]+'.format(
    _ALLOWED_PATH_CHARS, _ALLOWED_RELATIVE_IMPORT_NAME_CHARS)


def get_absolute_import_name(dir_path: str, import_name: str) -> str:
    """Joins a relative import path with an import name."""
    return f'{dir_path}:{import_name}'


def is_absolute_import_name(import_name: str) -> bool:
    """Checks if an import name is absolute."""
    return re.fullmatch(_ABSOLUTE_IMPORT_NAME_REGEX, import_name) is not None


def split_absolute_import_name(import_name: str) -> List[str]:
    """Splits an absolute import name into a relative import path and an
    import name."""
    return import_name.split(':')

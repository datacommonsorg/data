# Copyright 2026 Google LLC
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
"""Helpers for reading import manifests and resolving their input files."""

import glob
import json
import os
from typing import Dict, List, Optional


class MissingInputFilesError(RuntimeError):
    """Raised when non-wildcard `import_inputs` patterns match no files."""


def parse_manifest(path: str) -> dict:
    """Parses the import manifest.

    Args:
        path: Path to the import manifest file as a string.

    Returns:
        The parsed manifest as a dict.

    Raises:
        Same exceptions as open and json.load if the file does not exist or
        contains malformed json.
    """
    with open(path, encoding='utf-8') as file:
        return json.load(file)


def get_import_spec(manifest: dict, import_name: str) -> Optional[Dict]:
    """Returns the import specification named `import_name` in the manifest.

    Args:
        manifest: The parsed manifest as a dict.
        import_name: Name of the import, i.e. `import_name` in its spec.

    Returns:
        The import specification as a dict, or None if there is no import
        with that name.
    """
    for spec in manifest.get('import_specifications', []):
        if spec.get('import_name') == import_name:
            return spec
    return None


def get_import_input_files(import_input: Dict,
                           absolute_import_dir: str) -> List[str]:
    """Returns the input files for one entry of `import_inputs`.

    Files are returned in the order template_mcf, node_mcf and cleaned_csv.
    Files matching a single pattern are sorted. Wildcard patterns that match
    no files are skipped.

    Args:
        import_input: One entry of `import_inputs` in an import spec, mapping
          a file type to a pattern or a list of patterns.
        absolute_import_dir: Absolute path to the directory containing the
          manifest. Patterns are relative to it.

    Returns:
        List of absolute paths of the input files.

    Raises:
        MissingInputFilesError: A pattern without wildcards matched no files.
    """
    input_files = []
    errors = []
    # Get import files in the order template_mcf, node_mcf and cleaned_csv
    for file_type in sorted(import_input.keys(), reverse=True):
        pattern = import_input[file_type]
        patterns = [pattern]
        if isinstance(pattern, list):
            patterns = pattern
        for pattern in patterns:
            if pattern:
                files = glob.glob(os.path.join(absolute_import_dir, pattern),
                                  recursive=True)
                if not files and not glob.has_magic(pattern):
                    errors.append(
                        f'No matching files for {file_type}:{pattern}')
                else:
                    input_files.extend(sorted(files))
    if errors:
        raise MissingInputFilesError(
            f'Missing import files in {absolute_import_dir}: {errors}')
    return input_files

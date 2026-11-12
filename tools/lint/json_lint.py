# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Checks that JSON files in the repo are valid.

A file fails the check if it:
  - is not valid UTF-8 (a leading BOM is allowed),
  - is not valid JSON (e.g. trailing commas, comments, merge-conflict markers),
  - has the same key more than once in an object, or
  - uses NaN, Infinity or -Infinity (accepted by Python, but not valid JSON).

Formatting (indentation, key order, final newline) is not checked.

Usage (from the repo root):
  python3 tools/lint/json_lint.py            # Check the whole repo.
  python3 tools/lint/json_lint.py a.json dir # Check specific files/folders.
"""

import collections
import json
import os
import sys

# File extensions to check.
JSON_EXTENSIONS = ('.json', '.geojson')

# Directory names skipped anywhere in the tree.
EXCLUDED_DIRS = frozenset({
    '.git',
    # Python virtual environments. CI creates /workspace/.env, which contains
    # JSON files shipped with installed packages.
    '.env',
    '.venv',
    'node_modules',
    '__pycache__',
    '.ruff_cache',
    # Local scratch outputs (also ignored by .gitignore).
    'scratch',
})

# Files skipped by the check, relative to the repo root. Give a reason for
# each entry, and remove it once the file is fixed.
EXCLUDED_FILES = frozenset({
    # Python-style config with `#` comments, not JSON.
    'scripts/earthengine/ee_config.json',
    # Contains unresolved merge-conflict markers (from #2250); needs the
    # correct counter values to be restored.
    'scripts/fao/validation/report.json',
})

# Large files stored with Git LFS (https://git-lfs.com) are checked out as a
# small text "pointer" file instead of the real content, unless `git lfs pull`
# is run. A pointer file isn't JSON, so it is skipped. Pointer files always
# start with this line.
_LFS_POINTER_PREFIX = b'version https://git-lfs.github.com/spec/'

_REPO_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class _DuplicateKeyError(ValueError):
    pass


class _InvalidConstantError(ValueError):
    pass


def _reject_duplicate_keys(pairs):
    """object_pairs_hook for json.loads that fails on repeated keys."""
    result = dict(pairs)
    # Fast path: no duplicates if every key made it into the dict. This avoids
    # counting keys for every object, which is slow on large files.
    if len(result) == len(pairs):
        return result
    counts = collections.Counter(key for key, _ in pairs)
    duplicates = [key for key, count in counts.items() if count > 1]
    raise _DuplicateKeyError(
        f'duplicate keys: {", ".join(repr(k) for k in duplicates)}')


def _reject_constant(name):
    """parse_constant hook for json.loads that fails on NaN/Infinity."""
    raise _InvalidConstantError(f'{name} is not valid JSON')


def lint_file(path):
    """Returns a list of error messages for the file (empty if valid)."""
    with open(path, 'rb') as f:
        raw = f.read()

    if raw.startswith(_LFS_POINTER_PREFIX):
        return []

    try:
        text = raw.decode('utf-8-sig')
    except UnicodeDecodeError as e:
        return [f'not valid UTF-8: {e}']

    try:
        json.loads(text,
                   object_pairs_hook=_reject_duplicate_keys,
                   parse_constant=_reject_constant)
    except json.JSONDecodeError as e:
        return [f'{e.lineno}:{e.colno}: {e.msg}']
    except (_DuplicateKeyError, _InvalidConstantError) as e:
        return [str(e)]
    return []


def find_json_files(paths, repo_root=_REPO_ROOT):
    """Yields JSON files under the given paths, skipping excluded ones.

    Args:
      paths: Files or directories to search.
      repo_root: Directory that EXCLUDED_FILES entries are relative to.
    """
    for path in paths:
        if os.path.isfile(path):
            candidates = [path]
        else:
            candidates = []
            for dirpath, dirnames, filenames in os.walk(path):
                dirnames[:] = sorted(
                    d for d in dirnames if d not in EXCLUDED_DIRS)
                candidates.extend(
                    os.path.join(dirpath, name) for name in sorted(filenames))
        for candidate in candidates:
            if not candidate.endswith(JSON_EXTENSIONS):
                continue
            rel_path = os.path.relpath(candidate, repo_root)
            if rel_path.replace(os.sep, '/') in EXCLUDED_FILES:
                continue
            yield candidate


def main(argv):
    paths = argv[1:] or [_REPO_ROOT]
    num_files = 0
    num_failed = 0
    for path in find_json_files(paths):
        num_files += 1
        errors = lint_file(path)
        if errors:
            num_failed += 1
            display_path = os.path.relpath(path)
            if display_path.startswith('..'):
                display_path = path
            for error in errors:
                print(f'{display_path}: {error}')

    print(f'Checked {num_files} JSON files, {num_failed} failed.')
    if num_failed:
        print('ERROR: Fix the invalid JSON files listed above.',
              file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))

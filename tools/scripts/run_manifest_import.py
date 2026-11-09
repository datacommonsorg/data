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
"""Runs the Data Commons import tool for an import, given its manifest.

Builds the list of input files from the manifest's `import_inputs` the same
way the import executor does, and runs the import tool once per input through
`run_import_tool.sh`, which keeps the import tool JAR up to date.

The import's processing scripts must already have been run, so the files
listed in `import_inputs` (for example, `output/data.csv`) exist.

Usage:
  python3 tools/scripts/run_manifest_import.py \
      --manifest=scripts/us_bls/cpi/manifest.json \
      --import_name=BLS_CPI

  # Print the resolved files and commands without running them:
  python3 tools/scripts/run_manifest_import.py --manifest=... \
      --import_name=... --dry_run

  # Pass extra flags to the import tool after `--`:
  python3 tools/scripts/run_manifest_import.py --manifest=... \
      --import_name=... -- -n=4 --existence-checks=false

Output for input i is written to `<output_dir>/input<i>/genmcf` (or
`input<i>/lint` in lint mode). `<output_dir>` defaults to
`<manifest dir>/<import_name>`.
"""

import argparse
import glob
import json
import os
import shlex
import subprocess
import sys
from typing import Dict, List, Optional, Sequence

_RUN_IMPORT_TOOL_SH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                   'run_import_tool.sh')


class _ManifestImportError(Exception):
    """Raised when the manifest or its input files are invalid."""


def _load_import_spec(manifest_path: str, import_name: str) -> Dict:
    """Returns the import specification named `import_name` in the manifest."""
    with open(manifest_path, 'r') as f:
        manifest = json.load(f)
    specs = manifest.get('import_specifications', [])
    for spec in specs:
        if spec.get('import_name') == import_name:
            return spec
    available = ', '.join(spec.get('import_name', '?') for spec in specs)
    raise _ManifestImportError(
        f'Import "{import_name}" not found in {manifest_path}. '
        f'Available imports: {available or "(none)"}')


def _get_import_input_files(import_input: Dict,
                            absolute_import_dir: str) -> List[str]:
    """Returns the input files for one entry of `import_inputs`.

    Keep in sync with `ImportExecutor._get_import_input_files` in
    import-automation/executor/app/executor/import_executor.py.
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
        raise _ManifestImportError(
            f'Missing import files in {absolute_import_dir}: {errors}. '
            'Run the import\'s processing scripts first.')
    return input_files


def _get_unmatched_glob_patterns(import_input: Dict,
                                 absolute_import_dir: str) -> List[str]:
    """Returns `file_type:pattern` for each wildcard pattern matching no files.

    The import executor silently skips these, so a missing processing output
    can go unnoticed. This is kept separate from `_get_import_input_files` so
    that function stays identical to the import executor's.
    """
    unmatched = []
    for file_type in sorted(import_input.keys(), reverse=True):
        pattern = import_input[file_type]
        patterns = pattern if isinstance(pattern, list) else [pattern]
        for pattern in patterns:
            if pattern and glob.has_magic(pattern) and not glob.glob(
                    os.path.join(absolute_import_dir, pattern), recursive=True):
                unmatched.append(f'{file_type}:{pattern}')
    return unmatched


def _build_commands(
    manifest_path: str,
    import_name: str,
    mode: str = 'genmcf',
    output_dir: Optional[str] = None,
    tool_args: Sequence[str] = ()
) -> List[List[str]]:
    """Returns one import tool command per entry of `import_inputs`."""
    absolute_import_dir = os.path.dirname(os.path.abspath(manifest_path))
    spec = _load_import_spec(manifest_path, import_name)
    import_inputs = spec.get('import_inputs', [])
    if not import_inputs:
        raise _ManifestImportError(
            f'Import "{import_name}" has no import_inputs in {manifest_path}.')
    if not output_dir:
        output_dir = os.path.join(absolute_import_dir, import_name)

    commands = []
    for index, import_input in enumerate(import_inputs):
        input_files = _get_import_input_files(import_input, absolute_import_dir)
        for unmatched in _get_unmatched_glob_patterns(import_input,
                                                      absolute_import_dir):
            print(
                f'[run_manifest_import] [WARN] input{index}: no files match '
                f'{unmatched}. The import tool will run without them.',
                file=sys.stderr)
        output_path = os.path.join(os.path.abspath(output_dir), f'input{index}',
                                   mode)
        commands.append(
            [_RUN_IMPORT_TOOL_SH, f'-o={output_path}', *tool_args, mode] +
            input_files)
    return commands


def _parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description='Runs the DC import tool on the inputs listed in an '
        'import manifest. Pass extra import tool flags after "--".')
    parser.add_argument('--manifest',
                        required=True,
                        help='Path to the import\'s manifest.json.')
    parser.add_argument('--import_name',
                        required=True,
                        help='import_name of the import in the manifest.')
    parser.add_argument('--mode',
                        choices=['genmcf', 'lint'],
                        default='genmcf',
                        help='Import tool mode. Default: genmcf.')
    parser.add_argument(
        '--output_dir',
        help='Output directory. Default: <manifest dir>/<import_name>.')
    parser.add_argument('--dry_run',
                        action='store_true',
                        help='Print the commands without running them.')
    parser.add_argument('tool_args',
                        nargs='*',
                        help='Extra import tool flags, after "--".')
    return parser.parse_args(argv)


def main(argv: Sequence[str]) -> int:
    args = _parse_args(argv)
    try:
        commands = _build_commands(args.manifest, args.import_name, args.mode,
                                   args.output_dir, args.tool_args)
    except (_ManifestImportError, OSError, json.JSONDecodeError) as e:
        print(f'[run_manifest_import] [ERROR] {e}', file=sys.stderr)
        return 1

    # Run from the import directory, like the import executor.
    cwd = os.path.dirname(os.path.abspath(args.manifest))
    for index, command in enumerate(commands):
        print(f'[run_manifest_import] input{index}: {shlex.join(command)}',
              file=sys.stderr)
        if args.dry_run:
            continue
        try:
            result = subprocess.run(command, cwd=cwd, check=False)
        except OSError as e:
            print(
                f'[run_manifest_import] [ERROR] Failed to run the import tool '
                f'for input{index}: {e}',
                file=sys.stderr)
            return 1
        if result.returncode != 0:
            print(
                f'[run_manifest_import] [ERROR] Import tool failed for '
                f'input{index} with exit code {result.returncode}.',
                file=sys.stderr)
            return result.returncode
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))

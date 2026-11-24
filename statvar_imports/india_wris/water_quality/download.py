#!/usr/bin/env python3
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
"""Downloads manually staged India WRIS Water Quality CSVs from GCS.

India WRIS (https://indiawris.gov.in/wris/#/DataDownload) is geo-fenced to
Indian IP addresses and requires interactive CAPTCHA and email export. Raw
exports are staged to gs://unresolved_mcf/india_wris/water_quality/input_files/
and fetched unchanged by this script into input_files/ for processing by
stat_var_processor.py.
"""

from collections.abc import Sequence
import os
import sys
import tempfile

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.abspath(os.path.join(_SCRIPT_DIR, '..', '..', '..'))
_UTIL_DIR = os.path.join(_REPO_ROOT, 'util')
for _path in (_REPO_ROOT, _UTIL_DIR):
    if _path not in sys.path:
        sys.path.insert(0, _path)

from absl import app  # pylint: disable=wrong-import-position
from absl import flags  # pylint: disable=wrong-import-position
from absl import logging  # pylint: disable=wrong-import-position
import file_util  # pylint: disable=wrong-import-position

_FLAGS = flags.FLAGS

DEFAULT_GCS_INPUT_DIR = (
    'gs://unresolved_mcf/india_wris/water_quality/input_files')
DEFAULT_REQUIRED_FILES = (
    'groundWater.csv',
    'India_WRIS_Ground_Prod_Retained.csv',
    'surfaceWater.csv',
)


def _define_flags() -> None:
    """Defines command-line flags for downloading staged India WRIS files."""
    flags.DEFINE_string(
        'gcs_input_dir',
        DEFAULT_GCS_INPUT_DIR,
        'GCS directory URI containing manually staged raw India WRIS CSV files.',
    )
    flags.DEFINE_string(
        'output_dir',
        os.path.join(_SCRIPT_DIR, 'input_files'),
        'Local directory where raw source CSV files are saved unchanged.',
    )
    flags.DEFINE_list(
        'required_files',
        list(DEFAULT_REQUIRED_FILES),
        'Comma-separated list of required CSV filenames expected in GCS.',
    )


def _atomic_copy_from_source(src_uri: str, dst_path: str) -> None:
    """Copies one source file atomically and verifies non-empty content."""
    dst_dir = os.path.dirname(dst_path)
    os.makedirs(dst_dir, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(
        prefix=f'.{os.path.basename(dst_path)}.',
        suffix='.tmp',
        dir=dst_dir,
    )
    os.close(fd)
    try:
        logging.info('Copying staged source file from %s to %s', src_uri,
                     dst_path)
        copied_path = file_util.file_copy(src_uri, tmp_path)
        if not copied_path or not os.path.exists(tmp_path):
            raise FileNotFoundError(
                f'Failed to copy staged source file from {src_uri} to {dst_path}'
            )
        size_bytes = os.path.getsize(tmp_path)
        if size_bytes <= 0:
            raise RuntimeError(
                f'Downloaded staged source file is empty (0 bytes): {src_uri}')
        os.replace(tmp_path, dst_path)
        logging.info('Successfully downloaded %s (%d bytes)', dst_path,
                     size_bytes)
    except Exception as exc:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise RuntimeError(
            f'Failed to download staged India WRIS file {src_uri}: {exc}'
        ) from exc


def download_staged_files(
    gcs_input_dir: str = DEFAULT_GCS_INPUT_DIR,
    output_dir: str | None = None,
    required_files: Sequence[str] = DEFAULT_REQUIRED_FILES,
) -> list[str]:
    """Downloads all required and additional staged CSV files into output_dir.

    Args:
        gcs_input_dir: Base GCS URI or directory holding staged raw CSVs.
        output_dir: Local destination directory (defaults to <script>/input_files).
        required_files: Filenames that must exist and be non-empty.

    Returns:
        List of local destination file paths downloaded.

    Raises:
        ValueError: If gcs_input_dir or required_files is empty.
        RuntimeError: If any required or matched file fails to download or is empty.
    """
    clean_input_dir = (gcs_input_dir or '').strip().rstrip('/')
    if not clean_input_dir:
        raise ValueError('gcs_input_dir must be a non-empty path or gs:// URI.')
    if not required_files:
        raise ValueError('required_files must contain at least one filename.')

    target_dir = output_dir or os.path.join(_SCRIPT_DIR, 'input_files')
    os.makedirs(target_dir, exist_ok=True)

    downloaded_paths: list[str] = []
    seen_filenames: set[str] = set()

    for raw_name in required_files:
        filename = raw_name.strip()
        if not filename:
            continue
        src_uri = f'{clean_input_dir}/{filename}'
        dst_path = os.path.join(target_dir, filename)
        _atomic_copy_from_source(src_uri, dst_path)
        downloaded_paths.append(dst_path)
        seen_filenames.add(filename)

    wildcard_pattern = f'{clean_input_dir}/*.csv'
    logging.info('Checking for additional staged CSV files matching %s',
                 wildcard_pattern)
    matched_uris = sorted(file_util.file_get_matching(wildcard_pattern) or [])
    for matched_uri in matched_uris:
        filename = os.path.basename(matched_uri.rstrip('/'))
        if not filename or filename in seen_filenames:
            continue
        dst_path = os.path.join(target_dir, filename)
        _atomic_copy_from_source(matched_uri, dst_path)
        downloaded_paths.append(dst_path)
        seen_filenames.add(filename)

    logging.info(
        'Completed downloading %d staged India WRIS CSV files into %s',
        len(downloaded_paths),
        target_dir,
    )
    return downloaded_paths


def main(argv: list[str]) -> None:
    if len(argv) > 1:
        raise app.UsageError(f'Unexpected positional arguments: {argv[1:]}')
    download_staged_files(
        gcs_input_dir=_FLAGS.gcs_input_dir,
        output_dir=_FLAGS.output_dir,
        required_files=_FLAGS.required_files,
    )


if __name__ == '__main__':
    _define_flags()
    app.run(main)

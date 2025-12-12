#!/usr/bin/env python3

# Copyright 2025 Google LLC
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
"""Backup inputs and outputs from statvar processor run."""

import shutil
from datetime import datetime
from pathlib import Path

from absl import app
from absl import flags
from absl import logging

# Constants
_ATTEMPT_PREFIX = 'attempt_'

FLAGS = flags.FLAGS

flags.DEFINE_string('working_dir', '.',
                    'Working directory (default: current directory)')
flags.DEFINE_string('gemini_run_id', None,
                    'Gemini run ID (e.g., gemini_20250109_143022)')
flags.mark_flag_as_required('gemini_run_id')
flags.DEFINE_multi_string(
    'backup_files',
    [],  # Explicit list passed by caller
    'Files/directories to backup (relative to working_dir or absolute). '
    'Can be specified multiple times. Directories will backup all contents. '
    'Non-existent files will be skipped with a warning.')
flags.DEFINE_integer(
    'max_dir_files', 30,
    'Maximum number of files allowed when backing up a directory. '
    'Directories with more files will be skipped.')


def _get_next_attempt_number(gemini_run_dir: Path) -> int:
    """Get next attempt number by counting existing attempt directories."""
    existing_attempts = list(gemini_run_dir.glob(f'{_ATTEMPT_PREFIX}*'))
    return len(existing_attempts) + 1


def _resolve_path(path_str: str, working_dir: Path) -> Path:
    """Resolve path relative to working_dir if not absolute."""
    path = Path(path_str)
    if path.is_absolute():
        return path
    else:
        return working_dir / path


def _is_relative_to(path: Path, other: Path) -> bool:
    """True if path is the same as or under other."""
    try:
        path.relative_to(other)
        return True
    except ValueError:
        return False


def _backup_path(source_path: Path, dest_dir: Path, path_spec: str,
                 max_dir_files: int) -> bool:
    """Backup a file or directory to destination. Skip if not found.
    
    Args:
        source_path: Resolved path to backup
        dest_dir: Destination directory for backup
        path_spec: Original path specification (for logging)
        max_dir_files: Maximum allowed files when copying a directory
    
    Returns:
        True if backup successful, False otherwise
    """
    if not source_path.exists():
        logging.warning(f"  Skipping non-existent path: {path_spec}")
        return False

    try:
        if source_path.is_file():
            logging.info(f"  Copying file: {source_path} -> {dest_dir}")
            dest_file = dest_dir / source_path.name
            shutil.copy2(source_path, dest_file)
            logging.info(f"  Backed up file: {source_path.name}")
            return True
        elif source_path.is_dir():
            logging.info(f"  Preparing to copy directory: {source_path}")
            file_count = 0
            for item in source_path.rglob('*'):
                if item.is_file():
                    file_count += 1
                    if file_count > max_dir_files:
                        logging.warning(
                            f"  Skipping directory: {path_spec} has more than "
                            f"{max_dir_files} files")
                        return False
            logging.info(
                f"  Copying directory ({file_count} files): {source_path} -> "
                f"{dest_dir / source_path.name}")
            dest_subdir = dest_dir / source_path.name
            if dest_subdir.exists():
                shutil.rmtree(dest_subdir)
            shutil.copytree(source_path, dest_subdir)
            logging.info(
                f"  Backed up directory: {source_path.name}/ ({file_count} files)"
            )
            return True
    except Exception as e:
        logging.error(f"  Error backing up {path_spec}: {e}")
        return False

    return False


def execute_backup(
    working_dir: Path,
    gemini_run_id: str,
    path_specs: list[str],
    max_dir_files: int,
) -> Path:
    """Perform backup of processor run files.
    
    Args:
        working_dir: Base directory for the processor run.
        gemini_run_id: Identifier for the run.
        path_specs: Paths to backup (relative or absolute).
        max_dir_files: Maximum file count allowed for directories.

    Returns:
        Path to the backup directory
    """
    backup_base = working_dir / '.datacommons' / 'runs'
    gemini_run_dir = backup_base / gemini_run_id
    gemini_run_dir.mkdir(parents=True, exist_ok=True)

    # Get attempt number
    attempt_num = _get_next_attempt_number(gemini_run_dir)
    attempt_dir = gemini_run_dir / f'{_ATTEMPT_PREFIX}{attempt_num:03d}'
    attempt_dir.mkdir(parents=True, exist_ok=True)
    resolved_attempt_dir = attempt_dir.resolve()

    logging.info(f"Backing up attempt {attempt_num:03d} for {gemini_run_id}")
    logging.info(f"Working directory: {working_dir}")
    logging.info(f"Attempt directory: {attempt_dir}")
    logging.info(f"Resolved attempt directory: {resolved_attempt_dir}")

    # Track what was actually backed up
    backed_up = []
    skipped = []

    logging.info(f"Total items to back up: {len(path_specs)}")

    # Backup specified files/directories
    for path_spec in path_specs:
        logging.info(f"Processing: {path_spec}")
        source_path = _resolve_path(path_spec, working_dir)
        resolved_source = source_path.resolve()
        # Skip circular references between source and destination
        if (_is_relative_to(resolved_source, resolved_attempt_dir) or
                _is_relative_to(resolved_attempt_dir, resolved_source)):
            logging.error(
                f"  Skipping circular backup source: {resolved_source} conflicts "
                f"with destination {attempt_dir}")
            skipped.append(path_spec)
            continue

        if _backup_path(resolved_source, attempt_dir, path_spec, max_dir_files):
            backed_up.append(path_spec)
        else:
            skipped.append(path_spec)

    logging.info(
        f"Backup summary: {len(backed_up)} items copied, {len(skipped)} items "
        "skipped (missing or blocked)")

    # Save a manifest of what was backed up
    manifest_file = attempt_dir / 'backup_manifest.txt'
    with open(manifest_file, 'w') as f:
        f.write(f"Backup created: {datetime.now().isoformat()}\n")
        f.write(f"Gemini run ID: {gemini_run_id}\n")
        f.write(f"Attempt number: {attempt_num:03d}\n")
        f.write(f"Working directory: {working_dir}\n")
        f.write("\nRequested files:\n")
        for path_spec in path_specs:
            f.write(f"  - {path_spec}\n")
        f.write("\nBacked up successfully:\n")
        for path_spec in backed_up:
            f.write(f"  OK {path_spec}\n")
        if skipped:
            f.write("\nSkipped (missing or blocked):\n")
            for path_spec in skipped:
                f.write(f"  SKIP {path_spec}\n")

    logging.info(f"Backup completed: {attempt_dir}")
    if skipped:
        logging.info(f"  Skipped {len(skipped)} paths (missing or blocked)")
    logging.info(f"Manifest written to: {manifest_file}")

    return attempt_dir


def main(argv):
    """Main entry point."""
    del argv  # Unused
    working_dir = Path(FLAGS.working_dir).resolve()
    attempt_dir = execute_backup(
        working_dir=working_dir,
        gemini_run_id=FLAGS.gemini_run_id,
        path_specs=list(FLAGS.backup_files),
        max_dir_files=FLAGS.max_dir_files,
    )
    return str(attempt_dir)


if __name__ == '__main__':
    app.run(main)

#!/usr/bin/env python3

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
"""Backup inputs and outputs from statvar processor run."""

import os
import shutil
import sys
from datetime import datetime
from pathlib import Path

from absl import app
from absl import flags
from absl import logging

# Constants
ATTEMPT_PREFIX = 'attempt_'

FLAGS = flags.FLAGS

flags.DEFINE_string('working_dir', '.',
                    'Working directory (default: current directory)')
flags.DEFINE_string('gemini_run_id', None,
                    'Gemini run ID (e.g., gemini_20250109_143022)')
flags.mark_flag_as_required('gemini_run_id')
flags.DEFINE_multi_string(
    'backup_files',
    ['pvmap.csv', 'metadata.csv', 'output'],  # Default files
    'Files/directories to backup (relative to working_dir or absolute). '
    'Can be specified multiple times. Directories will backup all contents. '
    'Non-existent files will be skipped with a warning.')


def get_next_attempt_number(gemini_run_dir: Path) -> int:
    """Get next attempt number by counting existing attempt directories."""
    existing_attempts = list(gemini_run_dir.glob(f'{ATTEMPT_PREFIX}*'))
    return len(existing_attempts) + 1


def resolve_path(path_str: str, working_dir: Path) -> Path:
    """Resolve path relative to working_dir if not absolute."""
    path = Path(path_str)
    if path.is_absolute():
        return path
    else:
        return working_dir / path


def backup_path(source_path: Path, dest_dir: Path, path_spec: str) -> bool:
    """Backup a file or directory to destination. Skip if not found.
    
    Args:
        source_path: Resolved path to backup
        dest_dir: Destination directory for backup
        path_spec: Original path specification (for logging)
    
    Returns:
        True if backup successful, False otherwise
    """
    if not source_path.exists():
        logging.warning(f"  Skipping non-existent path: {path_spec}")
        return False

    try:
        if source_path.is_file():
            dest_file = dest_dir / source_path.name
            shutil.copy2(source_path, dest_file)
            logging.info(f"  Backed up file: {source_path.name}")
            return True
        elif source_path.is_dir():
            dest_subdir = dest_dir / source_path.name
            if dest_subdir.exists():
                shutil.rmtree(dest_subdir)
            shutil.copytree(source_path, dest_subdir)
            # Count files in the backed up directory
            file_count = sum(1 for _ in source_path.rglob('*') if _.is_file())
            logging.info(
                f"  Backed up directory: {source_path.name}/ ({file_count} files)"
            )
            return True
    except Exception as e:
        logging.error(f"  Error backing up {path_spec}: {e}")
        return False

    return False


def backup_run() -> str:
    """Perform backup of processor run files.
    
    Returns:
        Path to the backup directory
    """
    # Setup paths
    working_dir = Path(FLAGS.working_dir).resolve()
    backup_base = working_dir / '.datacommons' / 'runs'
    gemini_run_dir = backup_base / FLAGS.gemini_run_id
    gemini_run_dir.mkdir(parents=True, exist_ok=True)

    # Get attempt number
    attempt_num = get_next_attempt_number(gemini_run_dir)
    attempt_dir = gemini_run_dir / f'{ATTEMPT_PREFIX}{attempt_num:03d}'
    attempt_dir.mkdir(parents=True, exist_ok=True)

    logging.info(
        f"Backing up attempt {attempt_num:03d} for {FLAGS.gemini_run_id}")

    # Track what was actually backed up
    backed_up = []
    skipped = []

    # Backup specified files/directories
    for path_spec in FLAGS.backup_files:
        source_path = resolve_path(path_spec, working_dir)
        if backup_path(source_path, attempt_dir, path_spec):
            backed_up.append(path_spec)
        else:
            skipped.append(path_spec)

    # Save a manifest of what was backed up
    manifest_file = attempt_dir / 'backup_manifest.txt'
    with open(manifest_file, 'w') as f:
        f.write(f"Backup created: {datetime.now().isoformat()}\n")
        f.write(f"Gemini run ID: {FLAGS.gemini_run_id}\n")
        f.write(f"Attempt number: {attempt_num:03d}\n")
        f.write(f"Working directory: {working_dir}\n")
        f.write(f"\nRequested files:\n")
        for path_spec in FLAGS.backup_files:
            f.write(f"  - {path_spec}\n")
        f.write(f"\nBacked up successfully:\n")
        for path_spec in backed_up:
            f.write(f"  ✓ {path_spec}\n")
        if skipped:
            f.write(f"\nSkipped (not found):\n")
            for path_spec in skipped:
                f.write(f"  ✗ {path_spec}\n")

    logging.info(f"Backup completed: {attempt_dir}")
    if skipped:
        logging.info(f"  Skipped {len(skipped)} non-existent paths")

    return str(attempt_dir)


def main(argv):
    """Main entry point."""
    del argv  # Unused
    backup_run()


if __name__ == '__main__':
    app.run(main)

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
"""Utility script to check and retain missing historical data points.

This script compares a current output CSV with an older historical CSV. It
identifies rows in the historical file that are still missing from the current
output file based on specific composite keys and generates a unified
concatenated CSV. It safely accesses cloud storage locations using internal utilities.
"""

import os
import sys

# Dynamically find the path relative to this script's location
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# Navigate relative to tools/statvar_importer/ to find the shared util directory
_UTIL_PATH = os.path.abspath(os.path.join(_SCRIPT_DIR, '../../util/'))

if _UTIL_PATH not in sys.path:
  sys.path.append(_UTIL_PATH)

try:
  import file_util
except ModuleNotFoundError:
  # Fallback logic to check alternative root folder configurations
  _ALT_UTIL_PATH = os.path.abspath(os.path.join(_SCRIPT_DIR, '../../../util/'))
  if _ALT_UTIL_PATH not in sys.path:
    sys.path.append(_ALT_UTIL_PATH)
  import file_util

from absl import app
from absl import flags
from absl import logging
import pandas as pd

FLAGS = flags.FLAGS

flags.DEFINE_string(
    'current_output',
    None,
    'Path to the latest current output CSV file.',
)
flags.DEFINE_string(
    'historical_output',
    None,
    'Path to the historical retention CSV file (supports gs:// or storage.mtls paths).',
)
flags.DEFINE_string(
    'output_file',
    'final_combined_output.csv',
    'Path to save the generated unified output file.',
)


def _read_csv(file_path: str) -> pd.DataFrame:
  """Reads a CSV into a DataFrame, converting HTTP storage links to gs:// paths."""
  # Convert browser mTLS links to gs:// URI syntax if passed to the flag
  mtls_prefix = 'https://storage.mtls.cloud.google.com/'
  if file_path.startswith(mtls_prefix):
    file_path = 'gs://' + file_path[len(mtls_prefix):]
    logging.info('Normalized mTLS URL to native path: %s', file_path)

  if file_path.startswith('gs://'):
    with file_util.FileIO(file_path, 'r') as f:
      return pd.read_csv(f)
  return pd.read_csv(file_path)


def process_and_reconcile_data(current_path: str, historical_path: str,
                              output_path: str) -> None:
  """Compares historical data against current data and retains missing records.

  Args:
      current_path: Path to the current output data file.
      historical_path: Path to the historical tracking data file.
      output_path: Target path where the merged CSV file should be saved.
  """
  logging.info('Loading input CSV datasets...')
  try:
    current_df = _read_csv(current_path)
    historical_df = _read_csv(historical_path)
  except Exception as e:
    logging.fatal('Failed to read input files: %s', e)
    sys.exit(1)

  # Define the columns that serve as the unique identifier/key for each data point
  keys = [
      'observationAbout',
      'observationDate',
      'variableMeasured',
      'unit',
      'scalingFactor',
  ]

  logging.info('Generating series footprints for alignment validation...')

  # Extract only the key columns from the current CSV and drop any duplicates
  current_keys = current_df[keys].drop_duplicates()

  # Perform a left merge from the historical data onto the current keys
  merged = historical_df.merge(current_keys, on=keys, how='left', indicator=True)

  # Keep only the rows from the historical CSV that DO NOT exist in the current CSV
  historical_only = historical_df[merged['_merge'] == 'left_only'].copy()

  if historical_only.empty:
    logging.info('All historical data points are already active in current.')
    final_df = current_df
  else:
    logging.info(
        'Retaining %d records from the historical framework.',
        len(historical_only),
    )
    # Combine all data points from current CSV with the unique historical entries
    final_df = pd.concat([current_df, historical_only], ignore_index=True)

  try:
    with file_util.FileIO(output_path, 'w') as f:
      final_df.to_csv(f, index=False, encoding='utf-8')
    logging.info('Successfully saved unified dataset to: %s', output_path)

    print('=' * 80)
    print(f'Current Base Records Processed : {len(current_df)}')
    print(f'Historical Points Re-inserted  : {len(historical_only)}')
    print(f'Total Unified Series Exported  : {len(final_df)}')
    print(f'Target File Location           : {output_path}')
    print('=' * 80)
  except Exception as e:
    logging.fatal('Failed to write reconciliation dataset matrix: %s', e)
    sys.exit(1)


def main(_):
  flags.mark_flag_as_required('current_output')
  flags.mark_flag_as_required('historical_output')
  process_and_reconcile_data(
      FLAGS.current_output, FLAGS.historical_output, FLAGS.output_file
  )


if __name__ == '__main__':
  app.run(main)

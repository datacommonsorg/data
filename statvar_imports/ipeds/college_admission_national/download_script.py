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
"""This script downloads data from IPEDS and converts it from XLSX to CSV."""

import json
import os
import sys
import pandas as pd
from absl import app
from absl import flags
from absl import logging

# Allows the following module imports to work when running as a script
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(os.path.dirname(_SCRIPT_DIR)))

from util import download_util

FLAGS = flags.FLAGS

flags.DEFINE_string(
    'download_config_path',
    os.path.join(_SCRIPT_DIR, 'download_config.json'),
    'Path to the download configuration JSON file.')
flags.DEFINE_string('output_dir', os.path.join(_SCRIPT_DIR, 'input_files'),
                    'Directory to save the final CSV files.')


def download_and_convert_to_csv(url: str,
                                output_path: str,
                                xlsx_temp_path: str) -> None:
  """Downloads a file from a URL, converts from XLSX to CSV, and removes header rows."""
  logging.info(f'Downloading from {url}')
  download_util.download_file_from_url(url=url, output_file=xlsx_temp_path)

  if not os.path.exists(xlsx_temp_path):
    logging.error(f'Failed to download file from {url}')
    return

  logging.info(f'Converting {xlsx_temp_path} to CSV.')
  xls_df = pd.read_excel(xlsx_temp_path, header=None)

  start_row = 0
  found = False
  for i, row in xls_df.iterrows():
      if any('4-year' in str(cell) for cell in row):
          start_row = i
          found = True
          break
  
  if not found:
      logging.warning(f'"4-year" not found in {xlsx_temp_path}. Saving the file as is.')
      cleaned_df = xls_df
  else:
      cleaned_df = xls_df.iloc[start_row:]

  if cleaned_df.empty:
    logging.warning(f'Downloaded file from {url} is empty after cleaning.')
  else:
    cleaned_df.to_csv(output_path, index=False, header=False)
    logging.info(f'Successfully converted and saved to {output_path}')

  os.remove(xlsx_temp_path)
  logging.info(f'Removed temporary file: {xlsx_temp_path}')


def main(argv):
  """Main function to download and process admissions data."""
  del argv  # Unused

  if not os.path.exists(FLAGS.output_dir):
    os.makedirs(FLAGS.output_dir)

  with open(FLAGS.download_config_path, 'r') as f:
    configs = json.load(f)

  for config in configs:
    url = config['url']
    filename = config['filename']
    csv_output_path = os.path.join(FLAGS.output_dir, f'{filename}.csv')
    xlsx_temp_path = os.path.join(FLAGS.output_dir, f'{filename}.xlsx')
    
    download_and_convert_to_csv(url, csv_output_path, xlsx_temp_path)


if __name__ == '__main__':
  app.run(main)

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

from absl import app
from absl import flags
from absl import logging
from enum import Enum
import pandas as pd
import os
import json

FLAGS = flags.FLAGS
flags.DEFINE_string('config_file', 'config.json',
  'Path to the validation config file.')
flags.DEFINE_string('differ_output_location', '.',
  'Path to the differ output data.')
flags.DEFINE_string('stats_summary_location', '.',
  'Path to the stats summary report.')

POINT_ANALAYSIS_FILENAME = 'point-analysis-summary.csv'
STATS_SUMMARY_FILENAME = 'summary_report.csv'

Validation = Enum('Validation', [
  ('MODIFIED_COUNT', 1),
  ('UNMODIFIED_COUNT', 2),
  ('ADDED_COUNT', 3),
  ('DELETED_COUNT', 4),
  ('LATEST_DATA', 5),
])

class ImportValidation:
  '''
  Import validation
  '''
  def __init__(self, config_file: str):
    logging.info('Reading config from %s', config_file)
    self.validation_map = {
      Validation.MODIFIED_COUNT: self._modified_count_validation,
      Validation.ADDED_COUNT:  self._added_count_validation,
      Validation.DELETED_COUNT:  self._deleted_count_validation,
      Validation.UNMODIFIED_COUNT:  self._unmodified_count_validation
    }
    with open(config_file, encoding='utf-8') as fd:
      validation_config = json.load(fd)
      for config in validation_config:
        self.run_validation(config)

  def _latest_data_validation(self, config: dict):
    logging.info('Not yet implemented')

  def _deleted_count_validation(self, config: dict):
    df = pd.read_csv(os.path.join(
      FLAGS.differ_output_location, POINT_ANALAYSIS_FILENAME))
    if df['deleted'].sum() > config['threshold']:
      raise AssertionError(f'Validation failed: {config["validation"]}')

  def _modified_count_validation(self, config: dict):
    df = pd.read_csv(os.path.join(
      FLAGS.differ_output_location, POINT_ANALAYSIS_FILENAME))
    if df['modified'].nunique() > 1:
      raise AssertionError(f'Validation failed: {config["validation"]}')

  def _added_count_validation(self, config: dict):
    df = pd.read_csv(os.path.join(
      FLAGS.differ_output_location, POINT_ANALAYSIS_FILENAME))
    if df['added'].nunique() > 1:
      raise AssertionError(f'Validation failed: {config["validation"]}')

  def _unmodified_count_validation(self, config: dict):
    df = pd.read_csv(os.path.join(
      FLAGS.differ_output_location, POINT_ANALAYSIS_FILENAME))
    if df['same'].nunique() > 1:
      raise AssertionError(f'Validation failed: {config["validation"]}')

  def run_validation(self, config):
    try:
      self.validation_map[Validation[config['validation']]](config)
      logging.info('Validation passed: %s', config['validation'])
    except AssertionError as exc:
      logging.error(exc)

def main(_):
  ImportValidation(FLAGS.config_file)

if __name__ == '__main__':
  app.run(main)

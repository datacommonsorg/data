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
import pandas as pd
import os
import json

FLAGS = flags.FLAGS
flags.DEFINE_string('configFile', 'config.json',
  'Path to the validation config file.')
flags.DEFINE_string('differOutputLocation', '.',
  'Path to the differ output data.')
flags.DEFINE_string('statsSummaryLocation', '.',
  'Path to the stats summary report.')

POINT_ANALAYSIS_FILENAME = 'point-analysis-summary.csv'
STATS_SUMMARY_FILENAME = 'summary_report.csv'

class ImportValidation:
  '''
  Import validation
  '''
  def __init__(self, config_file: str):
    logging.info('Reading config from %s', config_file)
    with open(config_file, encoding='utf-8') as fd:
      self.config = json.load(fd)
      for validation in self.config:
        self.run_validation(validation)

  def _latest_data_check(self):
    logging.info('Running latest data check')

  def _deleted_count_check(self, threshold: int):
    df = pd.read_csv(os.path.join(
      FLAGS.differOutputLocation, POINT_ANALAYSIS_FILENAME))
    if df['deleted'].sum() > threshold:
      raise ValueError('Data point deletion check failed')
    else:
      logging.info('Deletion count validation passed')

  def run_validation(self, validation):
    match validation['name']:
      case 'DELETED_COUNT_CHECK':
        self._deleted_count_check(validation['threshold'])
      case 'LATEST_DATA_CHECK':
        self._latest_data_check()
      case _:
        raise ValueError(f'Unsupported validation type: {validation["name"]}')

def main(_):
  ImportValidation(FLAGS.configFile)

if __name__ == '__main__':
  app.run(main)

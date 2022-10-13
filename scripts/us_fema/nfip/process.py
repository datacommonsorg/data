# Copyright 2022 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the 'License');
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#         https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an 'AS IS' BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
'''Script to process flood insurance claims data from US FEMA's
National Flood Insurance Program using the generic stat-var_processor.'''

import glob
import os
import requests
import sys
import pandas as pd

from absl import app
from absl import flags
from absl import logging

_SCRIPTS_DIR = os.path.join(
    os.path.abspath(__file__).split('scripts')[0], 'scripts')
sys.path.append(_SCRIPTS_DIR)
sys.path.append(os.path.join(_SCRIPTS_DIR, "statvar"))

from stat_var_processor import StatVarDataProcessor, process

_FLAGS = flags.FLAGS

flags.DEFINE_string(
    'url',
    'https://www.fema.gov/about/reports-and-data/openfema/FimaNfipClaims.csv',
    'URL to download the insurance data.')
flags.DEFINE_string(input_csv, '/tmp/nfip.csv',
                    'CSV file containing data to be processed.')


class NFIPStatVarDataProcessor(StatVarDataProcessor):

    def __init__(self, config_dict: dict = None, counters_dict: dict = None):
        super().__init__(config_dict=config_dict, counters_dict=counters_dict)

    def preprocess_stat_var_pbs_pvs(self, pvs: dict) -> dict:
        '''Add additional PVs to the statvar obs.'''
        # Set observationPeriod based on date.
        if 'observationPeriod' not in pvs:
            date = pvs.get('observationDate', '')
            if date:
                if len(date) == len('YYYY'):
                    # Date is just a year: YYYY, Set period as 1PY.
                    pvs['observationPeriod'] = '1PY'
                elif len(date) == len('YYYY-MM'):
                    pvs['observationPeriod'] = '1PM'
        return pvs


def download_data_from_url(url: str, data_file: str) -> bool:
    '''Download data from the URL into the given file.'''
    logging.info(f'Downloading {url} into {data_file}...')
    response = requests.get(url)
    if response.status_code != 200:
        logging.error(f'Failed to download {url}: {response}')
        return False
    with open(data_file, 'w') as output_file:
        output_file.write(response.text)
    return True


def shard_csv_data(file: str,
                   column: str = 'state',
                   prefix_len: int = 2) -> list:
    '''Shard CSV file by unique values in column.
    Returns the list of output files.'''
    df = pd.read_csv(file, dtype=str)
    shards = set([x[:prefix_len] for x in df[column].unique()])
    (file_prefix, file_ext) = os.path.splitext(file)
    output_path = f'{file_prefix}-{column}'
    logging.info(
        f'Sharding {file} into {len(shards)} shards by column {column} into {output_path}*.csv.'
    )
    output_files = []
    for s in shards:
        output_file = f'{output_path}-{s}.csv'
        df[df[column].str.startswith(s)].to_csv(output_file, index=False)
        output_files.append(output_file)
    return True

def process_data(input_data, output_path):
    process(data_processor_class=NFIPStatVarDataProcessor,
            input_data=input_data,
            output_path=output_path,
            config_file=_FLAGS.config,
            pv_map_files=_FLAGS.pv_map,
            parallelism=_FLAGS.parallelism)

def main(_):
  input_data_files = _FLAGS.input_data
  if not os.path.exists(_FLAGS.input_csv):
    download_data_from_url(_FLAGS.url, _FLAGS.input_csv)
    # Shard input csv by state code.
    input_data_files = shard_csv_data(_FLAGS.input_csv, 'state', 2)
  process_data(input_data_files, _FLAGS.output_path)

if __name__ == '__main__':
    app.run(main)

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
"""Script to shard csv with goe columns."""

import csv
import io
import os
import sys

from absl import app
from absl import flags
from absl import logging
from typing import Union

_SCRIPTS_DIR = os.path.dirname(os.path.dirname(__file__))
sys.path.append(_SCRIPTS_DIR)
sys.path.append(os.path.dirname(_SCRIPTS_DIR))

import utils

from util.counters import Counters
from util.config_map import ConfigMap

flags.DEFINE_string('input_csv', '', 'CSV with S2 cell data to process')
flags.DEFINE_string('output_path', '', 'Output prefix for CSV files')
flags.DEFINE_string('config', '', 'JSOn file with config parameter settings.')

_FLAGS = flags.FLAGS


def shard_csv_file(filenames: str,
                   output_path: str,
                   config: ConfigMap,
                   counters=Counters):
    '''Shard a set of CSV files by the config.'''
    if counters is None:
        counters = Counters()
    input_files = utils.file_get_matching(filenames)
    logging.info(f'Processing csv files: {input_files}')
    shard_files = {}
    for filename in input_files:
        counters.add_counter('total', utils.file_estimate_num_rows(filename))
    output_columns = []
    # Process rows form each input file
    for filename in input_files:
        with open(filename, 'r') as csvfile:
            logging.info(f'Processing csv data file: {filename}')
            reader = csv.DictReader(csvfile)
            counters.add_counter('input-files', 1, filename)
            num_rows = 0
            output_columns = reader.fieldnames
            for row in reader:
                num_rows += 1
                if num_rows > config.get('input_rows', sys.maxsize):
                    break
                counters.add_counter('inputs', 1, filename)
                # Get the shard for the row
                shard_id = _get_s2_shard_for_data(
                    row, config.get('s2_shard_level', 1))
                if shard_id not in shard_files:
                    shard_files[shard_id] = _get_shard_csv_writer(
                        output_path, shard_id, output_columns)
                    counters.add_counter('num_shards', 1, filename)
                # Write the row into the corresponding shard file
                shard_files[shard_id][1].writerow(row)
                counters.add_counter(f'shard-rows-{shard_id}', 1, filename)
                counters.print_counters_periodically()
            logging.info(f'Processed {num_rows} rows from {filename}')

    # Close all open shard files.
    for filep, writer in shard_files.values():
        filep.close()
    logging.info(f'Generated {len(shard_files)} shard files in {output_path}')
    counters.print_counters()


def _get_s2_shard_for_data(data_pvs: dict, s2_shard_level: int) -> str:
    '''Returns the shard for the data dictionary.
  If the data includes s2CellId, uses the s2_shard_level parent as the shard.
  '''
    data_s2_cell = utils.s2_cell_from_dcid(data_pvs.get('s2CellId', None))
    if not data_s2_cell:
        if 'latitude' in data_pvs and 'longitude' in data_pvs:
            data_s2_cell = s2_cell_from_latlng(data_pvs.get('latitude', 0),
                                               data_pvs.get('longitude', 0),
                                               s2_shard_level)
    return utils.s2_cell_to_hex_str(data_s2_cell.parent(s2_shard_level).id())


def _get_shard_csv_writer(file_prefix: str, shard_id: str,
                          columns: list) -> (io.TextIOWrapper, csv.DictWriter):
    '''Returns a CSV dict writer wiht the given file prefix.'''

    csv_filename = utils.file_get_name(file_prefix, f'_shard_{shard_id}',
                                       '.csv')
    logging.info(f'Creating shrad file: {csv_filename}')
    filep = open(csv_filename, 'w')
    writer = csv.DictWriter(filep,
                            fieldnames=columns,
                            escapechar='\\',
                            extrasaction='ignore',
                            quotechar='"',
                            quoting=csv.QUOTE_NONNUMERIC)
    writer.writeheader()
    return filep, writer


def main(_):
    config = ConfigMap(filename=_FLAGS.config)
    counters = Counters()
    shard_csv_file(_FLAGS.input_csv, _FLAGS.output_path, config, counters)


if __name__ == '__main__':
    app.run(main)

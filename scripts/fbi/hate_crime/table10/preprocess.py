# Copyright 2021 Google LLC
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
"""A script to process FBI Hate Crime table 10 publications."""
import os
import sys
import tempfile
import csv
import json
import pandas as pd

from absl import app
from absl import flags
from absl import logging

# Allows the following module imports to work when running as a script
_SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(_SCRIPT_PATH, '..'))  # for utils

import utils
import file_util

flags.DEFINE_string(
    'config_file',
    'gs://unresolved_mcf/fbi/hate_crime/20250107/table_config.json',
    'Input config file')
flags.DEFINE_string(
    'output_dir', _SCRIPT_PATH, 'Directory path to write the cleaned CSV and'
    'MCF. Default behaviour is to write the artifacts in the current working'
    'directory.')
flags.DEFINE_bool(
    'gen_statvar_mcf', False, 'Generate MCF of StatVars. Default behaviour is'
    'to not generate the MCF file.')
_FLAGS = flags.FLAGS

_YEAR_INDEX = 0

# Columns in final cleaned CSV
_OUTPUT_COLUMNS = ('Year', 'StatVar', 'Quantity')

# A config that maps the year to corresponding xls file with args to be used
# with pandas.read_excel()
_YEARWISE_CONFIG = None


def _write_row(year: int, statvar_dcid: str, quantity: str,
               writer: csv.DictWriter):
    """A wrapper to write data to the cleaned CSV."""
    processed_dict = {
        'Year': year,
        'StatVar': statvar_dcid,
        'Quantity': quantity
    }
    writer.writerow(processed_dict)


def _write_output_csv(reader: csv.DictReader, writer: csv.DictWriter,
                      config: dict) -> list:
    """Reads each row of a CSV and creates statvars for counts of
    Incidents, Offenses, Victims and Known Offenders with different bias
    motivations.

    Args:
        reader: CSV dict reader.
        writer: CSV dict writer of final cleaned CSV.
        config: A dict which maps constraint props to the statvar based on
          values in the CSV. See scripts/fbi/hate_crime/table2/config.json for
          an example.

    Returns:
        A list of statvars.
    """
    statvars = []
    columns = list(reader.fieldnames)
    columns.remove('location')
    columns.remove('Year')
    for crime in reader:
        location = crime['location']
        location_key_value = config['pvs'][location]

        statvar_list = []
        for c in columns:
            statvar = {**config['populationType'][c]}
            statvar_list.append(statvar)

        utils.update_statvars(statvar_list, location_key_value)
        utils.update_statvar_dcids(statvar_list, config)

        for idx, c in enumerate(columns):
            _write_row(crime['Year'], statvar_list[idx]['Node'], crime[c],
                       writer)

        statvars.extend(statvar_list)

    return statvars


def _clean_dataframe(df: pd.DataFrame, year: str, table_num):
    """Clean the column names and offense type values in a dataframe."""
    with file_util.FileIO(_FLAGS.config_file, 'r') as f:
        _YEARWISE_CONFIG = json.load(f)
    year_config = _YEARWISE_CONFIG['table_config'][table_num]

    if year_config:
        if isinstance(year_config, list):
            df.columns = year_config
        else:
            for year_range_str, columns in year_config.items():
                year_range = year_range_str.split(",")
                if year in year_range:
                    df.columns = columns

    df.location = df.location.str.lower()
    df.location = df.location.str.replace(r'\d+', '', regex=True)
    return df


def main(argv):
    global _YEARWISE_CONFIG
    csv_files = []
    table_num = '10'
    with file_util.FileIO(_FLAGS.config_file, 'r') as f:
        _YEARWISE_CONFIG = json.load(f)
    config = _YEARWISE_CONFIG['year_config']
    if table_num not in config:
        logging.fatal(
            f"Error: Key {table_num} not found in the config. Please ensure the configuration for section {table_num} is present."
        )
    tmp_dir = '.'
    with tempfile.TemporaryDirectory() as tmp_dir:
        for year, config in config[table_num].items():
            xls_file_path = config['path']
            csv_file_path = os.path.join(tmp_dir, year + '.csv')
            logging.info(f"Processing : {xls_file_path}")
            read_file = pd.read_excel(xls_file_path, **config['args'])
            read_file = _clean_dataframe(read_file, year, table_num)
            read_file.insert(_YEAR_INDEX, 'Year', year)
            read_file.to_csv(csv_file_path, header=True, index=False)
            csv_files.append(csv_file_path)

        config_path = os.path.join(_SCRIPT_PATH, 'config.json')
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)

        cleaned_csv_path = os.path.join(_FLAGS.output_dir, 'cleaned.csv')
        statvars = utils.create_csv_mcf(csv_files, cleaned_csv_path, config,
                                        _OUTPUT_COLUMNS, _write_output_csv)
        if _FLAGS.gen_statvar_mcf:
            mcf_path = os.path.join(_FLAGS.output_dir, 'output.mcf')
            utils.create_mcf(statvars, mcf_path)


if __name__ == '__main__':
    app.run(main)

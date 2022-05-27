# Copyright 2022 Google LLC
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
"""Script to process EPH Heat Stress data."""

import os
import sys
import json
import csv
import copy

from absl import app
from absl import flags

# Allows the following module imports to work when running as a script
_SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(_SCRIPT_PATH, '..', '..', '..', 'util'))

from statvar_dcid_generator import get_statvar_dcid
from name_to_alpha2 import USSTATE_MAP_SPACE
from alpha2_to_dcid import USSTATE_MAP

flags.DEFINE_string('input_path', None,
                    'Path to directory with files to process')
flags.DEFINE_string('config_path', None, 'Path to config file')
flags.DEFINE_string('output_path', None,
                    'Path to directory where CSV, MCF will be written')

_FLAGS = flags.FLAGS

_CONFIG = None

# Columns in cleaned CSV
_OUTPUT_COLUMNS = ('Year', 'Geo', 'StatVar', 'Quantity')


def state_resolver(state: str) -> str:
    """Given a state name, returns it's dcid."""
    state_alpha_code = USSTATE_MAP_SPACE[state]
    geo_dcid = USSTATE_MAP[state_alpha_code]

    return geo_dcid


def _process_file(file_name: str, csv_reader: csv.DictReader,
                  csv_writer: csv.DictWriter) -> list:
    """
    Processes the data file using csv_reader and writes processed data to
    csv_writer.
    """
    template_statvar = {**_CONFIG["filename"][file_name]}
    data_col = 'Data Value'

    statvars = []
    for row in csv_reader:
        quantity = row[data_col]
        if quantity == 'Suppressed':  # Skip suppressed data
            continue
        quantity = float(quantity.replace(',', ''))

        row_statvar = copy.deepcopy(template_statvar)
        year = row['Year']
        # Data is for summertime (May 1 - Sep 30)
        year_with_month = year + '-09'

        state = row['State']
        geo_dcid = state_resolver(state)

        if 'Age Group' in row:
            age_group = row['Age Group']
            row_statvar.update(_CONFIG['pvs']['Age Group'][age_group])

        if 'Gender' in row:
            gender = row['Gender']
            row_statvar.update(_CONFIG['pvs']['Gender'][gender])

        row_statvar['Node'] = get_statvar_dcid(row_statvar)

        processed_dict = {
            'Year': year_with_month,
            'Geo': geo_dcid,
            'StatVar': row_statvar['Node'],
            'Quantity': quantity
        }
        csv_writer.writerow(processed_dict)
        statvars.append(row_statvar)

    return statvars


def is_quantity_range(val: str) -> bool:
    """Checks if [] are present in val. While this is not a perfect check for
    quantity ranges, it works in this case."""
    if '[' in val and ']' in val:
        return True
    return False


def write_to_mcf(sv_list: list, mcf_path: str):
    """Writes all statvars to a .mcf file."""
    if sv_list:
        dcid_set = set()
        with open(mcf_path, 'w', encoding='utf-8') as f:
            for sv in sv_list:
                dcid = sv['Node']
                if dcid in dcid_set:
                    continue
                dcid_set.add(dcid)
                statvar_mcf_list = [f'Node: dcid:{dcid}']
                for p, v in sv.items():
                    if p not in ['Node', 'unit']:
                        if is_quantity_range(v) or p == 'description':
                            statvar_mcf_list.append(f'{p}: {v}')
                        else:
                            statvar_mcf_list.append(f'{p}: dcs:{v}')
                statvar_mcf = '\n'.join(statvar_mcf_list) + '\n\n'
                f.write(statvar_mcf)


def main(argv):
    global _CONFIG
    with open(_FLAGS.config_path, 'r', encoding='utf-8') as config_f:
        _CONFIG = json.load(config_f)

    cleaned_csv_path = os.path.join(_FLAGS.output_path, 'cleaned.csv')
    output_mcf_path = os.path.join(_FLAGS.output_path, 'output.mcf')

    with open(cleaned_csv_path, 'w', encoding='utf-8') as cleaned_f:

        f_writer = csv.DictWriter(cleaned_f, fieldnames=_OUTPUT_COLUMNS)
        f_writer.writeheader()

        statvar_list = []
        for file_name in os.listdir(_FLAGS.input_path):
            if file_name.endswith('.csv'):
                file_path = os.path.join(_FLAGS.input_path, file_name)
                with open(file_path, 'r', encoding='utf-8') as csv_f:
                    f_reader = csv.DictReader(csv_f,
                                              delimiter=',',
                                              quotechar='"')
                    statvars = _process_file(file_name, f_reader, f_writer)
                    if statvars:
                        statvar_list.extend(statvars)

        write_to_mcf(statvar_list, output_mcf_path)


if __name__ == "__main__":
    flags.mark_flags_as_required(['input_path', 'config_path', 'output_path'])
    app.run(main)

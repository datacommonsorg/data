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
"""Script to process CDC Natality data."""

import os
import sys
import json
import csv

from absl import app
from absl import flags

# Allows the following module imports to work when running as a script
_SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(_SCRIPT_PATH, '../../../util/'))

from statvar_dcid_generator import get_statvar_dcid
from name_to_alpha2 import USSTATE_MAP_SPACE
from alpha2_to_dcid import USSTATE_MAP
from county_to_dcid import COUNTY_MAP

flags.DEFINE_string('input_path', None, 'Path to directory with files to clean')
flags.DEFINE_string('config_path', None, 'Path to config file')
flags.DEFINE_string('output_path', None,
                    'Path to directory where cleaned CSV, MCF will be written')
flags.DEFINE_list(
    'skip_years', None,
    'Use to skip data for certain years. Default does not skip any year.')

_FLAGS = flags.FLAGS

_CONFIG = None

# Columns in cleaned CSV
_OUTPUT_COLUMNS = ('Year', 'Geo', 'StatVar', 'Quantity', 'Unit')

_UNRESOLVED_GEOS = set()

_SKIP_YEARS = []  # Used to skip certain years in the data


def _update_statvars(sv_map: dict, update_dict: dict):
    """Adds the prop:value pairs in update_dict to the values in sv_map.

    Args:
        sv_map: A dictionary with values as statvars
        update_dict: A dictionary of prop:value pairs to be added to the
          statvars in sv_map.
    """
    for sv_value in sv_map.values():
        sv_value.update(update_dict)


def geo_resolver(geo: str, geo_type: str = 'State') -> str:
    """
    Given a geo name and it's type(State or County), returns the dcid if it
    exists.
    """
    geo_dcid = None
    if geo_type == 'State':
        state_alpha_code = USSTATE_MAP_SPACE[geo]
        geo_dcid = USSTATE_MAP[state_alpha_code]
    elif geo_type == 'County':
        if 'Unidentified' not in geo:  # Skipping 'Unidentified Counties' in data
            county, state_alpha_code = geo.split(',')
            geo_dcid = COUNTY_MAP[state_alpha_code.strip()].get(
                county.strip(), None)

    return geo_dcid


def _process_file(file_name: str, csv_reader: csv.DictReader,
                  csv_writer: csv.DictWriter) -> list:
    """Processes the cleaned data file using the file_name and csv_reader.
    Writes processed data to the csv_writer."""
    statvar_map = {}
    statvars = []
    update_d = {}
    data_cols = list(_CONFIG['data_cols'])
    geo_col = _CONFIG['geo']['col']
    geo_type = _CONFIG['geo']['type']

    for data_col in data_cols:
        statvar_map[data_col] = {**_CONFIG['populationType'][data_col]}

    # Add key values based on filename
    for file_kv in file_name.split('$$'):
        key, val = file_kv.split('=')
        if val in _CONFIG['filename'][key]:
            update_d.update(_CONFIG['filename'][key][val])
        else:
            return statvars  # Skip processing this file, statvars is empty

        # Average age does not make sense when mothersAge is a cprop
        if key == 'MAge' and val != 'All':
            if _CONFIG['year_range'] == '16-20':
                data_cols.remove('Average Age of Mother (years)')
            elif _CONFIG['year_range'] in ['07-20', '03-06']:
                data_cols.remove('Average Age of Mother')

    _update_statvars(statvar_map, update_d)

    for row in csv_reader:
        skip_statvar = False
        year = row['Year']
        if year in _SKIP_YEARS:
            continue
        geo = row[geo_col]

        geo_dcid = geo_resolver(geo, geo_type=geo_type)
        if geo_dcid is None:
            _UNRESOLVED_GEOS.add(geo)
            continue

        for data_col in data_cols:
            if row[data_col] == 'Suppressed':  # Skip suppressed data
                break

            if row[data_col] in ['Not Applicable', 'Missing County']:
                continue

            statvar = {**statvar_map[data_col]}

            for col in _CONFIG['cprop_cols']:
                val = row[col]
                if val in _CONFIG['pvs'][col]:  # If pv is defined
                    statvar.update(_CONFIG['pvs'][col][val])
                else:
                    skip_statvar = True
                    break  # Skip this row

            if not skip_statvar:
                statvar['Node'] = get_statvar_dcid(statvar)
                processed_dict = {
                    'Year': year,
                    'Geo': geo_dcid,
                    'StatVar': statvar['Node'],
                    'Quantity': row[data_col],
                    'Unit': statvar.get('unit', None)
                }
                csv_writer.writerow(processed_dict)
                statvars.append(statvar)

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
    global _CONFIG, _SKIP_YEARS
    with open(_FLAGS.config_path, 'r', encoding='utf-8') as config_f:
        _CONFIG = json.load(config_f)

    if _FLAGS.skip_years:
        _SKIP_YEARS = _FLAGS.skip_years

    cleaned_csv_path = os.path.join(_FLAGS.output_path, 'cleaned.csv')
    output_mcf_path = os.path.join(_FLAGS.output_path, 'output.mcf')

    with open(cleaned_csv_path, 'w', encoding='utf-8') as cleaned_f:

        f_writer = csv.DictWriter(cleaned_f, fieldnames=_OUTPUT_COLUMNS)
        f_writer.writeheader()

        statvar_list = []
        for file_name in os.listdir(_FLAGS.input_path):
            if file_name.endswith('.txt'):  # Raw data is .txt files
                file_path = os.path.join(_FLAGS.input_path, file_name)
                with open(file_path, 'r', encoding='utf-8') as csv_f:
                    f_reader = csv.DictReader(csv_f,
                                              delimiter=',',
                                              quotechar='"')
                    # Removing .txt from filename
                    f_name = os.path.splitext(file_name)[0]
                    statvars = _process_file(f_name, f_reader, f_writer)
                    if statvars:
                        statvar_list.extend(statvars)

        write_to_mcf(statvar_list, output_mcf_path)


if __name__ == "__main__":
    flags.mark_flags_as_required(['input_path', 'config_path', 'output_path'])
    app.run(main)

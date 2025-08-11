# Copyright 2025 Google LLC
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
import pandas as pd
from absl import app, logging, flags

# Allows the following module imports to work when running as a script
_SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(_SCRIPT_PATH, '..', '..', '..', 'util'))

from statvar_dcid_generator import get_statvar_dcid
from name_to_alpha2 import USSTATE_MAP_SPACE
from alpha2_to_dcid import USSTATE_MAP
from statvar_remap import STATVAR_REMAP_DICT
from clean_data import reads_config_file

_CONFIG = None
_OUTPUT_COLUMNS = ('Year', 'StatVar', 'Quantity', 'Geo', 'measurementMethod')

with open("./config.json", 'r', encoding='utf-8') as config_f:
    _CONFIG = json.load(config_f)


def generate_tmcf():
    # Writing Generated TMCF to local path.
    configs = reads_config_file()
    with open(_CONFIG.get("OUTPUT_PATH") + "/output.tmcf",
              'w+',
              encoding='utf-8') as f_out:
        f_out.write(configs['TMCF_TEMPLATE'].rstrip('\n'))


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

        if 'Sex' in row:
            sex = row['Sex']
            row_statvar.update(_CONFIG['pvs']['Sex'][sex])

        row_statvar['Node'] = get_statvar_dcid(row_statvar)
        for key in STATVAR_REMAP_DICT:
            if str(row_statvar['Node']) == str(key):
                row_statvar['Node'] = STATVAR_REMAP_DICT[key]

        processed_dict = {
            'Year': year_with_month,
            'StatVar': row_statvar['Node'],
            'Quantity': quantity,
            'Geo': geo_dcid,
        }
        """
        Country data is derived by aggregating state-level data. 
        State data is coming from the source, hence setting the measurementMethod value as empty.
        Therefore, country SVs are assigned the measurementMethod 'dcs:DataCommonsAggregate'.
        """
        processed_dict['measurementMethod'] = ""
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


def aggregate():
    """Method to aggregate EPH Heat Illness data from state level data."""
    df = pd.read_csv(_CONFIG.get('OUTPUT_PATH') + "/cleaned.csv",
                     dtype={'Quantity': 'float64'})

    # Aggregating all stat vars
    df.drop_duplicates(subset=['Year', 'Geo', 'StatVar'],
                       keep='first',
                       inplace=True)
    country_df = df.groupby(by=['Year', 'StatVar'],
                            as_index=False).agg({'Quantity': 'sum'})
    country_df['Geo'] = "country/USA"
    country_df['measurementMethod'] = "dcs:DataCommonsAggregate"
    country_df.to_csv(_CONFIG.get('OUTPUT_PATH') + "/country_output.csv",
                      index=False)


def process(cleaned_csv_path, output_mcf_path, input_path):
    with open(cleaned_csv_path, 'w', encoding='utf-8') as cleaned_f:
        f_writer = csv.DictWriter(cleaned_f, fieldnames=_OUTPUT_COLUMNS)
        f_writer.writeheader()
        statvar_list = []
        for file_name in os.listdir(input_path):
            if file_name.endswith('.csv'):
                file_path = os.path.join(input_path, file_name)
                with open(file_path, 'r', encoding='utf-8') as csv_f:
                    f_reader = csv.DictReader(csv_f,
                                              delimiter=',',
                                              quotechar='"')
                    statvars = _process_file(file_name, f_reader, f_writer)

                    if statvars:
                        statvar_list.extend(statvars)

        write_to_mcf(statvar_list, output_mcf_path)


def main(_):
    try:
        os.makedirs(_CONFIG.get('OUTPUT_PATH'), exist_ok=True)
        cleaned_csv_path = os.path.join(_CONFIG.get('OUTPUT_PATH'),
                                        'cleaned.csv')
        output_mcf_path = os.path.join(_CONFIG.get('OUTPUT_PATH'), 'output.mcf')
        try:
            os.listdir(_CONFIG.get('COMBINED_INPUT_CSV_FILE'))
        except:
            logging.error(
                "\n\nData not found!!!!!! Please run the script clean_data.py to download source data\n"
            )
        process(cleaned_csv_path, output_mcf_path,
                _CONFIG.get('COMBINED_INPUT_CSV_FILE'))
        generate_tmcf()
        aggregate()
        logging.info("Processing completed!")
    except Exception as e:
        logging.fatal(f"Encountered issue with process - {e}")


if __name__ == "__main__":
    app.run(main)

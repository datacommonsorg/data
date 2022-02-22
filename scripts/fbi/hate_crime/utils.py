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
"""Utility functions."""
import os
import sys
import csv

# Allows the following module imports to work when running as a script
_SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(_SCRIPT_PATH,
                             '../../../util/'))  # for statvar_dcid_generator

from statvar_dcid_generator import get_statvar_dcid


def create_csv_mcf(csv_files: list, cleaned_csv_path: str, config: dict,
                   output_cols: list, write_output_csv) -> list:
    """Creates StatVars according to values in csv_files and write the final
    output to a csv.

    Args:
        csv_files: A list of CSV file paths to process.
        cleaned_csv_path: Path of the final cleaned CSV file.
        config: A dict which maps constraint props to the statvar based on
          values in the CSV. See scripts/fbi/hate_crime/table2/config.json for
          an example.

    Returns:
        A list of statvars.
    """
    statvars = []
    with open(cleaned_csv_path, 'w', encoding='utf-8') as output_f:
        writer = csv.DictWriter(output_f, fieldnames=output_cols)
        writer.writeheader()

        for csv_file in csv_files:
            with open(csv_file, 'r', encoding='utf-8') as input_f:
                reader = csv.DictReader(input_f)
                statvars_list = write_output_csv(reader, writer, config)
                statvars.extend(statvars_list)
    return statvars


def update_statvars(statvar_list: list, key_value: dict):
    """Given a list of statvars and a key:value pair, this functions adds the
    key value pair to each statvar.
    """
    for d in statvar_list:
        d.update(key_value)


def get_dpv(statvar: dict, config: dict) -> list:
    """A function that goes through the statvar dict and the config and returns
    a list of properties to ignore when generating the dcid.

    Args:
        statvar: A dictionary of prop:values of the statvar
        config: A dict which maps constraint props to the statvar based on
          values in the CSV. See scripts/fbi/hate_crime/config.json for
          an example. The 'dpv' key is used to identify dependent properties.

    Returns:
        A list of properties to ignore when generating the dcid
    """
    ignore_props = []
    for spec in config['dpv']:
        if spec['cprop'] in statvar:
            dpv_prop = spec['dpv']['prop']
            dpv_val = spec['dpv']['val']
            if dpv_val == statvar.get(dpv_prop, None):
                ignore_props.append(dpv_prop)
    return ignore_props


def create_mcf(stat_vars: list, mcf_file_path: str):
    """Writes all statvars to a .mcf file."""
    dcid_set = set()
    final_mcf = ''
    for sv in stat_vars:
        statvar_mcf_list = []
        dcid = sv['Node']
        if dcid in dcid_set:
            continue
        dcid_set.add(dcid)
        for p, v in sv.items():
            if p != 'Node':
                statvar_mcf_list.append(f'{p}: dcs:{v}')
        statvar_mcf = 'Node: dcid:' + dcid + '\n' + '\n'.join(statvar_mcf_list)
        final_mcf += statvar_mcf + '\n\n'

    with open(mcf_file_path, 'w', encoding='utf-8') as f:
        f.write(final_mcf)


def update_statvar_dcids(statvar_list: list, config: dict):
    """Given a list of statvars, generates the dcid for each statvar after
    accounting for dependent PVs.
    """
    for d in statvar_list:
        ignore_props = get_dpv(d, config)
        dcid = get_statvar_dcid(d, ignore_props=ignore_props)
        d['Node'] = dcid

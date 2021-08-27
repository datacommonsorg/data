# Copyright 2021 Google LLC
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
"""
Utility to process UNEnergy data set into a csv with columns for StatVars
and generate a corresponding MCF with statVars and tMCF.
http://data.un.org/Data.aspx

Run this script in this folder:
python3 process.py
"""

import csv
import io
import os
import sys
from collections import defaultdict
import datetime
import time

import pandas as pd
import pandas.api.types as pd_types
import numpy as np
import typing

from absl import flags
from absl import app

import un_energy_codes
from country_codes import get_country_dcid

FLAGS = flags.FLAGS
flags.DEFINE_list('csv_data_files', [],
                  'csv files from UNData Energy datasets to process')
flags.DEFINE_string('dataset_name', 'undata-energy',
                    'Data set name used as file name for mcf and tmcf')
flags.DEFINE_integer('debug_level', 0, 'Data dir to download into')
flags.DEFINE_integer('debug_lines', 10000, 'Print error logs every N lines')

# Columns in the putput CSV
# todo(ajaits): Should it include original columns like transaction code, fuel code, etc?
OUTPUT_CSV_COLUMNS = [
    'Country_dcid', 'Year', 'Quantity', 'Unit_dcid', 'Scaling_factor',
    'Estimate', 'StatVar'
]

_DEFAULT_STAT_VAR_PV = {
    'typeOf': 'dcs:StatisticalVariable',
    'measurementQualifier': 'dcs:Annual',
    'populationType': 'dcs:Energy',
    'statType': 'dcs:measuredValue',
}


def print_debug(debug_level: int, *args):
    if FLAGS.debug_level >= debug_level:
        print("[", datetime.datetime.now(), "] ", *args, file=sys.stderr)


def _print_counters(counters, steps=None):
    row_key = 'inputs_processed'
    if steps is None or row_key not in counters or counters[
            row_key] % steps == 0:
        print('\nSTATS:')
        for k in sorted(counters):
            print(f"\t{k} = {counters[k]}")
        print('')


def _add_error_counter(counter_name: str, error_msg: str, counters):
    print_debug(2, "Error: ", counter_name, error_msg)
    if counters is not None:
        if counters[counter_name] % FLAGS.debug_lines == 0:
            print("ERROR: ", counter_name, ": ", error_msg)
        counters[counter_name] += 1


def remove_extra_characters(name: str) -> str:
    """Removes the parts of the name that is not used in thenode id, including:
         - any namespace: prefix, such as 'dcs:' or 'dcid:'
         - capitalized prefix of two or more letters
         - Any '_'
    """
    if name is None:
        return name
    # strip namespace: prefix
    name = name[name.find(':') + 1:]
    # string any prefix of 2 or more upper case letters.
    upper_prefix = 0
    while upper_prefix < len(name):
        if not name[upper_prefix].isupper():
            break
        upper_prefix += 1
    if upper_prefix > 1:
        name = name[upper_prefix:]
        name = name.removeprefix('_')
    # Replace all '_' with a capitalized letter.
    # Find all occurences of '_'.
    upper_idx = [-1] + [i for i, e in enumerate(name) if e == '_'] + [len(name)]
    # Capitalize the next letter after '_'.
    words = [
        name[x + 1].upper() + name[x + 2:y]
        for x, y in zip(upper_idx, upper_idx[1:])
        if name[x:y] != '_'
    ]
    return ''.join(words)


def add_property_value_name(pv_dict: dict,
                            prop: str,
                            name_list: list,
                            ignore_list=None):
    """Append value of the property in the pc_dict to the name_list.
       The value string is normalized by stripping prefix and removing '_'.
       The property is removed from the pv_dict as well.
    """
    if prop not in pv_dict:
        return
    value = remove_extra_characters(pv_dict[prop])
    pv_dict.pop(prop)
    if value is None:
        return
    if ignore_list is not None:
        if prop in ignore_list or value in ignore_list:
            return
    prefix_len = value.find(':') + 1
    name_list.append(value[prefix_len].upper() + value[prefix_len + 1:])


def get_stat_var_id(sv_pv: dict) -> str:
    """Generate a statvar id from a dictionary of PVs in the following syntax:
       <mqualifier>_<statype>_<measuredProp>_<PopulationType>_<constraint1>_<constraint2>_...
         where <prop> represents the normalized value string for the property
         and constraints are sorted alphabetically.
       Returns a string that can be used as the node id for a StatVar.
    """
    pv = dict(sv_pv)
    ids = []

    # Add default properties
    add_property_value_name(pv, 'measurementQualifier', ids)
    add_property_value_name(pv, 'statType', ids, ['MeasuredValue'])
    add_property_value_name(pv, 'measuredProperty', ids)
    add_property_value_name(pv, 'populationType', ids)
    pv.pop('typeOf')

    # Add the remaining properties in sorted order
    for prop in sorted(pv.keys()):
        add_property_value_name(pv, prop, ids)

    return '_'.join(ids)


def is_valid_stat_var(sv_pv, counters=None) -> bool:
    STAT_VAR_REQUIRED_PROPERTIES = [
        'measuredProperty',
        'populationType',
    ]
    for p in STAT_VAR_REQUIRED_PROPERTIES:
        if p not in sv_pv:
            _add_error_counter(
                f'error_missing_property_{p}',
                f'Stat var missing property {p}, statVar: {sv_pv}', counters)
            return False
    return True


def generate_stat_var(data_row, sv_pv, counters=None) -> str:
    sv_pv.update(_DEFAULT_STAT_VAR_PV)
    t_code = data_row['Transaction Code']
    fuel = data_row['Commodity Code']
    data_sv_pv = un_energy_codes.get_pv_for_energy_code(fuel, t_code, counters)
    if data_sv_pv is None or len(data_sv_pv) == 0:
        return None
    sv_pv.update(data_sv_pv)
    #fuel_dcid = data_row['Fuel_dcid']
    # if 'energySource' in sv_pv:
    #    energy_dcid = sv_pv['energySource']
    #    if fuel_dcid != energy_dcid:
    #        _add_error_counter('error_mismatch_energy_source',
    #                           f'Mismatch in energySource:{energy_dcid} ' +
    #                           f'!= Fuel:{fuel_dcid} for {sv_pv}',
    #                           counters)
    # elif fuel_dcid is not None:
    #    sv_pv['energySource'] = fuel_dcid
    #    counters['outputs_with_fuel_dcid'] += 1
    if not is_valid_stat_var(sv_pv):
        _add_error_counter('error_invalid_stat_var',
                           f'Invalid statVar {sv_pv} for row {data_row}',
                           counters)
        return None
    node_name = get_stat_var_id(sv_pv)
    if node_name is None or len(node_name) == 0:
        _add_error_counter('error_null_stat_var_name',
                           f'No node id for statVar {sv_pv}', counters)
        return None
    return node_name


def get_stat_var_mcf(sv_id, sv_pv) -> str:
    stat_var = []
    stat_var.append(f'Node: {sv_id}')
    for p in sorted(sv_pv.keys()):
        stat_var.append('{}: {}'.format(p, sv_pv[p]))
    return '\n'.join(stat_var)


def process_row(data_row, sv_map, csv_writer, f_out_mcf, counters):
    """Process a single row of input data for un energy.
       Generate a statvar for the fuel and transaction code
    """
    counters['inputs_processed'] += 1
    fuel = data_row['Commodity Code']
    country_code = data_row['Country or Area Code']
    country_name = data_row['Country or Area']
    t_code = data_row['Transaction Code']
    ct_code = data_row['Commodity - Transaction Code']
    ct_name = data_row['Commodity - Transaction']
    year = data_row['Year']
    units = data_row['Unit']
    quantity = data_row['Quantity']
    notes = data_row['Quantity Footnotes']
    if fuel == 'Commodity Code':
        return
    if fuel is None or country_code is None or t_code is None or year is None or quantity is None:
        _add_error_counter(f'error_invalid_input_row',
                           f'Invalid data row {data_row}', counters)
        return

    #fuel_dcid = un_energy_codes.get_energy_source_dcid(fuel)
    # if not fuel_dcid:
    #    _add_error_counter('error_unknown_fuel_code',
    #                       f'Fuel: {fuel}, Commodity code: {ct_code}, '
    #                       'Transaction: {ct_name}', counters)
    #    return
    #data_row['Fuel_dcid'] = fuel_dcid

    country_dcid = get_country_dcid(country_code)
    if not country_dcid:
        _add_error_counter(
            f'error_unknown_country_code_{country_code}',
            f'Country code: {country_code}, name: {country_name}', counters)
        return
    data_row['Country_dcid'] = f'dcs:{country_dcid}'

    unit_dcid, scaling_factor = un_energy_codes.get_unit_dcid_scale(units)
    if not unit_dcid or not scaling_factor:
        _add_error_counter('error_unknown_units',
                           f'Unit: {units}, Transaction: {ct_name}', counters)
        return
    data_row['Unit_dcid'] = unit_dcid
    if scaling_factor != 1:
        data_row['Scaling_factor'] = scaling_factor
    # else:
    #  data_row['Scaling_factor'] = ''

    if notes == "1":
        data_row['Estimate'] = 'Estimate'
    # else:
    #  data_row['IsEstimate'] = ''

    sv_pv = {}
    sv_id = generate_stat_var(data_row, sv_pv, counters)
    if not sv_id:
        _add_error_counter('error_invalid_stat_var',
                           f'Commodity code: {ct_code}, {ct_name}', counters)
        return
    data_row['StatVar'] = sv_id

    if sv_id not in sv_map:
        # New stat var generated. Output PVs to the mcf.
        stat_var_mcf = get_stat_var_mcf(sv_id, sv_pv)
        print_debug(1, 'Generating stat var node: ', stat_var_mcf)
        f_out_mcf.write('\n\n')
        f_out_mcf.write(stat_var_mcf)
        counters['output_stat_vars'] += 1
    sv_map[sv_id] += 1
    csv_writer.writerow(data_row)
    counters['output_csv_rows'] += 1


def process(in_paths: str, out_path: str):
    """Read data from CSV and create CSV,MCF with StatVars and tMCF for DC import"""
    counters = defaultdict(lambda: 0)
    counters['debug_lines'] = FLAGS.debug_lines
    sv_map = defaultdict(lambda: 0)
    csv_file_path = out_path + '.csv'
    start_ts = time.perf_counter()
    with open(csv_file_path, 'w', newline='') as f_out_csv:
        csv_writer = csv.DictWriter(f_out_csv,
                                    fieldnames=OUTPUT_CSV_COLUMNS,
                                    extrasaction='ignore',
                                    lineterminator='\n')
        csv_writer.writeheader()

        mcf_file_path = out_path + '.mcf'
        with open(mcf_file_path, 'w+', newline='') as f_out_mcf:
            for in_file in in_paths:
                with open(in_file) as csvfile:
                    line = 0
                    reader = csv.DictReader(csvfile)
                    for data_row in reader:
                        line += 1
                        data_row['_File'] = in_file
                        data_row['_Row'] = line
                        process_row(data_row, sv_map, csv_writer, f_out_mcf,
                                    counters)
                        _print_counters(counters, 100000)

    end_ts = time.perf_counter()
    counters['total_time_seconds'] = end_ts - start_ts
    _print_counters(counters)
    _print_counters(sv_map)
    print(
        'Processing rate: {:.2f}'.format(counters['inputs_processed'] /
                                         (end_ts - start_ts)), 'rows/sec')


def generate_schema_mcf(mcf_filename: str):
    """Generate MCF for schema such as enums and properties.
    """
    sv_map = defaultdict(lambda: 0)
    with open(mcf_filename, 'w+', newline='') as f_out_mcf:
        # Generate MCF nodes for enums
        enum_mcf = un_energy_codes.generate_un_energy_code_enums(sv_map)
        if enum_mcf is not None:
            for node in enum_mcf:
                if len(node) > 0:
                    f_out_mcf.write('\n\n')
                    f_out_mcf.write('\n'.join(node))
    _print_counters(sv_map)


def main(_):
    if len(FLAGS.csv_data_files) > 0 and FLAGS.dataset_name != '':
        process(FLAGS.csv_data_files, FLAGS.dataset_name)


if __name__ == '__main__':
    print('running main')
    app.run(main)

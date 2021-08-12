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
flags.DEFINE_string('schema_mcf', '', 'Generate schema MCF nodes for enums and properties')

# Columns in the putput CSV
# todo(ajaits): Should it include original columns like transaction code, fuel code, etc?
OUTPUT_CSV_COLUMNS = [
    'Fuel_dcid', 'Country_dcid', 'Year', 'Quantity', 'Unit_dcid', 'Scaling_factor', 'IsEstimate', 'StatVar'
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
    if steps is None or row_key not in counters or counters[row_key] % steps == 0:
        print('\nSTATS:')
        for k in sorted(counters):
            print(f"\t{k} = {counters[k]}")
        print('')


def _add_error_counter(counter_name: str, error_msg: str, counters):
    counters[counter_name] += 1
    print_debug(2, "Error: ", counter_name, error_msg)
    if counters[counter_name] % 1000 == 1:
        print("ERROR: ", counter_name, ": ", error_msg)


def add_property_value_name(pv_dict, prop: str, name_list, ignore_list=None):
    if prop not in pv_dict:
        return
    value = pv_dict[prop]
    pv_dict.pop(prop)
    if value is None:
        return
    if ignore_list is not None and value in ignore_list:
        return
    # strip out any prefix such as 'dcs:' or 'dcid:' or 'schema:'
    prefix_len = value.find(':') + 1
    name_list.append(value[prefix_len:])


def get_stat_var_id(sv_pv) -> str:
    # <mqualifier>_<statype>_<measuredProp>_<PopulationType>_<constraint1>_<constraint2>_...
    pv = dict(sv_pv)
    ids = []

    # Add default properties
    add_property_value_name(pv, 'measurementQualifier', ids)
    add_property_value_name(pv, 'statType', ids, ['dcs:measuredValue'])
    add_property_value_name(pv, 'measuredProperty', ids)
    add_property_value_name(pv, 'populationType', ids)
    pv.pop('typeOf')

    # Add the remaining properties in sorted order
    for prop in sorted(pv.keys()):
        add_property_value_name(pv, prop, ids)

    return '_'.join(ids)


def generate_stat_var(data_row, sv_pv, counters=None) -> str:
    sv_pv.update(_DEFAULT_STAT_VAR_PV)
    t_code = data_row['Transaction Code']
    data_sv_pv = un_energy_codes.get_pv_for_energy_code(t_code, counters)
    if data_sv_pv is None or len(data_sv_pv) == 0:
        return None
    sv_pv.update(data_sv_pv)
    node_name = get_stat_var_id(sv_pv)
    if node_name is None or len(node_name) == 0:
        _add_error_counter('error_null_stat_var_name', counters)
        return None
    return node_name


def get_stat_var_mcf(sv_id, sv_pv) -> str:
    stat_var = []
    stat_var.append(f'Node: {sv_id}')
    stat_var.append('typeOf: dcs:StatisticalVariable')
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

    fuel_dcid = un_energy_codes.get_energy_source_dcid(fuel)
    if not fuel_dcid:
        _add_error_counter('error_unknown_fuel_code',
                           f'Fuel: {fuel}, Commodity code: {ct_code}, '
                           'Transaction: {ct_name}', counters)
        return
    data_row['Fuel_dcid'] = fuel_dcid

    country_dcid = get_country_dcid(country_code)
    if not country_dcid:
        _add_error_counter('error_unknown_country_code',
                           f'Country code: {country_code}, name: {country_name}', counters)
        return
    data_row['Country_dcid'] = f'dcs:{country_dcid}'

    unit_dcid, scaling_factor = un_energy_codes.get_unit_dcid_scale(units)
    if not unit_dcid or not scaling_factor:
        _add_error_counter('error_unknown_units',
                           f'Unit: {units}, Transaction: {ct_name}', counters)
        return
    data_row['Unit_dcid'] = unit_dcid
    data_row['Scaling_factor'] = scaling_factor

    if notes == "1":
      data_row['IsEstimate'] = 'dcs:True'
    #else:
    #  data_row['IsEstimate'] = 'dcs:False'

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
                    reader = csv.DictReader(csvfile)
                    for data_row in reader:
                        process_row(data_row, sv_map, csv_writer,
                                    f_out_mcf, counters)
                        _print_counters(counters, 100000)

           
    end_ts = time.perf_counter()
    counters['total_time_seconds'] = end_ts - start_ts
    _print_counters(counters)
    _print_counters(sv_map)
    print('Processing rate: {:.2f}'.format(
          counters['inputs_processed'] / (end_ts - start_ts)), 'rows/sec')


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
    if FLAGS.schema_mcf != '':
        generate_schema_mcf(FLAGS.schema_mcf)


if __name__ == '__main__':
    print('running main')
    app.run(main)

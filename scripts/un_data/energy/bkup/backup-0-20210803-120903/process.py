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

import pandas as pd
import pandas.api.types as pd_types
import numpy as np
import typing

from absl import flags
from absl import app

import un_energy_codes_map

FLAGS = flags.FLAGS
flags.DEFINE_string('data_dir', 'tmp_raw_data', 'Data dir to download into')
flags.DEFINE_list('csv_data_files', [],
                  'csv files from UNData Energy datasets to process')
flags.DEFINE_string('dataset_name', 'undata-energy',
                    'Data set name used as file name for mcf and tmcf')

# Columns in the putput CSV
# todo(ajaits): Should it include original columns like transaction code, fuel code, etc?
OUTPUT_CSV_COLUMNS = [
    'Fuel_dcid', 'Country_dcid', 'Quantity', 'Unit_dcid', 'Scaling_factor', 'IsEstimate', 'StatVar'
]


def _print_counters(counters, steps=None):
    if not steps or counters['inputs_processed'] % steps == 0:
        print('\nSTATS:')
        for k in sorted(counters):
            print(f"\t{k} = {counters[k]}")
        print('')


def _add_error_counter(counter_name: str, error_msg: str, counters):
    counters[counter_name] += 1
    if counters[counter_name] % 1000 == 1:
        print("ERROR: ", counter_name, ": ", error_msg)


def generate_stat_var(data_row, sv_pv) -> str:


def get_stat_var_mcf(sv_id, sv_pv) -> str:
    stat_var = []
    stat_var.append(f'Node: {sv_id}')
    for p in sv_pv.keys():
        stat_var.append(f'{}: {}'.format(p, sv_pv[p]))
    return '\n'.join(stat_var)


def process_row(data_row, sv_map, f_out_csv, f_out_mcf, counters):
    """Process a single row of input data for un energy.
       Generate a statvar for the fuel and transaction code
    """
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

    fuel_dcid = un_energy_codes_map.get_energy_source_dcid(fuel)
    if not fuel_dcid:
        _add_error_counter('error_unknown_fuel_code',
                           f'Fuel: {fuel}, Commodity code: {ct_code}, '
                            'Transaction: {ct_name}')
        return
    data_row['Fuel_dcid'] = fuel_dcid

    country_dcid = un_energy_codes_map.get_country_dcid(country_code)
    if not country_dcid:
        _add_error_counter('error_unknown_country_code',
                           f'Country code: {country_code}, name: {country_name}')
        return
    data_row['Country_dcid'] = fuel_dcid

    unit_dcid, scaling_factor = un_energy_codes_map.get_unit_dcid_scale(units)
    if not unit_dcid or not scaling_factor:
        _add_error_counter('error_unknown_units',
                           f'Unit: {units}, Transaction: {ct_name}')
        return
    data_row['Unit_dcid'] = unit_dcid

    sv_pv = {}
    sv_id = generate_stat_var(data_row, sv_pv)
    if not sv_id:
        _add_error_counter('error_unknown_stat_var',
                           f'Commodity code: {ct_code}, {ct_name}')
        return
    data_row['StatVar'] = sv_id

    if sv_id not in sv_map:
        # New stat var geneated. Output PVs to the mcf.
        stat_var_mcf = get_stat_var_mcf(sv_id, sv_pv)
        print('Generating stat var node: ',



def process(in_paths: str, out_path: str):
    """Read data from CSV and create CSV,MCF with StatVars and tMCF for DC import"""
    counters=defaultdict(lambda: 0)
    sv_map={}
    csv_file_path=out_path + '.csv'
    with open(csv_file_path, 'a', newline='') as f_out_csv:
        writer=csv.DictWriter(f_out,
                                fieldnames=OUTPUT_CSV_COLUMNS,
                                lineterminator='\n')
        mcf_file_path=out_path + '.mcf'
        with open(mcf_file_path, 'w+', newline='') as f_out_mcf:
            for in_file in inpaths:
                with open(in_file) as csvfile:
                    reader=csv.DictReader(csvfile)
                    for data_row in reader:
                        process_row(data_row, sv_map, f_out_csv,
                                    f_out_mcf, counters)
                        _print_counters(counters, 10000)


if __name__ == '__main__':
    process(sys.argv[1], sys.argv[2])

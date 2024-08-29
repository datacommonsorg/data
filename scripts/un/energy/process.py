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
import datetime
import time

from absl import app
from absl import flags
from collections import defaultdict

# Allows the following module imports to work when running as a script
# module_dir_ is the path to where this code is running from.
module_dir_ = os.path.dirname(__file__)
sys.path.append(os.path.join(module_dir_))

from country_codes import get_country_dcid
import un_energy_codes
import download

FLAGS = flags.FLAGS
flags.DEFINE_list('csv_data_files', [],
                  'csv files from UNData Energy datasets to process')
flags.DEFINE_string('output_path', 'tmp_data_dir/un_energy_output',
                    'Data set name used as file name for mcf and tmcf')
flags.DEFINE_integer('debug_level', 0, 'Data dir to download into')
flags.DEFINE_integer('debug_lines', 100000, 'Print error logs every N lines')
flags.DEFINE_bool('copy_input_columns', False,
                  'Add columns from the input csv into the output')

# Columns in the putput CSV
# todo(ajaits): Should it include original columns like transaction code, fuel code, etc?
OUTPUT_CSV_COLUMNS = [
    'Country_dcid',
    'Year',
    'Quantity',
    'Unit_dcid',
    'Estimate',
    'StatVar',
]

INPUT_CSV_COLUMNS_COPIED = [
    'Commodity Code', 'Country or Area', 'Transaction Code',
    'Commodity - Transaction Code', 'Commodity - Transaction', 'Unit',
    'Quantity Footnotes'
]

_DEFAULT_STAT_VAR_PV = {
    'typeOf': 'dcs:StatisticalVariable',
    'measurementQualifier': 'dcs:Annual',
    'populationType': 'dcs:Energy',
    'statType': 'dcs:measuredValue',
}

UN_ENERGY_TMCF = """
Node: E:UNEnergy->E0
typeOf: dcs:StatVarObservation
observationAbout: C:UNEnergy->Country_dcid
variableMeasured: C:UNEnergy->StatVar
observationDate: C:UNEnergy->Year
observationPeriod: "P1Y"
value: C:UNEnergy->Quantity
unit: C:UNEnergy->Unit_dcid
measurementMethod: C:UNEnergy->Estimate
"""


def _print_debug(debug_level: int, *args):
    if debug_level <= 1:
        print("[", datetime.datetime.now(), "] ", *args, file=sys.stderr)


def _print_counters(counters, steps=None):
    row_key = 'inputs_processed'
    if steps is None or row_key not in counters or counters[
            row_key] % steps == 0:
        print('\nSTATS:')
        for k in sorted(counters):
            print(f"\t{k} = {counters[k]}")
        if 'inputs_processed' in counters:
            start_ts = counters['time_start']
            end_ts = time.perf_counter()
            print(
                'Processing rate: {:.2f}'.format(counters['inputs_processed'] /
                                                 (end_ts - start_ts)),
                'rows/sec')
        print('', flush=True)


def _add_error_counter(counter_name: str, error_msg: str, counters):
    _print_debug(2, "Error: ", counter_name, error_msg)
    if counters is not None:
        debug_lines = 1
        if 'debug_lines' in counters:
            debug_lines = counters['debug_lines']
        if counters[counter_name] % debug_lines == 0:
            print("ERROR: ", counter_name, ": ", error_msg)
        counters[counter_name] += 1


def _remove_extra_characters(name: str) -> str:
    """Removes the parts of the name that is not used in the node id,
    including:
         - any namespace: prefix, such as 'dcs:' or 'dcid:'
         - capitalized prefix of two or more letters
         - Any '_'
    For example: 'dcid:EIA_Other_fuel' will be converted to: 'OtherFuel'

    Args:
      name: string to be normalized.

    Returns:
      string without the extra characters and capitalized appropriately.
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
        if name[0] == '_':
            name = name[1:]
    # Replace all '_' with a capitalized letter.
    # Find all occurences of '_'.
    upper_idx = [-1] + \
        [i for i, e in enumerate(name) if e == '_'] + [len(name)]
    # Capitalize the next letter after '_'.
    words = [
        name[x + 1].upper() + name[x + 2:y]
        for x, y in zip(upper_idx, upper_idx[1:])
        if name[x:y] != '_'
    ]
    return ''.join(words)


def _add_property_value_name(pv_dict: dict,
                             prop: str,
                             name_list: list,
                             ignore_list=None):
    """Append value of the property in the pc_dict to the name_list.
    The value string is normalized by stripping prefix and removing '_'.
    The property is removed from the pv_dict as well.

    Args:
      pv_dict: dictionary of property and values.
         the matching property is remove from this dictionary.
      prop: string with the property code whose vales is to be extracted
      name_list: output list of strings into which the nornalized value
         string is added.
      ignore_list: [optional] list of strings of property or value
         that is not added to the name_list
    """
    if prop not in pv_dict:
        return
    orig_value = pv_dict[prop]
    value = _remove_extra_characters(orig_value)
    pv_dict.pop(prop)
    if value is None:
        return
    if ignore_list is not None:
        if prop in ignore_list or value in ignore_list or orig_value in ignore_list:
            return
    prefix_len = value.find(':') + 1
    name_list.append(value[prefix_len].upper() + value[prefix_len + 1:])


def _get_stat_var_id(sv_pv: dict, ignore_list=None) -> str:
    """Generate a statvar id from a dictionary of PVs in the following syntax:
    <mqualifier>_<statype>_<measuredProp>_<PopulationType>_<constraint1>_<constraint2>_...
        where <prop> represents the normalized value string for the property
        and constraints are sorted alphabetically.
    property and values in the ignore_list are not added to the id.

    Args:
      sv_pv: dictionary of properties and respective values for a StatVar
        for which the node id is to be generated.
      ignore_list: List of property of value strings not to be added to the name

    Returns:
      String with the node id containing values of PVs
      that can be used as the node id for a StatVar.
    """
    pv = dict(sv_pv)
    ids = []
    ignore_values = ['MeasuredValue', 'description']
    if ignore_list is not None:
        ignore_values.extend(ignore_list)

    # Add default properties
    _add_property_value_name(pv, 'measurementQualifier', ids, ignore_values)
    _add_property_value_name(pv, 'statType', ids, ignore_values)
    _add_property_value_name(pv, 'measuredProperty', ids, ignore_values)
    _add_property_value_name(pv, 'populationType', ids, ignore_values)
    pv.pop('typeOf')

    # Add the remaining properties in sorted order
    for prop in sorted(pv.keys()):
        _add_property_value_name(pv, prop, ids)

    return '_'.join(ids)


def is_valid_stat_var(sv_pv: dict, counters=None) -> bool:
    """Check if a StatVar is valid.
    Verifies if the statVar has the required properties.

    Args:
      sv_pv: Dictionary of property and value for a StatVar
      counters: [optional] error counters to be updated

    Returns:
      True if the statVar is valid.
    """
    # Check StatVar has all required properties.
    STAT_VAR_REQUIRED_PROPERTIES = [
        'measuredProperty',
        'populationType',
    ]
    for prop in STAT_VAR_REQUIRED_PROPERTIES:
        if prop not in sv_pv:
            _add_error_counter(
                f'error_missing_property_{p}',
                f'Stat var missing property {p}, statVar: {sv_pv}', counters)
            return False

    return True


def _get_scaled_value(value: str, multiplier: int) -> str:
    """Returns a scaled value for the given value and multiplier.

    Args:
      value: Original value in string. If it contains a decimal point
        the returned value will have the same precision.
    """
    round_digits = 0
    fraction_digits = value.find('.')
    if fraction_digits >= 0:
        round_digits = len(value) - fraction_digits - 1
    scaled_value = float(value) * multiplier
    if round_digits == 0:
        return str(int(scaled_value))
    return str(round(scaled_value, round_digits))


def generate_stat_var(data_row: dict, sv_pv: dict, counters=None) -> str:
    """Add property:values for a StatVar for the given data row.

    Args:
      data_row: dictionary of a cells in a CSV row keyed by the column name
      sv_pv: dictinary of PVs for a statVar into which new properties are added
      counters: [optional] error counters to be updated

    Returns:
      string for the stat_var node id with all PVs in sv_pv
    """
    sv_pv.update(_DEFAULT_STAT_VAR_PV)
    t_code = data_row['Transaction Code']
    fuel = data_row['Commodity Code']
    data_sv_pv = un_energy_codes.get_pv_for_energy_code(fuel, t_code, counters)
    if data_sv_pv is None or len(data_sv_pv) == 0:
        # data row is ignored
        return None
    if 'Ignore' in data_sv_pv:
        # statVar is to be ignored.
        ignore_reason = data_sv_pv['Ignore']
        ignore_reason = ignore_reason[ignore_reason.find(':') + 1:]
        _add_error_counter(f'warning_ignored_stat_var_{ignore_reason}',
                           f'Invalid statVar {sv_pv} for row {data_row}',
                           counters)
        return None
    sv_pv.update(data_sv_pv)
    if not is_valid_stat_var(sv_pv):
        _add_error_counter('error_invalid_stat_var',
                           f'Invalid statVar {sv_pv} for row {data_row}',
                           counters)
        return None
    node_name = _get_stat_var_id(sv_pv)
    if node_name is None or len(node_name) == 0:
        _add_error_counter('error_null_stat_var_name',
                           f'No node id for statVar {sv_pv}', counters)
        return None
    return f'dcid:{node_name}'


def _get_stat_var_mcf(sv_id: str, sv_pv: dict) -> str:
    """Generate a MCF node string for a statVar

    Args:
      sv_id: Node Id string for the StatVar
      sv_pv: dictionary of all property:values for the StatVar

    Returns:
      a string with StatVar node in MCF format with each property in a new line
      and properties are sorted in alphabetical order.
    """
    stat_var = []
    stat_var.append(f'Node: {sv_id}')
    for p in sorted(sv_pv.keys()):
        stat_var.append('{}: {}'.format(p, sv_pv[p]))
    return '\n'.join(stat_var)


def _get_stat_var_prop(prop_list: list, sv_pv: dict) -> str:
    """Get the value of the first property from the list in the StatVar.

    Args:
      prop_list: order list of properties looked up in the StatVar
      sv_pv: dictionary of StatVar PVs.

    Returns:
      value of the property without the namespace prefix or
      None if none of the properties exist in the statVar.
    """
    for prop in prop_list:
        if prop in sv_pv:
            prop_value = sv_pv[prop]
            if prop_value is not None:
                return prop_value[prop_value.find(':') + 1:]
    return ''


def _add_stat_var_description(data_row: dict, sv_pv: dict):
    """Adds a description to the StatVar using the input data_row containing
    the codes and text fields.

    Args:
      data_row: Dictionary with input/output CSV columns.
      sv_pv: Dictionary of StatVar PVs
    """
    if 'description' in sv_pv:
        return
    code = data_row['Commodity - Transaction Code']
    transaction = data_row['Commodity - Transaction']
    fuel_name = _get_stat_var_prop(
        ['energySource', 'fuelType', 'populationType'], sv_pv)
    measured_prop = _get_stat_var_prop(['measuredProperty'], sv_pv)
    sv_pv[
        'description'] = f'"UN Energy data for {fuel_name} {measured_prop}, {transaction} (code: {code})"'


def _process_row(data_row: dict, sv_map: dict, row_map: dict, sv_obs: dict,
                 csv_writer, f_out_mcf, counters):
    """Process a single row of input data for un energy.
    Generate a statvar for the fuel and transaction code and adds the MCF for the
    unique StatVars into the f_out_mcf file and the columns for the StatVarObservation
    into the csv_writer.

    Args:
      data_row: dictionary of CSV column values from the input file.
      sv_map: dictionary of statVar ids that are already emitted into f_out_mcf
      row_map: dictionary of data rows already processed.
        Used to dedup input rows.
      sv_obs: dictionary of StatVarObs already emitted
      csv_writer: file handle to write statvar observation values into.
      f_out_mcf: file handle to write unique statVar MCF nodes
      counters: counters to be updated
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

    # Ignore the column header and footers in case csv files were concatenated.
    if fuel == 'Commodity Code' or fuel == 'fnSeqID' or fuel == '1' or fuel == '':
        return
    if fuel is None or country_code is None or t_code is None or year is None or quantity is None:
        _add_error_counter(f'error_invalid_input_row',
                           f'Invalid data row {data_row}', counters)
        return

    # Check for duplicate rows
    row_key = f'{fuel}-{t_code}-{country_code}-{quantity}-{units}-{notes}'
    row_map[row_key] += 1
    if row_map[row_key] > 1:
        _add_error_counter('inputs_ignored_duplicate',
                           f'Duplicate input row: {data_row}', counters)
        return

    # Get the country from the numeric code.
    country_dcid = get_country_dcid(country_code)
    if country_dcid is None:
        _add_error_counter(
            f'error_unknown_country_code_{country_code}',
            f'Country code: {country_code}, name: {country_name}', counters)
        return
    if len(country_dcid) == 0:
        _add_error_counter(
            f'warning_ignoring_country_code_{country_code}',
            f'Country ignored: {country_code}, name: {country_name}', counters)
        return

    data_row['Country_dcid'] = f'dcs:{country_dcid}'

    # Add the quantity units and multiplier for the value if any.
    unit_dcid, multiplier = un_energy_codes.get_unit_dcid_scale(units)
    if not unit_dcid or not multiplier:
        _add_error_counter('error_unknown_units',
                           f'Unit: {units}, Transaction: {ct_name}', counters)
        return
    data_row['Unit_dcid'] = unit_dcid
    if multiplier > 1:
        data_row['Quantity'] = _get_scaled_value(quantity, multiplier)

    # The observation is an estimated value if it has a footnote.
    if notes == "1":
        data_row['Estimate'] = 'UNStatsEstimate'

    # Generate a StatVar for the row using the fuel and transaction code values.
    sv_pv = {}
    sv_id = generate_stat_var(data_row, sv_pv, counters)
    if not sv_id:
        return
    data_row['StatVar'] = sv_id

    if sv_id not in sv_map:
        # New stat var generated. Output PVs to the statvar mcf file.
        _add_stat_var_description(data_row, sv_pv)
        stat_var_mcf = _get_stat_var_mcf(sv_id, sv_pv)
        _print_debug(2, 'Generating stat var node: ', stat_var_mcf)
        f_out_mcf.write('\n\n')
        f_out_mcf.write(stat_var_mcf)
        counters['output_stat_vars'] += 1
    sv_map[sv_id] += 1

    # Check for duplicate StatVarObs.
    obs_key = f'{sv_id}-{country_dcid}-{year}'
    cur_value = f'{quantity}-{notes}'
    if obs_key in sv_obs:
        prev_value = sv_obs[obs_key]
        _add_error_counter(
            'warning_duplicate_obs_dropped',
            f'Duplicate value {cur_value} for SVO: {obs_key}, prev: {prev_value}',
            counters)
        return
    sv_obs[obs_key] = cur_value

    # Write the StatVarObs into the csv file.
    csv_writer.writerow(data_row)

    # Update counters.
    for prop in sv_pv:
        counters[f'outputs_with_property_{prop}'] += 1
    counters['output_csv_rows'] += 1


def process(in_paths: list,
            out_path: str,
            debug_lines=1,
            copy_input_columns=False) -> dict:
    """Read data from CSV and create CSV,MCF with StatVars and tMCF for DC import.
    Generates the following output files:
      - .csv: File with StatVarObservations
      - .mcf: File with StatVar Nodes in MCF format
      - .tmcf: File with tMCF for the StatVarObservation

    Args:
      in_paths: list of UN Energy CSV data files to be processed.
      out_path: prefix for the output StatVarObs csv and StatVar mcf files.
      debug_lines: Generate each error message once every debug_lines.
      copy_input_columns: Copy contents of input csv columns that are not used
         in statVarObs as well into the output csv.
         INPUT_CSV_COLUMNS_COPIED is the list of such columns.

    Returns:
      Counters after processing
    """
    counters = defaultdict(lambda: 0)
    counters['debug_lines'] = debug_lines
    sv_map = defaultdict(lambda: 0)
    row_map = defaultdict(lambda: 0)
    sv_obs = {}
    csv_file_path = out_path + '.csv'
    start_ts = time.perf_counter()
    counters['time_start'] = start_ts
    # Setup the output file handles for MCF and CSV.
    output_columns = OUTPUT_CSV_COLUMNS
    if copy_input_columns:
        output_columns.extend(INPUT_CSV_COLUMNS_COPIED)
    with open(csv_file_path, 'w', newline='') as f_out_csv:
        csv_writer = csv.DictWriter(f_out_csv,
                                    fieldnames=OUTPUT_CSV_COLUMNS,
                                    extrasaction='ignore',
                                    lineterminator='\n')
        csv_writer.writeheader()
        mcf_file_path = out_path + '.mcf'
        with open(mcf_file_path, 'w+', newline='') as f_out_mcf:
            # Process each CSV input file, one row at a time.
            for in_file in in_paths:
                print(f'Processing data file: {in_file}')
                with open(in_file) as csvfile:
                    counters['input_files'] += 1
                    line = 0
                    reader = csv.DictReader(csvfile)
                    for data_row in reader:
                        line += 1
                        data_row['_File'] = in_file
                        data_row['_Row'] = line
                        _process_row(data_row, sv_map, row_map, sv_obs,
                                     csv_writer, f_out_mcf, counters)
                        _print_counters(counters, counters['debug_lines'])
                print(f'Processed {line} rows from data file: {in_file}')
            f_out_mcf.write('\n')

    # Generate the tMCF file
    tmcf_file_path = out_path + '.tmcf'
    with open(tmcf_file_path, 'w', newline='') as f_out_tmcf:
        f_out_tmcf.write(UN_ENERGY_TMCF)

    end_ts = time.perf_counter()
    counters['time_end'] = end_ts
    counters['time_total_seconds'] = end_ts - start_ts
    _print_counters(counters)
    _print_counters(sv_map)
    print(
        'Processing rate: {:.2f}'.format(counters['inputs_processed'] /
                                         (end_ts - start_ts)), 'rows/sec')
    return counters


def main(_):
    csv_data_files = FLAGS.csv_data_files
    if len(csv_data_files) == 0:
        print(f'Downloading energy data set files')
        csv_data_files = download.download_un_energy_dataset()

    if len(csv_data_files) > 0 and FLAGS.output_path != '':
        process(csv_data_files, FLAGS.output_path, FLAGS.debug_lines,
                FLAGS.copy_input_columns)
    else:
        print(f'Please specify files to process with --csv_data_files=<,>')


if __name__ == '__main__':
    print('running main')
    app.run(main)
